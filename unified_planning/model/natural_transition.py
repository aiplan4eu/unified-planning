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


import unified_planning as up
from unified_planning.environment import get_environment, Environment
from unified_planning.exceptions import (
    UPTypeError,
    UPUnboundedVariablesError,
    UPProblemDefinitionError,
    UPUsageError,
)
from unified_planning.model.mixins.timed_conds_effs import TimedCondsEffs
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set, Union, Optional, Iterable
from collections import OrderedDict

from unified_planning.model.transition import SingleTimePointTransitionMixin, Transition


"""
Below we have natural transitions. These are not controlled by the agent. Natural transitions can be of two kinds:
Processes or Events.
Processes dictate how numeric variables evolve over time through the use of time-derivative functions
Events dictate the analogous of urgent transitions in timed automata theory
"""


class NaturalTransition(Transition, SingleTimePointTransitionMixin):
    """This is the `NaturalTransition` interface"""


class Process(NaturalTransition):
    """This is the `Process` class, which implements the abstract `NaturalTransition` class."""

    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _env: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        Transition.__init__(self, _name, _parameters, _env, **kwargs)
        SingleTimePointTransitionMixin.__init__(self, _env)
        self._effects: List[up.model.effect.Effect] = []
        # fluent assigned is the mapping of the fluent to it's value if it is an unconditional assignment
        self._fluents_assigned: Dict[
            "up.model.fnode.FNode", "up.model.fnode.FNode"
        ] = {}
        # fluent_inc_dec is the set of the fluents that have an unconditional increase or decrease
        self._fluents_inc_dec: Set["up.model.fnode.FNode"] = set()

    def __repr__(self) -> str:
        s = []
        s.append(f"process {self.name}")
        self._print_parameters(s)
        s.append(" {\n")
        s.append("    preconditions = [\n")
        for c in self.preconditions:
            s.append(f"      {str(c)}\n")
        s.append("    ]\n")
        s.append("    effects = [\n")
        for e in self.effects:
            s.append(f"      {str(e)}\n")
        s.append("    ]\n")
        s.append("  }")
        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Process):
            cond = (
                self._environment == oth._environment
                and self._name == oth._name
                and self._parameters == oth._parameters
            )
            return (
                cond
                and set(self._preconditions) == set(oth._preconditions)
                and set(self._effects) == set(oth._effects)
            )
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._name)
        for ap in self._parameters.items():
            res += hash(ap)
        for p in self._preconditions:
            res += hash(p)
        for e in self._effects:
            res += hash(e)
        return res

    def clone(self):
        new_params = OrderedDict(
            (param_name, param.type) for param_name, param in self._parameters.items()
        )
        new_process = Process(self._name, new_params, self._environment)
        new_process._preconditions = self._preconditions[:]
        new_process._effects = [e.clone() for e in self._effects]
        new_process._fluents_assigned = self._fluents_assigned.copy()
        new_process._fluents_inc_dec = self._fluents_inc_dec.copy()
        return new_process

    @property
    def effects(self) -> List["up.model.effect.Effect"]:
        """Returns the `list` of the `Process effects`."""
        return self._effects

    def clear_effects(self):
        """Removes all the `Process's effects`."""
        self._effects = []
        self._fluents_assigned = {}
        self._fluents_inc_dec = set()

    def _add_effect_instance(self, effect: "up.model.effect.Effect"):
        assert (
            effect.environment == self._environment
        ), "effect does not have the same environment of the Process"

        self._effects.append(effect)

    def add_derivative(
        self,
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
    ):
        """
        Adds the given `time derivative effect` to the `process's effects`.

        :param fluent: The `fluent` is the numeric state variable of which this process expresses its time derivative, which in Newton's notation would be over-dot(fluent).
        :param value: This is the actual time derivative function. For instance, `fluent = 4` expresses that the time derivative of `fluent` is 4.
        """
        (
            fluent_exp,
            value_exp,
            condition_exp,
        ) = self._environment.expression_manager.auto_promote(
            fluent,
            value,
            True,
        )
        if not fluent_exp.is_fluent_exp() and not fluent_exp.is_dot():
            raise UPUsageError(
                "fluent field of add_increase_effect must be a Fluent or a FluentExp or a Dot."
            )
        if not fluent_exp.type.is_compatible(value_exp.type):
            raise UPTypeError(
                f"Process effect has an incompatible value type. Fluent type: {fluent_exp.type} // Value type: {value_exp.type}"
            )
        if not fluent_exp.type.is_int_type() and not fluent_exp.type.is_real_type():
            raise UPTypeError("Derivative can be created only on numeric types!")
        self._add_effect_instance(
            up.model.effect.Effect(
                fluent_exp,
                value_exp,
                condition_exp,
                kind=up.model.effect.EffectKind.DERIVATIVE,
                forall=tuple(),
            )
        )


class Event(NaturalTransition):
    """This class represents an event."""

    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _env: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        Transition.__init__(self, _name, _parameters, _env, **kwargs)
        SingleTimePointTransitionMixin.__init__(self, _env)
        self._effects: List[up.model.effect.Effect] = []
        # fluent assigned is the mapping of the fluent to it's value if it is an unconditional assignment
        self._fluents_assigned: Dict[
            "up.model.fnode.FNode", "up.model.fnode.FNode"
        ] = {}
        # fluent_inc_dec is the set of the fluents that have an unconditional increase or decrease
        self._fluents_inc_dec: Set["up.model.fnode.FNode"] = set()

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Event):
            cond = (
                self._environment == oth._environment
                and self._name == oth._name
                and self._parameters == oth._parameters
            )
            return (
                cond
                and set(self._preconditions) == set(oth._preconditions)
                and set(self._effects) == set(oth._effects)
            )
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._name)
        for ap in self._parameters.items():
            res += hash(ap)
        for p in self._preconditions:
            res += hash(p)
        for e in self._effects:
            res += hash(e)
        return res

    def clone(self):
        new_params = OrderedDict(
            (param_name, param.type) for param_name, param in self._parameters.items()
        )
        new_event = Event(self._name, new_params, self._environment)
        new_event._preconditions = self._preconditions[:]
        new_event._effects = [e.clone() for e in self._effects]
        new_event._fluents_assigned = self._fluents_assigned.copy()
        new_event._fluents_inc_dec = self._fluents_inc_dec.copy()
        return new_event

    @property
    def effects(self) -> List["up.model.effect.Effect"]:
        """Returns the `list` of the `Event effects`."""
        return self._effects

    def clear_effects(self):
        """Removes all the `Event's effects`."""
        self._effects = []
        self._fluents_assigned = {}
        self._fluents_inc_dec = set()

    @property
    def conditional_effects(self) -> List["up.model.effect.Effect"]:
        """Returns the `list` of the `event conditional effects`.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible."""
        return [e for e in self._effects if e.is_conditional()]

    def is_conditional(self) -> bool:
        """Returns `True` if the `event` has `conditional effects`, `False` otherwise."""
        return any(e.is_conditional() for e in self._effects)

    @property
    def unconditional_effects(self) -> List["up.model.effect.Effect"]:
        """Returns the `list` of the `event unconditional effects`.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible."""
        return [e for e in self._effects if not e.is_conditional()]

    def add_effect(
        self,
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
        forall: Iterable["up.model.variable.Variable"] = tuple(),
    ):
        """
        Adds the given `assignment` to the `event's effects`.

        :param fluent: The `fluent` of which `value` is modified by the `assignment`.
        :param value: The `value` to assign to the given `fluent`.
        :param condition: The `condition` in which this `effect` is applied; the default
            value is `True`.
        :param forall: The 'Variables' that are universally quantified in this
            effect; the default value is empty.
        """
        (
            fluent_exp,
            value_exp,
            condition_exp,
        ) = self._environment.expression_manager.auto_promote(fluent, value, condition)
        if not fluent_exp.is_fluent_exp() and not fluent_exp.is_dot():
            raise UPUsageError(
                "fluent field of add_effect must be a Fluent or a FluentExp or a Dot."
            )
        if not self._environment.type_checker.get_type(condition_exp).is_bool_type():
            raise UPTypeError("Effect condition is not a Boolean condition!")
        if not fluent_exp.type.is_compatible(value_exp.type):
            # Value is not assignable to fluent (its type is not a subset of the fluent's type).
            raise UPTypeError(
                f"Event effect has an incompatible value type. Fluent type: {fluent_exp.type} // Value type: {value_exp.type}"
            )
        self._add_effect_instance(
            up.model.effect.Effect(fluent_exp, value_exp, condition_exp, forall=forall)
        )

    def add_increase_effect(
        self,
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
        forall: Iterable["up.model.variable.Variable"] = tuple(),
    ):
        """
        Adds the given `increase effect` to the `event's effects`.

        :param fluent: The `fluent` which `value` is increased.
        :param value: The given `fluent` is incremented by the given `value`.
        :param condition: The `condition` in which this `effect` is applied; the default
            value is `True`.
        :param forall: The 'Variables' that are universally quantified in this
            effect; the default value is empty.
        """
        (
            fluent_exp,
            value_exp,
            condition_exp,
        ) = self._environment.expression_manager.auto_promote(
            fluent,
            value,
            condition,
        )
        if not fluent_exp.is_fluent_exp() and not fluent_exp.is_dot():
            raise UPUsageError(
                "fluent field of add_increase_effect must be a Fluent or a FluentExp or a Dot."
            )
        if not condition_exp.type.is_bool_type():
            raise UPTypeError("Effect condition is not a Boolean condition!")
        if not fluent_exp.type.is_compatible(value_exp.type):
            raise UPTypeError(
                f"Event effect has an incompatible value type. Fluent type: {fluent_exp.type} // Value type: {value_exp.type}"
            )
        if not fluent_exp.type.is_int_type() and not fluent_exp.type.is_real_type():
            raise UPTypeError("Increase effects can be created only on numeric types!")
        self._add_effect_instance(
            up.model.effect.Effect(
                fluent_exp,
                value_exp,
                condition_exp,
                kind=up.model.effect.EffectKind.INCREASE,
                forall=forall,
            )
        )

    def add_decrease_effect(
        self,
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
        forall: Iterable["up.model.variable.Variable"] = tuple(),
    ):
        """
        Adds the given `decrease effect` to the `event's effects`.

        :param fluent: The `fluent` which value is decreased.
        :param value: The given `fluent` is decremented by the given `value`.
        :param condition: The `condition` in which this `effect` is applied; the default
            value is `True`.
        :param forall: The 'Variables' that are universally quantified in this
            effect; the default value is empty.
        """
        (
            fluent_exp,
            value_exp,
            condition_exp,
        ) = self._environment.expression_manager.auto_promote(fluent, value, condition)
        if not fluent_exp.is_fluent_exp() and not fluent_exp.is_dot():
            raise UPUsageError(
                "fluent field of add_decrease_effect must be a Fluent or a FluentExp or a Dot."
            )
        if not condition_exp.type.is_bool_type():
            raise UPTypeError("Effect condition is not a Boolean condition!")
        if not fluent_exp.type.is_compatible(value_exp.type):
            raise UPTypeError(
                f"Event effect has an incompatible value type. Fluent type: {fluent_exp.type} // Value type: {value_exp.type}"
            )
        if not fluent_exp.type.is_int_type() and not fluent_exp.type.is_real_type():
            raise UPTypeError("Decrease effects can be created only on numeric types!")
        self._add_effect_instance(
            up.model.effect.Effect(
                fluent_exp,
                value_exp,
                condition_exp,
                kind=up.model.effect.EffectKind.DECREASE,
                forall=forall,
            )
        )

    def _add_effect_instance(self, effect: "up.model.effect.Effect"):
        assert (
            effect.environment == self._environment
        ), "effect does not have the same environment of the event"
        up.model.effect.check_conflicting_effects(
            effect,
            None,
            None,
            self._fluents_assigned,
            self._fluents_inc_dec,
            "event",
        )
        self._effects.append(effect)

    def __repr__(self) -> str:
        s = []
        s.append(f"event {self.name}")
        self._print_parameters(s)
        s.append(" {\n")
        s.append("    preconditions = [\n")
        for c in self.preconditions:
            s.append(f"      {str(c)}\n")
        s.append("    ]\n")
        s.append("    effects = [\n")
        for e in self.effects:
            s.append(f"      {str(e)}\n")
        s.append("    ]\n")
        s.append("  }")
        return "".join(s)
