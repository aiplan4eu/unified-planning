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
    """
    Represents the multi-agent planning problem, with :class:`Agent <unified_planning.model.multi_agent.agent>`, with :class:`MAEnvironment <unified_planning.model.multi_agent.ma_environment>`, :class:`Fluents <unified_planning.model.Fluent>`, :class:`Objects <unified_planning.model.Object>` and :class:`UserTypes <unified_planning.model.Type>`.
    """

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

    def __setstate__(self, state):
        self.__dict__.update(state)
        for a in self._agents:
            a._add_user_type_method = self._add_user_type

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

    def __eq__(self, oth: object) -> bool:
        if not (isinstance(oth, MultiAgentProblem)) or self._env != oth._env:
            return False
        if self.kind != oth.kind or self._name != oth._name:
            return False
        if self.ma_environment != oth.ma_environment:
            return False
        if set(self._goals) != set(oth._goals):
            return False
        if set(self._user_types) != set(oth._user_types) or set(self._objects) != set(
            oth._objects
        ):
            return False
        if set(self._agents) != set(oth._agents):
            return False
        oth_initial_values = oth.initial_values
        for fluent, value in self.initial_values.items():
            oth_value = oth_initial_values.get(fluent, None)
            if oth_value is None:
                return False
            elif value != oth_value:
                return False
        return True

    def __hash__(self) -> int:
        res = hash(self._kind) + hash(self._name)
        res += hash(self.ma_environment)
        for a in self._agents:
            res += hash(a)
        for ut in self._user_types:
            res += hash(ut)
        for o in self._objects:
            res += hash(o)
        for iv in self.initial_values.items():
            res += hash(iv)
        for g in self._goals:
            res += hash(g)
        return res

    def clone(self):
        new_p = MultiAgentProblem(self._name, self._env)
        for f in self.ma_environment.fluents:
            new_p.ma_environment.add_fluent(f)
        for ag in self.agents:
            new_ag = up.model.multi_agent.Agent(ag.name, self)
            for f in ag.fluents:
                new_ag.add_fluent(f)
            for a in ag.actions:
                new_ag.add_action(a.clone())
        new_p._user_types = self._user_types[:]
        new_p._user_types_hierarchy = self._user_types_hierarchy.copy()
        new_p._objects = self._objects[:]
        new_p._initial_value = self._initial_value.copy()
        new_p._goals = self._goals[:]
        new_p._initial_defaults = self._initial_defaults.copy()
        return new_p

    def has_name(self, name: str) -> bool:
        """
        Returns `True` if the given `name` is already in the `MultiAgentProblem`, `False` otherwise.

        :param name: The target name to find in the `MultiAgentProblem`.
        :return: `True` if the given `name` is already in the `MultiAgentProblem`, `False` otherwise."""
        return self.has_object(name) or self.has_type(name) or self.has_agent(name)

    @property
    def ma_environment(self) -> "up.model.multi_agent.ma_environment.MAEnvironment":
        """Returns this `MultiAgentProblem` `MAEnvironment`."""
        return self._env_ma

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
        """
        Sets the initial value for the given `Fluent`. The given `Fluent` must be grounded, therefore if
        it's :func:`arity <unified_planning.model.Fluent.arity>` is `> 0`, the `fluent` parameter must be
        an `FNode` and the method :func:`~unified_planning.model.FNode.is_fluent_exp` must return `True`.

        :param fluent: The grounded `Fluent` of which the initial value must be set.
        :param value: The `value` assigned in the initial state to the given `fluent`.
        """
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        if not fluent_exp.type.is_compatible(value_exp.type):
            raise UPTypeError("Initial value assignment has not compatible types!")
        self._initial_value[fluent_exp] = value_exp

    def initial_value(
        self, fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"]
    ) -> "up.model.fnode.FNode":
        """
        Retrieves the initial value assigned to the given `fluent`.

        :param fluent: The target `fluent` of which the `value` in the initial state must be retrieved.
        :return: The `value` expression assigned to the given `fluent` in the initial state.
        """
        (fluent_exp,) = self._env.expression_manager.auto_promote(fluent)
        fluent_args = (
            fluent_exp.args if fluent_exp.is_fluent_exp() else fluent_exp.arg(0).args
        )
        for a in fluent_args:
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
        """
        Gets the initial value of all the grounded fluents present in the `MultiAgentProblem`.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible.
        """
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
        """
        Returns the problem's defined initial values; those are only the initial values set with the
        :func:`~unified_planning.model.multi_agent.MultiAgentProblem.set_initial_value` method.

        IMPORTANT NOTE: For all the initial values of the problem use :func:`initial_values <unified_planning.model.multi_agent.MultiAgentProblem.initial_values>`.
        """
        return self._initial_value

    def add_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        """
        Adds the given `goal` to the `MultiAgentProblem`; a goal is an expression that must be evaluated to `True` at the
        end of the execution of a :class:`~unified_planning.plans.Plan`. If a `Plan` does not satisfy all the given `goals`, it is not valid.

        :param goal: The expression added to the `MultiAgentProblem` :func:`goals <unified_planning.model.multi_agent.MultiAgentProblem.goals>`.
        """
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
        """
        Adds the given `goal` to the `MultiAgentProblem`.

        :param goals: The `list` of `goals` that must be added to the `MultiAgentProblem`.
        """
        for goal in goals:
            self.add_goal(goal)

    @property
    def goals(self) -> List["up.model.fnode.FNode"]:
        """Returns all the `goals` in the `MultiAgentProblem`."""
        return self._goals

    def clear_goals(self):
        """Removes all the `goals` from the `MultiAgentProblem`."""
        self._goals = []

    @property
    def kind(self) -> "up.model.problem_kind.ProblemKind":
        """
        Calculates and returns the `problem kind` of this `planning problem`.
        If the `Problem` is modified, this method must be called again in order to be reliable.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible.
        """
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
