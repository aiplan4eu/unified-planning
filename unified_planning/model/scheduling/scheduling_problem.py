from collections import OrderedDict
from typing import Optional, List, Union, Dict

from unified_planning.model.expression import ConstantExpression
from unified_planning.model.mixins import InitialStateMixin, MetricsMixin
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
from unified_planning.model.scheduling.chronicle import Chronicle
from unified_planning.model.timing import GlobalStartTiming


class SchedulingProblem(  # type: ignore[misc]
    AbstractProblem,
    UserTypesSetMixin,
    FluentsSetMixin,
    ObjectsSetMixin,
    InitialStateMixin,
    MetricsMixin,
):
    """A scheduling problem shares most of its construct with a planning problem with the following differences:
    - there are no action in a scheduling problem
    - it defines a set of variables and timepoints over which constraints can be stated
    - it provides some shortcuts to deal with typical scheduling constructs (activities, resources, ...)
    """

    @property
    def kind(self) -> "up.model.problem_kind.ProblemKind":
        self._kind = up.model.problem_kind.ProblemKind()
        self._kind.set_problem_class("SCHEDULING")
        return self._kind

    def __init__(
        self,
        name: Optional[str] = None,
        environment: Optional["up.environment.Environment"] = None,
        *,
        initial_defaults: Dict["up.model.types.Type", "ConstantExpression"] = {},
    ):
        AbstractProblem.__init__(self, name, environment)
        UserTypesSetMixin.__init__(self, self.environment, self.has_name)
        FluentsSetMixin.__init__(
            self, self.environment, self._add_user_type, self.has_name, initial_defaults
        )
        ObjectsSetMixin.__init__(
            self, self.environment, self._add_user_type, self.has_name
        )
        InitialStateMixin.__init__(self, self, self, self.environment)
        MetricsMixin.__init__(self, self.environment)
        self._operators_extractor = up.model.walkers.OperatorsExtractor()
        self._initial_value: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"] = {}

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
            s.append("]\n\n")
        s.append("\nBASE")
        s.append(str(self._base))

        s.append("\nActivities:\n  ")
        for act in self._activities:
            s.append(str(act))
            s.append("\n  ")

        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if not (isinstance(oth, SchedulingProblem)) or self._env != oth._env:
            return False
        if self.kind != oth.kind or self._name != oth._name:
            return False

        if not InitialStateMixin.__eq__(self, oth):
            return False
        if not FluentsSetMixin.__eq__(self, oth):
            return False
        if not MetricsMixin.__eq__(self, oth):
            return False

        if set(self._user_types) != set(oth._user_types) or set(self._objects) != set(
            oth._objects
        ):
            return False

        if self._base != oth._base:
            return False
        if set(self._activities) != set(oth._activities):
            return False
        return True

    def __hash__(self) -> int:
        res = hash(self.kind) + hash(self._name)

        res += FluentsSetMixin.__hash__(self)
        res += InitialStateMixin.__hash__(self)
        res += MetricsMixin.__hash__(self)

        for ut in self._user_types:
            res += hash(ut)
        for o in self._objects:
            res += hash(o)

        res += hash(self._base)
        res += sum(map(hash, self._activities))
        return res

    def clone(self):
        new_p = SchedulingProblem(self._name, self._env)
        FluentsSetMixin._clone_to(self, new_p)
        InitialStateMixin._clone_to(self, new_p)
        MetricsMixin._clone_to(self, new_p, new_actions=None)

        new_p._user_types = self._user_types[:]
        new_p._user_types_hierarchy = self._user_types_hierarchy.copy()
        new_p._objects = self._objects[:]

        new_p._base = self._base.clone()
        new_p._activities = [a.clone() for a in self._activities]
        return new_p

    def has_name(self, name: str) -> bool:
        return name in self._base._parameters

    def add_variable(self, name: str, tpe: Type) -> Parameter:
        assert not self.has_name(name)
        param = Parameter(name, tpe)
        self._base._parameters[name] = param
        return param

    def add_activity(self, name: str, duration: Optional[int]) -> "Activity":
        act = Activity(name=name, duration=duration)
        self._activities.append(act)
        return act

    def add_resource(self, name: str, capacity: int = 1) -> Fluent:
        """Declares a new resource: a numeric fluent in `[0, CAPACITY]` where capacity is the
        initial value of the fluent and denote the capacity of the resource."""
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
    ):
        """Enforce a boolean expression to be true in any solution"""
        self._base.add_constraint(constraint)

    def add_condition(self, span: TimeInterval, condition: FNode):
        self._base.add_condition(span, condition)

    def add_effect(
        self,
        timing: Union[int, "up.model.timing.Timing"],
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
    ):
        if isinstance(timing, int):
            timing = GlobalStartTiming(timing)
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
        timing: Union[int, "up.model.timing.Timing"],
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
    ):
        if isinstance(timing, int):
            timing = GlobalStartTiming(timing)
        self._base.add_decrease_effect(timing, fluent, value, condition)  # type: ignore
