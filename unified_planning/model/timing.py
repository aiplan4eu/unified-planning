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


from unified_planning.environment import Environment
from unified_planning.model.fnode import FNode
from enum import Enum, auto
from fractions import Fraction
from typing import Union, Optional


class TimepointKind(Enum):
    """
    `Enum` representing all the possible :func:`kinds <unified_planning.model.Timepoint.kind>` of a :class:`~unified_planning.model.Timepoint`.
    The `kind` of a Timepoint defines it's semantic:
    GLOBAL_START => At the start of the `Plan`
    GLOBAL_END   => At the end of the `Plan`
    START        => At the start of the `Action`
    END          => At the end of the `Action`
    """

    GLOBAL_START = auto()
    GLOBAL_END = auto()
    START = auto()
    END = auto()


class Timepoint:
    """Class used to define the point in the time from which a :class:`~unified_planning.model.Timing` is considered."""

    def __init__(self, kind: TimepointKind, container: Optional[str] = None):
        """
        Creates a new `Timepoint`.

        It is typically used to refer to:
         - the start/end of the containing action or method, or
         - to the start/end of a subtasks in a method

        Parameters
        ----------
        kind: TimepointKind
          Kind of the timepoint.
        container: Optional[str]
          Identifier of the container in which the timepoint is defined.
          If not set, then a start/end timepoint refers to the enclosing action or method.
        """
        assert container is None or isinstance(container, str)
        self._kind = kind
        self._container = container

    def __repr__(self):
        if (
            self._kind == TimepointKind.GLOBAL_START
            or self._kind == TimepointKind.START
        ):
            qualifier = "start"
        else:
            qualifier = "end"
        if self._container is None:
            return qualifier
        else:
            return f"{qualifier}({self._container})"

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Timepoint):
            return self._kind == oth._kind and self._container == oth._container
        else:
            return False

    def __hash__(self) -> int:
        return hash(self._kind) + hash(self._container)

    def __add__(self, delay: Union[int, Fraction]) -> "Timing":
        return Timing(delay, self)

    def __sub__(self, delay: Union[int, Fraction]) -> "Timing":
        return Timing(-delay, self)

    @property
    def kind(self) -> TimepointKind:
        """Returns the `kind` of this `Timepoint`; the `kind` defines the semantic of the `Timepoint`."""
        return self._kind

    @property
    def container(self):
        """Returns the `container` in which this `Timepoint` is defined or `None` if it refers to the enclosing `action/method`."""
        return self._container


class Timing:
    """
    Class that used a :class:`~unified_planning.model.Timepoint` to define from when this `Timing` is considered and a :func:`delay <unified_planning.model.Timing.delay>`,
    representing the distance from the given `Timepoint`.
    For example:
    A `GLOBAL_START Timepoint` with a `delay` of `5` means `5` units of time after the start of the `Plan`.
    """

    def __init__(self, delay: Union[int, Fraction], timepoint: Timepoint):
        self._timepoint = timepoint
        self._delay = delay

    def __repr__(self):
        if self._delay == 0:
            return f"{self._timepoint}"
        else:
            return f"{self._timepoint} + {self._delay}"

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Timing):
            return self._delay == oth._delay and self._timepoint == oth._timepoint
        else:
            return False

    def __hash__(self) -> int:
        return hash(self._delay) ^ hash(self._timepoint)

    def __add__(self, delay: Union[int, Fraction]) -> "Timing":
        return Timing(self.delay + delay, self.timepoint)

    def __sub__(self, delay: Union[int, Fraction]) -> "Timing":
        return Timing(self.delay - delay, self.timepoint)

    @property
    def delay(self) -> Union[int, Fraction]:
        """Returns the `delay` set for this `Timing` from the `timepoint`."""
        return self._delay

    @property
    def timepoint(self) -> Timepoint:
        """Returns the `Timepoint` from which this `Timing` is considered."""
        return self._timepoint

    def is_global(self) -> bool:
        """
        Returns `True` if this `Timing` refers to the global timing in the `Plan` and not the `start/end` of an :class:`~unified_planning.model.Action`,
        `False` otherwise.
        """
        return (
            self._timepoint.kind == TimepointKind.GLOBAL_START
            or self._timepoint.kind == TimepointKind.GLOBAL_END
        )

    def is_from_start(self) -> bool:
        """Returns `True` if this `Timing` is from the start, `False` if it is from the end."""
        return (
            self._timepoint.kind == TimepointKind.START
            or self._timepoint.kind == TimepointKind.GLOBAL_START
        )

    def is_from_end(self) -> bool:
        """Returns `True` if this `Timing` is from the end, `False` if it is from the start."""
        return not self.is_from_start()


def StartTiming(
    delay: Union[int, Fraction] = 0, container: Optional[str] = None
) -> Timing:
    """
    Returns the start timing of an :class:`~unified_planning.model.Action`.
    Created with a delay > 0 represents "delay" time
    after the start of the `Action`.

    For example, action starts at time 5:
    `StartTiming() = 5`
    `StartTiming(3) = 5+3 = 8`.

    :param delay: The delay from the start of an `action`.
    :param container: Identifier of the container in which the `timepoint` is defined.
        If not set, then refers to the enclosing `Action or method`.
    :return: The created `Timing`.
    """

    return Timing(delay, Timepoint(TimepointKind.START, container=container))


def EndTiming(container: Optional[str] = None) -> Timing:
    """
    Returns the end timing of an :class:`~unified_planning.model.Action`.

    For example, `Action` ends at time 10:
    `EndTiming() = 10`
    `EndTiming() - 4 = 10 - 4 = 6`.

    :param container: Identifier of the container in which the `Timepoint` is defined.
        If not set, then refers to the enclosing `action or method`.
    :return: The created `Timing`.
    """

    return Timing(delay=0, timepoint=Timepoint(TimepointKind.END, container=container))


def GlobalStartTiming(delay: Union[int, Fraction] = 0):
    """
    Represents the absolute `Timing`.
    Created with a delay > 0 represents `delay` time
    after the start of the execution.

    :param delay: The delay from the start of the `Plan`.
    :return: The created `Timing`.
    """

    return Timing(delay, Timepoint(TimepointKind.GLOBAL_START))


def GlobalEndTiming():
    """
    Represents the end `Timing` of an execution.
    Created with a delay > 0 represents "delay" time
    before the end of the execution.

    :param delay: The delay from the start of the `Plan`.
    :return: The created `Timing`.
    """

    return Timing(delay=0, timepoint=Timepoint(TimepointKind.GLOBAL_END))


class Interval:
    """Class that defines an `interval` with 2 :class:`expressions <unified_planning.model.FNode>` as bounds."""

    def __init__(
        self,
        lower: FNode,
        upper: FNode,
        is_left_open: bool = False,
        is_right_open: bool = False,
    ):
        self._lower = lower
        self._upper = upper
        self._is_left_open = is_left_open
        self._is_right_open = is_right_open
        assert (
            lower.environment == upper.environment
        ), "Interval s boundaries expression can not have different environments"

    def __repr__(self) -> str:
        if self.is_left_open():
            left_bound = "("
        else:
            left_bound = "["
        if self.is_right_open():
            right_bound = ")"
        else:
            right_bound = "]"
        return f"{left_bound}{str(self.lower)}, {str(self.upper)}{right_bound}"

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Interval):
            return (
                self._lower == oth._lower
                and self._upper == oth._upper
                and self._is_left_open == oth._is_left_open
                and self._is_right_open == oth._is_right_open
            )
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._lower) + hash(self._upper)
        if self._is_left_open:
            res ^= hash("is_left_open")
        if self._is_right_open:
            res ^= hash("is_right_open")
        return res

    @property
    def lower(self) -> FNode:
        """Returns the `Interval's` lower bound."""
        return self._lower

    @property
    def upper(self) -> FNode:
        """Returns the `Interval's` upper bound."""
        return self._upper

    @property
    def environment(self) -> "Environment":
        """Returns the `Interval's` `Environment`."""
        return self._lower.environment

    def is_left_open(self) -> bool:
        """Returns `True` if the `lower` bound of this `Interval` is not included in the `Interval`, `False` otherwise."""
        return self._is_left_open

    def is_right_open(self) -> bool:
        """Returns `True` if the `upper` bound of this `Interval` is not included in the `Interval`, `False` otherwise."""
        return self._is_right_open


class Duration:
    pass


class DurationInterval(Duration, Interval):
    """Class used to indicate that an `Interval` is also a `Duration`."""

    def __init__(
        self,
        lower: FNode,
        upper: FNode,
        is_left_open: bool = False,
        is_right_open: bool = False,
    ):
        Duration.__init__(self)
        Interval.__init__(self, lower, upper, is_left_open, is_right_open)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, DurationInterval):
            return (
                self._lower == oth._lower
                and self._upper == oth._upper
                and self._is_left_open == oth._is_left_open
                and self._is_right_open == oth._is_right_open
            )
        else:
            return False

    def __hash__(self) -> int:
        return hash((self._lower, self.upper, self._is_left_open, self._is_right_open))


def ClosedDurationInterval(lower: FNode, upper: FNode) -> DurationInterval:
    """
    Represents the (closed) interval duration constraint:
    `[lower, upper]`

    :param lower: The expression defining the `lower` bound of this interval.
    :param upper: The expression defining the `upper` bound of this interval.
    :return: The created `DurationInterval`.
    """
    return DurationInterval(lower, upper)


def FixedDuration(size: FNode) -> DurationInterval:
    """
    Represents a fixed duration constraint.

    :param size: The expression defining the only value in this `interval`.
    :return: The created `DurationInterval`.
    """
    return DurationInterval(size, size)


def OpenDurationInterval(lower: FNode, upper: FNode) -> DurationInterval:
    """Represents the (open) interval duration constraint:
    `(lower, upper)`

    :param lower: The expression defining the `lower` bound of this interval.
    :param upper: The expression defining the `upper` bound of this interval.
    :return: The created `DurationInterval`.
    """
    return DurationInterval(lower, upper, True, True)


def LeftOpenDurationInterval(lower: FNode, upper: FNode) -> DurationInterval:
    """Represents the (left open, right closed) interval duration constraint:
    `(lower, upper]`

    :param lower: The expression defining the `lower` bound of this interval.
    :param upper: The expression defining the `upper` bound of this interval.
    :return: The created `DurationInterval`.
    """
    return DurationInterval(lower, upper, True, False)


def RightOpenDurationInterval(lower: FNode, upper: FNode) -> DurationInterval:
    """
    Represents the (left closed, right open) interval duration constraint:
    `[lower, upper)`

    :param lower: The expression defining the `lower` bound of this interval.
    :param upper: The expression defining the `upper` bound of this interval.
    :return: The created `DurationInterval`.
    """
    return DurationInterval(lower, upper, False, True)


class TimeInterval:
    """Represents an `Interval` where the 2 bounds are :class:`~unified_planning.model.Timing`."""

    def __init__(
        self,
        lower: Timing,
        upper: Timing,
        is_left_open: bool = False,
        is_right_open: bool = False,
    ):
        self._lower = lower
        self._upper = upper
        self._is_left_open = is_left_open
        self._is_right_open = is_right_open

    def __repr__(self) -> str:
        if self.is_left_open():
            left_bound = "("
        else:
            left_bound = "["
        if self.is_right_open():
            right_bound = ")"
        else:
            right_bound = "]"
        if self.lower == self.upper:
            return f"{left_bound}{str(self.lower)}{right_bound}"
        else:
            return f"{left_bound}{str(self.lower)}, {str(self.upper)}{right_bound}"

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, TimeInterval):
            return (
                self._lower == oth._lower
                and self._upper == oth._upper
                and self._is_left_open == oth._is_left_open
                and self._is_right_open == oth._is_right_open
            )
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._lower) + hash(self._upper)
        if self._is_left_open:
            res ^= hash("is_left_open")
        if self._is_right_open:
            res ^= hash("is_right_open")
        return res

    @property
    def lower(self) -> Timing:
        """Returns the `TimeInterval's` lower bound."""
        return self._lower

    @property
    def upper(self) -> Timing:
        """Returns the `TimeInterval's` upper bound."""
        return self._upper

    def is_left_open(self) -> bool:
        """Returns `False` if this `TimeInterval` lower bound is included in the Interval, `True` otherwise."""
        return self._is_left_open

    def is_right_open(self) -> bool:
        """Returns `False` if this `TimeInterval` upper bound is included in the Interval, `True` otherwise."""
        return self._is_right_open


def TimePointInterval(tp: Timing) -> TimeInterval:
    """
    Returns the (point) temporal interval: `[tp, tp]`

    :param tp: The only `Timing` belonging to this interval.
    :return: The created `TimeInterval`.
    """
    return TimeInterval(tp, tp)


def ClosedTimeInterval(lower: Timing, upper: Timing) -> TimeInterval:
    """
    Returns the (closed) temporal interval: `[lower, upper]`

    :param lower: The `Timing` defining the `lower` bound of this interval.
    :param upper: The `Timing` defining the `upper` bound of this interval.
    :return: The created `TimeInterval`.
    """
    return TimeInterval(lower, upper)


def OpenTimeInterval(lower: Timing, upper: Timing) -> TimeInterval:
    """
    Returns the (open) temporal interval: `(lower, upper)`

    :param lower: The `Timing` defining the `lower` bound of this interval.
    :param upper: The `Timing` defining the `upper` bound of this interval.
    :return: The created `TimeInterval`.
    """
    return TimeInterval(lower, upper, True, True)


def LeftOpenTimeInterval(lower: Timing, upper: Timing) -> TimeInterval:
    """
    Returns the (left open, right closed) temporal interval: `(lower, upper]`

    :param lower: The `Timing` defining the `lower` bound of this interval.
    :param upper: The `Timing` defining the `upper` bound of this interval.
    :return: The created `TimeInterval`.
    """
    return TimeInterval(lower, upper, True, False)


def RightOpenTimeInterval(lower: Timing, upper: Timing) -> TimeInterval:
    """
    Returns the (left closed, right open) temporal interval: `[lower, upper)`

    :param lower: The `Timing` defining the `lower` bound of this interval.
    :param upper: The `Timing` defining the `upper` bound of this interval.
    :return: The created `TimeInterval`.
    """
    return TimeInterval(lower, upper, False, True)
