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

from itertools import chain

from fractions import Fraction
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    OrderedDict,
    Tuple,
    Type as TypingType,
    Union,
)

from pddl.logic.base import Formula, And, Or, Not, Imply, ForallCondition, ExistsCondition  # type: ignore
from pddl.logic.effects import When, Forall, Effect  # type: ignore
from pddl.logic.functions import NumericFunction, BinaryFunction, Increase, Decrease, NumericValue, EqualTo as EqualToFunction, Assign, LesserThan, LesserEqualThan, GreaterThan, GreaterEqualThan, Minus, Plus, Times, Divide, Metric  # type: ignore
from pddl.logic.predicates import DerivedPredicate, EqualTo as EqualToPredicate, Predicate  # type: ignore
from pddl.logic.terms import Constant, Variable, Term  # type: ignore
from pddl.core import Domain, Problem  # type: ignore
from pddl.action import Action  # type: ignore
from pddl.custom_types import name  # type: ignore

from unified_planning.model import (
    Fluent,
    Type,
    Parameter,
    Object,
    InstantaneousAction,
    FNode,
    Variable as UPVariable,
    Effect as UPEffect,
    Problem as UPProblem,
    Expression as UPExpression,
    Action as UPAction,
    EffectKind,
    MinimizeActionCosts,
    MinimizeExpressionOnFinalState,
    MaximizeExpressionOnFinalState,
    MinimizeSequentialPlanLength,
)
from unified_planning.model.type_manager import TypeManager
from unified_planning.model.expression import ExpressionManager
from unified_planning.environment import get_environment, Environment
from unified_planning.exceptions import (
    UPUnsupportedProblemTypeError,
)


def assert_not_none_type(t: Optional[Type]) -> Type:
    assert t is not None
    return t


class _ExpressionConverter:
    def __init__(
        self,
        expression_manager: ExpressionManager,
        types: Dict[name, Optional[Type]],
        fluents: Dict[name, Fluent],
        objects: Dict[name, Object],
    ):
        self._types = types
        self._fluents = fluents
        self._objects = objects
        self._em = expression_manager
        self._variables: Dict[Tuple[str, Type], UPVariable] = {}
        self._direct_matching_expressions: Dict[
            TypingType[BinaryFunction], Callable[..., FNode]
        ] = {
            And: self._em.And,
            Or: self._em.Or,
            Imply: self._em.Implies,
            EqualToFunction: self._em.Equals,
            LesserThan: self._em.LT,
            LesserEqualThan: self._em.LE,
            GreaterThan: self._em.GT,
            GreaterEqualThan: self._em.GE,
            Minus: self._em.Minus,
            Plus: self._em.Plus,
            Times: self._em.Times,
            Divide: self._em.Div,
        }

    def _convert_variable(self, variable: Variable) -> UPVariable:
        tt = next(iter(variable.type_tags))
        key = (variable.name, assert_not_none_type(self._types[tt]))
        if key not in self._variables:
            self._variables[key] = UPVariable(
                variable.name, assert_not_none_type(self._types[tt])
            )
        return self._variables[key]

    def convert_expression(
        self,
        formula: Formula,
        action_parameters: Dict[str, Parameter],
        quantifier_variables: Dict[str, UPVariable],
    ) -> FNode:
        em = self._em
        stack = [(formula, action_parameters, quantifier_variables)]
        result_stack: List[Any] = []

        while stack:
            (
                current_formula,
                current_action_parameters,
                current_quantifier_variables,
            ) = stack.pop()

            if isinstance(current_formula, NumericValue):
                formula_value = Fraction(current_formula.value)
                if formula_value.denominator == 1:
                    result_stack.append(em.Int(formula_value.numerator))
                else:
                    result_stack.append(em.Real(formula_value))
            elif type(current_formula) in self._direct_matching_expressions:
                for operand in current_formula.operands:
                    stack.append(
                        (
                            operand,
                            current_action_parameters,
                            current_quantifier_variables,
                        )
                    )
                result_stack.append(
                    (type(current_formula), len(current_formula.operands))
                )
            elif isinstance(current_formula, Not):
                stack.append(
                    (
                        current_formula.argument,
                        current_action_parameters,
                        current_quantifier_variables,
                    )
                )
                result_stack.append(Not)
            elif isinstance(current_formula, Constant):
                result_stack.append(em.ObjectExp(self._objects[current_formula.name]))
            elif isinstance(current_formula, (Predicate, NumericFunction)):
                for term in current_formula.terms:
                    stack.append(
                        (term, current_action_parameters, current_quantifier_variables)
                    )
                result_stack.append((current_formula.name, len(current_formula.terms)))
            elif isinstance(current_formula, DerivedPredicate):
                raise UPUnsupportedProblemTypeError(
                    f"Derived predicate {current_formula} not supported"
                )
            elif isinstance(current_formula, EqualToPredicate):
                stack.append(
                    (
                        current_formula.left,
                        current_action_parameters,
                        current_quantifier_variables,
                    )
                )
                stack.append(
                    (
                        current_formula.right,
                        current_action_parameters,
                        current_quantifier_variables,
                    )
                )
                result_stack.append(EqualToPredicate)
            elif isinstance(current_formula, ForallCondition):
                up_variables = [
                    self._convert_variable(v) for v in current_formula.variables
                ]
                new_quantifier_variables = current_quantifier_variables.copy()
                for v in up_variables:
                    new_quantifier_variables[v.name] = v
                stack.append(
                    (
                        current_formula.condition,
                        current_action_parameters,
                        new_quantifier_variables,
                    )
                )
                result_stack.append((ForallCondition, up_variables))
            elif isinstance(current_formula, ExistsCondition):
                up_variables = [
                    self._convert_variable(v) for v in current_formula.variables
                ]
                new_quantifier_variables = current_quantifier_variables.copy()
                for v in up_variables:
                    new_quantifier_variables[v.name] = v
                stack.append(
                    (
                        current_formula.condition,
                        current_action_parameters,
                        new_quantifier_variables,
                    )
                )
                result_stack.append((ExistsCondition, up_variables))
            elif isinstance(current_formula, Variable):
                if current_formula.name in current_quantifier_variables:
                    result_stack.append(
                        em.VariableExp(
                            current_quantifier_variables[current_formula.name]
                        )
                    )
                elif current_formula.name in current_action_parameters:
                    result_stack.append(
                        em.ParameterExp(current_action_parameters[current_formula.name])
                    )
                else:
                    raise UPUnsupportedProblemTypeError(
                        f"Variable {current_formula.name} not found in action parameters or quantifier variables"
                    )
            else:
                raise UPUnsupportedProblemTypeError(f"{current_formula} not supported!")

        # Second pass to construct the final expression
        final_stack: List[FNode] = []
        while result_stack:
            item = result_stack.pop()
            if isinstance(item, tuple):
                if item[0] in [ForallCondition, ExistsCondition]:
                    op_type, up_variables = item
                    condition = final_stack.pop()
                    if op_type == ForallCondition:
                        final_stack.append(em.Forall(condition, *up_variables))
                    else:
                        final_stack.append(em.Exists(condition, *up_variables))
                elif isinstance(item[0], str):
                    name, arity = item
                    args = [final_stack.pop() for _ in range(arity)]
                    final_stack.append(self._fluents[name](*reversed(args)))
                else:
                    op_type, arity = item
                    args = [final_stack.pop() for _ in range(arity)]
                    if op_type == Minus and len(args) == 1:
                        args.append(0)
                    final_stack.append(
                        self._direct_matching_expressions[op_type](*reversed(args))
                    )
            elif item == Not:
                arg = final_stack.pop()
                final_stack.append(em.Not(arg))
            elif item == EqualToPredicate:
                right = final_stack.pop()
                left = final_stack.pop()
                final_stack.append(em.Equals(left, right))
            else:
                final_stack.append(item)

        result = final_stack.pop()
        assert isinstance(result, FNode)
        return result


class AIPDDLConverter:
    """
    Through the `convert` method creates a :class:`~unified_planning.model.Problem`
    from the ai planning pddl Domain and Problem classes.

    If the given problem is `None` an incomplete UP Problem will be returned.

    :param domain: the ai planning pddl Domain to convert.
    :param problem: the ai planning pddl Problem to convert; can be `None`.
    :param environment: the environment in which the `UP Problem` is created,
        defaults to `None`.
    :return: the `UP Problem` parsed from the given ai planning `PDDL` Domain
        and Problem.
    """

    def __init__(
        self,
        domain: Domain,
        problem: Optional[Problem],
        environment: Optional[Environment] = None,
    ):
        self._environment = get_environment(environment)
        self._em: ExpressionManager = self._environment.expression_manager
        self._tm: TypeManager = self._environment.type_manager
        self._domain = domain
        self._problem = problem
        self._up_problem: Optional[UPProblem] = None
        self._types: Dict[name, Optional[Type]] = {}
        if self._has_object_user_type():
            self._types["object"] = self._tm.UserType("object")
        else:
            self._types["object"] = None
        self._fluents: Dict[name, Fluent] = {}
        self._objects: Dict[name, Object] = {}
        self._expression_converter: Optional[_ExpressionConverter] = None
        self._has_action_costs = False
        self._action_costs: Optional[Dict[str, UPExpression]] = None

    def _has_object_user_type(self) -> bool:
        objects: Iterator[Constant] = (
            self._domain.constants
            if self._problem is None
            else chain(self._domain.constants, self._problem.objects)
        )

        # extracts all the parameters of the fluents
        def get_all_fluents_terms() -> Iterator[Term]:
            for fluent in chain(self._domain.predicates, self._domain.functions):
                for term in fluent.terms:
                    yield term

        # extracts all the parameters of the actions
        def get_all_actions_params() -> Iterator[Variable]:
            for action in self._domain.actions:
                for param in action.parameters:
                    yield param

        for typed_element in chain(
            objects, get_all_fluents_terms(), get_all_actions_params()
        ):
            if "object" in typed_element.type_tags:
                return True

        return False

    def _up_type(self, type_name: name) -> Optional[Type]:
        return self._types[type_name]

    def _convert_type(self, type_name: name, type_father: Optional[Type]):
        ut = self._tm.UserType(type_name, type_father)
        self._types[type_name] = ut

    def _convert_types(self):
        # remaining_types contains the type that were not possible to convert
        # because the father_type was not converted yet. So those are stored
        # and populated later
        remaining_types = []
        for type_name, type_father_name in self._domain.types.items():
            if type_father_name is None or type_father_name in self._types:
                type_father = self._types.get(type_father_name)
                self._convert_type(type_name, type_father)
            else:
                remaining_types.append((type_name, type_father_name))

        # counter to avoid infinite loops; should never reach 0 unless a
        # type_father of a type is not defined
        chances = len(remaining_types)
        while remaining_types and chances > 0:
            type_name, type_father_name = remaining_types.pop(0)
            type_father = self._types.get(type_father_name)
            if type_father is not None:
                self._convert_type(type_name, type_father)
                chances = len(remaining_types)
            else:
                remaining_types.append((type_name, type_father_name))
                chances -= 1

        if remaining_types:
            raise UPUnsupportedProblemTypeError(
                f"Could not convert types: {remaining_types}"
            )

    def _variable_type(self, variable: Variable) -> Type:
        if len(variable.type_tags) == 0:
            raise UPUnsupportedProblemTypeError(
                f"Variable {variable.name} has no type tag"
            )
        if len(variable.type_tags) != 1:
            raise UPUnsupportedProblemTypeError(
                f"Variable {variable.name} has more than one type tag"
            )
        tt = next(iter(variable.type_tags))
        return assert_not_none_type(self._up_type(tt))

    def _variable_to_param(self, variable: Variable) -> Parameter:
        return Parameter(variable.name, self._variable_type(variable))

    def _convert_predicate_to_fluent(self, predicate: Predicate):
        assert self._up_problem is not None
        params = OrderedDict((v.name, self._variable_type(v)) for v in predicate.terms)
        fluent = Fluent(predicate.name, self._tm.BoolType(), **params)
        self._fluents[predicate.name] = fluent
        self._up_problem.add_fluent(fluent, default_initial_value=self._em.FALSE())

    def _problem_has_minimize_total_cost_metric(self) -> bool:
        assert self._problem is not None
        metric = self._problem.metric
        if metric is None:
            return False

        return (
            metric.optimization == Metric.MINIMIZE
            and isinstance(metric.expression, NumericFunction)
            and metric.expression.name == "total-cost"
            and metric.expression.arity == 0
        )

    def _convert_function_to_fluent(self, function: NumericFunction):
        assert self._up_problem is not None
        if (
            function.name == "total-cost"
            and function.arity == 0
            and (
                self._problem is None or self._problem_has_minimize_total_cost_metric()
            )
        ):
            self._has_action_costs = True
            self._action_costs = {}
            return
        params = OrderedDict((v.name, self._variable_type(v)) for v in function.terms)
        f = Fluent(function.name, self._tm.RealType(), **params)
        self._fluents[function.name] = f
        self._up_problem.add_fluent(f, default_initial_value=self._em.Int(0))

    def _convert_fluents(self):
        for pred in self._domain.predicates:
            self._convert_predicate_to_fluent(pred)
        for func in self._domain.functions:
            self._convert_function_to_fluent(func)

    def _add_object(self, obj: Constant):
        assert self._up_problem is not None
        if obj.type_tags is None:
            raise UPUnsupportedProblemTypeError(f"Object {obj.name} has no type tag")
        obj = Object(obj.name, assert_not_none_type(self._up_type(obj.type_tag)))
        self._objects[obj.name] = obj
        self._up_problem.add_object(obj)

    def _convert_constants(self):
        for obj in self._domain.constants:
            self._add_object(obj)

    def _convert_objects(self):
        assert self._problem is not None
        for obj in self._problem.objects:
            self._add_object(obj)

    def _convert_effects(
        self,
        action_parameters_expression: Dict[str, Parameter],
        effect: Effect,
        action_name: str,
    ) -> Iterator[UPEffect]:
        assert self._expression_converter is not None
        stack: List[Tuple[Effect, Dict[str, UPVariable], FNode]] = [
            (effect, {}, self._em.TRUE())
        ]

        while stack:
            (
                current_effect,
                current_quantifier_variables,
                current_condition,
            ) = stack.pop()

            # one to one effect conversion
            if isinstance(current_effect, Predicate):
                fluent = self._expression_converter.convert_expression(
                    current_effect,
                    action_parameters_expression,
                    current_quantifier_variables,
                )
                yield UPEffect(
                    fluent,
                    self._em.TRUE(),
                    current_condition,
                    forall=current_quantifier_variables.values(),
                )
            elif isinstance(current_effect, Not):
                fluent = self._expression_converter.convert_expression(
                    current_effect.argument,
                    action_parameters_expression,
                    current_quantifier_variables,
                )
                yield UPEffect(
                    fluent,
                    self._em.TRUE(),
                    current_condition,
                    forall=current_quantifier_variables.values(),
                )
            elif isinstance(current_effect, Assign):
                fluent = self._expression_converter.convert_expression(
                    current_effect.operands[0],
                    action_parameters_expression,
                    current_quantifier_variables,
                )
                value = self._expression_converter.convert_expression(
                    current_effect.operands[1],
                    action_parameters_expression,
                    current_quantifier_variables,
                )
                yield UPEffect(
                    fluent,
                    value,
                    current_condition,
                    forall=current_quantifier_variables.values(),
                )
            elif isinstance(current_effect, Increase):
                pddl_fluent = current_effect.operands[0]
                pddl_value = current_effect.operands[1]
                # check if action_cost is increased
                if (
                    isinstance(pddl_fluent, NumericFunction)
                    and pddl_fluent.name == "total-cost"
                    and pddl_fluent.arity == 0
                ):
                    assert self._has_action_costs
                    assert self._action_costs is not None
                    assert current_quantifier_variables == {}
                    assert current_condition == self._em.TRUE()
                    self._action_costs[
                        action_name
                    ] = self._expression_converter.convert_expression(
                        pddl_value,
                        action_parameters_expression,
                        current_quantifier_variables,
                    )
                else:
                    fluent = self._expression_converter.convert_expression(
                        pddl_fluent,
                        action_parameters_expression,
                        current_quantifier_variables,
                    )
                    assert fluent.is_fluent_exp()
                    value = self._expression_converter.convert_expression(
                        pddl_value,
                        action_parameters_expression,
                        current_quantifier_variables,
                    )
                    yield UPEffect(
                        fluent,
                        value,
                        current_condition,
                        EffectKind.INCREASE,
                        current_quantifier_variables.values(),
                    )
            elif isinstance(current_effect, Decrease):
                pddl_fluent = current_effect.operands[0]
                pddl_value = current_effect.operands[1]
                # check if it is decreasing the action cost
                if (
                    isinstance(pddl_fluent, NumericFunction)
                    and pddl_fluent.name == "total-cost"
                    and pddl_fluent.arity == 0
                ):
                    assert self._has_action_costs
                    assert self._action_costs is not None
                    assert current_quantifier_variables == {}
                    assert current_condition == self._em.TRUE()
                    positive_value = self._expression_converter.convert_expression(
                        pddl_value,
                        action_parameters_expression,
                        current_quantifier_variables,
                    )
                    negative_value = self._em.Minus(0, positive_value).simplify()
                    self._action_costs[action_name] = negative_value
                else:
                    fluent = self._expression_converter.convert_expression(
                        pddl_fluent,
                        action_parameters_expression,
                        current_quantifier_variables,
                    )
                    assert fluent.is_fluent_exp()
                    value = self._expression_converter.convert_expression(
                        pddl_value,
                        action_parameters_expression,
                        current_quantifier_variables,
                    )
                    yield UPEffect(
                        fluent,
                        value,
                        current_condition,
                        EffectKind.DECREASE,
                        current_quantifier_variables.values(),
                    )
            # one to (possibly) many effects conversion; add all sub_effects to
            # stack with additional info (condition or quantifier variables)
            elif isinstance(current_effect, When):
                assert current_condition == self._em.TRUE()
                new_condition = self._expression_converter.convert_expression(
                    current_effect.condition,
                    action_parameters_expression,
                    current_quantifier_variables,
                )
                stack.append(
                    (current_effect.effect, current_quantifier_variables, new_condition)
                )
            elif isinstance(current_effect, Forall):
                new_quantifier_variables = current_quantifier_variables.copy()
                for v in current_effect.variables:
                    new_quantifier_variables[v.name] = UPVariable(
                        v.name, self._variable_type(v)
                    )
                stack.append(
                    (current_effect.effect, new_quantifier_variables, current_condition)
                )
            elif isinstance(current_effect, And):
                for sub_effect in current_effect.operands:
                    stack.append(
                        (sub_effect, current_quantifier_variables, current_condition)
                    )
            else:
                raise UPUnsupportedProblemTypeError(
                    f"Effect {current_effect} of type {type(current_effect)} not supported"
                )

    def _convert_action(self, action: Action):
        assert self._up_problem is not None
        assert self._expression_converter is not None
        action_parameters = OrderedDict(
            (v.name, self._variable_type(v)) for v in action.parameters
        )
        action_parameters_expression = {
            p_name: Parameter(p_name, p_type)
            for p_name, p_type in action_parameters.items()
        }

        up_action = InstantaneousAction(action.name, **action_parameters)

        up_action.add_precondition(
            self._expression_converter.convert_expression(
                action.precondition, action_parameters_expression, {}
            )
        )

        for e in self._convert_effects(
            action_parameters_expression, action.effect, action.name
        ):
            up_action._add_effect_instance(e)

        self._up_problem.add_action(up_action)

    def _convert_initial_values(self):
        assert self._up_problem is not None
        assert self._expression_converter is not None
        assert self._problem is not None
        for init in self._problem.init:
            if (
                isinstance(init, EqualToFunction)
                and isinstance(init.operands[0], NumericFunction)
                and init.operands[0].name == "total-cost"
                and init.operands[0].arity == 0
            ):
                assert self._has_action_costs
                assert self._action_costs is not None
                continue

            init_expr = self._expression_converter.convert_expression(init, {}, {})
            if init_expr.is_fluent_exp():
                self._up_problem.set_initial_value(init_expr, self._em.TRUE())
            elif init_expr.is_equals():
                fluent = init_expr.arg(0)
                value = init_expr.arg(1)
                if value.is_fluent_exp():
                    fluent, value = value, fluent
                assert fluent.is_fluent_exp()
                self._up_problem.set_initial_value(fluent, value)
            else:
                raise UPUnsupportedProblemTypeError(
                    f"Initial value {init_expr} not supported"
                )

    def _convert_goals(self):
        assert self._up_problem is not None
        assert self._expression_converter is not None
        assert self._problem is not None
        self._up_problem.add_goal(
            self._expression_converter.convert_expression(self._problem.goal, {}, {})
        )

    def _add_quality_metric(self):
        assert self._up_problem is not None
        if self._has_action_costs:
            action_costs: Dict[UPAction, UPExpression] = {}
            assert self._action_costs is not None

            is_minimize_sequential_plan = True
            cost_1_set = {self._em.Int(1), self._em.Real(Fraction(1))}
            for action in self._up_problem.actions:
                cost = self._action_costs.get(action.name)
                if cost not in cost_1_set:
                    is_minimize_sequential_plan = False
            if is_minimize_sequential_plan:
                self._up_problem.add_quality_metric(
                    MinimizeSequentialPlanLength(self._environment)
                )
            else:
                for action_name, cost in self._action_costs.items():
                    action_costs[self._up_problem.action(action_name)] = cost
                self._up_problem.add_quality_metric(
                    MinimizeActionCosts(action_costs, self._em.Int(0))
                )
        elif self._problem is not None:
            metric = self._problem.metric
            if metric is not None:
                assert self._expression_converter is not None
                expression = self._expression_converter.convert_expression(
                    metric.expression, {}, {}
                )
                if metric.optimization == Metric.MINIMIZE:
                    up_metric: Union[
                        MinimizeExpressionOnFinalState, MaximizeExpressionOnFinalState
                    ] = MinimizeExpressionOnFinalState(expression)
                else:
                    up_metric = MaximizeExpressionOnFinalState(expression)
                self._up_problem.add_quality_metric(up_metric)

    def convert(self) -> UPProblem:
        """
        Converts the AI planning PDDL domains and problems given at the constructor
        and returns the equivalent UP Problem.

        :return: the unified_planning Problem equivalent to the AI planning PDDL domain
            and problem given at constructor
        """
        # if problem is cached, return it
        if self._up_problem is not None:
            problem_clone = self._up_problem.clone()
            return problem_clone

        # create and populate the problem
        problem_name = (
            self._domain.name if self._problem is None else self._problem.name
        )
        self._up_problem = UPProblem(problem_name, self._environment)

        # domain parsing
        self._convert_types()
        self._convert_fluents()
        self._convert_constants()
        self._convert_objects()

        expression_converter = _ExpressionConverter(
            self._em, self._types, self._fluents, self._objects
        )
        self._expression_converter = expression_converter

        for action in self._domain.actions:
            self._convert_action(action)

        self._add_quality_metric()

        # problem parsing
        if self._problem is not None:
            self._convert_initial_values()
            self._convert_goals()
        return self._up_problem


def check_ai_pddl_requirements(requirements: List[str]) -> bool:
    """
    Checks that all the given requirements are supported by the ai pddl parser.

    :param requirements: The `List` of requirements specified in the domain that
        is tested.
    :raises UPUnsupportedProblemTypeError: if the given requirements specify
        features that are not supported by the unified planning
    :return: `True` if all the specified requirements are supported by the ai
        planning pddl parser, `False` otherwise.
    """
    ai_pddl_planning_supported_requirements = {
        ":strips",
        ":typing",
        ":negative-preconditions",
        ":disjunctive-preconditions",
        ":equality",
        ":existential-preconditions",
        ":universal-preconditions",
        ":quantified-preconditions",
        ":conditional-effects",
        ":numeric-fluents",
        ":non-deterministic",
        ":adl",
        ":action-costs",
    }
    ai_pddl_planning_supported_requirements_not_up_supported = {
        ":derived-predicates",
    }
    non_up_supported_requirements = (
        ai_pddl_planning_supported_requirements_not_up_supported.intersection(
            requirements
        )
    )
    if non_up_supported_requirements:
        unsupported_req_str = ", ".join(non_up_supported_requirements)
        raise UPUnsupportedProblemTypeError(
            f"Problem requirements contain unsupported requirements: {unsupported_req_str}"
        )
    return all(req in ai_pddl_planning_supported_requirements for req in requirements)


def convert_problem_from_ai_pddl(
    domain: Domain,
    problem: Optional[Problem],
    environment: Optional[Environment] = None,
) -> UPProblem:
    """
    Creates a :class:`~unified_planning.model.Problem` from the ai planning pddl
    Domain and Problem classes.

    If the given problem is `None` an incomplete UP Problem will be returned.

    :param domain: the ai planning pddl Domain to convert.
    :param problem: the ai planning pddl Problem to convert; can be `None`.
    :param environment: the environment in which the `UP Problem` is created,
        defaults to `None`.
    :return: the `UP Problem` parsed from the given ai planning `PDDL` Domain
        and Problem.
    """
    converter = AIPDDLConverter(domain, problem, get_environment(environment))
    up_problem = converter.convert()
    return up_problem
