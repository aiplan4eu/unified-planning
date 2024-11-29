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
"""This module defines the problem class."""


from itertools import chain, product
import unified_planning as up
import unified_planning.model.tamp
from unified_planning.model import Fluent
from unified_planning.model.abstract_problem import AbstractProblem
from unified_planning.model.mixins import (
    ActionsSetMixin,
    TimeModelMixin,
    FluentsSetMixin,
    ObjectsSetMixin,
    UserTypesSetMixin,
    InitialStateMixin,
    MetricsMixin,
)
from unified_planning.model.expression import ConstantExpression
from unified_planning.model.operators import OperatorKind
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.model.types import _IntType
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPTypeError,
    UPUsageError,
    UPNoSuitableEngineAvailableException,
    UPUnsupportedProblemTypeError,
)

import networkx as nx
from fractions import Fraction
from typing import Any, Optional, List, Dict, Set, Tuple, Union, cast, Iterable


class Problem(  # type: ignore[misc]
    AbstractProblem,
    UserTypesSetMixin,
    TimeModelMixin,
    FluentsSetMixin,
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
        ActionsSetMixin.__init__(
            self, self.environment, self._add_user_type, self.has_name
        )
        ObjectsSetMixin.__init__(
            self, self.environment, self._add_user_type, self.has_name
        )
        InitialStateMixin.__init__(self, self, self, self.environment)
        MetricsMixin.__init__(self, self.environment)

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
        :return: `True` if the given `name` is already in the `Problem`, `False` otherwise.
        """
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

            elif isinstance(a, up.model.transition.Event): 
                # NOTE copypaste of above, with mixin should become one single block
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
            elif isinstance(a, up.model.transition.Process):
                for e in a.effects:
                    remove_used_fluents(e.fluent, e.value, e.condition)
                    static_fluents.discard(e.fluent.fluent())
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

    def get_unused_fluents(self) -> Set["up.model.fluent.Fluent"]:
        """
        Returns the set of `fluents` that are never used in the problem.
        """
        return self._get_static_and_unused_fluents()[1]

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
        if (interval.lower.is_from_end() and interval.lower.delay != 0) or (
            interval.upper.is_from_end() and interval.upper.delay != 0
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
        forall: Iterable["up.model.variable.Variable"] = tuple(),
    ):
        """
        Adds the given `timed effect` to the `Problem`; a `timed effect` is an :class:`~unified_planning.model.Effect` applied at a fixed time.

        :param timing: The exact time in which the given `Effect` is applied.
        :param fluent: The fluent modified by the `Effect`.
        :param value: The value assigned to the given `fluent` at the given `time`.
        :param condition: The condition that must be evaluated to `True` in order for this `Effect` to be
            actually applied.
        :param forall: The 'Variables' that are universally quantified in this
            effect; the default value is empty.
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
            timing,
            up.model.effect.Effect(fluent_exp, value_exp, condition_exp, forall=forall),
        )

    def add_increase_effect(
        self,
        timing: "up.model.timing.Timing",
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
        forall: Iterable["up.model.variable.Variable"] = tuple(),
    ):
        """
        Adds the given `timed increase effect` to the `Problem`; a `timed effect` is an :class:`~unified_planning.model.Effect` applied at a fixed time.

        :param timing: The exact time in which the given `Effect` is applied.
        :param fluent: The fluent increased by the `Effect`.
        :param value: The value of which the given `fluent` is increased at the given `time`.
        :param condition: The condition that must be evaluated to `True` in order for this `Effect` to be
            actually applied.
        :param forall: The 'Variables' that are universally quantified in this
            effect; the default value is empty.
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
                forall=forall,
            ),
        )

    def add_decrease_effect(
        self,
        timing: "up.model.timing.Timing",
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
        forall: Iterable["up.model.variable.Variable"] = tuple(),
    ):
        """
        Adds the given timed decrease effect to the problem; a `timed effect` is an :class:`~unified_planning.model.Effect` applied at a fixed time.

        :param timing: The exact time in which the given `Effect` is applied.
        :param fluent: The fluent decreased by the `Effect`.
        :param value: The value of which the given `fluent` is decrease at the given `time`.
        :param condition: The condition that must be evaluated to `True` in order for this `Effect` to be
            actually applied.
        :param forall: The 'Variables' that are universally quantified in this
            effect; the default value is empty.
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
                forall=forall,
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
    def state_invariants(self) -> List["up.model.fnode.FNode"]:
        """Returns the List of ``state_invariants`` in the problem."""
        em = self._env.expression_manager
        state_invariants = []
        for tc in self._trajectory_constraints:
            if tc.is_always():
                state_invariants.append(tc.arg(0))
            elif tc.is_and():
                for a in tc.args:
                    if a.is_always():
                        state_invariants.append(a.arg(0))
            elif tc.is_forall() and tc.arg(0).is_always():
                state_invariants.append(em.Forall(tc.arg(0).arg(0), *tc.variables()))
        return state_invariants

    def add_state_invariant(self, invariant: "up.model.expression.BoolExpression"):
        """
        Adds the given ``invariant`` to the problem's state invariants.
        State invariants are added as ``Always`` trajectory constraints.

        :param invariant: The invariant expression to add to this problem as a state invariant.
        """
        self.add_trajectory_constraint(self._env.expression_manager.Always(invariant))

    def _kind_factory(self) -> "_KindFactory":
        """Returns an intermediate view for the kind computation.
        Subclasses can use the result of this method to update the kind"""
        factory = _KindFactory(
            self,
            problem_class="ACTION_BASED",
            environment=self._env,
        )

        for action in self._actions:
            factory.update_problem_kind_action(action)
        if len(self._timed_effects) > 0:
            factory.kind.set_time("CONTINUOUS_TIME")
            factory.kind.set_time("TIMED_EFFECTS")
        for effect in chain(*self._timed_effects.values()):
            factory.update_problem_kind_effect(effect)
        if len(self._timed_goals) > 0:
            factory.kind.set_time("TIMED_GOALS")
            factory.kind.set_time("CONTINUOUS_TIME")
        for tc in self._trajectory_constraints:
            if tc.is_always():
                factory.kind.set_constraints_kind("STATE_INVARIANTS")
            else:
                factory.kind.set_constraints_kind("TRAJECTORY_CONSTRAINTS")
        for goal in chain(*self._timed_goals.values(), self._goals):
            factory.update_problem_kind_expression(goal)
        factory.update_problem_kind_initial_state(self)
        if len(list(self.processes)) > 0:
            factory.kind.set_time("PROCESSES")

        return factory

    @property
    def kind(self) -> "up.model.problem_kind.ProblemKind":
        """
        Calculates and returns the `problem kind` of this `planning problem`.
        If the `Problem` is modified, this method must be called again in order to be reliable.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible.
        """
        return self._kind_factory().finalize()


class _KindFactory:
    """Utility class to help analyze the kind of `AbstractProblem` subclass."""

    def __init__(
        self,
        pb: AbstractProblem,
        problem_class: str,
        environment: "unified_planning.Environment",
    ):
        assert isinstance(pb, MetricsMixin)
        assert isinstance(pb, FluentsSetMixin)
        assert isinstance(pb, ObjectsSetMixin)
        assert isinstance(pb, UserTypesSetMixin)
        assert isinstance(pb, TimeModelMixin)

        # WARNING: self.pb may in fact be any subclass of AbstractProblem that has the above mixins.
        # We declare it as a Problem to avoid limitations of the python type system
        self.pb: up.model.Problem = pb
        self.static_fluents: Set[Fluent] = pb.get_static_fluents()
        self.unused_fluents: Set[Fluent] = pb.get_unused_fluents()

        self.environment: unified_planning.Environment = environment
        self.kind: up.model.ProblemKind = up.model.ProblemKind(
            version=LATEST_PROBLEM_KIND_VERSION
        )

        self.kind.set_problem_class(problem_class)

        # set optimistically and remove if we encounter a counter example
        self.kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")

        # Create a simplifier and a linear_checker with the problem, so static fluents can be considered as constants
        self.simplifier: up.model.walkers.simplifier.Simplifier = (
            up.model.walkers.simplifier.Simplifier(self.environment, self.pb)
        )
        self.linear_checker: up.model.walkers.linear_checker.LinearChecker = (
            up.model.walkers.linear_checker.LinearChecker(self.pb, self.environment)
        )
        self.operators_extractor: up.model.walkers.OperatorsExtractor = (
            up.model.walkers.OperatorsExtractor()
        )

        (
            fluents_to_only_increase,
            fluents_to_only_decrease,
        ) = self.update_problem_kind_metric()
        # fluents that can only be increased (resp. decreased) for the problem to be SIMPLE_NUMERIC_PLANNING
        self.fluents_to_only_increase: Set[Fluent] = fluents_to_only_increase
        self.fluents_to_only_decrease: Set[Fluent] = fluents_to_only_decrease

        for fluent in self.pb.fluents:
            self.update_problem_kind_fluent(fluent)
        for object in self.pb.all_objects:
            self.update_problem_kind_type(object.type)

    def finalize(self) -> "up.model.ProblemKind":
        """Once all features have been added, remove unnecessary features that were added preventively."""
        if not self.kind.has_real_fluents() and not self.kind.has_int_fluents():
            self.kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
        elif not self.kind.has_simple_numeric_planning():
            self.kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        if self.kind.has_continuous_time() and self.pb.discrete_time:
            self.kind.set_time("DISCRETE_TIME")
            self.kind.unset_time("CONTINUOUS_TIME")
        if self.pb.self_overlapping and (
            self.kind.has_continuous_time() or self.kind.has_discrete_time()
        ):
            self.kind.set_time("SELF_OVERLAPPING")
        return self.kind

    def update_problem_kind_type(self, type: "up.model.types.Type"):
        if type.is_user_type():
            self.kind.set_typing("FLAT_TYPING")
            if cast(up.model.types._UserType, type).father is not None:
                self.kind.set_typing("HIERARCHICAL_TYPING")

    def update_problem_kind_effect(
        self,
        e: "up.model.effect.Effect",
    ):
        value = self.simplifier.simplify(e.value)
        fluents_in_value = self.environment.free_vars_extractor.get(value)
        if e.is_conditional():
            self.update_problem_kind_expression(e.condition)
            self.kind.set_effects_kind("CONDITIONAL_EFFECTS")
            t = e.fluent.type
            if t.is_int_type() or t.is_real_type():
                self.kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
        if e.is_forall():
            self.kind.set_effects_kind("FORALL_EFFECTS")
        if e.is_increase():
            self.kind.set_effects_kind("INCREASE_EFFECTS")
            # If the value is a number (int or real) and it violates the constraint
            # on the "fluents_to_only_increase" or on "fluents_to_only_decrease",
            # unset simple_numeric_planning
            if (  # value is a constant number
                value.is_int_constant() or value.is_real_constant()
            ):
                if (
                    e.fluent in self.fluents_to_only_increase
                    and value.constant_value() < 0
                ) or (
                    e.fluent in self.fluents_to_only_decrease
                    and value.constant_value() > 0
                ):
                    self.kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
            else:
                self.kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
                if any(f in self.static_fluents for f in fluents_in_value):
                    self.kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
                if any(f not in self.static_fluents for f in fluents_in_value):
                    self.kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        elif e.is_decrease():
            self.kind.set_effects_kind("DECREASE_EFFECTS")
            # If the value is a number (int or real) and it violates the constraint
            # on the "fluents_to_only_increase" or on "fluents_to_only_decrease",
            # unset simple_numeric_planning
            if (  # value is a constant number
                value.is_int_constant() or value.is_real_constant()
            ):
                if (
                    e.fluent in self.fluents_to_only_increase
                    and value.constant_value() > 0
                ) or (
                    e.fluent in self.fluents_to_only_decrease
                    and value.constant_value() < 0
                ):
                    self.kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
            else:
                self.kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
                if any(f in self.static_fluents for f in fluents_in_value):
                    self.kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
                if any(f not in self.static_fluents for f in fluents_in_value):
                    self.kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        elif e.is_assignment():
            value_type = value.type
            if (
                value_type.is_int_type() or value_type.is_real_type()
            ):  # the value is a number
                if (  # if the fluent has increase/decrease constraints or the value assigned is not a constant,
                    # unset "SIMPLE_NUMERIC_PLANNING"
                    e.fluent in self.fluents_to_only_increase
                    or e.fluent in self.fluents_to_only_decrease
                    or not value.is_constant()
                ):
                    self.kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
                if any(f in self.static_fluents for f in fluents_in_value):
                    self.kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
                if any(f not in self.static_fluents for f in fluents_in_value):
                    self.kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
            elif value.type.is_bool_type():
                if any(f in self.static_fluents for f in fluents_in_value):
                    self.kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
                if any(f not in self.static_fluents for f in fluents_in_value):
                    self.kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
            elif value.type.is_user_type():
                if any(f in self.static_fluents for f in fluents_in_value):
                    self.kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
                if any(f not in self.static_fluents for f in fluents_in_value):
                    self.kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")

    def update_problem_kind_expression(
        self,
        exp: "up.model.fnode.FNode",
    ):
        ops = self.operators_extractor.get(exp)
        if OperatorKind.EQUALS in ops:
            self.kind.set_conditions_kind("EQUALITIES")
        if OperatorKind.NOT in ops:
            self.kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        if OperatorKind.OR in ops or OperatorKind.IMPLIES in ops:
            self.kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        if OperatorKind.EXISTS in ops:
            self.kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        if OperatorKind.FORALL in ops:
            self.kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        is_linear, _, _ = self.linear_checker.get_fluents(exp)
        if not is_linear:
            self.kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")

    def update_problem_kind_fluent(
        self,
        fluent: "up.model.fluent.Fluent",
    ):
        type = fluent.type
        if fluent not in self.unused_fluents or (
            not type.is_int_type() and not type.is_real_type()
        ):
            self.update_problem_kind_type(type)
        if type.is_int_type() or type.is_real_type():
            numeric_type = type
            assert isinstance(
                numeric_type, (up.model.types._RealType, up.model.types._IntType)
            )
            if (
                numeric_type.lower_bound is not None
                or numeric_type.upper_bound is not None
            ):
                self.kind.set_numbers("BOUNDED_TYPES")
            if fluent not in self.unused_fluents:
                if type.is_int_type():
                    self.kind.set_fluents_type("INT_FLUENTS")
                else:
                    assert type.is_real_type()
                    self.kind.set_fluents_type("REAL_FLUENTS")
        elif type.is_user_type():
            self.kind.set_fluents_type("OBJECT_FLUENTS")
        for param in fluent.signature:
            pt = param.type
            self.update_problem_kind_type(pt)
            if pt.is_bool_type():
                self.kind.set_parameters("BOOL_FLUENT_PARAMETERS")
            elif pt.is_int_type():
                self.kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")

    def update_action_parameter(self, param: "up.model.Parameter"):
        pt = param.type
        self.update_problem_kind_type(pt)
        if pt.is_bool_type():
            self.kind.set_parameters("BOOL_ACTION_PARAMETERS")
        elif pt.is_real_type():
            self.kind.set_parameters("REAL_ACTION_PARAMETERS")
        elif pt.is_int_type():
            if (
                cast(_IntType, pt).lower_bound is None
                or cast(_IntType, pt).upper_bound is None
            ):
                self.kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
            else:
                self.kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")

    def update_action_duration(self, duration: "up.model.DurationInterval"):
        lower, upper = duration.lower, duration.upper
        for dur_bound in (lower, upper):
            if dur_bound.type.is_int_type():
                self.kind.set_expression_duration("INT_TYPE_DURATIONS")
            else:
                assert dur_bound.type.is_real_type()
                self.kind.set_expression_duration("REAL_TYPE_DURATIONS")

        if lower != upper:
            self.kind.set_time("DURATION_INEQUALITIES")
        free_vars = self.environment.free_vars_extractor.get(
            lower
        ) | self.environment.free_vars_extractor.get(upper)
        if len(free_vars) > 0:
            only_static = True
            for fv in free_vars:
                if fv.fluent() not in self.static_fluents:
                    only_static = False
                    break
            if only_static:
                self.kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
            else:
                self.kind.set_expression_duration("FLUENTS_IN_DURATIONS")

    def update_action_timed_condition(
        self, span: "up.model.TimeInterval", cond: "up.model.FNode"
    ):
        if span.lower.delay != 0 or span.upper.delay != 0:
            for t in [span.lower, span.upper]:
                if (t.is_from_start() and t.delay > 0) or (
                    t.is_from_end() and t.delay < 0
                ):
                    self.kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
                else:
                    self.kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        self.update_problem_kind_expression(cond)

    def update_action_timed_effect(self, t: "up.model.Timing", eff: "up.model.Effect"):
        if t.delay != 0:
            if (t.is_from_start() and t.delay > 0) or (t.is_from_end() and t.delay < 0):
                self.kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
            else:
                self.kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        self.update_problem_kind_effect(eff)

    def update_problem_kind_action(
        self,
        action: "up.model.action.Action",
    ):
        for param in action.parameters:
            self.update_action_parameter(param)
        if isinstance(action, up.model.action.SensingAction):
            self.kind.set_problem_class("CONTINGENT")
        if isinstance(action, up.model.tamp.InstantaneousMotionAction):
            if len(action.motion_constraints) > 0:
                self.kind.set_problem_class("TAMP")
        if isinstance(action, up.model.action.InstantaneousAction):
            for c in action.preconditions:
                self.update_problem_kind_expression(c)
            for e in action.effects:
                self.update_problem_kind_effect(e)
            if action.simulated_effect is not None:
                self.kind.set_simulated_entities("SIMULATED_EFFECTS")
        elif isinstance(action, up.model.action.DurativeAction):
            self.update_action_duration(action.duration)
            for i, lc in action.conditions.items():
                for c in lc:
                    self.update_action_timed_condition(i, c)
            for t, le in action.effects.items():
                for e in le:
                    self.update_action_timed_effect(t, e)
            if len(action.simulated_effects) > 0:
                self.kind.set_simulated_entities("SIMULATED_EFFECTS")
            self.kind.set_time("CONTINUOUS_TIME")
        elif isinstance(action, up.model.transition.Process):
            pass # TODO add Process kind
        elif isinstance(action, up.model.transition.Event):
            pass # TODO add Event kind
        else:
            raise NotImplementedError

    def update_problem_kind_metric(
        self,
    ) -> Tuple[Set["up.model.Fluent"], Set["up.model.Fluent"]]:
        """Updates the kind object passed as parameter to account for given metrics.
        Return a pair for fluent sets that should respectively be only increased/decreased
        (necessary for checking numeric problem kind properties).
        """
        fluents_to_only_increase = set()
        fluents_to_only_decrease = set()
        fve = self.pb.environment.free_vars_extractor
        for metric in self.pb.quality_metrics:
            oversub_gains: Iterable[Any] = []
            oversub_goals: Iterable["up.model.fnode.FNode"] = []
            if metric.is_minimize_expression_on_final_state():
                assert isinstance(
                    metric, up.model.metrics.MinimizeExpressionOnFinalState
                )
                self.kind.set_quality_metrics("FINAL_VALUE")
                self.update_problem_kind_expression(metric.expression)
                (
                    is_linear,
                    fnode_to_only_increase,  # positive fluents in minimize can only be increased
                    fnode_to_only_decrease,  # negative fluents in minimize can only be decreased
                ) = self.linear_checker.get_fluents(metric.expression)
                if is_linear:
                    fluents_to_only_increase = {
                        e.fluent() for e in fnode_to_only_increase
                    }
                    fluents_to_only_decrease = {
                        e.fluent() for e in fnode_to_only_decrease
                    }
                else:
                    self.kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
            elif metric.is_maximize_expression_on_final_state():
                assert isinstance(
                    metric, up.model.metrics.MaximizeExpressionOnFinalState
                )
                self.kind.set_quality_metrics("FINAL_VALUE")
                self.update_problem_kind_expression(metric.expression)
                (
                    is_linear,
                    fnode_to_only_decrease,  # positive fluents in maximize can only be decreased
                    fnode_to_only_increase,  # negative fluents in maximize can only be increased
                ) = self.linear_checker.get_fluents(metric.expression)
                if is_linear:
                    fluents_to_only_increase = {
                        e.fluent() for e in fnode_to_only_increase
                    }
                    fluents_to_only_decrease = {
                        e.fluent() for e in fnode_to_only_decrease
                    }
                else:
                    self.kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
            elif metric.is_minimize_action_costs():
                assert isinstance(metric, up.model.metrics.MinimizeActionCosts)
                self.kind.set_quality_metrics("ACTIONS_COST")
                costs = list(metric.costs.values())
                if metric.default is not None:
                    costs.append(metric.default)
                for cost in costs:
                    if cost is None:
                        raise UPProblemDefinitionError(
                            "The cost of an Action can't be None."
                        )
                    t = cost.type
                    if t.is_int_type():
                        self.kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
                    elif t.is_real_type():
                        self.kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
                    for f in fve.get(cost):
                        if f.fluent() in self.static_fluents:
                            self.kind.set_actions_cost_kind(
                                "STATIC_FLUENTS_IN_ACTIONS_COST"
                            )
                        else:
                            self.kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
            elif metric.is_minimize_makespan():
                self.kind.set_quality_metrics("MAKESPAN")
            elif metric.is_minimize_sequential_plan_length():
                self.kind.set_quality_metrics("PLAN_LENGTH")
            elif metric.is_oversubscription():
                assert isinstance(metric, up.model.Oversubscription)
                self.kind.set_quality_metrics("OVERSUBSCRIPTION")
                oversub_goals = metric.goals.keys()
                oversub_gains = metric.goals.values()
            elif metric.is_temporal_oversubscription():
                assert isinstance(metric, up.model.TemporalOversubscription)
                self.kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
                oversub_goals = map(lambda x: x[1], metric.goals.keys())
                oversub_gains = metric.goals.values()
            else:
                assert False, "Unknown quality metric"
            for goal in oversub_goals:
                self.update_problem_kind_expression(goal)
            for oversub_gain in oversub_gains:
                if isinstance(oversub_gain, int):
                    self.kind.set_oversubscription_kind(
                        "INT_NUMBERS_IN_OVERSUBSCRIPTION"
                    )
                else:
                    assert isinstance(
                        oversub_gain, Fraction
                    ), "Typing error in metric creation"
                    self.kind.set_oversubscription_kind(
                        "REAL_NUMBERS_IN_OVERSUBSCRIPTION"
                    )
        return fluents_to_only_increase, fluents_to_only_decrease

    def update_problem_kind_initial_state(self, init: InitialStateMixin):
        for fluent in init._fluents_with_undefined_values():
            if fluent.type.is_int_type() or fluent.type.is_real_type():
                self.kind.set_initial_state("UNDEFINED_INITIAL_NUMERIC")
            else:
                self.kind.set_initial_state("UNDEFINED_INITIAL_SYMBOLIC")


def generate_causal_graph(
    problem: Problem,
) -> Tuple[
    nx.DiGraph,
    Dict[
        Tuple["up.model.fnode.FNode", "up.model.fnode.FNode"],
        Set["up.plans.ActionInstance"],
    ],
]:
    """
    This method generates the causal graph of the given problem. The causal graph is a directed
    graph where the nodes are the fluents of the problem (instantiated to objects) and there is
    an edge from node A to node B if an action (instantiated to objects) reads/writes A and
    writes B. This means that somehow the A and B fluents are related trough that action.

    :param problem: The problem to compute the causal graph.
    :return: The tuple where the first element is the causal graph and the second element is the
        mapping from the pairs of nodes connected in the graph to the set of actions that link
        the first node to the second; every element of the set is composed by 2 elements, the
        first one is the lifted action, the second one is the tuple of parameters used to ground
        the action.
    """
    if isinstance(
        problem, (up.model.htn.HierarchicalProblem, up.model.ContingentProblem)
    ):
        raise NotImplementedError
    assert type(problem) == Problem, "Error not handled."

    if not problem.actions:
        raise UPUsageError("Can't create the causal graph of a Problem without actions")
    to_ground = any(a.parameters for a in problem.actions)
    actions_mapping: Dict[
        "up.model.action.Action",
        Tuple["up.model.action.Action", Tuple["up.model.fnode.FNode", ...]],
    ] = {}
    grounded_problem = problem
    if to_ground:
        try:
            with problem.environment.factory.Compiler(
                problem_kind=problem.kind, compilation_kind="GROUNDING"
            ) as grounder:
                res = grounder.compile(problem)
                grounded_problem = res.problem
                ai_mapping = res.map_back_action_instance
                for ga in grounded_problem.actions:
                    lifted_ai = ai_mapping(ga())
                    actions_mapping[ga] = (
                        lifted_ai.action,
                        lifted_ai.actual_parameters,
                    )
        except UPNoSuitableEngineAvailableException as ex:
            raise UPUsageError(
                "To plot the causal graph of a problem, the problem must be grounded or a grounder capable of handling the given problem must be installed.\n"
                + str(ex)
            )

    # Populate 2 maps:
    #  one from a fluent to all the actions reading that fluent
    #  one from a fluent to all the actions writing that fluent
    fluents_red: Dict["up.model.fnode.FNode", Set["up.model.action.Action"]] = {}
    fluents_written: Dict["up.model.fnode.FNode", Set["up.model.action.Action"]] = {}

    fve = problem.environment.free_vars_extractor
    for action in grounded_problem.actions:
        assert not action.parameters
        if isinstance(action, up.model.action.InstantaneousAction):
            for p in action.preconditions:
                for fluent in fve.get(p):
                    if any(map(fve.get, fluent.args)):
                        raise UPUnsupportedProblemTypeError(
                            f"Fluent {fluent} contains other fluents. Causal Graph can't be generated with nested fluents."
                        )
                    fluents_red.setdefault(fluent, set()).add(action)
            for e in action.effects:
                fluent = e.fluent
                assert fluent.is_fluent_exp()
                assert not any(map(fve.get, fluent.args)), "Error in effect definition"
                fluents_written.setdefault(fluent, set()).add(action)
                for fluent in chain(fve.get(e.value), fve.get(e.condition)):
                    if any(map(fve.get, fluent.args)):
                        raise NotImplementedError(
                            "nested fluents still are not implemented"
                        )
                    fluents_red.setdefault(fluent, set()).add(action)
        elif isinstance(action, up.model.action.DurativeAction):
            for p in chain(*action.conditions.values()):
                for fluent in fve.get(p):
                    if any(map(fve.get, fluent.args)):
                        raise UPUnsupportedProblemTypeError(
                            f"Fluent {fluent} contains other fluents. Causal Graph can't be generated with nested fluents."
                        )
                    fluents_red.setdefault(fluent, set()).add(action)
            for e in chain(*action.effects.values()):
                fluent = e.fluent
                assert fluent.is_fluent_exp()
                if any(map(fve.get, fluent.args)):
                    raise NotImplementedError("nested fluents are not implemented")
                fluents_written.setdefault(fluent, set()).add(action)
                for fluent in chain(fve.get(e.value), fve.get(e.condition)):
                    if any(map(fve.get, fluent.args)):
                        raise NotImplementedError("nested fluents are not implemented")
                    fluents_red.setdefault(fluent, set()).add(action)
        else:
            raise NotImplementedError
    edge_actions_map: Dict[
        Tuple["up.model.fnode.FNode", "up.model.fnode.FNode"],
        Set["up.plans.ActionInstance"],
    ] = {}
    graph = nx.DiGraph()
    all_fluents = set(chain(fluents_red.keys(), fluents_written.keys()))
    # Add an edge if a fluent that is red or written and it's in the same action of a written fluent
    empty_set: Set["up.model.fnode.FNode"] = set()
    for left_node, right_node in product(all_fluents, fluents_written.keys()):
        rn_actions = fluents_written.get(right_node, empty_set)
        if left_node != right_node and rn_actions:
            actions = edge_actions_map.setdefault((left_node, right_node), set())
            edge_created = False
            for ln_action in chain(
                fluents_red.get(left_node, empty_set),
                fluents_written.get(left_node, empty_set),
            ):
                assert isinstance(ln_action, up.model.Action)
                if ln_action in rn_actions:
                    if not edge_created:
                        edge_created = True
                        graph.add_edge(left_node, right_node)
                    actions.add(
                        up.plans.ActionInstance(
                            *actions_mapping.get(ln_action, (ln_action, tuple()))
                        )
                    )
    return graph, edge_actions_map
