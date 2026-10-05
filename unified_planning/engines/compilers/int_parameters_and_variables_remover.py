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
"""This module defines the integer parameters and variables remover compiler."""

from itertools import product
from fractions import Fraction
import warnings
import unified_planning as up
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model.fnode import FNode
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    Problem,
    InstantaneousAction,
    DurativeAction,
    DurationInterval,
    Timing,
    TimeInterval,
    Variable,
    Action,
    ProblemKind,
    MinimizeActionCosts,
    MinimizeExpressionOnFinalState,
    MaximizeExpressionOnFinalState,
    Oversubscription,
    TemporalOversubscription,
    IntVariable,
    Parameter,
    OperatorKind,
    Effect,
    Expression,
    SimulatedEffect,
)
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.compilers.utils import get_fresh_name
from unified_planning.plans import ActionInstance
from typing import (
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Tuple,
    OrderedDict,
    Union,
    cast,
)
from unified_planning.model.types import _IntType
from unified_planning.model.expression import BoolExpression
from functools import partial


class IntParametersAndVariablesRemover(engines.engine.Engine, CompilerMixin):
    """
    Removes bounded integer action parameters and quantified integer variables.

    Each combination of integer parameter values produces an action candidate.
    Other parameter types remain in the action signature. For example, an
    action with ``n: IntType(1, 3)`` and precondition ``n < 2`` produces only the
    instance with ``n = 1``; the other candidates have false preconditions.

    After substituting action parameters, ``IntVariable`` ranges are expanded
    into conjunctions for ``Forall``, disjunctions for ``Exists``, and individual
    effects for universal effects. Both endpoints are included. Dependencies
    between integer variables determine their expansion order, and all bounds
    must become integer constants. Object variables remain quantified.

    Supports instantaneous and durative actions; continuous effects are not
    supported. Integer-valued fluents and integer fluent parameters are not
    removed by this compiler.

    The returned ``CompilerResult.map_back_action_instance`` restores the
    original action and the integer arguments at their original positions.
    Use it with ``Plan.replace_action_instances`` to reconstruct a plan for
    the original problem.
    """

    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(
            self, CompilationKind.INT_PARAMETERS_AND_VARIABLES_REMOVING
        )

    @property
    def name(self):
        return "ipavr"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("REAL_ACTION_PARAMETERS")
        supported_kind.set_numbers("BOUNDED_TYPES")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_fluents_type("INT_FLUENTS")
        supported_kind.set_fluents_type("REAL_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_conditions_kind("INT_VARIABLES")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FORALL_EFFECTS")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECTS")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_time("SELF_OVERLAPPING")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("INT_TYPE_DURATIONS")
        supported_kind.set_expression_duration("REAL_TYPE_DURATIONS")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_constraints_kind("STATE_INVARIANTS")
        supported_kind.set_constraints_kind("TRAJECTORY_CONSTRAINTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= IntParametersAndVariablesRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.INT_PARAMETERS_AND_VARIABLES_REMOVING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = problem_kind.clone()
        new_kind.unset_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        new_kind.unset_conditions_kind("INT_VARIABLES")
        if (
            problem_kind.has_int_variables()
            and problem_kind.has_existential_conditions()
        ):
            new_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        if problem_kind.has_conditional_effects() and problem_kind.has_bounded_types():
            # Invalid assignments become applicability conditions on the action.
            new_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
            if problem_kind.has_forall_effects():
                new_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        return new_kind

    # ==================== INT VARIABLE TRANSFORMATION ====================
    def _split_variables(
        self, variables: Iterable[Union[Variable, IntVariable]]
    ) -> Tuple[Tuple[Variable, ...], Dict[IntVariable, Tuple[FNode, FNode]]]:
        """Separate regular variables from int variables."""
        regular_vars = []
        int_vars = {}
        for var in variables:
            if isinstance(var, IntVariable):
                int_vars[var] = (var.initial, var.last)
            else:
                regular_vars.append(var)
        return tuple(regular_vars), int_vars

    def _evaluate_int_var_ranges(
        self, old_problem, new_problem, int_vars, int_params, instantiation
    ):
        """
        Evaluate the range bounds with the current parameter values, so that
        quantified int variables get concrete integer bounds.
        """
        updated = {}
        for variable, (initial, last) in int_vars.items():
            new_initial = self._transform_expression(
                old_problem, new_problem, initial, int_params, instantiation
            )
            new_last = self._transform_expression(
                old_problem, new_problem, last, int_params, instantiation
            )
            if (
                new_initial is None
                or not new_initial.is_int_constant()
                or new_last is None
                or not new_last.is_int_constant()
            ):
                raise UPProblemDefinitionError(
                    f"The bounds of integer variable {variable.name} must become "
                    "integer constants after instantiating the enclosing parameters "
                    "and variables."
                )
            updated[variable] = (
                new_initial.constant_value(),
                new_last.constant_value(),
            )
        return updated

    def _get_int_var_instantiations(
        self,
        old_problem: Problem,
        new_problem: Problem,
        int_vars: Dict[IntVariable, Tuple[FNode, FNode]],
        int_params: Dict[Union[Parameter, IntVariable], int],
        instantiation: Tuple[int, ...],
    ) -> Iterator[Tuple[Dict[Union[Parameter, IntVariable], int], Tuple[int, ...]]]:
        """Evaluate dependent ranges after instantiating their dependencies."""
        oracle = old_problem.environment.free_vars_oracle
        dependencies = {}
        for variable, bounds in int_vars.items():
            free_vars = oracle.get_free_variables(
                bounds[0]
            ) | oracle.get_free_variables(bounds[1])
            unbound = free_vars.difference(int_vars, int_params)
            if unbound:
                names = ", ".join(sorted(v.name for v in unbound))
                raise UPProblemDefinitionError(
                    f"The bounds of integer variable {variable.name} reference "
                    f"variables that have not been instantiated: {names}"
                )
            dependencies[variable] = set(free_vars.intersection(int_vars))

        ordered = []
        while dependencies:
            ready = [v for v, required in dependencies.items() if not required]
            if not ready:
                names = ", ".join(v.name for v in dependencies)
                raise UPProblemDefinitionError(
                    f"Circular dependencies between integer variable bounds: {names}"
                )
            for variable in ready:
                ordered.append(variable)
                del dependencies[variable]
            for required in dependencies.values():
                required.difference_update(ready)

        def expand(index, params, values):
            if index == len(ordered):
                yield params, values
                return
            variable = ordered[index]
            ranges = self._evaluate_int_var_ranges(
                old_problem, new_problem, {variable: int_vars[variable]}, params, values
            )
            lower, upper = ranges[variable]
            expanded_params = params.copy()
            expanded_params[variable] = len(values)
            for value in range(lower, upper + 1):
                yield from expand(index + 1, expanded_params, values + (value,))

        yield from expand(0, int_params, instantiation)

    def _get_range_instantiation(
        self, ranges: Mapping[Parameter, Tuple[int, int]]
    ) -> List[Tuple[int, ...]]:
        """Generate all combinations of values for int variables."""
        if not ranges:
            return [()]
        range_iterables = [range(start, end + 1) for start, end in ranges.values()]
        return list(product(*range_iterables))

    # ==================== EXPRESSION TRANSFORMATION ====================

    def _transform_quantifier(
        self,
        old_problem: Problem,
        new_problem: Problem,
        node: FNode,
        int_params: Dict[Union[Parameter, IntVariable], int],
        instantiation: Tuple[int, ...],
    ) -> Optional[FNode]:
        """
        Transform forall/exists by expanding int variables.
        Replaces int variables with concrete instantiation, then expands the quantifier into a
        conjunction/disjunction over valid value ranges.
        """
        em = old_problem.environment.expression_manager
        body_variables = old_problem.environment.free_vars_oracle.get_free_variables(
            node.arg(0)
        )
        # Match simplification: do not retain integer variables only used in bounds.
        variables = tuple(
            variable
            for variable in node.variables()
            if not isinstance(variable, IntVariable) or variable in body_variables
        )
        if not variables:
            return self._transform_expression(
                old_problem, new_problem, node.arg(0), int_params, instantiation
            )
        if variables != tuple(node.variables()):
            node = em.create_node(node.node_type, tuple(node.args), variables)
        regular_vars, int_vars = self._split_variables(variables)
        if any(
            variable.type.is_user_type() and not any(old_problem.objects(variable.type))
            for variable in regular_vars
        ):
            # An empty domain leaves no instances to evaluate, even if the
            # body would otherwise contain undefined expressions.
            return old_problem.environment.expression_manager.Bool(node.is_forall())

        if not int_vars:
            # No int variables: keep quantifier
            new_args = [
                self._transform_expression(
                    old_problem, new_problem, arg, int_params, instantiation
                )
                for arg in node.args
            ]
            if new_args == list(node.args):
                return node
            em = old_problem.environment.expression_manager
            defined_args = self._handle_undef_args(node.node_type, new_args, em)
            if defined_args is None:
                return None
            em = old_problem.environment.expression_manager
            return em.create_node(
                node.node_type, tuple(defined_args), regular_vars
            ).simplify()

        # Expand quantifier body for each instantiation
        expanded_args = []
        has_instances = False
        for expanded_int_params, full_inst in self._get_int_var_instantiations(
            old_problem, new_problem, int_vars, int_params, instantiation
        ):
            has_instances = True
            for arg in node.args:
                transformed = self._transform_expression(
                    old_problem, new_problem, arg, expanded_int_params, full_inst
                )
                if transformed is None:
                    # Forall is strict; Exists ignores undefined instances
                    # unless every instance is undefined.
                    if node.is_forall():
                        return None
                    continue
                expanded_args.append(transformed)
        if not has_instances:
            return new_problem.environment.expression_manager.Bool(node.is_forall())
        if not expanded_args:
            return None

        # Combine with appropriate operator
        em = new_problem.environment.expression_manager
        new_op = OperatorKind.AND if node.is_forall() else OperatorKind.OR
        new_node = em.create_node(new_op, tuple(expanded_args)).simplify()
        if regular_vars:
            if node.is_exists():
                return em.Exists(new_node, *regular_vars)
            elif node.is_forall():
                return em.Forall(new_node, *regular_vars)
            else:
                raise UPProblemDefinitionError(f"Error handling quantifiers!")
        return new_node

    def _transform_fluent_exp(
        self, old_problem, new_problem, node, int_params, instantiation
    ):
        new_args = []
        for arg in node.args:
            transformed = self._transform_expression(
                old_problem, new_problem, arg, int_params, instantiation
            )
            if transformed is None:
                return None
            new_args.append(transformed)
        return node.fluent()(*new_args)

    def _handle_undef_args(
        self, node_type: OperatorKind, args: List, em
    ) -> Union[List[FNode], None]:
        """Handle undefined (None) values in arguments based on operator semantics."""
        if None not in args:
            return args
        if node_type in {OperatorKind.OR, OperatorKind.EXISTS}:
            filtered = [arg for arg in args if arg is not None]
            return filtered if filtered else None
        elif node_type == OperatorKind.IMPLIES:
            if args[1] is None and args[0] is not None:
                return [args[0], em.FALSE()]
            return [em.TRUE(), args[1]] if args[1] is not None else None
        else:
            return None

    def _transform_generic(
        self,
        old_problem: Problem,
        new_problem: Problem,
        node: FNode,
        int_params: Dict[Union[Parameter, IntVariable], int],
        instantiation: Tuple[int, ...],
    ) -> Union[FNode, None]:
        """Generic recursive transformation. Arithmetic that becomes undefined after substitution
        (e.g. division by zero) is handled and returned as None."""
        em = old_problem.environment.expression_manager
        new_args = [
            self._transform_expression(
                old_problem, new_problem, arg, int_params, instantiation
            )
            for arg in node.args
        ]
        # Leave ordinary UP expressions unchanged when no integer parameter
        # substitution or integer-variable expansion affected their arguments.
        if new_args == list(node.args):
            return node
        defined_args = self._handle_undef_args(node.node_type, new_args, em)
        if defined_args is None or defined_args == []:
            return None
        try:
            return em.create_node(node.node_type, tuple(defined_args)).simplify()
        except (
            ZeroDivisionError
        ):  # division by zero is currently the only undefined arithmetic
            return None

    def _transform_expression(
        self,
        old_problem: Problem,
        new_problem: Problem,
        node: FNode,
        int_params: Optional[Dict[Union[Parameter, IntVariable], int]] = None,
        instantiation: Optional[Tuple[int, ...]] = None,
    ) -> Union[FNode, None]:
        """
        Transform expression by substituting integer parameters and expanding quantifiers, replacing:
        - Integer parameters and int variables with their instantiated values
        - Quantifiers over int variables expanded into and/or
        """
        if int_params is None:
            int_params = {}
        if instantiation is None:
            instantiation = ()
        # Base cases
        if node.is_constant() or node.is_variable_exp() or node.is_timing_exp():
            return node

        if node.is_int_variable_exp():
            variable = node.int_variable()
            if variable in int_params:
                var_index = int_params[variable]
                return old_problem.environment.expression_manager.Int(
                    instantiation[var_index]
                )
            return node

        if node.is_parameter_exp():
            parameter = node.parameter()
            if parameter in int_params:
                return old_problem.environment.expression_manager.Int(
                    instantiation[int_params[parameter]]
                )
            return node

        if node.is_fluent_exp():
            return self._transform_fluent_exp(
                old_problem, new_problem, node, int_params, instantiation
            )

        if node.is_forall() or node.is_exists():
            return self._transform_quantifier(
                old_problem, new_problem, node, int_params, instantiation
            )

        return self._transform_generic(
            old_problem, new_problem, node, int_params, instantiation
        )

    # ==================== ACTION TRANSFORMATION ====================

    def _transform_simulated_effect(
        self, problem, new_problem, effect, int_param_map, instantiation
    ) -> SimulatedEffect:
        """Instantiate targets and restore integer arguments for the callback."""
        fluents = []
        for fluent in effect.fluents:
            transformed = self._transform_expression(
                problem, new_problem, fluent, int_param_map, instantiation
            )
            assert transformed is not None
            fluents.append(transformed)
        em = problem.environment.expression_manager
        integer_arguments = {
            parameter: em.Int(instantiation[index])
            for parameter, index in int_param_map.items()
        }

        def function(callback_problem, state, actual_parameters):
            parameters = dict(actual_parameters)
            parameters.update(integer_arguments)
            return effect.function(callback_problem, state, parameters)

        # Rebuilding an existing effect should not repeat its deprecation warning.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return SimulatedEffect(fluents, function)

    def _add_effect_to_action(
        self,
        action: Action,
        effect: Effect,
        timing: Optional[Timing] = None,
    ):
        """Attach an instantiated effect to an instantaneous or durative action."""
        if isinstance(action, InstantaneousAction):
            action._add_effect_instance(effect)
        elif isinstance(action, DurativeAction):
            assert timing is not None
            action._add_effect_instance(timing, effect)
        else:
            raise UPProblemDefinitionError(
                f"Unsupported action type: {type(action).__name__}"
            )

    def _transform_single_effect(
        self,
        effect: Effect,
        fluent: Optional[FNode],
        value: Optional[FNode],
        condition: Optional[FNode],
        forall: Tuple,
    ) -> Tuple[Optional[Effect], FNode]:
        """
        Return the instantiated effect and the condition required for its validity.

        A false condition rejects the instance. An absent effect with a true
        condition represents an effect that never fires. This transformation does
        not modify an action or a problem.
        """
        em = effect.environment.expression_manager
        if condition is None or condition.is_false():
            return None, em.TRUE()
        if fluent is not None and value is not None:
            out_of_bounds = False
            if (
                effect.is_assignment()
                and fluent.type.is_int_type()
                and value.is_constant()
            ):
                fluent_type = cast(_IntType, fluent.type)
                lower, upper = fluent_type.lower_bound, fluent_type.upper_bound
                out_of_bounds = (
                    lower is not None and value.constant_value() < lower
                ) or (upper is not None and value.constant_value() > upper)
            if not out_of_bounds:
                return Effect(fluent, value, condition, effect.kind, forall), em.TRUE()

        # An undefined target/value or an out-of-bounds assignment is only
        # permissible when the instantiated condition does not hold.
        guard = em.Not(condition)
        if forall:
            guard = em.Forall(guard, *forall)
        return None, guard.simplify()

    def _instantiate_effect(
        self,
        old_problem: Problem,
        new_problem: Problem,
        effect: Effect,
        int_param_map: Dict[Union[Parameter, IntVariable], int],
        instantiation: Tuple[int, ...],
    ) -> Iterator[Tuple[Optional[Effect], FNode]]:
        """
        Expand integer variables and yield effects with their validity conditions.
        The caller decides how to attach them to an action or a problem.
        """
        regular_forall, int_vars = self._split_variables(list(effect.forall))
        if any(
            variable.type.is_user_type() and not any(old_problem.objects(variable.type))
            for variable in regular_forall
        ):
            return
        if not int_vars:
            new_fluent = self._transform_expression(
                old_problem, new_problem, effect.fluent, int_param_map, instantiation
            )
            new_value = self._transform_expression(
                old_problem, new_problem, effect.value, int_param_map, instantiation
            )
            new_condition = self._transform_expression(
                old_problem, new_problem, effect.condition, int_param_map, instantiation
            )

            yield self._transform_single_effect(
                effect,
                new_fluent,
                new_value,
                new_condition,
                regular_forall,
            )
            return

        # Use the same dependent-range expansion as Forall and Exists.
        for expanded_int_params, full_inst in self._get_int_var_instantiations(
            old_problem, new_problem, int_vars, int_param_map, instantiation
        ):
            new_fluent = self._transform_expression(
                old_problem, new_problem, effect.fluent, expanded_int_params, full_inst
            )
            new_value = self._transform_expression(
                old_problem, new_problem, effect.value, expanded_int_params, full_inst
            )
            new_condition = self._transform_expression(
                old_problem,
                new_problem,
                effect.condition,
                expanded_int_params,
                full_inst,
            )
            yield self._transform_single_effect(
                effect,
                new_fluent,
                new_value,
                new_condition,
                regular_forall,
            )

    def _add_instantiated_effects(
        self,
        problem: Problem,
        new_problem: Problem,
        old_action: Action,
        new_action: Action,
        int_param_map: Dict[Union[Parameter, IntVariable], int],
        instantiation: Tuple[int, ...],
    ) -> bool:
        """
        Add all effects to instantiated action.
        Returns False if the action must be pruned. An empty effect list is valid.
        """
        effects_by_timing: Iterable[Tuple[Optional[Timing], List[Effect]]]
        if isinstance(old_action, InstantaneousAction):
            effects_by_timing = [(None, old_action.effects)]
        elif isinstance(old_action, DurativeAction):
            effects_by_timing = old_action.effects.items()
        else:
            raise UPProblemDefinitionError(
                f"Unsupported action type: {type(old_action).__name__}"
            )
        for timing, effects in effects_by_timing:
            for effect in effects:
                for transformed, guard in self._instantiate_effect(
                    problem, new_problem, effect, int_param_map, instantiation
                ):
                    if guard.is_false():
                        return False
                    if not guard.is_true():
                        if isinstance(new_action, InstantaneousAction):
                            new_action.add_precondition(guard)
                        elif isinstance(new_action, DurativeAction):
                            assert timing is not None
                            new_action.add_condition(timing, guard)
                    if transformed is not None:
                        self._add_effect_to_action(new_action, transformed, timing)
        return True

    def _transform_timed_effects(self, problem: Problem, new_problem: Problem):
        """Transform global timed effects and attach them to the compiled problem."""
        for timing, effects in problem.timed_effects.items():
            for effect in effects:
                for transformed, guard in self._instantiate_effect(
                    problem, new_problem, effect, {}, ()
                ):
                    if not guard.is_true():
                        raise UPProblemDefinitionError(
                            f"IPAVR cannot compile global timed effect at {timing}: "
                            "integer-variable expansion produces an invalid effect "
                            f"that may be enabled. Check the effect: {effect}"
                        )
                    if transformed is not None:
                        new_problem._add_effect_instance(timing, transformed)

    def _create_instantiated_action(
        self,
        problem: Problem,
        new_problem: Problem,
        action: Action,
        regular_params: OrderedDict,
        int_param_map: Dict[Union[Parameter, IntVariable], int],
        instantiation: Tuple[int, ...],
    ) -> Union[Action, None]:
        """
        Create a single instantiated action for a specific integer parameter assignment.
        Transforms preconditions and effects, pruning the action if any become false/invalid.
        """
        # Generate unique name
        action_name = get_fresh_name(
            new_problem, action.name, list(map(str, instantiation))
        )
        # Create action with only regular (noninteger) parameters
        new_action: Union[InstantaneousAction, DurativeAction]
        conditions: Iterable[Tuple[Optional[TimeInterval], List[FNode]]]
        simulated_effects: Iterable[Tuple[Optional[Timing], Optional[SimulatedEffect]]]
        if isinstance(action, InstantaneousAction):
            new_action = InstantaneousAction(
                action_name, regular_params, action.environment
            )
            conditions = [(None, action.preconditions)]
            simulated_effects = [(None, action.simulated_effect)]
        elif isinstance(action, DurativeAction):
            if action.continuous_effects:
                raise UPProblemDefinitionError(
                    "IPAVR does not support continuous effects"
                )
            new_action = DurativeAction(action_name, regular_params, action.environment)
            lower = self._transform_expression(
                problem,
                new_problem,
                action.duration.lower,
                int_param_map,
                instantiation,
            )
            upper = self._transform_expression(
                problem,
                new_problem,
                action.duration.upper,
                int_param_map,
                instantiation,
            )
            if lower is None or upper is None:
                return None
            try:
                new_action.set_duration_constraint(
                    DurationInterval(
                        lower,
                        upper,
                        action.duration.is_left_open(),
                        action.duration.is_right_open(),
                    )
                )
            except UPProblemDefinitionError:
                # Empty duration intervals cannot produce applicable instances.
                return None
            conditions = action.conditions.items()
            simulated_effects = action.simulated_effects.items()
        else:
            raise UPProblemDefinitionError(
                f"Unsupported action type: {type(action).__name__}"
            )

        for interval, expressions in conditions:
            for expression in expressions:
                transformed = self._transform_expression(
                    problem, new_problem, expression, int_param_map, instantiation
                )
                if transformed is None:
                    return None
                if isinstance(new_action, InstantaneousAction):
                    if transformed.is_false():
                        return None
                    new_action.add_precondition(transformed)
                else:
                    assert interval is not None
                    new_action.add_condition(interval, transformed)

        # Transform effects
        has_valid_effects = self._add_instantiated_effects(
            problem, new_problem, action, new_action, int_param_map, instantiation
        )
        if not has_valid_effects:
            return None
        for timing, effect in simulated_effects:
            if effect is not None:
                simulated = self._transform_simulated_effect(
                    problem,
                    new_problem,
                    effect,
                    int_param_map,
                    instantiation,
                )
                if isinstance(new_action, InstantaneousAction):
                    new_action.set_simulated_effect(simulated)
                else:
                    assert timing is not None
                    new_action.set_simulated_effect(timing, simulated)
        return new_action

    def _instantiate_action(
        self,
        problem: Problem,
        new_problem: Problem,
        action: Action,
    ) -> List[Tuple[Action, Tuple[int, ...]]]:
        """
        Create all valid instantiation of an action for integer parameters.
        Generates Cartesian product of integer parameter ranges, validates each, and returns list of pairs for valid instances.
        """
        # Separate regular and integer parameters
        regular_params = OrderedDict()
        int_param_map: Dict[Union[Parameter, IntVariable], int] = {}
        int_param_ranges: Dict[Parameter, Tuple[int, int]] = {}

        for param in action.parameters:
            if not param.type.is_int_type():
                regular_params[param.name] = param.type
            else:
                param_type = cast(_IntType, param.type)
                if param_type.lower_bound is None or param_type.upper_bound is None:
                    raise UPProblemDefinitionError(
                        f"IPAVR requires finite bounds for integer parameter {param.name}"
                    )
                int_param_map[param] = len(int_param_map)
                int_param_ranges[param] = (
                    param_type.lower_bound,
                    param_type.upper_bound,
                )

        # Generate all instantiation
        instantiation = self._get_range_instantiation(int_param_ranges)
        result = []
        for inst in instantiation:
            new_action = self._create_instantiated_action(
                problem, new_problem, action, regular_params, int_param_map, inst
            )
            if new_action is not None:
                result.append((new_action, inst))
        return result

    def _transform_actions(
        self, problem: Problem, new_problem: Problem
    ) -> Dict[Action, Tuple[Action, Tuple[int, ...]]]:
        """Transform all actions by grounding integer parameters."""
        new_to_old = {}
        for action in problem.actions:
            instantiated_actions = self._instantiate_action(
                problem, new_problem, action
            )
            for new_action, instantiation in instantiated_actions:
                new_problem.add_action(new_action)
                new_to_old[new_action] = (action, instantiation)
        return new_to_old

    # ==================== QUALITY METRICS TRANSFORMATION ====================

    def _transform_quality_metrics(
        self,
        problem: Problem,
        new_problem: Problem,
        new_to_old: Dict[Action, Tuple[Action, Tuple[int, ...]]],
    ):
        """Transform quality metrics, handling action costs with integer parameter substitution."""
        for qm in problem.quality_metrics:
            if qm.is_minimize_sequential_plan_length() or qm.is_minimize_makespan():
                new_problem.add_quality_metric(qm)
            elif qm.is_minimize_action_costs():
                assert isinstance(qm, MinimizeActionCosts)
                new_costs = self._transform_action_costs(qm, new_to_old)
                new_problem.add_quality_metric(
                    MinimizeActionCosts(
                        new_costs,
                        default=qm.default,
                        environment=new_problem.environment,
                    )
                )
            elif isinstance(qm, Oversubscription):
                goals: Dict[BoolExpression, Union[Fraction, int]] = {}
                for goal, reward in qm.goals.items():
                    transformed = self._transform_expression(problem, new_problem, goal)
                    if transformed is None:
                        raise UPProblemDefinitionError(
                            "Undefined oversubscription goal"
                        )
                    # Different original goals can become identical after expansion.
                    goals[transformed] = goals.get(transformed, 0) + reward
                new_problem.add_quality_metric(
                    Oversubscription(
                        {goal: reward for goal, reward in goals.items()},
                        environment=new_problem.environment,
                    )
                )
            elif isinstance(qm, TemporalOversubscription):
                timed_goals: Dict[
                    Tuple[TimeInterval, BoolExpression], Union[Fraction, int]
                ] = {}
                for (interval, goal), reward in qm.goals.items():
                    transformed = self._transform_expression(problem, new_problem, goal)
                    if transformed is None:
                        raise UPProblemDefinitionError(
                            "Undefined oversubscription goal"
                        )
                    key = (interval, transformed)
                    timed_goals[key] = timed_goals.get(key, 0) + reward
                new_problem.add_quality_metric(
                    TemporalOversubscription(
                        {key: reward for key, reward in timed_goals.items()},
                        environment=new_problem.environment,
                    )
                )
            elif isinstance(
                qm, (MinimizeExpressionOnFinalState, MaximizeExpressionOnFinalState)
            ):
                expression = self._transform_expression(
                    problem, new_problem, qm.expression
                )
                if expression is None:
                    raise UPProblemDefinitionError("Undefined final-state metric")
                new_problem.add_quality_metric(
                    type(qm)(expression, environment=new_problem.environment)
                )
            else:
                new_problem.add_quality_metric(qm)

    def _transform_action_costs(
        self,
        qm: MinimizeActionCosts,
        new_to_old: Dict[Action, Tuple[Action, Tuple[int, ...]]],
    ) -> Dict[Action, Expression]:
        """Transform action costs by substituting integer parameter values."""
        new_costs: Dict[Action, Expression] = {}
        for new_action, (old_action, instantiation) in new_to_old.items():
            if old_action is None:
                continue
            old_cost = qm.get_action_cost(old_action)
            if old_cost is None:
                continue
            integer_parameters = (
                parameter
                for parameter in old_action.parameters
                if parameter.type.is_int_type()
            )
            substitutions: Dict[Expression, Expression] = dict(
                zip(integer_parameters, instantiation)
            )
            new_costs[new_action] = old_cost.substitute(substitutions)
        return new_costs

    # ==================== GOALS TRANSFORMATION ====================
    def _transform_goals(self, problem: Problem, new_problem: Problem):
        for goal in problem.goals:
            transformed = self._transform_expression(problem, new_problem, goal)
            if transformed is None:
                raise UPProblemDefinitionError(
                    f"Undefined final goal after expanding integer variables: {goal}"
                )
            new_problem.add_goal(transformed)
        for interval, goals in problem.timed_goals.items():
            for goal in goals:
                transformed = self._transform_expression(problem, new_problem, goal)
                if transformed is None:
                    raise UPProblemDefinitionError(
                        f"Undefined timed goal in interval {interval} "
                        f"after expanding integer variables: {goal}"
                    )
                new_problem.add_timed_goal(interval, transformed)
        for constraint in problem.trajectory_constraints:
            transformed = self._transform_expression(problem, new_problem, constraint)
            if transformed is None:
                raise UPProblemDefinitionError("Undefined trajectory constraint")
            if transformed.is_false():
                new_problem.add_goal(transformed)
            elif not transformed.is_true():
                new_problem.add_trajectory_constraint(transformed)

    @staticmethod
    def _map_back_action_instance(
        action_instance: ActionInstance,
        new_to_old: Dict[Action, Tuple[Action, Tuple[int, ...]]],
    ) -> ActionInstance:
        """Restore integer arguments in their original positions."""
        original_action, integer_values = new_to_old[action_instance.action]
        integers = iter(integer_values)
        remaining = iter(action_instance.actual_parameters)

        parameters = [
            next(integers) if parameter.type.is_int_type() else next(remaining)
            for parameter in original_action.parameters
        ]

        return ActionInstance(
            original_action,
            parameters,
            action_instance.agent,
            action_instance.motion_paths,
        )

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """Main compilation."""
        assert isinstance(problem, Problem)

        if type(problem) is Problem:
            new_problem = Problem(problem.name, problem.environment)
            problem._clone_to_without_actions_and_metrics(new_problem)
        else:
            new_problem = problem.clone()
            new_problem.clear_actions()
            new_problem.clear_quality_metrics()

        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_goals()
        new_problem.clear_timed_goals()
        new_problem.clear_timed_effects()
        new_problem.clear_trajectory_constraints()

        new_to_old = self._transform_actions(problem, new_problem)
        self._transform_quality_metrics(problem, new_problem, new_to_old)
        self._transform_goals(problem, new_problem)
        self._transform_timed_effects(problem, new_problem)

        return CompilerResult(
            new_problem,
            partial(self._map_back_action_instance, new_to_old=new_to_old),
            self.name,
        )
