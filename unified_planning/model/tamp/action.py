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
from typing import Optional, List, Iterable, Dict, Union, Tuple
from collections import Counter, OrderedDict

from unified_planning.model.timing import EndTiming, StartTiming, TimeInterval, Timing
from unified_planning.model.scheduling.activity import Activity


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
        obj_from: "up.model.expression.Expression",
        obj_to: "up.model.expression.Expression",
        attached_config_from: "up.model.expression.Expression",
        attached_config_to: "up.model.expression.Expression",
        attached_link_from: str,
        attached_link_to: str,
        touchable_links_from: Optional[List[str]] = None,
        touchable_links_to: Optional[List[str]] = None,
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
            obj_from_exp,
            obj_to_exp,
        ) = self._environment.expression_manager.auto_promote(obj_from, obj_to)
        tm1 = self._environment.type_checker.get_type(obj_from_exp)
        tm2 = self._environment.type_checker.get_type(obj_to_exp)

        if not tm1.is_movable_type() or not tm2.is_movable_type():
            raise UPTypeError(
                "Objects of Transform's constructor must be of movable type!"
            )

        (
            attached_config_from_exp,
            attached_config_to_exp,
        ) = self._environment.expression_manager.auto_promote(
            attached_config_from, attached_config_to
        )
        tc1 = self._environment.type_checker.get_type(attached_config_from_exp)
        tc2 = self._environment.type_checker.get_type(attached_config_to_exp)
        if not tc1.is_configuration_type() or not tc2.is_configuration_type():
            raise UPTypeError(
                "Configurations of Transform's constructor must be of configuration type!"
            )

        if tc1.kind != tc2.kind:
            raise UPTypeError(
                "Configurations of Object 1 and 2 must be of the same configuration kind!"
            )

        self._obj_from = obj_from_exp
        self._obj_to = obj_to_exp
        self._attached_config_from = attached_config_from_exp
        self._attached_config_to = attached_config_to_exp
        self._attached_link_from = attached_link_from
        self._attached_link_to = attached_link_to
        self._touchable_links_from = touchable_links_from
        self._touchable_links_to = touchable_links_to

    def __eq__(self, oth) -> bool:
        if not isinstance(oth, Attachment) or self._environment != oth._environment:
            return False
        if (
            self._obj_from != oth._obj_from
            or self._obj_to != oth._obj_to
            or self._attached_config_from != oth._attached_config_from
            or self._attached_config_to != oth._attached_config_to
            or self._attached_link_from != oth._attached_link_from
            or self._attached_link_to != oth._attached_link_to
            or Counter(self._touchable_links_from)
            != Counter(self._touchable_links_from)
            or Counter(self._touchable_links_to) != Counter(self._touchable_links_to)
        ):
            return False
        return True

    def __hash__(self) -> int:
        res = hash(self._obj_from)
        res += hash(self._obj_to)
        res += hash(self._attached_config_from)
        res += hash(self._attached_config_to)
        res += hash(self._attached_link_from)
        res += hash(self._attached_link_to)
        for l in self._touchable_links_from:
            res += hash(l)
        for l in self._touchable_links_to:
            res += hash(l)
        return res

    def __repr__(self) -> str:
        s = ["attachment("]
        s.append(str(self.obj_from))
        s.append(", ")
        s.append(str(self.obj_to))
        s.append(", ")
        s.append(str(self.attached_config_from))
        s.append(", ")
        s.append(str(self.attached_config_to))
        s.append(", ")
        s.append(self.attached_link_from)
        s.append(", ")
        s.append(self.attached_link_to)
        s.append(", ")
        s.append("[" + ", ".join(self.touchable_links_from) + "]")
        s.append(", ")
        s.append("[" + ", ".join(self.touchable_links_to) + "]")
        s.append(")")
        return "".join(s)

    @property
    def obj_from(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the movable object to be attached."""
        return self._obj_from

    @property
    def obj_to(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the movable object to which attach."""
        return self._obj_to

    @property
    def attached_config_from(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the attached configuration of movable object to be attached."""
        return self._attached_config_from

    @property
    def attached_config_to(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the attached configuration of the movable object to which attach."""
        return self._attached_config_to

    @property
    def attached_link_from(self) -> str:
        """Returns the name of the attached link of movable object to be attached."""
        return self._attached_link_from

    @property
    def attached_link_to(self) -> str:
        """Returns the name of the attached link of the movable object to which attach."""
        return self._attached_link_to

    @property
    def touchable_links_from(self) -> List[str]:
        """Returns the name of the touchable links of the movable object to be attached."""
        return self._touchable_links_from

    @property
    def touchable_links_to(self) -> List[str]:
        """Returns the name of the touchable links of the movable object to which attach."""
        return self._touchable_links_to


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


class TransformConstraint(MotionConstraint):
    """
    This class represents a constraint on the existance of a transformation between two objects.

    This is defined by the involved movable objects, their configurations,
    and the associated links that establish their connection.

    """

    def __init__(
        self,
        obj_from: "up.model.expression.Expression",
        obj_to: "up.model.expression.Expression",
        config_from: "up.model.expression.Expression",
        config_to: "up.model.expression.Expression",
        link_from: str,
        link_to: str,
        environment: Optional[Environment] = None,
    ):

        super().__init__(environment)

        (
            obj_from_exp,
            obj_to_exp,
        ) = self._environment.expression_manager.auto_promote(obj_from, obj_to)
        tm1 = self._environment.type_checker.get_type(obj_from_exp)
        tm2 = self._environment.type_checker.get_type(obj_to_exp)

        if not tm1.is_movable_type() or not tm2.is_movable_type():
            raise UPTypeError(
                "Objects of TransformConstraint's constructor must be of movable type!"
            )

        (
            config_from_exp,
            config_to_exp,
        ) = self._environment.expression_manager.auto_promote(config_from, config_to)
        tc1 = self._environment.type_checker.get_type(config_from_exp)
        tc2 = self._environment.type_checker.get_type(config_to_exp)
        if not tc1.is_configuration_type() or not tc2.is_configuration_type():
            raise UPTypeError(
                "Configurations of TransformConstraint's constructor must be of configuration type!"
            )

        if tc1.kind != tc2.kind:
            raise UPTypeError(
                "Configurations of Object 1 and 2 must be of the same configuration kind!"
            )

        self._obj_from = obj_from_exp
        self._obj_to = obj_to_exp
        self._config_from = config_from_exp
        self._config_to = config_to_exp
        self._link_from = link_from
        self._link_to = link_to

    def __eq__(self, oth) -> bool:
        if (
            not isinstance(oth, TransformConstraint)
            or self._environment != oth._environment
        ):
            return False
        if (
            self._obj_from != oth._obj_from
            or self._obj_to != oth._obj_to
            or self._config_from != oth._config_from
            or self._config_to != oth._config_to
            or self._link_from != oth._link_from
            or self._link_to != oth._link_to
        ):
            return False
        return True

    def __hash__(self) -> int:
        res = hash(self._obj_from)
        res += hash(self._obj_to)
        res += hash(self._config_from)
        res += hash(self._config_to)
        res += hash(self._link_from)
        res += hash(self._link_to)
        return res

    def __repr__(self) -> str:
        s = ["transform("]
        s.append(str(self.obj_from))
        s.append(", ")
        s.append(str(self.obj_to))
        s.append(", ")
        s.append(str(self.config_from))
        s.append(", ")
        s.append(str(self.config_to))
        s.append(", ")
        s.append(self.link_from)
        s.append(", ")
        s.append(self.link_to)
        s.append(")")
        return "".join(s)

    @property
    def obj_from(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the movable object from which the `TransformConstraint` is computed."""
        return self._obj_from

    @property
    def obj_to(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the movable object to which the `TransformConstraint` is computed."""
        return self._obj_to

    @property
    def config_from(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the configuration of the movable object from which `TransformConstraint` is computed."""
        return self._config_from

    @property
    def config_to(self) -> "up.model.fnode.FNode":
        """Returns the `FNode` representing the configuration of the movable object to which the `TransformConstraint` is computed."""
        return self._config_to

    @property
    def link_from(self) -> str:
        """Returns the name of the link of the movable object from which the `TransformConstraint` is computed."""
        return self._link_from

    @property
    def link_to(self) -> str:
        """Returns the name of the link of the movable object to which the `TransformConstraint` is computed."""
        return self._link_to


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
            Dict["up.model.tamp.MovableObject", "up.model.fnode.FNode"]
        ] = None,
        dynamic_obstacles_at_start: Optional[
            Dict["up.model.tamp.MovableObject", "up.model.fnode.FNode"]
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
    ) -> Optional[Dict["up.model.tamp.MovableObject", "up.model.fnode.FNode"]]:
        """Returns the set of `MovableObject` associated with the fluent expressions that represent their configuration during all the constraint (static obstacles)."""
        return self._static_obstacles

    @property
    def dynamic_obstacles_at_start(
        self,
    ) -> Optional[Dict["up.model.tamp.MovableObject", "up.model.fnode.FNode"]]:
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


class ActivityWaypoints(MotionConstraint):

    def __init__(
        self,
        movable: "up.model.expression.Expression",
        starting: "up.model.expression.Expression",
        waypoints: List["up.model.expression.Expression"],
        static_obstacles: Optional[
            Union[List["up.model.tamp.MovableObject"], Dict]
        ] = None,
        dynamic_obstacles_at_start: Optional[
            Union[List["up.model.tamp.MovableObject"], Dict]
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
    ) -> Optional[Union[List["up.model.tamp.MovableObject"], Dict]]:
        return self._static_obstacles

    @property
    def dynamic_obstacles_at_start(
        self,
    ) -> Optional[Union[List["up.model.tamp.MovableObject"], Dict]]:
        return self._dynamic_obstacles_at_start

    @property
    def attachments(self) -> List[Attachment]:
        """Returns the list `Attachment` for this motion constraint."""
        return self._attachments

    # def _get_obstacles(
    #     self,
    #     obstacles: Dict[
    #         "up.model.expression.Expression",
    #         List[Tuple[Optional[Activity], "up.model.expression.Expression"]],
    #     ],
    # ) -> Dict["up.model.FNode", List[Tuple[Optional[Activity], "up.model.FNode"]]]:
    #     res_obstacles = {}
    #     for movable, activity_config_pairs in obstacles.items():
    #         (movable_exp,) = self._environment.expression_manager.auto_promote(movable)
    #         if not self._environment.type_checker.get_type(
    #             movable_exp
    #         ).is_movable_type():
    #             raise UPTypeError("must be of movable type!")

    #         res_obstacles[movable_exp] = []
    #         for activity, config in activity_config_pairs:
    #             (config_exp,) = self._environment.expression_manager.auto_promote(
    #                 config
    #             )
    #             if not self._environment.type_checker.get_type(
    #                 config_exp
    #             ).is_configuration_type():
    #                 raise UPTypeError("config parameter must be of configuration type!")

    #             res_obstacles[movable_exp].append((activity, config_exp))

    #     return res_obstacles


class MotionActivity(Activity):
    """This class represents a motion activity."""

    def __init__(
        self,
        name: str,
        duration: int = 1,
        optional: bool = False,
        _env: Optional[Environment] = None,
    ):
        Activity.__init__(self, name, duration, optional, _env)
        self._motion_constraints: List[MotionConstraint] = []
        self._motion_effects: List[Tuple["up.model.FNode", "up.model.FNode"]] = []

    def __eq__(self, oth: object) -> bool:
        if not isinstance(oth, MotionActivity):
            return False
        if self._motion_constraints != oth._motion_constraints:
            # FIXME
            return False
        if self._motion_effects != oth._motion_effects:
            return False
        return super().__eq__(oth)

    def __hash__(self) -> int:
        res = super().__hash__()
        res += sum(map(hash, self.motion_constraints))
        res += sum(map(hash, self.motion_effects))
        return res

    def __repr__(self) -> str:
        s = ["motion-activity {"]
        s.append(super().__repr__().replace("/n", "\n  "))
        s.append("  motion-constraints")
        s.append("  " + repr(self.motion_constraints))
        s.append("  motion-effects")
        s.append("  " + repr(self.motion_effects))
        s.append("}")
        return "\n".join(s)

    def clone(self):
        new = MotionActivity(self.name, optional=self.optional, _env=self._environment)
        self._clone_to(new)
        new._duration = self._duration
        new._motion_constraints = self.motion_constraints
        new._motion_effects = self.motion_effects
        return new

    @property
    def motion_constraints(self) -> List[MotionConstraint]:
        return self._motion_constraints

    @property
    def motion_effects(
        self,
    ) -> List[
        Tuple["up.model.expression.Expression", "up.model.expression.Expression"]
    ]:
        return self._motion_effects

    def clear_motion_constraints(self):
        """Removes all `motion_constraints`."""
        self._motion_constraints = []

    def clear_motion_constraints(self):
        """Removes all `motion_effects`."""
        self._motion_effects = []

    def add_motion_constraint(self, motion_constraint: MotionConstraint):
        self._motion_constraints.append(motion_constraint)

    def add_motion_effect(
        self,
        movable: "up.model.expression.Expression",
        config: "up.model.expression.Expression",
    ):
        (movable_exp, config_exp) = self._environment.expression_manager.auto_promote(
            movable, config
        )
        if not self._environment.type_checker.get_type(movable_exp).is_movable_type():
            raise UPTypeError("movable parameter must be of movable type!")
        if not self._environment.type_checker.get_type(
            config_exp
        ).is_configuration_type():
            raise UPTypeError("config parameter must be of configuration type!")

        self._motion_effects.append((movable_exp, config_exp))
