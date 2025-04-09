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

from typing import Optional, List, Dict, Tuple

import unified_planning as up
from unified_planning.model.expression import ConstantExpression
from unified_planning.model.scheduling import SchedulingProblem
from unified_planning.model.tamp import MotionActivity
from unified_planning.exceptions import UPTypeError


class SchedulingMotionProblem(SchedulingProblem):

    def __init__(
        self,
        name: Optional[str] = None,
        environment: Optional["up.environment.Environment"] = None,
        *,
        initial_defaults: Dict["up.model.types.Type", "ConstantExpression"] = {},
    ):
        SchedulingProblem.__init__(
            self, name, environment, initial_defaults=initial_defaults
        )
        self._motion_activities: List[MotionActivity] = []
        self._inital_configuration: List[Tuple["up.model.FNode", "up.model.FNode"]] = []

    def __repr__(self) -> str:
        s = [super().__repr__()]
        s.append("initial configuration:")
        for (movable, config) in self._inital_configuration:
            s.append(f"  {movable}: {config}")
        return "\n".join(s)

    def __eq__(self, oth: object) -> bool:
        if not isinstance(oth, SchedulingMotionProblem):
            return False
        return (
            super().__eq__(oth)
            # TODO
            # and self._motion_activities == oth._motion_activities
        )

    def __hash__(self) -> int:
        return super().__hash__()

    @property
    def kind(self) -> "up.model.problem_kind.ProblemKind":
        # TODO
        problem_kind = super().kind
        problem_kind.set_problem_class("SAMP")
        return problem_kind

    def clone(self):
        """Returns an equivalent problem."""
        new_p = super().clone()
        new_p._motion_activities = self.motion_activities
        return new_p

    def add_motion_activity(
        self, name: str, duration: int = 0, optional: bool = False
    ) -> "MotionActivity":
        """Adds a motion activity to the problem."""
        act = MotionActivity(name, duration, optional)
        self._activities.append(act)
        self._motion_activities.append(act)
        return act

    @property
    def motion_activities(self) -> List["MotionActivity"]:
        """Returns the list of motion activities in this problem."""
        return self._motion_activities

    def set_initial_configuration(
        self,
        movable: "up.model.expression.Expression",
        config: "up.model.expression.Expression",
    ):
        (movable_exp, config_exp) = self.environment.expression_manager.auto_promote(
            movable, config
        )
        if not self.environment.type_checker.get_type(movable_exp).is_movable_type():
            raise UPTypeError("movable parameter must be of movable type!")
        if not self.environment.type_checker.get_type(
            config_exp
        ).is_configuration_type():
            raise UPTypeError("config parameter must be of configuration type!")

        self._inital_configuration.append((movable_exp, config_exp))
