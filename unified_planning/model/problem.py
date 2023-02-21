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
"""This module defines the problem class."""


import unified_planning as up
from unified_planning.model.abstract_problem import AbstractProblem
from unified_planning.model.mixins import (
    ActionsSetMixin,
    FluentsSetMixin,
    ObjectsSetMixin,
    UserTypesSetMixin,
    InitialStateMixin,
)
from unified_planning.model.expression import ConstantExpression
from unified_planning.model.operators import OperatorKind
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPTypeError,
    UPExpressionDefinitionError,
)
from fractions import Fraction
from typing import Optional, List, Dict, Set, Union, cast


class Problem(
    AbstractProblem,
    UserTypesSetMixin,
    FluentsSetMixin,
    ActionsSetMixin,
    ObjectsSetMixin,
    InitialStateMixin,
):
    """
    Represents the classical planning problem, with :class:`Actions <unified_planning.model.Action>`, :class:`Fluents <unified_planning.model.Fluent>`, :class:`Objects <unified_planning.model.Object>` and :class:`UserTypes <unified_planning.model.Type>`.

    The `Actions` can be :class:`DurativeActions <unified_planning.model.DurativeAction>` when the `Problem` deals with time.
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
        FluentsSetMixin.__init__(
            self, self.environment, self._add_user_type, self.has_name, initial_defaults
        )
        ActionsSetMixin.__init__(
            self, self.environment, self._add_user_type, self.has_name
        )
        ObjectsSetMixin.__init__(
            self, self.environment, self._add_user_type, self.has_name
        )
        InitialStateMixin.__init__(self, self, self, self.environment)
        self._operators_extractor = up.model.walkers.OperatorsExtractor()
        self._timed_effects: Dict[
            "up.model.timing.Timing", List["up.model.effect.Effect"]
        ] = {}
        self._timed_goals: Dict[
            "up.model.timing.TimeInterval", List["up.model.fnode.FNode"]
        ] = {}
        self._trajectory_constraints: List["up.model.fnode.FNode"] = list()
        self._goals: List["up.model.fnode.FNode"] = list()
        self._metrics: List["up.model.metrics.PlanQualityMetric"] = []

    def __repr__(self) -> str:
        s = []
        if not self.name is None:
            s.append(f"problem name = {str(self.name)}\n\n")
        if len(self.user_types) > 0:
            s.append(f"types = {str(list(self.user_types))}\n\n")
        s.append("fluents = [\n")
        for f in self.fluents:
            s.append(f"  {str(f)}\n")
        s.append("]\n\n")
        s.append("actions = [\n")
        for a in self.actions:
            s.append(f"  {str(a)}\n")
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
        if len(self.timed_effects) > 0:
            s.append("timed effects = [\n")
            for t, el in self.timed_effects.items():
                s.append(f"  {str(t)} :\n")
                for e in el:
                    s.append(f"    {str(e)}\n")
            s.append("]\n\n")
        if len(self.timed_goals) > 0:
            s.append("timed goals = [\n")
            for i, gl in self.timed_goals.items():
                s.append(f"  {str(i)} :\n")
                for g in gl:
                    s.append(f"    {str(g)}\n")
            s.append("]\n\n")
        s.append("goals = [\n")
        for g in self.goals:
            s.append(f"  {str(g)}\n")
        s.append("]\n\n")
        if self.trajectory_constraints:
            s.append("trajectory constraints = [\n")
            for c in self.trajectory_constraints:
                s.append(f"  {str(c)}\n")
            s.append("]\n\n")
        if len(self.quality_metrics) > 0:
            s.append("quality metrics = [\n")
            for qm in self.quality_metrics:
                s.append(f"  {str(qm)}\n")
            s.append("]\n\n")
        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if not (isinstance(oth, Problem)) or self._env != oth._env:
            return False
        if self.kind != oth.kind or self._name != oth._name:
            return False
        if set(self._fluents) != set(oth._fluents) or set(self._goals) != set(
            oth._goals
        ):
            return False
        if set(self._user_types) != set(oth._user_types) or set(self._objects) != set(
            oth._objects
        ):
            return False
        if set(self._actions) != set(oth._actions):
            return False
        if set(self._trajectory_constraints) != set(oth._trajectory_constraints):
            return False
        if not self._eq_initial_state(oth):
            return False
        if len(self._timed_effects) != len(oth._timed_effects):
            return False
        for t, tel in self._timed_effects.items():
            oth_tel = oth._timed_effects.get(t, None)
            if oth_tel is None:
                return False
            elif set(tel) != set(oth_tel):
                return False
        if len(self._timed_goals) != len(oth._timed_goals):
            return False
        for i, tgl in self._timed_goals.items():
            oth_tgl = oth._timed_goals.get(i, None)
            if oth_tgl is None:
                return False
            elif set(tgl) != set(oth_tgl):
                return False
        return True

    def __hash__(self) -> int:
        res = hash(self._kind) + hash(self._name)
        for f in self._fluents:
            res += hash(f)
        for a in self._actions:
            res += hash(a)
        for ut in self._user_types:
            res += hash(ut)
        for o in self._objects:
            res += hash(o)
        for c in self._trajectory_constraints:
            res += hash(c)
        for iv in self.initial_values.items():
            res += hash(iv)
        for t, el in self._timed_effects.items():
            res += hash(t)
            for e in set(el):
                res += hash(e)
        for i, gl in self._timed_goals.items():
            res += hash(i)
            for g in set(gl):
                res += hash(g)
        for g in self._goals:
            res += hash(g)
        return res

    def clone(self):
        new_p = Problem(self._name, self._env)
        new_p._fluents = self._fluents[:]
        new_p._actions = [a.clone() for a in self._actions]
        new_p._user_types = self._user_types[:]
        new_p._user_types_hierarchy = self._user_types_hierarchy.copy()
        new_p._objects = self._objects[:]
        new_p._initial_value = self._initial_value.copy()
        new_p._timed_effects = {
            t: [e.clone() for e in el] for t, el in self._timed_effects.items()
        }
        new_p._timed_goals = {i: [g for g in gl] for i, gl in self._timed_goals.items()}
        new_p._goals = self._goals[:]
        new_p._trajectory_constraints = self._trajectory_constraints[:]
        new_p._metrics = []
        for m in self._metrics:
            if isinstance(m, up.model.metrics.MinimizeActionCosts):
                costs = {new_p.action(a.name): c for a, c in m.costs.items()}
                new_p._metrics.append(up.model.metrics.MinimizeActionCosts(costs))
            else:
                new_p._metrics.append(m)
        new_p._initial_defaults = self._initial_defaults.copy()
        new_p._fluents_defaults = self._fluents_defaults.copy()
        return new_p

    def has_name(self, name: str) -> bool:
        """
        Returns `True` if the given `name` is already in the `Problem`, `False` otherwise.

        :param name: The target name to find in the `Problem`.
        :return: `True` if the given `name` is already in the `Problem`, `False` otherwise."""
        return (
            self.has_action(name)
            or self.has_fluent(name)
            or self.has_object(name)
            or self.has_type(name)
        )

    def normalize_plan(self, plan: "up.plans.Plan") -> "up.plans.Plan":
        """
        Normalizes the given `Plan`, that is potentially the result of another
        `Problem`, updating the :class:`~unified_planning.model.Object` references present in it with the ones of
        this `Problem` which are syntactically equal.

        :param plan: The `Plan` that must be normalized.
        :return: A `Plan` syntactically valid for this `Problem`.
        """
        return plan.replace_action_instances(self._replace_action_instance)

    def _replace_action_instance(
        self, action_instance: "up.plans.ActionInstance"
    ) -> "up.plans.ActionInstance":
        em = self.environment.expression_manager
        new_a = self.action(action_instance.action.name)
        params = []
        for p in action_instance.actual_parameters:
            if p.is_object_exp():
                obj = self.object(p.object().name)
                params.append(em.ObjectExp(obj))
            elif p.is_bool_constant():
                params.append(em.Bool(p.is_true()))
            elif p.is_int_constant():
                params.append(em.Int(cast(int, p.constant_value())))
            elif p.is_real_constant():
                params.append(em.Real(cast(Fraction, p.constant_value())))
            else:
                raise NotImplementedError
        return up.plans.ActionInstance(new_a, tuple(params))

    def get_static_fluents(self) -> Set["up.model.fluent.Fluent"]:
        """
        Returns the set of the `static fluents`.

        `Static fluents` are those who can't change their values because they never
        appear in the :func:`fluent <unified_planning.model.Effect.fluent>` field of an `Effect`, therefore there are no :func:`Actions <unified_planning.model.Problem.actions>`
        in the `Problem` that can change their value.
        """
        static_fluents: Set["up.model.fluent.Fluent"] = set(self._fluents)
        for a in self._actions:
            if isinstance(a, up.model.action.InstantaneousAction):
                for e in a.effects:
                    static_fluents.discard(e.fluent.fluent())
                if a.simulated_effect is not None:
                    for f in a.simulated_effect.fluents:
                        static_fluents.discard(f.fluent())
            elif isinstance(a, up.model.action.DurativeAction):
                for el in a.effects.values():
                    for e in el:
                        static_fluents.discard(e.fluent.fluent())
                for _, se in a.simulated_effects.items():
                    for f in se.fluents:
                        static_fluents.discard(f.fluent())
            else:
                raise NotImplementedError
        for el in self._timed_effects.values():
            for e in el:
                if e.fluent.fluent() in static_fluents:
                    static_fluents.remove(e.fluent.fluent())
        return static_fluents

    def add_timed_goal(
        self,
        interval: Union["up.model.timing.Timing", "up.model.timing.TimeInterval"],
        goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool],
    ):
        """
        Adds the `timed goal` to the `Problem`. A `timed goal` is a `goal` that must be satisfied in a
        given period of time.

        :param interval: The interval of time in which the given goal must be `True`.
        :param goal: The expression that must be evaluated to `True` in the given `interval`.
        """
        assert (
            isinstance(goal, bool) or goal.environment == self._env
        ), "timed_goal does not have the same environment of the problem"
        if isinstance(interval, up.model.Timing):
            interval = up.model.TimePointInterval(interval)
        if (interval.lower.is_from_end() and interval.lower.delay > 0) or (
            interval.upper.is_from_end() and interval.upper.delay > 0
        ):
            raise UPProblemDefinitionError(
                "Problem timing can not be `end - k` with k > 0."
            )
        (goal_exp,) = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        goals = self._timed_goals.setdefault(interval, [])
        if goal_exp not in goals:
            goals.append(goal_exp)

    @property
    def timed_goals(
        self,
    ) -> Dict["up.model.timing.TimeInterval", List["up.model.fnode.FNode"]]:
        """Returns all the `timed goals` in the `Problem`."""
        return self._timed_goals

    def clear_timed_goals(self):
        """Removes all the `timed goals` from the `Problem`."""
        self._timed_goals = {}

    def add_timed_effect(
        self,
        timing: "up.model.timing.Timing",
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
    ):
        """
        Adds the given `timed effect` to the `Problem`; a `timed effect` is an :class:`~unified_planning.model.Effect` applied at a fixed time.

        :param timing: The exact time in which the given `Effect` is applied.
        :param fluent: The fluent modified by the `Effect`.
        :param value: The value assigned to the given `fluent` at the given `time`.
        :param condition: The condition that must be evaluated to `True` in order for this `Effect` to be
            actually applied.
        """
        if timing.is_from_end():
            raise UPProblemDefinitionError(
                f"Timing used in timed effect cannot be EndTiming."
            )
        (
            fluent_exp,
            value_exp,
            condition_exp,
        ) = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPTypeError("Effect condition is not a Boolean condition!")
        if not fluent_exp.type.is_compatible(value_exp.type):
            raise UPTypeError("Timed effect has not compatible types!")
        self._add_effect_instance(
            timing, up.model.effect.Effect(fluent_exp, value_exp, condition_exp)
        )

    def add_increase_effect(
        self,
        timing: "up.model.timing.Timing",
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
    ):
        """
        Adds the given `timed increase effect` to the `Problem`; a `timed effect` is an :class:`~unified_planning.model.Effect` applied at a fixed time.

        :param timing: The exact time in which the given `Effect` is applied.
        :param fluent: The fluent increased by the `Effect`.
        :param value: The value of which the given `fluent` is increased at the given `time`.
        :param condition: The condition that must be evaluated to `True` in order for this `Effect` to be
            actually applied.
        """
        (
            fluent_exp,
            value_exp,
            condition_exp,
        ) = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not condition_exp.type.is_bool_type():
            raise UPTypeError("Effect condition is not a Boolean condition!")
        if not fluent_exp.type.is_compatible(value_exp.type):
            raise UPTypeError("Timed effect has not compatible types!")
        if not fluent_exp.type.is_int_type() and not fluent_exp.type.is_real_type():
            raise UPTypeError("Decrease effects can be created only on numeric types!")
        self._add_effect_instance(
            timing,
            up.model.effect.Effect(
                fluent_exp,
                value_exp,
                condition_exp,
                kind=up.model.effect.EffectKind.INCREASE,
            ),
        )

    def add_decrease_effect(
        self,
        timing: "up.model.timing.Timing",
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
    ):
        """
        Adds the given timed decrease effect to the problem; a `timed effect` is an :class:`~unified_planning.model.Effect` applied at a fixed time.

        :param timing: The exact time in which the given `Effect` is applied.
        :param fluent: The fluent decreased by the `Effect`.
        :param value: The value of which the given `fluent` is decrease at the given `time`.
        :param condition: The condition that must be evaluated to `True` in order for this `Effect` to be
            actually applied.
        """
        (
            fluent_exp,
            value_exp,
            condition_exp,
        ) = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not condition_exp.type.is_bool_type():
            raise UPTypeError("Effect condition is not a Boolean condition!")
        if not fluent_exp.type.is_compatible(value_exp.type):
            raise UPTypeError("Timed effect has not compatible types!")
        if not fluent_exp.type.is_int_type() and not fluent_exp.type.is_real_type():
            raise UPTypeError("Decrease effects can be created only on numeric types!")
        self._add_effect_instance(
            timing,
            up.model.effect.Effect(
                fluent_exp,
                value_exp,
                condition_exp,
                kind=up.model.effect.EffectKind.DECREASE,
            ),
        )

    def _add_effect_instance(
        self, timing: "up.model.timing.Timing", effect: "up.model.effect.Effect"
    ):
        assert (
            effect.environment == self._env
        ), "effect does not have the same environment of the problem"
        effects = self._timed_effects.setdefault(timing, [])
        if effect not in effects:
            effects.append(effect)

    @property
    def timed_effects(
        self,
    ) -> Dict["up.model.timing.Timing", List["up.model.effect.Effect"]]:
        """Returns all the `timed effects` in the `Problem`."""
        return self._timed_effects

    def clear_timed_effects(self):
        """Removes all the `timed effects` from the `Problem`."""
        self._timed_effects = {}

    def add_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        """
        Adds the given `goal` to the `Problem`; a goal is an expression that must be evaluated to `True` at the
        end of the execution of a :class:`~unified_planning.plans.Plan`. If a `Plan` does not satisfy all the given `goals`, it is not valid.

        :param goal: The expression added to the `Problem` :func:`goals <unified_planning.model.Problem.goals>`.
        """
        assert (
            isinstance(goal, bool) or goal.environment == self._env
        ), "goal does not have the same environment of the problem"
        (goal_exp,) = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        if goal_exp != self._env.expression_manager.TRUE():
            self._goals.append(goal_exp)

    def add_trajectory_constraint(self, constraint: "up.model.fnode.FNode"):
        """
        Adds the given `trajectory_constraint` to the `Problem`;
        a trajectory_constraint is an expression defined as:
        Always, Sometime, At-Most-Once, Sometime-Before, Sometime-After or
        defined with universal quantifiers.
        Nesting of these temporal operators is forbidden.

        :param trajectory_constraint: The expression added to the `Problem`.
        """
        if constraint.is_and() or constraint.is_forall():
            for arg in constraint.args:
                assert (
                    arg.is_sometime()
                    or arg.is_sometime_after()
                    or arg.is_sometime_before()
                    or arg.is_at_most_once()
                    or arg.is_always()
                ), "trajectory constraint not in the correct form"
        else:
            assert (
                constraint.is_sometime()
                or constraint.is_sometime_after()
                or constraint.is_sometime_before()
                or constraint.is_at_most_once()
                or constraint.is_always()
            ), "trajectory constraint not in the correct form"
        self._trajectory_constraints.append(constraint.simplify())

    @property
    def goals(self) -> List["up.model.fnode.FNode"]:
        """Returns all the `goals` in the `Problem`."""
        return self._goals

    @property
    def trajectory_constraints(self) -> List["up.model.fnode.FNode"]:
        """Returns the 'trajectory_constraints' in the 'Problem'."""
        return self._trajectory_constraints

    def clear_goals(self):
        """Removes all the `goals` from the `Problem`."""
        self._goals = []

    def clear_trajectory_constraints(self):
        """Removes the trajectory_constraints."""
        self._trajectory_constraints = []

    def add_quality_metric(self, metric: "up.model.metrics.PlanQualityMetric"):
        """
        Adds the given `quality metric` to the `Problem`; a `quality metric` defines extra requirements that a :class:`~unified_planning.plans.Plan`
        must satisfy in order to be valid.

        :param metric: The `quality metric` that a `Plan` of this `Problem` must satisfy in order to be valid.
        """
        self._metrics.append(metric)

    @property
    def quality_metrics(self) -> List["up.model.metrics.PlanQualityMetric"]:
        """Returns all the `quality metrics` in the `Problem`."""
        return self._metrics

    def clear_quality_metrics(self):
        """Removes all the `quality metrics` in the `Problem`."""
        self._metrics = []

    @property
    def kind(self) -> "up.model.problem_kind.ProblemKind":
        """
        Calculates and returns the `problem kind` of this `planning problem`.
        If the `Problem` is modified, this method must be called again in order to be reliable.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible.
        """
        # Create the needed data structures
        fluents_to_only_increase: Set["up.model.fluent.Fluent"] = set()
        fluents_to_only_decrease: Set["up.model.fluent.Fluent"] = set()
        static_fluents: Set["up.model.fluent.Fluent"] = self.get_static_fluents()

        # Create a simplifier and a linear_checker with the problem, so static fluents can be considered as constants
        simplifier = up.model.walkers.simplifier.Simplifier(self._env, self)
        linear_checker = up.model.walkers.linear_checker.LinearChecker(self)
        self._kind = up.model.problem_kind.ProblemKind()
        self._kind.set_problem_class("ACTION_BASED")
        self._kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        for metric in self._metrics:
            if isinstance(metric, up.model.metrics.MinimizeExpressionOnFinalState):
                self._kind.set_quality_metrics("FINAL_VALUE")
                (
                    is_linear,
                    fnode_to_only_increase,  # positive fluents in minimize can only be increased
                    fnode_to_only_decrease,  # negative fluents in minimize can only be decreased
                ) = linear_checker.get_fluents(metric.expression)
                if is_linear:
                    fluents_to_only_increase = {
                        e.fluent() for e in fnode_to_only_increase
                    }
                    fluents_to_only_decrease = {
                        e.fluent() for e in fnode_to_only_decrease
                    }
                else:
                    self._kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
            elif isinstance(metric, up.model.metrics.MaximizeExpressionOnFinalState):
                self._kind.set_quality_metrics("FINAL_VALUE")
                (
                    is_linear,
                    fnode_to_only_decrease,  # positive fluents in maximize can only be decreased
                    fnode_to_only_increase,  # negative fluents in maximize can only be increased
                ) = linear_checker.get_fluents(metric.expression)
                if is_linear:
                    fluents_to_only_increase = {
                        e.fluent() for e in fnode_to_only_increase
                    }
                    fluents_to_only_decrease = {
                        e.fluent() for e in fnode_to_only_decrease
                    }
                else:
                    self._kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
            elif isinstance(metric, up.model.metrics.MinimizeActionCosts):
                self._kind.set_quality_metrics("ACTIONS_COST")
            elif isinstance(metric, up.model.metrics.MinimizeMakespan):
                self._kind.set_quality_metrics("MAKESPAN")
            elif isinstance(metric, up.model.metrics.MinimizeSequentialPlanLength):
                self._kind.set_quality_metrics("PLAN_LENGTH")
            elif isinstance(metric, up.model.metrics.Oversubscription):
                self._kind.set_quality_metrics("OVERSUBSCRIPTION")
            else:
                assert False, "Unknown quality metric"
        for fluent in self._fluents:
            self._update_problem_kind_fluent(fluent)
        for object in self._objects:
            self._update_problem_kind_type(object.type)
        for action in self._actions:
            self._update_problem_kind_action(
                action,
                fluents_to_only_increase,
                fluents_to_only_decrease,
                static_fluents,
                simplifier,
                linear_checker,
            )
        if len(self._timed_effects) > 0:
            self._kind.set_time("CONTINUOUS_TIME")
            self._kind.set_time("TIMED_EFFECT")
        for effect_list in self._timed_effects.values():
            for effect in effect_list:
                self._update_problem_kind_effect(
                    effect,
                    fluents_to_only_increase,
                    fluents_to_only_decrease,
                    simplifier,
                    linear_checker,
                )
        if len(self._timed_goals) > 0:
            self._kind.set_time("TIMED_GOALS")
            self._kind.set_time("CONTINUOUS_TIME")
        if len(self._trajectory_constraints) > 0:
            self._kind.set_constraints_kind("TRAJECTORY_CONSTRAINTS")
        for goal_list in self._timed_goals.values():
            for goal in goal_list:
                self._update_problem_kind_condition(goal, linear_checker)
        for goal in self._goals:
            self._update_problem_kind_condition(goal, linear_checker)
        if (
            not self._kind.has_continuous_numbers()
            and not self._kind.has_discrete_numbers()
        ):
            self._kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
        else:
            if not self._kind.has_simple_numeric_planning():
                self._kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        return self._kind

    def _update_problem_kind_effect(
        self,
        e: "up.model.effect.Effect",
        fluents_to_only_increase: Set["up.model.fluent.Fluent"],
        fluents_to_only_decrease: Set["up.model.fluent.Fluent"],
        simplifier: "up.model.walkers.simplifier.Simplifier",
        linear_checker: "up.model.walkers.linear_checker.LinearChecker",
    ):
        value = simplifier.simplify(e.value)
        if e.is_conditional():
            self._update_problem_kind_condition(e.condition, linear_checker)
            self._kind.set_effects_kind("CONDITIONAL_EFFECTS")
        if e.is_increase():
            self._kind.set_effects_kind("INCREASE_EFFECTS")
            # If the value is a number (int or real) and it violates the constraint
            # on the "fluents_to_only_increase" or on "fluents_to_only_decrease",
            # unset simple_numeric_planning
            if (  # value is a constant number
                value.is_int_constant() or value.is_real_constant()
            ):
                if (
                    e.fluent in fluents_to_only_increase and value.constant_value() < 0
                ) or (
                    e.fluent in fluents_to_only_decrease and value.constant_value() > 0
                ):
                    self._kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
            else:
                self._kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
        elif e.is_decrease():
            self._kind.set_effects_kind("DECREASE_EFFECTS")
            # If the value is a number (int or real) and it violates the constraint
            # on the "fluents_to_only_increase" or on "fluents_to_only_decrease",
            # unset simple_numeric_planning
            if (  # value is a constant number
                value.is_int_constant() or value.is_real_constant()
            ):
                if (
                    e.fluent in fluents_to_only_increase and value.constant_value() > 0
                ) or (
                    e.fluent in fluents_to_only_decrease and value.constant_value() < 0
                ):
                    self._kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
            else:
                self._kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
        elif e.is_assignment():
            value_type = value.type
            if (
                value_type.is_int_type() or value_type.is_real_type()
            ):  # the value is a number
                if (  # if the fluent has increase/decrease constraints or the value assigned is not a constant,
                    # unset "SIMPLE_NUMERIC_PLANNING"
                    e.fluent in fluents_to_only_increase
                    or e.fluent in fluents_to_only_decrease
                    or not value.is_constant()
                ):
                    self._kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")

    def _update_problem_kind_condition(
        self,
        exp: "up.model.fnode.FNode",
        linear_checker: "up.model.walkers.linear_checker.LinearChecker",
    ):
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
        is_linear, _, _ = linear_checker.get_fluents(exp)
        if not is_linear:
            self._kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")

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

    def _update_problem_kind_action(
        self,
        action: "up.model.action.Action",
        fluents_to_only_increase: Set["up.model.fluent.Fluent"],
        fluents_to_only_decrease: Set["up.model.fluent.Fluent"],
        static_fluents: Set["up.model.fluent.Fluent"],
        simplifier: "up.model.walkers.simplifier.Simplifier",
        linear_checker: "up.model.walkers.linear_checker.LinearChecker",
    ):
        for p in action.parameters:
            self._update_problem_kind_type(p.type)
        if isinstance(action, up.model.action.SensingAction):
            self._kind.set_problem_class("CONTINGENT")
        if isinstance(action, up.model.action.InstantaneousAction):
            for c in action.preconditions:
                self._update_problem_kind_condition(c, linear_checker)
            for e in action.effects:
                self._update_problem_kind_effect(
                    e,
                    fluents_to_only_increase,
                    fluents_to_only_decrease,
                    simplifier,
                    linear_checker,
                )
            if action.simulated_effect is not None:
                self._kind.set_simulated_entities("SIMULATED_EFFECTS")
        elif isinstance(action, up.model.action.DurativeAction):
            lower, upper = action.duration.lower, action.duration.upper
            if lower != upper:
                self._kind.set_time("DURATION_INEQUALITIES")
            free_vars = self.environment.free_vars_extractor.get(
                lower
            ) | self.environment.free_vars_extractor.get(upper)
            if len(free_vars) > 0:
                only_static = True
                for fv in free_vars:
                    if fv.fluent() not in static_fluents:
                        only_static = False
                        break
                if only_static:
                    self._kind.set_expression_duration("STATIC_FLUENTS_IN_DURATION")
                else:
                    self._kind.set_expression_duration("FLUENTS_IN_DURATION")
            for i, lc in action.conditions.items():
                if i.lower.delay != 0 or i.upper.delay != 0:
                    self._kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
                for c in lc:
                    self._update_problem_kind_condition(c, linear_checker)
            for t, le in action.effects.items():
                if t.delay != 0:
                    self._kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
                for e in le:
                    self._update_problem_kind_effect(
                        e,
                        fluents_to_only_increase,
                        fluents_to_only_decrease,
                        simplifier,
                        linear_checker,
                    )
            if len(action.simulated_effects) > 0:
                self._kind.set_simulated_entities("SIMULATED_EFFECTS")
            self._kind.set_time("CONTINUOUS_TIME")
        else:
            raise NotImplementedError
