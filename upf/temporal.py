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


from upf.fnode import FNode
from upf.timing import Timing
from fractions import Fraction
from typing import List, Union, Dict
from collections import OrderedDict


class IntervalDuration:
    def __init__(self, lower: FNode, upper: FNode):
        self._lower = lower
        self._upper = upper

    def lower(self):
        return self._lower

    def upper(self):
        return self._upper

    def is_left_open(self):
        raise NotImplementedError

    def is_right_open(self):
        raise NotImplementedError


class ClosedIntervalDuration(IntervalDuration):
    '''Represents the (closed) interval duration constraint:
            [lower, upper]
    '''
    def __init__(self, lower: FNode, upper: FNode):
        IntervalDuration.__init__(self, lower, upper)

    def __repr__(self) -> str:
        return f'[{str(self._lower)}, {str(self._upper)}]'

    def is_left_open(self):
        return False

    def is_right_open(self):
        return False


class FixedDuration(ClosedIntervalDuration):
    '''Represents a fixed duration constraint'''
    def __init__(self, size: FNode):
        ClosedIntervalDuration.__init__(self, size, size)

    def __repr__(self) -> str:
        return f'[{self._lower}]'


class OpenIntervalDuration(IntervalDuration):
    '''Represents the (open) interval duration constraint:
            (lower, upper)
    '''
    def __init__(self, lower: FNode, upper: FNode):
        IntervalDuration.__init__(self, lower, upper)

    def __repr__(self) -> str:
        return f'({self._lower}, {self._upper})'

    def is_left_open(self):
        return True

    def is_right_open(self):
        return True


class LeftOpenIntervalDuration(IntervalDuration):
    '''Represents the (left open, right closed) interval duration constraint:
            (lower, upper]
    '''
    def __init__(self, lower: FNode, upper: FNode):
        IntervalDuration.__init__(self, lower, upper)

    def __repr__(self) -> str:
        return f'({self._lower}, {self._upper}]'

    def is_left_open(self):
        return True

    def is_right_open(self):
        return False


class RightOpenIntervalDuration(IntervalDuration):
    '''Represents the (left closed, right open) interval duration constraint:
            [lower, upper)
    '''
    def __init__(self, lower: FNode, upper: FNode):
        IntervalDuration.__init__(self, lower, upper)

    def __repr__(self) -> str:
        return f'[{self._lower}, {self._upper})'

    def is_left_open(self):
        return False

    def is_right_open(self):
        return True


class Interval:
    def __init__(self, lower: Timing, upper: Timing):
        self._lower = lower
        self._upper = upper

    def lower(self):
        return self._lower

    def upper(self):
        return self._upper

    def is_left_open(self):
        raise NotImplementedError

    def is_right_open(self):
        raise NotImplementedError


class ClosedInterval(Interval):
    '''Represents the (closed) interval:
            [lower, upper]
    '''
    def __init__(self, lower: Timing, upper: Timing):
        Interval.__init__(self, lower, upper)

    def __repr__(self) -> str:
        return f'[{str(self._lower)}, {str(self._upper)}]'

    def is_left_open(self):
        return False

    def is_right_open(self):
        return False


class OpenInterval(Interval):
    '''Represents the (open) interval:
            (lower, upper)
    '''
    def __init__(self, lower: Timing, upper: Timing):
        Interval.__init__(self, lower, upper)

    def __repr__(self) -> str:
        return f'({self._lower}, {self._upper})'

    def is_left_open(self):
        return True

    def is_right_open(self):
        return True


class LeftOpenInterval(Interval):
    '''Represents the (left open, right closed) interval:
            (lower, upper]
    '''
    def __init__(self, lower: Timing, upper: Timing):
        Interval.__init__(self, lower, upper)

    def __repr__(self) -> str:
        return f'({self._lower}, {self._upper}]'

    def is_left_open(self):
        return True

    def is_right_open(self):
        return False


class RightOpenInterval(Interval):
    '''Represents the (left closed, right open) interval:
            [lower, upper)
    '''
    def __init__(self, lower: Timing, upper: Timing):
        Interval.__init__(self, lower, upper)

    def __repr__(self) -> str:
        return f'[{self._lower}, {self._upper})'

    def is_left_open(self):
        return False

    def is_right_open(self):
        return True
