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
"""
This module defines the `Effect` class.
A basic `Effect` has a `fluent` and an `expression`.
A `condition` can be added to make it a `conditional effect`.
"""


import unified_planning as up
from unified_planning.exceptions import (
    UPConflictingEffectsException,
    UPProblemDefinitionError,
    UPUnboundedVariablesError,
)
from enum import Enum, auto
from typing import List, Callable, Dict, Optional, Set, Union, Iterable, Tuple, Iterator


class EffectKind(Enum):
    """
    The `Enum` representing the possible `Effects` in the `unified_planning`.

    The semantic is the following of an `effect` with fluent `F`, value `V` and condition `C`:
    `ASSIGN`   => `if C then F <= V`
    `INCREASE` => `if C then F <= F + V`
    `DECREASE` => `if C then F <= F - V`
    """

    ASSIGN = auto()
    INCREASE = auto()
    DECREASE = auto()


class Effect:
    """
    This class represent an effect. It has a :class:`~unified_planning.model.Fluent`, modified by this effect, a value
    that determines how the `Fluent` is modified, a `condition` that determines if the `Effect`
    is actually applied or not and an `EffectKind` that determines the semantic of the `Effect`.
    """

    def __init__(
        self,
        fluent: "up.model.fnode.FNode",
        value: "up.model.fnode.FNode",
        condition: "up.model.fnode.FNode",
        kind: EffectKind = EffectKind.ASSIGN,
        forall: Iterable["up.model.variable.Variable"] = tuple(),
    ):
        fve = fluent.environment.free_vars_extractor
        fluents_in_fluent = fve.get(fluent)
        fluents_in_fluent.remove(fluent)
        if fluents_in_fluent:
            raise UPProblemDefinitionError(
                f"The fluent: {fluent} contains other fluents in his arguments: {fluents_in_fluent}"
            )
        self._fluent = fluent
        self._value = value
        self._condition = condition
        self._kind = kind
        fvo = fluent.environment.free_vars_oracle
        free_vars: Set["up.model.variable.Variable"] = fvo.get_free_variables(fluent)
        free_vars.update(fvo.get_free_variables(value))
        free_vars.update(fvo.get_free_variables(condition))

        def free_vars_without_duplicates() -> Iterator["up.model.variable.Variable"]:
            # store seen variables to avoid duplicates
            seen: Set["up.model.variable.Variable"] = set()
            for v in forall:
                if v in free_vars and not v in seen:
                    seen.add(v)
                    yield v
            unbounded_vars = free_vars.difference(seen)
            if unbounded_vars:
                raise UPUnboundedVariablesError(
                    f"Some variables in the effect are unbounded: {unbounded_vars}"
                )

        self._forall: Tuple["up.model.variable.Variable", ...] = tuple(
            free_vars_without_duplicates()
        )
        assert (
            fluent.environment == value.environment
            and value.environment == condition.environment
            and all(fluent.environment == v.environment for v in self._forall)
        ), "Effect expressions have different environment."

    def __repr__(self) -> str:
        s = []
        if self.is_forall():
            s.append(f"forall {', '.join(str(v) for v in self._forall)}")
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
                and set(self._forall) == set(oth._forall)
            )
        else:
            return False

    def __hash__(self) -> int:
        return (
            hash(self._fluent)
            + hash(self._value)
            + hash(self._condition)
            + hash(self._kind)
            + sum(map(hash, self._forall))
        )

    def clone(self):
        new_effect = Effect(
            self._fluent, self._value, self._condition, self._kind, self._forall
        )
        return new_effect

    def is_forall(self) -> bool:
        """
        Returns `True` if the `Effect` is a `forall` effect; this means that the `Effect`
        is applied for the instances of all the specified `Variables`."""
        return len(self._forall) > 0

    def is_conditional(self) -> bool:
        """
        Returns `True` if the `Effect` condition is not `True`; this means that the `Effect` might
        not always be applied but depends on the runtime evaluation of it's :func:`condition <unified_planning.model.Effect.condition>`.
        """
        return not self._condition.is_true()

    @property
    def fluent(self) -> "up.model.fnode.FNode":
        """Returns the `Fluent` that is modified by this `Effect`."""
        return self._fluent

    @property
    def value(self) -> "up.model.fnode.FNode":
        """Returns the `value` given to the `Fluent` by this `Effect`."""
        return self._value

    def set_value(self, new_value: "up.model.fnode.FNode"):
        """
        Sets the `value` given to the `Fluent` by this `Effect`.

        :param new_value: The `value` that will be set as this `effect's value`.
        """
        self._value = new_value

    @property
    def condition(self) -> "up.model.fnode.FNode":
        """Returns the `condition` required for this `Effect` to be applied."""
        return self._condition

    def set_condition(self, new_condition: "up.model.fnode.FNode"):
        """
        Sets the `condition` required for this `Effect` to be applied.

        :param new_condition: The expression set as this `effect's condition`.
        """
        self._condition = new_condition

    @property
    def kind(self) -> EffectKind:
        """Returns the `kind` of this `Effect`."""
        return self._kind

    @property
    def forall(self) -> Tuple["up.model.variable.Variable", ...]:
        """Returns the `Variables` that are universally quantified in this `Effect`."""
        return self._forall

    @property
    def environment(self) -> "up.environment.Environment":
        """Returns this `Effect's Environment`."""
        return self._fluent.environment

    def is_assignment(self) -> bool:
        """Returns `True` if the :func:`kind <unified_planning.model.Effect.kind>` of this `Effect` is an `assignment`, `False` otherwise."""
        return self._kind == EffectKind.ASSIGN

    def is_increase(self) -> bool:
        """Returns `True` if the :func:`kind <unified_planning.model.Effect.kind>` of this `Effect` is an `increase`, `False` otherwise."""
        return self._kind == EffectKind.INCREASE

    def is_decrease(self) -> bool:
        """Returns `True` if the :func:`kind <unified_planning.model.Effect.kind>` of this `Effect` is a `decrease`, `False` otherwise."""
        return self._kind == EffectKind.DECREASE


class SimulatedEffect:
    """
    This class represents a `simulated effect` over a list of :class:`~unified_planning.model.Fluent` expressions.
    The `fluent's parameters` must be constants or :class:`~unified_planning.model.Action` `parameters`.
    The callable function must return the result of the `simulated effects` applied
    in the given :class:`~unified_planning.model.State` for the specified `fluent` expressions.
    """

    def __init__(
        self,
        fluents: List[Union["up.model.fnode.FNode", "up.model.fluent.Fluent"]],
        function: Callable[
            [
                "up.model.problem.AbstractProblem",
                "up.model.state.State",
                Dict["up.model.parameter.Parameter", "up.model.fnode.FNode"],
            ],
            List["up.model.fnode.FNode"],
        ],
    ):
        self._fluents: List["up.model.fnode.FNode"] = []
        env = None
        for f in fluents:
            if env is None:
                env = f.environment
            assert env is not None
            if isinstance(f, up.model.Fluent):
                (f_exp,) = env.expression_manager.auto_promote(f)
            else:
                f_exp = f
            assert isinstance(f_exp, up.model.FNode), "Typing not respected"
            if not f_exp.is_fluent_exp():
                raise up.exceptions.UPUsageError(
                    "Simulated effects can be defined on fluent expressions with constant parameters"
                )
            for c in f_exp.args:
                if not (c.is_constant() or c.is_parameter_exp()):
                    raise up.exceptions.UPUsageError(
                        "Simulated effects can be defined on fluent expressions with constant parameters"
                    )
            if env != f_exp.environment:
                raise up.exceptions.UPUsageError(
                    "The same SimulatedEffect contains fluents of different environments."
                )
            self._fluents.append(f_exp)
        assert env is not None
        self._env: "up.environment.Environment" = env
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
    def environment(self) -> "up.environment.Environment":
        return self._env

    @property
    def fluents(self) -> List["up.model.fnode.FNode"]:
        """Returns the `list` of `Fluents Expressions` modified by this `SimulatedEffect`."""
        return self._fluents

    @property
    def function(
        self,
    ) -> Callable[
        [
            "up.model.problem.AbstractProblem",
            "up.model.state.State",
            Dict["up.model.parameter.Parameter", "up.model.fnode.FNode"],
        ],
        List["up.model.fnode.FNode"],
    ]:
        """
        Return the function that contains the information on how the `fluents` of this `SimulatedEffect`
        are modified when this `simulated effect` is applied.
        """
        return self._function


def check_conflicting_effects(
    effect: Effect,
    timing: Optional["up.model.timing.Timing"],
    simulated_effect: Optional[SimulatedEffect],
    fluents_assigned: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"],
    fluents_inc_dec: Set["up.model.fnode.FNode"],
    name: str,
):
    """
    This method checks if the effect that would be added is in conflict with the effects/simulated-effects
    already in the action/problem.

    Note: This method has side effects on the fluents_assigned mapping and the fluents_inc_dec set, based
        on the given effect.

    :param effect: The target effect to add.
    :param timing: Optionally, the timing at which the effect is performed; None if the timing
        is not meaningful, like in InstantaneousActions.
    :param simulated_effect: The simulated effect that happen in the same moment of the effect.
    :param fluents_assigned: The mapping from a fluent to it's value of the effects happening in the
        same instant of the given effect.
    :param fluents_inc_dec: The set of fluents being increased or decremented in the same instant
        of the given effect.
    :param name: string used for better error indexing.
    :raises: UPConflictingException if the given effect is in conflict with the data structure around it.
    """
    assigned_value = fluents_assigned.get(effect.fluent, None)
    if not effect.is_conditional() and not effect.fluent.type.is_bool_type():
        if effect.is_assignment():
            # if the same fluent is involved in an increase/decrease, raise exception
            if effect.fluent in fluents_inc_dec:
                if timing is None:
                    msg = f"The effect {effect} is in conflict with the increase/decrease effects already in the {name}."
                else:
                    msg = f"The effect {effect} at timing {timing} is in conflict with the increase/decrease effects already in the {name}."
                raise UPConflictingEffectsException(msg)
            # if the same fluent is involved in a simulated effect
            elif (
                simulated_effect is not None
                and effect.fluent in simulated_effect.fluents
            ):
                if timing is None:
                    msg = f"The effect {effect} is in conflict with the simulated effects already in the {name}."
                else:
                    msg = f"The effect {effect} at timing {timing} is in conflict with the simulated effects already in the {name}."
                raise UPConflictingEffectsException(msg)
            # the same fluent is involved in another assign
            elif assigned_value is not None:
                # if the 2 values are different, raise exception
                if assigned_value != effect.value and not (
                    assigned_value.is_constant()
                    and effect.value.is_constant()
                    and assigned_value.constant_value() == effect.value.constant_value()
                ):
                    if timing is None:
                        msg = f"The effect {effect} is in conflict with the effects already in the {name}."
                    else:
                        msg = f"The effect {effect} at timing {timing} is in conflict with the effects already in the {name}."
                    raise UPConflictingEffectsException(msg)
            else:
                fluents_assigned[effect.fluent] = effect.value
        elif effect.is_increase() or effect.is_decrease():
            if effect.fluent in fluents_assigned:
                if timing is None:
                    msg = f"The effect {effect} is in conflict with the effects already in the {name}."
                else:
                    msg = f"The effect {effect} at timing {timing} is in conflict with the effects already in the {name}."
                raise UPConflictingEffectsException(msg)
            fluents_inc_dec.add(effect.fluent)
            if (
                simulated_effect is not None
                and effect.fluent in simulated_effect.fluents
            ):
                if timing is None:
                    msg = f"The effect {effect} is in conflict with the simulated effects already in the {name}."
                else:
                    msg = f"The effect {effect} at timing {timing} is in conflict with the simulated effects already in the {name}."
                raise UPConflictingEffectsException(msg)
        else:
            raise NotImplementedError


def check_conflicting_simulated_effects(
    simulated_effect: SimulatedEffect,
    timing: Optional["up.model.timing.Timing"],
    fluents_assigned: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"],
    fluents_inc_dec: Set["up.model.fnode.FNode"],
    name: str,
):
    """
    This method checks if the simulated effect that would be added is in conflict with the effects
    already in the action/problem.

    :param simulated_effect: The target simulated_effect to add.
    :param timing: Optionally, the timing at which the simulated_effect is performed; None if the timing
        is not meaningful, like in InstantaneousActions.
    :param fluents_assigned: The mapping from a fluent to it's value of the effects happening in the
        same instant of the given simulated_effect.
    :param fluents_inc_dec: The set of fluents being increased or decremented in the same instant
        of the given simulated_effect.
    :param name: string used for better error indexing.
    :raises: UPConflictingException if the given simulated_effect is in conflict with the data structure around it.
    """
    for f in simulated_effect.fluents:
        if f in fluents_inc_dec or f in fluents_assigned:
            if timing is None:
                msg = f"The simulated effect {simulated_effect} is in conflict with the effects already in the {name}."
            else:
                msg = f"The simulated effect {simulated_effect} at timing {timing} is in conflict with the effects already in the {name}."
            raise UPConflictingEffectsException(msg)
