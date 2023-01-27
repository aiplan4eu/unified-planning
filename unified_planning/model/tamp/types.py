# Copyright 2023 AIPlan4EU project
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

from typing import Tuple, Optional
from dataclasses import dataclass
from unified_planning.model.types import _UserType, Type
from unified_planning.exceptions import UPTypeError


class _MovableType(_UserType):
    """Represents the movable type."""

    def __init__(self, name: str, father: Optional[Type] = None):
        super().__init__(name, father)
        if father is not None and (not father.is_movable_type()):
            raise UPTypeError("father field of a MovableType must be a MovableType.")

    def is_movable_type(self) -> bool:
        return True


@dataclass
class OccupancyMap:
    """
    This class represents an occupancy map.

    An occupancy map is a representation of the free and occupied working space,
    where occupied areas represents the fixed obstacles.
    The map is characterized by a frame of reference, that is a set of coordinates
    that can be used to determine positions and velocities of objects in that frame.
    """

    filename: str
    reference_frame: Tuple[int, ...]


class _ConfigurationType(_UserType):
    """Represents the configuration type."""

    def __init__(self, name: str, occupancy_map: OccupancyMap, size: int):
        super().__init__(name, None)
        self._size = size
        self._occupancy_map = occupancy_map

    @property
    def size(self) -> int:
        """Returns the size of this `ConfigurationType` (e.g., the number of Degrees of Freedom involved in the configuration)."""
        return self._size

    @property
    def occupancy_map(self) -> OccupancyMap:
        """Returns the occupancy map of this `ConfigurationType`."""
        return self._occupancy_map

    def is_configuration_type(self) -> bool:
        return True
