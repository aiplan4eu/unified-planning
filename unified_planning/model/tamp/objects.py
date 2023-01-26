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

from enum import Enum, auto
from typing import Dict, Optional, Any, Tuple
from unified_planning.model import Object
from unified_planning.environment import Environment
import unified_planning.model.types


class MotionModels(Enum):
    REEDSSHEPP = auto()


class MovableObject(Object):
    def __init__(
        self,
        name: str,
        typename: "unified_planning.model.types.Type",
        model: str,
        motion_model: MotionModels,
        parameters: Dict[str, Any],
        env: Optional[Environment] = None,
    ):
        super().__init__(name, typename, env)
        self._model = model
        self._motion_model = motion_model
        self._parameters = parameters

    @property
    def model(self) -> str:
        return self._model

    @property
    def motion_model(self) -> MotionModels:
        return self._motion_model

    @property
    def parameters(self) -> Dict[str, Any]:
        return self._parameters


class ConfigurationObject(Object):
    def __init__(
        self,
        name: str,
        typename: "unified_planning.model.types.Type",
        configuration: Tuple[int, ...],
        env: Optional[Environment] = None,
    ):
        super().__init__(name, typename, env)
        self._configuration = configuration

    @property
    def configuration(self) -> Tuple[int, ...]:
        return self._configuration
