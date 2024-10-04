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
# copyright info is not up to date as of september 27th 2024
"""
This module defines the InterpretedFunction class.
An InterpretedFunction has a name, a return type, a signature
that defines the types of its parameters and its code.
Due to the way some functions work in Python,
problems containing interpreted functions are currently
not supported by the parallel planners
"""

import unified_planning as up
from unified_planning.model.types import domain_size, domain_item, _IntType
from unified_planning.environment import get_environment, Environment
from unified_planning.exceptions import UPTypeError
from typing import List, OrderedDict, Optional, Union, Iterator, cast, Callable


class InterpretedFunction:
    """Represents an interpreted function."""

    def __init__(
        self,
        name: str,
        return_type: "up.model.types.Type",
        _signature: OrderedDict[str, "up.model.types.Type"],
        function: Callable,
        environment: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        self._env = get_environment(environment)
        self._name = name
        self._function = function
        assert self._env.type_manager.has_type(
            return_type
        ), "type of parameter does not belong to the same environment of the interpreted function"
        self._return_type = return_type
        self._signature: List["up.model.parameter.Parameter"] = []
        if _signature is not None:
            assert len(kwargs) == 0
            if isinstance(_signature, OrderedDict):
                for param_name, param_type in _signature.items():
                    self._signature.append(
                        up.model.parameter.Parameter(param_name, param_type, self._env)
                    )
            else:
                raise NotImplementedError
        else:
            for param_name, param_type in kwargs.items():
                self._signature.append(
                    up.model.parameter.Parameter(param_name, param_type, self._env)
                )

    def __repr__(self) -> str:
        sign = ""
        if self.arity > 0:
            sign_items = [f"{p.name}={str(p.type)}" for p in self.signature]
            sign = f'[{", ".join(sign_items)}]'
        return f"{str(self.return_type)} {self.name}{sign}"

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, InterpretedFunction):
            return (
                self._name == oth._name
                and self._return_type == oth._return_type
                and self._signature == oth._signature
                and self._env == oth._env
                and self._function == oth._function
            )
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._return_type)
        for p in self._signature:
            res += hash(p)
        return res ^ hash(self._name)

    def __getstate__(self):
        state = self.__dict__.copy()
        # removing the function here so that pickler does not get mad at us
        # interpreted functions in parallel problems won't work
        state["_function"] = None
        return state

    @property
    def function(self) -> Callable:
        """Returns the `InterpretedFunction` `function`."""
        return self._function

    @property
    def name(self) -> str:
        """Returns the `InterpretedFunction` `name`."""
        return self._name

    @property
    def return_type(self) -> "up.model.types.Type":
        """Returns the `InterpretedFunction` expected return `Type`."""
        return self._return_type

    @property
    def signature(self) -> List["up.model.parameter.Parameter"]:
        """
        Returns the `InterpretedFunction` `signature`.
        The `signature` is the `List` of `Parameters` indicating the :class:`Types <unified_planning.model.Type>` compatible with this `InterpretedFunction`.
        """
        return self._signature

    @property
    def arity(self) -> int:
        """
        Returns the `InterpretedFunction` arity.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible.
        """
        return len(self._signature)

    @property
    def environment(self) -> "Environment":
        """Returns the `InterpretedFunction` `Environment`."""
        return self._env

    def __call__(
        self, *args: "up.model.expression.Expression"
    ) -> "up.model.fnode.FNode":
        """
        Returns an interpreted function expression with the given parameters.

        :param args: The expressions used as this interpreted function's parameters in the created expression.
        :return: The created InterpretedFunctionExp.
        """
        return self._env.expression_manager.InterpretedFunctionExp(self, args)

    #
    # Infix operators
    #

    def __add__(self, right):
        return self._env.expression_manager.Plus(self, right)

    def __radd__(self, left):
        return self._env.expression_manager.Plus(left, self)

    def __sub__(self, right):
        return self._env.expression_manager.Minus(self, right)

    def __rsub__(self, left):
        return self._env.expression_manager.Minus(left, self)

    def __mul__(self, right):
        return self._env.expression_manager.Times(self, right)

    def __rmul__(self, left):
        return self._env.expression_manager.Times(left, self)

    def __truediv__(self, right):
        return self._env.expression_manager.Div(self, right)

    def __rtruediv__(self, left):
        return self._env.expression_manager.Div(left, self)

    def __floordiv__(self, right):
        return self._env.expression_manager.Div(self, right)

    def __rfloordiv__(self, left):
        return self._env.expression_manager.Div(left, self)

    def __gt__(self, right):
        return self._env.expression_manager.GT(self, right)

    def __ge__(self, right):
        return self._env.expression_manager.GE(self, right)

    def __lt__(self, right):
        return self._env.expression_manager.LT(self, right)

    def __le__(self, right):
        return self._env.expression_manager.LE(self, right)

    def __pos__(self):
        return self._env.expression_manager.Plus(0, self)

    def __neg__(self):
        return self._env.expression_manager.Minus(0, self)

    def Equals(self, right):
        return self._env.expression_manager.Equals(self, right)

    def And(self, *other):
        return self._env.expression_manager.And(self, *other)

    def __and__(self, *other):
        return self._env.expression_manager.And(self, *other)

    def __rand__(self, *other):
        return self._env.expression_manager.And(*other, self)

    def Or(self, *other):
        return self._env.expression_manager.Or(self, *other)

    def __or__(self, *other):
        return self._env.expression_manager.Or(self, *other)

    def __ror__(self, *other):
        return self._env.expression_manager.Or(*other, self)

    def Not(self):
        return self._env.expression_manager.Not(self)

    def __invert__(self):
        return self._env.expression_manager.Not(self)

    def Xor(self, *other):
        em = self._env.expression_manager
        return em.And(em.Or(self, *other), em.Not(em.And(self, *other)))

    def __xor__(self, *other):
        em = self._env.expression_manager
        return em.And(em.Or(self, *other), em.Not(em.And(self, *other)))

    def __rxor__(self, other):
        em = self._env.expression_manager
        return em.And(em.Or(*other, self), em.Not(em.And(*other, self)))

    def Implies(self, right):
        return self._env.expression_manager.Implies(self, right)

    def Iff(self, right):
        return self._env.expression_manager.Iff(self, right)
