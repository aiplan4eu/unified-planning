# Copyright 2021 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""This module defines the trajectory constraints remover class."""

import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.walkers import Simplifier, ExpressionQuantifiersRemover
from unified_planning.shortcuts import *
from unified_planning.model.operators import OperatorKind

NUM = "num"
CONSTRAINTS = "constraints"
HOLD = "hold"
GOAL = "goal"
SEEN_PHI = "seen-phi"
SEEN_PSI = "seen-psi"
SEPARATOR = "-"

class TrajectoryConstraintsRemover(engines.engine.Engine, CompilerMixin):
    """Translate problem in another problem with no trajectory constraints."""

    def __init__(self):
        self._simplifier = None

    @property
    def name(self):
        return "TrajectoryConstraintsRemover"

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= TrajectoryConstraintsRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.TRAJECTORY_CONSTRAINTS_REMOVING

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class('ACTION_BASED') # type: ignore
        supported_kind.set_typing('FLAT_TYPING') # type: ignore
        supported_kind.set_typing('HIERARCHICAL_TYPING') # type: ignore
        supported_kind.set_numbers('CONTINUOUS_NUMBERS') # type: ignore
        supported_kind.set_numbers('DISCRETE_NUMBERS') # type: ignore
        supported_kind.set_fluents_type('NUMERIC_FLUENTS') # type: ignore
        supported_kind.set_fluents_type('OBJECT_FLUENTS') # type: ignore
        supported_kind.set_conditions_kind('NEGATIVE_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('EQUALITY') # type: ignore
        supported_kind.set_conditions_kind('EXISTENTIAL_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('UNIVERSAL_CONDITIONS') # type: ignore
        supported_kind.set_effects_kind('CONDITIONAL_EFFECTS') # type: ignore
        supported_kind.set_effects_kind('INCREASE_EFFECTS') # type: ignore
        supported_kind.set_effects_kind('DECREASE_EFFECTS') # type: ignore
        supported_kind.set_time('CONTINUOUS_TIME') # type: ignore
        supported_kind.set_time('DISCRETE_TIME') # type: ignore
        supported_kind.set_time('INTERMEDIATE_CONDITIONS_AND_EFFECTS') # type: ignore
        supported_kind.set_time('TIMED_EFFECT') # type: ignore
        supported_kind.set_time('TIMED_GOALS') # type: ignore
        supported_kind.set_time('DURATION_INEQUALITIES') # type: ignore
        supported_kind.set_simulated_entities('SIMULATED_EFFECTS') # type: ignore
        supported_kind.set_constraints_kind('TRAJECTORY_CONSTRAINTS') # type: ignore
        return supported_kind

    def compile(self, problem: 'up.model.AbstractProblem',
                compilation_kind: 'up.engines.CompilationKind') -> CompilerResult:
        if not self.supports(problem.kind):
            raise up.exceptions.UPUsageError('This compiler cannot handle this kind of problem!')
        assert isinstance(problem, Problem)
        if not self.supports_compilation(compilation_kind):
            raise up.exceptions.UPUsageError('This compiler cannot handle this kind of compilation!')
        self._env = problem.env
        self._simplifier = Simplifier(self._env)
        self._expression_quantifier_remover = ExpressionQuantifiersRemover(problem.env)
        with self._env.factory.Compiler(problem_kind=problem.kind, compilation_kind=engines.CompilationKind.GROUNDING) as grounder:
            grounding_result = grounder.compile(problem, engines.CompilationKind.GROUNDING)
        self._problem = grounding_result.problem
        A = grounding_result.problem.actions
        I_g = grounding_result.problem.initial_values
        I = self._ground_initial_state(A, I_g)
        C_temp = self._simplifier.simplify(And(problem.trajectory_constraints))
        C = self._build_constraint_list(C_temp)
        relevancy_dict = self._build_relevancy_dict(C)
        A_prime = []
        G_temp = []
        I_prime, F_prime = self._get_monitoring_atoms(C, I)
        for c in self._LTC(C):
            monitoring_atom = FluentExp(Fluent(f'{c._monitoring_atom_predicate}', BoolType()))
            G_temp.append(monitoring_atom)
        G_prime = And(G_temp)
        for a in A:
            E = list() # type: ignore
            relevant_constraints = self._get_relevant_constraints(a, relevancy_dict)
            for c in relevant_constraints:
                if c.is_always():
                    precondition, to_add = self._manage_always_compilation(c.args[0], a)
                elif c.is_at_most_once():
                    precondition, to_add = self._manage_amo_compilation(c.args[0], c._monitoring_atom_predicate, a, E)
                elif c.is_sometime_before():
                    precondition, to_add = self._manage_sb_compilation(c.args[0], c.args[1], c._monitoring_atom_predicate, a, E)
                elif c.is_sometime():
                    self._manage_sometime_compilation(c.args[0], c._monitoring_atom_predicate, a, E)
                elif c.is_sometime_after():
                    self._manage_sa_compilation(c.args[0], c.args[1], c._monitoring_atom_predicate, a, E)
                else:
                    raise Exception(f'ERROR This compiler cannot handle this constraint = {c}')
                if c.is_always() or c.is_at_most_once() or c.is_sometime_before():
                    if to_add and not precondition.is_true():
                        a.preconditions.append(precondition)
            for eff in E:
                a.effects.append(eff)
            if FALSE() not in a.preconditions:
                A_prime.append(a)
        G_new = self._simplifier.simplify(And(grounding_result.problem.goals, G_prime))
        grounding_result.problem.clear_goals()
        grounding_result.problem.add_goal(G_new)
        grounding_result.problem.clear_trajectory_constraints()
        for fluent in F_prime:
            grounding_result.problem.add_fluent(fluent)
        grounding_result.problem.clear_actions()
        for action in A_prime:
            grounding_result.problem.add_action(action)
        for init_val in I_prime:
            grounding_result.problem.set_initial_value(FluentExp(Fluent(f'{init_val}', BoolType())), TRUE())
        return grounding_result

    def _build_constraint_list(self, C_temp):
        C_list = C_temp.args if C_temp.is_and() else [C_temp]
        C_to_return = self._simplifier.simplify(And(self._remove_quantifire(C_list)))
        return C_to_return.args if C_to_return.is_and() else [C_to_return]

    def _remove_quantifire(self, C):
        new_C = []
        for c in C:
            if c.is_always():
                new_C.append(Always(self._get_constraints_condition(c.args[0])))
            elif c.is_sometime():
                new_C.append(Sometime(self._get_constraints_condition(c.args[0])))
            elif c.is_at_most_once():
                new_C.append(At_Most_Once(self._get_constraints_condition(c.args[0])))
            elif c.is_sometime_before():
                new_C.append(Sometime_Before(
                             self._get_constraints_condition(c.args[0]),
                             self._get_constraints_condition(c.args[1]))
                            )
            elif c.is_sometime_after():
                new_C.append(Sometime_After(
                             self._get_constraints_condition(c.args[0]),
                             self._get_constraints_condition(c.args[1]))
                            )
            else:
                new_C.append(self._get_constraints_condition(c))
        return new_C

    def _get_constraints_condition(self, cond):
        if cond.is_forall() or cond.is_exists():
            return self._expression_quantifier_remover.remove_quantifiers(cond, self._problem)
        elif cond.is_and():
            args = []
            for arg in cond.args:
                args.append(self._get_constraints_condition(arg))
            return self._simplifier.simplify(And(args))
        elif cond.is_or():
            args = []
            for arg in cond.args:
                args.append(self._get_constraints_condition(arg))
            return self._simplifier.simplify(Or(args))
        elif cond.is_not():
            return self._simplifier.simplify(Not(self._get_constraints_condition(cond.args[0])))
        else :
            return cond

    def _manage_sa_compilation(self, phi, psi, m_atom, a, E):
        R1 = self._simplifier.simplify(self._regression(phi, a))
        R2 = self._simplifier.simplify(self._regression(psi, a))
        monitoring_atom = FluentExp(Fluent(f'{m_atom}', BoolType()))
        if phi != R1 or psi != R2:
            cond = self._simplifier.simplify(And([R1, Not(R2)]))
            self._add_cond_eff(E, cond, Not(monitoring_atom))
        if psi != R2:
            self._add_cond_eff(E, R2, monitoring_atom)

    def _manage_sometime_compilation(self, phi, m_atom, a, E):
        monitoring_atom = FluentExp(Fluent(f'{m_atom}', BoolType()))
        R = self._simplifier.simplify(self._regression(phi, a))
        if R != phi:
            self._add_cond_eff(E, R, monitoring_atom)

    def _manage_sb_compilation(self, phi, psi, m_atom, a, E):
        monitoring_atom = FluentExp(Fluent(f'{m_atom}', BoolType()))
        R_phi = self._simplifier.simplify(self._regression(phi, a))
        if R_phi == phi:
            added_precond = (None, False)
        else:
            rho = self._simplifier.simplify(Or([Not(R_phi), monitoring_atom]))
            added_precond = (rho, True)
        R_psi = self._simplifier.simplify(self._regression(psi, a))
        if R_psi != psi:
            self._add_cond_eff(E, R_psi, monitoring_atom)
        return added_precond

    def _manage_amo_compilation(self, phi, m_atom, a, E):
        monitoring_atom = FluentExp(Fluent(f'{m_atom}', BoolType()))
        R = self._simplifier.simplify(self._regression(phi, a))
        if R == phi:
            return None, False
        else:
            rho = self._simplifier.simplify(Or([Not(R), Not(monitoring_atom), phi]))
            self._add_cond_eff(E, R, monitoring_atom)
            return rho, True

    def _manage_always_compilation(self, phi, a):
        R = self._simplifier.simplify(self._regression(phi, a))
        if R == phi:
            return None, False
        else:
            return R, True

    def _add_cond_eff(self, E, cond, eff):
        if (not self._simplifier.simplify(cond).is_false()):
            if eff.is_not():
                E.append(Effect(condition=cond, fluent=eff.args[0], value=FALSE()))
            else:
                E.append(Effect(condition=cond, fluent=eff, value=TRUE()))

    def _get_relevant_constraints(self, a, relevancy_dict):
        relevant_constrains = []
        for eff in a.effects:
            constr = relevancy_dict.get(eff.fluent, [])
            for c in constr:
                if c not in relevant_constrains:
                    relevant_constrains.append(c)
        return relevant_constrains        

    def _ground_initial_state(self, A, I):
        grounding_init_state = {}
        for act in A:
            for eff in act.effects:
                grounding_init_state[eff.fluent] = None
        I_grunded = {}
        for key_gr in grounding_init_state.keys():
            if key_gr in I:
                if I[key_gr].is_true():
                    I_grunded[key_gr] = I[key_gr]
        return I_grunded

    def _remove_duplicates(self, relevant_atoms):
        elems = []
        for elem in relevant_atoms:
            if elem not in elems:
                elems.append(elem)
        return elems

    def _simple_substitution(self, set, phi):
        if phi.is_true():
            return TRUE()
        if phi.is_false():
            return FALSE()
        if phi.is_fluent_exp() or phi.is_not():
            if phi in set:
                return TRUE()
            phi_neg = Not(phi)
            if phi_neg in set:
                return FALSE()
            else:
                if phi.is_not():
                    return TRUE()
                else:
                    return FALSE()
        elif phi.is_or():
            return Or(self._simple_substitution(set, component) for component in phi.args)
        else:
            return And(self._simple_substitution(set, component) for component in phi.args)

    def _true_init(self, state, phi):
        logical_value_in_init = self._simplifier.simplify(self._simple_substitution(state, phi))
        if logical_value_in_init.is_true():
            return True
        elif logical_value_in_init.is_false():
            return False
        else:
            raise Exception("ERROR in initial state evaluation of a constraint")

    def _evaluate_constraint(self, constr, initial_state):
        if constr.is_sometime():
            return HOLD, self._true_init(initial_state, constr.args[0])
        elif constr.is_sometime_after():
            return HOLD, self._true_init(initial_state, constr.args[1]) or not self._true_init(initial_state, constr.args[0])
        elif constr.is_sometime_before():
            return SEEN_PSI, self._true_init(initial_state, constr.args[1])
        elif constr.is_at_most_once():
            return SEEN_PHI, self._true_init(initial_state, constr.args[0])
        else:
            return None, self._true_init(initial_state, constr.args[0])

    def _get_monitoring_atoms(self, C, I):
        monitoring_atoms = []
        monitoring_atoms_counter = 0
        initial_state_prime = []   
        for constr in C:
            if not constr.is_always():
                type, init_state_value = self._evaluate_constraint(constr, I)
                fluent = Fluent(f'{type}{SEPARATOR}{monitoring_atoms_counter}', BoolType())
                monitoring_atoms.append(fluent)
                monitoring_atom = FluentExp(fluent)
                constr.set_monitoring_atom_predicate(monitoring_atom)
                if init_state_value:
                    initial_state_prime.append(monitoring_atom)
                if constr.is_sometime_before():
                    if self._true_init(I, constr.args[0]):
                        raise Exception("PROBLEM NOT SOLVABLE: a sometime-before is violated in the initial state")
                monitoring_atoms_counter += 1
        for constr in C:
            if constr.is_always():
                if not self._true_init(I, constr.args[0]):
                    raise Exception("PROBLEM NOT SOLVABLE: an always is violated in the initial state")
        return initial_state_prime, monitoring_atoms

    def _build_relevancy_dict(self, C):
        relevancy_dict = {}
        for c in C:
            relevant_atoms = []
            for condition in c.args:
                relevant_atoms += self._get_all_atoms(condition)
                relevant_atoms = self._remove_duplicates(relevant_atoms)
            for atom in relevant_atoms:
                if atom not in relevancy_dict:
                    relevancy_dict[atom] = []
                relevancy_dict[atom].append(c)
        return relevancy_dict

    def _get_all_atoms(self, condition):
        if condition.is_fluent_exp():
            return [condition]
        elif condition.is_and() or condition.is_or() or condition.is_not():
            atoms = []
            for arg in condition.args:
                atoms += self._get_all_atoms(arg)
            return atoms
        else:
            return []

    def _ITC(C):
        for constr in C:
            if constr.kind in [OperatorKind.ALWAYS, OperatorKind.SOMETIME_BEFORE, OperatorKind.AT_MOST_ONCE]:
                yield constr

    def _LTC(self, C):
        for constr in C:
            if constr.node_type in [OperatorKind.SOMETIME, OperatorKind.SOMETIME_AFTER]:
                yield constr

    def _gamma_substitution(self, literal, action):
        negated_literal = Not(expression=literal)
        gamma1 = self._gamma(literal, action)
        gamma2 = Not(self._gamma(negated_literal, action))
        conjunction = And([literal, gamma2])
        return Or([gamma1, conjunction])

    def _gamma(self, literal, action):
        disjunction = []
        for eff in action.effects:
            cond = eff.condition
            if eff.value.is_false():  
                eff = Not(eff.fluent)
            else:
                eff = eff.fluent         
            if literal == eff:
                if cond.is_true():
                    return TRUE() 
                disjunction.append(cond)
        if not disjunction:
            return False
        return Or(disjunction)

    def _regression(self, phi, action):
        if phi.is_false() or phi.is_true():
            return phi
        elif phi.is_fluent_exp():
            return self._gamma_substitution(phi, action)
        elif phi.is_or():
            return Or([self._regression(component, action) for component in phi.args])
        elif phi.is_and():
            return And([self._regression(component, action) for component in phi.args])
        elif phi.is_not():
            return Not(self._regression(phi.args[0], action))
        else:
            raise up.exceptions.UPUsageError("This compiler cannot handle this expression")
 

