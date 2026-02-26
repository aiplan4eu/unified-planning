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

from abc import ABC
from dataclasses import dataclass
from typing import Tuple, List

from unified_planning.model.tamp.objects import SE2, SE3


class Path(ABC):
    """
    This class represents a geometric path.
    A geometric path is a list of waypoints,
    either in the joint space or in the operating space of the robot,
    usually bringing the robot from an initial to a final configuration.
    """

    pass


@dataclass(eq=True, frozen=True)
class SE2Path(Path):
    """
    This class represents an SE2 Path.
    It is composed of a list of tuple where each element is a waypoint (e.g., pose of the robot in N-d space).
    """

    path: List[SE2]


@dataclass(eq=True, frozen=True)
class SE3Path(Path):
    """
    This class represents an SE3 Path.
    It is composed of a list of tuple where each element is a waypoint (e.g., pose of the robot in N-d space).
    """

    path: List[SE3]


@dataclass(eq=True, frozen=True)
class SE2WithControlsPath(Path):
    """
    This class represents a ReedsShepp Path.
    It is composed of a list of tuple where:
    - the first element is the waypoint (e.g., pose of the robot in N-d space);
    - the second element is the linear velocity to be applied at that waypoint.
    - the third element is the angular velocity to be applied at that waypoint.
    - the fourth element is the duration of the applied control.
    """

    path: List[Tuple[SE2, float, float, float]]
