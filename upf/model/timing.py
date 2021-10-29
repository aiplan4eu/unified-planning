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


from upf.model.fnode import FNode
from fractions import Fraction
from typing import List, Union, Dict
from collections import OrderedDict

class Timing:
    def __init__(self, bound: Union[int, Fraction]):
        self._bound = bound

    def __repr__(self):
        raise NotImplementedError

    def bound(self):
        return self._bound

    def is_from_start(self):
        raise NotImplementedError

    def is_from_end(self):
        raise NotImplementedError


class StartTiming(Timing):
    '''Represents the start timing of an action.
    Created with a bound != 0 represents "bound" time
    after the start of an action.

    For example, action starts at time 5:
    StartTiming() = 5
    StartTiming(3) = 5+3 = 8'''

    def __init__(self, bound: Union[int, Fraction] = 0):
        Timing.__init__(self, bound)

    def __repr__(self):
        if self._bound == 0:
            return 'start'
        else:
            return f'start + {self._bound}'

    def is_from_start(self):
        return True

    def is_from_end(self):
        return False


def AbsoluteTiming(bound: Union[int, Fraction] = 0):
    return StartTiming(bound)


class EndTiming(Timing):
    '''Represents the end timing of an action.
    Created with a bound != 0 represents "bound" time
    before the end of an action.

    For example, action ends at time 10:
    EndTiming() = 10
    EndTiming(1.5) = 10-Fraction(3, 2) = Fraction(17, 2) = 8.5'''

    def __init__(self, bound: Union[int, Fraction] = 0):
        Timing.__init__(self, bound)

    def __repr__(self):
        if self._bound == 0:
            return 'end'
        else:
            return f'end - {self._bound}'

    def is_from_start(self):
        return False

    def is_from_end(self):
        return True


class IntervalDuration:
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
        return f'{left_bound}{str(self.lower())}, {str(self.upper())}{right_bound}'

    def lower(self):
        return self._lower

    def upper(self):
        return self._upper

    def is_left_open(self) -> bool:
        return self._is_left_open

    def is_right_open(self) -> bool:
        return self._is_right_open

def ClosedIntervalDuration(lower: FNode, upper: FNode) -> IntervalDuration:
    '''Represents the (closed) interval duration constraint:
            [lower, upper]
    '''
    return IntervalDuration(lower, upper)

def FixedDuration(size: FNode) -> IntervalDuration:
    '''Represents a fixed duration constraint'''
    return IntervalDuration(size, size)

def OpenIntervalDuration(lower: FNode, upper: FNode) -> IntervalDuration:
    '''Represents the (open) interval duration constraint:
            (lower, upper)
    '''
    return IntervalDuration(lower, upper, True, True)

def LeftOpenIntervalDuration(lower: FNode, upper: FNode) -> IntervalDuration:
    '''Represents the (left open, right closed) interval duration constraint:
            (lower, upper]
    '''
    return IntervalDuration(lower, upper, True, False)

def RightOpenIntervalDuration(lower: FNode, upper: FNode) -> IntervalDuration:
    '''Represents the (left closed, right open) interval duration constraint:
            [lower, upper)
    '''
    return IntervalDuration(lower, upper, False, True)

class Interval:
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
        return f'{left_bound}{str(self.lower())}, {str(self.upper())}{right_bound}'

    def lower(self):
        return self._lower

    def upper(self):
        return self._upper

    def is_left_open(self) -> bool:
        return self._is_left_open

    def is_right_open(self) -> bool:
        return self._is_right_open

def ClosedInterval(lower: Timing, upper: Timing) -> Interval:
    '''Represents the (closed) interval duration constraint:
            [lower, upper]
    '''
    return Interval(lower, upper)

def OpenInterval(lower: Timing, upper: Timing) -> Interval:
    '''Represents the (open) interval duration constraint:
            (lower, upper)
    '''
    return Interval(lower, upper, True, True)

def LeftOpenInterval(lower: Timing, upper: Timing) -> Interval:
    '''Represents the (left open, right closed) interval duration constraint:
            (lower, upper]
    '''
    return Interval(lower, upper, True, False)

def RightOpenInterval(lower: Timing, upper: Timing) -> Interval:
    '''Represents the (left closed, right open) interval duration constraint:
            [lower, upper)
    '''
    return Interval(lower, upper, False, True)
