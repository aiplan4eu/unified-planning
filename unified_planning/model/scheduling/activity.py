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

from typing import Optional, Union

from unified_planning.model.expression import NumericExpression

from unified_planning.model.fnode import FNode
from unified_planning.environment import get_environment, Environment
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model import (
    Timepoint,
    Timing,
    TimepointKind,
    Fluent,
    NumericConstant,
)
import unified_planning as up
from unified_planning.model.scheduling.chronicle import Chronicle


class Activity(Chronicle):
    """Activity is essentially an interval with start and end timepoint that facilitates defining constraints in the
    associated :class:`SchedulingProblem`"""

    def __init__(
        self, name: str, duration: int = 0, _env: Optional[Environment] = None
    ):
        Chronicle.__init__(self, name, _env=_env)
        self._start = Timepoint(TimepointKind.START, container=name)
        self._end = Timepoint(TimepointKind.END, container=name)

        self.set_fixed_duration(duration)

    @property
    def start(self) -> Timepoint:
        """Returns a reference to the start time of this activity."""
        return self._start

    @property
    def end(self) -> Timepoint:
        """Returns a reference to the start time of this activity."""
        return self._end

    @property
    def duration(self) -> "up.model.timing.DurationInterval":
        """Returns the `activity` `duration interval`."""
        return self._duration

    def set_fixed_duration(self, value: "up.model.expression.NumericExpression"):
        """
        Sets the `duration interval` for this `activity` as the interval `[value, value]`.

        :param value: The `value` set as both edges of this `action's duration`.
        """
        (value_exp,) = self._environment.expression_manager.auto_promote(value)
        self._set_duration_constraint(up.model.timing.FixedDuration(value_exp))

    def set_duration_bounds(
        self,
        lower: "up.model.expression.NumericExpression",
        upper: "up.model.expression.NumericExpression",
    ):
        """
        Sets the `duration interval` for this `activity` as the interval `[lower, upper]`.

        :param lower: The value set as the lower edge of this `action's duration`.
        :param upper: The value set as the upper edge of this `action's duration`.
        """
        lower_exp, upper_exp = self._environment.expression_manager.auto_promote(
            lower, upper
        )
        self._set_duration_constraint(
            up.model.timing.ClosedDurationInterval(lower_exp, upper_exp)
        )

    def _set_duration_constraint(self, duration: "up.model.timing.DurationInterval"):
        """
        Sets the `duration interval` for this `action`.

        :param duration: The new `duration interval` of this `action`.
        """
        lower, upper = duration.lower, duration.upper
        tlower = self._environment.type_checker.get_type(lower)
        tupper = self._environment.type_checker.get_type(upper)
        assert tlower.is_int_type() or tlower.is_real_type()
        assert tupper.is_int_type() or tupper.is_real_type()
        if (
            lower.is_constant()
            and upper.is_constant()
            and (
                upper.constant_value() < lower.constant_value()
                or (
                    upper.constant_value() == lower.constant_value()
                    and (duration.is_left_open() or duration.is_right_open())
                )
            )
        ):
            raise UPProblemDefinitionError(
                f"{duration} is an empty interval duration of action: {self.name}."
            )
        self._duration = duration

    def uses(self, resource: Union[Fluent, FNode], amount: NumericExpression = 1):
        """Asserts that the activity borrows a given amount (1 by default) of the resource.
        The borrowed resources will be reusable by another activity at the time epoch immediately
        succeeding the activity end.

        :param resource: Fluent expression that denotes the resource taht is used.
        :param amount: Quantity of the resource that is borrowed over the course of the activity.
        """
        self.add_decrease_effect(self.start, resource, amount)
        self.add_increase_effect(self.end, resource, amount)

    def add_release_date(self, date: NumericExpression):
        """Sets the earliest date at which the activity can be started."""
        self.add_constraint(get_environment().expression_manager.LE(date, self.start))

    def add_deadline(self, date: NumericExpression):
        """Sets the latest date at which the activity might end."""
        self.add_constraint(get_environment().expression_manager.LE(self.end, date))

    def clone(self):
        """Generates a copy of this activity."""
        new = Activity(self.name, _env=self._environment)
        self._clone_to(new)
        new._duration = self._duration
        return new

    def __hash__(self):
        return Chronicle.__hash__(self) + hash(self._duration)

    def __eq__(self, other):
        return (
            isinstance(other, Activity)
            and Chronicle.__eq__(self, other)
            and self._duration == other._duration
        )
