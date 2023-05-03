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


from numbers import Real
import unified_planning as up
import unified_planning.model.tamp
from unified_planning.model.abstract_problem import AbstractProblem
from unified_planning.model.mixins import (
    ActionsSetMixin,
    TimeModelMixin,
    FluentsSetMixin,
    GlobalConstraintsMixin,
    ObjectsSetMixin,
    UserTypesSetMixin,
    InitialStateMixin,
    MetricsMixin,
)
from unified_planning.model.expression import ConstantExpression
from unified_planning.model.operators import OperatorKind
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPTypeError,
)
from fractions import Fraction
from typing import Optional, List, Dict, Set, Tuple, Union, cast


class Problem(  # type: ignore[misc]
    AbstractProblem,
    UserTypesSetMixin,
    TimeModelMixin,
    FluentsSetMixin,
    GlobalConstraintsMixin,
    ActionsSetMixin,
    ObjectsSetMixin,
    InitialStateMixin,
    MetricsMixin,
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
        TimeModelMixin.__init__(
            self, epsilon_default=None, discrete_time=False, self_overlapping=False
        )
        FluentsSetMixin.__init__(
            self, self.environment, self._add_user_type, self.has_name, initial_defaults
        )
        GlobalConstraintsMixin.__init__(self, self.environment)
        ActionsSetMixin.__init__(
            self, self.environment, self._add_user_type, self.has_name
        )
        ObjectsSetMixin.__init__(
            self, self.environment, self._add_user_type, self.has_name
        )
        InitialStateMixin.__init__(self, self, self, self.environment)
        MetricsMixin.__init__(self, self.environment)
        self._operators_extractor = up.model.walkers.OperatorsExtractor()
        self._timed_effects: Dict[
            "up.model.timing.Timing", List["up.model.effect.Effect"]
        ] = {}
        self._timed_goals: Dict[
            "up.model.timing.TimeInterval", List["up.model.fnode.FNode"]
        ] = {}
        self._trajectory_constraints: List["up.model.fnode.FNode"] = list()
        self._goals: List["up.model.fnode.FNode"] = list()
        self._fluents_assigned: Dict[
            "up.model.timing.Timing",
            Dict["up.model.fnode.FNode", "up.model.fnode.FNode"],
        ] = {}
        self._fluents_inc_dec: Dict[
            "up.model.timing.Timing", Set["up.model.fnode.FNode"]
        ] = {}

    def __repr__(self) -> str:
        s = []
        custom_str = lambda x: f"  {str(x)}\n"
        if self.name is not None:
            s.append(f"problem name = {str(self.name)}\n\n")
        if self._epsilon is not None:
            s.append(f"epsilon separation = {self._epsilon}\n\n")
        if len(self.user_types) > 0:
            s.append(f"types = {str(list(self.user_types))}\n\n")
        s.append("fluents = [\n")
        s.extend(map(custom_str, self.fluents))
        s.append("]\n\n")
        s.append("actions = [\n")
        s.extend(map(custom_str, self.actions))
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
        s.extend(map(custom_str, self.goals))
        s.append("]\n\n")
        if self.trajectory_constraints:
            s.append("trajectory constraints = [\n")
            s.extend(map(custom_str, self.trajectory_constraints))
            s.append("]\n\n")
        if self.global_constraints:
            s.append("global constraints = [\n")
            s.extend(map(custom_str, self.global_constraints))
            s.append("]\n\n")
        if len(self.quality_metrics) > 0:
            s.append("quality metrics = [\n")
            s.extend(map(custom_str, self.quality_metrics))
            s.append("]\n\n")
        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if not (isinstance(oth, Problem)) or self._env != oth._env:
            return False
        if self.kind != oth.kind or self._name != oth._name:
            return False

        if not UserTypesSetMixin.__eq__(self, oth):
            return False
        if not ObjectsSetMixin.__eq__(self, oth):
            return False
        if not FluentsSetMixin.__eq__(self, oth):
            return False
        if not GlobalConstraintsMixin.__eq__(self, oth):
            return False
        if not InitialStateMixin.__eq__(self, oth):
            return False
        if not MetricsMixin.__eq__(self, oth):
            return False

        if set(self._goals) != set(oth._goals):
            return False
        if set(self._actions) != set(oth._actions):
            return False
        if set(self._trajectory_constraints) != set(oth._trajectory_constraints):
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
        res = hash(self._name)

        res += FluentsSetMixin.__hash__(self)
        res += GlobalConstraintsMixin.__hash__(self)
        res += ObjectsSetMixin.__hash__(self)
        res += UserTypesSetMixin.__hash__(self)
        res += InitialStateMixin.__hash__(self)
        res += MetricsMixin.__hash__(self)

        for a in self._actions:
            res += hash(a)
        for c in self._trajectory_constraints:
            res += hash(c)
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
        UserTypesSetMixin._clone_to(self, new_p)
        ObjectsSetMixin._clone_to(self, new_p)
        FluentsSetMixin._clone_to(self, new_p)
        InitialStateMixin._clone_to(self, new_p)
        TimeModelMixin._clone_to(self, new_p)

        new_p._actions = [a.clone() for a in self._actions]
        new_p._timed_effects = {
            t: [e.clone() for e in el] for t, el in self._timed_effects.items()
        }
        new_p._timed_goals = {i: [g for g in gl] for i, gl in self._timed_goals.items()}
        new_p._goals = self._goals[:]
        new_p._trajectory_constraints = self._trajectory_constraints[:]
        new_p._fluents_assigned = {
            t: d.copy() for t, d in self._fluents_assigned.items()
        }

        # last as it requires actions to be cloned already
        MetricsMixin._clone_to(self, new_p, new_actions=new_p)
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

    def _get_static_and_unused_fluents(
        self,
    ) -> Tuple[Set["up.model.fluent.Fluent"], Set["up.model.fluent.Fluent"]]:
        """
        Support method to calculate the set of static fluents (The fluents that are never modified in the problem)
        and the set of the unused fluents (The fluents that are never red in the problem.
        NOTE: The fluents used only in the ActionCost quality metric are in the unused_fluents set anyway).
        """
        static_fluents: Set["up.model.fluent.Fluent"] = set(self._fluents)
        unused_fluents: Set["up.model.fluent.Fluent"] = set(self._fluents)
        fve = self._env.free_vars_extractor
        # function that takes an FNode and removes all the fluents contained in the given FNode
        # from the unused_fluents  set.
        remove_used_fluents = lambda *exps: unused_fluents.difference_update(
            (f.fluent() for e in exps for f in fve.get(e))
        )
        for a in self._actions:
            if isinstance(a, up.model.action.InstantaneousAction):
                remove_used_fluents(*a.preconditions)
                for e in a.effects:
                    remove_used_fluents(e.fluent, e.value, e.condition)
                    static_fluents.discard(e.fluent.fluent())
                if a.simulated_effect is not None:
                    # empty the set because a simulated effect reads all the fluents
                    unused_fluents.clear()
                    for f in a.simulated_effect.fluents:
                        static_fluents.discard(f.fluent())
            elif isinstance(a, up.model.action.DurativeAction):
                for cl in a.conditions.values():
                    remove_used_fluents(*cl)
                for el in a.effects.values():
                    for e in el:
                        remove_used_fluents(e.fluent, e.value, e.condition)
                        static_fluents.discard(e.fluent.fluent())
                for se in a.simulated_effects.values():
                    unused_fluents.clear()
                    for f in se.fluents:
                        static_fluents.discard(f.fluent())
            else:
                raise NotImplementedError
        for el in self._timed_effects.values():
            for e in el:
                remove_used_fluents(e.fluent, e.value, e.condition)
                static_fluents.discard(e.fluent.fluent())
        for gl in self._timed_goals.values():
            remove_used_fluents(*gl)
        remove_used_fluents(*self._trajectory_constraints)
        remove_used_fluents(*self._goals)
        for qm in self.quality_metrics:
            if isinstance(
                qm,
                (
                    up.model.metrics.MinimizeExpressionOnFinalState,
                    up.model.metrics.MaximizeExpressionOnFinalState,
                ),
            ):
                remove_used_fluents(qm.expression)
            elif isinstance(qm, up.model.metrics.Oversubscription):
                remove_used_fluents(*qm.goals.keys())
            elif isinstance(qm, up.model.metrics.TemporalOversubscription):
                for _, g in qm.goals.keys():
                    remove_used_fluents(g)
        return static_fluents, unused_fluents

    def get_static_fluents(self) -> Set["up.model.fluent.Fluent"]:
        """
        Returns the set of the `static fluents`.

        `Static fluents` are those who can't change their values because they never
        appear in the :func:`fluent <unified_planning.model.Effect.fluent>` field of an `Effect`, therefore there are no :func:`Actions <unified_planning.model.Problem.actions>`
        in the `Problem` that can change their value.
        """
        return self._get_static_and_unused_fluents()[0]

    @property
    def timed_goals(
        self,
    ) -> Dict["up.model.timing.TimeInterval", List["up.model.fnode.FNode"]]:
        """Returns all the `timed goals` in the `Problem`."""
        return self._timed_goals

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

    def clear_timed_goals(self):
        """Removes all the `timed goals` from the `Problem`."""
        self._timed_goals = {}

    @property
    def timed_effects(
        self,
    ) -> Dict["up.model.timing.Timing", List["up.model.effect.Effect"]]:
        """Returns all the `timed effects` in the `Problem`."""
        return self._timed_effects

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
        fluents_inc_dec = self._fluents_inc_dec.setdefault(timing, set())

        up.model.effect.check_conflicting_effects(
            effect,
            timing,
            None,
            self._fluents_assigned.setdefault(timing, {}),
            fluents_inc_dec,
            "problem",
        )
        self._timed_effects.setdefault(timing, []).append(effect)

    def clear_timed_effects(self):
        """Removes all the `timed effects` from the `Problem`."""
        self._timed_effects = {}
        self._fluents_assigned = {}
        self._fluents_inc_dec = {}

    @property
    def goals(self) -> List["up.model.fnode.FNode"]:
        """Returns all the `goals` in the `Problem`."""
        return self._goals

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

    def clear_goals(self):
        """Removes all the `goals` from the `Problem`."""
        self._goals = []

    @property
    def trajectory_constraints(self) -> List["up.model.fnode.FNode"]:
        """Returns the 'trajectory_constraints' in the 'Problem'."""
        return self._trajectory_constraints

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

    def clear_trajectory_constraints(self):
        """Removes the trajectory_constraints."""
        self._trajectory_constraints = []

    @property
    def kind(self) -> "up.model.problem_kind.ProblemKind":
        """
        Calculates and returns the `problem kind` of this `planning problem`.
        If the `Problem` is modified, this method must be called again in order to be reliable.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible.
        """
        # Create the needed data structures
        static_fluents, unused_fluents = self._get_static_and_unused_fluents()

        # Create a simplifier and a linear_checker with the problem, so static fluents can be considered as constants
        simplifier = up.model.walkers.simplifier.Simplifier(self._env, self)
        linear_checker = up.model.walkers.linear_checker.LinearChecker(self)
        self._kind = up.model.problem_kind.ProblemKind()
        self._kind.set_problem_class("ACTION_BASED")
        self._kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        fluents_to_only_increase, fluents_to_only_decrease = self._update_kind_metric(
            self._kind, linear_checker, static_fluents
        )
        for fluent in self._fluents:
            self._update_problem_kind_fluent(fluent, unused_fluents)
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
            self._kind.set_time("TIMED_EFFECTS")
        for effect_list in self._timed_effects.values():
            for effect in effect_list:
                self._update_problem_kind_effect(
                    effect,
                    fluents_to_only_increase,
                    fluents_to_only_decrease,
                    static_fluents,
                    simplifier,
                    linear_checker,
                )
        if len(self._timed_goals) > 0:
            self._kind.set_time("TIMED_GOALS")
            self._kind.set_time("CONTINUOUS_TIME")
        if self._trajectory_constraints:
            self._kind.set_constraints_kind("TRAJECTORY_CONSTRAINTS")
        if self._global_constraints:
            self._kind.set_constraints_kind("GLOBAL_CONSTRAINTS")
            for gc in self._global_constraints:
                self._update_problem_kind_condition(gc, linear_checker)
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
        if self._kind.has_continuous_time() and self.discrete_time:
            self._kind.set_time("DISCRETE_TIME")
            self._kind.unset_time("CONTINUOUS_TIME")
        if self._self_overlapping and (
            self._kind.has_continuous_time() or self._kind.has_discrete_time()
        ):
            self._kind.set_time("SELF_OVERLAPPING")
        return self._kind

    def _update_problem_kind_effect(
        self,
        e: "up.model.effect.Effect",
        fluents_to_only_increase: Set["up.model.fluent.Fluent"],
        fluents_to_only_decrease: Set["up.model.fluent.Fluent"],
        static_fluents: Set["up.model.fluent.Fluent"],
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
            value = e.value
            fluents_in_value = self._env.free_vars_extractor.get(value)
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
            if any(f in static_fluents for f in fluents_in_value):
                self._kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
            if any(f not in static_fluents for f in fluents_in_value):
                self._kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
            elif value.type.is_bool_type():
                if any(f in static_fluents for f in fluents_in_value):
                    self._kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
                if any(f not in static_fluents for f in fluents_in_value):
                    self._kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")

    def _update_problem_kind_condition(
        self,
        exp: "up.model.fnode.FNode",
        linear_checker: "up.model.walkers.linear_checker.LinearChecker",
    ):
        ops = self._operators_extractor.get(exp)
        if OperatorKind.EQUALS in ops:
            self._kind.set_conditions_kind("EQUALITIES")
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

    def _update_problem_kind_fluent(
        self,
        fluent: "up.model.fluent.Fluent",
        unused_fluents: Set["up.model.fluent.Fluent"],
    ):
        type = fluent.type
        if fluent not in unused_fluents or (
            not type.is_int_type() and not type.is_real_type()
        ):
            self._update_problem_kind_type(type)
        if fluent.type.is_int_type() or type.is_real_type():
            numeric_type = type
            assert isinstance(
                numeric_type, (up.model.types._RealType, up.model.types._IntType)
            )
            if (
                numeric_type.lower_bound is not None
                or numeric_type.upper_bound is not None
            ):
                self._kind.set_numbers("BOUNDED_TYPES")
            if fluent not in unused_fluents:
                self._kind.set_fluents_type("NUMERIC_FLUENTS")
        elif type.is_user_type():
            self._kind.set_fluents_type("OBJECT_FLUENTS")
        for p in fluent.signature:
            # TODO understant if here we need a check that the fluent is not unused
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
        if isinstance(action, up.model.tamp.InstantaneousMotionAction):
            if len(action.motion_constraints) > 0:
                self._kind.set_problem_class("TAMP")
        if isinstance(action, up.model.action.InstantaneousAction):
            for c in action.preconditions:
                self._update_problem_kind_condition(c, linear_checker)
            for e in action.effects:
                self._update_problem_kind_effect(
                    e,
                    fluents_to_only_increase,
                    fluents_to_only_decrease,
                    static_fluents,
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
                    self._kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
                else:
                    self._kind.set_expression_duration("FLUENTS_IN_DURATIONS")
            for i, lc in action.conditions.items():
                if i.lower.delay != 0 or i.upper.delay != 0:
                    for t in [i.lower, i.upper]:
                        if (t.is_from_start() and t.delay > 0) or (
                            t.is_from_end() and t.delay < 0
                        ):
                            self._kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
                        else:
                            self._kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
                for c in lc:
                    self._update_problem_kind_condition(c, linear_checker)
            for t, le in action.effects.items():
                if t.delay != 0:
                    if (t.is_from_start() and t.delay > 0) or (
                        t.is_from_end() and t.delay < 0
                    ):
                        self._kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
                    else:
                        self._kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
                for e in le:
                    self._update_problem_kind_effect(
                        e,
                        fluents_to_only_increase,
                        fluents_to_only_decrease,
                        static_fluents,
                        simplifier,
                        linear_checker,
                    )
            if len(action.simulated_effects) > 0:
                self._kind.set_simulated_entities("SIMULATED_EFFECTS")
            self._kind.set_time("CONTINUOUS_TIME")
        else:
            raise NotImplementedError
