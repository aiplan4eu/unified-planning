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
import unified_planning
import unified_planning.environment
import unified_planning.walkers as walkers
from unified_planning.model import DurativeAction
from unified_planning.exceptions import UPTypeError, UPProblemDefinitionError
from typing import IO, List, Optional
from io import StringIO
from functools import reduce


class ConverterToPDDLString(walkers.DagWalker):
    '''Expression converter to a PDDL string.'''

    def __init__(self, env: 'unified_planning.environment.Environment'):
        walkers.DagWalker.__init__(self)
        self.simplifier = walkers.Simplifier(env)

    def convert(self, expression):
        '''Converts the given expression to a PDDL string.'''
        return self.walk(self.simplifier.simplify(expression))

    def walk_exists(self, expression, args):
        assert len(args) == 1
        vars_string_list = [f"?{v.name()} - {str(v.type())}" for v in expression.variables()]
        return f'(exists ({" ".join(vars_string_list)})\n {args[0]})'

    def walk_forall(self, expression, args):
        assert len(args) == 1
        vars_string_list = [f"?{v.name()} - {str(v.type())}" for v in expression.variables()]
        return f'(forall ({" ".join(vars_string_list)})\n {args[0]})'

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
    '''This class can be used to write a Problem in PDDL.'''

    def __init__(self, problem: 'unified_planning.model.Problem', needs_requirements: bool = True):
        self.problem = problem
        self.needs_requirements = needs_requirements

    def _write_domain(self, out: IO[str]):
        problem_kind = self.problem.kind()
        if problem_kind.has_intermediate_conditions_and_effects() or problem_kind.has_maintain_goals(): # type: ignore
            raise UPProblemDefinitionError('PDDL2.1 does not support ICE or maintained goals.\nICE are Intermediate Conditions and Effects therefore when an Effect (or Condition) are not at StartTIming(0) or EndTIming(0).')
        if problem_kind.has_timed_effect() or problem_kind.has_timed_goals(): # type: ignore
            raise UPProblemDefinitionError('PDDL2.1 does not support timed effects or timed goals.')
        out.write('(define ')
        if self.problem.name is None:
            name = 'pddl'
        else:
            name = f'{self.problem.name}'
        out.write(f'(domain {name}-domain)\n')

        if self.needs_requirements:
            out.write(' (:requirements :strips')
            if problem_kind.has_flat_typing(): # type: ignore
                out.write(' :typing')
            if problem_kind.has_negative_conditions(): # type: ignore
                out.write(' :negative-preconditions')
            if problem_kind.has_disjunctive_conditions(): # type: ignore
                out.write(' :disjunctive-preconditions')
            if problem_kind.has_equality(): # type: ignore
                out.write(' :equality')
            if (problem_kind.has_continuous_numbers() or # type: ignore
                problem_kind.has_discrete_numbers()): # type: ignore
                out.write(' :numeric-fluents')
            if problem_kind.has_conditional_effects(): # type: ignore
                out.write(' :conditional-effects')
            if problem_kind.has_existential_conditions(): # type: ignore
                out.write(' :existential-preconditions')
            if problem_kind.has_universal_conditions(): # type: ignore
                out.write(' :universal-preconditions')
            if (problem_kind.has_continuous_time() or # type: ignore
                problem_kind.has_discrete_time()): # type: ignore
                out.write(' :durative-actions')
            if problem_kind.has_duration_inequalities(): # type: ignore
                out.write(' :duration-inequalities')
            out.write(')\n')

        if problem_kind.has_hierarchical_typing(): # type: ignore
            self.object_freshname = 'object'
            while self.problem.has_type(self.object_freshname):
                self.object_freshname = self.object_freshname + '_'
            user_types_hierarchy = self.problem.user_types_hierarchy()
            out.write(f' (:types\n')
            stack: List['unified_planning.model.Type'] = user_types_hierarchy[None] if None in user_types_hierarchy else []
            out.write(f'    {" ".join(t.name() if t.name() != "object" else self.object_freshname for t in stack)} - object\n')  # type: ignore
            while stack:
                current_type = stack.pop()
                direct_sons: List['unified_planning.model.Type'] = user_types_hierarchy[current_type]
                if direct_sons:
                    stack.extend(direct_sons)
                    out.write(f'    {" ".join([t.name() if t.name() != "object" else self.object_freshname for t in direct_sons])} - {current_type.name() if current_type.name() != "object" else self.object_freshname}\n')  # type: ignore
            out.write(' )\n')
        else:
            out.write(f' (:types {" ".join([t.name() for t in self.problem.user_types()])})\n' if len(self.problem.user_types()) > 0 else '') # type: ignore

        predicates = []
        functions = []
        for f in self.problem.fluents():
            if f.type().is_bool_type():
                params = []
                i = 0
                for p in f.signature():
                    if p.is_user_type():
                        params.append(f' ?p{str(i)} - {p.name() if p.name() != "object" else self.object_freshname}') # type: ignore
                        i += 1
                    else:
                        raise UPTypeError('PDDL supports only user type parameters')
                predicates.append(f'({f.name()}{"".join(params)})')
            elif f.type().is_int_type() or f.type().is_real_type():
                params = []
                i = 0
                for p in f.signature():
                    if p.is_user_type():
                        params.append(f' ?p{str(i)} - {p.name() if p.name() != "object" else self.object_freshname}') # type: ignore
                        i += 1
                    else:
                        raise UPTypeError('PDDL supports only user type parameters')
                functions.append(f'({f.name()}{"".join(params)})')
            else:
                raise UPTypeError('PDDL supports only boolean and numerical fluents')
        out.write(f' (:predicates {" ".join(predicates)})\n' if len(predicates) > 0 else '')
        out.write(f' (:functions {" ".join(functions)})\n' if len(functions) > 0 else '')

        converter = ConverterToPDDLString(self.problem.env)
        for a in self.problem.actions():
            if isinstance(a, unified_planning.model.InstantaneousAction):
                out.write(f' (:action {a.name}')
                out.write(f'\n  :parameters (')
                for ap in a.parameters():
                    if ap.type().is_user_type():
                        out.write(f' ?{ap.name()} - {ap.type().name() if ap.type().name() != "object" else self.object_freshname}') # type: ignore
                    else:
                        raise UPTypeError('PDDL supports only user type parameters')
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
            elif isinstance(a, DurativeAction):
                out.write(f' (:durative-action {a.name}')
                out.write(f'\n  :parameters (')
                for ap in a.parameters():
                    if ap.type().is_user_type():
                        out.write(f' ?{ap.name()} - {ap.type().name() if ap.type().name() != "object" else self.object_freshname}') # type: ignore
                    else:
                        raise UPTypeError('PDDL supports only user type parameters')
                out.write(')')
                l, r = a.duration().lower(), a.duration().upper()
                if l == r:
                    out.write(f'\n  :duration (= ?duration {str(l)})')
                else:
                    out.write(f'\n  :duration (and ')
                    if a.duration().is_left_open():
                        out.write(f'(> ?duration {str(l)})')
                    else:
                        out.write(f'(>= ?duration {str(l)})')
                    if a.duration().is_right_open():
                        out.write(f'(< ?duration {str(r)})')
                    else:
                        out.write(f'(<= ?duration {str(r)})')
                    out.write(')')
                if len(a.conditions()) + len(a.durative_conditions()) > 0:
                    out.write(f'\n  :condition (and ')
                    for t, cl in a.conditions().items():
                        for c in cl:
                            if t.is_from_start():
                                out.write(f'(at start {converter.convert(c)})')
                            elif t.is_from_end():
                                out.write(f'(at end {converter.convert(c)})')
                    for interval, cl in a.durative_conditions().items():
                        for c in cl:
                            if not interval.is_left_open():
                                out.write(f'(at start {converter.convert(c)})')
                            out.write(f'(over all {converter.convert(c)})')
                            if not interval.is_right_open():
                                out.write(f'(at end {converter.convert(c)})')
                    out.write(')')
                if len(a.effects()) > 0:
                    out.write('\n  :effect (and')
                    for t, el in a.effects().items():
                        for e in el:
                            if t.is_from_start():
                                out.write(f' (at start')
                            else:
                                out.write(f' (at end')
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

                    out.write(')')
                out.write(')\n')
            else:
                raise NotImplementedError
        out.write(')\n')

    def _write_problem(self, out: IO[str]):
        if self.problem.name is None:
            name = 'pddl'
        else:
            name = f'{self.problem.name}'
        out.write(f'(define (problem {name}-problem)\n')
        out.write(f' (:domain {name}-domain)\n')
        if len(self.problem.user_types()) > 0:
            out.write(' (:objects ')
            for t in self.problem.user_types():
                objects: List['unified_planning.model.Object'] = list(self.problem.objects(t))
                if len(objects) > 0:
                    out.write(f'\n   {" ".join([o.name() for o in objects])} - {t.name() if t.name() != "object" else self.object_freshname}') # type: ignore
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
        '''Prints to std output the PDDL domain.'''
        self._write_domain(sys.stdout)

    def print_problem(self):
        '''Prints to std output the PDDL problem.'''
        self._write_problem(sys.stdout)

    def get_domain(self) -> str:
        '''Returns the PDDL domain.'''
        out = StringIO()
        self._write_domain(out)
        return out.getvalue()

    def get_problem(self) -> str:
        '''Returns the PDDL problem.'''
        out = StringIO()
        self._write_problem(out)
        return out.getvalue()

    def write_domain(self, filename: str):
        '''Dumps to file the PDDL domain.'''
        with open(filename, 'w') as f:
            self._write_domain(f)

    def write_problem(self, filename: str):
        '''Dumps to file the PDDL problem.'''
        with open(filename, 'w') as f:
            self._write_problem(f)
