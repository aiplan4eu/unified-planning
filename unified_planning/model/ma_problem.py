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
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPTypeError,
    UPExpressionDefinitionError,
    UPValueError,
)
from fractions import Fraction
from typing import List, Dict, Set, Union, cast
from unified_planning.model.abstract_problem import AbstractProblem
from unified_planning.model.mixins import (
    ObjectsSetMixin,
    UserTypesSetMixin,
    AgentsSetMixin,
)


class MultiAgentProblem(
    AbstractProblem,
    UserTypesSetMixin,
    ObjectsSetMixin,
    AgentsSetMixin
):
    """Represents a planning MultiAgentProblem."""

    def __init__(
        self,
        name: str = None,
        env: "up.environment.Environment" = None,
        *,
        initial_defaults: Dict["up.model.types.Type", "ConstantExpression"] = {}
    ):
        AbstractProblem.__init__(self, name, env)
        UserTypesSetMixin.__init__(self, self.has_name)
        ObjectsSetMixin.__init__(self, self.env, self._add_user_type, self.has_name)
        AgentsSetMixin.__init__(self, self.env, self.has_name)

        self._initial_defaults = initial_defaults
        self._env_ma: "up.model.MAEnvironment" = up.model.MAEnvironment(self)
        self._env_initial_value: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"] = {}
        self._agent_goals: Dict["up.model.agent.Agent", List["up.model.fnode.FNode"]] = {}
        self._agent_initial_value: Dict["up.model.agent.Agent", List[Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]]] = {}
        self._operators_extractor = up.model.walkers.OperatorsExtractor()
        self._env_goals: List["up.model.fnode.FNode"] = list()

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
            if len(self.get_ma_environment.fluents) > 0: # type: ignore
                for f in self.get_ma_environment.fluents: # type: ignore
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
        for ag, initial_values in self.agents_initial_values.items():
            for initial_value in initial_values:
                for k, v in initial_value.items():
                    s.append(f" {str(ag._name)}: {str(k)} := {str(v)}\n")
        s.append("]\n\n")

        s.append("MA-environment initial values = [\n")
        for k, v in self._env_initial_value.items():
            s.append(f" MA-environment: {str(k)} := {str(v)}\n")
        s.append("]\n\n")

        s.append("agents goals = [\n")
        for ag, goal in self.agents_goals.items():
            s.append(f" {str(ag._name)}: {str(goal)}\n")
        s.append("]\n\n")

        s.append("MA-environment goals = [\n")
        if len(self._env_goals) > 0:
            for g in self._env_goals:
                s.append(f"  {'MA-Environment'} {str(g)}\n")
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
        for iv in self._env_initial_value.items():
            res += hash(iv)
        for goals in self._agent_goals.values():
            for g in goals:
                res += hash(g)
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
        """Add a MAenvironment."""
        self._env_ma = env_ma
        return self._env_ma

    @property
    def get_ma_environment(self) -> ["up.model.MAEnvironment"]:
        """Get a MA-environment."""
        return self._env_ma

    def set_env_initial_value(
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
        """Sets the MA-environment initial value for the given fluent."""
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        if not self._env.type_checker.is_compatible_exp(fluent_exp, value_exp):
            raise UPTypeError("Initial value assignment has not compatible types!")
        self._env_initial_value[fluent_exp] = value_exp

    def set_env_initial_values(
            self,
            initial_values: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]
    ):
        """Sets the initial_values for the given agent."""
        for k, v in initial_values.items():
            self.set_env_initial_value(k, v)

    def env_initial_value(
        self, fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"]
    ) -> "up.model.fnode.FNode":
        """Gets the initial value of the given fluent."""
        (fluent_exp,) = self._env.expression_manager.auto_promote(fluent)
        for a in fluent_exp.args:
            if not a.is_constant():
                raise UPExpressionDefinitionError(
                    f"Impossible to return the initial value of a fluent expression with no constant arguments: {fluent_exp}."
                )
        if fluent_exp in self._env_initial_value:
            return self._env_initial_value[fluent_exp]
        elif fluent_exp.fluent() in self.get_ma_environment._fluents_defaults:
            return self.get_ma_environment._fluents_defaults[fluent_exp.fluent()]
        else:
            raise UPProblemDefinitionError("Initial value not set!")

    @property
    def env_initial_values(self) -> Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]:
        """Gets the MA-environment initial value of the fluents.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible."""
        res = self._env_initial_value
        for f in self.get_ma_environment.fluents:
            if f.arity == 0:
                f_exp = self._env.expression_manager.FluentExp(f)
                res[f_exp] = self.env_initial_value(f_exp)
            else:
                ground_size = 1
                domain_sizes = []
                for p in f.signature:
                    ds = domain_size(self, p.type)
                    domain_sizes.append(ds)
                    ground_size *= ds
                for i in range(ground_size):
                    f_exp = self._get_ith_fluent_exp(f, domain_sizes, i)
                    res[f_exp] = self.env_initial_value(f_exp)
        return res

    def add_env_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        """Adds a MA-environment goal ."""
        assert (isinstance(goal, bool) or goal.environment == self._env), "goal does not have the same environment of the problem"
        (goal_exp,) = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        if goal_exp != self._env.expression_manager.TRUE():
            self._env_goals.append(goal_exp)

    def set_agent_goal(
            self,
            agent: "up.model.agent.Agent",
            goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        """Sets the goal for the given agent."""
        assert (isinstance(goal, bool) or goal.environment == self._env), "goal does not have the same environment of the problem"
        (goal_exp,) = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        if goal_exp != self._env.expression_manager.TRUE():
            if agent in self.agents:
                self._agent_goals.setdefault(agent, [])
                self._agent_goals[agent].append(goal_exp)
            else:
                raise UPValueError(f"Agent {agent._name} is not defined!")

    def add_env_goals(
            self,
            goals: List[Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]]
    ):
        """Sets the goals for the MA-environment."""
        for goal in goals:
            self.add_env_goal(goal)

    @property
    def env_goals(self) -> List["up.model.fnode.FNode"]:
        """Returns the goals."""
        return self._env_goals

    def set_agent_initial_value(
            self,
            agent: "up.model.agent.Agent",
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
        """Sets the initial value for the given agent."""
        initial_value = {}
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        if not self._env.type_checker.is_compatible_exp(fluent_exp, value_exp):
            raise UPTypeError("Initial value assignment has not compatible types!")
        initial_value[fluent_exp] = value_exp

        if agent in self.agents:
            self._agent_initial_value.setdefault(agent, [])
            self._agent_initial_value[agent].append(initial_value)
        else:
            print(self.agents)
            raise UPValueError(f"Agent {agent._name} is not defined!")

    def set_agent_initial_values(
            self,
            agent: "up.model.agent.Agent",
            initial_values: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]
    ):
        """Sets the initial_values for the given agent."""
        for k, v in initial_values.items():
            self.set_agent_initial_value(agent, k, v)


    @property
    def agents_initial_values(self) -> Dict["up.model.agent.Agent", List[Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]]]:
        """Returns the goals."""
        return self._agent_initial_value

    def set_agent_goals(
            self,
            agent: "up.model.agent.Agent",
            goals: List[Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]]
    ):
        """Sets the goals for the given agent."""
        for goal in goals:
            self.set_agent_goal(agent, goal)

    @property
    def agents_goals(self) -> Dict["up.model.agent.Agent", List["up.model.fnode.FNode"]]:
        """Returns the goals."""
        return self._agent_goals

    def agent_goals(
            self,
            agent:  "up.model.agent.Agent"
    ):
        """Returns the goals for the given agent"""
        if agent in self._agent_goals.keys():
            return self._agent_goals[agent]

    def clear_agent_goals(self, agent):
        """Removes the goals."""
        self._agent_goals[agent] = []

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
        for agent_goals in self.agents_goals.values():
            for goal in agent_goals:
                self._update_problem_kind_condition(goal)
        for goal in self.env_goals:
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