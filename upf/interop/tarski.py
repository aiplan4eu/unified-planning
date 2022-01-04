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

import upf
import itertools
import tarski.fstrips # type: ignore
from fractions import Fraction
from upf.exceptions import UPFProblemDefinitionError
from upf.environment import Environment
from collections import OrderedDict
from typing import Union, Dict
from tarski.syntax.formulas import Formula, is_and, is_or, is_neg, is_atom # type: ignore
from tarski.syntax.formulas import Tautology, Contradiction, QuantifiedFormula, Quantifier # type: ignore
from tarski.syntax.terms import Term, CompoundTerm, BuiltinPredicateSymbol # type: ignore
from tarski.syntax.terms import Constant, Variable, BuiltinFunctionSymbol # type: ignore
from tarski.fstrips.fstrips import AddEffect, DelEffect, FunctionalEffect # type: ignore


def convert_tarski_formula(env: Environment, fluents: Dict[str, 'upf.model.Fluent'],
                           objects: Dict[str, 'upf.model.Object'],
                           action_parameters: Dict[str, 'upf.model.ActionParameter'],
                           formula: Union[Formula, Term]) -> 'upf.model.FNode':
    """Converts a tarski formula in a upf expression."""
    em = env.expression_manager
    if is_and(formula):
        children = [convert_tarski_formula(env, fluents, objects, action_parameters, f)
                    for f in formula.subformulas]
        return em.And(*children)
    elif is_or(formula):
        children = [convert_tarski_formula(env, fluents, objects, action_parameters, f)
                    for f in formula.subformulas]
        return em.Or(*children)
    elif is_neg(formula):
        assert len(formula.subformulas) == 1
        return em.Not(convert_tarski_formula(env, fluents, objects, action_parameters,
                                                  formula.subformulas[0]))
    elif is_atom(formula) or isinstance(formula, CompoundTerm):
        children = [convert_tarski_formula(env, fluents, objects, action_parameters, f)
                    for f in formula.subterms]
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
            raise UPFProblemDefinitionError(symbol + ' not supported!')
    elif isinstance(formula, Constant):
        if formula.sort.name == 'number':
            return em.Real(Fraction(float(formula.name)))
        elif formula.name in objects:
            return em.ObjectExp(objects[formula.name])
        else:
            raise UPFProblemDefinitionError(formula + ' not supported!')
    elif isinstance(formula, Variable):
        if formula.symbol in action_parameters:
            return em.ParameterExp(action_parameters[formula.symbol])
        else:
            return em.VariableExp(upf.model.Variable(formula.symbol, \
                env.type_manager.UserType(formula.sort.name)))
    elif isinstance(formula, QuantifiedFormula):
        expression = convert_tarski_formula(env, fluents, objects, action_parameters, formula.formula)
        variables = [upf.model.Variable(v.symbol, env.type_manager.UserType(v.sort.name)) \
            for v in formula.variables]
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
        raise UPFProblemDefinitionError(str(formula) + ' not supported!')


def convert_tarski_problem(env: Environment, tarski_problem: tarski.fstrips.Problem) -> 'upf.model.Problem':
    """Converts a tarski problem in a upf.Problem."""
    em = env.expression_manager
    tm = env.type_manager
    lang = tarski_problem.language
    problem = upf.model.Problem(tarski_problem.name)

    # Convert types
    types = {}
    for t in lang.sorts:
        types[str(t.name)] = tm.UserType(str(t.name))

    # Convert predicates and functions
    fluents = {}
    for p in lang.predicates:
        if str(p.name) in ['=', '!=', '<', '<=', '>', '>=']:
            continue
        signature = []
        for t in p.sort:
            signature.append(types[str(t.name)])
        fluent = upf.model.Fluent(p.name, tm.BoolType(), signature)
        fluents[fluent.name()] = fluent
        problem.add_fluent(fluent)
    for p in lang.functions:
        if str(p.name) in ['ite', '@', '+', '-', '*', '/', '**', '%', 'sqrt']:
            continue
        signature = []
        for t in p.domain:
            signature.append(types[str(t.name)])
        fluent = upf.model.Fluent(p.name, tm.RealType(), signature)
        fluents[fluent.name()] = fluent
        problem.add_fluent(fluent)

    # Convert objects
    objects = {}
    for c in lang.constants():
        o = upf.model.Object(str(c.name), types[str(c.sort.name)])
        objects[o.name()] = o
        problem.add_object(o)

    # Convert actions
    for a_name in tarski_problem.actions:
        a = tarski_problem.get_action(a_name)
        parameters = OrderedDict()
        for p in a.parameters:
            parameters[p.symbol] = types[p.sort.name]
        action = upf.model.InstantaneousAction(a_name, parameters)
        action_parameters = {}
        for p in parameters.keys():
            action_parameters[p] = action.parameter(p)
        f = convert_tarski_formula(env, fluents, objects, action_parameters, a.precondition)
        action.add_precondition(f)
        for eff in a.effects:
            condition = convert_tarski_formula(env, fluents, objects, action_parameters, eff.condition)
            if isinstance(eff, AddEffect):
                f = convert_tarski_formula(env, fluents, objects, action_parameters, eff.atom)
                action.add_effect(f, True, condition)
            elif isinstance(eff, DelEffect):
                f = convert_tarski_formula(env, fluents, objects, action_parameters, eff.atom)
                action.add_effect(f, False, condition)
            elif isinstance(eff, FunctionalEffect):
                lhs = convert_tarski_formula(env, fluents, objects, action_parameters, eff.lhs)
                rhs = convert_tarski_formula(env, fluents, objects, action_parameters, eff.rhs)
                action.add_effect(lhs, rhs, condition)
            else:
                raise UPFProblemDefinitionError(eff + ' not supported!')
        problem.add_action(action)

    # Set initial values
    initial_values = {}
    for fluent in fluents.values():
        l = [problem.objects(t) for t in fluent.signature()]
        if fluent.type().is_bool_type():
            default_value = em.FALSE()
        elif fluent.type().is_real_type():
            default_value = em.Real(Fraction(0))
        elif fluent.type().is_int_type():
            default_value = em.Int(0)
        if len(l) == 0:
            initial_values[em.FluentExp(fluent)] = default_value
        else:
            for args in itertools.product(*l):
                initial_values[fluent(*args)] = default_value
    for i in tarski_problem.init.as_atoms():
        if isinstance(i, tuple):
            lhs = convert_tarski_formula(env, fluents, objects, {}, i[0])
            rhs = convert_tarski_formula(env, fluents, objects, {}, i[1])
            initial_values[lhs] = rhs
        else:
            f = convert_tarski_formula(env, fluents, objects, {}, i)
            initial_values[f] = em.TRUE()
    for lhs, rhs in initial_values.items():
        problem.set_initial_value(lhs, rhs)

    # Convert goals
    problem.add_goal(convert_tarski_formula(env, fluents, objects, {}, tarski_problem.goal))

    return problem
