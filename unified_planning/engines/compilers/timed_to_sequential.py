# Copyright 2025 Unified Planning library and its maintainers
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
"""This module defines the timed to sequential problem converter class."""

import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    Problem,
    ProblemKind,
    InstantaneousAction,
    DurativeAction,
    Action,
    Effect,
    State,
    UPState,
    ExpressionManager,
    Fluent,
    FNode,
)
from unified_planning.model.timing import StartTiming, EndTiming, Interval
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.compilers.utils import replace_action
from typing import Dict, Optional, List, Tuple, OrderedDict, cast
from fractions import Fraction
from functools import partial
from unified_planning.exceptions import (
    UPUnsupportedProblemTypeError,
    UPUsageError,
    UPUnreachableCodeError,
)
from unified_planning.model.walkers.free_vars import FreeVarsExtractor
from unified_planning.model.walkers.simplifier import Simplifier
from unified_planning.plans import (
    SequentialPlan,
    TimeTriggeredPlan,
    ActionInstance,
    Plan,
)
from unified_planning.model.problem_kind import FEATURES
from unified_planning.engines import UPSequentialSimulator


def plan_back_conversion_callable(
    sp: SequentialPlan, problem: Problem, new_problem: Problem, new_to_old: Dict
):
    if not isinstance(sp, SequentialPlan):
        raise UPUsageError("Plan to map back is not sequential")
    if problem.epsilon is not None:
        min_time_step = problem.epsilon
    else:
        min_time_step = Fraction(1, 100)
    simulator = UPSequentialSimulator(new_problem)
    simplifier = Simplifier(problem.environment)
    fve = FreeVarsExtractor()
    state: Optional[State] = simulator.get_initial_state()
    assert isinstance(state, UPState)
    time_now = Fraction(0)
    ttptuples: List[Tuple[Fraction, ActionInstance, Optional[Fraction]]] = []
    for action_instance in sp.actions:
        if action_instance.action not in new_to_old:
            raise UPUsageError(
                f"Action {action_instance.action.name} not found during compilation is present in this plan"
            )
        action_for_mapback = new_to_old[action_instance.action]
        assert action_for_mapback is not None
        new_action_instance = ActionInstance(
            action=action_for_mapback,
            params=action_instance.actual_parameters,
            agent=action_instance.agent,
            motion_paths=action_instance.motion_paths,
        )
        if isinstance(action_for_mapback, DurativeAction):
            tinterval = action_for_mapback.duration
            assert isinstance(tinterval, Interval)
            dtime = min_time_step
            if not tinterval.is_left_open():
                if tinterval.lower.is_constant():
                    dtime = Fraction(tinterval.lower.constant_value())
                else:
                    par_sub_dict: Dict = {}
                    for paramname, paramvalue in zip(
                        action_for_mapback.parameters,
                        action_instance.actual_parameters,
                    ):
                        par_sub_dict[paramname] = paramvalue
                    tlower_with_pars = tinterval.lower.substitute(par_sub_dict)
                    flu_subs_dict: Dict = {}
                    for flu_obj in fve.get(tlower_with_pars):
                        flu_subs_dict[flu_obj] = state.get_value(flu_obj)
                    tlower_constant = simplifier.simplify(
                        tlower_with_pars.substitute(flu_subs_dict)
                    )
                    dtime = Fraction(tlower_constant.constant_value())
            else:
                # NOTE if open use min step
                dtime = min_time_step
            ttptuples.append((time_now, new_action_instance, dtime))
            time_now = time_now + dtime + min_time_step
        elif isinstance(action_for_mapback, InstantaneousAction):
            ttptuples.append((time_now, new_action_instance, None))
            time_now = time_now + min_time_step
        else:
            # NOTE this should not happen as other kinds of transitions are not supported
            raise UPUsageError
        state = simulator.apply(cast(State, state), action_instance)
        assert state is not None
    ttp = TimeTriggeredPlan(ttptuples)
    return ttp


class TimedToSequential(engines.engine.Engine, CompilerMixin):
    """
    Timed to Sequential compiler class: this class offers the capability to
    transform a problem with durative actions into one only using instantaneous actions.
    Every durative action is compiled into an instantaneous action by condensing
    all all conditions at start time and all effects at end time.
    """

    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.TIMED_TO_SEQUENTIAL)

    @property
    def name(self):
        return "t2s"

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
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
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
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_expression_duration("INT_TYPE_DURATIONS")
        supported_kind.set_expression_duration("REAL_TYPE_DURATIONS")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATIONS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= TimedToSequential.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.TIMED_TO_SEQUENTIAL

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = problem_kind.clone()
        for timefeat in FEATURES["TIME"]:
            new_kind.unset_time(timefeat)
        for durfeat in FEATURES["EXPRESSION_DURATION"]:
            new_kind.unset_expression_duration(durfeat)
        return new_kind

    def get_effects_data_structures(
        self, action: DurativeAction, em: ExpressionManager, fve: FreeVarsExtractor
    ) -> Tuple[Dict, Dict[Fluent, List[Effect]], Dict[Fluent, List[Effect]]]:
        old_end_effects: Dict = {}
        old_start_effects: Dict = {}
        for timepoint, oel in action.effects.items():
            if timepoint == StartTiming():
                for oe in oel:
                    if oe.fluent not in old_start_effects.keys():
                        old_start_effects[oe.fluent] = []
                    old_start_effects[oe.fluent].append(oe)
            elif timepoint == EndTiming():
                for oe in oel:
                    if oe.fluent not in old_end_effects.keys():
                        old_end_effects[oe.fluent] = []
                    old_end_effects[oe.fluent].append(oe)
            else:
                raise UPUnsupportedProblemTypeError(
                    "Intermediate effects are not supported"
                )
        start_effects_subs = self.get_start_effects_substitutions(
            action=action,
            old_start_effects=old_start_effects,
            old_end_effects=old_end_effects,
            fve=fve,
            em=em,
        )
        return start_effects_subs, old_start_effects, old_end_effects

    def get_start_effects_substitutions(
        self,
        action: DurativeAction,
        old_start_effects: Dict[Fluent, List[Effect]],
        old_end_effects: Dict[Fluent, List[Effect]],
        fve: FreeVarsExtractor,
        em: ExpressionManager,
    ):
        start_effects_subs: Dict = {}
        for osef, osel in old_start_effects.items():
            start_effects_subs[osef] = osef
            for ose in osel:
                assert isinstance(ose, Effect)
                if not ose.condition == em.TRUE():
                    dangerous_fluent = ose.fluent
                    for tinterval, ocl in action.conditions.items():
                        if tinterval.upper == EndTiming():
                            # postconds and invariants (time upper = end)
                            for oc in ocl:
                                if dangerous_fluent in fve.get(oc):
                                    raise UPUnsupportedProblemTypeError(
                                        "start time conditional effects that affect fluents used in invariants/post conditions are not supported"
                                    )
                    for oeel in old_end_effects.values():
                        for oee in oeel:
                            if oee.is_increase() or oee.is_decrease():
                                # fluent and value sides of inc/dec posteffs
                                if dangerous_fluent in fve.get(
                                    oee.fluent
                                ) or dangerous_fluent in fve.get(oee.value):
                                    raise UPUnsupportedProblemTypeError(
                                        "start time conditional effects that affect increase/descrease effects at end time are not supported"
                                    )
                            else:
                                # value side of assign posteffs
                                if dangerous_fluent in fve.get(oee.value):
                                    raise UPUnsupportedProblemTypeError(
                                        "start time conditional effects that affect values of effects at end time are not supported"
                                    )
                if ose.is_assignment():
                    # NOTE we should never find assignments associated with any other kind of effect
                    start_effects_subs[ose.fluent] = ose.value
                elif ose.is_increase():
                    start_effects_subs[ose.fluent] = em.Plus(
                        start_effects_subs[ose.fluent], ose.value
                    )
                elif ose.is_decrease():
                    start_effects_subs[ose.fluent] = em.Minus(
                        start_effects_subs[ose.fluent], ose.value
                    )
                else:
                    raise UPUnreachableCodeError
        return start_effects_subs

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """
        Takes an instance of a (timed) :class:`~unified_planning.model.Problem` that contains Durative Actions
        and returns a :class:`~unified_planning.engines.results.CompilerResult` where the :meth:`problem<unified_planning.engines.results.CompilerResult.problem>`
        field instead only contains instantaneous actions (sequential problem).

        :param problem: The instance of the :class:`~unified_planning.model.Problem` that must be returned without state innvariants.
        :param compilation_kind: The :class:`~unified_planning.engines.CompilationKind` that must be applied on the given problem (optional);
            only :class:`~unified_planning.engines.CompilationKind.TIMED_TO_SEQUENTIAL` is supported by this compiler
        :return: The resulting :class:`~unified_planning.engines.results.CompilerResult` data structure.
        """
        assert isinstance(problem, Problem)
        env = problem.environment
        em = env.expression_manager
        fve = FreeVarsExtractor()

        new_to_old: Dict[Action, Optional[Action]] = {}

        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"

        new_problem.clear_actions()

        for action in problem.actions:
            if isinstance(action, InstantaneousAction):
                new_to_old[action] = action
                new_problem.add_action(action.clone())
                continue
            pdict = OrderedDict()
            for p in action.parameters:
                pdict[p.name] = p.type
            new_action = InstantaneousAction(action.name, pdict)
            assert isinstance(action, DurativeAction)

            (
                start_effects_subs,
                old_start_effects,
                old_end_effects,
            ) = self.get_effects_data_structures(action=action, em=em, fve=fve)

            for timeinterval, ocl in action.conditions.items():
                # intermediate not supported
                # upper = lower = start -> precond (no sub)
                # upper = lower = end -> postcond (must sub)
                # upper = end, lower = start -> invariant (both sub and not)
                # so basically, if lower = start then add condition without sub, if upper = end then add condition with sub
                if (
                    timeinterval.lower == StartTiming()
                    and not timeinterval.is_left_open()
                ):
                    for oc in ocl:
                        new_action.add_precondition(oc)
                if timeinterval.upper == EndTiming():
                    for oc in ocl:
                        new_action.add_precondition(oc.substitute(start_effects_subs))

            for oeef, oeel in old_end_effects.items():
                for oee in oeel:
                    assert isinstance(oee, Effect)
                    if not oee.condition == em.TRUE():
                        new_cond = oee.condition.substitute(start_effects_subs)
                    else:
                        new_cond = em.TRUE()
                    if oee.is_assignment():
                        new_value = oee.value.substitute(start_effects_subs)
                        new_action.add_effect(oeef, new_value, new_cond)
                    elif oee.is_increase():
                        new_value = em.Plus(oeef, oee.value)
                        new_value = new_value.substitute(start_effects_subs)
                        new_action.add_effect(oeef, new_value, new_cond)
                    elif oee.is_decrease():
                        new_value = em.Minus(oeef, oee.value)
                        new_value = new_value.substitute(start_effects_subs)
                        new_action.add_effect(oeef, new_value, new_cond)
                    else:
                        raise UPUnreachableCodeError
                    new_value = None
            for osef, osel in old_start_effects.items():
                for ose in osel:
                    assert isinstance(ose, Effect)
                    if osef not in old_end_effects.keys():
                        if ose.is_assignment():
                            new_action.add_effect(osef, ose.value, ose.condition)
                        elif ose.is_increase():
                            new_action.add_increase_effect(
                                osef, ose.value, ose.condition
                            )
                        elif ose.is_decrease():
                            new_action.add_increase_effect(
                                osef, ose.value, ose.condition
                            )
                        else:
                            raise UPUnreachableCodeError
            new_to_old[new_action] = action
            new_problem.add_action(new_action)

        return CompilerResult(
            problem=new_problem,
            plan_back_conversion=partial(
                plan_back_conversion_callable,
                problem=problem,
                new_problem=new_problem,
                new_to_old=new_to_old,
            ),
            engine_name=self.name,
            map_back_action_instance=None,
        )
