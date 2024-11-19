# Copyright 2024 Unified Planning library and its maintainers
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
from typing import Dict, List, Optional, Union
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
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
    get_fresh_parameter_name,
)
from unified_planning.model.timing import StartTiming
from unified_planning.plans.plan import ActionInstance
from unified_planning.shortcuts import BoolType


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

        new_objects: Dict = {}
        new_fluents: Dict = {}
        if_known: Dict = {}
        for ifun_exp, val in self._interpreted_functions_values.items():
            ifun = ifun_exp.interpreted_function()
            if ifun not in if_known:
                if_known[ifun] = []
            if ifun not in new_fluents:
                f_name = get_fresh_name(new_problem, f"_f_{ifun.name}")
                f = Fluent(f_name, ifun.return_type, p=kNum)
                new_fluents[ifun] = f
                default_value = self._default_value_given_type(ifun.return_type)
                new_problem.add_fluent(f, default_initial_value=default_value)
            else:
                f = new_fluents[ifun]
            if tuple(ifun_exp.args) in new_objects:
                o = new_objects[tuple(ifun_exp.args)]
            else:
                o = Object(get_fresh_name(new_problem, f"_o"), kNum)
                new_objects[tuple(ifun_exp.args)] = o
                new_problem.add_object(o)
            if tuple(ifun_exp.args) not in if_known[ifun]:
                if_known[ifun].append(tuple(ifun_exp.args))
            new_problem.set_initial_value(f(o), val)

        has_changed_fluents: Dict = {}
        # NOTE - contents has_changed_fluents could be more optimal
        # now tracking fluents are added for all fluents that can change from any effect
        # in theory we do not need fluents that are completely isolated from IFs
        for a in problem.actions:
            # these fluents are created and added to the problem at the start as we
            # might need some of them before we encounter them during the compilation
            found_effects = self._get_effects(a)
            for time, ef in found_effects:
                f = ef.fluent.fluent()
                if f in has_changed_fluents.keys():
                    continue
                new_f_name = get_fresh_name(new_problem, f"_{f.name}_has_changed")
                new_f = Fluent(new_f_name, BoolType())
                new_problem.add_fluent(new_f, default_initial_value=False)
                new_problem.set_initial_value(new_f, em.FALSE())
                has_changed_fluents[f] = new_f

        for a in problem.actions:
            for new_params, dur, conds, effs in self._expand_action(
                a, new_fluents, new_objects, if_known, has_changed_fluents
            ):
                new_a = self._clone_action_with_extras(a, new_params, conds, dur, effs)
                new_a.name = get_fresh_name(new_problem, a.name)
                new_problem.add_action(new_a)
                new_to_old[new_a] = a

        old_goals = new_problem.goals
        new_problem.clear_goals()
        for goal_c in old_goals:
            # the goal is modified in order to handle situations where
            # the fluents contained in it have changed
            g_c = goal_c
            all_fluents_fnodes = self.free_vars_extractor.get(goal_c)
            all_fluents = []
            for f_fnode in all_fluents_fnodes:
                all_fluents.append(f_fnode.fluent())
            for k in has_changed_fluents.keys():
                if k in all_fluents:
                    g_c = em.Or(goal_c, has_changed_fluents[k])
            new_problem.add_goal(g_c)

        return CompilerResult(
            new_problem, partial(custom_replace, map=new_to_old), self.name
        )

    def _expand_action(
        self, a, new_fluents, new_objects, if_known, has_changed_fluents
    ):
        em = a.environment.expression_manager
        conds = []
        effs = []
        ifs = []
        for t, exp in self._get_conditions(a):
            all_fluent_exps = self.free_vars_extractor.get(exp)
            all_f = [f_exp.fluent() for f_exp in all_fluent_exps]
            extra_c = [hcf for f, hcf in has_changed_fluents.items() if f in all_f]
            new_c = em.Or([exp] + extra_c)
            ifuns = self.interpreted_functions_extractor.get(exp)
            if ifuns:
                ifs.append((t, new_c, ifuns, ElementKind.CONDITION, None))
            else:
                conds.append((t, new_c))
        for time, ef in self._get_effects(a):
            ifuns = self.interpreted_functions_extractor.get(ef.value)

            if ifuns:
                ifs.append((time, ef.value, ifuns, ElementKind.EFFECT, ef))
            else:
                f = ef.fluent.fluent()
                effs.append((time, ef))
                if f not in has_changed_fluents.keys():
                    continue
                # if the fluent is one of the changing ones
                # this action sets it to a (possibly) known value
                # so the tracking fluent is set to has_changed if at least one
                # of the fluents in value is tagged with has_changed

                f_list = [v.fluent() for v in self.free_vars_extractor.get(ef.value)]
                o_e = em.Or([em.FluentExp(has_changed_fluents[vf]) for vf in f_list])

                tracking_fluent_exp = em.FluentExp(has_changed_fluents[f])
                reset_tracker_eff = Effect(tracking_fluent_exp, o_e, em.TRUE())
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
            if not knowledge_compatible(ifs, known_vec, new_fluents.keys()):
                continue
            new_params: List = []
            new_conds: List = []
            new_effs: List = []
            i = 0
            for (t, exp, ifuns, case, eff_instance), known in zip(ifs, known_vec):
                subs = {}
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
                        p_n = get_fresh_parameter_name(a, f"_p_{ifun.name}_" + str(i))
                        new_param = up.model.Parameter(p_n, kNum)
                        new_params.append(new_param)
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
                            o = new_objects[p_known]
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
                        f = eff_instance.fluent.fluent()
                        tracking_f = em.FluentExp(has_changed_fluents[f])
                        reset_tracker_eff = Effect(tracking_f, em.FALSE(), em.TRUE())
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
                        tracking_f = em.FluentExp(has_changed_fluents[f])
                        n_e = Effect(tracking_f, em.TRUE(), em.TRUE())
                        new_effs.append((t, n_e))
            yield new_params, (lower, upper), conds + new_conds, effs + new_effs

    def _clone_action_with_extras(self, a, new_params, conditions, duration, effects):
        updated_params = OrderedDict((p.name, p.type) for p in a.parameters)
        for n in new_params:
            updated_params[n.name] = n.type

        new_a: Optional[Union[DurativeAction, InstantaneousAction]] = None
        if isinstance(a, DurativeAction):
            new_dur_a = DurativeAction(a.name, updated_params, a.environment)
            for time, eff in effects:
                new_dur_a._add_effect_instance(time, eff.clone())
            if a.simulated_effects is not None:
                for t, se in a.simulated_effects.items():
                    new_dur_a.set_simulated_effect(t, se)
            new_dur_a.clear_conditions()
            for ii, c in conditions:
                new_dur_a.add_condition(ii, c)
            new_dur_a.set_closed_duration_interval(duration[0], duration[1])
            new_a = new_dur_a
        elif isinstance(a, up.model.InstantaneousAction):
            new_ia = InstantaneousAction(a.name, updated_params, a.environment)
            for time, eff in effects:
                new_ia._add_effect_instance(eff.clone())
            if a.simulated_effect is not None:
                new_ia.set_simulated_effect(a.simulated_effect)
            new_ia.clear_preconditions()
            for c in conditions:
                new_ia.add_precondition(c[1])
            new_a = new_ia
        else:
            raise NotImplementedError

        return new_a

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

    def _get_effects(self, a):
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

    def _get_conditions(self, a):
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
    # the default replace can't handle a different number of parameters
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
    # returns true if no conflicts are found and we have the necessary knowledge about the IFs in question

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
