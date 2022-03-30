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

import unified_planning.model.types
from unified_planning.environment import get_env
from unified_planning.model import *
from unified_planning.solvers import Solver
from typing import Iterable, List, Union, Dict, Tuple, Optional
from fractions import Fraction


def And(*args: Union[BoolExpression, Iterable[BoolExpression]]) -> FNode:
    return get_env().expression_manager.And(*args)

def Or(*args: Union[BoolExpression, Iterable[BoolExpression]]) -> FNode:
    return get_env().expression_manager.Or(*args)

def Not(expression: BoolExpression) -> FNode:
    return get_env().expression_manager.Not(expression)

def Implies(left: BoolExpression, right: BoolExpression) -> FNode:
    return get_env().expression_manager.Implies(left, right)

def Iff(left: BoolExpression, right: BoolExpression) -> FNode:
    return get_env().expression_manager.Iff(left, right)

def Exists(expression: BoolExpression, *vars: 'unified_planning.model.Variable') -> FNode:
    return get_env().expression_manager.Exists(expression, *vars)

def Forall(expression: BoolExpression, *vars: 'unified_planning.model.Variable') -> FNode:
    return get_env().expression_manager.Forall(expression, *vars)

def FluentExp(fluent: 'unified_planning.model.Fluent', params: Tuple[Expression, ...] = tuple()) -> FNode:
    return get_env().expression_manager.FluentExp(fluent, params)

def ParameterExp(param: 'unified_planning.model.Parameter') -> FNode:
    return get_env().expression_manager.ParameterExp(param)

def VariableExp(var: 'unified_planning.model.Variable') -> FNode:
    return get_env().expression_manager.VariableExp(var)

def ObjectExp(obj: 'unified_planning.model.Object') -> FNode:
    return get_env().expression_manager.ObjectExp(obj)

def TRUE() -> FNode:
    return get_env().expression_manager.TRUE()

def FALSE() -> FNode:
    return get_env().expression_manager.FALSE()

def Bool(value: bool) -> FNode:
    return get_env().expression_manager.Bool(value)

def Int(value: int) -> FNode:
    return get_env().expression_manager.Int(value)

def Real(value: Fraction) -> FNode:
    return get_env().expression_manager.Real(value)

def Plus(*args: Union[Expression, Iterable[Expression]]) -> FNode:
    return get_env().expression_manager.Plus(*args)

def Minus(left: Expression, right: Expression) -> FNode:
    return get_env().expression_manager.Minus(left, right)

def Times(*args: Union[Expression, Iterable[Expression]]) -> FNode:
    return get_env().expression_manager.Times(*args)

def Div(left: Expression, right: Expression) -> FNode:
    return get_env().expression_manager.Div(left, right)

def LE(left: Expression, right: Expression) -> FNode:
    return get_env().expression_manager.LE(left, right)

def GE(left: Expression, right: Expression) -> FNode:
    return get_env().expression_manager.GE(left, right)

def LT(left: Expression, right: Expression) -> FNode:
    return get_env().expression_manager.LT(left, right)

def GT(left: Expression, right: Expression) -> FNode:
    return get_env().expression_manager.GT(left, right)

def Equals(left: Expression, right: Expression) -> FNode:
    return get_env().expression_manager.Equals(left, right)

def BoolType() -> unified_planning.model.types.Type:
    return get_env().type_manager.BoolType()

def IntType(lower_bound: int = None, upper_bound: int = None) -> unified_planning.model.types.Type:
    return get_env().type_manager.IntType(lower_bound, upper_bound)

def RealType(lower_bound: Fraction = None, upper_bound: Fraction = None) -> unified_planning.model.types.Type:
    return get_env().type_manager.RealType(lower_bound, upper_bound)

def UserType(name: str, father: Optional[Type] = None) -> unified_planning.model.types.Type:
    return get_env().type_manager.UserType(name, father)

def OneshotPlanner(*, name: Optional[str] = None,
                   names: Optional[List[str]] = None,
                   params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                   problem_kind: ProblemKind = ProblemKind(),
                   optimality_guarantee: Optional[Union[int, str]] = None) -> Optional[Solver]:
    """
    Returns a oneshot planner. There are three ways to call this method:
    - using 'name' (the name of a specific planner) and 'params' (planner dependent options).
      e.g. OneshotPlanner(name='tamer', params={'heuristic': 'hadd'})
    - using 'names' (list of specific planners name) and 'params' (list of
      planner dependent options) to get a Parallel solver.
      e.g. OneshotPlanner(names=['tamer', 'tamer'],
                          params=[{'heuristic': 'hadd'}, {'heuristic': 'hmax'}])
    - using 'problem_kind' and 'optimality_guarantee'.
          e.g. OneshotPlanner(problem_kind=problem.kind, optimality_guarantee=SOLVED_OPTIMALLY)
    """
    return get_env().factory.OneshotPlanner(name=name, names=names, params=params,
                                            problem_kind=problem_kind,
                                            optimality_guarantee=optimality_guarantee)

def PlanValidator(*, name: Optional[str] = None,
                   names: Optional[List[str]] = None,
                   params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                   problem_kind: ProblemKind = ProblemKind()) -> Optional[Solver]:
    """
    Returns a plan validator. There are three ways to call this method:
    - using 'name' (the name of a specific plan validator) and 'params'
      (plan validator dependent options).
      e.g. PlanValidator(name='tamer', params={'opt': 'val'})
    - using 'names' (list of specific plan validators name) and 'params' (list of
      plan validators dependent options) to get a Parallel solver.
      e.g. PlanValidator(names=['tamer', 'tamer'],
                         params=[{'opt1': 'val1'}, {'opt2': 'val2'}])
    - using 'problem_kind' parameter.
      e.g. PlanValidator(problem_kind=problem.kind)
    """
    return get_env().factory.PlanValidator(name=name, names=names, params=params,
                                           problem_kind=problem_kind)

def Grounder(*, name: Optional[str] = None, params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                   problem_kind: ProblemKind = ProblemKind()) -> Optional[Solver]:
    """
    Returns a Grounder. There are three ways to call this method:
    - using 'name' (the name of a specific grounder) and 'params'
        (grounder dependent options).
        e.g. Grounder(name='tamer', params={'opt': 'val'})
    - using 'problem_kind' parameter.
        e.g. Grounder(problem_kind=problem.kind)
    """
    return get_env().factory.Grounder(name=name, params=params,
                                           problem_kind=problem_kind)
