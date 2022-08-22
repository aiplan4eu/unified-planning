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
"""Provides the most used functions in a nicely wrapped API.
This module defines a global environment, so that most methods can be
called without the need to specify an environment or a ExpressionManager.
"""

import sys
import unified_planning as up
import unified_planning.model.types
from unified_planning.environment import get_env
from unified_planning.model import *
from unified_planning.engines import Engine, CompilationKind
from typing import IO, Iterable, List, Union, Dict, Tuple, Optional
from fractions import Fraction


def And(*args: Union[BoolExpression, Iterable[BoolExpression]]) -> FNode:
    """
    Returns a conjunction of terms.
    This function has polymorphic n-arguments:
        - `And(a,b,c)`
        - `And([a,b,c])`
    Restriction: Arguments must be `boolean`.

    :param *args: Either an `Iterable` of `boolean expressions`, like `[a, b, c]`, or an unpacked version
    of it, like `a, b, c`.
    :return: The `AND` expression created.
    """
    return get_env().expression_manager.And(*args)


def Or(*args: Union[BoolExpression, Iterable[BoolExpression]]) -> FNode:
    """
    Returns an disjunction of terms.
    This function has polymorphic n-arguments:
        - `Or(a,b,c)`
        - `Or([a,b,c])`
    Restriction: Arguments must be `boolean`

    :param *args: Either an `Iterable` of `boolean expressions`, like `[a, b, c]`, or an unpacked version
    of it, like `a, b, c`.
    :return: The `OR` expression created.
    """
    return get_env().expression_manager.Or(*args)


def Not(expression: BoolExpression) -> FNode:
    """
    Creates an expression of the form:
        `not expression`
    Restriction: `expression` must be of `boolean type`

    :param expression: The `boolean` expression of which the negation must be created.
    :return: The created `NOT` expression.
    """
    return get_env().expression_manager.Not(expression)


def Implies(left: BoolExpression, right: BoolExpression) -> FNode:
    """
    Creates an expression of the form:
        `left -> right`
    Restriction: `Left` and `Right` must be of `boolean type`

    :param left: The `boolean` expression acting as the premise of the `Implies`.
    :param right: The `boolean` expression acting as the implied part of the `Implies`.
    :return: The created `Implication`.
    """
    return get_env().expression_manager.Implies(left, right)


def Iff(left: BoolExpression, right: BoolExpression) -> FNode:
    """
    Creates an expression of the form:
        `left <-> right`
    Semantically, The expression is `True` only if `left` and `right` have the same value.
    Restriction: `Left` and `Right` must be of `boolean type`

    :param left: The `left` member of the `Iff expression`.
    :param right: The `right` member of the `Iff expression`.
    :return: The created `Iff` expression.
    """
    return get_env().expression_manager.Iff(left, right)


def Exists(
    expression: BoolExpression, *vars: "unified_planning.model.Variable"
) -> FNode:
    """
    Creates an expression of the form:
        `Exists (var[0]... var[n]) | expression`
    Restriction: expression must be of `boolean type` and
                vars must be of `Variable` type

    :param expression: The main expression of the `existential`. The expression should contain
        the given `variables`.
    :param *vars: All the `Variables` appearing in the `existential` expression.
    :return: The created `Existential` expression.
    """
    return get_env().expression_manager.Exists(expression, *vars)


def Forall(
    expression: BoolExpression, *vars: "unified_planning.model.Variable"
) -> FNode:
    """Creates an expression of the form:
        `Forall (var[0]... var[n]) | expression`
    Restriction: expression must be of `boolean type` and
                vars must be of `Variable` type

    :param expression: The main expression of the `universal` quantifier. The expression should contain
        the given `variables`.
    :param *vars: All the `Variables` appearing in the `universal` expression.
    :return: The created `Forall` expression.
    """
    return get_env().expression_manager.Forall(expression, *vars)


def FluentExp(
    fluent: "unified_planning.model.Fluent", params: Tuple[Expression, ...] = tuple()
) -> FNode:
    """
    Creates an expression for the given `fluent` and `parameters`.
    Restriction: `parameters type` must be compatible with the `Fluent` :func:`signature <unified_planning.model.Fluent.signature>`

    :param fluent: The `Fluent` that will be set as the `payload` of this expression.
    :param params: The expression acting as `parameters` for this `Fluent`; mainly the parameters will
        be :class:`Objects <unified_planning.model.Object>` (when the `FluentExp` is grounded) or :func:`Action parameters <unified_planning.model.Action.parameters>` (when the `FluentExp` is lifted).
    :return: The created `Fluent` Expression.
    """
    return get_env().expression_manager.FluentExp(fluent, params)


def ParameterExp(param: "unified_planning.model.Parameter") -> FNode:
    """
    Returns an expression for the given :func:`Action parameter <unified_planning.model.Action.parameters>`.

    :param param: The `Parameter` that must be promoted to `FNode`.
    :return: The `FNode` containing the given `param` as his payload.
    """
    return get_env().expression_manager.ParameterExp(param)


def VariableExp(var: "unified_planning.model.Variable") -> FNode:
    """
    Returns an expression for the given `Variable`.

    :param var: The `Variable` that must be promoted to `FNode`.
    :return: The `FNode` containing the given `variable` as his payload.
    """
    return get_env().expression_manager.VariableExp(var)


def ObjectExp(obj: "unified_planning.model.Object") -> FNode:
    """
    Returns an expression for the given object.

    :param obj: The `Object` that must be promoted to `FNode`.
    :return: The `FNode` containing the given object as his payload.
    """
    return get_env().expression_manager.ObjectExp(obj)


def TimingExp(timing: "up.model.timing.Timing") -> "up.model.fnode.FNode":
    """
    Returns an expression for the given `Timing`.

    :param timing: The `Timing` that must be promoted to `FNode`.
    :return: The `FNode` containing the given `timing` as his payload.
    """
    return get_env().expression_manager.TimingExp(timing)


def TRUE() -> FNode:
    """Return the boolean constant `True`."""
    return get_env().expression_manager.TRUE()


def FALSE() -> FNode:
    """Return the boolean constant `False`."""
    return get_env().expression_manager.FALSE()


def Bool(value: bool) -> FNode:
    """
    Return a boolean constant.

    :param value: The boolean value that must be promoted to `FNode`.
    :return: The `FNode` containing the given `value` as his payload.
    """
    return get_env().expression_manager.Bool(value)


def Int(value: int) -> FNode:
    """
    Return an `int` constant.

    :param value: The integer that must be promoted to `FNode`.
    :return: The `FNode` containing the given `integer` as his payload.
    """
    return get_env().expression_manager.Int(value)


def Real(value: Fraction) -> FNode:
    """
    Return a `real` constant.

    :param value: The `Fraction` that must be promoted to `FNode`.
    :return: The `FNode` containing the given `value` as his payload.
    """
    return get_env().expression_manager.Real(value)


def Plus(*args: Union[Expression, Iterable[Expression]]) -> FNode:
    """
    Creates an expression of the form:
    `args[0] + ... + args[n]`

    :param *args: Either an `Iterable` of expressions, like `[a, b, 3]`, or an unpacked version
        of it, like `a, b, 3`.
    :return: The `PLUS` expression created. (like `a + b + 3`)
    """
    return get_env().expression_manager.Plus(*args)


def Minus(left: Expression, right: Expression) -> FNode:
    """
    Creates an expression of the form: `left - right`.

    :param left: The `Minus minuend`.
    :param right: The `Minus subtrahend`.
    :return: The created `Minus` expression.
    """
    return get_env().expression_manager.Minus(left, right)


def Times(*args: Union[Expression, Iterable[Expression]]) -> FNode:
    """
    Creates an expression of the form:
    `args[0] * ... * args[n]`

    :param *args: Either an `Iterable` of expressions, like `[a, b, 3]`, or an unpacked version
        of it, like `a, b, 3`.
    :return: The `TIMES` expression created. (like `a * b * 3`)
    """
    return get_env().expression_manager.Times(*args)


def Div(left: Expression, right: Expression) -> FNode:
    """
    Creates an expression of the form: `left / right`.

    :param left: The `Div dividend`.
    :param right: The `Div divisor`.
    :return: The created `DIV` expression.
    """
    return get_env().expression_manager.Div(left, right)


def LE(left: Expression, right: Expression) -> FNode:
    """
    Creates an expression of the form: `left <= right`.

    :param left: The left side of the `<=`.
    :param right: The right side of the `<=`.
    :return: The created `LE` expression.
    """
    return get_env().expression_manager.LE(left, right)


def GE(left: Expression, right: Expression) -> FNode:
    """
    Creates an expression of the form: `left >= right`.

    :param left: The left side of the `>=`.
    :param right: The right side of the `>=`.
    :return: The created `GE` expression.
    """
    return get_env().expression_manager.GE(left, right)


def LT(left: Expression, right: Expression) -> FNode:
    """
    Creates an expression of the form: `left < right`.

    :param left: The left side of the `<`.
    :param right: The right side of the `<`.
    :return: The created `LT` expression.
    """
    return get_env().expression_manager.LT(left, right)


def GT(left: Expression, right: Expression) -> FNode:
    """
    Creates an expression of the form: `left > right`.

    :param left: The left side of the `>`.
    :param right: The right side of the `>`.
    :return: The created `GT` expression.
    """
    return get_env().expression_manager.GT(left, right)


def Equals(left: Expression, right: Expression) -> FNode:
    """
    Creates an expression of the form: `left == right`.

    NOTE: Is not valid for boolean expression, for those use `Iff`.

    :param left: The left side of the `==`.
    :param right: The right side of the `==`.
    :return: The created `Equals` expression.
    """
    return get_env().expression_manager.Equals(left, right)


def Dot(left: Agent, right: FNode) -> FNode:
    return get_env().expression_manager.Dot(left, right)


def BoolType() -> unified_planning.model.types.Type:
    """Returns the global environment's boolean type."""
    return get_env().type_manager.BoolType()


def IntType(
    lower_bound: int = None, upper_bound: int = None
) -> unified_planning.model.types.Type:
    """
    Returns the `integer` type defined in the global environment with the given `bounds`.
    If the type already exists, it is returned, otherwise it is created and returned.

    :param lower_bound: The integer used as this type's `lower bound`.
    :param upper_bound: The integer used as this type's `upper bound`.
    :return: The retrieved or created type.
    """
    return get_env().type_manager.IntType(lower_bound, upper_bound)


def RealType(
    lower_bound: Fraction = None, upper_bound: Fraction = None
) -> unified_planning.model.types.Type:
    """
    Returns the `real` type defined in the global environment with the given `bounds`.
    If the type already exists, it is returned, otherwise it is created and returned.

    :param lower_bound: The `Fraction` used as this type's `lower bound`.
    :param upper_bound: The `Fraction` used as this type's `upper bound`.
    :return: The retrieved or created `type`.
    """
    return get_env().type_manager.RealType(lower_bound, upper_bound)


def UserType(
    name: str, father: Optional[Type] = None
) -> unified_planning.model.types.Type:
    """
    Returns the user type defined in the global environment with the given `name` and `father`.
    If the type already exists, it is returned, otherwise it is created and returned.

    :param name: The name of this `user type`.
    :param father: The user type that must be set as the `father` for the created `type`.
    :return:  The retrieved or created `type`.
    """
    return get_env().type_manager.UserType(name, father)


def OneshotPlanner(
    *,
    name: Optional[str] = None,
    names: Optional[List[str]] = None,
    params: Union[Dict[str, str], List[Dict[str, str]]] = None,
    problem_kind: ProblemKind = ProblemKind(),
    optimality_guarantee: Optional[Union["up.engines.OptimalityGuarantee", str]] = None,
) -> Engine:
    """
    Returns a oneshot planner. There are three ways to call this method:
    - using 'name' (the name of a specific planner) and 'params' (planner dependent options).
      e.g. OneshotPlanner(name='tamer', params={'heuristic': 'hadd'})
    - using 'names' (list of specific planners name) and 'params' (list of
      planner dependent options) to get a Parallel engine.
      e.g. OneshotPlanner(names=['tamer', 'tamer'],
                          params=[{'heuristic': 'hadd'}, {'heuristic': 'hmax'}])
    - using 'problem_kind' and 'optimality_guarantee'.
          e.g. OneshotPlanner(problem_kind=problem.kind, optimality_guarantee=SOLVED_OPTIMALLY)
    """
    return get_env().factory.OneshotPlanner(
        name=name,
        names=names,
        params=params,
        problem_kind=problem_kind,
        optimality_guarantee=optimality_guarantee,
    )


def PlanValidator(
    *,
    name: Optional[str] = None,
    names: Optional[List[str]] = None,
    params: Union[Dict[str, str], List[Dict[str, str]]] = None,
    problem_kind: ProblemKind = ProblemKind(),
    plan_kind: Optional[Union["up.plans.PlanKind", str]] = None,
) -> Engine:
    """
    Returns a plan validator. There are three ways to call this method:
    - using 'name' (the name of a specific plan validator) and 'params'
      (plan validator dependent options).
      e.g. PlanValidator(name='tamer', params={'opt': 'val'})
    - using 'names' (list of specific plan validators name) and 'params' (list of
      plan validators dependent options) to get a Parallel engine.
      e.g. PlanValidator(names=['tamer', 'tamer'],
                         params=[{'opt1': 'val1'}, {'opt2': 'val2'}])
    - using 'problem_kind' and 'plan_kind' parameters.
      e.g. PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind)
    """
    return get_env().factory.PlanValidator(
        name=name,
        names=names,
        params=params,
        problem_kind=problem_kind,
        plan_kind=plan_kind,
    )


def Compiler(
    *,
    name: Optional[str] = None,
    names: Optional[List[str]] = None,
    params: Union[Dict[str, str], List[Dict[str, str]]] = None,
    problem_kind: ProblemKind = ProblemKind(),
    compilation_kind: Optional[Union["up.engines.CompilationKind", str]] = None,
    compilation_kinds: Optional[List[Union["up.engines.CompilationKind", str]]] = None,
) -> "up.engines.engine.Engine":
    """
    Returns a Compiler or a pipeline of Compilers.

    To get a Compiler there are two ways to call this method:
    - using 'name' (the name of a specific compiler) and 'params'
      (compiler dependent options).
      e.g. Compiler(name='tamer', params={'opt': 'val'})
    - using 'problem_kind' and 'compilation_kind' parameters.
      e.g. Compiler(problem_kind=problem.kind, compilation_kind=GROUNDING)

    To get a pipeline of Compilers there are two ways to call this method:
    - using 'names' (the names of the specific compilers), 'params'
      (compilers dependent options) and 'compilation_kinds'.
      e.g. Compiler(names=['up_quantifiers_remover', 'up_grounder'],
                    params=[{'opt1': 'val1'}, {'opt2': 'val2'}],
                    compilation_kinds=[QUANTIFIERS_REMOVING, GROUNDING])
    - using 'problem_kind' and 'compilation_kinds' parameters.
      e.g. Compiler(problem_kind=problem.kind,
                    compilation_kinds=[QUANTIFIERS_REMOVING, GROUNDING])
    """
    return get_env().factory.Compiler(
        name=name,
        names=names,
        params=params,
        problem_kind=problem_kind,
        compilation_kind=compilation_kind,
        compilation_kinds=compilation_kinds,
    )


def Simulator(
    problem: "up.model.AbstractProblem",
    *,
    name: Optional[str] = None,
    params: Union[Dict[str, str], List[Dict[str, str]]] = None,
) -> "up.engines.engine.Engine":
    """
    Returns a Simulator. There are two ways to call this method:
    - using 'problem_kind' through the problem field.
        e.g. Simulator(problem)
    - using 'name' (the name of a specific simulator) and eventually some 'params'
        (simulator dependent options).
        e.g. Simulator(problem, name='sequential_simulator')
    """
    return get_env().factory.Simulator(problem=problem, name=name, params=params)


def Replanner(
    problem: "up.model.AbstractProblem",
    *,
    name: Optional[str] = None,
    params: Union[Dict[str, str], List[Dict[str, str]]] = None,
    optimality_guarantee: Optional[Union["up.engines.OptimalityGuarantee", str]] = None,
) -> "up.engines.engine.Engine":
    """
    Returns a Replanner. There are two ways to call this method:
    - using 'problem' (with its kind) and 'optimality_guarantee' parameters.
      e.g. Replanner(problem, optimality_guarantee=SOLVED_OPTIMALLY)
    - using 'name' (the name of a specific replanner) and 'params'
      (replanner dependent options).
      e.g. Replanner(problem, name='replanner[tamer]')
    """
    return get_env().factory.Replanner(
        problem=problem,
        name=name,
        params=params,
        optimality_guarantee=optimality_guarantee,
    )


def print_engines_info(stream: IO[str] = sys.stdout, full_credits: bool = False):
    get_env().factory.print_engines_info(stream, full_credits)


def set_credits_stream(stream: Optional[IO[str]]):
    get_env().credits_stream = stream
