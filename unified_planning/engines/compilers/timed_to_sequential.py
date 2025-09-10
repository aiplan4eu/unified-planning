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
)
from unified_planning.model.timing import StartTiming, EndTiming, Interval
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.compilers.utils import replace_action
from typing import Dict, Optional, List, Tuple
from fractions import Fraction
from functools import partial
from unified_planning.exceptions import (
    UPUnsupportedProblemTypeError,
)
from unified_planning.plans import SequentialPlan, TimeTriggeredPlan, ActionInstance


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
        new_kind.unset_expression_duration("INT_TYPE_DURATIONS")
        new_kind.unset_expression_duration("REAL_TYPE_DURATIONS")
        new_kind.unset_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        new_kind.unset_expression_duration("FLUENTS_IN_DURATIONS")
        new_kind.unset_time("CONTINUOUS_TIME")
        new_kind.unset_time("DISCRETE_TIME")
        new_kind.unset_time("DURATION_INEQUALITIES")
        return new_kind

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

        new_to_old: Dict[Action, Optional[Action]] = {}

        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"

        new_problem.clear_actions()

        for action in problem.actions:
            new_action = InstantaneousAction(action.name)
            if isinstance(action, InstantaneousAction):
                new_to_old[new_action] = action
                new_problem.add_action(new_action)
                continue
            assert isinstance(action, DurativeAction)
            start = StartTiming()
            end = EndTiming()
            old_end_effects: Dict = {}
            old_start_effects: Dict = {}
            for timepoint, oel in action.effects.items():
                if timepoint == start:
                    for oe in oel:
                        if oe.fluent not in old_start_effects.keys():
                            old_start_effects[oe.fluent] = []
                        old_start_effects[oe.fluent].append(oe)
                elif timepoint == end:
                    for oe in oel:
                        if oe.fluent not in old_end_effects.keys():
                            old_end_effects[oe.fluent] = []
                        old_end_effects[oe.fluent].append(oe)
                else:
                    raise UPUnsupportedProblemTypeError(
                        "Intermediate effects are not supported"
                    )

            subs_dict: Dict = {}
            for osef, osel in old_start_effects.items():
                subs_dict[osef] = osef
                for ose in osel:
                    assert isinstance(ose, Effect)
                    if ose.is_assignment():
                        # NOTE we should never find assignments associated with any other kind of effect
                        subs_dict[ose.fluent] = ose.value
                    elif ose.is_increase():
                        subs_dict[ose.fluent] = em.Plus(
                            subs_dict[ose.fluent], ose.value
                        )
                    elif ose.is_decrease():
                        subs_dict[ose.fluent] = em.Minus(
                            subs_dict[ose.fluent], ose.value
                        )
                    else:
                        raise UPUnsupportedProblemTypeError

            for timeinterval, ocl in action.conditions.items():
                if timeinterval.upper == start and timeinterval.lower == start:
                    for oc in ocl:
                        new_action.add_precondition(oc)
                else:
                    for oc in ocl:
                        new_action.add_precondition(oc.substitute(subs_dict))

            # TODO find a way to keep increase/decrease instead of turning everything into assignments - is this necessary?
            for oeef, oeel in old_end_effects.items():
                for oee in oeel:
                    assert isinstance(oee, Effect)
                    if oee.is_assignment():
                        new_value = oee.value.substitute(subs_dict)
                        new_action.add_effect(oeef, new_value)
                    elif oee.is_increase():
                        new_value = em.Plus(oeef, oee.value)
                        new_value = new_value.substitute(subs_dict)
                        new_action.add_effect(oeef, new_value)
                    elif oee.is_decrease():
                        new_value = em.Minus(oeef, oee.value)
                        new_value = new_value.substitute(subs_dict)
                        new_action.add_effect(oeef, new_value)
                    else:
                        raise UPUnsupportedProblemTypeError
                    new_value = None
            for osef, osel in old_start_effects.items():
                for ose in osel:
                    assert isinstance(ose, Effect)
                    if osef not in old_end_effects.keys():
                        if ose.is_assignment():
                            new_action.add_effect(osef, ose.value)
                        elif ose.is_increase():
                            new_action.add_increase_effect(osef, ose.value)
                        elif ose.is_decrease():
                            new_action.add_increase_effect(osef, ose.value)
                        else:
                            raise UPUnsupportedProblemTypeError
            new_to_old[new_action] = action
            new_problem.add_action(new_action)

        # TODO setup for map_back_callable system instead of single action map back
        def map_back_callable(sp: SequentialPlan) -> TimeTriggeredPlan:
            MIN_TIME_STEP = Fraction(1, 100)
            time_now: Fraction = Fraction(0)
            ttptuples: List[Tuple[Fraction, ActionInstance, Optional[Fraction]]] = []
            for action_instance in sp.actions:
                if action_instance.action in new_to_old:
                    action_for_mapback = new_to_old[action_instance.action]
                    assert action_for_mapback is not None
                    tinterval = action_for_mapback.duration
                    assert isinstance(tinterval, Interval)
                    dtime = MIN_TIME_STEP  # TODO change placeholder once we decide what to do
                    if not tinterval.is_left_open():
                        dtime = Fraction(
                            tinterval.lower.constant_value()
                        )  # TODO check is this correct?
                else:
                    action_for_mapback = action_instance.action
                    assert action_for_mapback is not None
                    dtime = MIN_TIME_STEP

                new_action_instance = ActionInstance(
                    action=action_for_mapback,
                    params=action_instance.actual_parameters,
                    agent=action_instance.agent,
                    motion_paths=action_instance.motion_paths,
                )
                ttptuples.append((time_now, new_action_instance, dtime))
                time_now = time_now + dtime + MIN_TIME_STEP
            ttp = TimeTriggeredPlan(ttptuples)
            return ttp

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )
