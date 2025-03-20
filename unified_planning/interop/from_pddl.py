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
import re

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
from warnings import warn

from pddl import parse_domain, parse_problem  # type: ignore
from pddl.parser.domain import DomainParser  # type: ignore
from pddl.parser.problem import ProblemParser  # type: ignore
from pddl.logic.base import Formula, And, Or, Not, Imply, ForallCondition, ExistsCondition  # type: ignore
from pddl.logic.effects import When, Forall, Effect  # type: ignore
from pddl.logic.functions import NumericFunction, BinaryFunction, Increase, Decrease, NumericValue, EqualTo as EqualToFunction, Assign, LesserThan, LesserEqualThan, GreaterThan, GreaterEqualThan, Minus, Plus, Times, Divide, Metric  # type: ignore
from pddl.logic.predicates import DerivedPredicate, EqualTo as EqualToPredicate, Predicate  # type: ignore
from pddl.logic.terms import Constant, Variable  # type: ignore
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
        self.types = types
        self.fluents = fluents
        self.objects = objects
        self.em = expression_manager
        self.variables: Dict[Tuple[str, Type], UPVariable] = {}
        self.direct_matching_expressions: Dict[
            TypingType[BinaryFunction], Callable[..., FNode]
        ] = {
            And: self.em.And,
            Or: self.em.Or,
            Imply: self.em.Implies,
            EqualToFunction: self.em.Equals,
            LesserThan: self.em.LT,
            LesserEqualThan: self.em.LE,
            GreaterThan: self.em.GT,
            GreaterEqualThan: self.em.GE,
            Minus: self.em.Minus,
            Plus: self.em.Plus,
            Times: self.em.Times,
            Divide: self.em.Div,
        }

    def convert_variable(self, variable: Variable) -> UPVariable:
        tt = next(iter(variable.type_tags))
        key = (variable.name, assert_not_none_type(self.types[tt]))
        if key not in self.variables:
            self.variables[key] = UPVariable(
                variable.name, assert_not_none_type(self.types[tt])
            )
        return self.variables[key]

    def convert_expression(
        self,
        formula: Formula,
        action_parameters: Dict[str, Parameter],
        quantifier_variables: Dict[str, UPVariable],
    ) -> FNode:
        em = self.em
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
                    result_stack.append(em.Real(Fraction(current_formula.value)))
            elif type(current_formula) in self.direct_matching_expressions:
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
                result_stack.append(em.ObjectExp(self.objects[current_formula.name]))
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
                    self.convert_variable(v) for v in current_formula.variables
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
                    self.convert_variable(v) for v in current_formula.variables
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
                    final_stack.append(self.fluents[name](*reversed(args)))
                else:
                    op_type, arity = item
                    args = [final_stack.pop() for _ in range(arity)]
                    final_stack.append(
                        self.direct_matching_expressions[op_type](*reversed(args))
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
    def __init__(
        self,
        domain: Domain,
        problem: Optional[Problem],
        environment: Optional[Environment] = None,
    ):
        self.domain = domain
        self.problem = problem
        problem_name = domain.name if problem is None else problem.name
        self.up_problem = UPProblem(problem_name)
        self.types: Dict[name, Optional[Type]] = {"object": None}
        self.fluents: Dict[name, Fluent] = {}
        self.objects: Dict[name, Object] = {}
        self.expression_converter: Optional[_ExpressionConverter] = None
        self.environment = get_environment(environment)
        self.em: ExpressionManager = self.environment.expression_manager
        self.tm: TypeManager = self.environment.type_manager
        self.has_action_costs = False
        self.action_costs: Optional[Dict[str, UPExpression]] = None

    def up_type(self, type_name: name) -> Optional[Type]:
        return self.types[type_name]

    def convert_type(self, type_name: name, type_father: Optional[Type]):
        ut = self.tm.UserType(type_name, type_father)
        self.types[type_name] = ut

    def convert_types(self):
        remaining_types = []
        for type_name, type_father_name in self.domain.types.items():
            if type_father_name is None or type_father_name in self.types:
                type_father = self.types.get(type_father_name)
                self.convert_type(type_name, type_father)
            else:
                remaining_types.append((type_name, type_father_name))
        chances = len(remaining_types)
        while remaining_types and chances > 0:
            type_name, type_father_name = remaining_types.pop(0)
            type_father = self.types.get(type_father_name)
            if type_father is not None:
                self.convert_type(type_name, type_father)
                chances = len(remaining_types)
            else:
                remaining_types.append((type_name, type_father_name))
                chances -= 1

        if remaining_types:
            raise UPUnsupportedProblemTypeError(
                f"Could not convert types: {remaining_types}"
            )

    def variable_type(self, variable: Variable) -> Type:
        if len(variable.type_tags) == 0:
            raise UPUnsupportedProblemTypeError(
                f"Variable {variable.name} has no type tag"
            )
        if len(variable.type_tags) != 1:
            raise UPUnsupportedProblemTypeError(
                f"Variable {variable.name} has more than one type tag"
            )
        tt = next(iter(variable.type_tags))
        return assert_not_none_type(self.up_type(tt))

    def variable_to_param(self, variable: Variable) -> Parameter:
        return Parameter(variable.name, self.variable_type(variable))

    def convert_predicate(self, predicate: Predicate):
        params = OrderedDict((v.name, self.variable_type(v)) for v in predicate.terms)
        f = Fluent(predicate.name, self.tm.BoolType(), **params)
        self.fluents[predicate.name] = f
        self.up_problem.add_fluent(f, default_initial_value=self.em.FALSE())

    def problem_has_minimize_total_cost_metric(self) -> bool:
        assert self.problem is not None
        metric = self.problem.metric
        if metric is None:
            return False

        return (
            metric.optimization == Metric.MINIMIZE
            and isinstance(metric.expression, NumericFunction)
            and metric.expression.name == "total-cost"
            and metric.expression.arity == 0
        )

    def convert_function(self, function: NumericFunction):
        if (
            function.name == "total-cost"
            and function.arity == 0
            and (self.problem is None or self.problem_has_minimize_total_cost_metric())
        ):
            self.has_action_costs = True
            self.action_costs = {}
            return
        params = OrderedDict((v.name, self.variable_type(v)) for v in function.terms)
        f = Fluent(function.name, self.tm.RealType(), **params)
        self.fluents[function.name] = f
        self.up_problem.add_fluent(f, default_initial_value=self.em.Int(0))

    def convert_fluents(self):
        for pred in self.domain.predicates:
            self.convert_predicate(pred)
        for func in self.domain.functions:
            self.convert_function(func)

    def add_object(self, obj: Constant):
        if obj.type_tags is None:
            raise UPUnsupportedProblemTypeError(f"Object {obj.name} has no type tag")
        # TODO understand what to do with objects of type "object"
        # Probably a flag "has_object_type" should be added
        obj = Object(obj.name, assert_not_none_type(self.up_type(obj.type_tag)))
        self.objects[obj.name] = obj
        self.up_problem.add_object(obj)

    def convert_constants(self):
        for obj in self.domain.constants:
            self.add_object(obj)

    def convert_objects(self):
        assert self.problem is not None
        for obj in self.problem.objects:
            self.add_object(obj)

    def convert_effects(
        self,
        action_parameters_expression: Dict[str, Parameter],
        effect: Effect,
        quantifier_variables: Dict[str, UPVariable],
        condition: FNode,
        action_name: str,
    ) -> Iterator[UPEffect]:
        assert self.expression_converter is not None
        if isinstance(effect, Predicate):
            fluent = self.expression_converter.convert_expression(
                effect, action_parameters_expression, quantifier_variables
            )
            yield UPEffect(
                fluent,
                self.em.TRUE(),
                condition,
                forall=tuple(quantifier_variables.values()),
            )
        elif isinstance(effect, Not):
            fluent = self.expression_converter.convert_expression(
                effect.argument, action_parameters_expression, quantifier_variables
            )
            yield UPEffect(
                fluent,
                self.em.FALSE(),
                condition,
                forall=tuple(quantifier_variables.values()),
            )
        elif isinstance(effect, Assign):
            fluent = self.expression_converter.convert_expression(
                effect.operands[0], action_parameters_expression, quantifier_variables
            )
            value = self.expression_converter.convert_expression(
                effect.operands[1], action_parameters_expression, quantifier_variables
            )
            yield UPEffect(
                fluent,
                value,
                condition,
                forall=tuple(quantifier_variables.values()),
            )
        elif isinstance(effect, When):
            assert condition == self.em.TRUE()
            new_condition = self.expression_converter.convert_expression(
                effect.condition, action_parameters_expression, quantifier_variables
            )
            for e in self.convert_effects(
                action_parameters_expression,
                effect.effect,
                quantifier_variables,
                new_condition,
                action_name,
            ):
                yield e
        elif isinstance(effect, Forall):
            new_quantifier_variables = quantifier_variables.copy()
            for v in effect.variables:
                new_quantifier_variables[v.name] = UPVariable(
                    v.name, self.variable_type(v)
                )
            for e in self.convert_effects(
                action_parameters_expression,
                effect.effect,
                new_quantifier_variables,
                condition,
                action_name,
            ):
                yield e
        elif isinstance(effect, And):
            for sub_effect in effect.operands:
                for e in self.convert_effects(
                    action_parameters_expression,
                    sub_effect,
                    quantifier_variables,
                    condition,
                    action_name,
                ):
                    yield e
        elif isinstance(effect, Increase):
            pddl_fluent = effect.operands[0]
            pddl_value = effect.operands[1]
            if (
                isinstance(pddl_fluent, NumericFunction)
                and pddl_fluent.name == "total-cost"
            ):
                assert self.has_action_costs
                assert self.action_costs is not None
                assert quantifier_variables == {}
                assert condition == self.em.TRUE()
                self.action_costs[
                    action_name
                ] = self.expression_converter.convert_expression(
                    pddl_value, action_parameters_expression, quantifier_variables
                )
            else:
                fluent = self.expression_converter.convert_expression(
                    pddl_fluent, action_parameters_expression, quantifier_variables
                )
                assert fluent.is_fluent_exp()
                value = self.expression_converter.convert_expression(
                    pddl_value, action_parameters_expression, quantifier_variables
                )
                yield UPEffect(
                    fluent,
                    value,
                    condition,
                    kind=EffectKind.INCREASE,
                    forall=tuple(quantifier_variables.values()),
                )
        elif isinstance(effect, Decrease):
            pddl_fluent = effect.operands[0]
            pddl_value = effect.operands[1]
            fluent = self.expression_converter.convert_expression(
                pddl_fluent, action_parameters_expression, quantifier_variables
            )
            assert fluent.is_fluent_exp()
            value = self.expression_converter.convert_expression(
                pddl_value, action_parameters_expression, quantifier_variables
            )
            yield UPEffect(
                fluent,
                value,
                condition,
                kind=EffectKind.DECREASE,
                forall=tuple(quantifier_variables.values()),
            )
        else:
            raise UPUnsupportedProblemTypeError(
                f"Effect {effect} of type {type(effect)} not supported"
            )

    def convert_action(self, action: Action):
        assert self.expression_converter is not None
        action_parameters = OrderedDict(
            (v.name, self.variable_type(v)) for v in action.parameters
        )
        action_parameters_expression = {
            p_name: Parameter(p_name, p_type)
            for p_name, p_type in action_parameters.items()
        }

        up_action = InstantaneousAction(action.name, **action_parameters)

        up_action.add_precondition(
            self.expression_converter.convert_expression(
                action.precondition, action_parameters_expression, {}
            )
        )

        for e in self.convert_effects(
            action_parameters_expression, action.effect, {}, self.em.TRUE(), action.name
        ):
            up_action._add_effect_instance(e)

        self.up_problem.add_action(up_action)

    def convert_initial_values(self):
        assert self.expression_converter is not None
        assert self.problem is not None
        for init in self.problem.init:
            if (
                isinstance(init, EqualToFunction)
                and isinstance(init.operands[0], NumericFunction)
                and init.operands[0].name == "total-cost"
            ):
                assert self.has_action_costs
                assert self.action_costs is not None
                continue

            init_expr = self.expression_converter.convert_expression(init, {}, {})
            if init_expr.is_fluent_exp():
                self.up_problem.set_initial_value(init_expr, self.em.TRUE())
            elif init_expr.is_equals():
                fluent = init_expr.arg(0)
                value = init_expr.arg(1)
                if value.is_fluent_exp():
                    fluent, value = value, fluent
                assert fluent.is_fluent_exp()
                self.up_problem.set_initial_value(fluent, value)
            else:
                raise UPUnsupportedProblemTypeError(
                    f"Initial value {init_expr} not supported"
                )

    def convert_goals(self):
        assert self.expression_converter is not None
        assert self.problem is not None
        self.up_problem.add_goal(
            self.expression_converter.convert_expression(self.problem.goal, {}, {})
        )

    def add_quality_metric(self):
        if self.has_action_costs:
            action_costs: Dict[UPAction, UPExpression] = {}
            assert self.action_costs is not None
            for action_name, cost in self.action_costs.items():
                action_costs[self.up_problem.action(action_name)] = cost
            self.up_problem.add_quality_metric(MinimizeActionCosts(action_costs))
        elif self.problem is not None:
            metric = self.problem.metric
            if metric is not None:
                assert self.expression_converter is not None
                expression = self.expression_converter.convert_expression(
                    metric.expression, {}, {}
                )
                if metric.optimization == Metric.MINIMIZE:
                    up_metric: Union[
                        MinimizeExpressionOnFinalState, MaximizeExpressionOnFinalState
                    ] = MinimizeExpressionOnFinalState(expression)
                else:
                    up_metric = MaximizeExpressionOnFinalState(expression)
                self.up_problem.add_quality_metric(up_metric)

    def convert(self) -> UPProblem:
        # domain parsing
        self.convert_types()
        self.convert_fluents()
        self.convert_constants()
        self.convert_objects()

        expression_converter = _ExpressionConverter(
            self.em, self.types, self.fluents, self.objects
        )
        self.expression_converter = expression_converter

        for action in self.domain.actions:
            self.convert_action(action)

        self.add_quality_metric()

        # problem parsing
        if self.problem is not None:
            self.convert_initial_values()
            self.convert_goals()
        return self.up_problem


def extract_requirements(domain_str: str) -> List[str]:
    """
    Extract the requirements from the given domain in a List of requirements strings.
    For example if the requirements are `(:requirements :strips :typing)` returns:
    `[":strips", ":typing"]`

    :param domain_str: the domain str from which the requirements have to be extracted.
    :return: The `List[str]` of requirements extracted from the domain.
    """
    requirements_lines = []
    found_requirements = False

    for line in domain_str.splitlines():
        if ":requirements" in line:
            assert not found_requirements
            found_requirements = True
        if found_requirements:
            requirements_lines.append(line)
            if ")" in line:
                break

    requirements_str = " ".join(requirements_lines)
    match = re.search(r"\(:requirements\s+([^)]+)\)", requirements_str)
    if match:
        requirements = match.group(1).split()
        return requirements
    else:
        return []


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


def from_ai_pddl(
    ai_domain_or_domain_str: Union[Domain, str],
    ai_problem_or_problem_str: Optional[Union[Problem, str]],
    environment: Optional[Environment] = None,
) -> UPProblem:
    """
    Creates a :class:`~unified_planning.model.Problem` from the ai planning pddl
    Domain and Problem classes or from their `PDDL` str representations.

    If the given problem is None an incomplete UP Problem will be returned.

    :param ai_domain_or_domain_str: the domain to parse, either in the ai planning
        pddl format or in the pddl string representation.
    :param ai_problem_or_problem_str: the problem to parse, either in the ai planning
        pddl format or in the pddl string representation; can be `None`.
    :param environment: the environment in which the `UP Problem` is created,
        defaults to `None`.
    :return: the `UP Problem` parsed from the given `PDDL` domain and problem.
    """
    domain = (
        ai_domain_or_domain_str
        if isinstance(ai_domain_or_domain_str, Domain)
        else DomainParser()(ai_domain_or_domain_str)
    )
    problem = None
    if ai_problem_or_problem_str is not None:
        problem = (
            ai_problem_or_problem_str
            if isinstance(ai_problem_or_problem_str, Problem)
            else ProblemParser()(ai_problem_or_problem_str)
        )
    converter = AIPDDLConverter(domain, problem, get_environment(environment))
    up_problem = converter.convert()
    return up_problem


def from_ai_pddl_filenames(
    domain_filename: str,
    problem_filename: Optional[str],
    environment: Optional[Environment] = None,
) -> UPProblem:
    """
    Creates a :class:`~unified_planning.model.Problem` from the ai planning pddl
    Domain and Problem classes or from their `PDDL` str representations.

    If the given problem is None an incomplete UP Problem will be returned.

    :param domain_filename: the path to the file containing the domain to parse
        with ai pddl planning and then convert to a `UP Problem`.
    :param problem_filename: the path to the file containing the problem to parse
        with ai pddl planning and then convert to a `UP Problem`; can be `None`.
    :param environment: the environment in which the `UP Problem` is created,
        defaults to `None`.
    :return: the `UP Problem` parsed from the given `PDDL` domain and problem.
    """
    domain = parse_domain(domain_filename)
    problem = parse_problem(problem_filename) if problem_filename is not None else None
    up_problem = from_ai_pddl(domain, problem, environment)
    return up_problem
