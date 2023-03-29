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


import unified_planning
import itertools
import tarski.fstrips
from fractions import Fraction
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.environment import Environment
from collections import OrderedDict
from typing import Optional, Union, Dict, cast
from tarski.syntax import Interval
from tarski.syntax.formulas import Formula, is_and, is_or, is_neg, is_atom
from tarski.syntax.formulas import (
    Tautology,
    Contradiction,
    QuantifiedFormula,
    Quantifier,
)
from tarski.syntax.terms import Term, CompoundTerm, BuiltinPredicateSymbol
from tarski.syntax.terms import Constant, Variable, BuiltinFunctionSymbol
from tarski.fstrips.fstrips import AddEffect, DelEffect, FunctionalEffect


def convert_tarski_formula(
    environment: Environment,
    fluents: Dict[str, "unified_planning.model.Fluent"],
    objects: Dict[str, "unified_planning.model.Object"],
    action_parameters: Dict[str, "unified_planning.model.Parameter"],
    types: Dict[str, Optional["unified_planning.model.Type"]],
    formula: Union[Formula, Term],
) -> "unified_planning.model.FNode":
    """Converts a tarski formula in a unified_planning expression."""
    em = environment.expression_manager
    if is_and(formula):
        children = [
            convert_tarski_formula(
                environment, fluents, objects, action_parameters, types, f
            )
            for f in formula.subformulas
        ]
        return em.And(*children)
    elif is_or(formula):
        children = [
            convert_tarski_formula(
                environment, fluents, objects, action_parameters, types, f
            )
            for f in formula.subformulas
        ]
        return em.Or(*children)
    elif is_neg(formula):
        assert len(formula.subformulas) == 1
        return em.Not(
            convert_tarski_formula(
                environment,
                fluents,
                objects,
                action_parameters,
                types,
                formula.subformulas[0],
            )
        )
    elif is_atom(formula) or isinstance(formula, CompoundTerm):
        children = [
            convert_tarski_formula(
                environment, fluents, objects, action_parameters, types, f
            )
            for f in formula.subterms
        ]
        if is_atom(formula):
            symbol = formula.predicate.symbol
        else:
            symbol = formula.symbol.name
        if symbol == BuiltinPredicateSymbol.EQ:
            assert len(children) == 2
            return em.Equals(children[0], children[1])
        elif symbol == BuiltinPredicateSymbol.NE:
            assert len(children) == 2
            return em.Not(em.Equals(children[0], children[1]))
        elif symbol == BuiltinPredicateSymbol.LT:
            assert len(children) == 2
            return em.LT(children[0], children[1])
        elif symbol == BuiltinPredicateSymbol.LE:
            assert len(children) == 2
            return em.LE(children[0], children[1])
        elif symbol == BuiltinPredicateSymbol.GT:
            assert len(children) == 2
            return em.GT(children[0], children[1])
        elif symbol == BuiltinPredicateSymbol.GE:
            assert len(children) == 2
            return em.GE(children[0], children[1])
        elif symbol == BuiltinFunctionSymbol.ADD:
            assert len(children) == 2
            return em.Plus(children[0], children[1])
        elif symbol == BuiltinFunctionSymbol.SUB:
            assert len(children) == 2
            return em.Minus(children[0], children[1])
        elif symbol == BuiltinFunctionSymbol.MUL:
            assert len(children) == 2
            return em.Times(children[0], children[1])
        elif symbol == BuiltinFunctionSymbol.DIV:
            assert len(children) == 2
            return em.Div(children[0], children[1])
        elif symbol in fluents:
            return fluents[symbol](*children)
        else:
            raise UPProblemDefinitionError(symbol + " not supported!")
    elif isinstance(formula, Constant):
        if formula.sort.name == "number":
            return em.Real(Fraction(float(formula.name)))
        elif isinstance(formula.sort, tarski.syntax.Interval):
            if formula.sort.language.is_subtype(
                formula.sort, formula.sort.language.Integer
            ) or formula.sort.language.is_subtype(
                formula.sort, formula.sort.language.Natural
            ):
                return em.Int(int(formula.name))
            elif formula.sort.language.is_subtype(
                formula.sort, formula.sort.language.Real
            ):
                return em.Real(Fraction(float(formula.name)))
            else:
                raise NotImplementedError
        elif formula.name in objects:
            return em.ObjectExp(objects[formula.name])
        else:
            raise UPProblemDefinitionError(formula + " not supported!")
    elif isinstance(formula, Variable):
        if formula.symbol in action_parameters:
            return em.ParameterExp(action_parameters[formula.symbol])
        else:
            return em.VariableExp(
                unified_planning.model.Variable(
                    formula.symbol,
                    cast(
                        unified_planning.model.Type,
                        _convert_type_and_update_dict(
                            formula.sort,
                            types,
                            environment.type_manager,
                            formula.sort.language,
                        ),
                    ),
                    environment,
                )
            )
    elif isinstance(formula, QuantifiedFormula):
        expression = convert_tarski_formula(
            environment, fluents, objects, action_parameters, types, formula.formula
        )
        variables = [
            unified_planning.model.Variable(
                v.symbol,
                cast(
                    unified_planning.model.Type,
                    _convert_type_and_update_dict(
                        v.sort, types, environment.type_manager, v.sort.language
                    ),
                ),
                environment,
            )
            for v in formula.variables
        ]
        if formula.quantifier == Quantifier.Exists:
            return em.Exists(expression, *variables)
        elif formula.quantifier == Quantifier.Forall:
            return em.Forall(expression, *variables)
        else:
            raise NotImplementedError
    elif isinstance(formula, Tautology):
        return em.TRUE()
    elif isinstance(formula, Contradiction):
        return em.FALSE()
    else:
        raise UPProblemDefinitionError(str(formula) + " not supported!")


def _check_if_tarski_problem_uses_object_type(
    tarski_problem: tarski.fstrips.Problem,
) -> bool:
    lang = tarski_problem.language
    for p in lang.predicates:
        if str(p.name) in ["=", "!=", "<", "<=", ">", ">="]:
            continue
        for t in p.sort:
            if str(t.name) == "object":
                return True
    for p in lang.functions:
        if str(p.name) in ["ite", "@", "+", "-", "*", "/", "**", "%", "sqrt"]:
            continue
        for t in p.domain:
            if str(t.name) == "object":
                return True
        func_sort = p.sort[-1]
        if str(func_sort.name) == "object":
            return True
    for c in lang.constants():
        if str(c.sort.name) == "object":
            return True
    for a_name in tarski_problem.actions:
        a = tarski_problem.get_action(a_name)
        for p in a.parameters:
            if str(p.sort.name) == "object":
                return True
    return False


def _convert_type_and_update_dict(
    sort: tarski.syntax.Sort,
    types_dict: Dict[str, Optional["unified_planning.model.Type"]],
    tm: "unified_planning.model.type_manager.TypeManager",
    lang: "tarski.fol.FirstOrderLanguage",
) -> Optional["unified_planning.model.Type"]:
    """Converts a tarski type in a unified_planning type and inserts it into the types_dict.
    Important NOTE: This function modifies the parameter types_dict."""
    if str(sort.name) in types_dict:  # type already defined
        return types_dict[str(sort.name)]
    if isinstance(sort, Interval):  # if the type is an Interval
        if sort == lang.Integer:
            up_type = tm.IntType()
        elif sort == lang.Natural:
            up_type = tm.IntType(lower_bound=0)
        elif sort == lang.Real:
            up_type = tm.RealType()
        elif sort.encode == lang.Integer.encode:
            up_type = tm.IntType(sort.lower_bound, sort.upper_bound)
        elif sort.encode == lang.Natural.encode:
            up_type = tm.IntType(0, sort.upper_bound)
        elif sort.encode == lang.Real.encode:
            up_type = tm.RealType(sort.lower_bound, sort.upper_bound)
        else:
            raise NotImplementedError
    else:  # the type should be a user_type
        tarski_father = tarski.syntax.sorts.parent(sort)
        up_father: Optional["unified_planning.model.Type"] = None
        if tarski_father is not None:
            up_father = _convert_type_and_update_dict(
                tarski_father, types_dict, tm, lang
            )
        up_type = tm.UserType(str(sort.name), up_father)
    assert up_type is not None  # sanity check
    types_dict[str(sort.name)] = up_type
    return up_type


def convert_problem_from_tarski(
    environment: Environment, tarski_problem: tarski.fstrips.Problem
) -> "unified_planning.model.Problem":
    """
    Converts a tarski problem in a `Problem`.

    :param environment: The unified_planning `Environment`.
    :param tarski_problem: The tarski problem to convert.
    :return: The generated `Problem`.
    """
    em = environment.expression_manager
    tm = environment.type_manager
    lang = tarski_problem.language
    problem = unified_planning.model.Problem(tarski_problem.name)

    # Convert types
    types: Dict[str, Optional["unified_planning.model.Type"]] = {}
    uses_object_type: bool = _check_if_tarski_problem_uses_object_type(tarski_problem)
    if not uses_object_type:
        types[
            "object"
        ] = None  # we set object as None, so when it is the father of a type in tarski, in UP it will be None.
    for t in lang.sorts:
        # types will be filled with the needed types in this loop.
        _convert_type_and_update_dict(t, types, tm, lang)

    # Convert predicates and functions
    fluents = {}
    for p in lang.predicates:
        if str(p.name) in ["=", "!=", "<", "<=", ">", ">="]:
            continue
        signature: OrderedDict[str, "unified_planning.model.Type"] = OrderedDict()
        for i, t in enumerate(p.sort):
            type = types[str(t.name)]
            assert type is not None
            signature[f"p{str(i+1)}"] = type
        fluent = unified_planning.model.Fluent(p.name, tm.BoolType(), signature)
        fluents[fluent.name] = fluent
        problem.add_fluent(fluent)
    for p in lang.functions:
        if str(p.name) in ["ite", "@", "+", "-", "*", "/", "**", "%", "sqrt"]:
            continue
        signature = OrderedDict()
        for i, t in enumerate(p.domain):
            type = types[str(t.name)]
            assert type is not None
            signature[f"p{str(i+1)}"] = type
        func_sort = p.sort[-1]
        if isinstance(func_sort, Interval):
            if func_sort.encode == lang.Real.encode:
                if func_sort.name == "Real" or func_sort.name == "number":
                    fluent = unified_planning.model.Fluent(
                        p.name, tm.RealType(), signature
                    )
                else:
                    fluent = unified_planning.model.Fluent(
                        p.name,
                        tm.RealType(
                            lower_bound=Fraction(func_sort.lower_bound),
                            upper_bound=Fraction(func_sort.upper_bound),
                        ),
                        signature,
                    )
            else:
                assert (
                    func_sort.encode == lang.Integer.encode
                    or func_sort.encode == lang.Natural.encode
                )
                if func_sort.name == "Integer":
                    fluent = unified_planning.model.Fluent(
                        p.name, tm.IntType(), signature
                    )
                elif func_sort.name == "Natual":
                    fluent = unified_planning.model.Fluent(
                        p.name, tm.IntType(lower_bound=0), signature
                    )
                else:
                    fluent = unified_planning.model.Fluent(
                        p.name,
                        tm.IntType(
                            lower_bound=func_sort.lower_bound,
                            upper_bound=func_sort.upper_bound,
                        ),
                        signature,
                    )
        else:
            fluent = unified_planning.model.Fluent(
                p.name, types[func_sort.name], signature
            )
        fluents[fluent.name] = fluent
        problem.add_fluent(fluent)

    # Convert objects
    objects = {}
    for c in lang.constants():
        type = types[str(c.sort.name)]
        assert type is not None
        o = unified_planning.model.Object(str(c.name), type, environment)
        objects[o.name] = o
        problem.add_object(o)

    # Convert actions
    for a_name in tarski_problem.actions:
        a = tarski_problem.get_action(a_name)
        parameters: OrderedDict[str, "unified_planning.model.Type"] = OrderedDict()
        for p in a.parameters:
            type = types[str(p.sort.name)]
            assert type is not None
            parameters[p.symbol] = type
        action = unified_planning.model.InstantaneousAction(a_name, parameters)
        action_parameters = {}
        for p in parameters.keys():
            action_parameters[p] = action.parameter(p)
        f = convert_tarski_formula(
            environment, fluents, objects, action_parameters, types, a.precondition
        )
        action.add_precondition(f)
        for eff in a.effects:
            condition = convert_tarski_formula(
                environment, fluents, objects, action_parameters, types, eff.condition
            )
            if isinstance(eff, AddEffect):
                f = convert_tarski_formula(
                    environment, fluents, objects, action_parameters, types, eff.atom
                )
                action.add_effect(f, True, condition)
            elif isinstance(eff, DelEffect):
                f = convert_tarski_formula(
                    environment, fluents, objects, action_parameters, types, eff.atom
                )
                action.add_effect(f, False, condition)
            elif isinstance(eff, FunctionalEffect):
                lhs = convert_tarski_formula(
                    environment, fluents, objects, action_parameters, types, eff.lhs
                )
                rhs = convert_tarski_formula(
                    environment, fluents, objects, action_parameters, types, eff.rhs
                )
                action.add_effect(lhs, rhs, condition)
            else:
                raise UPProblemDefinitionError(eff + " not supported!")
        problem.add_action(action)

    # Set initial values
    initial_values = {}
    for fluent in fluents.values():
        l = [problem.objects(p.type) for p in fluent.signature]
        if fluent.type.is_bool_type():
            default_value = em.FALSE()
        elif fluent.type.is_real_type():
            default_value = em.Real(Fraction(0))
        elif fluent.type.is_int_type():
            default_value = em.Int(0)
        elif fluent.type.is_user_type():
            continue
        if len(l) == 0:
            initial_values[em.FluentExp(fluent)] = default_value
        else:
            for args in itertools.product(*l):
                initial_values[fluent(*args)] = default_value
    for i in tarski_problem.init.as_atoms():
        if isinstance(i, tuple):
            lhs = convert_tarski_formula(environment, fluents, objects, {}, types, i[0])
            rhs = convert_tarski_formula(environment, fluents, objects, {}, types, i[1])
            initial_values[lhs] = rhs
        else:
            f = convert_tarski_formula(environment, fluents, objects, {}, types, i)
            initial_values[f] = em.TRUE()
    for lhs, rhs in initial_values.items():
        problem.set_initial_value(lhs, rhs)

    # Convert goals
    problem.add_goal(
        convert_tarski_formula(
            environment, fluents, objects, {}, types, tarski_problem.goal
        )
    )

    return problem
