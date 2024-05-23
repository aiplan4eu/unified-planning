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

from enum import Enum, auto
from typing import Dict, Optional, Any, Tuple, List
from unified_planning.model import Object
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
import unified_planning.model.types


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
    SE2Control = auto()


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
        model: Optional[str] = None,
        motion_model: MotionModels,
        parameters: Dict[str, Any],
        env: Optional[Environment] = None,
    ):
        super().__init__(name, typename, env)
        if model is None and footprint is None:
            raise UPUsageError(
                "One of `model` or `footprint` paramters must be specified!"
            )
        self._footprint = footprint
        self._model = model
        self._motion_model = motion_model
        self._parameters = parameters

    @property
    def model(self) -> Optional[str]:
        """Returns the model of this `MovableObject` (i.e., its geometry, kinematic model, and dynamic model)."""
        return self._model

    @property
    def footprint(self) -> Optional[List[Tuple[float, float]]]:
        """Returns the footprint of this `MovableObject`."""
        return self._footprint

    @property
    def motion_model(self) -> MotionModels:
        """Returns the motion model of this `MovableObject`."""
        return self._motion_model

    @property
    def parameters(self) -> Dict[str, Any]:
        """Returns the `dict` of parameters of the motion model of this `MovableObject`."""
        return self._parameters


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
        configuration: Tuple[float, ...],
        env: Optional[Environment] = None,
    ):
        super().__init__(name, typename, env)
        self._configuration = configuration

    @property
    def configuration(self) -> Tuple[float, ...]:
        """Returns the configuration of this `ConfigurationObject`."""
        return self._configuration
