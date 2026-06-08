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
from enum import Enum, auto
from typing import Dict, Optional, Any, Tuple, List, Callable

from unified_planning.model import Object
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
import unified_planning.model.types


class ConfigurationKind(Enum):
    """
    This class represents the kind of a configuration space.

    It identifies the structure of the configurations a movable object can assume,
    such as `SE2` (planar) or `SE3` (spatial) poses.
    """

    SE2 = auto()
    SE3 = auto()


class ConfigurationInstance(ABC):
    """
    Abstract base class for concrete configurations.

    Configuration instances represent the state of a movable object in a
    configuration space, such as an SE2 or SE3 pose.
    """

    pass


@dataclass(eq=True, frozen=True)
class SE2(ConfigurationInstance):
    """
    This dataclass represents a configuration of type (x, y, theta)
    """

    x: float
    y: float
    theta: float

    def __iter__(self):
        return iter((self.x, self.y, self.theta))

    def __len__(self):
        return 3

    def __getitem__(self, i):
        return (self.x, self.y, self.theta)[i]


@dataclass(eq=True, frozen=True)
class SE3(ConfigurationInstance):
    """
    This dataclass represents a configuration of type (x, y, z, rx, ry, rz, rw)
    """

    x: float
    y: float
    z: float
    rx: float
    ry: float
    rz: float
    rw: float

    def __iter__(self):
        return iter((self.x, self.y, self.z, self.rx, self.ry, self.rz, self.rw))

    def __len__(self):
        return 7

    def __getitem__(self, i):
        return (self.x, self.y, self.z, self.rx, self.ry, self.rz, self.rw)[i]


class MotionModels(Enum):
    """
    This class represents the set of available motion models.

    A motion model describes how a movable object moves with respect to time
    and is usually expressed as an equation of motion governing the transition of
    object states, such as position and velocity.
    """

    REEDSSHEPP = auto()
    SE2 = auto()
    SE3 = auto()


class MovableObject(Object):
    """
    This class represents a movable object.

    A movable object is an object able to move in an environment
    according to a certain motion model. Such an object is characterized
    by a certain geometry as well as a kinematic and dynamic model.
    """

    def __init__(
        self,
        name: str,
        typename: "unified_planning.model.types.Type",
        *,
        footprint: Optional[List[Tuple[float, float]]] = None,
        geometric_model: Optional[str] = None,
        motion_model: MotionModels,
        motion_parameters: Optional[Dict[str, Any]] = None,
        control_model: Optional[Callable] = None,
        control_parameters: Optional[Dict[str, Any]] = None,
        env: Optional[Environment] = None,
    ):
        super().__init__(name, typename, env)
        if geometric_model is None and footprint is None:
            raise UPUsageError(
                "One of `model` or `footprint` parameters must be specified!"
            )
        self._footprint = footprint
        self._geometric_model = geometric_model
        self._motion_model = motion_model
        self._motion_parameters = motion_parameters
        self._control_model = control_model
        self._control_parameters = control_parameters

    def __eq__(self, oth: object) -> bool:
        return (
            isinstance(oth, MovableObject)
            and super().__eq__(oth)
            and self._footprint == oth._footprint
            and self._geometric_model == oth._geometric_model
            and self._motion_model == oth._motion_model
            and self._motion_parameters == oth._motion_parameters
            and self._control_model == oth._control_model
            and self._control_parameters == oth._control_parameters
        )

    def __hash__(self) -> int:
        return super().__hash__() + hash(
            (
                tuple(self._footprint) if self._footprint is not None else None,
                self._geometric_model,
                self._motion_model,
                (
                    frozenset(self._motion_parameters.items())
                    if self._motion_parameters is not None
                    else None
                ),
                self._control_model,
                (
                    frozenset(self._control_parameters.items())
                    if self._control_parameters is not None
                    else None
                ),
            )
        )

    @property
    def geometric_model(self) -> Optional[str]:
        """Returns the geometric model of this `MovableObject` (i.e., its geometry, kinematic model, and dynamic model)."""
        return self._geometric_model

    @property
    def footprint(self) -> Optional[List[Tuple[float, float]]]:
        """Returns the footprint of this `MovableObject`."""
        return self._footprint

    @property
    def motion_model(self) -> MotionModels:
        """Returns the motion model of this `MovableObject`."""
        return self._motion_model

    @property
    def motion_parameters(self) -> Optional[Dict[str, Any]]:
        """Returns the `dict` of motion parameters of the motion model of this `MovableObject`."""
        return self._motion_parameters

    @property
    def control_model(self) -> Optional[Callable]:
        """Returns the control model of this `MovableObject`."""
        return self._control_model

    @property
    def control_parameters(self) -> Optional[Dict[str, Any]]:
        """Returns the `dict` of control parameters of the motion model of this `MovableObject`."""
        return self._control_parameters


class ConfigurationObject(Object):
    """
    This class represents a configuration object.

    A configuration of a movable object at a certain time is the description of its state
    at that moment in time.
    """

    def __init__(
        self,
        name: str,
        typename: "unified_planning.model.types.Type",
        configuration: ConfigurationInstance,
        env: Optional[Environment] = None,
    ):
        super().__init__(name, typename, env)
        self._configuration = configuration

    def __eq__(self, oth: object) -> bool:
        return (
            isinstance(oth, ConfigurationObject)
            and super().__eq__(oth)
            and self._configuration == oth._configuration
        )

    def __hash__(self) -> int:
        return super().__hash__() + hash(self._configuration)

    @property
    def configuration(self) -> ConfigurationInstance:
        """Returns the `ConfigurationInstance` of this `ConfigurationObject`."""
        return self._configuration
