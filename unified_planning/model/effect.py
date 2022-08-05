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
"""
This module defines the Effect class.
A basic Effect has a fluent and an expression.
A condition can be added to make it a conditional effect.
"""


import unified_planning as up
from enum import Enum, auto
from typing import List, Callable, Dict


class EffectKind(Enum):
    """
    The Enum representing the possible effects in the unified_planning.

    The semantic is the following of an effect with fluent F, value V and condition C:
    ASSIGN   => if C then F <= V
    INCREASE => if C then F <= F + V
    DECREASE => if C then F <= F - V
    """

    ASSIGN = auto()
    INCREASE = auto()
    DECREASE = auto()


class Effect:
    """
    This class represent an effect. It has a Fluent, modified by this effect, a value
    that determines how the fluent is modified, a condition that determines if the effect
    is actually applied or not and an EffectKind that determines the semantic of the effect.
    """

    def __init__(
        self,
        fluent: "up.model.fnode.FNode",
        value: "up.model.fnode.FNode",
        condition: "up.model.fnode.FNode",
        kind: EffectKind = EffectKind.ASSIGN,
    ):
        self._fluent = fluent
        self._value = value
        self._condition = condition
        self._kind = kind
        assert (
            fluent.environment == value.environment
            and value.environment == condition.environment
        ), "Effect expressions have different environment."

    def __repr__(self) -> str:
        s = []
        if self.is_conditional():
            s.append(f"if {str(self._condition)} then")
        s.append(f"{str(self._fluent)}")
        if self.is_assignment():
            s.append(":=")
        elif self.is_increase():
            s.append("+=")
        elif self.is_decrease():
            s.append("-=")
        s.append(f"{str(self._value)}")
        return " ".join(s)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Effect):
            return (
                self._fluent == oth._fluent
                and self._value == oth._value
                and self._condition == oth._condition
                and self._kind == oth._kind
            )
        else:
            return False

    def __hash__(self) -> int:
        return (
            hash(self._fluent)
            + hash(self._value)
            + hash(self._condition)
            + hash(self._kind)
        )

    def clone(self):
        new_effect = Effect(self._fluent, self._value, self._condition, self._kind)
        return new_effect

    def is_conditional(self) -> bool:
        """
        Returns True if the Effect condition is not True; this means that the effect might
        not always be applied but depends on the runtime evaluation of it's condition.
        """
        return not self._condition.is_true()

    @property
    def fluent(self) -> "up.model.fnode.FNode":
        """Returns the Fluent that is modified by this effect."""
        return self._fluent

    @property
    def value(self) -> "up.model.fnode.FNode":
        """Returns the value given to the Fluent by this Effect."""
        return self._value

    def set_value(self, new_value: "up.model.fnode.FNode"):
        """
        Sets the value given to the Fluent by this Effect.

        :param new_value: The value that will be set as this effect's value.
        """
        self._value = new_value

    @property
    def condition(self) -> "up.model.fnode.FNode":
        """Returns the condition required for this Effect to be applied."""
        return self._condition

    def set_condition(self, new_condition: "up.model.fnode.FNode"):
        """
        Sets the condition required for this Effect to be applied.

        :param new_condition: The expression set as this effect's condition.
        """
        self._condition = new_condition

    @property
    def kind(self) -> EffectKind:
        """Returns the kind of this Effect."""
        return self._kind

    @property
    def environment(self) -> "up.environment.Environment":
        """Returns this effect's environment."""
        return self._fluent.environment

    def is_assignment(self) -> bool:
        """Returns True if the kind of this Effect is an assignment, False otherwise."""
        return self._kind == EffectKind.ASSIGN

    def is_increase(self) -> bool:
        """Returns True if the kind of this Effect is an increase, False otherwise."""
        return self._kind == EffectKind.INCREASE

    def is_decrease(self) -> bool:
        """Returns True if the kind of this Effect is a decrease, False otherwise."""
        return self._kind == EffectKind.DECREASE


class SimulatedEffect:
    """
    This class represents a simulated effect over a list of fluent expressions.
    The fluents parameters must be constants or action parameters.
    The callable function must return the result of the simulated effects applied
    in the given state for the specified fluent expressions.
    """

    def __init__(
        self,
        fluents: List["up.model.fnode.FNode"],
        function: Callable[
            [
                "up.model.problem.AbstractProblem",
                "up.model.state.ROState",
                Dict["up.model.parameter.Parameter", "up.model.fnode.FNode"],
            ],
            List["up.model.fnode.FNode"],
        ],
    ):
        for f in fluents:
            if not f.is_fluent_exp():
                raise up.exceptions.UPUsageError(
                    "Simulated effects can be defined on fluent expressions with constant parameters"
                )
            for c in f.args:
                if not (c.is_constant or c.is_parameter_exp()):
                    raise up.exceptions.UPUsageError(
                        "Simulated effects can be defined on fluent expressions with constant parameters"
                    )
        self._fluents = fluents
        self._function = function

    def __repr__(self) -> str:
        return f"{self._fluents} := simulated"

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, SimulatedEffect):
            return self._fluents == oth._fluents and self._function == oth._function
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._function)
        for f in self._fluents:
            res += hash(f)
        return res

    @property
    def fluents(self) -> List["up.model.fnode.FNode"]:
        """Returns the list of fluents modified by this SimulatedEffect."""
        return self._fluents

    @property
    def function(
        self,
    ) -> Callable[
        [
            "up.model.problem.AbstractProblem",
            "up.model.state.ROState",
            Dict["up.model.parameter.Parameter", "up.model.fnode.FNode"],
        ],
        List["up.model.fnode.FNode"],
    ]:
        """
        Return the function that contains the information on how the fluents of this SimulatedEffect
        are modified when the simulated effect is applied.
        """
        return self._function
