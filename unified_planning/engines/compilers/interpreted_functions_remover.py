# Copyright 2021-2023 AIPlan4EU project
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
"""This module defines the interpreted functions remover class."""

from fractions import Fraction
from functools import partial
import itertools
from enum import Enum
from collections import OrderedDict
from typing import Dict, Optional
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.exceptions import UPUsageError
from unified_planning.model import (
    Problem,
    ProblemKind,
    Action,
)
from unified_planning.model.fluent import Fluent
from unified_planning.model.mixins.timed_conds_effs import TimedCondsEffs
from unified_planning.model.object import Object
from unified_planning.model.effect import Effect
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
)
from unified_planning.model.timing import StartTiming
from unified_planning.plans.plan import ActionInstance
from unified_planning.shortcuts import BoolType


class c_type(Enum):
    CONDITION = 1
    DURATION_LOWER = 2
    DURATION_UPPER = 3
    EFFECT = 4


class InterpretedFunctionsRemover(engines.engine.Engine, CompilerMixin):
    """
    Interpreted functions remover class: this class offers the capability
    to transform a :class:`~unified_planning.model.Problem` with interpreted functions used as conditions`
    into a `Problem` without interpreted functions in action conditions. This capability is offered by the :meth:`~unified_planning.engines.compilers.InterpretedFunctionsRemover.compile`
    method, that returns a :class:`~unified_planning.engines.CompilerResult` in which the :meth:`problem <unified_planning.engines.CompilerResult.problem>` field
    is the compiled Problem.

    This is done by changing every evaluation of an expression that contains an interpreted function to true.

    This `Compiler` supports only the the `INTERPRETED_FUNCTIONS_REMOVER` :class:`~unified_planning.engines.CompilationKind`.
    """

    def __init__(self, interpreted_functions_values=None):
        engines.engine.Engine.__init__(self)
        self.operators_extractor: up.model.walkers.OperatorsExtractor = (
            up.model.walkers.OperatorsExtractor()
        )
        self.interpreted_functions_extractor: up.model.walkers.InterpretedFunctionsExtractor = (
            up.model.walkers.InterpretedFunctionsExtractor()
        )
        self.names_extractor: up.model.walkers.NamesExtractor = (
            up.model.walkers.NamesExtractor()
        )
        self.free_vars_extractor: up.model.walkers.FreeVarsExtractor = (
            up.model.walkers.FreeVarsExtractor()
        )
        self._use_old_algorithm = False
        self._interpreted_functions_values = interpreted_functions_values

        CompilerMixin.__init__(self, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING)

    @property
    def name(self):
        return "ifrm"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("REAL_ACTION_PARAMETERS")
        supported_kind.set_numbers("BOUNDED_TYPES")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_fluents_type("INT_FLUENTS")
        supported_kind.set_fluents_type("REAL_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("INTERPRETED_FUNCTIONS_IN_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FORALL_EFFECTS")
        supported_kind.set_effects_kind("INTERPRETED_FUNCTIONS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("INTERPRETED_FUNCTIONS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECTS")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_time("SELF_OVERLAPPING")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("INT_TYPE_DURATIONS")
        supported_kind.set_expression_duration("REAL_TYPE_DURATIONS")
        supported_kind.set_expression_duration("INTERPRETED_FUNCTIONS_IN_DURATIONS")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_constraints_kind("STATE_INVARIANTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= InterpretedFunctionsRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.INTERPRETED_FUNCTIONS_REMOVING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        assert isinstance(problem_kind, ProblemKind)
        new_kind = problem_kind.clone()
        if new_kind.has_interpreted_functions_in_conditions():
            new_kind.unset_conditions_kind("INTERPRETED_FUNCTIONS_IN_CONDITIONS")
        if new_kind.has_interpreted_functions_in_durations():
            new_kind.unset_expression_duration("INTERPRETED_FUNCTIONS_IN_DURATIONS")
            new_kind.set_expression_duration("INT_TYPE_DURATIONS")
        if new_kind.has_interpreted_functions_in_boolean_assignments():
            new_kind.unset_effects_kind("INTERPRETED_FUNCTIONS_IN_BOOLEAN_ASSIGNMENTS")
        if new_kind.has_interpreted_functions_in_numeric_assignments():
            new_kind.unset_effects_kind("INTERPRETED_FUNCTIONS_IN_NUMERIC_ASSIGNMENTS")

        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """
        :param problem: The instance of the :class:`~unified_planning.model.Problem` that must be compiled.
        :param compilation_kind: The :class:`~unified_planning.engines.CompilationKind` that must be applied on the given problem;
            only :class:`~unified_planning.engines.CompilationKind.INTERPRETED_FUNCTIONS_REMOVER` is supported by this compiler
        :return: The resulting :class:`~unified_planning.engines.results.CompilerResult` data structure.
        :raises: :exc:`~unified_planning.exceptions.UPProblemDefinitionError` when the :meth:`condition<unified_planning.model.Effect.condition>` of an
            :class:`~unified_planning.model.Effect` can't be removed without changing the :class:`~unified_planning.model.Problem` semantic.
        """
        assert isinstance(problem, Problem)
        env = problem.environment
        em = env.expression_manager

        if self._interpreted_functions_values is None:
            self._interpreted_functions_values = OrderedDict()

        new_to_old: Dict[Action, Optional[Action]] = {}
        new_problem = problem.clone()

        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_actions()

        kNum = env.type_manager.UserType(get_fresh_name(new_problem, "kNum"))

        new_objects: dict = {}
        new_fluents: dict = {}
        if_known: dict = {}
        for ifun_exp, val in self._interpreted_functions_values.items():
            # this does not add the functions we have not found with the validator yet
            ifun = ifun_exp.interpreted_function()
            if ifun not in if_known:
                if_known[ifun] = []
            if ifun not in new_fluents:
                f = Fluent(
                    get_fresh_name(new_problem, f"_f_{ifun.name}"),
                    ifun.return_type,
                    p=kNum,
                )
                new_fluents[ifun] = f
                new_problem.add_fluent(
                    f,
                    default_initial_value=self._default_value_given_type(
                        ifun.return_type
                    ),
                )
            else:
                f = new_fluents[ifun]

            if tuple(ifun_exp.args) in new_objects:
                o = new_objects[tuple(ifun_exp.args)]
            else:
                if_known[ifun].append(tuple(ifun_exp.args))
                o = Object(get_fresh_name(new_problem, f"_o"), kNum)
                new_objects[tuple(ifun_exp.args)] = o
                new_problem.add_object(o)
            new_problem.set_initial_value(f(o), val)

        assignment_tracking_fluents: dict = {}
        for a in problem.actions:
            found_effects = self.get_effects(a)
            for time, ef in found_effects:
                if ef.fluent.fluent() not in assignment_tracking_fluents.keys():
                    ifuns = self.interpreted_functions_extractor.get(ef.value)
                    if len(ifuns) != 0:
                        new_f_name = get_fresh_name(
                            new_problem,
                            "_" + str(ef.fluent.fluent().name) + "_has_changed",
                        )
                        f = Fluent(new_f_name, BoolType())
                        new_problem.add_fluent(f, default_initial_value=False)
                        new_problem.set_initial_value(f, em.FALSE())
                        assignment_tracking_fluents[ef.fluent.fluent()] = f
        for a in problem.actions:
            conds = []
            effs = []
            ifs = []
            for t, c in self.get_conditions(a):
                new_c = c
                all_fluents_fnodes = self.free_vars_extractor.get(c)
                all_fluents = []
                for f_fnode in all_fluents_fnodes:
                    all_fluents.append(f_fnode.fluent())
                for k in assignment_tracking_fluents.keys():
                    if k in all_fluents:
                        new_c = em.Or(new_c, assignment_tracking_fluents[k])

                ifuns = self.interpreted_functions_extractor.get(new_c)
                if ifuns:
                    ifs.append((t, new_c, ifuns, c_type.CONDITION, None))
                else:
                    conds.append((t, new_c))

            for time, ef in self.get_effects(a):
                ifuns = self.interpreted_functions_extractor.get(ef.value)
                if len(ifuns) != 0:
                    ifs.append((time, ef.value, ifuns, c_type.EFFECT, ef))

                else:

                    # if effect assigns value to an unknown fluent, put tracker back to known state
                    # TODO - fix cascade effect that might lead to incorrect results
                    # cascade effect is preset not only here

                    effs.append((time, ef))
                    if ef.fluent.fluent() in assignment_tracking_fluents.keys():
                        # if the fluent is one of the changing ones
                        # this action sets it to a (possibly) known value

                        tracking_fluent_expression = em.FluentExp(
                            assignment_tracking_fluents[ef.fluent.fluent()]
                        )
                        reset_tracker_eff = Effect(
                            tracking_fluent_expression, em.FALSE(), em.TRUE()
                        )
                        effs.append((time, reset_tracker_eff))
            lower, upper = None, None
            if isinstance(a, up.model.DurativeAction):
                lower = a.duration.lower
                ifuns = self.interpreted_functions_extractor.get(lower)
                if ifuns:
                    ifs.append(
                        (StartTiming(), lower, ifuns, c_type.DURATION_LOWER, None)
                    )
                    lower = None
                upper = a.duration.upper
                ifuns = self.interpreted_functions_extractor.get(upper)
                if ifuns:
                    ifs.append(
                        (StartTiming(), upper, ifuns, c_type.DURATION_UPPER, None)
                    )
                    upper = None

            for known in itertools.product([True, False], repeat=len(ifs)):
                if not knowledge_compatible(ifs, known, new_fluents.keys()):
                    continue
                new_params = []
                new_conds = []
                new_effs: list = []
                paramcounter = 0
                for (t, c, ifuns, case, eff_instance), k in zip(ifs, known):
                    subs = {}
                    implies = []
                    l1 = []
                    for ifun in ifuns:
                        if k:
                            paramcounter = paramcounter + 1
                            new_param = up.model.Parameter(
                                get_fresh_name(
                                    new_problem,
                                    f"_p_{ifun.interpreted_function().name}_"
                                    + str(paramcounter),
                                ),
                                kNum,
                            )
                            new_params.append(new_param)
                            f = new_fluents[ifun.interpreted_function()]
                            subs[ifun] = f(new_param)
                        l2 = []
                        if ifun.interpreted_function() in if_known.keys():

                            for p_known in if_known[ifun.interpreted_function()]:
                                pf = em.And(
                                    [
                                        self.EqualsOrIff(v1, v2, em)
                                        for v1, v2 in zip(ifun.args, p_known)
                                    ]
                                )
                                if k:
                                    ob = new_objects[p_known]
                                    implies.append(
                                        (t, em.Implies(pf, em.Equals(new_param, ob)))
                                    )
                                l2.append(pf)
                        else:
                            pass
                        if len(l2) != 0:
                            l1.append(em.Or(l2))
                    if k:
                        # in case we know the valus of the if
                        new_conds.append((t, em.And(l1)))
                        new_conds.extend(implies)
                        if case == c_type.DURATION_LOWER:
                            lower = c.substitute(subs)
                        elif case == c_type.DURATION_UPPER:
                            upper = c.substitute(subs)
                        elif case == c_type.EFFECT:
                            assert eff_instance is not None
                            n_e_v = c.substitute(subs)
                            n_e = eff_instance.clone()
                            n_e.set_value(n_e_v)
                            new_effs.append((t, n_e))
                            tracking_fluent_expression = em.FluentExp(
                                assignment_tracking_fluents[
                                    eff_instance.fluent.fluent()
                                ]
                            )
                            reset_tracker_eff = Effect(
                                tracking_fluent_expression, em.FALSE(), em.TRUE()
                            )
                            new_effs.append((t, reset_tracker_eff))
                        elif case == c_type.CONDITION:
                            new_conds.append((t, c.substitute(subs)))
                        else:
                            raise NotImplementedError
                    else:
                        # in case we do not know the values of the if
                        if len(l1) != 0:
                            new_conds.append((t, em.Not(em.And(l1))))
                        if case == c_type.DURATION_LOWER:
                            lower = em.Real(Fraction(1, 1))
                        elif case == c_type.DURATION_UPPER:
                            upper = em.Real(Fraction(1000000, 1))
                        if case == c_type.EFFECT:
                            assert eff_instance is not None
                            tracking_fluent_expression = em.FluentExp(
                                assignment_tracking_fluents[
                                    eff_instance.fluent.fluent()
                                ]
                            )
                            n_e = Effect(
                                tracking_fluent_expression, em.TRUE(), em.TRUE()
                            )
                            new_effs.append((t, n_e))

                new_a = self.clone_action_with_extras(
                    a, new_params, conds + new_conds, (lower, upper), effs + new_effs
                )
                new_a.name = get_fresh_name(new_problem, a.name)
                new_problem.add_action(new_a)
                new_to_old[new_a] = a

        old_goals = new_problem.goals
        new_problem.clear_goals()
        for goal_c in old_goals:
            g_c = goal_c
            all_fluents_fnodes = self.free_vars_extractor.get(goal_c)
            all_fluents = []
            for f_fnode in all_fluents_fnodes:
                all_fluents.append(f_fnode.fluent())
            for k in assignment_tracking_fluents.keys():
                if k in all_fluents:
                    g_c = em.Or(goal_c, assignment_tracking_fluents[k])
            new_problem.add_goal(g_c)
        return CompilerResult(
            new_problem, partial(custom_replace, map=new_to_old), self.name
        )

    def clone_action_with_extras(self, a, new_params, conditions, duration, effects):

        updated_parameters = OrderedDict(
            (param.name, param.type) for param in a.parameters
        )
        for n in new_params:
            updated_parameters[n.name] = n.type

        new_action: Optional[
            up.model.DurativeAction | up.model.InstantaneousAction
        ] = None
        if isinstance(a, up.model.DurativeAction):
            new_durative_action = up.model.DurativeAction(
                a.name, updated_parameters, a.environment
            )
            for time, eff in effects:
                new_durative_action._add_effect_instance(time, eff.clone())
            if a.simulated_effects is not None:
                for t, se in a.simulated_effects.items():
                    new_durative_action.set_simulated_effect(t, se)
            new_durative_action.clear_conditions()
            for ii, c in conditions:
                new_durative_action.add_condition(ii, c)
            new_lower = duration[0]
            new_upper = duration[1]
            new_durative_action.set_closed_duration_interval(new_lower, new_upper)
            new_action = new_durative_action
        elif isinstance(a, up.model.InstantaneousAction):
            new_instantaneous_action = up.model.InstantaneousAction(
                a.name, updated_parameters, a.environment
            )
            for time, eff in effects:
                new_instantaneous_action._add_effect_instance(eff.clone())
            if a.simulated_effect is not None:
                new_instantaneous_action.set_simulated_effect(a.simulated_effect)

            not_timed_conditions = []
            for c in conditions:
                not_timed_conditions.append(c[1])
            new_instantaneous_action.clear_preconditions()
            for c in not_timed_conditions:
                new_instantaneous_action.add_precondition(c)
            new_action = new_instantaneous_action
        else:
            raise NotImplementedError
        return new_action

    def EqualsOrIff(self, v1, v2, manager):
        ret_exp = None
        if v1.type.is_bool_type():
            ret_exp = manager.Iff(v1, v2)
        else:
            ret_exp = manager.Equals(v1, v2)
        return ret_exp

    def _default_value_given_type(self, t):
        if t.is_bool_type():
            return False
        if t.is_int_type():
            if t.lower_bound is None:
                return 0
            else:
                return t.lower_bound
        if t.is_real_type():
            if t.lower_bound is None:
                return Fraction(0, 1)
            else:
                return t.lower_bound
        else:
            raise NotImplementedError

    def get_effects(self, a):
        eff_list: list = []
        time_list: list = []
        if isinstance(a, up.model.InstantaneousAction):
            i_aeffs = a.effects
            for aeff in i_aeffs:
                eff_list.append(aeff)
                time_list.append(None)
        elif isinstance(a, up.model.DurativeAction):
            d_aeffs = a.effects
            for time in d_aeffs:
                for eff in d_aeffs[time]:
                    eff_list.append(eff)
                    time_list.append(time)
        else:
            raise NotImplementedError
        return zip(time_list, eff_list)

    def get_conditions(self, a):
        cond_list: list = []
        time_list: list = []
        if isinstance(a, up.model.DurativeAction):
            a_conditions = a.conditions.items()
            for ii, cl in a_conditions:
                for c in cl:
                    fixed_c_list = _split_ands(c)
                    for fc in fixed_c_list:
                        cond_list.append(fc)
                        time_list.append(ii)
        else:
            a_preconditions = a.preconditions
            for p in a_preconditions:
                fixed_p_list = _split_ands(p)
                for fp in fixed_p_list:
                    cond_list.append(fp)
                    time_list.append(None)
        return zip(time_list, cond_list)


def _split_ands(e):
    templist = []
    if e.is_and():
        for sub in e.args:
            templist.append(sub)
    else:
        templist.append(e)
    return templist


def custom_replace(
    action_instance: ActionInstance,
    map: Dict["up.model.Action", Optional["up.model.Action"]],
) -> Optional[ActionInstance]:
    try:
        replaced_action = map[action_instance.action]
    except KeyError:
        raise UPUsageError(
            "The Action of the given ActionInstance does not have a valid replacement."
        )
    expected_amount = 0
    if replaced_action is not None:
        if replaced_action.parameters is not None:
            expected_amount = len(replaced_action.parameters)

    new_list: list = list()
    i = 0
    while i < expected_amount:
        new_list.append(action_instance.actual_parameters[i])
        i = i + 1
    if replaced_action is not None:
        return ActionInstance(
            replaced_action,
            new_list,
            action_instance.agent,
            action_instance.motion_paths,
        )
    else:
        return None


def knowledge_compatible(ifs, known, key_list):
    retval = True
    kifuns = []
    ukifuns = []
    for (t, _, ifuns, _, _), k in zip(ifs, known):
        if k:
            for ifun in ifuns:
                if (t, ifun) in ukifuns:
                    retval = False
                else:
                    kifuns.append((t, ifun))

                if ifun.interpreted_function() not in key_list:
                    retval = False
        else:
            for ifun in ifuns:
                if (t, ifun) in kifuns:
                    retval = False
                else:
                    ukifuns.append((t, ifun))

    return retval
