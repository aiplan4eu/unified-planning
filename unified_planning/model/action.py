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
"""
This module defines the `Action` class and some of his extensions.
"""


import unified_planning as up
from unified_planning.environment import get_environment, Environment
from unified_planning.exceptions import (
    UPTypeError,
    UPUnboundedVariablesError,
    UPProblemDefinitionError,
    UPUsageError,
)
from unified_planning.model.mixins.timed_conds_effs import TimedCondsEffs
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set, Union, Optional, Iterable
from collections import OrderedDict

from unified_planning.model.transition import (
    UntimedEffectMixin,
    PreconditionMixin,
    Transition,
)


class Action(Transition):
    """This is the `Action` interface."""

    def __call__(
        self,
        *args: "up.model.Expression",
        agent: Optional["up.model.multi_agent.Agent"] = None,
        motion_paths: Optional[
            Dict["up.model.tamp.MotionConstraint", "up.model.tamp.Path"]
        ] = None,
    ) -> "up.plans.plan.ActionInstance":
        params = tuple(args)
        return up.plans.plan.ActionInstance(
            self, params, agent=agent, motion_paths=motion_paths
        )


class InstantaneousAction(UntimedEffectMixin, Action, PreconditionMixin):
    """Represents an instantaneous action."""

    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _env: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        Action.__init__(self, _name, _parameters, _env, **kwargs)
        PreconditionMixin.__init__(self, _env)
        UntimedEffectMixin.__init__(self, _env)

    def __repr__(self) -> str:
        s = []
        s.append(f"action {self.name}")
        first = True
        for p in self.parameters:
            if first:
                s.append("(")
                first = False
            else:
                s.append(", ")
            s.append(str(p))
        if not first:
            s.append(")")
        s.append(" {\n")
        s.append("    preconditions = [\n")
        for c in self.preconditions:
            s.append(f"      {str(c)}\n")
        s.append("    ]\n")
        s.append("    effects = [\n")
        for e in self.effects:
            s.append(f"      {str(e)}\n")
        s.append("    ]\n")
        if self._simulated_effect is not None:
            s.append(f"    simulated effect = {self._simulated_effect}\n")
        s.append("  }")
        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, InstantaneousAction):
            cond = (
                self._environment == oth._environment
                and self._name == oth._name
                and self._parameters == oth._parameters
            )
            return (
                cond
                and set(self._preconditions) == set(oth._preconditions)
                and set(self._effects) == set(oth._effects)
                and self._simulated_effect == oth._simulated_effect
            )
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._name)
        for ap in self._parameters.items():
            res += hash(ap)
        for p in self._preconditions:
            res += hash(p)
        for e in self._effects:
            res += hash(e)
        res += hash(self._simulated_effect)
        return res

    def clone(self):
        new_params = OrderedDict(
            (param_name, param.type) for param_name, param in self._parameters.items()
        )
        new_instantaneous_action = InstantaneousAction(
            self._name, new_params, self._environment
        )
        new_instantaneous_action._preconditions = self._preconditions[:]
        new_instantaneous_action._effects = [e.clone() for e in self._effects]
        new_instantaneous_action._fluents_assigned = self._fluents_assigned.copy()
        new_instantaneous_action._fluents_inc_dec = self._fluents_inc_dec.copy()
        new_instantaneous_action._simulated_effect = self._simulated_effect
        return new_instantaneous_action


class DurativeAction(Action, TimedCondsEffs):
    """Represents a durative action."""

    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _env: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        Action.__init__(self, _name, _parameters, _env, **kwargs)
        TimedCondsEffs.__init__(self, _env)
        self._duration: "up.model.timing.DurationInterval" = (
            up.model.timing.FixedDuration(self._environment.expression_manager.Int(0))
        )

    def __repr__(self) -> str:
        s = []
        s.append(f"durative action {self.name}")
        first = True
        for p in self.parameters:
            if first:
                s.append("(")
                first = False
            else:
                s.append(", ")
            s.append(str(p))
        if not first:
            s.append(")")
        s.append(" {\n")
        s.append(f"    duration = {str(self._duration)}\n")
        s.append("    conditions = [\n")
        for i, cl in self.conditions.items():
            s.append(f"      {str(i)}:\n")
            for c in cl:
                s.append(f"        {str(c)}\n")
        s.append("    ]\n")
        s.append("    effects = [\n")
        for t, el in self.effects.items():
            s.append(f"      {str(t)}:\n")
            for e in el:
                s.append(f"        {str(e)}:\n")
        s.append("    ]\n")
        s.append("    simulated effects = [\n")
        for t, se in self.simulated_effects.items():
            s.append(f"      {str(t)}: {se}\n")
        s.append("    ]\n")
        s.append("  }")
        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if not isinstance(oth, DurativeAction):
            return False
        if (
            self._environment != oth._environment
            or self._name != oth._name
            or self._parameters != oth._parameters
            or self._duration != oth._duration
        ):
            return False
        if not TimedCondsEffs.__eq__(self, oth):
            return False
        return True

    def __hash__(self) -> int:
        res = hash(self._name) + hash(self._duration)
        for ap in self._parameters.items():
            res += hash(ap)
        res += TimedCondsEffs.__hash__(self)
        return res

    def clone(self):
        new_params = OrderedDict(
            (param_name, param.type) for param_name, param in self._parameters.items()
        )
        new_durative_action = DurativeAction(self._name, new_params, self._environment)
        new_durative_action._duration = self._duration

        TimedCondsEffs._clone_to(self, new_durative_action)
        return new_durative_action

    @property
    def duration(self) -> "up.model.timing.DurationInterval":
        """Returns the `action` `duration interval`."""
        return self._duration

    def set_duration_constraint(self, duration: "up.model.timing.DurationInterval"):
        """
        Sets the `duration interval` for this `action`.

        :param duration: The new `duration interval` of this `action`.
        """
        lower, upper = duration.lower, duration.upper
        tlower = self._environment.type_checker.get_type(lower)
        tupper = self._environment.type_checker.get_type(upper)
        assert tlower.is_int_type() or tlower.is_real_type()
        assert tupper.is_int_type() or tupper.is_real_type()
        if (
            lower.is_constant()
            and upper.is_constant()
            and (
                upper.constant_value() < lower.constant_value()
                or (
                    upper.constant_value() == lower.constant_value()
                    and (duration.is_left_open() or duration.is_right_open())
                )
            )
        ):
            raise UPProblemDefinitionError(
                f"{duration} is an empty interval duration of action: {self.name}."
            )
        self._duration = duration

    def set_fixed_duration(self, value: "up.model.expression.NumericExpression"):
        """
        Sets the `duration interval` for this `action` as the interval `[value, value]`.

        :param value: The `value` set as both edges of this `action's duration`.
        """
        (value_exp,) = self._environment.expression_manager.auto_promote(value)
        self.set_duration_constraint(up.model.timing.FixedDuration(value_exp))

    def set_closed_duration_interval(
        self,
        lower: "up.model.expression.NumericExpression",
        upper: "up.model.expression.NumericExpression",
    ):
        """
        Sets the `duration interval` for this `action` as the interval `[lower, upper]`.

        :param lower: The value set as the lower edge of this `action's duration`.
        :param upper: The value set as the upper edge of this `action's duration`.
        """
        lower_exp, upper_exp = self._environment.expression_manager.auto_promote(
            lower, upper
        )
        self.set_duration_constraint(
            up.model.timing.ClosedDurationInterval(lower_exp, upper_exp)
        )

    def set_open_duration_interval(
        self,
        lower: "up.model.expression.NumericExpression",
        upper: "up.model.expression.NumericExpression",
    ):
        """
        Sets the `duration interval` for this action as the interval `]lower, upper[`.

        :param lower: The value set as the lower edge of this `action's duration`.
        :param upper: The value set as the upper edge of this `action's duration`.

        Note that `lower` and `upper` are not part of the interval.
        """
        lower_exp, upper_exp = self._environment.expression_manager.auto_promote(
            lower, upper
        )
        self.set_duration_constraint(
            up.model.timing.OpenDurationInterval(lower_exp, upper_exp)
        )

    def set_left_open_duration_interval(
        self,
        lower: "up.model.expression.NumericExpression",
        upper: "up.model.expression.NumericExpression",
    ):
        """
        Sets the `duration interval` for this `action` as the interval `]lower, upper]`.

        :param lower: The value set as the lower edge of this `action's duration`.
        :param upper: The value set as the upper edge of this `action's duration`.

        Note that `lower` is not part of the interval.
        """
        lower_exp, upper_exp = self._environment.expression_manager.auto_promote(
            lower, upper
        )
        self.set_duration_constraint(
            up.model.timing.LeftOpenDurationInterval(lower_exp, upper_exp)
        )

    def set_right_open_duration_interval(
        self,
        lower: "up.model.expression.NumericExpression",
        upper: "up.model.expression.NumericExpression",
    ):
        """
        Sets the `duration interval` for this `action` as the interval `[lower, upper[`.

        :param lower: The value set as the lower edge of this `action's duration`.
        :param upper: The value set as the upper edge of this `action's duration`.

        Note that `upper` is not part of the interval.
        """
        lower_exp, upper_exp = self._environment.expression_manager.auto_promote(
            lower, upper
        )
        self.set_duration_constraint(
            up.model.timing.RightOpenDurationInterval(lower_exp, upper_exp)
        )

    def is_conditional(self) -> bool:
        """Returns `True` if the `action` has `conditional effects`, `False` otherwise."""
        # re-implemenation needed for inheritance, delegate implementation.
        return TimedCondsEffs.is_conditional(self)


class SensingAction(InstantaneousAction):
    """This class represents a sensing action."""

    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _env: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        InstantaneousAction.__init__(self, _name, _parameters, _env, **kwargs)
        self._observed_fluents: List["up.model.fnode.FNode"] = []

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, SensingAction):
            return super().__eq__(oth) and set(self._observed_fluents) == set(
                oth._observed_fluents
            )
        else:
            return False

    def __hash__(self) -> int:
        res = super().__hash__()
        for of in self._observed_fluents:
            res += hash(of)
        return res

    def clone(self):
        new_params = OrderedDict()
        for param_name, param in self._parameters.items():
            new_params[param_name] = param.type
        new_sensing_action = SensingAction(self._name, new_params, self._environment)
        new_sensing_action._preconditions = self._preconditions[:]
        new_sensing_action._effects = [e.clone() for e in self._effects]
        new_sensing_action._fluents_assigned = self._fluents_assigned.copy()
        new_sensing_action._fluents_inc_dec = self._fluents_inc_dec.copy()
        new_sensing_action._simulated_effect = self._simulated_effect
        new_sensing_action._observed_fluents = self._observed_fluents.copy()
        return new_sensing_action

    def add_observed_fluents(self, observed_fluents: Iterable["up.model.fnode.FNode"]):
        """
        Adds the given list of observed fluents.

        :param observed_fluents: The list of observed fluents that must be added.
        """
        for of in observed_fluents:
            self.add_observed_fluent(of)

    def add_observed_fluent(self, observed_fluent: "up.model.fnode.FNode"):
        """
        Adds the given observed fluent.

        :param observed_fluent: The observed fluent that must be added.
        """
        self._observed_fluents.append(observed_fluent)

    @property
    def observed_fluents(self) -> List["up.model.fnode.FNode"]:
        """Returns the `list` observed fluents."""
        return self._observed_fluents

    def __repr__(self) -> str:
        b = InstantaneousAction.__repr__(self)[0:-3]
        s = ["sensing-", b]
        s.append("    observations = [\n")
        for e in self._observed_fluents:
            s.append(f"      {str(e)}\n")
        s.append("    ]\n")
        s.append("  }")
        return "".join(s)
