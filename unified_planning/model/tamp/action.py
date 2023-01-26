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


import unified_planning as up
from unified_planning.environment import Environment, get_env
from unified_planning.model import InstantaneousAction
from unified_planning.exceptions import UPTypeError
from typing import Optional, List
from collections import OrderedDict


class MotionConstraint:
    def __init__(self, env: Optional[Environment] = None):
        self._env = get_env(env)

    def __eq__(self, oth) -> bool:
        raise NotImplementedError

    def __hash__(self) -> int:
        raise NotImplementedError


class Waypoints(MotionConstraint):
    def __init__(
        self,
        movable: "up.model.expression.Expression",
        starting: "up.model.expression.Expression",
        waypoints: List["up.model.expression.Expression"],
        env: Optional[Environment] = None,
    ):
        super().__init__(env)
        (movable_exp,) = self._env.expression_manager.auto_promote(movable)
        if not self._env.type_checker.get_type(movable_exp).is_movable_type():
            raise UPTypeError(
                "First parameter of Waypoints's constructor must be of movable type!"
            )
        starting_exp, *waypoints_exp = self._env.expression_manager.auto_promote(
            starting, *waypoints
        )
        t = self._env.type_checker.get_type(starting_exp)
        if not t.is_configuration_type():
            raise UPTypeError(
                "starting parameter of Waypoints's constructor must be of configuration type!"
            )
        for p in waypoints_exp:
            pt = self._env.type_checker.get_type(p)
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

    def __eq__(self, oth) -> bool:
        if not isinstance(oth, Waypoints) or self._env != oth._env:
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

    @property
    def movable(self) -> "up.model.fnode.FNode":
        return self._movable

    @property
    def starting(self) -> "up.model.fnode.FNode":
        return self._starting

    @property
    def waypoints(self) -> List["up.model.fnode.FNode"]:
        return self._waypoints


class InstantaneousMotionAction(InstantaneousAction):
    """This class represents an instantaneous motion action."""

    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _env: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        InstantaneousAction.__init__(self, _name, _parameters, _env, **kwargs)
        self._motion_constraints: List[MotionConstraint] = []

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, InstantaneousMotionAction):
            return super().__eq__(oth) and set(self._motion_constraints) == set(
                oth._motion_constraints
            )
        else:
            return False

    def __hash__(self) -> int:
        res = super().__hash__()
        for of in self._motion_constraints:
            res += hash(of)
        return res

    def clone(self):
        new_params = OrderedDict()
        for param_name, param in self._parameters.items():
            new_params[param_name] = param.type
        new_motion_action = InstantaneousMotionAction(self._name, new_params, self._env)
        new_motion_action._preconditions = self._preconditions[:]
        new_motion_action._effects = [e.clone() for e in self._effects]
        new_motion_action._fluents_assigned = self._fluents_assigned.copy()
        new_motion_action._fluents_inc_dec = self._fluents_inc_dec.copy()
        new_motion_action._simulated_effect = self._simulated_effect
        new_motion_action._motion_constraints = self._motion_constraints.copy()
        return new_motion_action

    def add_motion_constraints(self, motion_constraints: List[MotionConstraint]):
        """
        Adds the given list of motion constraints.

        :param motion_constraints: The list of motion constraints that must be added.
        """
        for of in motion_constraints:
            self.add_motion_constraint(of)

    def add_motion_constraint(self, motion_constraint: MotionConstraint):
        """
        Adds the given motion constraint.

        :param motion_constraint: The motion constraint that must be added.
        """
        self._motion_constraints.append(motion_constraint)

    @property
    def motion_constraints(self) -> List[MotionConstraint]:
        """Returns the `list` motion constraints."""
        return self._motion_constraints

    def __repr__(self) -> str:
        b = InstantaneousAction.__repr__(self)[0:-3]
        s = ["motion-", b]
        s.append("    observations = [\n")
        for e in self._motion_constraints:
            s.append(f"      {str(e)}\n")
        s.append("    ]\n")
        s.append("  }")
        return "".join(s)
