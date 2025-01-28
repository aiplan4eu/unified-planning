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
from unified_planning.exceptions import UPTypeError, UPUnboundedVariablesError
from abc import ABC, abstractmethod
from typing import Optional, List, Iterable, Dict, Union
from collections import Counter, OrderedDict

from unified_planning.model.timing import EndTiming, StartTiming, TimeInterval, Timing


class Transform(ABC):
    """
    This class represents a transformation between two objects.

    This is defined by the involved movable objects, their configurations,
    and the associated links that establish their connection.

    """

    def __init__(
        self,
        movable1: "up.model.expression.Expression",
        movable2: "up.model.expression.Expression",
        config1: "up.model.expression.Expression",
        config2: "up.model.expression.Expression",
        link1: str,
        link2: str,
        environment: Optional[Environment] = None,
    ):
        self._environment = get_environment(environment)

        (
            movable1_exp,
            movable2_exp,
        ) = self._environment.expression_manager.auto_promote(movable1, movable2)
        tm1 = self._environment.type_checker.get_type(movable1_exp)
        tm2 = self._environment.type_checker.get_type(movable2_exp)

        if not tm1.is_movable_type() or not tm2.is_movable_type():
            raise UPTypeError(
                "Objects of Transform's constructor must be of movable type!"
            )

        if tm1 != tm2:
            raise UPTypeError("Object 1 and 2 must be of the same movable type!")

        (
            config1_exp,
            config2_exp,
        ) = self._environment.expression_manager.auto_promote(config1, config2)
        tc1 = self._environment.type_checker.get_type(config1_exp)
        tc2 = self._environment.type_checker.get_type(config2_exp)
        if not tc1.is_configuration_type() or not tc2.is_configuration_type():
            raise UPTypeError(
                "Configurations of Transform's constructor must be of configuration type!"
            )

        if tc1 != tc2:
            raise UPTypeError(
                "Configurations of Object 1 and 2 must be of the same configuration type!"
            )

        self._movable1 = movable1_exp
        self._movable2 = movable2_exp
        self._config1 = config1_exp
        self._config2 = config2_exp
        self._link1 = link1
        self._link2 = link2

    def __eq__(self, oth) -> bool:
        if not isinstance(oth, Transform) or self._environment != oth._environment:
            return False
        if (
            self._movable1 != oth._movable1
            or self._movable2 != oth._movable2
            or self._config1 != oth._config1
            or self._config2 != oth._config2
            or self._link1 != oth._link1
            or self._link2 != oth._link2
        ):
            return False
        return True

    def __hash__(self) -> int:
        res = hash(self._movable1)
        res += hash(self._movable2)
        res += hash(self._config1)
        res += hash(self._config2)
        res += hash(self._link1)
        res += hash(self._link2)
        return res

    def __repr__(self) -> str:
        s = ["transform("]
        s.append(str(self.movable1))
        s.append(", ")
        s.append(str(self.movable2))
        s.append(", ")
        s.append(str(self.config1))
        s.append(", ")
        s.append(str(self.config2))
        s.append(", ")
        s.append(self.link1)
        s.append(", ")
        s.append(self.link2)
        s.append(")")
        return "".join(s)

    @property
    def movable1(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the first involved movable object."""
        return self._movable1

    @property
    def movable2(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the second involved movable object."""
        return self._movable2

    @property
    def config1(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the configuration of the first involved movable object."""
        return self._config1

    @property
    def config2(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the configuration of the second involved movable object."""
        return self._config2

    @property
    def link1(self) -> str:
        """Returns the name of the link of the first involved movable object."""
        return self._link1

    @property
    def link2(self) -> str:
        """Returns the name of the link of the second involved movable object."""
        return self._link2


class Attachment(ABC):
    """
    This class represents an attachment between two objects.

    This is defined by the involved movable objects, their attachment configurations,
    and the associated links that establish their connection.

    Once the two objects are attached, a set of touchable links is defined for each object.
    These links are the ones for which collision checking is disabled between the two objects.

    """

    def __init__(
        self,
        activation_condition: List["up.model.fnode.FNode"],
        movable1: "up.model.expression.Expression",
        movable2: "up.model.expression.Expression",
        attached_config1: "up.model.expression.Expression",
        attached_config2: "up.model.expression.Expression",
        attached_link1: str,
        attached_link2: str,
        touchable_links1: Optional[List[str]] = None,
        touchable_links2: Optional[List[str]] = None,
        environment: Optional[Environment] = None,
    ):
        self._environment = get_environment(environment)

        (activation_cond_exp,) = self._environment.expression_manager.auto_promote(
            activation_condition
        )
        assert self._environment.type_checker.get_type(
            activation_cond_exp
        ).is_bool_type()

        free_vars = self._environment.free_vars_oracle.get_free_variables(
            activation_cond_exp
        )
        if len(free_vars) != 0:
            raise UPUnboundedVariablesError(
                f"The activation condition {str(activation_cond_exp)} has unbounded variables:\n{str(free_vars)}"
            )

        (
            movable1_exp,
            movable2_exp,
        ) = self._environment.expression_manager.auto_promote(movable1, movable2)
        tm1 = self._environment.type_checker.get_type(movable1_exp)
        tm2 = self._environment.type_checker.get_type(movable2_exp)

        if not tm1.is_movable_type() or not tm2.is_movable_type():
            raise UPTypeError(
                "Objects of Transform's constructor must be of movable type!"
            )

        if tm1 != tm2:
            raise UPTypeError("Object 1 and 2 must be of the same movable type!")

        (
            attached_config1_exp,
            attached_config2_exp,
        ) = self._environment.expression_manager.auto_promote(
            attached_config1, attached_config2
        )
        tc1 = self._environment.type_checker.get_type(attached_config1_exp)
        tc2 = self._environment.type_checker.get_type(attached_config2_exp)
        if not tc1.is_configuration_type() or not tc2.is_configuration_type():
            raise UPTypeError(
                "Configurations of Transform's constructor must be of configuration type!"
            )

        if tc1 != tc2:
            raise UPTypeError(
                "Configurations of Object 1 and 2 must be of the same configuration type!"
            )

        self._movable1 = movable1_exp
        self._movable2 = movable2_exp
        self._attached_config1 = attached_config1_exp
        self._attached_config2 = attached_config2_exp
        self._attached_link1 = attached_link1
        self._attached_link2 = attached_link2
        self._touchable_links1 = touchable_links1
        self._touchable_links2 = touchable_links2

    def __eq__(self, oth) -> bool:
        if not isinstance(oth, Attachment) or self._environment != oth._environment:
            return False
        if (
            self._movable1 != oth._movable1
            or self._movable2 != oth._movable2
            or self._attached_config1 != oth._attached_config1
            or self._attached_config2 != oth._attached_config2
            or self._attached_link1 != oth._attached_link1
            or self._attached_link2 != oth._attached_link2
            or Counter(self._touchable_links1) != Counter(self._touchable_links2)
        ):
            return False
        return True

    def __hash__(self) -> int:
        res = hash(self._movable1)
        res += hash(self._movable2)
        res += hash(self._attached_config1)
        res += hash(self._attached_config2)
        res += hash(self._attached_link1)
        res += hash(self._attached_link2)
        for l in self._touchable_links1:
            res += hash(l)
        for l in self._touchable_links2:
            res += hash(l)
        return res

    def __repr__(self) -> str:
        s = ["attachment("]
        s.append(str(self.movable1))
        s.append(", ")
        s.append(str(self.movable2))
        s.append(", ")
        s.append(str(self.attached_config1))
        s.append(", ")
        s.append(str(self.attached_config2))
        s.append(", ")
        s.append(self.attached_link1)
        s.append(", ")
        s.append(self.attached_link2)
        s.append(", ")
        s.append("[" + ", ".join(self.touchable_links1) + "]")
        s.append(", ")
        s.append("[" + ", ".join(self.touchable_links2) + "]")
        s.append(")")
        return "".join(s)

    @property
    def movable1(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the first involved movable object."""
        return self._movable1

    @property
    def movable2(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the second involved movable object."""
        return self._movable2

    @property
    def attached_config1(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the attached configuration of the first involved movable object."""
        return self._attached_config1

    @property
    def attached_config2(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the attached configuration of the second involved movable object."""
        return self._attached_config2

    @property
    def attached_link1(self) -> str:
        """Returns the name of the attached link of the first involved movable object."""
        return self._attached_link1

    @property
    def attached_link2(self) -> str:
        """Returns the name of the attached link of the second involved movable object."""
        return self._attached_link2

    @property
    def touchable_links1(self) -> List[str]:
        """Returns the name of the touchable links of the first involved movable object."""
        return self._touchable_links1

    @property
    def touchable_links2(self) -> List[str]:
        """Returns the name of the touchable links of the second involved movable object."""
        return self._touchable_links2


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
    `attachments` is a list of `Attachments`, i.e., extensions of movable objects that change their geometric models.
    """

    def __init__(
        self,
        movable: "up.model.expression.Expression",
        starting: "up.model.expression.Expression",
        waypoints: List["up.model.expression.Expression"],
        static_obstacles: Optional[
            Dict["up.model.tamp.objects.MovableObject", "up.model.fnode.FNode"]
        ] = None,
        dynamic_obstacles_at_start: Optional[
            Dict["up.model.tamp.objects.MovableObject", "up.model.fnode.FNode"]
        ] = None,
        attachments: Optional[List[Attachment]] = None,
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
        self._attachments = attachments

    def __eq__(self, oth) -> bool:
        if not isinstance(oth, Waypoints) or self._environment != oth._environment:
            return False
        if self._movable != oth._movable or self._starting != oth._starting:
            return False
        if set(self._waypoints) != set(oth._waypoints):
            return False
        if self._attachments != oth._attachments:
            return False
        return True

    def __hash__(self) -> int:
        res = hash(self._movable)
        res += hash(self._starting)
        for p in self._waypoints:
            res += hash(p)
        for a in self._attachments:
            res += hash(a)
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
        if self.attachments is not None:
            s.append(", ")
            s.append(str(self.attachments))
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
    ) -> Optional[Dict["up.model.tamp.objects.MovableObject", "up.model.fnode.FNode"]]:
        """Returns the set of `MovableObject` associated with the fluent expressions that represent their configuration during all the constraint (static obstacles)."""
        return self._static_obstacles

    @property
    def dynamic_obstacles_at_start(
        self,
    ) -> Optional[Dict["up.model.tamp.objects.MovableObject", "up.model.fnode.FNode"]]:
        """Returns the set of `MovableObject` associated with the fluent expressions that represent their configuration at the beginning of the constraint (possibly dynamic obstacles)."""
        return self._dynamic_obstacles_at_start

    @property
    def attachments(self) -> List[Attachment]:
        """Returns the list `Attachment` for this motion constraint."""
        return self._attachments


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
