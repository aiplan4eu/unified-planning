from typing import Optional

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
    """Activity is essentially an interval with start and end timing that facilitates defining constraints in the
    associated SchedulingProblem"""

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

    def uses(self, resource: Union[Fluent, FNode], amount: NumericConstant = 1):
        """Asserts that the activity borrows a given amount (1 by default) of the resource.
        The borrowed resources will be reusable by another activity at the time epoch immediately
         succeeding the activity end.
        """
        self.add_decrease_effect(Timing(0, self.start), resource, amount)
        self.add_increase_effect(Timing(0, self.end), resource, amount)

    def set_release_date(self, date: int):
        """Set the earliest date at which the activity can be started."""
        self.add_constraint(get_environment().expression_manager.LE(date, self.start))

    def set_deadline(self, date: int):
        """Set the latest date at which the activity might end."""
        self.add_constraint(get_environment().expression_manager.LE(self.end, date))
