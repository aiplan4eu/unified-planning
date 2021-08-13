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

import sys
import upf.environment
import upf.walkers as walkers
from upf.simplifier import Simplifier
from upf.exceptions import UPFTypeError
from typing import IO
from io import StringIO
from functools import reduce


class ConverterToPDDLString(walkers.DagWalker):
    """Expression converter to a PDDL string."""

    def __init__(self, env: 'upf.environment.Environment'):
        walkers.DagWalker.__init__(self)
        self.simplifier = Simplifier(env)

    def convert(self, expression):
        """Converts the given expression to a PDDL string."""
        return self.walk(self.simplifier.simplify(expression))

    def walk_exists(self, expression, args):
        assert len(args) == 1
        vars = expression.variables()
        vars_string = "("
        for v in vars:
            vars_string = vars_string + "?"
            vars_string = vars_string + v.name()
            vars_string = vars_string + " - "
            vars_string = vars_string + str(v.type())
        vars_string = vars_string + ")"
        return f'(exists {vars_string}\n {args[0]})'

    def walk_forall(self, expression, args):
        assert len(args) == 1
        vars = expression.variables()
        vars_string = "("
        for v in vars:
            vars_string = vars_string + "?"
            vars_string = vars_string + v.name()
            vars_string = vars_string + " - "
            vars_string = vars_string + str(v.type())
        vars_string = vars_string + ")"
        return f'(forall {vars_string}\n {args[0]})'

    def walk_variable_exp(self, expression, args):
        assert len(args) == 0
        return f'?{expression.variable().name()}'

    def walk_and(self, expression, args):
        assert len(args) > 1
        return f'(and {" ".join(args)})'

    def walk_or(self, expression, args):
        assert len(args) > 1
        return f'(or {" ".join(args)})'

    def walk_not(self, expression, args):
        assert len(args) == 1
        return f'(not {args[0]})'

    def walk_implies(self, expression, args):
        assert len(args) == 2
        return f'(imply {args[0]} {args[1]})'

    def walk_iff(self, expression, args):
        assert len(args) == 2
        return f'(and (imply {args[0]} {args[1]}) (imply {args[1]} {args[0]}) )'

    def walk_fluent_exp(self, expression, args):
        fluent = expression.fluent()
        return f'({fluent.name()}{" " if len(args) > 0 else ""}{" ".join(args)})'

    def walk_param_exp(self, expression, args):
        assert len(args) == 0
        p = expression.parameter()
        return f'?{p.name()}'

    def walk_object_exp(self, expression, args):
        assert len(args) == 0
        o = expression.object()
        return f'{o.name()}'

    def walk_bool_constant(self, expression, args):
        raise

    def walk_real_constant(self, expression, args):
        assert len(args) == 0
        return str(expression.constant_value())

    def walk_int_constant(self, expression, args):
        assert len(args) == 0
        return str(expression.constant_value())

    def walk_plus(self, expression, args):
        assert len(args) > 1
        return reduce(lambda x, y: f'(+ {y} {x})', args)

    def walk_minus(self, expression, args):
        assert len(args) == 2
        return f'(- {args[0]} {args[1]})'

    def walk_times(self, expression, args):
        assert len(args) > 1
        return reduce(lambda x, y: f'(* {y} {x})', args)

    def walk_div(self, expression, args):
        assert len(args) == 2
        return f'(/ {args[0]} {args[1]})'

    def walk_le(self, expression, args):
        assert len(args) == 2
        return f'(<= {args[0]} {args[1]})'

    def walk_lt(self, expression, args):
        assert len(args) == 2
        return f'(< {args[0]} {args[1]})'

    def walk_equals(self, expression, args):
        assert len(args) == 2
        return f'(= {args[0]} {args[1]})'


class PDDLWriter:
    """This class can be used to write a Problem in PDDL."""

    def __init__(self, problem: 'upf.Problem', needs_requirements: bool = True):
        self.problem = problem
        self.needs_requirements = needs_requirements

    def _write_domain(self, out: IO[str]):
        out.write('(define ')
        if self.problem.name() is None:
            name = 'pddl'
        else:
            name = f'{self.problem.name()}'
        out.write(f'(domain {name}-domain)\n')

        if self.needs_requirements:
            out.write(' (:requirements :strips')
            if self.problem.kind().has_flat_typing(): # type: ignore
                out.write(' :typing')
            if self.problem.kind().has_negative_conditions(): # type: ignore
                out.write(' :negative-preconditions')
            if self.problem.kind().has_disjunctive_conditions(): # type: ignore
                out.write(' :disjunctive-preconditions')
            if self.problem.kind().has_equality(): # type: ignore
                out.write(' :equality')
            if (self.problem.kind().has_continuous_numbers() or # type: ignore
                self.problem.kind().has_discrete_numbers()): # type: ignore
                out.write(' :numeric-fluents')
            if self.problem.kind().has_conditional_effects(): # type: ignore
                out.write(' :conditional-effects')
            if self.problem.kind().has_existential_preconditions(): # type: ignore
                out.write(' :existential-preconditions')
            if self.problem.kind().has_universal_preconditions(): # type: ignore
                out.write(' :universal-preconditions')
            out.write(')\n')

        out.write(f' (:types {" ".join(self.problem.user_types().keys())})\n' if len(self.problem.user_types()) > 0 else '')

        predicates = []
        functions = []
        for f in self.problem.fluents().values():
            if f.type().is_bool_type():
                params = []
                i = 0
                for p in f.signature():
                    if p.is_user_type():
                        params.append(f' ?p{str(i)} - {p.name()}') # type: ignore
                        i += 1
                    else:
                        raise UPFTypeError('PDDL supports only user type parameters')
                predicates.append(f'({f.name()}{"".join(params)})')
            elif f.type().is_int_type() or f.type().is_real_type():
                params = []
                i = 0
                for p in f.signature():
                    if p.is_user_type():
                        params.append(f' ?p{str(i)} - {p.name()}') # type: ignore
                        i += 1
                    else:
                        raise UPFTypeError('PDDL supports only user type parameters')
                functions.append(f'({f.name()}{"".join(params)})')
            else:
                raise UPFTypeError('PDDL supports only boolean and numerical fluents')
        out.write(f' (:predicates {" ".join(predicates)})\n' if len(predicates) > 0 else '')
        out.write(f' (:functions {" ".join(functions)})\n' if len(functions) > 0 else '')

        converter = ConverterToPDDLString(self.problem.env)
        for a in self.problem.actions().values():
            out.write(f' (:action {a.name()}')
            out.write(f'\n  :parameters (')
            for ap in a.parameters():
                if ap.type().is_user_type():
                    out.write(f' ?{ap.name()} - {ap.type().name()}') # type: ignore
                else:
                    raise UPFTypeError('PDDL supports only user type parameters')
            out.write(')')
            if len(a.preconditions()) > 0:
                out.write(f'\n  :precondition (and {" ".join([converter.convert(p) for p in a.preconditions()])})')
            if len(a.effects()) > 0:
                out.write('\n  :effect (and')
                for e in a.effects():
                    if e.is_conditional():
                        out.write(f' (when {converter.convert(e.condition())}')
                    if e.value().is_true():
                        out.write(f' {converter.convert(e.fluent())}')
                    elif e.value().is_false():
                        out.write(f' (not {converter.convert(e.fluent())})')
                    elif e.is_increase():
                        out.write(f' (increase {converter.convert(e.fluent())} {converter.convert(e.value())})')
                    elif e.is_decrease():
                        out.write(f' (decrease {converter.convert(e.fluent())} {converter.convert(e.value())})')
                    else:
                        out.write(f' (assign {converter.convert(e.fluent())} {converter.convert(e.value())})')
                    if e.is_conditional():
                        out.write(f')')

                out.write(')')
            out.write(')\n')
        out.write(')\n')

    def _write_problem(self, out: IO[str]):
        if self.problem.name() is None:
            name = 'pddl'
        else:
            name = f'{self.problem.name()}'
        out.write(f'(define (problem {name}-problem)\n')
        out.write(f' (:domain {name}-domain)\n')
        if len(self.problem.user_types()) > 0:
            out.write(' (:objects ')
            for t in self.problem.user_types().values():
                out.write(f'\n   {" ".join([o.name() for o in self.problem.objects(t)])} - {t.name()}') # type: ignore
            out.write('\n )\n')
        converter = ConverterToPDDLString(self.problem.env)
        out.write(' (:init')
        for f, v in self.problem.initial_values().items():
            if v.is_true():
                out.write(f' {converter.convert(f)}')
            elif v.is_false():
                pass
            else:
                out.write(f' (= {converter.convert(f)} {converter.convert(v)})')
        out.write(')\n')
        out.write(f' (:goal (and {" ".join([converter.convert(p) for p in self.problem.goals()])}))\n')
        out.write(')\n')

    def print_domain(self):
        """Prints to std output the PDDL domain."""
        self._write_domain(sys.stdout)

    def print_problem(self):
        """Prints to std output the PDDL problem."""
        self._write_problem(sys.stdout)

    def get_domain(self) -> str:
        """Returns the PDDL domain."""
        out = StringIO()
        self._write_domain(out)
        return out.getvalue()

    def get_problem(self) -> str:
        """Returns the PDDL problem."""
        out = StringIO()
        self._write_problem(out)
        return out.getvalue()

    def write_domain(self, filename: str):
        """Dumps to file the PDDL domain."""
        with open(filename, 'w') as f:
            self._write_domain(f)

    def write_problem(self, filename: str):
        """Dumps to file the PDDL problem."""
        with open(filename, 'w') as f:
            self._write_problem(f)
