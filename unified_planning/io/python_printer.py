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
#​

from fractions import Fraction
import sys
import unified_planning
import unified_planning.environment
import unified_planning.walkers as walkers
from unified_planning.model import DurativeAction
from unified_planning.exceptions import UPTypeError, UPProblemDefinitionError
from typing import IO, Any, Optional
from io import StringIO
from functools import reduce

def _get_optional(x: Optional[Any]):
    if x:
        return str(x)
    return 'None'

# def _get_type(t: 'unified_planning.model.Type'):
#     if t.is_bool_type():
#         return 'tm.BoolType()'
#     elif t.is_int_type():
#         return f'tm.IntType({_get_optional(t.lower_bound())}, {_get_optional(t.upper_bound())})'
#     elif t.is_real_type():
#         return f'tm.RealType({_get_optional(t.lower_bound())}, {_get_optional(t.upper_bound())})'
#     elif t.is_user_type():
#         return f'tm.UserType("{t.name()}")'
#     else:
#         raise UPTypeError('Unknown type: %s' % t)


class ConverterToPythonString(walkers.DagWalker):
    '''Expression converter to a Python string.'''

    def __init__(self, env: 'unified_planning.environment.Environment'):
        walkers.DagWalker.__init__(self)
        self.simplifier = walkers.Simplifier(env)

    def convert(self, expression):
        '''Converts the given expression to a PDDL string.'''
        if expression is None:
            return 'None'
        return self.walk(self.simplifier.simplify(expression))

    def walk_exists(self, expression, args):
        assert len(args) == 1
        vars_string_list = [f'up.model.Variable("{v.name()}", {_print_python_type(v.type())})' for v in expression.variables()]
        return f'emgr.Exists([{", ".join(vars_string_list)}], {args[0]})'

    def walk_forall(self, expression, args):
        assert len(args) == 1
        vars_string_list = [f'up.model.Variable("{v.name()}", {_print_python_type(v.type())})' for v in expression.variables()]
        return f'emgr.Forall([{", ".join(vars_string_list)}], {args[0]})'


    def walk_variable_exp(self, expression, args):
        assert len(args) == 0
        v = expression.variable()
        return f'up.model.Variable("{v.name()}", {_print_python_type(v.type())})'

    def walk_and(self, expression, args):
        assert len(args) > 1
        return f'emgr.And({", ".join(args)})'

    def walk_or(self, expression, args):
        assert len(args) > 1
        return f'emgr.Or({", ".join(args)})'

    def walk_not(self, expression, args):
        assert len(args) == 1
        return f'emgr.Not({args[0]})'

    def walk_implies(self, expression, args):
        assert len(args) == 2
        return f'emgr.Implies({args[0]}, {args[1]})'

    def walk_iff(self, expression, args):
        assert len(args) == 2
        return f'emgr.Iff({args[0]}, {args[1]})'

    def walk_fluent_exp(self, expression, args):
        fluent = expression.fluent()
        if args:
            return f'fluent_{fluent.name()}({", ".join(args)})'
        return f'fluent_{fluent.name()}'

    def walk_param_exp(self, expression, args):
        assert len(args) == 0
        p = expression.parameter()
        return f'param{p.name()}'

    def walk_object_exp(self, expression, args):
        assert len(args) == 0
        o = expression.object()
        return f'obj_{o.name()}'

    def walk_bool_constant(self, expression, args):
        assert len(args) == 0
        if expression.bool_constant_value():
            return 'emgr.TRUE()'
        else:
            return 'emgr.FALSE()'

    def walk_real_constant(self, expression, args):
        assert len(args) == 0
        return f'emgr.Real("{str(expression.constant_value())}")'

    def walk_int_constant(self, expression, args):
        assert len(args) == 0
        return f'emgr.Int({str(expression.constant_value())})'

    def walk_plus(self, expression, args):
        assert len(args) > 1
        return f'emgr.Plus({", ".join(args)})'

    def walk_minus(self, expression, args):
        assert len(args) == 2
        return f'emgr.Minus({args[0]}, {args[1]})'

    def walk_times(self, expression, args):
        assert len(args) > 1
        return f'emgr.Times({", ".join(args)})'

    def walk_div(self, expression, args):
        assert len(args) == 2
        return f'emgr.Div({args[0]}, {args[1]})'

    def walk_le(self, expression, args):
        assert len(args) == 2
        return f'emgr.LE({args[0]}, {args[1]})'

    def walk_lt(self, expression, args):
        assert len(args) == 2
        return f'emgr.LT({args[0]}, {args[1]})'

    def walk_equals(self, expression, args):
        assert len(args) == 2
        return f'emgr.Equals({args[0]}, {args[1]})'


class PythonWriter:
    '''This class can be used to write a Problem in PDDL.'''

    def __init__(self, problem: 'unified_planning.model.Problem'):
        self.problem = problem

    def _write_domain(self, out: IO[str]):
        out.write('import unified_planning as up\n')
        out.write('env = up.environment.get_env()\n')
        out.write('emgr = env.expression_manager\n')
        out.write('tm = env.type_manager\n')
        out.write(f'problem = up.model.Problem("{self.problem.name}")\n')

        for t in self.problem.user_types():
            if t.father() is None:
                out.write(f'type_{t.name()} = tm.UserType("{t.name()}")\n')
            else:#TODO: make sure that the fathers are added before their sons in the Problem._user_types List
                out.write(f'type_{t.name()} = tm.UserType("{t.name()}", type_{t.father().name()})\n') 

        for f in self.problem.fluents():
            params = ', '.join(_print_python_type(p) for p in f.signature())
            out.write(f'fluent_{f.name()} = up.model.Fluent("{f.name()}", {_print_python_type(f.type())}, [{params}])\n')

        for o in self.problem.all_objects():
            out.write(f'object_{o.name()} = up.model.Object("{o.name()}", type_{o.type().name()})\n') #NOTE works if objects are only of user_type.

        converter = ConverterToPythonString(self.problem.env)
        for a in self.problem.actions():
            if isinstance(a, unified_planning.model.InstantaneousAction):
                out.write(f'act_{a.name} = up.model.InstantaneousAction("{a.name}"')
                for ap in a.parameters():
                    out.write(f', {ap.name()}={_print_python_type(ap.type())}')
                out.write(")\n")
                for ap in a.parameters():
                    out.write(f'parameter_{ap.name()} = act_{a.name}.parameter("{ap.name()}")\n')
                for p in a.preconditions():
                    out.write(f'act_{a.name}.add_precondition({converter.convert(p)})\n')
                for e in a.effects():
                    if e.is_increase():
                        out.write(f'act_{a.name}.add_increase_effect(fluent={converter.convert(e.fluent())}, value={converter.convert(e.value())}, condition={converter.convert(e.condition())})\n')
                    elif e.is_decrease():
                        out.write(f'act_{a.name}.add_decrease_effect(fluent={converter.convert(e.fluent())}, value={converter.convert(e.value())}, condition={converter.convert(e.condition())})\n')
                    else:
                        out.write(f'act_{a.name}.add_effect(fluent={converter.convert(e.fluent())}, value={converter.convert(e.value())}, condition={converter.convert(e.condition())})\n')
            elif isinstance(a, unified_planning.model.DurativeAction):
                out.write(f'act_{a.name} = up.model.DurativeAction("{a.name}"')
                for ap in a.parameters():
                    out.write(f', {ap.name()}={_print_python_type(ap.type())}')
                out.write(')\n')
                for ap in a.parameters():
                    out.write(f'parameter_{ap.name()} = act_{a.name}.parameter("{ap.name()}")\n')
                out.write(f'act_{a.name}.set_duration_constraint({_convert_interval_duration(a.duration())})\n')
                for c in a.conditions():
                    out.write(f'act_{a.name}.add_condition({converter.convert(c)})')
                for i, dc in a.durative_conditions():
                    out.write(f'act_{a.name}.add_durative_condition({_convert_interval(i)}, {converter.convert(dc)})')
                for t, e in a.effects():
                    if e.is_increase():
                        out.write(f'act_{a.name}.add_increase_effect(timing={_convert_timing(t)}, fluent={converter.convert(e.fluent())}, value={converter.convert(e.value())}, condition={converter.convert(e.condition())})\n')
                    elif e.is_decrease():
                        out.write(f'act_{a.name}.add_decrease_effect(timing={_convert_timing(t)}, fluent={converter.convert(e.fluent())}, value={converter.convert(e.value())}, condition={converter.convert(e.condition())})\n')
                    else:
                        out.write(f'act_{a.name}.add_effect(timing={_convert_timing(t)}, fluent={converter.convert(e.fluent())}, value={converter.convert(e.value())}, condition={converter.convert(e.condition())})\n')
            
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

    # def _write_problem(self, out: IO[str]):
    #     if self.problem.name is None:
    #         name = 'pddl'
    #     else:
    #         name = f'{self.problem.name}'
    #     out.write(f'(define (problem {name}-problem)\n')
    #     out.write(f' (:domain {name}-domain)\n')
    #     if len(self.problem.user_types()) > 0:
    #         out.write(' (:objects ')
    #         for t in self.problem.user_types():
    #             out.write(f'\n   {" ".join([o.name() for o in self.problem.objects(t)])} - {t.name()}') # type: ignore
    #         out.write('\n )\n')
    #     converter = ConverterToPDDLString(self.problem.env)
    #     out.write(' (:init')
    #     for f, v in self.problem.initial_values().items():
    #         if v.is_true():
    #             out.write(f' {converter.convert(f)}')
    #         elif v.is_false():
    #             pass
    #         else:
    #             out.write(f' (= {converter.convert(f)} {converter.convert(v)})')
    #     out.write(')\n')
    #     out.write(f' (:goal (and {" ".join([converter.convert(p) for p in self.problem.goals()])}))\n')
    #     out.write(')\n')

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

def _print_python_type(type: 'unified_planning.model.types.Type') -> str:
    '''This method takes a type and returns how to use it from command line.
    For the user_types it assumes they have already been created and just refers to them.'''
    if type.is_user_type():
        return f'type_{type.name()}'
    elif type.is_bool_type():
        return 'BoolType()'
    elif type.is_int_type():
        return f'IntType({str(type.lower_bound())}, {str(type.upper_bound())})'
    elif type.is_real_type():
        return f'RealType({str(type.lower_bound())}, {str(type.upper_bound())})'
    else:
        raise NotImplementedError

def _convert_timing(timing: unified_planning.model.Timing) -> str:
    bound: str = f'{str(timing.bound())}'
    if isinstance(timing.bound(), Fraction):
        bound = f'Fraction({str(timing.bound().numerator)}, {str(timing.bound().denomiantor)})'
    if timing.is_from_start():
        return f'StartTiming({bound})'
    else:
        return f'EndTiming({bound})'

def _convert_interval(interval: unified_planning.model.Interval) -> str:
    interval_feature: str = 'ClosedInterval'
    if interval.is_left_open() and interval.is_right_open():
        interval_feature = 'OpenInterval'
    elif interval.is_left_open() and not interval.is_right_open():
        interval_feature = 'LeftOpenInterval'
    elif not interval.is_left_open() and interval.is_right_open():
        interval_feature = 'RightOpenInterval'
    return f'{interval_feature}({_convert_interval(interval.lower())}, {_convert_interval(interval.upper())})'

def _convert_interval_duration(interval: unified_planning.model.IntervalDuration, converter: ConverterToPythonString) -> str:
    interval_feature: str = 'ClosedIntervalDuration'
    if interval.is_left_open() and interval.is_right_open():
        interval_feature = 'OpenIntervalDuration'
    elif interval.is_left_open() and not interval.is_right_open():
        interval_feature = 'LeftOpenIntervalDuration'
    elif not interval.is_left_open() and interval.is_right_open():
        interval_feature = 'RightOpenIntervalDuration'
    return f'{interval_feature}({converter.convert(interval.lower())}, {converter.convert(interval.upper())})'
