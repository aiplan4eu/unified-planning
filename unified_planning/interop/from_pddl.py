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

import re

from fractions import Fraction
from typing import (
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    OrderedDict,
    Tuple,
    Type as TypingType,
)
from warnings import warn

from pddl import parse_domain, parse_problem  # type: ignore
from pddl.logic.base import Formula, And, Or, OneOf, Not, Imply, ForallCondition, ExistsCondition  # type: ignore
from pddl.logic.effects import When, Forall, Effect  # type: ignore
from pddl.logic.functions import NumericFunction, BinaryFunction, Increase, Decrease, NumericValue, EqualTo as EqualToFunction, Assign, LesserThan, LesserEqualThan, GreaterThan, GreaterEqualThan, Minus, Plus, Times, Divide  # type: ignore
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
)
from unified_planning.model.type_manager import TypeManager
from unified_planning.model.expression import ExpressionManager
from unified_planning.environment import get_environment
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPUnsupportedProblemTypeError,
    UPAIPDDLPlanningError,
)
from unified_planning.io import PDDLReader


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
        if isinstance(formula, NumericValue):
            formula_value = Fraction(formula.value)
            if formula_value.denominator == 1:
                return em.Int(formula_value.numerator)
            return em.Real(Fraction(formula.value))
        elif type(formula) in self.direct_matching_expressions:
            args = [
                self.convert_expression(arg, action_parameters, quantifier_variables)
                for arg in formula.operands
            ]
            return self.direct_matching_expressions[type(formula)](*args)
        elif isinstance(formula, Not):
            return em.Not(
                self.convert_expression(
                    formula.argument, action_parameters, quantifier_variables
                )
            )
        elif isinstance(formula, Constant):
            return em.ObjectExp(self.objects[formula.name])
        elif isinstance(formula, (Predicate, NumericFunction)):
            children = [
                self.convert_expression(f, action_parameters, quantifier_variables)
                for f in formula.terms
            ]
            return self.fluents[formula.name](*children)
        elif isinstance(formula, DerivedPredicate):
            raise UPUnsupportedProblemTypeError(
                f"Derived predicate {formula} not supported"
            )
        elif isinstance(formula, EqualToPredicate):
            left = self.convert_expression(
                formula.left, action_parameters, quantifier_variables
            )
            right = self.convert_expression(
                formula.right, action_parameters, quantifier_variables
            )
            return em.Equals(left, right)
        elif isinstance(formula, ForallCondition):
            up_variables = [self.convert_variable(v) for v in formula.variables]
            new_quantifier_variables = quantifier_variables.copy()
            for v in up_variables:
                new_quantifier_variables[v.name] = v
            return em.Forall(
                self.convert_expression(
                    formula.condition, action_parameters, new_quantifier_variables
                ),
                *up_variables,
            )
        elif isinstance(formula, ExistsCondition):
            up_variables = [self.convert_variable(v) for v in formula.variables]
            new_quantifier_variables = quantifier_variables.copy()
            for v in up_variables:
                new_quantifier_variables[v.name] = v
            return em.Exists(
                self.convert_expression(
                    formula.condition, action_parameters, new_quantifier_variables
                ),
                *up_variables,
            )
        elif isinstance(formula, Variable):
            if formula.name in quantifier_variables:
                return em.VariableExp(quantifier_variables[formula.name])
            elif formula.name in action_parameters:
                return em.ParameterExp(action_parameters[formula.name])
            else:
                raise UPUnsupportedProblemTypeError(
                    f"Variable {formula.name} not found in action parameters or quantifier variables"
                )

        else:
            raise UPUnsupportedProblemTypeError(f"{formula} not supported!")


class _Converter:
    def __init__(self, domain: Domain, problem: Problem):
        self.domain = domain
        self.problem = problem
        self.up_problem = UPProblem(problem.name)
        self.types: Dict[name, Optional[Type]] = {"object": None}
        self.fluents: Dict[name, Fluent] = {}
        self.objects: Dict[name, Object] = {}
        self.expression_converter: Optional[_ExpressionConverter] = None
        self.environment = get_environment()
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

    def convert_function(self, function: NumericFunction):
        # TODO Understand what is the second part of domain.function (Optional[name_like])
        if function.name == "total-cost":
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
        # TODO Understand what is the second part of domain.function (Optional[name_like])
        for func in self.domain.functions:
            self.convert_function(func)

    def convert_objects(self):
        for obj in self.problem.objects:
            if obj.type_tags is None:
                raise UPUnsupportedProblemTypeError(
                    f"Object {obj.name} has no type tag"
                )
            # TODO understand what to do with objects of type "object"
            # Probably a flag "has_object_type" should be added
            obj = Object(obj.name, assert_not_none_type(self.up_type(obj.type_tag)))
            self.objects[obj.name] = obj
            self.up_problem.add_object(obj)

    def convert_effects(
        self,
        action_parameters_expression: Dict[str, Parameter],
        effect: Effect,
        quantifier_variables: Dict[str, UPVariable],
        condition: FNode,
        action_name: str,
    ) -> Iterator[UPEffect]:
        # TODO EqualTo and NumericFunctions
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
        for init in self.problem.init:
            # print(init)
            # print(type(init))
            # print(isinstance(init, EqualTo))
            if (
                isinstance(init, EqualToFunction)
                and isinstance(init.operands[0], NumericFunction)
                and init.operands[0].name == "total-cost"
            ):
                assert self.has_action_costs
                assert self.action_costs is not None
                continue
            # if isinstance(init, EqualTo):
            #     print(init)
            #     print(type(init.left))

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

    def convert(self) -> UPProblem:
        self.up_problem = UPProblem(self.problem.name)
        self.convert_types()
        self.convert_fluents()
        self.convert_objects()

        expression_converter = _ExpressionConverter(
            self.em, self.types, self.fluents, self.objects
        )
        self.expression_converter = expression_converter

        for action in self.domain.actions:
            self.convert_action(action)

        self.convert_initial_values()
        self.convert_goals()
        self.add_quality_metric()

        return self.up_problem


def convert_problem_from_pddl(domain_path: str, problem_path: str) -> UPProblem:
    try:
        domain = parse_domain(domain_path)
        problem = parse_problem(problem_path)
    except Exception as e:
        raise UPAIPDDLPlanningError(f"Error parsing PDDL: {str(e)}")
    converter = _Converter(domain, problem)
    up_problem = converter.convert()
    return up_problem


def _convert_with_pddl_reader(
    domain_path: str, problem_path: Optional[str]
) -> UPProblem:
    reader = PDDLReader()
    problem = reader.parse_problem(domain_path, problem_path)
    return problem


def _extract_requirements(domain_path: str) -> List[str]:
    requirements_lines = []
    found_requirements = False

    with open(domain_path, "r") as f:
        for line in f:
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


def _check_requirements(requirements: List[str]) -> bool:
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


def from_pddl(
    domain_path: str,
    problem_path: Optional[str],
    force_pddl_reader: bool = False,
    force_ai_planning_reader: bool = False,
    deactivate_fallback: bool = False,
) -> UPProblem:

    if force_pddl_reader or problem_path is None:
        return _convert_with_pddl_reader(domain_path, problem_path)
    if force_ai_planning_reader:
        return convert_problem_from_pddl(domain_path, problem_path)
    requirements = _extract_requirements(domain_path)
    if _check_requirements(requirements):
        try:
            return convert_problem_from_pddl(domain_path, problem_path)
        except UPUnsupportedProblemTypeError as e:
            if deactivate_fallback:
                raise e
            warn(
                f"The problem could not be converted using the AI Planning reader due to an issue in the UP converter: {e}"
            )
        except UPAIPDDLPlanningError as e:
            if deactivate_fallback:
                raise e
            warn(
                f"The problem could not be converted using the AI Planning reader due to an issue in the AI PDDL parser: {e}"
            )
    return _convert_with_pddl_reader(domain_path, problem_path)
