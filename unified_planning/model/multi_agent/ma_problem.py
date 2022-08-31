# Copyright 2021 AIPlan4EU project
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
"""This module defines the MultiAgentProblem class."""

import unified_planning as up
from unified_planning.model.abstract_problem import AbstractProblem
from unified_planning.model.expression import ConstantExpression
from unified_planning.model.operators import OperatorKind
from unified_planning.model.fluent import get_all_fluent_exp
from unified_planning.model.walkers.substituter import Substituter
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPTypeError,
    UPExpressionDefinitionError,
    UPValueError,
)
from fractions import Fraction
from typing import List, Dict, Set, Union, cast
from unified_planning.model.mixins import (
    ObjectsSetMixin,
    UserTypesSetMixin,
    AgentsSetMixin,
)


class MultiAgentProblem(
    AbstractProblem,
    UserTypesSetMixin,
    ObjectsSetMixin,
    AgentsSetMixin,
):
    """Represents a planning MultiAgentProblem."""

    def __init__(
        self,
        name: str = None,
        env: "up.environment.Environment" = None,
        *,
        initial_defaults: Dict["up.model.types.Type", "ConstantExpression"] = {},
    ):
        AbstractProblem.__init__(self, name, env)
        UserTypesSetMixin.__init__(self, self.has_name)
        ObjectsSetMixin.__init__(self, self.env, self._add_user_type, self.has_name)
        AgentsSetMixin.__init__(self, self.env, self.has_name)

        self._initial_defaults = initial_defaults
        self._env_ma = up.model.multi_agent.ma_environment.MAEnvironment(self)
        self._goals: List["up.model.fnode.FNode"] = list()
        self._initial_value: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"] = {}
        self._operators_extractor = up.model.walkers.OperatorsExtractor()

    def __repr__(self) -> str:
        s = []
        if not self.name is None:
            s.append(f"problem name = {str(self.name)}\n\n")
        if len(self.user_types) > 0:
            s.append(f"types = {str(list(self.user_types))}\n\n")
        s.append("environment fluents = [\n")
        for f in self.ma_environment.fluents:
            s.append(f"  {str(f)}\n")
        s.append("]\n\n")
        s.append("agents = [\n")
        for ag in self.agents:
            s.append(f"  {str(ag)}\n")
        s.append("]\n\n")
        if len(self.user_types) > 0:
            s.append("objects = [\n")
            for ty in self.user_types:
                s.append(f"  {str(ty)}: {str(list(self.objects(ty)))}\n")
            s.append("]\n\n")
        s.append("initial values = [\n")
        for k, v in self._initial_value.items():
            s.append(f"  {str(k)} := {str(v)}\n")
        s.append("]\n\n")
        s.append("goals = [\n")
        for g in self.goals:
            s.append(f"  {str(g)}\n")
        s.append("]\n\n")
        return "".join(s)

    def __hash__(self) -> int:
        res = hash(self._kind) + hash(self._name)
        for ag in self.agents:
            for f in ag._fluents:
                res += hash(f)
        for ag in self.agents:
            for a in ag._actions:
                res += hash(a)
        for ut in self._user_types:
            res += hash(ut)
        for o in self._objects:
            res += hash(o)
        for iv in self._initial_value.items():
            res += hash(iv)
        for goals in self._goals:
            res += hash(goals)
        return res

    def has_name(self, name: str) -> bool:
        """Returns true if the name is in the problem."""
        return self.has_object(name) or self.has_type(name) or self.has_agent(name)

    @property
    def ma_environment(self) -> "up.model.multi_agent.ma_environment.MAEnvironment":
        """Returns the MA-environment."""
        return self._env_ma

    @ma_environment.setter
    def ma_environment(
        self, env_ma: "up.model.multi_agent.ma_environment.MAEnvironment"
    ):
        """Sets the MA-environment."""
        self._env_ma = env_ma

    def set_initial_value(
        self,
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: Union[
            "up.model.fnode.FNode",
            "up.model.fluent.Fluent",
            "up.model.object.Object",
            bool,
            int,
            float,
            Fraction,
        ],
    ):
        """Sets the initial value for the given fluent."""
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        if not fluent_exp.type.is_compatible(value_exp.type):
            raise UPTypeError("Initial value assignment has not compatible types!")
        self._initial_value[fluent_exp] = value_exp

    def initial_value(
        self, fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"]
    ) -> "up.model.fnode.FNode":
        """Gets the initial value of the given fluent."""
        (fluent_exp,) = self._env.expression_manager.auto_promote(fluent)
        for a in fluent_exp.args:
            if not a.is_constant():
                raise UPExpressionDefinitionError(
                    f"Impossible to return the initial value of a fluent expression with no constant arguments: {fluent_exp}."
                )
        if fluent_exp in self._initial_value:
            return self._initial_value[fluent_exp]
        elif fluent_exp.is_dot():
            agent = fluent_exp.agent()
            f = fluent_exp.arg(0).fluent()
            v = agent.fluents_defaults.get(f, None)
            if v is None:
                raise UPProblemDefinitionError("Initial value not set!")
            return v
        elif fluent_exp.fluent() in self.ma_environment.fluents_defaults:
            return self.ma_environment.fluents_defaults[fluent_exp.fluent()]
        else:
            raise UPProblemDefinitionError("Initial value not set!")

    @property
    def initial_values(self) -> Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]:
        """Gets the initial value of the fluents.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible."""
        res = self._initial_value
        for f in self.ma_environment.fluents:
            for f_exp in get_all_fluent_exp(self, f):
                res[f_exp] = self.initial_value(f_exp)
        for a in self.agents:
            for f in a.fluents:
                for f_exp in get_all_fluent_exp(self, f):
                    d = self.env.expression_manager.Dot(a, f_exp)
                    res[d] = self.initial_value(d)
        return res

    @property
    def explicit_initial_values(
        self,
    ) -> Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]:
        """Returns the problem's defined initial values.
        IMPORTANT NOTE: For all the initial values of hte problem use Problem.initial_values."""
        return self._initial_value

    def add_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        """Adds a goal."""
        assert (
            isinstance(goal, bool) or goal.environment == self._env
        ), "goal does not have the same environment of the problem"
        (goal_exp,) = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        if goal_exp != self._env.expression_manager.TRUE():
            self._goals.append(goal_exp)

    def add_goals(
        self, goals: List[Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]]
    ):
        """Sets the goals for the given agent."""
        for goal in goals:
            self.add_goal(goal)

    @property
    def goals(self) -> List["up.model.fnode.FNode"]:
        """Returns the goals."""
        return self._goals

    def clear_goals(self):
        """Removes the goals."""
        self._goals = []

    @property
    def kind(self) -> "up.model.problem_kind.ProblemKind":
        """Returns the problem kind of this planning problem.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible."""
        self._kind = up.model.problem_kind.ProblemKind()
        self._kind.set_problem_class("ACTION_BASED_MULTI_AGENT")
        for ag in self.agents:
            for fluent in ag.fluents:
                self._update_problem_kind_fluent(fluent)
        for fluent in self.ma_environment.fluents:
            self._update_problem_kind_fluent(fluent)
        for ag in self.agents:
            for action in ag.actions:
                self._update_problem_kind_action(action)
        for goal in self._goals:
            self._update_problem_kind_condition(goal)
        return self._kind

    def _update_problem_kind_effect(self, e: "up.model.effect.Effect"):
        if e.is_conditional():
            self._update_problem_kind_condition(e.condition)
            self._kind.set_effects_kind("CONDITIONAL_EFFECTS")
        if e.is_increase():
            self._kind.set_effects_kind("INCREASE_EFFECTS")
        elif e.is_decrease():
            self._kind.set_effects_kind("DECREASE_EFFECTS")

    def _update_problem_kind_condition(self, exp: "up.model.fnode.FNode"):
        ops = self._operators_extractor.get(exp)
        if OperatorKind.EQUALS in ops:
            self._kind.set_conditions_kind("EQUALITY")
        if OperatorKind.NOT in ops:
            self._kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        if OperatorKind.OR in ops:
            self._kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        if OperatorKind.EXISTS in ops:
            self._kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        if OperatorKind.FORALL in ops:
            self._kind.set_conditions_kind("UNIVERSAL_CONDITIONS")

    def _update_problem_kind_type(self, type: "up.model.types.Type"):
        if type.is_user_type():
            self._kind.set_typing("FLAT_TYPING")
            if cast(up.model.types._UserType, type).father is not None:
                self._kind.set_typing("HIERARCHICAL_TYPING")
        elif type.is_int_type():
            self._kind.set_numbers("DISCRETE_NUMBERS")
        elif type.is_real_type():
            self._kind.set_numbers("CONTINUOUS_NUMBERS")

    def _update_problem_kind_fluent(self, fluent: "up.model.fluent.Fluent"):
        self._update_problem_kind_type(fluent.type)
        if fluent.type.is_int_type() or fluent.type.is_real_type():
            self._kind.set_fluents_type("NUMERIC_FLUENTS")
        elif fluent.type.is_user_type():
            self._kind.set_fluents_type("OBJECT_FLUENTS")
        for p in fluent.signature:
            self._update_problem_kind_type(p.type)

    def _update_problem_kind_action(self, action: "up.model.action.Action"):
        for p in action.parameters:
            self._update_problem_kind_type(p.type)
        if isinstance(action, up.model.action.InstantaneousAction):
            for c in action.preconditions:
                self._update_problem_kind_condition(c)
            for e in action.effects:
                self._update_problem_kind_effect(e)
            self._kind.set_time("CONTINUOUS_TIME")
        else:
            raise NotImplementedError
