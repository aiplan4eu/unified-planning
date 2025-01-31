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
"""This module defines all the types."""

import unified_planning
from unified_planning.model.expression import NumericConstant, uniform_numeric_constant
from unified_planning.model.tamp.objects import ConfigurationKind
from unified_planning.model.types import (
    Type,
    _IntType,
    _RealType,
    _UserType,
    BOOL,
    TIME,
)
from unified_planning.model.tamp.types import (
    _MovableType,
    _ConfigurationType,
    OccupancyMap,
)
from unified_planning.exceptions import UPTypeError
from fractions import Fraction
from typing import Optional, Dict, Tuple, Union, cast


class TypeManager:
    """Class that manages the :class:`Types <unified_planning.model.Type>` in the :class:`~unified_planning.Environment`."""

    def __init__(self):
        self._bool = BOOL
        self._ints: Dict[Tuple[Optional[int], Optional[int]], Type] = {}
        self._reals: Dict[Tuple[Optional[Fraction], Optional[Fraction]], Type] = {}
        self._user_types: Dict[Tuple[str, Optional[Type]], Type] = {}
        self._movable_types: Dict[Tuple[str, Optional[Type]], Type] = {}
        self._configuration_types: Dict[Tuple[str, OccupancyMap, int], Type] = {}

    def has_type(self, type: Type) -> bool:
        """
        Returns `True` if the given type is already defined in this :class:`~unified_planning.Environment`.

        :param type: The type searched in this `Environment`.
        :return: `True` if the given `type` is found, `False` otherwise.
        """
        if type.is_bool_type():
            return type == self._bool
        elif type.is_int_type():
            assert isinstance(type, _IntType)
            return self._ints.get((type.lower_bound, type.upper_bound), None) == type
        elif type.is_real_type():
            assert isinstance(type, _RealType)
            return self._reals.get((type.lower_bound, type.upper_bound), None) == type
        elif type.is_time_type():
            return type == TIME
        elif type.is_movable_type():
            assert isinstance(type, _MovableType)
            return self._movable_types.get((type.name, type.father), None) == type
        elif type.is_configuration_type():
            assert isinstance(type, _ConfigurationType)
            return (
                self._configuration_types.get(
                    (type.name, type.occupancy_map, type.kind), None
                )
                == type
            )
        elif type.is_user_type():
            assert isinstance(type, _UserType)
            return self._user_types.get((type.name, type.father), None) == type
        else:
            raise NotImplementedError

    def BoolType(self) -> Type:
        """Returns this `Environment's` boolean `Type`."""
        return self._bool

    def IntType(
        self, lower_bound: Optional[int] = None, upper_bound: Optional[int] = None
    ) -> Type:
        """
        Returns the `integer type` defined in this :class:`~unified_planning.Environment` with the given bounds.
        If the `Type` already exists, it is returned, otherwise it is created and returned.

        :param lower_bound: The integer used as this type's lower bound.
        :param upper_bound: The integer used as this type's upper bound.
        :return: The retrieved or created `Type`.
        """
        k = (lower_bound, upper_bound)
        if k in self._ints:
            return self._ints[k]
        else:
            it = _IntType(lower_bound, upper_bound)
            self._ints[k] = it
            return it

    def RealType(
        self,
        lower_bound: Optional[NumericConstant] = None,
        upper_bound: Optional[NumericConstant] = None,
    ) -> Type:
        """
        Returns the `real type` defined in this :class:`~unified_planning.Environment` with the given bounds.
        If the type already exists, it is returned, otherwise it is created and returned.

        :param lower_bound: The number used as this type's lower bound.
        :param upper_bound: The number used as this type's upper bound.
        :return: The retrieved or created `Type`.
        """
        if lower_bound is not None:
            lower_bound = uniform_numeric_constant(lower_bound)
        if upper_bound is not None:
            upper_bound = uniform_numeric_constant(upper_bound)
        if isinstance(lower_bound, int):
            lower_bound = Fraction(lower_bound)
        if isinstance(upper_bound, int):
            upper_bound = Fraction(upper_bound)
        k = (lower_bound, upper_bound)
        if k in self._reals:
            return self._reals[k]
        else:
            rt = _RealType(lower_bound, upper_bound)
            self._reals[k] = rt
            return rt

    def UserType(self, name: str, father: Optional[Type] = None) -> Type:
        """
        Returns the user type defined in this :class:`~unified_planning.Environment` with the given `name` and `father`.
        If the type already exists, it is returned, otherwise it is created and returned.

        :param name: The name of this user type.
        :param father: The user type that must be set as the father for this type.
        :return: The retrieved or created `Type`.
        """
        if (name, father) in self._user_types:
            return self._user_types[(name, father)]
        else:
            if father is not None:
                assert isinstance(father, _UserType)
                if any(
                    cast(_UserType, ancestor).name == name
                    for ancestor in father.ancestors
                ):
                    raise UPTypeError(
                        f"The name: {name} is already used. A UserType and one of his ancestors can not share the name."
                    )
            ut = _UserType(name, father)
            self._user_types[(name, father)] = ut
            return ut

    def MovableType(self, name: str, father: Optional[Type] = None) -> Type:
        """
        Returns the movable type defined in this :class:`~unified_planning.Environment` with the given `name` and `father`.
        If the type already exists, it is returned, otherwise it is created and returned.

        :param name: The name of this movable type.
        :param father: The movable type that must be set as the father for this type.
        :return: The retrieved or created `Type`.
        """
        if (name, father) in self._movable_types:
            return self._movable_types[(name, father)]
        else:
            if father is not None:
                assert isinstance(father, _MovableType)
                if any(
                    cast(_MovableType, ancestor).name == name
                    for ancestor in father.ancestors
                ):
                    raise UPTypeError(
                        f"The name: {name} is already used. A MovableType and one of his ancestors can not share the name."
                    )
            mt = _MovableType(name, father)
            self._movable_types[(name, father)] = mt
            return mt

    def ConfigurationType(
        self, name: str, occupancy_map: OccupancyMap, kind: ConfigurationKind
    ) -> Type:
        """
        Returns the configuration type defined in this :class:`~unified_planning.Environment` with the given `name`,
        `occupancy_map` and `kind`.
        If the type already exists, it is returned, otherwise it is created and returned.

        :param name: The name of this configuration type.
        :param occupancy_map: The occupancy map.
        :param kind: The kind of the configuration.
        :return: The retrieved or created `Type`.
        """
        if (name, occupancy_map, kind) in self._configuration_types:
            return self._configuration_types[(name, occupancy_map, kind)]
        else:
            ct = _ConfigurationType(name, occupancy_map, kind)
            self._configuration_types[(name, occupancy_map, kind)] = ct
            return ct
