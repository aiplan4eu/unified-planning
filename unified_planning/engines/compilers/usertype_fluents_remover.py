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
"""This module defines the conditional effects remover class."""


from fractions import Fraction
from itertools import product
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    Problem,
    ProblemKind,
    Fluent,
    Parameter,
    BoolExpression,
    NumericConstant,
    Action,
    InstantaneousAction,
    DurativeAction,
    Effect,
    SimulatedEffect,
    FNode,
    ExpressionManager,
    MinimizeActionCosts,
    MinimizeExpressionOnFinalState,
    MaximizeExpressionOnFinalState,
    Oversubscription,
    TemporalOversubscription,
    Object,
    Expression,
    DurationInterval,
    UPState,
)
from unified_planning.model.walkers import UsertypeFluentsWalker
from unified_planning.model.types import _UserType
from unified_planning.engines.compilers.utils import replace_action
from unified_planning.model.fluent import get_all_fluent_exp
from typing import Iterator, Dict, List, OrderedDict, Set, Tuple, Optional, Union, cast
from functools import partial


class UsertypeFluentsRemover(engines.engine.Engine, CompilerMixin):
    """
    This class offers the capability to remove usertype fluents from the Problem.

    This is done by substituting them with a boolean fluent that takes the usertype
    object as a parameter and return True if the original fluent would have returned
    the object, False otherwise.

    This `Compiler` supports only the the `USERTYPE_FLUENTS_REMOVING` :class:`~unified_planning.engines.CompilationKind`.
    """

    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.USERTYPE_FLUENTS_REMOVING)

    @property
    def name(self):
        return "utfr"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("REAL_ACTION_PARAMETERS")
        supported_kind.set_numbers("CONTINUOUS_NUMBERS")
        supported_kind.set_numbers("DISCRETE_NUMBERS")
        supported_kind.set_numbers("BOUNDED_TYPES")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_fluents_type("NUMERIC_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECTS")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATIONS")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_constraints_kind("TRAJECTORY_CONSTRAINTS")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= UsertypeFluentsRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.USERTYPE_FLUENTS_REMOVING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = ProblemKind(problem_kind.features)
        if new_kind.has_fluents_type("OBJECT_FLUENTS"):
            new_kind.unset_fluents_type("OBJECT_FLUENTS")
            new_kind.set_effects_kind("CONDITIONAL_EFFECTS")
            new_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
            new_kind.set_conditions_kind("EQUALITIES")
            new_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """
        Takes an instance of a :class:`~unified_planning.model.Problem` and the wanted :class:`~unified_planning.engines.CompilationKind`
        and returns a :class:`~unified_planning.engines.results.CompilerResult` where the :meth:`problem<unified_planning.engines.results.CompilerResult.problem>` field does not have usertype fluents.

        :param problem: The instance of the :class:`~unified_planning.model.Problem` that must be returned without usertype fluents.
        :param compilation_kind: The :class:`~unified_planning.engines.CompilationKind` that must be applied on the given problem;
            only :class:`~unified_planning.engines.CompilationKind.USERTYPE_FLUENTS_REMOVING` is supported by this compiler
        :return: The resulting :class:`~unified_planning.engines.results.CompilerResult` data structure.
        """
        assert isinstance(problem, Problem)
        env = problem.environment
        tm = env.type_manager
        em = env.expression_manager

        new_to_old: Dict[Action, Action] = {}

        new_problem = Problem(f"{self.name}_{problem.name}", env)
        new_problem.add_objects(problem.all_objects)

        fluents_map: Dict[Fluent, Fluent] = {}
        for fluent in problem.fluents:
            assert isinstance(fluent, Fluent)
            if fluent.type.is_user_type():
                new_signature = fluent.signature[:]
                base_name = str(cast(_UserType, fluent.type).name).lower()
                new_param_name = base_name
                count = 0
                while any(p.name == new_param_name for p in new_signature):
                    new_param_name = f"{base_name}_{count}"
                    count += 1
                new_signature.append(Parameter(new_param_name, fluent.type, env))
                new_fluent = Fluent(fluent.name, tm.BoolType(), new_signature, env)
                fluents_map[fluent] = new_fluent
                new_problem.add_fluent(new_fluent)
            else:
                new_problem.add_fluent(fluent)

        used_names = self._get_names_in_problem(problem)
        utf_remover = UsertypeFluentsWalker(fluents_map, used_names, env)

        for old_action in problem.actions:
            params = OrderedDict(((p.name, p.type) for p in old_action.parameters))
            if isinstance(old_action, InstantaneousAction):
                new_action: Union[
                    InstantaneousAction, DurativeAction
                ] = InstantaneousAction(old_action.name, _parameters=params, _env=env)
                assert isinstance(new_action, InstantaneousAction)
                for p in old_action.preconditions:
                    new_action.add_precondition(
                        utf_remover.remove_usertype_fluents_from_condition(p)
                    )
                for e in old_action.effects:
                    for ne in self._convert_effect(
                        e, problem, fluents_map, em, utf_remover
                    ):
                        new_action._add_effect_instance(ne)
                if old_action.simulated_effect is not None:
                    new_action.set_simulated_effect(
                        self._convert_simulated_effect(
                            old_action.simulated_effect, fluents_map, em, problem
                        )
                    )
            elif isinstance(old_action, DurativeAction):
                new_action = DurativeAction(
                    old_action.name, _parameters=params, _env=env
                )
                assert isinstance(new_action, DurativeAction)
                for i, cl in old_action.conditions.items():
                    for c in cl:
                        new_action.add_condition(
                            i, utf_remover.remove_usertype_fluents_from_condition(c)
                        )
                for t, el in old_action.effects.items():
                    for e in el:
                        for ne in self._convert_effect(
                            e, problem, fluents_map, em, utf_remover
                        ):
                            new_action._add_effect_instance(t, ne)
                duration = old_action.duration
                new_duration = DurationInterval(
                    utf_remover.remove_usertype_fluents_from_condition(duration.lower),
                    utf_remover.remove_usertype_fluents_from_condition(duration.upper),
                    duration.is_left_open(),
                    duration.is_right_open(),
                )
                new_action.set_duration_constraint(new_duration)
                for t, se in old_action.simulated_effects.items():
                    new_action.set_simulated_effect(
                        t, self._convert_simulated_effect(se, fluents_map, em, problem)
                    )
            else:
                raise NotImplementedError(
                    f"Not implemented action class: {type(old_action)}"
                )
            new_problem.add_action(new_action)
            new_to_old[new_action] = old_action

        for g in problem.goals:
            new_problem.add_goal(utf_remover.remove_usertype_fluents_from_condition(g))

        for t, el in problem.timed_effects.items():
            for e in el:
                for ne in self._convert_effect(
                    e, problem, fluents_map, em, utf_remover
                ):
                    new_problem._add_effect_instance(t, ne)

        for i, cl in problem.timed_goals.items():
            for c in cl:
                new_problem.add_timed_goal(
                    i, utf_remover.remove_usertype_fluents_from_condition(c)
                )

        for tr in problem.trajectory_constraints:
            new_problem.add_trajectory_constraint(
                utf_remover.remove_usertype_fluents_from_condition(tr)
            )

        for qm in problem.quality_metrics:
            if qm.is_minimize_sequential_plan_length() or qm.is_minimize_makespan():
                new_problem.add_quality_metric(qm)
            elif qm.is_minimize_expression_on_final_state():
                assert isinstance(qm, MinimizeExpressionOnFinalState)
                new_problem.add_quality_metric(
                    MinimizeExpressionOnFinalState(
                        utf_remover.remove_usertype_fluents_from_condition(
                            qm.expression
                        ),
                        environment=new_problem.environment,
                    )
                )
            elif qm.is_maximize_expression_on_final_state():
                assert isinstance(qm, MaximizeExpressionOnFinalState)
                new_problem.add_quality_metric(
                    MaximizeExpressionOnFinalState(
                        utf_remover.remove_usertype_fluents_from_condition(
                            qm.expression
                        ),
                        environment=new_problem.environment,
                    )
                )
            elif qm.is_minimize_action_costs():
                assert isinstance(qm, MinimizeActionCosts)
                new_costs: Dict["up.model.Action", "up.model.Expression"] = {}
                for new_act, old_act in new_to_old.items():
                    cost = qm.get_action_cost(old_act)
                    if cost is not None:
                        cost = utf_remover.remove_usertype_fluents_from_condition(cost)
                        new_costs[new_act] = cost
                new_problem.add_quality_metric(
                    MinimizeActionCosts(new_costs, environment=new_problem.environment)
                )
            elif qm.is_oversubscription():
                assert isinstance(qm, Oversubscription)
                new_goals: Dict[BoolExpression, NumericConstant] = {
                    utf_remover.remove_usertype_fluents_from_condition(g): v
                    for g, v in qm.goals.items()
                }
                new_problem.add_quality_metric(
                    Oversubscription(new_goals, environment=new_problem.environment)
                )
            elif qm.is_temporal_oversubscription():
                assert isinstance(qm, TemporalOversubscription)
                new_temporal_goals: Dict[
                    Tuple["up.model.timing.TimeInterval", "up.model.BoolExpression"],
                    NumericConstant,
                ] = {
                    (i, utf_remover.remove_usertype_fluents_from_condition(g)): v
                    for (i, g), v in qm.goals.items()
                }
                new_problem.add_quality_metric(
                    TemporalOversubscription(
                        new_temporal_goals, environment=new_problem.environment
                    )
                )
            else:
                raise NotImplementedError

        for f, v in problem.initial_values.items():
            (
                new_fluent_exp,
                fluent_var,
                free_vars,
                last_fluent,
                free_fluents,
            ) = utf_remover.remove_usertype_fluents(f)
            assert (
                not free_vars and not free_fluents
            ), "Error in fluent's initial values; expected all constant for fluent arguments"
            if fluent_var is not None:
                assert last_fluent is not None
                assert (
                    v.is_object_exp()
                ), "Error: Usertype fluents initial value is not an object"
                value_obj = v.object()
                for obj in problem.objects(fluent_var.type):
                    new_problem.set_initial_value(
                        last_fluent.substitute({fluent_var: obj}), obj == value_obj
                    )
            else:
                new_problem.set_initial_value(f, v)

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )

    def _convert_simulated_effect(
        self,
        simulated_effect: SimulatedEffect,
        fluents_map: Dict[Fluent, Fluent],
        em: ExpressionManager,
        original_problem: Problem,
    ) -> SimulatedEffect:
        result_fluents: List[Union[Fluent, FNode]] = []
        for f_exp in simulated_effect.fluents:
            if f_exp.fluent not in fluents_map:
                result_fluents.append(f_exp)
            else:
                for o in original_problem.objects(f_exp.type):
                    compiled_fluents_args = f_exp.args[:]
                    compiled_fluents_args.append(em.ObjectExp(o))
                    result_fluents.append(
                        em.FluentExp(fluents_map[f_exp.fluent()], compiled_fluents_args)
                    )

        def new_fun(
            compiled_problem: "up.model.problem.AbstractProblem",
            compiled_state: "up.model.state.State",
            params: Dict["up.model.parameter.Parameter", "up.model.fnode.FNode"],
        ) -> List["up.model.fnode.FNode"]:
            # create a the state for the original problem from the state of the
            # compiled problem
            assert isinstance(compiled_problem, Problem)
            original_state: Dict[FNode, FNode] = {}
            for f in original_problem.fluents:
                if f not in fluents_map:
                    for fluent_exp in get_all_fluent_exp(original_problem, f):
                        original_state[fluent_exp] = compiled_state.get_value(
                            fluent_exp
                        )
                else:
                    compiled_fluent = fluents_map[f]
                    for compiled_fluent_exp in get_all_fluent_exp(
                        compiled_problem, compiled_fluent
                    ):
                        compiled_value = compiled_state.get_value(compiled_fluent_exp)
                        assert (
                            compiled_value.is_bool_constant()
                        ), "Error, boolean value is not a boolean constant in the state"
                        if compiled_value.bool_constant_value():
                            original_fluent_exp = em.FluentExp(
                                f, compiled_fluent_exp.args[:-1]
                            )
                            obj_exp = compiled_fluent_exp.args[-1]
                            test_value = original_state.setdefault(
                                original_fluent_exp, obj_exp
                            )
                            assert (
                                obj_exp == test_value
                            ), "Error, found True Value multiple times in the same state for a boolean fluent used to remove a UserType fluent"
            state = UPState(original_state)
            # populate the ret_val list with the default returned value, when a non
            # usertype fluent is returned, while with a series of True and False
            # when a usertype is returned
            ret_val = []
            result_fluents_iterator = iter(result_fluents)
            for ret_f_exp in simulated_effect.function(original_problem, state, params):
                if ret_f_exp.type.is_user_type():
                    assert ret_f_exp.is_object_exp()
                    returned_obj = ret_f_exp.object()
                    true_found = False
                    for _ in original_problem.objects(ret_f_exp.type):
                        current_val = next(result_fluents_iterator)
                        assert isinstance(current_val, FNode)
                        current_obj = current_val.args[-1].object()
                        if returned_obj == current_obj:
                            assert (
                                not true_found
                            ), "error, multiple true value found, only 1 accepted"
                            true_found = True
                            ret_val.append(em.TRUE())
                        else:
                            ret_val.append(em.FALSE())
                else:
                    next(result_fluents_iterator)
                    ret_val.append(ret_f_exp)
            return ret_val

        return SimulatedEffect(result_fluents, new_fun)

    def _convert_effect(
        self,
        effect: Effect,
        problem: Problem,
        fluents_map: Dict[Fluent, Fluent],
        em: ExpressionManager,
        utf_remover: UsertypeFluentsWalker,
    ) -> Iterator[Effect]:
        returned_effects: Set[Effect] = set()
        (
            new_fluent,
            fluent_last_var,
            fluent_free_vars,
            fluent_last_fluent,
            fluent_added_fluents,
        ) = utf_remover.remove_usertype_fluents(effect.fluent)
        (
            new_value,
            value_last_var,
            value_free_vars,
            value_last_fluent,
            value_added_fluents,
        ) = utf_remover.remove_usertype_fluents(effect.value)

        if fluent_last_var is not None:  # this effect's fluent is a user_type fluent
            assert fluent_last_fluent is not None
            fluent_free_vars.add(fluent_last_var)
            if value_last_var is not None:  # also the value is a user_type fluent
                assert value_last_fluent is not None
                assert effect.value.fluent() in fluents_map
                new_value = value_last_fluent
                # The "top-level" variables of the fluent and the value must be the same
                new_value = new_value.substitute({value_last_var: fluent_last_var})
            else:
                # transform the expression of type Usertype in the corresponding boolean expression
                new_value = em.Equals(new_value, fluent_last_var)
            assert effect.fluent.fluent() in fluents_map
            new_fluent = fluent_last_fluent
        new_condition = utf_remover.remove_usertype_fluents_from_condition(
            effect.condition
        )
        condition_to_add = em.And(
            *fluent_added_fluents,
            *value_added_fluents,
        )
        vars_list = list(fluent_free_vars)
        vars_list.extend(value_free_vars)
        # create all the possible configurations of variable instantiations and
        # evaluate if the result is a valid Effect or not. In case it is, yield
        # the Effect and proceed with the next iteration
        for objects in product(*(problem.objects(v.type) for v in vars_list)):
            assert len(objects) == len(vars_list)
            objects = cast(Tuple[Object, ...], objects)
            subs: Dict[Expression, Expression] = dict(zip(vars_list, objects))
            resulting_effect_fluent = new_fluent.substitute(subs).simplify()
            resulting_effect_value = new_value.substitute(subs).simplify()
            # Check if the type is boolean and not a constant, make it a conditional
            # assignment with the correct boolean constant instead
            if (
                resulting_effect_value.type.is_bool_type()
                and not resulting_effect_value.is_bool_constant()
            ):
                positive_condition = em.And(
                    condition_to_add, resulting_effect_value
                ).substitute(subs)
                positive_condition = em.And(
                    new_condition, positive_condition
                ).simplify()
                if (
                    not positive_condition.is_constant()
                    or positive_condition.bool_constant_value()
                ):
                    effect = Effect(
                        resulting_effect_fluent,
                        em.TRUE(),
                        positive_condition,
                        effect.kind,
                    )
                    if effect not in returned_effects:
                        yield effect
                        returned_effects.add(effect)
                negative_condition = em.And(
                    condition_to_add, em.Not(resulting_effect_value)
                ).substitute(subs)
                negative_condition = em.And(
                    new_condition, negative_condition
                ).simplify()
                if (
                    not negative_condition.is_constant()
                    or negative_condition.bool_constant_value()
                ):
                    effect = Effect(
                        resulting_effect_fluent,
                        em.FALSE(),
                        negative_condition,
                        effect.kind,
                    )
                    if effect not in returned_effects:
                        yield effect
                        returned_effects.add(effect)
            else:
                subbed_cond = (
                    em.And(new_condition, condition_to_add).substitute(subs).simplify()
                )
                if not subbed_cond.is_constant() or subbed_cond.bool_constant_value():
                    effect = Effect(
                        resulting_effect_fluent,
                        resulting_effect_value,
                        subbed_cond,
                        effect.kind,
                    )
                    if effect not in returned_effects:
                        yield effect
                        returned_effects.add(effect)

    def _update_names_in_effect(self, effect: Effect, defined_names: Set[str]):
        """Important NOTE: this method adds elements to the defined_names set."""
        defined_names.update(effect._fluent.get_contained_names())
        defined_names.update(effect._value.get_contained_names())
        defined_names.update(effect._condition.get_contained_names())

    def _get_names_in_problem(self, problem: Problem) -> Set[str]:
        defined_names: Set[str] = (
            {problem._name} if problem._name is not None else set()
        )
        for ut in problem._user_types:
            defined_names.add(cast(up.model.types._UserType, ut).name)
        for f in problem._fluents:
            defined_names.add(f.name)
        for a in problem._actions:
            if isinstance(a, InstantaneousAction):
                defined_names.update(a._parameters)
                for p in a._preconditions:
                    defined_names.update(p.get_contained_names())
                for e in a._effects:
                    self._update_names_in_effect(e, defined_names)
            elif isinstance(a, DurativeAction):
                defined_names.update(a._parameters)
                defined_names.update(a.duration.lower.get_contained_names())
                defined_names.update(a.duration.upper.get_contained_names())
                for cl in a._conditions.values():
                    for c in cl:
                        defined_names.update(c.get_contained_names())
                for el in a._effects.values():
                    for e in el:
                        self._update_names_in_effect(e, defined_names)
            else:
                raise NotImplementedError(f"Action class {type(a)} not implemented.")
        for o in problem._objects:
            defined_names.add(o.name)
        for fe, ve in problem.initial_values.items():
            defined_names.update(fe.get_contained_names())
            defined_names.update(ve.get_contained_names())
        for el in problem._timed_effects.values():
            for e in el:
                self._update_names_in_effect(e, defined_names)
        for gl in problem._timed_goals.values():
            for g in gl:
                defined_names.update(g.get_contained_names())
        for g in problem._goals:
            defined_names.update(g.get_contained_names())
        for tr in problem.trajectory_constraints:
            defined_names.update(tr.get_contained_names())
        for qm in problem._metrics:
            if qm.is_minimize_action_costs():
                assert isinstance(qm, MinimizeActionCosts)
                for cost in qm.costs.values():
                    if cost is not None:
                        defined_names.update(cost.get_contained_names())
            elif (
                qm.is_minimize_expression_on_final_state()
                or qm.is_maximize_expression_on_final_state()
            ):
                assert isinstance(
                    qm, (MinimizeExpressionOnFinalState, MaximizeExpressionOnFinalState)
                )
                defined_names.update(qm.expression.get_contained_names())
            elif qm.is_oversubscription():
                assert isinstance(qm, Oversubscription)
                for g in qm.goals:
                    defined_names.update(g.get_contained_names())
            elif qm.is_temporal_oversubscription():
                assert isinstance(qm, TemporalOversubscription)
                for _, g in qm.goals:
                    defined_names.update(g.get_contained_names())

        return defined_names
