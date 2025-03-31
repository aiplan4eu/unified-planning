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

from collections import OrderedDict
from fractions import Fraction
from typing import Optional, List, Union, Dict, Tuple

from unified_planning.model.effect import Effect
from unified_planning.model.expression import ConstantExpression, TimeExpression
from unified_planning.model.mixins import (
    InitialStateMixin,
    MetricsMixin,
    TimeModelMixin,
)
from unified_planning.model.mixins.objects_set import ObjectsSetMixin
from unified_planning.model.mixins.fluents_set import FluentsSetMixin
from unified_planning.model.mixins.user_types_set import UserTypesSetMixin
from unified_planning.model.abstract_problem import AbstractProblem

import unified_planning as up
from unified_planning.model import (
    Type,
    Parameter,
    Fluent,
    FNode,
    TimeInterval,
)
from unified_planning.model.scheduling.activity import Activity
from unified_planning.model.scheduling.chronicle import Chronicle, Scope
from unified_planning.model.timing import GlobalStartTiming, Timing, Timepoint


class SchedulingProblem(  # type: ignore[misc]
    AbstractProblem,
    UserTypesSetMixin,
    TimeModelMixin,
    FluentsSetMixin,
    ObjectsSetMixin,
    InitialStateMixin,
    MetricsMixin,
):
    """A scheduling problem shares most of its construct with a planning problem with the following differences:

    - scheduling problems replaces *actions* with *activities*. While in planning, a solution plan may contain zero, one
      or multiple instances of the same action, in scheduling the solution must contain *exactly one* instance of each activity.
    - it defines a set of variables and timepoints over which constraints can be stated,
    - it provides some shortcuts to deal with typical scheduling constructs (activities, resources, ...)
    - by default, a `SchedulingProblem` assumes a discrete time model with a minimal temporal separation (aka `epsilon`) of 1.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        environment: Optional["up.environment.Environment"] = None,
        *,
        initial_defaults: Dict["up.model.types.Type", "ConstantExpression"] = {},
    ):
        AbstractProblem.__init__(self, name, environment)
        UserTypesSetMixin.__init__(self, self.environment, self.has_name)
        TimeModelMixin.__init__(
            self,
            epsilon_default=Fraction(1),
            discrete_time=True,
            self_overlapping=False,
        )
        FluentsSetMixin.__init__(
            self, self.environment, self._add_user_type, self.has_name, initial_defaults
        )
        ObjectsSetMixin.__init__(
            self, self.environment, self._add_user_type, self.has_name
        )
        InitialStateMixin.__init__(self, self, self, self.environment)
        MetricsMixin.__init__(self, self.environment)

        # the base chronicle contains all timed goals and timed effects
        self._base: Chronicle = Chronicle(":", _env=environment)
        self._activities: List[Activity] = []

        self._metrics: List["up.model.metrics.PlanQualityMetric"] = []

    def __repr__(self) -> str:
        s = []
        if self.name is not None:
            s.append(f"problem name = {str(self.name)}\n\n")
        if len(self.user_types) > 0:
            s.append(f"types = {str(list(self.user_types))}\n\n")
        s.append("fluents = [\n")
        for f in self.fluents:
            s.append(f"  {str(f)}\n")
        s.append("]\n\n")
        if len(self.user_types) > 0:
            s.append("objects = [\n")
            for ty in self.user_types:
                s.append(f"  {str(ty)}: {str(list(self.objects(ty)))}\n")
            s.append("]\n\n")
        s.append("initial fluents default = [\n")
        for f in self._fluents:
            if f in self._fluents_defaults:
                v = self._fluents_defaults[f]
                s.append(f"  {str(f)} := {str(v)}\n")
        s.append("]\n\n")
        s.append("initial values = [\n")
        for k, v in self.explicit_initial_values.items():
            s.append(f"  {str(k)} := {str(v)}\n")
        s.append("]\n\n")
        if len(self.quality_metrics) > 0:
            s.append("quality metrics = [\n")
            for qm in self.quality_metrics:
                s.append(f"  {str(qm)}\n")
            s.append("]\n")
        s.append("\nBASE")
        s.append(str(self._base))

        s.append("\n\nActivities:\n  ")
        for act in self._activities:
            s.append(str(act))
            s.append("\n  ")

        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if not (isinstance(oth, SchedulingProblem)) or self._env != oth._env:
            return False
        if self.kind != oth.kind or self._name != oth._name:
            return False

        if not UserTypesSetMixin.__eq__(self, oth):
            return False
        if not ObjectsSetMixin.__eq__(self, oth):
            return False
        if not FluentsSetMixin.__eq__(self, oth):
            return False
        if not InitialStateMixin.__eq__(self, oth):
            return False
        if not MetricsMixin.__eq__(self, oth):
            return False

        if self._base != oth._base:
            return False
        if set(self._activities) != set(oth._activities):
            return False
        return True

    def __hash__(self) -> int:
        res = hash(self.kind) + hash(self._name)

        res += UserTypesSetMixin.__hash__(self)
        res += ObjectsSetMixin.__hash__(self)
        res += FluentsSetMixin.__hash__(self)
        res += InitialStateMixin.__hash__(self)
        res += MetricsMixin.__hash__(self)

        res += hash(self._base)
        res += sum(map(hash, self._activities))
        return res

    @property
    def kind(self) -> "up.model.problem_kind.ProblemKind":
        factory = up.model.problem._KindFactory(self, "SCHEDULING", self.environment)

        # note: auto promoted to discrete time in `finalize()` if that's what is said in the TimeModelMixin.
        factory.kind.set_time("CONTINUOUS_TIME")

        if len(self.base_conditions) > 0:
            factory.kind.set_time("TIMED_GOALS")

        if len(self.base_effects) > 0:
            factory.kind.set_time("TIMED_EFFECTS")

        for _, cond, _ in self.all_conditions():
            factory.update_problem_kind_expression(cond)

        for constraint, scope in self.base_scoped_constraints:
            factory.update_problem_kind_expression(constraint)
            if len(scope) > 0:
                factory.kind.set_scheduling("SCOPED_CONSTRAINTS")

        for _, eff in self.base_effects:
            factory.update_problem_kind_effect(eff)

        for act in self.activities:
            if act.optional:
                factory.kind.set_scheduling("OPTIONAL_ACTIVITIES")

            factory.update_action_duration(act.duration)
            for param in act.parameters:
                factory.update_action_parameter(param)
            for t, effs in act.effects.items():
                for e in effs:
                    factory.update_action_timed_effect(t, e)
            for span, conds in act.conditions.items():
                for cond in conds:
                    factory.update_action_timed_condition(span, cond)
            for constraint, scope in act.scoped_constraints:
                factory.update_problem_kind_expression(constraint)
                if len(scope) > 0:
                    factory.kind.set_scheduling("SCOPED_CONSTRAINTS")

        factory.update_problem_kind_initial_state(self)

        return factory.finalize()

    def clone(self):
        """Returns an equivalent problem."""
        new_p = SchedulingProblem(self._name, self._env)
        UserTypesSetMixin._clone_to(self, new_p)
        ObjectsSetMixin._clone_to(self, new_p)
        FluentsSetMixin._clone_to(self, new_p)
        TimeModelMixin._clone_to(self, new_p)
        InitialStateMixin._clone_to(self, new_p)
        MetricsMixin._clone_to(self, new_p, new_actions=None)

        new_p._base = self._base.clone()
        new_p._activities = [a.clone() for a in self._activities]
        return new_p

    def add_variable(self, name: str, tpe: Type) -> Parameter:
        """Adds a new decision variable to the problem.
        Such variables essentially act as existentially quantified variables whose scope is
        the entire problem, which allows referring to them everywhere and access their values in the solution.
        """
        assert not self.has_name(name)
        param = Parameter(name, tpe)
        self._base._parameters[name] = param
        return param

    def get_variable(self, name: str) -> Parameter:
        """Returns the existing decision variable with the given name."""
        return self._base.get_parameter(name)

    def add_activity(self, name: str, duration: int = 0, optional: bool = False) -> "Activity":
        """Creates a new activity with the given `name` in the problem.

        :param name: Name that uniquely identifies the activity.
        :param duration: (optional) Fixed duration of the activity. If not set, the duration to 0 (instantaneous activity).
                         The duration can alter be overriden on the Activity object.
        """
        if any(a.name == name for a in self._activities):
            raise ValueError(f"An activity with name '{name}' already exists.")
        act = Activity(name=name, duration=duration, optional=optional)
        self._activities.append(act)
        return act

    @property
    def activities(self) -> List[Activity]:
        """Return a list of all potential activities in the problem."""
        return self._activities

    def get_activity(self, name: str) -> "Activity":
        """Returns the activity with the given name."""
        for act in self.activities:
            if act.name == name:
                return act
        raise ValueError(
            f"Unknown activity '{name}'. Available activity names: {[a.name for a in self.activities]}"
        )

    def add_resource(self, name: str, capacity: int) -> Fluent:
        """Declares a new resource: a bounded integer fluent in `[0, CAPACITY]` where capacity is the
        default initial value of the fluent and denote the capacity of the resource.

        :param name: Name of the fluent that will represent the resource.
        :param capacity: Upper bound on the fluent value. By default, the fluent initial value is set to `capacity`.
        """
        tpe = self._env.type_manager.IntType(0, capacity)
        return self.add_fluent(name, tpe, default_initial_value=capacity)

    def add_constraint(
        self,
        constraint: Union[
            "up.model.fnode.FNode",
            "up.model.fluent.Fluent",
            "up.model.parameter.Parameter",
            bool,
        ],
        scope: Optional[Scope] = None
    ):
        """Enforce a boolean expression to be true in any solution"""

        self._base._add_constraint(constraint, scope=[] if scope is None else scope)

    def add_condition(self, span: TimeInterval, condition: FNode):
        self._base.add_condition(span, condition)

    def add_effect(
        self,
        timing: "up.model.expression.TimeExpression",
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
    ):
        self._base.add_effect(timing, fluent, value, condition)  # type: ignore

    def add_increase_effect(
        self,
        timing: Union[int, "up.model.timing.Timing"],
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
    ):
        if isinstance(timing, int):
            timing = GlobalStartTiming(timing)
        self._base.add_increase_effect(timing, fluent, value, condition)  # type: ignore

    def add_decrease_effect(
        self,
        timing: TimeExpression,
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
    ):
        self._base.add_decrease_effect(timing, fluent, value, condition)  # type: ignore

    @property
    def base_variables(self) -> List[Parameter]:
        """Return all decisions variables that were defined in the base problem (i.e. not in the activities)"""
        return self._base.parameters.copy()

    @property
    def base_constraints(self) -> List[FNode]:
        """Returns all constraints defined in the base problem (ignoring any constraint defined in an activity)."""
        return self._base.constraints.copy()

    @property
    def base_scoped_constraints(self) -> List[Tuple[FNode, Scope]]:
        """Returns all constraints defined in the base problem (ignoring any constraint defined in an activity)."""
        return self._base.scoped_constraints.copy()

    @property
    def base_conditions(self) -> List[Tuple[TimeInterval, FNode]]:
        """Returns all timed conditions defined in the base problem
        (i.e. excluding those defined in activities)."""
        return [
            (timing, cond)
            for (timing, conds) in self._base.conditions.items()
            for cond in conds
        ]

    @property
    def base_effects(self) -> List[Tuple[Timing, Effect]]:
        """Returns all timed effects defined in the base problem
        (i.e. excluding those defined in activities)."""
        return [
            (timing, eff)
            for (timing, effs) in self._base.effects.items()
            for eff in effs
        ]

    def all_variables(
        self,
    ) -> List[Tuple[Union[Parameter, Timepoint], Optional[Activity]]]:
        """Returns all decision variables (timepoints and parameters) defined in this problem and its activities.
        For each variable, the activity in which it was defined is also given."""
        vars: List[Tuple[Union[Parameter, Timepoint], Optional[Activity]]] = []
        vars += map(lambda param: (param, None), self._base.parameters)
        for activity in self.activities:
            vars.append((activity.start, activity))
            vars.append((activity.end, activity))
            vars += map(lambda param: (param, activity), activity.parameters)
        return vars

    def all_constraints(self) -> List[FNode]:
        """Returns all constraints enforced in this problem or in any of its activities."""
        cs = self._base.constraints.copy()
        for a in self.activities:
            cs += a.constraints
        return cs

    def all_scoped_constraints(self) -> List[Tuple[FNode, Scope]]:
        """Returns all scoped constraints enforced in this problem or in any of its activities."""
        cs = self._base.scoped_constraints.copy()
        for a in self.activities:
            cs += a.scoped_constraints
        return cs

    def all_conditions(self) -> List[Tuple[TimeInterval, FNode, Optional[Activity]]]:
        """Returns all timed conditions enforced in this problem or in any of its activities.
        For each condition, the activity in which it was defined is also given."""
        cs: List[Tuple[TimeInterval, FNode, Optional[Activity]]] = []
        for timing, conds in self._base.conditions.items():
            cs += list(map(lambda cond: (timing, cond, None), conds))
        for act in self.activities:
            for timing, conds in act.conditions.items():
                cs += map(lambda cond: (timing, cond, act), conds)
        return cs

    def all_effects(self) -> List[Tuple[Timing, Effect, Optional[Activity]]]:
        """Returns all timed effects enforced in this problem or in any of its activities.
        For each effect, the activity in which it was defined is also given."""
        es: List[Tuple[Timing, Effect, Optional[Activity]]] = []
        for timing, effs in self._base.effects.items():
            es += map(lambda eff: (timing, eff, None), effs)
        for act in self.activities:
            for timing, effs in act.effects.items():
                es += map(lambda eff: (timing, eff, act), effs)
        return es

    def normalize_plan(self, plan: "up.plans.Plan") -> "up.plans.Plan":
        """
        Normalizes the given `Plan`, that is potentially the result of another
        `Problem`, updating the `Object` references in the `Plan` with the ones of
        this `Problem` which are syntactically equal.

        :param plan: The `Plan` that must be normalized.
        :return: A `Plan` syntactically valid for this `Problem`.
        """
        raise NotImplementedError
        # TODO

    def has_name(self, name: str) -> bool:
        return name in self._base._parameters
