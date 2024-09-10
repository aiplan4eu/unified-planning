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
"""This module defines different utility functions for the compilers."""


from fractions import Fraction
import unified_planning as up
from unified_planning.exceptions import UPConflictingEffectsException, UPUsageError
from unified_planning.environment import Environment
from unified_planning.model import (
    FNode,
    TimeInterval,
    Action,
    InstantaneousAction,
    DurativeAction,
    Problem,
    Effect,
    Expression,
    BoolExpression,
    NumericConstant,
    SimulatedEffect,
    Parameter,
    DurationInterval,
    TimePointInterval,
    PlanQualityMetric,
    MinimizeActionCosts,
    MinimizeExpressionOnFinalState,
    MaximizeExpressionOnFinalState,
    Oversubscription,
    TemporalOversubscription,
    AbstractProblem,
)
from unified_planning.plans import ActionInstance
from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    OrderedDict,
    Sequence,
    Tuple,
    Union,
    cast,
)


def check_and_simplify_conditions(
    problem: AbstractProblem, action: DurativeAction, simplifier
) -> Tuple[bool, List[Tuple[TimeInterval, FNode]]]:
    """
    Simplifies conditions and if it is False (a contraddiction)
    returns False, otherwise returns True.
    If the simplification is True (a tautology) removes all conditions at the given timing.
    If the simplification is still an AND rewrites back every "arg" of the AND
    in the conditions
    If the simplification is not an AND sets the simplification as the only
    condition at the given timing.
    Then, the new conditions are returned as a List[Tuple[Timing, FNode]] and the user can
    decide how to use the new conditions.
    """
    # new action conditions
    nac: List[Tuple[TimeInterval, FNode]] = []
    # i = interval, lc = list condition
    for i, lc in action.conditions.items():
        # conditions (as an And FNode)
        c = problem.environment.expression_manager.And(lc)
        # conditions simplified
        cs = simplifier.simplify(c)
        if cs.is_bool_constant():
            if not cs.bool_constant_value():
                return (
                    False,
                    [],
                )
        else:
            if cs.is_and():
                for new_cond in cs.args:
                    nac.append((i, new_cond))
            else:
                nac.append((i, cs))
    return (True, nac)


def check_and_simplify_preconditions(
    problem: AbstractProblem, action: InstantaneousAction, simplifier
) -> Tuple[bool, List[FNode]]:
    """
    Simplifies preconditions and if it is False (a contraddiction)
    returns False, otherwise returns True.
    If the simplification is True (a tautology) removes all preconditions.
    If the simplification is still an AND rewrites back every "arg" of the AND
    in the preconditions
    If the simplification is not an AND sets the simplification as the only
    precondition.
    Then, the new preconditions are returned as a List[FNode] and the user can
    decide how to use the new preconditions.
    """
    # action preconditions
    ap = action.preconditions
    if len(ap) == 0:
        return (True, [])
    # preconditions (as an And FNode)
    p = problem.environment.expression_manager.And(ap)
    # preconditions simplified
    ps = simplifier.simplify(p)
    # new action preconditions
    nap: List[FNode] = []
    if ps.is_bool_constant():
        if not ps.bool_constant_value():
            return (False, [])
    else:
        if ps.is_and():
            nap.extend(ps.args)
        else:
            nap.append(ps)
    action._set_preconditions(nap)
    return (True, nap)


def create_effect_with_given_subs(
    problem: Problem,
    old_effect: Effect,
    simplifier,
    subs: Dict[Expression, Expression],
) -> Optional[Effect]:
    new_fluent = old_effect.fluent.substitute(subs)
    new_value = old_effect.value.substitute(subs)
    new_condition = simplifier.simplify(old_effect.condition.substitute(subs))
    if new_condition == problem.environment.expression_manager.FALSE():
        return None
    else:
        return Effect(
            new_fluent, new_value, new_condition, old_effect.kind, old_effect.forall
        )


def create_action_with_given_subs(
    problem: Problem,
    old_action: Action,
    simplifier,
    subs: Dict[Expression, Expression],
) -> Optional[Action]:
    """This method is used to instantiate the actions parameters to a constant."""
    naming_list: List[str] = []
    for param, value in subs.items():
        assert isinstance(param, Parameter)
        assert isinstance(value, FNode)
        naming_list.append(str(value))
    c_subs = cast(Dict[Parameter, FNode], subs)
    if isinstance(old_action, InstantaneousAction):
        new_action = InstantaneousAction(
            get_fresh_name(problem, old_action.name, naming_list)
        )
        for p in old_action.preconditions:
            new_action.add_precondition(p.substitute(subs))
        for e in old_action.effects:
            new_effect = create_effect_with_given_subs(problem, e, simplifier, subs)
            if new_effect is not None:
                # We try to add the new effect, but a compiler might generate conflicting effects,
                # so the action is just considered invalid
                try:
                    new_action._add_effect_instance(new_effect)
                except UPConflictingEffectsException:
                    return None
        se = old_action.simulated_effect
        if se is not None:
            new_fluents = []
            for f in se.fluents:
                new_fluents.append(f.substitute(subs))

            def fun(_problem, _state, _):
                assert se is not None
                return se.function(_problem, _state, c_subs)

            # We try to add the new simulated effect, but a compiler might generate conflicting effects,
            # so the action is just considered invalid
            try:
                new_action.set_simulated_effect(SimulatedEffect(new_fluents, fun))
            except UPConflictingEffectsException:
                return None
        is_feasible, new_preconditions = check_and_simplify_preconditions(
            problem, new_action, simplifier
        )
        if not is_feasible:
            return None
        new_action._set_preconditions(new_preconditions)
        return new_action
    elif isinstance(old_action, DurativeAction):
        new_durative_action = DurativeAction(
            get_fresh_name(problem, old_action.name, naming_list)
        )
        old_duration = old_action.duration
        new_duration = DurationInterval(
            old_duration.lower.substitute(subs),
            old_duration.upper.substitute(subs),
            old_duration.is_left_open(),
            old_duration.is_right_open(),
        )
        new_durative_action.set_duration_constraint(new_duration)
        for i, cl in old_action.conditions.items():
            for c in cl:
                new_durative_action.add_condition(i, c.substitute(subs))
        for t, el in old_action.effects.items():
            for e in el:
                new_effect = create_effect_with_given_subs(problem, e, simplifier, subs)
                if new_effect is not None:
                    # We try to add the new simulated effect, but a compiler might generate conflicting effects,
                    # so the action is just considered invalid
                    try:
                        new_durative_action._add_effect_instance(t, new_effect)
                    except UPConflictingEffectsException:
                        return None
        for t, se in old_action.simulated_effects.items():
            new_fluents = []
            for f in se.fluents:
                new_fluents.append(f.substitute(subs))

            def fun(_problem, _state, _):
                assert se is not None
                return se.function(_problem, _state, c_subs)

            # We try to add the new simulated effect, but a compiler might generate conflicting effects,
            # so the action is just considered invalid
            try:
                new_durative_action.set_simulated_effect(
                    t, SimulatedEffect(new_fluents, fun)
                )
            except UPConflictingEffectsException:
                return None
        is_feasible, new_conditions = check_and_simplify_conditions(
            problem, new_durative_action, simplifier
        )
        if not is_feasible:
            return None
        new_durative_action.clear_conditions()
        for interval, c in new_conditions:
            new_durative_action.add_condition(interval, c)
        return new_durative_action
    else:
        raise NotImplementedError


def get_fresh_name(
    problem: AbstractProblem,
    original_name: str,
    parameters_names: Sequence[str] = tuple(),
) -> str:
    """This method returns a fresh name for the problem, given a name and an iterable of names in input."""
    name_list = [original_name]
    name_list.extend(parameters_names)
    new_name = "_".join(name_list)
    base_name = new_name
    count = 0
    while problem.has_name(new_name):
        new_name = f"{base_name}_{str(count)}"
        count += 1
    return new_name


def lift_action_instance(
    action_instance: ActionInstance,
    map: Dict["up.model.Action", Tuple["up.model.Action", List["up.model.FNode"]]],
) -> ActionInstance:
    """ "map" is a map from every action in the "grounded_problem" to the tuple
    (original_action, parameters).

    Where the grounded action is obtained by grounding
    the "original_action" with the specific "parameters"."""
    lifted_action, parameters = map[action_instance.action]
    return ActionInstance(lifted_action, tuple(parameters))


def replace_action(
    action_instance: ActionInstance,
    map: Dict["up.model.Action", Optional["up.model.Action"]],
) -> Optional[ActionInstance]:
    try:
        replaced_action = map[action_instance.action]
    except KeyError:
        raise UPUsageError(
            "The Action of the given ActionInstance does not have a valid replacement."
        )
    if replaced_action is not None:
        return ActionInstance(
            replaced_action,
            action_instance.actual_parameters,
            action_instance.agent,
            action_instance.motion_paths,
        )
    else:
        return None


def add_invariant_condition_apply_function_to_problem_expressions(
    original_problem: Problem,
    new_problem: Problem,
    condition: Optional[FNode] = None,
    function: Optional[Callable[[FNode], FNode]] = None,
) -> Dict[Action, Optional[Action]]:
    """
    This function takes the original problem, the new problem and adds to the new problem
    all the fields that involve an expression, applying the given function (the identity if it is None)
    to all expressions in the problem and adding the condition as an invariant for the whole problem;
    adding it as a final goal and as a precondition for every action. For the temporal case,
    whenever there is the possibility that a point in time is relevant, the condition is also added there.

    NOTE: The new_problem field will be modified!

    :param original_problem: The Problem acting as a base that will be modified in the new problem.
    :param new_problem: The problem created from the original problem; outside of this function the name,
        the fluents and the objects must be manually added.
    :param condition: Optionally, the condition to add in every relevant point of the Problem, making
        it de-facto an invariant.
    :param function: Optionally, the function that will be called and that creates every expression of the
        new problem.
    :return: The mapping from the actions of the new problem to the actions of the original problem;
        every action is mapped to the action it was generated from.
    """
    env = new_problem.environment
    em = env.expression_manager
    if condition is None:
        condition = em.TRUE()
    assert condition is not None
    if function is None:
        function = lambda x: x
    new_to_old: Dict[Action, Optional[Action]] = {}

    for constraint in original_problem.trajectory_constraints:
        new_problem.add_trajectory_constraint(function(constraint))

    for original_action in original_problem.actions:
        params = OrderedDict(((p.name, p.type) for p in original_action.parameters))
        if isinstance(original_action, InstantaneousAction):
            new_action: Union[
                InstantaneousAction, DurativeAction
            ] = InstantaneousAction(original_action.name, params, env)
            assert isinstance(new_action, InstantaneousAction)
            new_cond = em.And(
                *map(function, original_action.preconditions), condition
            ).simplify()
            if new_cond.is_false():
                continue
            elif new_cond.is_and():
                for arg in new_cond.args:
                    new_action.add_precondition(arg)
            else:
                new_action.add_precondition(new_cond)
            for effect in original_action.effects:
                new_action._add_effect_instance(
                    _apply_function_to_effect(effect, function)
                )
        elif isinstance(original_action, DurativeAction):
            new_action = DurativeAction(original_action.name, params, env)
            assert isinstance(new_action, DurativeAction)
            old_duration = original_action.duration
            new_duration = DurationInterval(
                function(old_duration.lower),
                function(old_duration.upper),
                old_duration.is_left_open(),
                old_duration.is_right_open(),
            )
            new_action.set_duration_constraint(new_duration)
            for interval, cond_list in original_action.conditions.items():
                new_cond = em.And(*map(function, cond_list), condition).simplify()
                if new_cond.is_false():
                    continue
                elif new_cond.is_and():
                    for arg in new_cond.args:
                        new_action.add_condition(interval, arg)
                else:
                    new_action.add_condition(interval, new_cond)
            for timing, effects in original_action.effects.items():
                for effect in effects:
                    new_action._add_effect_instance(
                        timing, _apply_function_to_effect(effect, function)
                    )
                interval = TimePointInterval(timing)
                if interval not in new_action.conditions:
                    new_action.add_condition(interval, condition)
        else:
            raise NotImplementedError
        new_problem.add_action(new_action)
        new_to_old[new_action] = original_action

    for interval, goal_list in original_problem.timed_goals.items():
        new_goal = em.And(*map(function, goal_list), condition).simplify()
        if new_goal.is_and():
            for arg in new_goal.args:
                new_problem.add_timed_goal(interval, arg)
        else:
            new_problem.add_timed_goal(interval, new_goal)
    for timing, effects in original_problem.timed_effects.items():
        for effect in effects:
            new_problem._add_effect_instance(
                timing, _apply_function_to_effect(effect, function)
            )
        interval = TimePointInterval(timing)
        if interval not in new_problem.timed_goals:
            new_problem.add_timed_goal(interval, condition)

    new_goal = em.And(*map(function, original_problem.goals), condition).simplify()
    if new_goal.is_and():
        for arg in new_goal.args:
            new_problem.add_goal(arg)
    else:
        new_problem.add_goal(new_goal)

    for qm in original_problem.quality_metrics:
        if qm.is_minimize_action_costs():
            assert isinstance(qm, MinimizeActionCosts)
            new_costs: Dict["up.model.Action", "up.model.Expression"] = {}
            for new_a, old_a in new_to_old.items():
                if old_a is None:
                    continue
                cost = qm.get_action_cost(old_a)
                if cost is not None:
                    cost = function(cost)
                    new_costs[new_a] = cost
            new_qm: PlanQualityMetric = MinimizeActionCosts(
                new_costs, environment=new_problem.environment
            )
        elif qm.is_minimize_expression_on_final_state():
            assert isinstance(qm, MinimizeExpressionOnFinalState)
            new_qm = MinimizeExpressionOnFinalState(
                function(qm.expression), environment=new_problem.environment
            )
        elif qm.is_maximize_expression_on_final_state():
            assert isinstance(qm, MaximizeExpressionOnFinalState)
            new_qm = MaximizeExpressionOnFinalState(
                function(qm.expression), environment=new_problem.environment
            )
        elif qm.is_oversubscription():
            assert isinstance(qm, Oversubscription)
            new_goals: Dict[BoolExpression, NumericConstant] = {}
            for goal, gain in qm.goals.items():
                new_goal = function(em.And(goal, condition).simplify())
                new_goals[new_goal] = (
                    cast(Union[int, Fraction], new_goals.get(new_goal, 0)) + gain
                )
            new_qm = Oversubscription(new_goals, environment=new_problem.environment)
        elif qm.is_temporal_oversubscription():
            assert isinstance(qm, TemporalOversubscription)
            new_temporal_goals: Dict[
                Tuple["up.model.timing.TimeInterval", "up.model.BoolExpression"],
                NumericConstant,
            ] = {}
            for (interval, goal), gain in qm.goals.items():
                new_goal = function(em.And(goal, condition).simplify())
                new_temporal_goals[(interval, new_goal)] = (
                    cast(
                        Union[int, Fraction],
                        new_temporal_goals.get((interval, new_goal), 0),
                    )
                    + gain
                )
            new_qm = TemporalOversubscription(
                new_temporal_goals, environment=new_problem.environment
            )
        else:
            new_qm = qm
        new_problem.add_quality_metric(new_qm)

    for fluent, value in original_problem.initial_values.items():
        new_problem.set_initial_value(function(fluent), function(value))

    return new_to_old


def _apply_function_to_effect(
    effect: Effect, function: Callable[[FNode], FNode]
) -> Effect:
    auto_promote = effect.environment.expression_manager.auto_promote
    return Effect(
        function(effect.fluent),
        function(effect.value),
        function(effect.condition),
        effect.kind,
        tuple((exp.variable() for exp in auto_promote(effect.forall))),
    )


def updated_minimize_action_costs(
    quality_metric: PlanQualityMetric,
    new_to_old: Union[Dict[Action, Action], Dict[Action, Optional[Action]]],
    environment: Environment,
):
    """
    This method takes a `MinimizeActionCosts` `PlanQualityMetric`, a mapping from the new
    action introduced by the compiler to the old action of the problem (None if the
    new action) does not have a counterpart in the original problem) and returns the
    updated equivalent metric for the new problem. This simply changes the costs keys
    and does not alter the cost expression, so it does not cover use-cases like grounding.

    :param quality_metric: The `MinimizeActionCosts`metric to update.
    :param new_to_old: The action's mapping from the compiled problem to the original problem.
    :param environment: The environment of the new problem (therefore, also of the new actions).
    """
    assert isinstance(quality_metric, MinimizeActionCosts)
    new_costs: Dict["up.model.Action", "up.model.Expression"] = {}
    for new_act, old_act in new_to_old.items():
        if old_act is not None:
            new_cost = quality_metric.get_action_cost(old_act)
            if new_cost is not None:
                new_costs[new_act] = new_cost
        else:
            new_costs[new_act] = environment.expression_manager.Int(0)
    return MinimizeActionCosts(new_costs, environment=environment)
