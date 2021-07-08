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

import upf
import itertools
import tarski.io  # type: ignore
import tarski.fstrips # type: ignore
from fractions import Fraction
from upf.environment import Environment, get_env
from upf.exceptions import UPFProblemDefinitionError
from tarski.syntax.formulas import Formula, is_and, is_or, is_neg, is_atom # type: ignore
from tarski.syntax.terms import Term, CompoundTerm, BuiltinPredicateSymbol # type: ignore
from tarski.syntax.terms import Constant, Variable, BuiltinFunctionSymbol # type: ignore
from tarski.fstrips.fstrips import AddEffect, DelEffect, FunctionalEffect # type: ignore
from collections import OrderedDict
from typing import Union, Dict


class PDDLReader:
    def __init__(self, env: Environment = None):
        self.reader = tarski.io.PDDLReader(raise_on_error=True,
                                           strict_with_requirements=False)
        self.env = get_env(env)
        self.em = self.env.expression_manager
        self.tm = self.env.type_manager

    def _convert_formula(self, fluents: Dict[str, upf.Fluent],
                         objects: Dict[str, upf.Object],
                         action_parameters: Dict[str, upf.ActionParameter],
                         formula: Union[Formula, Term]) -> upf.fnode.FNode:
        if is_and(formula):
            children = [self._convert_formula(fluents, objects, action_parameters, f)
                        for f in formula.subformulas]
            return self.em.And(*children)
        elif is_or(formula):
            children = [self._convert_formula(fluents, objects, action_parameters, f)
                        for f in formula.subformulas]
            return self.em.Or(*children)
        elif is_neg(formula):
            assert len(formula.subformulas) == 1
            return self.em.Not(self._convert_formula(fluents, objects, action_parameters,
                                             formula.subformulas[0]))
        elif is_atom(formula) or isinstance(formula, CompoundTerm):
            children = [self._convert_formula(fluents, objects, action_parameters, f)
                        for f in formula.subterms]
            if is_atom(formula):
                symbol = formula.predicate.symbol
            else:
                symbol = formula.symbol.name
            if symbol == BuiltinPredicateSymbol.EQ:
                assert len(children) == 2
                return self.em.Equals(children[0], children[1])
            elif symbol == BuiltinPredicateSymbol.NE:
                assert len(children) == 2
                return self.em.Not(self.em.Equals(children[0], children[1]))
            elif symbol == BuiltinPredicateSymbol.LT:
                assert len(children) == 2
                return self.em.LT(children[0], children[1])
            elif symbol == BuiltinPredicateSymbol.LE:
                assert len(children) == 2
                return self.em.LE(children[0], children[1])
            elif symbol == BuiltinPredicateSymbol.GT:
                assert len(children) == 2
                return self.em.GT(children[0], children[1])
            elif symbol == BuiltinPredicateSymbol.GE:
                assert len(children) == 2
                return self.em.GE(children[0], children[1])
            elif symbol == BuiltinFunctionSymbol.ADD:
                assert len(children) == 2
                return self.em.Plus(children[0], children[1])
            elif symbol == BuiltinFunctionSymbol.SUB:
                assert len(children) == 2
                return self.em.Minus(children[0], children[1])
            elif symbol == BuiltinFunctionSymbol.MUL:
                assert len(children) == 2
                return self.em.Times(children[0], children[1])
            elif symbol == BuiltinFunctionSymbol.DIV:
                assert len(children) == 2
                return self.em.Div(children[0], children[1])
            elif symbol in fluents:
                return fluents[symbol](*children)
            else:
                raise UPFProblemDefinitionError(symbol + ' not supported!')
        elif isinstance(formula, Constant):
            if formula.sort.name == 'number':
                return self.em.Real(Fraction(float(formula.name)))
            elif formula.name in objects:
                return self.em.ObjectExp(objects[formula.name])
            else:
                raise UPFProblemDefinitionError(symbol + ' not supported!')
        elif isinstance(formula, Variable):
            assert formula.symbol in action_parameters
            return self.em.ParameterExp(action_parameters[formula.symbol])
        else:
            raise UPFProblemDefinitionError(formula + ' not supported!')

    def _convert_tarski_problem(self, tarski_problem: tarski.fstrips.Problem) -> upf.Problem:
        lang = tarski_problem.language
        problem = upf.Problem(tarski_problem.name)

        # Convert types
        types = {}
        for t in lang.sorts:
            types[str(t.name)] = self.tm.UserType(str(t.name))

        # Convert predicates and functions
        fluents = {}
        for p in lang.predicates:
            if str(p.name) in ['=', '!=', '<', '<=', '>', '>=']:
                continue
            signature = []
            for t in p.sort:
                signature.append(types[str(t.name)])
            fluent = upf.Fluent(p.name, self.tm.BoolType(), signature)
            fluents[fluent.name()] = fluent
            problem.add_fluent(fluent)
        for p in lang.functions:
            if str(p.name) in ['ite', '@', '+', '-', '*', '/', '**', '%', 'sqrt']:
                continue
            signature = []
            for t in p.domain:
                signature.append(types[str(t.name)])
            fluent = upf.Fluent(p.name, self.tm.RealType(), signature)
            fluents[fluent.name()] = fluent
            problem.add_fluent(fluent)

        # Convert objects
        objects = {}
        for c in lang.constants():
            o = upf.Object(str(c.name), types[str(c.sort.name)])
            objects[o.name()] = o
            problem.add_object(o)

        # Convert actions
        for a_name in tarski_problem.actions:
            a = tarski_problem.get_action(a_name)
            parameters = OrderedDict()
            for p in a.parameters:
                parameters[p.symbol] = types[p.sort.name]
            action = upf.Action(a_name, parameters)
            action_parameters = {}
            for p in parameters.keys():
                action_parameters[p] = action.parameter(p)
            f = self._convert_formula(fluents, objects, action_parameters, a.precondition)
            action.add_precondition(f)
            for eff in a.effects:
                if isinstance(eff, AddEffect):
                    f = self._convert_formula(fluents, objects, action_parameters, eff.atom)
                    action.add_effect(f, True)
                elif isinstance(eff, DelEffect):
                    f = self._convert_formula(fluents, objects, action_parameters, eff.atom)
                    action.add_effect(f, False)
                elif isinstance(eff, FunctionalEffect):
                    lhs = self._convert_formula(fluents, objects, action_parameters, eff.lhs)
                    rhs = self._convert_formula(fluents, objects, action_parameters, eff.rhs)
                    action.add_effect(lhs, rhs)
                else:
                    raise UPFProblemDefinitionError(eff + ' not supported!')
            problem.add_action(action)

        # Set initial values
        initial_values = {}
        for fluent in fluents.values():
            l = [problem.objects(t) for t in fluent.signature()]
            if fluent.type().is_bool_type():
                default_value = self.em.FALSE()
            elif fluent.type().is_real_type():
                default_value = self.em.Real(Fraction(0))
            elif fluent.type().is_int_type():
                default_value = self.em.Int(0)
            if len(l) == 0:
                initial_values[self.em.FluentExp(fluent)] = default_value
            else:
                for args in itertools.product(*l):
                    initial_values[fluent(*args)] = default_value
        for i in tarski_problem.init.as_atoms():
            if isinstance(i, tuple):
                lhs = self._convert_formula(fluents, objects, {}, i[0])
                rhs = self._convert_formula(fluents, objects, {}, i[1])
                initial_values[lhs] = rhs
            else:
                f = self._convert_formula(fluents, objects, {}, i)
                initial_values[f] = self.em.TRUE()
        for lhs, rhs in initial_values.items():
            problem.set_initial_value(lhs, rhs)

        # Convert goals
        problem.add_goal(self._convert_formula(fluents, objects, {}, tarski_problem.goal))

        return problem

    def parse_problem(self, domain: str, problem: str) -> upf.Problem:
        self.reader.parse_domain(domain)
        problem = self.reader.parse_instance(problem)
        return self._convert_tarski_problem(problem)
