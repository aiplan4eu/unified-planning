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


import unified_planning as up
from unified_planning.environment import Environment, get_environment
from unified_planning.exceptions import UPTypeError
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Union


class MotionConstraint(ABC):
    """
    This class represents a motion constraint.

    A motion constraint is a constraint that must hold true among the continuous parameters of a motion action
    for it to be a legal transition of the system in its workspace.
    """

    def __init__(self, environment: Optional[Environment] = None):
        self._environment = get_environment(environment)

    @abstractmethod
    def __eq__(self, oth) -> bool:
        raise NotImplementedError

    @abstractmethod
    def __hash__(self) -> int:
        raise NotImplementedError

    @property
    def environment(self) -> Environment:
        """Returns the `Environment` in which this MotionConstraint exists."""
        return self._environment


class Waypoints(MotionConstraint):
    """
    This class represents a waypoints contraint.

    The waypoints constraint is a `MotionConstraint` representing the existence of a trajectory
    in the free configuration space of a movable object that lets it traverse a set of input waypoints
    starting from an initial configuration.

    `static_obstacles` is a dictionary that maps those movable obstacles that remain static during the existence of the constraint with their configurations.
    `dynamic_obstacles_at_start` is a dictionary that maps those movable obstacles that may move during the existence of the constraint with their configurations at the beginning of the constraint.
    """

    def __init__(
        self,
        movable: "up.model.expression.Expression",
        starting: "up.model.expression.Expression",
        waypoints: List["up.model.expression.Expression"],
        static_obstacles: Optional[
            Dict["up.model.motion.MovableObject", "up.model.fnode.FNode"]
        ] = None,
        dynamic_obstacles_at_start: Optional[
            Dict["up.model.motion.MovableObject", "up.model.fnode.FNode"]
        ] = None,
        environment: Optional[Environment] = None,
    ):
        super().__init__(environment)
        (movable_exp,) = self._environment.expression_manager.auto_promote(movable)
        if not self._environment.type_checker.get_type(movable_exp).is_movable_type():
            raise UPTypeError(
                "First parameter of Waypoints's constructor must be of movable type!"
            )
        (
            starting_exp,
            *waypoints_exp,
        ) = self._environment.expression_manager.auto_promote(starting, *waypoints)
        t = self._environment.type_checker.get_type(starting_exp)
        if not t.is_configuration_type():
            raise UPTypeError(
                "starting parameter of Waypoints's constructor must be of configuration type!"
            )
        for p in waypoints_exp:
            pt = self._environment.type_checker.get_type(p)
            if not pt.is_configuration_type():
                raise UPTypeError(
                    "waypoints parameter of Waypoints's constructor must be a list of configuration type objects!"
                )
            if t != pt:
                raise UPTypeError(
                    "starting and waypoints must be of the same configuration type!"
                )
        self._movable = movable_exp
        self._starting = starting_exp
        self._waypoints = waypoints_exp
        self._static_obstacles = static_obstacles
        self._dynamic_obstacles_at_start = dynamic_obstacles_at_start

    def __eq__(self, oth) -> bool:
        if not isinstance(oth, Waypoints) or self._environment != oth._environment:
            return False
        if self._movable != oth._movable or self._starting != oth._starting:
            return False
        if set(self._waypoints) != set(oth._waypoints):
            return False
        return True

    def __hash__(self) -> int:
        res = hash(self._movable)
        res += hash(self._starting)
        for p in self._waypoints:
            res += hash(p)
        return res

    def __repr__(self) -> str:
        s = ["waypoints("]
        s.append(str(self.movable))
        s.append(", ")
        s.append(str(self.starting))
        s.append(", ")
        s.append(str(self.waypoints))
        if self.static_obstacles is not None:
            s.append(", ")
            s.append(str(self.static_obstacles))
        if self.dynamic_obstacles_at_start is not None:
            s.append(", ")
            s.append(str(self.dynamic_obstacles_at_start))
        s.append(")")
        return "".join(s)

    @property
    def movable(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the involved movable object."""
        return self._movable

    @property
    def starting(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the starting configuration of the involved movable object."""
        return self._starting

    @property
    def waypoints(self) -> List["up.model.fnode.FNode"]:
        """Returns the `list` of `FNode` representing the set of waypoints that the involved movable object should traverse."""
        return self._waypoints

    @property
    def static_obstacles(
        self,
    ) -> Optional[Dict["up.model.motion.MovableObject", "up.model.fnode.FNode"]]:
        """Returns the set of `MovableObject` associated with the fluent expressions that represent their configuration during all the constraint (static obstacles)."""
        return self._static_obstacles

    @property
    def dynamic_obstacles_at_start(
        self,
    ) -> Optional[Dict["up.model.motion.MovableObject", "up.model.fnode.FNode"]]:
        """Returns the set of `MovableObject` associated with the fluent expressions that represent their configuration at the beginning of the constraint (possibly dynamic obstacles)."""
        return self._dynamic_obstacles_at_start


class ActivityWaypoints(MotionConstraint):

    def __init__(
        self,
        movable: "up.model.expression.Expression",
        starting: "up.model.expression.Expression",
        waypoints: List["up.model.expression.Expression"],
        static_obstacles: Optional[
            Union[
                List["up.model.motion.MovableObject"],
                Dict["up.model.motion.MovableObject", "up.model.Fluent"],
            ]
        ] = None,
        dynamic_obstacles_at_start: Optional[
            Union[
                List["up.model.motion.MovableObject"],
                Dict["up.model.motion.MovableObject", "up.model.Fluent"],
            ]
        ] = None,
        environment: Optional[Environment] = None,
    ):
        super().__init__(environment)
        (movable_exp,) = self._environment.expression_manager.auto_promote(movable)
        if not self._environment.type_checker.get_type(movable_exp).is_movable_type():
            raise UPTypeError(
                "First parameter of Waypoints's constructor must be of movable type!"
            )
        (
            starting_exp,
            *waypoints_exp,
        ) = self._environment.expression_manager.auto_promote(starting, *waypoints)
        t = self._environment.type_checker.get_type(starting_exp)
        if not t.is_configuration_type():
            raise UPTypeError(
                "starting parameter of Waypoints's constructor must be of configuration type!"
            )
        for p in waypoints_exp:
            pt = self._environment.type_checker.get_type(p)
            if not pt.is_configuration_type():
                raise UPTypeError(
                    "waypoints parameter of Waypoints's constructor must be a list of configuration type objects!"
                )
            if t != pt:
                raise UPTypeError(
                    "starting and waypoints must be of the same configuration type!"
                )
        self._movable = movable_exp
        self._starting = starting_exp
        self._waypoints = waypoints_exp
        self._static_obstacles = static_obstacles
        self._dynamic_obstacles_at_start = dynamic_obstacles_at_start

    def __eq__(self, oth) -> bool:
        if not isinstance(oth, Waypoints) or self._environment != oth._environment:
            return False
        if self._movable != oth._movable or self._starting != oth._starting:
            return False
        if set(self._waypoints) != set(oth._waypoints):
            return False
        return True

    def __hash__(self) -> int:
        res = hash(self._movable)
        res += hash(self._starting)
        for p in self._waypoints:
            res += hash(p)
        return res

    def __repr__(self) -> str:
        s = ["waypoints("]
        s.append(str(self.movable))
        s.append(", ")
        s.append(str(self.starting))
        s.append(", ")
        s.append(str(self.waypoints))
        if self.static_obstacles is not None:
            s.append(", ")
            s.append(str(self.static_obstacles))
        if self.dynamic_obstacles_at_start is not None:
            s.append(", ")
            s.append(str(self.dynamic_obstacles_at_start))
        s.append(")")
        return "".join(s)

    @property
    def movable(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the involved movable object."""
        return self._movable

    @property
    def starting(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the starting configuration of the involved movable object."""
        return self._starting

    @property
    def waypoints(self) -> List["up.model.fnode.FNode"]:
        """Returns the `list` of `FNode` representing the set of waypoints that the involved movable object should traverse."""
        return self._waypoints

    @property
    def static_obstacles(
        self,
    ) -> Optional[
        Union[
            List["up.model.motion.MovableObject"],
            Dict["up.model.motion.MovableObject", "up.model.Fluent"],
        ]
    ]:
        return self._static_obstacles

    @property
    def dynamic_obstacles_at_start(
        self,
    ) -> Optional[
        Union[
            List["up.model.motion.MovableObject"],
            Dict["up.model.motion.MovableObject", "up.model.Fluent"],
        ]
    ]:
        return self._dynamic_obstacles_at_start
