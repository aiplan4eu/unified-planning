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
from upf.environment import Environment, get_env
from pyparsing import Word, alphanums, alphas, ZeroOrMore, OneOrMore # type: ignore
from pyparsing import Optional, one_of, Suppress, nestedExpr, Group, restOfLine # type: ignore
from pyparsing.results import ParseResults # type: ignore
from collections import OrderedDict
from fractions import Fraction


name = Word(alphas, alphanums+'_'+'-')
variable = Suppress('?') + name

require_def = Suppress('(') + ':requirements' + \
    OneOrMore(one_of(':strips :typing :negative-preconditions :disjunctive-preconditions :equality :existential-preconditions :universal-preconditions :quantified-preconditions :conditional-effects :fluents :numeric-fluents :adl')) \
    + Suppress(')')

types_def = Suppress('(') + ':types' + \
    OneOrMore(Group(Group(OneOrMore(name)) + \
                    Optional(Suppress('-') + name))).setResultsName('types') \
    + Suppress(')')

constants_def = Suppress('(') + ':constants' + \
    OneOrMore(Group(Group(OneOrMore(name)) + \
                    Optional(Suppress('-') + name))).setResultsName('constants') \
    + Suppress(')')

predicate = Suppress('(') + \
    Group(name + Group(ZeroOrMore(Group(Group(OneOrMore(variable)) + \
                                             Optional(Suppress('-') + name))))) \
    + Suppress(')')

predicates_def = Suppress('(') + ':predicates' + \
    Group(OneOrMore(predicate)).setResultsName('predicates') \
    + Suppress(')')

functions_def = Suppress('(') + ':functions' + \
    Group(OneOrMore(predicate)).setResultsName('functions') \
    + Suppress(')')

parameters = OneOrMore(Group(Group(OneOrMore(variable)) \
                             + Optional(Suppress('-') + name))).setResultsName('params')
action_def = Group(Suppress('(') + ':action' + name.setResultsName('name') \
                   + Optional(':parameters' + Suppress('(') + parameters + Suppress(')')) \
                   + Optional(':precondition' + nestedExpr().setResultsName('pre')) \
                   + Optional(':effect' + nestedExpr().setResultsName('eff')) \
                   + Suppress(')'))

pp_domain = Suppress('(') + 'define' + Suppress('(') + 'domain' + name + Suppress(')') \
    + Optional(require_def) + Optional(types_def) + Optional(constants_def) \
    + Optional(predicates_def) + Optional(functions_def) \
    + Group(ZeroOrMore(action_def)).setResultsName('actions') + Suppress(')')

objects = OneOrMore(Group(Group(OneOrMore(name)) \
                          + Optional(Suppress('-') + name))).setResultsName('objects')
pp_problem = Suppress('(') + 'define' \
    + Suppress('(') + 'problem' + name.setResultsName('name') + Suppress(')') \
    + Suppress('(') + ':domain' + name + Suppress(')') + Optional(require_def) \
    + Optional(Suppress('(') + ':objects' + objects + Suppress(')')) \
    + Suppress('(') + ':init' + OneOrMore(nestedExpr()).setResultsName('init') + Suppress(')') \
    + Suppress('(') + ':goal' + nestedExpr().setResultsName('goal') + Suppress(')') \
    + Suppress(')')

pp_domain.ignore(';' + restOfLine)
pp_problem.ignore(';' + restOfLine)


class PDDLReader:
    """
    Parse a PDDL problem and generate a upf problem.
    """
    def __init__(self, env: Environment = None):
        self._env = get_env(env)
        self._em = self._env.expression_manager
        self._tm = self._env.type_manager
        self._operators = {
            'and' : self._em.And,
            'or' : self._em.Or,
            'not' : self._em.Not,
            'imply' : self._em.Implies,
            '>=' : self._em.GE,
            '<=' : self._em.LE,
            '>' : self._em.GT,
            '<' : self._em.LT,
            '=' : self._em.Equals,
            '+' : self._em.Plus,
            '-' : self._em.Minus,
            '/' : self._em.Div,
            '*' : self._em.Times
        }

    def _parse_exp(self, problem, act, var, exp):
        if isinstance(exp, ParseResults) and len(exp) == 0:
            return self._em.TRUE()
        elif isinstance(exp, ParseResults) and exp[0] == '-' and len(exp) == 2:
            return Times(-1, self._parse_exp(problem, act, var, exp[1]))
        elif isinstance(exp, ParseResults) and exp[0] in self._operators:
            op = self._operators[exp[0]]
            exp = exp[1:]
            return op(*[self._parse_exp(problem, act, var, e) for e in exp])
        elif isinstance(exp, ParseResults) and exp[0] in ['exists', 'forall']:
            op = Exists if exp[0] == 'exists' else Forall
            vars_string = ' '.join(exp[1])
            vars_res = parameters.parseString(vars_string)
            vars = {}
            for g in vars_res['params']:
                t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
                for o in g[0]:
                    vars[o] = upf.model.Variable(o, t)
            return op(self._parse_exp(problem, act, vars, exp[2]), *vars.values())
        elif isinstance(exp, ParseResults) and problem.has_fluent(exp[0]):
            f = problem.fluent(exp[0])
            args = [self._parse_exp(problem, act, var, e) for e in exp[1:]]
            return self._em.FluentExp(f, tuple(args))
        elif isinstance(exp, ParseResults) and len(exp) == 1:
            return self._parse_exp(problem, act, var, exp[0])
        elif isinstance(exp, str) and exp[0] == '?' and exp[1:] in var:
            return self._em.VariableExp(var[exp[1:]])
        elif isinstance(exp, str) and exp[0] == '?':
            return self._em.ParameterExp(act.parameter(exp[1:]))
        elif isinstance(exp, str) and problem.has_fluent(exp):
            return self._em.FluentExp(problem.fluent(exp))
        elif isinstance(exp, str) and problem.has_object(exp):
            return self._em.ObjectExp(problem.object(exp))
        elif isinstance(exp, str):
            return self._em.Real(Fraction(exp))
        else:
            raise Exception(f'Not able to handle: {exp}')

    def _add_eff(self, problem, act, exp, cond=True):
        op = exp[0]
        if op == 'and':
            exp = exp[1:]
            for e in exp:
                self._add_eff(problem, act, e)
        elif op == 'when':
            c = self._parse_exp(problem, act, {}, exp[1])
            self._add_eff(problem, acr, exp[2], cond)
        elif op == 'not':
            exp = exp[1]
            act.add_effect(self._parse_exp(problem, act, {}, exp), self._em.FALSE(), cond)
        elif op == 'assign':
            act.add_effect(self._parse_exp(problem, act, {}, exp[1]),
                           self._parse_exp(problem, act, {}, exp[2]), cond)
        elif op == 'increase':
            act.add_increase_effect(self._parse_exp(problem, act, {}, exp[1]),
                                    self._parse_exp(problem, act, {}, exp[2]), cond)
        elif op == 'decrease':
            act.add_decrease_effect(self._parse_exp(problem, act, {}, exp[1]),
                                    self._parse_exp(problem, act, {}, exp[2]), cond)
        else:
            act.add_effect(self._parse_exp(problem, act, {}, exp), self._em.TRUE(), cond)


    def parse_problem(self, domain_filename: str, problem_filename: str) -> 'upf.model.Problem':
        domain_res = pp_domain.parseFile(domain_filename)
        problem_res = pp_problem.parseFile(problem_filename)

        problem = upf.model.Problem(problem_res['name'], self._env,
                                    initial_defaults={self._tm.BoolType(): self._em.FALSE()})

        if 'predicates' in domain_res:
            for p in domain_res['predicates']:
                n = p[0]
                params = []
                for g in p[1]:
                    t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
                    params.extend([t for i in range(len(g[0]))])
                f = upf.model.Fluent(n, self._tm.BoolType(), params, self._env)
                problem.add_fluent(f)

        if 'functions' in domain_res:
            for p in domain_res['functions']:
                n = p[0]
                params = []
                for g in p[1]:
                    t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
                    params.extend([t for i in range(len(g[0]))])
                f = upf.model.Fluent(n, self._tm.RealType(), params, self._env)
                problem.add_fluent(f)

        if 'constants' in domain_res:
            for g in domain_res['constants']:
                t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
                for o in g[0]:
                    problem.add_object(upf.model.Object(o, t))

        if 'actions' in domain_res:
            for a in domain_res['actions']:
                n = a['name']
                a_params = OrderedDict()
                for g in a['params']:
                    t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
                    for p in g[0]:
                        a_params[p] = t
                act = upf.model.InstantaneousAction(n, a_params, self._env)
                pre = a['pre'][0]
                act.add_precondition(self._parse_exp(problem, act, {}, pre))
                eff = a['eff'][0]
                self._add_eff(problem, act, eff)
                problem.add_action(act)

        if 'objects' in problem_res:
            for g in problem_res['objects']:
                t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
                for o in g[0]:
                    problem.add_object(upf.model.Object(o, t))

        for i in problem_res['init']:
            if i[0] == '=':
                f = self._parse_exp(problem, None, {}, i[1])
                v = self._parse_exp(problem, None, {}, i[2])
                problem.set_initial_value(f, v)
            else:
                problem.set_initial_value(self._parse_exp(problem, None, {}, i), self._em.TRUE())

        problem.add_goal(self._parse_exp(problem, None, {}, problem_res['goal'][0]))

        return problem
