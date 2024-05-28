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
from unified_planning.model import InstantaneousAction, DurativeAction
from unified_planning.model.mixins.timed_conds_effs import TimedCondsEffs
from unified_planning.exceptions import UPTypeError
from abc import ABC, abstractmethod
from typing import Optional, List, Iterable, Dict, Union
from collections import OrderedDict

from unified_planning.model.timing import EndTiming, StartTiming, TimeInterval, Timing


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
    """

    def __init__(
        self,
        movable: "up.model.expression.Expression",
        starting: "up.model.expression.Expression",
        waypoints: List["up.model.expression.Expression"],
        obstacles: Optional[
            Dict["up.model.tamp.objects.MovableObject", "up.model.fnode.FNode"]
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
        self._obstacles = obstacles

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
        s.append(", ")
        s.append(str(self.obstacles))
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
    def obstacles(
        self,
    ) -> Optional[Dict["up.model.tamp.objects.MovableObject", "up.model.fnode.FNode"]]:
        """Returns the set of `MovableObject` associated with the fluent expressions that represent their configuration."""
        return self._obstacles


class InstantaneousMotionAction(InstantaneousAction):
    """This class represents an instantaneous motion action."""

    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _environment: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        InstantaneousAction.__init__(self, _name, _parameters, _environment, **kwargs)
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
        new_motion_action = InstantaneousMotionAction(
            self._name, new_params, self._environment
        )
        new_motion_action._preconditions = self._preconditions[:]
        new_motion_action._effects = [e.clone() for e in self._effects]
        new_motion_action._fluents_assigned = self._fluents_assigned.copy()
        new_motion_action._fluents_inc_dec = self._fluents_inc_dec.copy()
        new_motion_action._simulated_effect = self._simulated_effect
        new_motion_action._motion_constraints = self._motion_constraints.copy()
        return new_motion_action

    def add_motion_constraints(self, motion_constraints: Iterable[MotionConstraint]):
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
        """Returns the `list` of motion constraints."""
        return self._motion_constraints

    def __repr__(self) -> str:
        b = InstantaneousAction.__repr__(self)[0:-3]
        s = ["motion-", b]
        s.append("    motion constraints = [\n")
        for e in self._motion_constraints:
            s.append(f"      {str(e)}\n")
        s.append("    ]\n")
        s.append("  }")
        return "".join(s)


class DurativeMotionAction(DurativeAction):
    """This class represents a durative motion action."""

    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _environment: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        DurativeAction.__init__(self, _name, _parameters, _environment, **kwargs)
        self._timed_motion_constraints: Dict[
            "up.model.timing.TimeInterval", List[MotionConstraint]
        ] = {}

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, DurativeMotionAction):
            if len(self._timed_motion_constraints) != len(
                oth._timed_motion_constraints
            ):
                return False
            for i, mcl in self._timed_motion_constraints.items():
                oth_mcl = oth._timed_motion_constraints.get(i, None)
                if oth_mcl is None:
                    return False
                elif set(mcl) != set(oth_mcl):
                    return False
            return super().__eq__(oth)
        else:
            return False

    def __hash__(self) -> int:
        res = super().__hash__()
        for i, mcl in self._timed_motion_constraints.items():
            res += hash(i)
            for mc in mcl:
                res += hash(mc)
        return res

    def __repr__(self) -> str:
        b = DurativeAction.__repr__(self)[0:-3]
        s = ["motion-", b]

        s.append("    timed motion constraints = [\n")
        for i, cl in self.timed_motion_constraints.items():
            s.append(f"      {str(i)}:\n")
            for c in cl:
                s.append(f"        {str(c)}\n")
        s.append("    ]\n")
        s.append("  }\n")
        return "".join(s)

    def clone(self):

        new_params = OrderedDict(
            (param_name, param.type) for param_name, param in self._parameters.items()
        )
        new_durative_motion_action = DurativeMotionAction(
            self._name, new_params, self._environment
        )
        new_durative_motion_action._duration = self._duration

        TimedCondsEffs._clone_to(self, new_durative_motion_action)

        new_durative_motion_action._timed_motion_constraints = {
            t: mcl[:] for t, mcl in self._timed_motion_constraints.items()
        }

        return new_durative_motion_action

    @property
    def timed_motion_constraints(
        self,
    ) -> Dict["up.model.timing.TimeInterval", List[MotionConstraint]]:
        return self._timed_motion_constraints

    def clear_timed_motion_constraints(self):
        """Removes all `timed_motion_constraints`."""
        self._timed_motion_constraints = {}

    def add_motion_constraint(
        self,
        # interval: Union[
        #    "up.model.expression.TimeExpression", "up.model.timing.TimeInterval"
        # ],
        motion_constraint: MotionConstraint,
    ):
        # if not isinstance(interval, up.model.TimeInterval):
        #    # transform from int/float/timepoint... to Timing
        #    timing = Timing.from_time(interval)
        #    interval = up.model.TimePointInterval(timing)  # and from Timing to Interval

        interval = TimeInterval(StartTiming(), EndTiming())

        if interval in self._timed_motion_constraints:
            self._timed_motion_constraints[interval].append(motion_constraint)
        else:
            self._timed_motion_constraints[interval] = [motion_constraint]
