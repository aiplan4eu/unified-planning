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
from unified_planning.model.types import domain_size, domain_item
from unified_planning.model.walkers.substituter import Substituter
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPTypeError,
    UPExpressionDefinitionError,
    UPValueError,
)
from fractions import Fraction
from typing import List, Dict, Set, Union, cast
from unified_planning.model.ma_environment import MAEnvironment
from unified_planning.model.mixins import (
    ObjectsSetMixin,
    UserTypesSetMixin,
    AgentsSetMixin,
)


class MultiAgentProblem(
    AbstractProblem, UserTypesSetMixin, ObjectsSetMixin, AgentsSetMixin,
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
        self._env_ma: "up.model.MAEnvironment" = up.model.MAEnvironment(self)
        self._goals: List["up.model.fnode.FNode"] = list()
        self._initial_value: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"] = {}
        self._operators_extractor = up.model.walkers.OperatorsExtractor()

    def __repr__(self) -> str:
        s = []
        if not self.name is None:
            s.append(f"problem name = {str(self.name)}\n\n")
        if len(self.user_types) > 0:
            s.append(f"types = {str(list(self.user_types))}\n\n")

        s.append("agents fluents = [\n")
        for ag in self.agents:
            for f in ag.fluents:
                s.append(f"  {str(ag._name)}: {str(f)}\n")
        if self.get_ma_environment is not None:
            if len(self.get_ma_environment.fluents) > 0:  # type: ignore
                for f in self.get_ma_environment.fluents:  # type: ignore
                    s.append(f"  {'MA-Environment'} {str(f)}\n")
        s.append("]\n\n")

        s.append("agents actions = [\n")
        for ag in self.agents:
            for a in ag.actions:
                s.append(f"  {str(ag._name)}: {str(a)}\n")
        s.append("]\n\n")

        if len(self.user_types) > 0:
            s.append("objects = [\n")
            for ty in self.user_types:
                s.append(f"  {str(ty)}: {str(list(self.objects(ty)))}\n")
            s.append("]\n\n")

        s.append("initial fluents default = [\n")
        for ag in self.agents:
            for f in ag._fluents:
                if f in ag._fluents_defaults:
                    v = ag._fluents_defaults[f]
                    s.append(f"  {str(ag._name)}: {str(f)} := {str(v)}\n")
        s.append("]\n\n")

        s.append("agents initial values = [\n")
        for k, v in self.agents_initial_values.items():
            s.append(f" {str(k)} := {str(v)}\n")
        s.append("]\n\n")

        s.append("MA-environment initial values = [\n")
        for k, v in self.env_initial_values.items():
            s.append(f" MA-environment: {str(k)} := {str(v)}\n")
        s.append("]\n\n")

        s.append("agents goals = [\n")
        if len(self.agents_goals) > 0:
            for goal in self.agents_goals:
                s.append(f" {str(goal)}\n")
        s.append("]\n\n")

        s.append("MA-environment goals = [\n")
        if len(self.env_goals) > 0:
            for goal in self.env_goals:
                s.append(f" {'MA-Environment'} {str(goal)}\n")
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
        return (
            self.get_ma_environment.has_fluent(name)
            or self.has_object(name)
            or self.has_type(name)
            or self.has_agent(name)
        )

    def set_ma_environment(self, env_ma) -> Union["up.model.MAEnvironment"]:
        """Add a MA-environment."""
        self._env_ma = env_ma
        return self._env_ma

    @property
    def get_ma_environment(self) -> "up.model.MAEnvironment":
        """Get a MA-environment."""
        return self._env_ma

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

    def agent_goals(
        self, agent: "up.model.agent.Agent"
    ) -> List["up.model.fnode.FNode"]:
        """Returns the goals for the given agent"""
        agent_goals = []
        for goal in self._goals:
            if not goal.is_dot() and goal.args[0].is_dot():
                if type(goal) is up.model.agent.Agent:
                    if agent.name == goal.args[0].agent():
                        agent_goals.append(goal)
            else:
                if type(goal) is up.model.agent.Agent:
                    if agent.name == goal.agent().name:
                        agent_goals.append(goal)
        return agent_goals

    @property
    def agents_goals(self) -> List["up.model.fnode.FNode"]:
        """Returns the goals of agents"""
        agents_goals = []
        for i in self._goals:
            if not i.is_dot() and i.args[0].is_dot():
                if type(i.args[0]._content.payload) is up.model.agent.Agent:
                    agents_goals.append(i)
            else:
                if type(i._content.payload) is up.model.agent.Agent:
                    agents_goals.append(i)
        return agents_goals

    def add_agent_goals(
        self, agent: "up.model.agent.Agent", goals: List["up.model.fnode.FNode"]
    ):
        """Sets the goals for the given agent."""
        for goal in goals:
            if not goal.is_fluent_exp() and goal.args[0].is_fluent_exp():
                sub = Substituter(self.env)
                subs_map = {}
                agent_goal = self.env.expression_manager.Dot(agent, goal.args[0])
                old_exp = sub._get_key(goal.args[0])
                new_exp = sub._get_key(agent_goal)
                subs_map[old_exp] = new_exp
                agent_goal = sub.substitute(goal, subs_map)
            else:
                agent_goal = self.env.expression_manager.Dot(agent, goal)
            self.add_goal(agent_goal)

    def clear_goals(self):
        """Removes the goals."""
        self._goals = []

    def add_env_goals(self, goals: List["up.model.fnode.FNode"]):
        """Sets the goals for the given agent."""
        for goal in goals:
            if not goal.is_fluent_exp() and goal.args[0].is_fluent_exp():
                sub = Substituter(self.env)
                subs_map = {}
                env_goal = self.env.expression_manager.Dot(
                    self.get_ma_environment, goal.args[0]
                )
                old_exp = sub._get_key(goal.args[0])
                new_exp = sub._get_key(env_goal)
                subs_map[old_exp] = new_exp
                env_goal = sub.substitute(goal, subs_map)
            else:
                env_goal = self.env.expression_manager.Dot(
                    self.get_ma_environment, goal
                )
            self.add_goal(env_goal)

    @property
    def env_goals(self) -> List["up.model.fnode.FNode"]:
        """Returns the goals of MA-environment"""
        ma_env_goals = []
        for i in self._goals:
            if not i.is_dot() and i.args[0].is_dot():
                if (
                    type(i.args[0]._content.payload)
                    is up.model.ma_environment.MAEnvironment
                ):
                    ma_env_goals.append(i)
            else:
                if type(i._content.payload) is up.model.ma_environment.MAEnvironment:
                    ma_env_goals.append(i)
        return ma_env_goals

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

    def set_initial_values(
        self, initial_values: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]
    ):
        """Sets the initial_values"""
        for k, v in initial_values.items():
            self.set_initial_value(k, v)

    @property
    def initial_values(self) -> Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]:
        """Returns the initial_values."""
        return self._initial_value

    def set_agent_initial_values(
        self,
        agent: "up.model.agent.Agent",
        initial_values: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"],
    ):
        """Sets the initial_values for the given agent."""
        for k, v in initial_values.items():
            if not k.is_fluent_exp() and k.args[0].is_fluent_exp():
                sub = Substituter(self.env)
                subs_map = {}
                agent_initial_value = self.env.expression_manager.Dot(agent, k.args[0])
                old_exp = sub._get_key(k.args[0])
                new_exp = sub._get_key(agent_initial_value)
                subs_map[old_exp] = new_exp
                agent_initial_value = sub.substitute(k, subs_map)
            else:
                agent_initial_value = self.env.expression_manager.Dot(agent, k)
            self.set_initial_value(agent_initial_value, v)

    def agent_initial_values(
        self, agent: "up.model.agent.Agent"
    ) -> Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]:
        """Returns the initial_values for the given agent"""
        agent_initial_values = {}
        for i, v in self._initial_value.items():
            if not i.is_dot() and i.args[0].is_dot():
                if type(i) is up.model.agent.Agent:
                    if agent.name == i.args[0].agent().name:
                        agent_initial_values[i] = v
            else:
                if type(i) is up.model.agent.Agent:
                    if agent.name == i.agent().name:
                        agent_initial_values[i] = v
        return agent_initial_values

    @property
    def agents_initial_values(
        self,
    ) -> Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]:
        """Returns the initial_values of agents"""
        agents_initial_values = {}
        for i, v in self._initial_value.items():
            if not i.is_dot() and i.args[0].is_dot():
                if type(i.args[0]._content.payload) is up.model.agent.Agent:
                    agents_initial_values[i] = v
            else:
                if type(i._content.payload) is up.model.agent.Agent:
                    agents_initial_values[i] = v
        return agents_initial_values

    @property
    def env_initial_values(
        self,
    ) -> Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]:
        """Returns the initial_values of MA-environment"""
        env_initial_values = {}
        for i, v in self._initial_value.items():
            if not i.is_dot() and i.args[0].is_dot():
                if (
                    type(i.args[0]._content.payload)
                    is up.model.ma_environment.MAEnvironment
                ):
                    env_initial_values[i] = v
            else:
                if type(i._content.payload) is up.model.ma_environment.MAEnvironment:
                    env_initial_values[i] = v
        return env_initial_values

    def set_env_initial_values(
        self, initial_values: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]
    ):
        """Sets the initial_values."""
        for k, v in initial_values.items():
            if not k.is_fluent_exp() and k.args[0].is_fluent_exp():
                sub = Substituter(self.env)
                subs_map = {}
                env_initial_value = self.env.expression_manager.Dot(
                    self.get_ma_environment, k.args[0]
                )
                old_exp = sub._get_key(k.args[0])
                new_exp = sub._get_key(env_initial_value)
                subs_map[old_exp] = new_exp
                env_initial_value = sub.substitute(k, subs_map)
            else:
                env_initial_value = self.env.expression_manager.Dot(
                    self.get_ma_environment, k
                )
            self.set_initial_value(env_initial_value, v)

    def _get_ith_fluent_exp(
        self, fluent: "up.model.fluent.Fluent", domain_sizes: List[int], idx: int
    ) -> "up.model.fnode.FNode":
        """Returns the ith ground fluent expression."""
        quot = idx
        rem = 0
        actual_parameters = []
        for i, p in enumerate(fluent.signature):
            ds = domain_sizes[i]
            rem = quot % ds
            quot //= ds
            v = domain_item(self, p.type, rem)
            actual_parameters.append(v)
        return fluent(*actual_parameters)

    @property
    def kind(self) -> "up.model.problem_kind.ProblemKind":
        """Returns the problem kind of this planning problem.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible."""
        self._kind = up.model.problem_kind.ProblemKind()
        self._kind.set_problem_class("ACTION_BASED_MULTI_AGENT")
        for ag in self.agents:
            for fluent in ag._fluents:
                self._update_problem_kind_fluent(fluent)
        for fluent in self.get_ma_environment._fluents:
            self._update_problem_kind_fluent(fluent)
        for ag in self.agents:
            for action in ag._actions:
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
