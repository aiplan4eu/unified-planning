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
# copyright info is not up to date as of september 27th 2024
"""This module defines the interpreted functions effects remover class."""

from fractions import Fraction
from functools import partial
import itertools

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
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
)
from unified_planning.model.timing import StartTiming
from unified_planning.plans.plan import ActionInstance


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
        supported_kind.set_conditions_kind(
            "INTERPRETED_FUNCTIONS_IN_CONDITIONS"
        )  # added this
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
        supported_kind.set_expression_duration(
            "INTERPRETED_FUNCTIONS_IN_DURATIONS"
        )  # added this
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
        # supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        # supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")
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
        print("Compiling...")
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

        for a in problem.actions:
            print("-------------------------------------------------------------------")
            print("looping for a in problem actions")

            print("now on action")
            print(a)
            conds = []
            if_conds = []
            for t, c in self.get_conditions(a):
                ifuns = self.interpreted_functions_extractor.get(c)
                if ifuns:
                    if_conds.append((t, c, ifuns, False, False))
                else:
                    conds.append((t, c))

            lower, upper = None, None
            if isinstance(a, up.model.DurativeAction):
                lower = a.duration.lower
                ifuns = self.interpreted_functions_extractor.get(lower)
                if ifuns:
                    if_conds.append((StartTiming(), lower, ifuns, True, True))
                    lower = None
                upper = a.duration.upper
                ifuns = self.interpreted_functions_extractor.get(upper)
                if ifuns:
                    if_conds.append((StartTiming(), upper, ifuns, True, False))
                    upper = None

            for known in itertools.product([True, False], repeat=len(if_conds)):
                if not knowledge_compatible(if_conds, known, new_fluents.keys()):
                    print("this is not compatible with our knowledge")
                    print("we have to skip this case")
                    # is this ok?
                    continue
                new_params = []
                new_conds = []
                paramcounter = 0
                for (t, c, ifuns, is_duration, is_lower), k in zip(if_conds, known):
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
                            # in this case it means that this function has to be ocnsidered unknown
                            # and there are no known values to put as not in the condition
                            pass
                        if len(l2) != 0:
                            l1.append(em.Or(l2))
                    if k:
                        new_conds.append((t, em.And(l1)))
                        new_conds.extend(implies)
                        if is_duration:
                            if is_lower:
                                lower = c.substitute(subs)
                            else:
                                upper = c.substitute(subs)
                        else:
                            new_conds.append((t, c.substitute(subs)))
                    else:
                        if len(l1) != 0:
                            new_conds.append((t, em.Not(em.And(l1))))
                        if is_duration:
                            if is_lower:
                                lower = em.Real(Fraction(1, 1))
                            else:
                                upper = em.Real(Fraction(1000000, 1))

                new_a = self.clone_action_with_extra_params(
                    a, new_params, conds + new_conds, (lower, upper)
                )
                print("case:")
                for ifc, kv in zip(if_conds, known):
                    print(*ifc[2])
                    if kv:
                        print("known")
                    else:
                        print("unknown")
                print("---compiled action:")
                new_a.name = get_fresh_name(new_problem, a.name)
                print(new_a)
                new_problem.add_action(new_a)
                new_to_old[new_a] = a
        print("finished compiling!")

        return CompilerResult(
            new_problem, partial(custom_replace, map=new_to_old), self.name
        )

    def clone_action_with_extra_params(self, a, new_params, conditions, duration):
        # TODO - finish implementing this

        updated_parameters = OrderedDict(
            (param.name, param.type) for param in a.parameters
        )
        for n in new_params:
            updated_parameters[n.name] = n.type

            # following stuff has to be split between instantaneous and durative
        # new_instantaneous_action = InstantaneousAction(
        #    action.name, new_params, action.environment
        # )
        # for p in action.preconditions:
        #    new_instantaneous_action.add_precondition(p)
        # for eff in action.effects:
        #    new_instantaneous_action._add_effect_instance(eff.clone())
        # if action.simulated_effect is not None:
        #    new_instantaneous_action.set_simulated_effect(action.simulated_effect)

        new_action: Optional[
            up.model.DurativeAction | up.model.InstantaneousAction
        ] = None
        if isinstance(a, up.model.DurativeAction):
            new_durative_action = up.model.DurativeAction(
                a.name, updated_parameters, a.environment
            )
            for time in a.effects:
                effs = a.effects[time]
                for eff in effs:
                    new_durative_action._add_effect_instance(time, eff.clone())
            if a.simulated_effects is not None:
                for t, se in a.simulated_effects.items():
                    new_durative_action.set_simulated_effect(
                        t, se
                    )  # TODO - check if this is correct
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

            for eff in a.effects:
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
        print("new action:")
        print(new_action)
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

    def add_condition(self, a, t, c):
        raise NotImplementedError


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
    # this might want a tuple instad of a list
    if replaced_action is not None:
        return ActionInstance(
            replaced_action,
            new_list,
            action_instance.agent,
            action_instance.motion_paths,
        )
    else:
        return None


def knowledge_compatible(_ic, _k, _kl):
    retval = True
    for (t, c, ifuns, is_duration, is_lower), k in zip(_ic, _k):
        if k:
            for ifun in ifuns:
                if ifun.interpreted_function() not in _kl:
                    retval = False
    # TODO add skip for always false conditions (e.g. funx(a) known and funx (a) unknown)
    return retval
