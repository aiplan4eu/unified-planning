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


from unified_planning.model.fnode import FNode
from enum import Enum, auto
from fractions import Fraction
from typing import Union


class TimepointKind(Enum):
    GLOBAL_START = auto()
    GLOBAL_END = auto()
    START = auto()
    END = auto()


class Timepoint:
    def __init__(self, kind: TimepointKind, container=None):
        self._kind = kind
        self._container = container

    def __repr__(self):
        if self._kind == TimepointKind.GLOBAL_START or self._kind == TimepointKind.START:
            qualifier = 'start'
        else:
            qualifier = 'end'
        if self._container is None:
            return qualifier
        else:
            return f'{qualifier}({self._container.identifier})'

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Timepoint):
            return self._kind == oth._kind and self._container == oth._container
        else:
            return False

    def __hash__(self) -> int:
        return hash(self._kind) + hash(self._container)

    @property
    def kind(self) -> TimepointKind:
        return self._kind

    @property
    def container(self):
        """Returns a subtask or None"""
        return self._container


class Timing:
    def __init__(self, delay: Union[int, Fraction], timepoint: Timepoint):
        self._timepoint = timepoint
        self._delay = delay

    def __repr__(self):
        if self._delay == 0:
            return f'{self._timepoint}'
        else:
            return f'{self._timepoint} + {self._delay}'

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Timing):
            return self._delay == oth._delay and self._timepoint == oth._timepoint
        else:
            return False

    def __hash__(self) -> int:
        return hash(self._delay) ^ hash(self._timepoint)

    @property
    def delay(self) -> Union[int, Fraction]:
        return self._delay

    def is_global(self) -> bool:
        return self._timepoint.kind == TimepointKind.GLOBAL_START or \
            self._timepoint.kind == TimepointKind.GLOBAL_END

    def is_from_start(self) -> bool:
        return self._timepoint.kind == TimepointKind.START or \
            self._timepoint.kind == TimepointKind.GLOBAL_START

    def is_from_end(self) -> bool:
        return not self.is_from_start()


def StartTiming(delay: Union[int, Fraction] = 0) -> Timing:
    '''Represents the start timing of an action.
    Created with a delay > 0 represents "delay" time
    after the start of an action.

    For example, action starts at time 5:
    StartTiming() = 5
    StartTiming(3) = 5+3 = 8'''

    return Timing(delay, Timepoint(TimepointKind.START))


def EndTiming(delay: Union[int, Fraction] = 0) -> Timing:
    '''Represents the end timing of an action.
    Created with a delay > 0 represents "delay" time
    before the end of an action.

    For example, action ends at time 10:
    EndTiming() = 10
    EndTiming(1.5) = 10-Fraction(3, 2) = Fraction(17, 2) = 8.5'''

    return Timing(delay, Timepoint(TimepointKind.END))


def GlobalStartTiming(delay: Union[int, Fraction] = 0):
    '''Represents the absolute timing.
    Created with a delay > 0 represents "delay" time
    after the start of the execution.'''

    return Timing(delay, Timepoint(TimepointKind.GLOBAL_START))


def GlobalEndTiming(delay: Union[int, Fraction] = 0):
    '''Represents the end timing of an execution.
    Created with a delay > 0 represents "delay" time
    before the end of the execution.'''

    return Timing(delay, Timepoint(TimepointKind.GLOBAL_END))


class Interval:
    def __init__(self, lower: FNode, upper: FNode, is_left_open: bool = False, is_right_open: bool = False):
        self._lower = lower
        self._upper = upper
        self._is_left_open = is_left_open
        self._is_right_open = is_right_open

    def __repr__(self) -> str:
        if self.is_left_open():
            left_bound = '('
        else:
            left_bound = '['
        if self.is_right_open():
            right_bound = ')'
        else:
            right_bound = ']'
        return f'{left_bound}{str(self.lower)}, {str(self.upper)}{right_bound}'

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Interval):
            return self._lower == oth._lower and self._upper == oth._upper and self._is_left_open == oth._is_left_open and self._is_right_open == oth._is_right_open
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._lower) + hash(self._upper)
        if self._is_left_open:
            res ^= hash('is_left_open')
        if self._is_right_open:
            res ^= hash('is_right_open')
        return res

    @property
    def lower(self) -> FNode:
        return self._lower

    @property
    def upper(self) -> FNode:
        return self._upper

    def is_left_open(self) -> bool:
        return self._is_left_open

    def is_right_open(self) -> bool:
        return self._is_right_open


class Duration:
    pass


class DurationInterval(Duration, Interval):
    def __init__(self, lower: FNode, upper: FNode, is_left_open: bool = False, is_right_open: bool = False):
        Duration.__init__(self)
        Interval.__init__(self, lower, upper, is_left_open, is_right_open)


def ClosedDurationInterval(lower: FNode, upper: FNode) -> DurationInterval:
    '''Represents the (closed) interval duration constraint:
            [lower, upper]
    '''
    return DurationInterval(lower, upper)


def FixedDuration(size: FNode) -> DurationInterval:
    '''Represents a fixed duration constraint'''
    return DurationInterval(size, size)


def OpenDurationInterval(lower: FNode, upper: FNode) -> DurationInterval:
    '''Represents the (open) interval duration constraint:
            (lower, upper)
    '''
    return DurationInterval(lower, upper, True, True)


def LeftOpenDurationInterval(lower: FNode, upper: FNode) -> DurationInterval:
    '''Represents the (left open, right closed) interval duration constraint:
            (lower, upper]
    '''
    return DurationInterval(lower, upper, True, False)


def RightOpenDurationInterval(lower: FNode, upper: FNode) -> DurationInterval:
    '''Represents the (left closed, right open) interval duration constraint:
            [lower, upper)
    '''
    return DurationInterval(lower, upper, False, True)


class TimeInterval:
    def __init__(self, lower: Timing, upper: Timing, is_left_open: bool = False, is_right_open: bool = False):
        self._lower = lower
        self._upper = upper
        self._is_left_open = is_left_open
        self._is_right_open = is_right_open

    def __repr__(self) -> str:
        if self.is_left_open():
            left_bound = '('
        else:
            left_bound = '['
        if self.is_right_open():
            right_bound = ')'
        else:
            right_bound = ']'
        if self.lower == self.upper:
            return f'{left_bound}{str(self.lower)}{right_bound}'
        else:
            return f'{left_bound}{str(self.lower)}, {str(self.upper)}{right_bound}'

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, TimeInterval):
            return self._lower == oth._lower and self._upper == oth._upper and self._is_left_open == oth._is_left_open and self._is_right_open == oth._is_right_open
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._lower) + hash(self._upper)
        if self._is_left_open:
            res ^= hash('is_left_open')
        if self._is_right_open:
            res ^= hash('is_right_open')
        return res

    @property
    def lower(self) -> Timing:
        return self._lower

    @property
    def upper(self) -> Timing:
        return self._upper

    def is_left_open(self) -> bool:
        return self._is_left_open

    def is_right_open(self) -> bool:
        return self._is_right_open


def TimePointInterval(tp: Timing) -> TimeInterval:
    '''Represents the (point) temporal interval: [tp, tp]'''
    return TimeInterval(tp, tp)


def ClosedTimeInterval(lower: Timing, upper: Timing) -> TimeInterval:
    '''Represents the (closed) temporal interval: [lower, upper]'''
    return TimeInterval(lower, upper)


def OpenTimeInterval(lower: Timing, upper: Timing) -> TimeInterval:
    '''Represents the (open) temporal interval: (lower, upper)'''
    return TimeInterval(lower, upper, True, True)


def LeftOpenTimeInterval(lower: Timing, upper: Timing) -> TimeInterval:
    '''Represents the (left open, right closed) temporal interval: (lower, upper]'''
    return TimeInterval(lower, upper, True, False)


def RightOpenTimeInterval(lower: Timing, upper: Timing) -> TimeInterval:
    '''Represents the (left closed, right open) temporal interval: [lower, upper)'''
    return TimeInterval(lower, upper, False, True)
