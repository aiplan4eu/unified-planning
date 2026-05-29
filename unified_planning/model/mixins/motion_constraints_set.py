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

from typing import Iterable, List, Set
import unified_planning as up


class MotionConstraintsSetMixin:
    """
    This class is a mixin that contains a `set` of `motion constraints` with some related methods.
    """

    def __init__(self):
        self._motion_constraints: List["up.model.motion.MotionConstraint"] = list()
        self._motion_constraints_set: Set["up.model.motion.MotionConstraint"] = set()

    def add_motion_constraints(
        self, motion_constraints: Iterable["up.model.motion.MotionConstraint"]
    ):
        """
        Adds the given motion constraints.

        :param motion_constraints: Iterable of motion constraints to add.
        """
        for mc in motion_constraints:
            self.add_motion_constraint(mc)

    def add_motion_constraint(
        self, motion_constraint: "up.model.motion.MotionConstraint"
    ):
        """
        Adds the given motion constraint.

        :param motion_constraint: The motion constraint to add.
        """
        if motion_constraint not in self._motion_constraints_set:
            self._motion_constraints_set.add(motion_constraint)
            self._motion_constraints.append(motion_constraint)

    def clear_motion_constraints(self):
        """Removes all motion constraints."""
        self._motion_constraints.clear()
        self._motion_constraints_set.clear()

    @property
    def motion_constraints(self) -> List["up.model.motion.MotionConstraint"]:
        """Returns the set of motion constraints."""
        return self._motion_constraints
