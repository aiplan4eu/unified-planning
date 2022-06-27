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
'''
This module defines the Fluent class.
A Fluent has a name, a type and a signature
that defines the types of its parameters.
'''

import unified_planning as up
from unified_planning.environment import get_env, Environment
from typing import List, OrderedDict, Optional, Union


class Fluent:
    '''Represents a fluent.'''
    def __init__(self, name: str, typename: 'up.model.types.Type' = None,
                 _signature: Optional[Union[OrderedDict[str, 'up.model.types.Type'], List['up.model.parameter.Parameter']]] = None,
                 env: Environment = None, **kwargs: 'up.model.types.Type'):
        self._env = get_env(env)
        self._name = name
        if typename is None:
            self._typename = self._env.type_manager.BoolType()
        else:
            self._typename = typename
        self._signature: List['up.model.parameter.Parameter'] = []
        if _signature is not None:
            assert len(kwargs) == 0
            if isinstance(_signature, OrderedDict):
                for param_name, param_type in _signature.items():
                    self._signature.append(up.model.parameter.Parameter(param_name, param_type))
            elif isinstance(_signature, List):
                self._signature = _signature[:]
            else:
                raise NotImplementedError
        else:
            for param_name, param_type in kwargs.items():
                self._signature.append(up.model.parameter.Parameter(param_name, param_type))

    def __repr__(self) -> str:
        sign = ''
        if self.arity > 0:
            sign_items = [f'{p.name}={str(p.type)}' for p in self.signature]
            sign = f'[{", ".join(sign_items)}]'
        return f'{str(self.type)} {self.name}{sign}'

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Fluent):
            return self._name == oth._name and self._typename == oth._typename and self._signature == oth._signature and self._env == oth._env
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._typename)
        for p in self._signature:
            res += hash(p)
        return res ^ hash(self._name)

    @property
    def name(self) -> str:
        '''Returns the fluent name.'''
        return self._name

    @property
    def type(self) -> 'up.model.types.Type':
        '''Returns the fluent type.'''
        return self._typename

    @property
    def signature(self) -> List['up.model.parameter.Parameter']:
        '''Returns the fluent signature.
        The signature is the List of Parameters.
        '''
        return self._signature

    @property
    def arity(self) -> int:
        '''Returns the fluent arity.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible.'''
        return len(self._signature)

    def __call__(self, *args: 'up.model.expression.Expression') -> 'up.model.fnode.FNode':
        '''Returns a fluent expression with the given parameters.'''
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
