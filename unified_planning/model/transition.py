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

    def is_conditional(self) -> bool:
        """Returns `True` if the `Transition` has `conditional effects`, `False` otherwise."""
        raise NotImplementedError


class SingleTimePointTransitionMixin:
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
