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

from decimal import Decimal
from fractions import Fraction
from unified_planning.exceptions import UPProblemDefinitionError
from typing import Optional, Union


class EpsilonSeparationMixin:
    """
    This class defines the problem's mixin for the epsilon separation.

    When this mixin is initialized, a default must be set.
    Then, the epsilon value can be changed based on the user's request.
    """

    def __init__(
        self,
        default: Optional[Fraction],
    ):
        self._epsilon = default

    @property
    def epsilon(self) -> Optional[Fraction]:
        """
        This parameter has meaning only in temporal problems: it defines the minimum
        amount of time that can elapse between 2 temporal events. A temporal event can
        be, for example, the start of an action, the end of an action, an intermediate
        step of an action, a timed effect of the problem.

        When None, it means that this minimum step is chosen by the Engine the Problem
        is given to.
        """
        return self._epsilon

    @epsilon.setter
    def epsilon(self, new_value: Optional[Union[float, Decimal, Fraction, str]]):
        if new_value is not None:
            if not isinstance(new_value, Fraction):
                try:
                    new_value = Fraction(new_value)
                except ValueError:
                    raise UPProblemDefinitionError(
                        "The epsilon of a problem must be convertible to a Fraction."
                    )
            if new_value < 0:
                raise UPProblemDefinitionError("The epsilon must be a positive value!")
        self._epsilon = new_value

    def _clone_to(self, other: "EpsilonSeparationMixin"):
        other.epsilon = self._epsilon
