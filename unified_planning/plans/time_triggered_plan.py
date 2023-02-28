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


import unified_planning as up
import unified_planning.plans as plans
from unified_planning.model import InstantaneousAction, Timing, DurativeAction, Problem
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
from typing import Callable, Optional, Set, Tuple, List, Union
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
        return str(self._actions)

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
            for t in action.effects.keys():
                times.add(_absolute_time(t, start, duration))
            for t in action.simulated_effects.keys():
                times.add(_absolute_time(t, start, duration))
            for i in action.conditions.keys():
                times.add(_absolute_time(i.lower, start, duration))
                times.add(_absolute_time(i.upper, start, duration))

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
        return start + duration - relative_time.delay
