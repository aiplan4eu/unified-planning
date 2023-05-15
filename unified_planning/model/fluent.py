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
This module defines the Fluent class.
A Fluent has a name, a type and a signature
that defines the types of its parameters.
"""

import unified_planning as up
from unified_planning.model.types import domain_size, domain_item, _IntType
from unified_planning.environment import get_environment, Environment
from unified_planning.exceptions import UPTypeError
from typing import List, OrderedDict, Optional, Union, Iterator, cast


class Fluent:
    """Represents a fluent."""

    def __init__(
        self,
        name: str,
        typename: Optional["up.model.types.Type"] = None,
        _signature: Optional[
            Union[
                OrderedDict[str, "up.model.types.Type"],
                List["up.model.parameter.Parameter"],
            ]
        ] = None,
        environment: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        self._env = get_environment(environment)
        self._name = name
        if typename is None:
            self._typename = self._env.type_manager.BoolType()
        else:
            assert self._env.type_manager.has_type(
                typename
            ), "type of parameter does not belong to the same environment of the fluent"
            self._typename = typename
        self._signature: List["up.model.parameter.Parameter"] = []
        if _signature is not None:
            assert len(kwargs) == 0
            if isinstance(_signature, OrderedDict):
                for param_name, param_type in _signature.items():
                    self._signature.append(
                        up.model.parameter.Parameter(param_name, param_type, self._env)
                    )
            elif isinstance(_signature, List):
                assert all(
                    p.environment == self._env for p in _signature
                ), "one of the parameters does not belong to the same environment of the fluent"
                self._signature = _signature[:]
            else:
                raise NotImplementedError
        else:
            for param_name, param_type in kwargs.items():
                self._signature.append(
                    up.model.parameter.Parameter(param_name, param_type, self._env)
                )
        for param in self._signature:
            pt = param.type
            if pt.is_real_type() or (
                pt.is_int_type()
                and (
                    cast(_IntType, pt).lower_bound is None
                    or cast(_IntType, pt).upper_bound is None
                )
            ):
                raise UPTypeError(
                    f"Parameter {param} of fluent {name} has type {pt}; fluents parameters must have finite domains."
                )

    def __repr__(self) -> str:
        sign = ""
        if self.arity > 0:
            sign_items = [f"{p.name}={str(p.type)}" for p in self.signature]
            sign = f'[{", ".join(sign_items)}]'
        return f"{str(self.type)} {self.name}{sign}"

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Fluent):
            return (
                self._name == oth._name
                and self._typename == oth._typename
                and self._signature == oth._signature
                and self._env == oth._env
            )
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._typename)
        for p in self._signature:
            res += hash(p)
        return res ^ hash(self._name)

    @property
    def name(self) -> str:
        """Returns the `Fluent` `name`."""
        return self._name

    @property
    def type(self) -> "up.model.types.Type":
        """Returns the `Fluent` `Type`."""
        return self._typename

    @property
    def signature(self) -> List["up.model.parameter.Parameter"]:
        """
        Returns the `Fluent` `signature`.
        The `signature` is the `List` of `Parameters` indicating the :class:`Types <unified_planning.model.Type>` compatible with this `Fluent`.
        """
        return self._signature

    @property
    def arity(self) -> int:
        """
        Returns the `Fluent` arity.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible.
        """
        return len(self._signature)

    @property
    def environment(self) -> "Environment":
        """Returns the `Fluent` `Environment`."""
        return self._env

    def __call__(
        self, *args: "up.model.expression.Expression"
    ) -> "up.model.fnode.FNode":
        """
        Returns a fluent expression with the given parameters.

        :param args: The expressions used as this fluent's parameters in the created expression.
        :return: The created FluentExp.
        """
        return self._env.expression_manager.FluentExp(self, args)

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


def get_ith_fluent_exp(
    objects_set: "up.model.mixins.ObjectsSetMixin",
    fluent: "up.model.fluent.Fluent",
    domain_sizes: List[int],
    idx: int,
) -> "up.model.fnode.FNode":
    """Returns the ith ground fluent expression."""
    quot = idx
    rem = 0
    actual_parameters = []
    for i, p in enumerate(fluent.signature):
        ds = domain_sizes[i]
        rem = quot % ds
        quot //= ds
        v = domain_item(objects_set, p.type, rem)
        actual_parameters.append(v)
    return fluent(*actual_parameters)


def get_all_fluent_exp(
    objects_set: "up.model.mixins.ObjectsSetMixin",
    fluent: "up.model.fluent.Fluent",
) -> Iterator["up.model.fnode.FNode"]:
    if fluent.arity == 0:
        yield fluent.environment.expression_manager.FluentExp(fluent)
    else:
        ground_size = 1
        domain_sizes = []
        for p in fluent.signature:
            ds = domain_size(objects_set, p.type)
            domain_sizes.append(ds)
            ground_size *= ds
        for i in range(ground_size):
            yield get_ith_fluent_exp(objects_set, fluent, domain_sizes, i)
