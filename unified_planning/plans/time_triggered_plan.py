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


from functools import partial
from itertools import chain
import unified_planning as up
import unified_planning.plans as plans
from unified_planning.model import (
    InstantaneousAction,
    Timing,
    DurativeAction,
    Problem,
    FNode,
    TimepointKind,
    Effect,
    TimeInterval,
    Timepoint,
    SimulatedEffect,
)
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
from typing import (
    Callable,
    Dict,
    Iterator,
    Optional,
    OrderedDict,
    Set,
    Tuple,
    List,
    Union,
)
from fractions import Fraction


class TimeTriggeredPlan(plans.plan.Plan):
    """Represents a time triggered plan."""

    def __init__(
        self,
        actions: List[Tuple[Fraction, "plans.plan.ActionInstance", Optional[Fraction]]],
        environment: Optional["Environment"] = None,
    ):
        """
        The first `Fraction` represents the absolute time in which the
        `Action` starts, while the last `Fraction` represents the duration
        of the `Action` to fulfill the `problem goals`.
        The `Action` can be an `InstantaneousAction`, this is represented with a duration set
        to `None`.
        """
        # if we have a specific environment or we don't have any actions
        if environment is not None or not actions:
            plans.plan.Plan.__init__(
                self, plans.plan.PlanKind.TIME_TRIGGERED_PLAN, environment
            )
        # If we don't have a specific environment and have at least 1 action, use the environment of the first action
        else:
            assert len(actions) > 0
            plans.plan.Plan.__init__(
                self,
                plans.plan.PlanKind.TIME_TRIGGERED_PLAN,
                actions[0][1].action.environment,
            )
        for (
            _,
            ai,
            _,
        ) in (
            actions
        ):  # check that given environment and the environment in the actions is the same
            if ai.action.environment != self._environment:
                raise UPUsageError(
                    "The environment given to the plan is not the same of the actions in the plan."
                )
        self._actions = actions

    def __repr__(self) -> str:
        return f"TimeTriggeredPlan({self._actions})"

    def __str__(self) -> str:
        def convert_ai(start_ai_dur):
            start, ai, dur = start_ai_dur
            if dur is None:
                return f"    {float(start)}: {ai}"
            else:
                return f"    {float(start)}: {ai} [{float(dur)}]"

        ret = ["TimeTriggeredPlan:"]
        ret.extend(map(convert_ai, sorted(self._actions, key=lambda x: x[0])))
        return "\n".join(ret)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, TimeTriggeredPlan) and len(self._actions) == len(
            oth._actions
        ):
            for (s, ai, d), (oth_s, oth_ai, oth_d) in zip(self._actions, oth._actions):
                if (
                    s != oth_s
                    or ai.action != oth_ai.action
                    or ai.actual_parameters != oth_ai.actual_parameters
                    or d != oth_d
                ):
                    return False
            return True
        else:
            return False

    def __hash__(self) -> int:
        count: int = 0
        for i, (s, ai, d) in enumerate(self._actions):
            count += (
                i + hash(ai.action) + hash(ai.actual_parameters) + hash(s) + hash(d)
            )
        return count

    def __contains__(self, item: object) -> bool:
        if isinstance(item, plans.plan.ActionInstance):
            return any(item.is_semantically_equivalent(a) for _, a, _ in self._actions)
        else:
            return False

    @property
    def timed_actions(
        self,
    ) -> List[Tuple[Fraction, "plans.plan.ActionInstance", Optional[Fraction]]]:
        """
        Returns the sequence of tuples (`start`, `action_instance`, `duration`) where:

        - `start` is when the `ActionInstance` starts;
        - `action_instance` is the `grounded Action` applied;
        - `duration` is the (optional) duration of the `ActionInstance`.
        """
        return self._actions

    def replace_action_instances(
        self,
        replace_function: Callable[
            ["plans.plan.ActionInstance"], Optional["plans.plan.ActionInstance"]
        ],
    ) -> "plans.plan.Plan":
        """
        Returns a new `TimeTriggeredPlan` where every `ActionInstance` of the current `Plan` is replaced using the given `replace_function`.

        :param replace_function: The function that applied to an `ActionInstance A` returns the `ActionInstance B`; `B`
            replaces `A` in the resulting `Plan`.
        :return: The `TimeTriggeredPlan` where every `ActionInstance` is replaced using the given `replace_function`.
        """
        new_ai = []
        for s, ai, d in self._actions:
            replaced_ai = replace_function(ai)
            if replaced_ai is not None:
                new_ai.append((s, replaced_ai, d))
        new_env = self._environment
        if len(new_ai) > 0:
            _, ai, _ = new_ai[0]
            new_env = ai.action.environment
        return TimeTriggeredPlan(new_ai, new_env)

    def convert_to(
        self,
        plan_kind: "plans.plan.PlanKind",
        problem: "up.model.AbstractProblem",
    ) -> "plans.plan.Plan":
        """
        This function takes a `PlanKind` and returns the representation of `self`
        in the given `plan_kind`. If the conversion does not make sense, raises
        an exception.

        :param plan_kind: The plan_kind of the returned plan.
        :param problem: The `Problem` of which this plan is referring to.
        :return: The plan equivalent to self but represented in the kind of
            `plan_kind`.
        """
        if plan_kind == self._kind:
            return self
        elif plan_kind == plans.plan.PlanKind.STN_PLAN:
            return _convert_to_stn(self, problem)
        else:
            raise UPUsageError(f"{type(self)} can't be converted to {plan_kind}.")

    def extract_epsilon(self, problem: Problem) -> Optional[Fraction]:
        """
        Returns the epsilon of this plan. The epsilon is the minimum time that
        elapses between 2 events of this plan.

        :param problem: The problem referred by this plan.
        :return: The minimum time elapses between 2 events of this plan. None is
            returned if the plan does not have at least 2 events.
        """
        times: Set[Fraction] = {Fraction(0)}
        for i in problem.timed_goals.keys():
            times.add(Fraction(i.lower.delay))
            times.add(Fraction(i.upper.delay))
        for t in problem.timed_effects.keys():
            times.add(Fraction(t.delay))
        for start, ai, duration in self._actions:
            times.add(start)
            if duration is None:
                assert isinstance(
                    ai.action, InstantaneousAction
                ), "Error, None duration specified for non InstantaneousAction"
                continue
            times.add(start + duration)
            action = ai.action
            assert isinstance(action, DurativeAction)
            times.update(extract_action_timings(action, start, duration))

        sorted_times: List[Fraction] = sorted(times)
        epsilon = sorted_times[-1]
        if epsilon == Fraction(0):
            return None
        prev_time = sorted_times[0]
        for current_time in sorted_times[1:]:
            epsilon = min(epsilon, current_time - prev_time)
            prev_time = current_time
        return epsilon


def _absolute_time(
    relative_time: Timing, start: Fraction, duration: Fraction
) -> Fraction:
    """
    Given the start time and the timing in the action returns the absolute
    time of the given timing.

    :param relative_time: The timing in the action.
    :param start: the starting time of the action.
    :param duration: The duration of the action.
    :return: The absolute time of the given timing.
    """
    if relative_time.is_from_start():
        return start + relative_time.delay
    else:
        return start + duration + relative_time.delay


def _convert_to_stn(
    time_triggered_plan: TimeTriggeredPlan,
    problem: "up.model.AbstractProblem",
) -> "plans.stn_plan.STNPlan":
    # This algorithm takes the TimeTriggeredPlan and converts it to an STNPlan, by
    # removing the temporal dimension, creating a SequentialPlan, then de-ordering the
    # SequentialPlan creating a PartialOrderPlan and re-adding the temporal dimension,
    # getting an STNPlan in the end.
    from unified_planning.plans.stn_plan import STNPlanNode, STNPlan

    assert isinstance(problem, Problem), "This algorithm works only for Problem"

    if problem.kind.has_external_conditions_and_effects():
        raise NotImplementedError(
            "Currently the algorithm does not support external conditions and effects"
        )

    epsilon = problem.epsilon
    if epsilon is None:
        epsilon = time_triggered_plan.extract_epsilon(problem)
        if epsilon is None:
            epsilon = Fraction(1, 1000)
        else:
            epsilon = min(epsilon / 10, Fraction(1, 1000))
    assert epsilon is not None

    # Constraints that go in the final STNPlan
    stn_constraints: Dict[
        STNPlanNode, List[Tuple[Optional[Fraction], Optional[Fraction], STNPlanNode]]
    ] = {}

    start_plan_node = STNPlanNode(TimepointKind.GLOBAL_START, None)

    # Mapping from an ActionInstance to it's Starting STNPlanNodes
    ai_to_start_node: Dict["plans.plan.ActionInstance", STNPlanNode] = {}

    # create a mockup durative action that contains the problem's timed_effects and conditions
    mockup_action = DurativeAction("mockup_action")
    for interval, cl in problem.timed_goals.items():
        start_timepoint = Timepoint(
            TimepointKind.START if interval.lower.is_from_start() else TimepointKind.END
        )
        start_timing = Timing(interval.lower.delay, start_timepoint)
        end_timepoint = Timepoint(
            TimepointKind.START if interval.upper.is_from_start() else TimepointKind.END
        )
        end_timing = Timing(interval.upper.delay, end_timepoint)
        relative_interval = TimeInterval(
            start_timing, end_timing, interval.is_left_open(), interval.is_right_open()
        )
        for c in cl:
            mockup_action.add_condition(relative_interval, c)

    for global_timing, el in problem.timed_effects.items():
        timepoint = Timepoint(
            TimepointKind.START if global_timing.is_from_start() else TimepointKind.END
        )
        timing = Timing(global_timing.delay, timepoint)
        for e in el:
            mockup_action._add_effect_instance(timing, e)

    mockup_action_instance = plans.ActionInstance(mockup_action)

    events: Dict[Fraction, List["plans.plan.ActionInstance"]] = {}

    # Mapping from an event to the action and the relative time that created it
    event_creating_ais: Dict[
        "plans.plan.ActionInstance", Tuple["plans.plan.ActionInstance", Fraction]
    ] = {}

    for start, ai, duration in chain(
        [(Fraction(0), mockup_action_instance, Fraction(-1))],
        time_triggered_plan.timed_actions,
    ):
        if ai == mockup_action_instance:
            start_node = start_plan_node
        else:
            start_node = STNPlanNode(TimepointKind.START, ai)
        end_node = None
        action = ai.action
        if duration is None:
            assert isinstance(
                action, InstantaneousAction
            ), "Error, None duration specified for non InstantaneousAction"
            events.setdefault(start, []).append(ai)
            event_creating_ais[ai] = (ai, Fraction(0))
            stn_constraints.setdefault(start_plan_node, []).append(
                (Fraction(0), None, start_node)
            )
        else:
            assert isinstance(
                action, DurativeAction
            ), "Error, Action is not a DurativeAction nor an InstantaneousAction"

            for absolute_timing, inst_action in extract_instantenous_actions(
                action, start, duration, epsilon
            ):
                if absolute_timing < 0:
                    continue
                inst_ai = plans.ActionInstance(inst_action, ai.actual_parameters)
                events.setdefault(absolute_timing, []).append(inst_ai)

                relative_timing = absolute_timing - start
                assert relative_timing >= 0
                event_creating_ais[inst_ai] = (ai, relative_timing)

            if ai != mockup_action_instance:
                end_node = STNPlanNode(TimepointKind.END, ai)
                assert start_node not in stn_constraints
                stn_constraints[start_node] = [(duration, duration, end_node)]
        ai_to_start_node[ai] = start_node

    simultaneous_events: List[Set["plans.plan.ActionInstance"]] = [
        set(l) for l in events.values() if len(l) > 1
    ]

    sorted_events = sorted(events.items(), key=lambda acts: acts[0])

    # Create the equivalent sequential plan and then deorder it to partial order plan
    list_act = [ia for _, se in sorted_events for ia in se]
    seq_plan = plans.SequentialPlan(list_act)
    partial_order_plan = seq_plan.convert_to(plans.PlanKind.PARTIAL_ORDER_PLAN, problem)
    assert isinstance(partial_order_plan, plans.PartialOrderPlan)

    for ai_current, l_next_ai in partial_order_plan.get_adjacency_list.items():
        # Get the ActionInstance that generated this event and add the constraint between the starting of the action and the start
        # of the action that generated the other event.
        # If the 2 events were simultaneous and have a constraint, they are forced to happen together, otherwise the event
        # that is scheduled later in the original plan is forced to happen later also in the STN (later by an epsilon > 0)
        current_generating_ai, current_skew_time = event_creating_ais[ai_current]
        current_start_node = ai_to_start_node[current_generating_ai]

        current_simultaneous_events = None
        for se in simultaneous_events:
            if ai_current in se:
                current_simultaneous_events = se
                break

        for ai_next in l_next_ai:
            next_generating_ai, next_skew_time = event_creating_ais[ai_next]
            next_start_node = ai_to_start_node[next_generating_ai]

            if current_generating_ai != next_generating_ai:
                upper_bound = None
                if (
                    current_simultaneous_events is not None
                    and ai_next in current_simultaneous_events
                ):
                    lower_bound = current_skew_time - next_skew_time
                    upper_bound = lower_bound
                else:
                    lower_bound = current_skew_time - next_skew_time + epsilon

                stn_constraints.setdefault(current_start_node, []).append(
                    (
                        lower_bound,
                        upper_bound,
                        next_start_node,
                    )
                )

    return STNPlan(constraints=stn_constraints)  # type: ignore [arg-type]


def get_timepoint_conditions(
    action: DurativeAction,
    timing: Fraction,
    start: Fraction,
    duration: Fraction,
) -> List[FNode]:
    timepoint_conditions: List[FNode] = []
    for time_interval, cond_list in action.conditions.items():
        if is_time_in_interv(start, duration, timing, time_interval):
            timepoint_conditions.extend(cond_list)
    return timepoint_conditions


def get_timepoint_effects(
    action: DurativeAction,
    timing: Fraction,
    start: Fraction,
    duration: Fraction,
) -> List[Effect]:
    timepoint_effects = []
    for effects_timing, el in action.effects.items():
        absolute_effect_time = _absolute_time(effects_timing, start, duration)
        if absolute_effect_time == timing:
            timepoint_effects.extend(el)
    return timepoint_effects


def get_timepoint_simulated_effects(
    action: DurativeAction,
    timing: Fraction,
    start: Fraction,
    duration: Fraction,
) -> Optional[SimulatedEffect]:
    sim_eff: Optional[SimulatedEffect] = None
    for se_timing, se in action.simulated_effects.items():
        absolute_effect_time = _absolute_time(se_timing, start, duration)
        if absolute_effect_time == timing:
            if sim_eff is not None:
                raise NotImplementedError(
                    f"The algorithm to convert from ttp to stn works if there are no conflicting effects. \
                    The action: {action.name} with duration: {duration} has 2 simulated effects at the same time"
                )
            sim_eff = se
    return sim_eff


def extract_action_timings(
    action: DurativeAction,
    start: Fraction,
    duration: Fraction,
    epsilon: Fraction = Fraction(0),
) -> Set[Fraction]:
    timings: Set[Fraction] = set()

    absolute_time = lambda timing: _absolute_time(timing, start, duration)
    timings.update(map(absolute_time, chain(action.effects, action.simulated_effects)))

    for interval in action.conditions.keys():
        lower_increment: Fraction = epsilon if interval.is_left_open() else Fraction(0)
        upper_increment: Fraction = (
            -epsilon if interval.is_right_open() else Fraction(0)
        )
        timings.add(_absolute_time(interval.lower, start, duration) + lower_increment)
        timings.add(_absolute_time(interval.upper, start, duration) + upper_increment)

    return timings


def extract_instantenous_actions(
    action: DurativeAction, start: Fraction, duration: Fraction, epsilon: Fraction
) -> Iterator[Tuple[Fraction, InstantaneousAction]]:

    for i, timing in enumerate(
        extract_action_timings(action, start, duration, epsilon)
    ):

        inst_action = InstantaneousAction(
            f"{action.name}_{i}",
            _parameters=OrderedDict(((p.name, p.type) for p in action.parameters)),
        )
        for cond in get_timepoint_conditions(action, timing, start, duration):
            inst_action.add_precondition(cond)
        for eff in get_timepoint_effects(action, timing, start, duration):
            inst_action._add_effect_instance(eff)
        sim_eff = get_timepoint_simulated_effects(action, timing, start, duration)
        if sim_eff is not None:
            inst_action.set_simulated_effect(sim_eff)

        yield timing, inst_action


def is_time_in_interv(
    start: Fraction,
    duration: Fraction,
    timing: Fraction,
    interval: "up.model.timing.TimeInterval",
) -> bool:
    """
    Return if the timepoint is in the interval given.
    """
    upper_time = _absolute_time(interval.upper, start=start, duration=duration)
    lower_time = _absolute_time(interval.lower, start=start, duration=duration)
    timing_bigger_than_lower = (
        timing > lower_time if interval.is_left_open() else timing >= lower_time
    )
    timing_smaller_than_upper = (
        timing < upper_time if interval.is_right_open() else timing <= upper_time
    )
    return timing_bigger_than_lower and timing_smaller_than_upper
