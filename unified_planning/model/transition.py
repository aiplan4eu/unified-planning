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
This module defines the `Transition` base class and some of his extensions.
A `Transition` has a `name`, a `list` of `Parameter`, a `list` of `preconditions`
and a `list` of `effects`.
"""


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


class Transition(ABC):
    """This is the `Transition` interface."""

    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _env: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        self._environment = get_environment(_env)
        self._name = _name
        self._parameters: "OrderedDict[str, up.model.parameter.Parameter]" = (
            OrderedDict()
        )
        if _parameters is not None:
            assert len(kwargs) == 0
            for n, t in _parameters.items():
                assert self._environment.type_manager.has_type(
                    t
                ), "type of parameter does not belong to the same environment of the transition"
                self._parameters[n] = up.model.parameter.Parameter(
                    n, t, self._environment
                )
        else:
            for n, t in kwargs.items():
                assert self._environment.type_manager.has_type(
                    t
                ), "type of parameter does not belong to the same environment of the transition"
                self._parameters[n] = up.model.parameter.Parameter(
                    n, t, self._environment
                )

    @abstractmethod
    def __eq__(self, oth: object) -> bool:
        raise NotImplementedError

    def _print_parameters(self, s):
        first = True
        for p in self.parameters:
            if first:
                s.append("(")
                first = False
            else:
                s.append(", ")
            s.append(str(p))
        if not first:
            s.append(")")

    @abstractmethod
    def __hash__(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def clone(self):
        raise NotImplementedError

    def is_conditional(self) -> bool:
        """Returns `True` if the `Transition` has `conditional effects`, `False` otherwise."""
        raise NotImplementedError

    @property
    def environment(self) -> Environment:
        """Returns this `Transition` `Environment`."""
        return self._environment

    @property
    def name(self) -> str:
        """Returns the `Transition `name`."""
        return self._name

    @name.setter
    def name(self, new_name: str):
        """Sets the `Transition` `name`."""
        self._name = new_name

    @property
    def parameters(self) -> List["up.model.parameter.Parameter"]:
        """Returns the `list` of the `Transition parameters`."""
        return list(self._parameters.values())

    def parameter(self, name: str) -> "up.model.parameter.Parameter":
        """
        Returns the `parameter` of the `Transition` with the given `name`.

        Example
        -------
        >>> from unified_planning.shortcuts import *
        >>> location_type = UserType("Location")
        >>> move = InstantaneousAction("move", source=location_type, target=location_type)
        >>> move.parameter("source")  # return the "source" parameter of the transition, with type "Location"
        Location source
        >>> move.parameter("target")
        Location target

        If a parameter's name (1) does not conflict with an existing attribute of `Transition` and (2) does not start with '_'
        it can also be accessed as if it was an attribute of the transition. For instance:

        >>> move.source
        Location source

        :param name: The `name` of the target `parameter`.
        :return: The `parameter` of the `Transition` with the given `name`.
        """
        if name not in self._parameters:
            raise ValueError(f"Transition '{self.name}' has no parameter '{name}'")
        return self._parameters[name]

    def __getattr__(self, parameter_name: str) -> "up.model.parameter.Parameter":
        if parameter_name.startswith("_"):
            # guard access as pickling relies on attribute error to be thrown even when
            # no attributes of the object have been set.
            # In this case accessing `self._name` or `self._parameters`, would re-invoke __getattr__
            raise AttributeError(f"Transition has no attribute '{parameter_name}'")
        if parameter_name not in self._parameters:
            raise AttributeError(
                f"Transition '{self.name}' has no attribute or parameter '{parameter_name}'"
            )
        return self._parameters[parameter_name]


class PreconditionMixin:
    def __init__(self, _env):
        self._preconditions: List["up.model.fnode.FNode"] = []
        self._environment = get_environment(_env)

    @property
    def preconditions(self) -> List["up.model.fnode.FNode"]:
        """Returns the `list` of the `Action` `preconditions`."""
        return self._preconditions

    def clear_preconditions(self):
        """Removes all the `Action preconditions`"""
        self._preconditions = []

    def add_precondition(
        self,
        precondition: Union[
            "up.model.fnode.FNode",
            "up.model.fluent.Fluent",
            "up.model.parameter.Parameter",
            bool,
        ],
    ):
        """
        Adds the given expression to `action's preconditions`.

        :param precondition: The expression that must be added to the `action's preconditions`.
        """
        (precondition_exp,) = self._environment.expression_manager.auto_promote(
            precondition
        )
        assert self._environment.type_checker.get_type(precondition_exp).is_bool_type()
        if precondition_exp == self._environment.expression_manager.TRUE():
            return
        free_vars = self._environment.free_vars_oracle.get_free_variables(
            precondition_exp
        )
        if len(free_vars) != 0:
            raise UPUnboundedVariablesError(
                f"The precondition {str(precondition_exp)} has unbounded variables:\n{str(free_vars)}"
            )
        if precondition_exp not in self._preconditions:
            self._preconditions.append(precondition_exp)

    def _set_preconditions(self, preconditions: List["up.model.fnode.FNode"]):
        self._preconditions = preconditions


class UntimedEffectMixin:
    def __init__(self, _env):
        self._environment = get_environment(_env)
        self._effects: List[up.model.effect.Effect] = []
        self._simulated_effect: Optional[up.model.effect.SimulatedEffect] = None
        # fluent assigned is the mapping of the fluent to it's value if it is an unconditional assignment
        self._fluents_assigned: Dict[
            "up.model.fnode.FNode", "up.model.fnode.FNode"
        ] = {}
        # fluent_inc_dec is the set of the fluents that have an unconditional increase or decrease
        self._fluents_inc_dec: Set["up.model.fnode.FNode"] = set()

    @property
    def effects(self) -> List["up.model.effect.Effect"]:
        """Returns the `list` of the `Action effects`."""
        return self._effects

    def clear_effects(self):
        """Removes all the `Action's effects`."""
        self._effects = []
        self._fluents_assigned = {}
        self._fluents_inc_dec = set()
        self._simulated_effect = None

    @property
    def conditional_effects(self) -> List["up.model.effect.Effect"]:
        """Returns the `list` of the `action conditional effects`.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible."""
        return [e for e in self._effects if e.is_conditional()]

    def is_conditional(self) -> bool:
        """Returns `True` if the `action` has `conditional effects`, `False` otherwise."""
        return any(e.is_conditional() for e in self._effects)

    @property
    def unconditional_effects(self) -> List["up.model.effect.Effect"]:
        """Returns the `list` of the `action unconditional effects`.

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
        Adds the given `assignment` to the `action's effects`.

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
                f"InstantaneousAction effect has an incompatible value type. Fluent type: {fluent_exp.type} // Value type: {value_exp.type}"
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
        Adds the given `increase effect` to the `action's effects`.

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
                f"InstantaneousAction effect has an incompatible value type. Fluent type: {fluent_exp.type} // Value type: {value_exp.type}"
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
        Adds the given `decrease effect` to the `action's effects`.

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
                f"InstantaneousAction effect has an incompatible value type. Fluent type: {fluent_exp.type} // Value type: {value_exp.type}"
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
        ), "effect does not have the same environment of the action"
        up.model.effect.check_conflicting_effects(
            effect,
            None,
            self._simulated_effect,
            self._fluents_assigned,
            self._fluents_inc_dec,
            "action",
        )
        self._effects.append(effect)

    @property
    def simulated_effect(self) -> Optional["up.model.effect.SimulatedEffect"]:
        """Returns the `action` `simulated effect`."""
        return self._simulated_effect

    def set_simulated_effect(self, simulated_effect: "up.model.effect.SimulatedEffect"):
        """
        Sets the given `simulated effect` as the only `action's simulated effect`.

        :param simulated_effect: The `SimulatedEffect` instance that must be set as this `action`'s only
            `simulated effect`.
        """
        up.model.effect.check_conflicting_simulated_effects(
            simulated_effect,
            None,
            self._fluents_assigned,
            self._fluents_inc_dec,
            "action",
        )
        if simulated_effect.environment != self._environment:
            raise UPUsageError(
                "The added SimulatedEffect does not have the same environment of the Action"
            )
        self._simulated_effect = simulated_effect
