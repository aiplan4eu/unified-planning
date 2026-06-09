# Copyright 2024-2026 Unified Planning library and its maintainers
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
from enum import Enum, auto
from collections import OrderedDict
from typing import Dict, List, Optional, Union, Tuple, Iterable, FrozenSet, Set, Any
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
from unified_planning.model.action import DurativeAction, InstantaneousAction
from unified_planning.model.fluent import Fluent
from unified_planning.model.object import Object
from unified_planning.model.effect import Effect
from unified_planning.model.fnode import FNode
from unified_planning.model.types import Type
from unified_planning.model.expression import ExpressionManager
from unified_planning.model.parameter import Parameter
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
    get_fresh_parameter_name,
)
from unified_planning.model.timing import StartTiming, Timing, TimeInterval
from unified_planning.plans.plan import ActionInstance
from unified_planning.model.walkers import Simplifier
from unified_planning.exceptions import UPUnsupportedProblemTypeError
from unified_planning.model.interpreted_function import InterpretedFunction


class ElementKind(Enum):
    """
    ElementKind enum:
    this enum is used to identify in which situation an IF that is found during compilation is used
    """

    CONDITION = auto()
    DURATION_LOWER = auto()
    DURATION_UPPER = auto()
    EFFECT = auto()


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
        self._remove_quantifiers = lambda x: x

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
        supported_kind.set_effects_kind("INTERPRETED_FUNCTIONS_IN_OBJECT_ASSIGNMENTS")
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
        if new_kind.has_interpreted_functions_in_object_assignments():
            new_kind.unset_effects_kind("INTERPRETED_FUNCTIONS_IN_OBJECT_ASSIGNMENTS")
            new_kind.set_fluents_type("OBJECT_FLUENTS")

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
        eqr = up.model.walkers.ExpressionQuantifiersRemover(env)

        def _def_remove_quantifiers(exp):
            ifuns = self.interpreted_functions_extractor.get(exp)
            if not ifuns:
                return exp
            return eqr.remove_quantifiers(expression=exp, objects_set=new_problem)

        self._remove_quantifiers = _def_remove_quantifiers

        new_objects: Dict = {}
        new_obj_vals: Dict = {}
        new_fluents: Dict = {}
        if_known: Dict = {}
        kNums: Dict = {}
        for ifun_exp, val in self._interpreted_functions_values.items():
            ifun = ifun_exp.interpreted_function()
            if ifun in kNums:
                kNum = kNums[ifun]
            else:
                kNum = env.type_manager.UserType(
                    get_fresh_name(new_problem, f"kNum_{ifun.name}")
                )
                kNums[ifun] = kNum
            if ifun not in if_known:
                if_known[ifun] = []
            if ifun not in new_fluents:
                f_name = get_fresh_name(new_problem, f"_f_{ifun.name}")
                f = Fluent(f_name, ifun.return_type, p=kNum)
                new_fluents[ifun] = f
                default_value = self._default_value_given_type(
                    ifun.return_type, problem
                )
                new_problem.add_fluent(f, default_initial_value=default_value)
            else:
                f = new_fluents[ifun]
            if ifun_exp.interpreted_function() not in new_objects:
                new_objects[ifun_exp.interpreted_function()] = {}
            if ifun_exp.interpreted_function() not in new_obj_vals:
                new_obj_vals[ifun_exp.interpreted_function()] = {}
            if val in new_obj_vals[ifun_exp.interpreted_function()]:
                o = new_obj_vals[ifun_exp.interpreted_function()][val]
            else:
                o = Object(get_fresh_name(new_problem, f"_o_{kNum.name}"), kNum)
                new_obj_vals[ifun_exp.interpreted_function()][val] = o
                new_problem.add_object(o)

            if tuple(ifun_exp.args) in new_objects[ifun_exp.interpreted_function()]:
                pass
            else:
                new_objects[ifun_exp.interpreted_function()][tuple(ifun_exp.args)] = o
            if tuple(ifun_exp.args) not in if_known[ifun]:
                if_known[ifun].append(tuple(ifun_exp.args))
            new_problem.set_initial_value(f(o), val)

        is_unknown_fluents: Dict = {}
        changing_fluents = self._find_changing_fluents(problem)
        for f in changing_fluents:
            new_f_name = get_fresh_name(new_problem, f"_{f.name}_is_unknown")
            new_f = Fluent(new_f_name, env.type_manager.BoolType())
            new_problem.add_fluent(new_f, default_initial_value=False)
            new_problem.set_initial_value(new_f, em.FALSE())
            is_unknown_fluents[f] = new_f

        for a in problem.actions:
            for new_params, dur, conds, effs in self._expand_action(
                a, new_fluents, new_objects, if_known, is_unknown_fluents
            ):
                new_a = self._clone_action_with_extras(
                    a, new_params, dur, conds, effs, em
                )
                if new_a is None:
                    continue
                new_a.name = get_fresh_name(new_problem, a.name)
                new_problem.add_action(new_a)
                new_to_old[new_a] = a

        old_goals = new_problem.goals
        new_problem.clear_goals()
        for goal_c in old_goals:
            # the goal is modified in order to handle situations where
            # the fluents contained in it are unknown
            g_c = goal_c
            all_fluents_fnodes = self.free_vars_extractor.get(goal_c)
            all_fluents = []
            for f_fnode in all_fluents_fnodes:
                all_fluents.append(f_fnode.fluent())
            for k in is_unknown_fluents:
                if k in all_fluents:
                    g_c = em.Or(goal_c, is_unknown_fluents[k])
            new_problem.add_goal(g_c)

        return CompilerResult(
            new_problem, partial(custom_replace, map=new_to_old), self.name
        )

    def _expand_action(
        self,
        a: Action,
        new_fluents: Dict[InterpretedFunction, Fluent],
        new_objects: Dict[InterpretedFunction, Dict[Tuple[FNode], Object]],
        if_known: Dict[InterpretedFunction, List[Tuple[FNode]]],
        is_unknown_fluents: Dict[Fluent, Fluent],
    ) -> Iterable[
        Tuple[
            List[Parameter],
            Tuple[Optional[FNode], Optional[FNode]],
            List[Tuple[Optional[Union[Timing, TimeInterval]], FNode]],
            List[Tuple[Optional[Timing], Effect]],
        ]
    ]:
        """
        Computes the set of parameters, conditions, durations and effects for actions deriving from the action `a`
        NOTE that for InstantaneousActions all the time related fields will be None

        :param a: the action we are compiling that we need to expand into multiple actions to handle all the cases
        :param new_fluents: the dict containing fluents that substitute the interpred functions of known values
        :param new_objects: the dict that maps the interpreted functions with known values to the objects that represent the arguments with known values
        :param if_known: the dict that maps the interpreted functions with the list of arguments for which we know the values
        :param is_unknown_fluents: the dict that maps the fluents of the original problem to the new tracking fluents used to mark wether or not the value of the original fluents are currently known
        :returns: (yield) the parameters, durations, conditions and effects necessary to create the new compiled actions
        """
        em = a.environment.expression_manager
        conds = []
        effs = []
        ifs: List[
            Tuple[
                Optional[Union[Timing, TimeInterval]],
                FNode,
                FrozenSet[FNode],
                ElementKind,
                Optional[Effect],
            ]
        ] = []
        for t_interval, exp in self._get_conditions(a):
            all_fluent_exps = self.free_vars_extractor.get(exp)
            all_f = [f_exp.fluent() for f_exp in all_fluent_exps]
            extra_c = [hcf for f, hcf in is_unknown_fluents.items() if f in all_f]
            new_c = em.Or(extra_c + [exp])
            ifuns = self.interpreted_functions_extractor.get(exp)
            if ifuns:
                if t_interval is not None:
                    if t_interval.lower != t_interval.upper:
                        raise UPUnsupportedProblemTypeError(
                            "Interpreted Functions Remover does not support durative conditions that contain Interpreted Functions"
                        )
                ifs.append((t_interval, new_c, ifuns, ElementKind.CONDITION, None))
            else:
                conds.append((t_interval, new_c))
        for time, ef in self._get_effects(a):
            ifuns = self.interpreted_functions_extractor.get(ef.value)
            if ifuns:
                ifs.append((time, ef.value, ifuns, ElementKind.EFFECT, ef))
            else:
                effs.append((time, ef))
                f = ef.fluent.fluent()
                # only if the fluent is one of the changing ones
                # we need to set the tracker
                if f not in is_unknown_fluents:
                    continue
                reset_tracker_eff = self._create_tracking_effect(
                    ef, is_unknown_fluents, em
                )
                if reset_tracker_eff is not None:
                    effs.append((time, reset_tracker_eff))

        lower, upper = None, None
        if isinstance(a, up.model.DurativeAction):
            lower = a.duration.lower
            ifuns = self.interpreted_functions_extractor.get(lower)
            if ifuns:
                ifs.append(
                    (StartTiming(), lower, ifuns, ElementKind.DURATION_LOWER, None)
                )
                lower = None
            upper = a.duration.upper
            ifuns = self.interpreted_functions_extractor.get(upper)
            if ifuns:
                ifs.append(
                    (StartTiming(), upper, ifuns, ElementKind.DURATION_UPPER, None)
                )
                upper = None
        for known_vec in itertools.product([True, False], repeat=len(ifs)):
            if not knowledge_compatible(ifs, known_vec, list(new_fluents.keys())):
                continue
            new_params: List[Parameter] = []
            new_conds: List = []
            new_effs: List = []
            i = 0
            IF_and_pars_to_knum: Dict[
                tuple[InterpretedFunction, list[up.model.fnode.FNode]],
                up.model.Parameter,
            ] = {}
            IF_and_pars_and_timestamp_to_knum: Dict[
                tuple[
                    InterpretedFunction,
                    list[up.model.fnode.FNode],
                    Optional[Union[Timing, TimeInterval]],
                ],
                up.model.Parameter,
            ] = {}
            for (t, exp, ifuns, case, eff_instance), known in zip(ifs, known_vec):
                subs: Dict = {}
                implies = []
                l1 = []
                for ifun_exp in ifuns:
                    ifun = ifun_exp.interpreted_function()
                    if ifun not in if_known:
                        continue
                    if known:
                        i += 1
                        f = new_fluents[ifun]
                        kNum = f.signature[0].type
                        fluents_in_if_pars = self.free_vars_extractor.get(ifun_exp)
                        # if only pars -> map (ifun, [pars]) -> parameter object
                        # we don't have to worry about them changing over time
                        # if has fluents -> map (ifun, [pars], timestamp) -> parameter object
                        # at the same time we can use the same object, but different times might require different objects
                        if len(fluents_in_if_pars) > 0:
                            if (
                                ifun,
                                ifun_exp.args,
                                t,
                            ) not in IF_and_pars_and_timestamp_to_knum.keys():
                                p_n = get_fresh_parameter_name(
                                    a, f"_p_{ifun.name}_" + str(i)
                                )
                                new_param = up.model.Parameter(p_n, kNum)
                                new_params.append(new_param)
                                IF_and_pars_and_timestamp_to_knum[
                                    (ifun, ifun_exp.args, t)
                                ] = new_param
                            else:
                                new_param = IF_and_pars_and_timestamp_to_knum[
                                    (ifun, ifun_exp.args, t)
                                ]
                        else:
                            if (
                                ifun,
                                ifun_exp.args,
                            ) not in IF_and_pars_to_knum.keys():
                                p_n = get_fresh_parameter_name(
                                    a, f"_p_{ifun.name}_" + str(i)
                                )
                                new_param = up.model.Parameter(p_n, kNum)
                                new_params.append(new_param)
                                IF_and_pars_to_knum[(ifun, ifun_exp.args)] = new_param
                            else:
                                new_param = IF_and_pars_to_knum[(ifun, ifun_exp.args)]

                        subs[ifun_exp] = f(new_param)
                    l2 = []
                    for p_known in if_known[ifun]:
                        pf = em.And(
                            [
                                em.EqualsOrIff(v1, v2)
                                for v1, v2 in zip(ifun_exp.args, p_known)
                            ]
                        )
                        if known:
                            o = new_objects[ifun_exp.interpreted_function()][p_known]
                            implies.append((t, em.Implies(pf, em.Equals(new_param, o))))
                        l2.append(pf)
                    if len(l2) != 0:
                        l1.append(em.Or(l2))
                if known:
                    # in case we know the valus of the if
                    new_conds.append((t, em.And(l1)))
                    new_conds.extend(implies)
                    if case == ElementKind.DURATION_LOWER:
                        lower = exp.substitute(subs)
                    elif case == ElementKind.DURATION_UPPER:
                        upper = exp.substitute(subs)
                    elif case == ElementKind.EFFECT:
                        assert eff_instance is not None
                        n_e = eff_instance.clone()
                        n_e.set_value(exp.substitute(subs))
                        new_effs.append((t, n_e))
                        reset_tracker_eff = self._create_tracking_effect(
                            eff_instance, is_unknown_fluents, em
                        )
                        if reset_tracker_eff is not None:
                            new_effs.append((t, reset_tracker_eff))
                    elif case == ElementKind.CONDITION:
                        new_conds.append((t, exp.substitute(subs)))
                    else:
                        raise NotImplementedError
                else:
                    # in case we do not know the values of the if
                    if len(l1) != 0:
                        new_conds.append((t, em.Not(em.And(l1))))
                    if case == ElementKind.DURATION_LOWER:
                        lower = em.Real(Fraction(1, 1))
                    elif case == ElementKind.DURATION_UPPER:
                        upper = em.Real(Fraction(1000000, 1))
                    if case == ElementKind.EFFECT:
                        assert eff_instance is not None
                        f = eff_instance.fluent.fluent()
                        tracking_f = em.FluentExp(is_unknown_fluents[f])
                        n_e = Effect(tracking_f, em.TRUE(), em.TRUE())
                        new_effs.append((t, n_e))
            yield new_params, (lower, upper), conds + new_conds, effs + new_effs

    def _clone_action_with_extras(
        self,
        a: Action,
        new_params: List[Parameter],
        duration: Tuple[Optional[FNode], Optional[FNode]],
        conditions: List[Tuple[Optional[Union[Timing, TimeInterval]], FNode]],
        effects: List[Tuple[Optional[Timing], Effect]],
        em: ExpressionManager,
    ) -> Optional[Action]:
        """
        Creates a new action based on `a`, but with the new parameters, conditions, duration and effects, if no conflicts are found

        :param a: the action we want to start off from
        :param new_params: the new parameters that have to be added to the action
        :param duration: the duration (lower, upper) of the new action
        :param conditions: the conditions of the new action
        :param effects: the effects of the new action
        :param em: the problem's expression manager
        :returns: the newly created action
        """
        updated_params = OrderedDict((p.name, p.type) for p in a.parameters)
        for n in new_params:
            updated_params[n.name] = n.type

        new_a: Optional[Union[DurativeAction, InstantaneousAction]] = None
        if isinstance(a, DurativeAction):
            new_dur_a = DurativeAction(a.name, updated_params, a.environment)
            for time, eff in effects:
                assert time is not None
                new_dur_a._add_effect_instance(time, eff.clone())
            if a.simulated_effects is not None:
                for t, se in a.simulated_effects.items():
                    new_dur_a.set_simulated_effect(t, se)
            new_dur_a.clear_conditions()
            da_simp = Simplifier(new_dur_a.environment)
            for ii, c in conditions:
                simplified_c = da_simp.simplify(c)
                if simplified_c.is_bool_constant():
                    if simplified_c.constant_value() == False:
                        return None
                    elif simplified_c.constant_value() == True:
                        continue
                for nii, ncs in new_dur_a.conditions.items():
                    if nii == ii and em.Not(simplified_c) in ncs:
                        return None
                assert ii is not None
                new_dur_a.add_condition(ii, simplified_c)
            assert duration[0] is not None
            assert duration[1] is not None
            new_dur_a.set_closed_duration_interval(duration[0], duration[1])
            new_a = new_dur_a
        elif isinstance(a, up.model.InstantaneousAction):
            new_ia = InstantaneousAction(a.name, updated_params, a.environment)
            for time, eff in effects:
                new_ia._add_effect_instance(eff.clone())
            if a.simulated_effect is not None:
                new_ia.set_simulated_effect(a.simulated_effect)
            new_ia.clear_preconditions()
            ia_simp = Simplifier(new_ia.environment)
            for _, c in conditions:
                simplified_c = ia_simp.simplify(c)
                if simplified_c.is_bool_constant():
                    if simplified_c.constant_value() == False:
                        return None
                    elif simplified_c.constant_value() == True:
                        continue
                if em.Not(simplified_c) not in new_ia.preconditions:
                    new_ia.add_precondition(simplified_c)
                else:
                    return None
            new_a = new_ia
        else:
            raise NotImplementedError

        return new_a

    def _default_value_given_type(
        self, t: Type, problem: Problem
    ) -> Optional[Union[bool, int, Fraction, Object]]:
        """
        Return the default value for the type `t` in the Problem `problem`

        :param t: the Type object we need the default value of
        :param problem: the problem we want the default value of the type for (only matters for UserTypes)
        :returns: the default value
        """
        if t.is_bool_type():
            return False
        elif t.is_int_type() or t.is_real_type():
            assert hasattr(t, "lower_bound")
            assert hasattr(t, "upper_bound")
            c = int if t.is_int_type() else Fraction
            if t.lower_bound is None:
                if t.upper_bound is None:
                    return c(0)
                else:
                    return c(t.upper_bound - 1)
            else:
                if t.upper_bound is None:
                    return c(t.lower_bound + 1)
                else:
                    return c((t.upper_bound + t.lower_bound) / 2)
        elif t.is_user_type():
            try:
                return next(problem.objects(t))
            except StopIteration:
                return None
        else:
            raise NotImplementedError

    def _find_changing_fluents(self, problem: Problem) -> Set[Fluent]:
        """
        Finds the set of fluents that can be modifyed by effects with interpreted functions

        :param problem: the problem we want to find the changing fluents in
        :returns: the set of
        """
        found_fluents_set: set[up.model.Fluent] = set()
        len_start = 0
        len_end = 1
        while len_end > len_start:
            len_start = len(found_fluents_set)
            for a in problem.actions:
                found_effects = self._get_effects(a)
                for _, ef in found_effects:
                    f = ef.fluent.fluent()
                    v = ef.value
                    ifs = self.interpreted_functions_extractor.get(v)
                    if ifs:
                        found_fluents_set.add(f)
                    else:
                        fs_e = self.free_vars_extractor.get(v)
                        for f_e in fs_e:
                            if f_e.fluent() in found_fluents_set:
                                found_fluents_set.add(f)
            len_end = len(found_fluents_set)
        return found_fluents_set

    def _create_tracking_effect(
        self,
        ef: Effect,
        is_unknown_fluents: Dict[Fluent, Fluent],
        em: ExpressionManager,
    ) -> Optional[Effect]:
        """
        Creates, if necessary, a new tracking effect that sets the tracking fluent to unknown if at least one of the fluents in the value is unknown

        :param ef: the effect that might cause a value to become unknown
        :param is_unknown_fluents: the dict that maps the tracking fluents to the ones they track
        :param em: the problem's expression manager
        :return: the newely created effect
        """
        f = ef.fluent.fluent()
        f_list = []
        for v in self.free_vars_extractor.get(ef.value):
            if v.fluent() in is_unknown_fluents:
                f_list.append(v.fluent())

        o_e = em.Or([em.FluentExp(is_unknown_fluents[vf]) for vf in f_list])
        tracking_fluent_exp = em.FluentExp(is_unknown_fluents[f])

        if tracking_fluent_exp == o_e:
            return None

        reset_tracker_eff = Effect(tracking_fluent_exp, o_e, em.TRUE())
        return reset_tracker_eff

    def _get_effects(self, a: Action) -> Iterable[Tuple[Optional[Timing], Effect]]:
        """
        Computes the list of times and effects for all effects for action `a`.
        In the case of InstantaneousActions the times will be None

        :param a: the action we want to extract the effects from
        :returns: the zip iterable of tuples (time, effect)
        """
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

    def _get_conditions(
        self, a: Action
    ) -> Iterable[Tuple[Optional[TimeInterval], FNode]]:
        """
        Computes the list of times and conditions for all conditions for action `a`.
        In the case of InstantaneousActions the times will be None

        :param a: the action we want to extract the conditions from
        :returns: the zip iterable of tuples (time, condition)
        """
        cond_list: list = []
        time_list: list = []
        if isinstance(a, DurativeAction):
            a_conditions = a.conditions.items()
            for ii, cl in a_conditions:
                for c in cl:
                    fixed_c_list = _split_ands(self._remove_quantifiers(c))
                    for fc in fixed_c_list:
                        cond_list.append(fc)
                        time_list.append(ii)
        else:
            assert isinstance(a, InstantaneousAction)
            a_preconditions = a.preconditions
            for p in a_preconditions:
                fixed_p_list = _split_ands(self._remove_quantifiers(p))
                for fp in fixed_p_list:
                    cond_list.append(fp)
                    time_list.append(None)
        return zip(time_list, cond_list)


def _split_ands(e: FNode) -> List[FNode]:
    """
    Given an expression `e`, returns [a, b] if e was in the form `a AND b`, returns [e] otherwise

    :param e: the expression we want to split
    :returns: the list of expressions after splitting
    """
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
    """
    This is the modified `replace_action` function,
    as the one in utils does not handle actions with different number of parameters
    """
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


def knowledge_compatible(
    ifs: List[
        Tuple[Optional[Union[Timing, TimeInterval]], Any, FrozenSet[FNode], Any, Any]
    ],
    known: Tuple[bool, ...],
    key_list: List[InterpretedFunction],
) -> bool:
    """
    Checks if we have some values for the desired combination of known interpreted functions and no conflicts are found

    Example of a conflict could be an interpreted function to be considered known in a condition at time t, but unknown in an effect at the same time t
    :param ifs: the list of tuples with all the instances of an interpreted function appearing
    :param known: the list of booleans with the same length as ifs for this case we want to check
    :param key_list: the list of interpreted functions we have known values for
    :return: true if no problems are foud, false otherwise
    """

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
