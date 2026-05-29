# Copyright 2026 Unified Planning library and its maintainers
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

from unified_planning.plans.schedule import Schedule, Variable, Value
from unified_planning.model.scheduling import Activity
from unified_planning.environment import Environment
from unified_planning.model.motion.activity import MotionActivity
from unified_planning.model.motion.constraint import MotionConstraint
from typing import Optional, Tuple, List, Dict


class MotionSchedule(Schedule):
    """
    This class represents the solution of a scheduling and motion planning problem.

    In addition to a `Schedule`, it carries the geometric `motion_paths` computed for each
    `(MotionActivity, MotionConstraint)` pair of the problem.
    """

    def __init__(
        self,
        activities: Optional[List[Activity]] = None,
        assignment: Optional[Dict[Variable, Value]] = None,
        motion_paths: Dict[
            Tuple[MotionActivity, MotionConstraint], List[Tuple[float, ...]]
        ] = {},
        environment: Optional[Environment] = None,
    ):
        super().__init__(activities, assignment, environment)
        self._motion_paths = motion_paths

    @property
    def motion_paths(
        self,
    ) -> Dict[Tuple[MotionActivity, MotionConstraint], List[Tuple[float, ...]]]:
        """Returns the geometric path computed for each `(MotionActivity, MotionConstraint)` pair."""
        return self._motion_paths

    @motion_paths.setter
    def motion_paths(
        self,
        motion_paths: Dict[
            Tuple[MotionActivity, MotionConstraint], List[Tuple[float, ...]]
        ],
    ):
        """Sets the geometric path for each `(MotionActivity, MotionConstraint)` pair."""
        self._motion_paths = motion_paths
