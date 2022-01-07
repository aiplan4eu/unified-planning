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
    OneOrMore(one_of(':strips :typing :negative-preconditions :disjunctive-preconditions :equality :existential-preconditions :universal-preconditions :quantified-preconditions :conditional-effects :fluents :numeric-fluents :adl :durative-actions')) \
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
                   + ':parameters' + Suppress('(') + parameters + Suppress(')') \
                   + Optional(':precondition' + nestedExpr().setResultsName('pre')) \
                   + Optional(':effect' + nestedExpr().setResultsName('eff')) \
                   + Suppress(')'))

dur_action_def = Group(Suppress('(') + ':durative-action' + name.setResultsName('name') \
                       + ':parameters' + Suppress('(') + parameters + Suppress(')') \
                       + ':duration' + nestedExpr().setResultsName('duration') \
                       + ':condition' + nestedExpr().setResultsName('cond') \
                       + ':effect' + nestedExpr().setResultsName('eff') \
                       + Suppress(')'))

pp_domain = Suppress('(') + 'define' + Suppress('(') + 'domain' + name + Suppress(')') \
    + Optional(require_def) + Optional(types_def) + Optional(constants_def) \
    + Optional(predicates_def) + Optional(functions_def) \
    + Group(ZeroOrMore(action_def | dur_action_def)).setResultsName('actions') + Suppress(')')

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
            op = self._em.Exists if exp[0] == 'exists' else self._em.Forall
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
            raise upf.exceptions.UPFProblemDefinitionError(f'Not able to handle: {exp}')

    def _add_effect(self, problem, act, exp, cond=True, timing=None):
        op = exp[0]
        if op == 'and':
            exp = exp[1:]
            for e in exp:
                self._add_effect(problem, act, e, cond, timing)
        elif op == 'when':
            cond = self._parse_exp(problem, act, {}, exp[1])
            self._add_effect(problem, act, exp[2], cond, timing)
        elif op == 'not':
            exp = exp[1]
            eff = (self._parse_exp(problem, act, {}, exp), self._em.FALSE(), cond)
            act.add_effect(*eff if timing is None else (timing, *eff))
        elif op == 'assign':
            eff = (self._parse_exp(problem, act, {}, exp[1]),
                   self._parse_exp(problem, act, {}, exp[2]), cond)
            act.add_effect(*eff if timing is None else (timing, *eff))
        elif op == 'increase':
            eff = (self._parse_exp(problem, act, {}, exp[1]),
                   self._parse_exp(problem, act, {}, exp[2]), cond)
            act.add_increase_effect(*eff if timing is None else (timing, *eff))
        elif op == 'decrease':
            eff = (self._parse_exp(problem, act, {}, exp[1]),
                   self._parse_exp(problem, act, {}, exp[2]), cond)
            act.add_decrease_effect(*eff if timing is None else (timing, *eff))
        else:
            eff = (self._parse_exp(problem, act, {}, exp), self._em.TRUE(), cond)
            act.add_effect(*eff if timing is None else (timing, *eff))

    def _add_condition(self, problem, act, exp, vars=None):
        op = exp[0]
        if op == 'and':
            for e in exp[1:]:
                self._add_condition(problem, act, e, vars)
        elif op == 'forall':
            vars_string = ' '.join(exp[1])
            vars_res = parameters.parseString(vars_string)
            if vars is None:
                vars = {}
            for g in vars_res['params']:
                t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
                for o in g[0]:
                    vars[o] = upf.model.Variable(o, t)
            self._add_condition(problem, act, exp[2], vars)
        elif len(exp) == 3 and op == 'at' and exp[1] == 'start':
            cond = self._parse_exp(problem, act, {} if vars is None else vars, exp[2])
            if vars is not None:
                cond = self._em.Forall(cond, *vars.values())
            act.add_condition(upf.model.StartTiming(), cond)
        elif len(exp) == 3 and op == 'at' and exp[1] == 'end':
            cond = self._parse_exp(problem, act, {} if vars is None else vars, exp[2])
            if vars is not None:
                cond = self._em.Forall(cond, *vars.values())
            act.add_condition(upf.model.EndTiming(), cond)
        elif len(exp) == 3 and op == 'over' and exp[1] == 'all':
            t_all = upf.model.ClosedInterval(upf.model.StartTiming(), upf.model.EndTiming())
            cond = self._parse_exp(problem, act, {} if vars is None else vars, exp[2])
            if vars is not None:
                cond = self._em.Forall(cond, *vars.values())
            act.add_durative_condition(t_all, cond)
        else:
            raise upf.exceptions.UPFProblemDefinitionError(f'Not able to handle: {exp}')

    def _add_timed_effects(self, problem, act, eff):
        op = eff[0]
        if op == 'and':
            for e in eff[1:]:
                self._add_timed_effects(problem, act, e)
        elif len(eff) == 3 and op == 'at' and eff[1] == 'start':
            self._add_effect(problem, act, eff[2], timing=upf.model.StartTiming())
        elif len(eff) == 3 and op == 'at' and eff[1] == 'end':
            self._add_effect(problem, act, eff[2], timing=upf.model.EndTiming())
        else:
            raise upf.exceptions.UPFProblemDefinitionError(f'Not able to handle: {eff}')


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
                if 'duration' in a:
                    dur_act = upf.model.DurativeAction(n, a_params, self._env)
                    dur = a['duration'][0]
                    if dur[0] == '=':
                        dur_act.set_fixed_duration(self._parse_exp(problem, dur_act,
                                                                   {}, dur[2]))
                    elif dur[0] == 'and':
                        upper = None
                        lower = None
                        for j in range(1, len(dur)):
                            v = Fraction(dur[j][2])
                            if dur[j][0] == '>=':
                                if lower is None or v > lower:
                                    lower = v
                            elif dur[j][0] == '<=':
                                if upper is None or v < upper:
                                    upper = v
                            else:
                                raise upf.exceptions.UPFProblemDefinitionError(f'Not able to handle duration constraint of action {n}')
                        if lower is None or upper is None:
                            raise upf.exceptions.UPFProblemDefinitionError(f'Not able to handle duration constraint of action {n}')
                        d = upf.model.ClosedIntervalDuration(self._em.Real(lower),
                                                             self._em.Real(upper))
                        dur_act.set_duration_constraint(d)
                    else:
                        raise upf.exceptions.UPFProblemDefinitionError(f'Not able to handle duration constraint of action {n}')
                    cond = a['cond'][0]
                    self._add_condition(problem, dur_act, cond)
                    eff = a['eff'][0]
                    self._add_timed_effects(problem, dur_act, eff)
                    problem.add_action(dur_act)
                else:
                    act = upf.model.InstantaneousAction(n, a_params, self._env)
                    pre = a['pre'][0]
                    act.add_precondition(self._parse_exp(problem, act, {}, pre))
                    eff = a['eff'][0]
                    self._add_effect(problem, act, eff)
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
            elif len(i) == 3 and i[0] == 'at' and i[1].replace('.','',1).isdigit():
                ti = upf.model.StartTiming(Fraction(i[1]))
                va = self._parse_exp(problem, None, {}, i[2])
                if va.is_fluent_exp():
                    problem.add_timed_effect(ti, va, self._em.TRUE())
                elif va.is_not():
                    problem.add_timed_effect(ti, va.arg(0), self._em.FALSE())
                elif va.is_equals():
                    problem.add_timed_effect(ti, va.arg(0), va.arg(1))
                else:
                    raise upf.exceptions.UPFProblemDefinitionError(f'Not able to handle this TIL {i}')
            else:
                problem.set_initial_value(self._parse_exp(problem, None, {}, i), self._em.TRUE())

        problem.add_goal(self._parse_exp(problem, None, {}, problem_res['goal'][0]))

        return problem
