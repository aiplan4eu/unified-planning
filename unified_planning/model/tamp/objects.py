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

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, Any, Tuple, List, Callable, Union
from unified_planning.model import Object
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
import unified_planning.model.types


class ConfigurationKind(Enum):
    SE2 = auto()
    SE3 = auto()
    JOINT = auto()
    MULTILINK = auto()


class ConfigurationInstance:
    pass


@dataclass(eq=True, frozen=True)
class SE2(ConfigurationInstance):
    """
    This dataclass represents a configuration of type (x, y, theta)
    """

    x: float
    y: float
    theta: float


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


@dataclass(eq=True, frozen=True)
class Joint(ConfigurationInstance):
    """
    This dataclass represents a configuration of a (eventually) torque controlled joint.

    The configuration (revolute or prismatic) is defined by:
    * the position of the joint (rad or m),
    * the velocity of the joint (rad/s or m/s) and
    * the effort that is applied in the joint (Nm or N).

    Each field is optional. When e.g. your joints have no effort associated with them, you can leave the effort array empty.
    """

    position: Optional[float] = None
    velocty: Optional[float] = None
    effort: Optional[float] = None


@dataclass(eq=True, frozen=True)
class MultiLink(ConfigurationInstance):
    """
    This class represents the configuration of a multi link object.

    """

    base_link = Tuple[str, Union[SE2, SE3]]
    joints = Dict[str, Joint]


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
    def motion_parameters(self) -> Dict[str, Any]:
        """Returns the `dict` of motion parameters of the motion model of this `MovableObject`."""
        return self._motion_parameters

    @property
    def control_model(self) -> Callable:
        """Returns the control model of this `MovableObject`."""
        return self._control_model

    @property
    def control_parameters(self) -> Dict[str, Any]:
        """Returns the `dict` of control parameters of the motion model of this `MovableObject`."""
        return self._control_parameters


class ConfigurationObject(Object):
    """
    This class represents a configuration object.

    A configuration of a movable object at a certain time is the description of its state
    (i.e., the values of its links and joints) at that moment in time.
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

    @property
    def configuration(self) -> ConfigurationInstance:
        """Returns the `ConfigurationInstance` of this `ConfigurationObject`."""
        return self._configuration
