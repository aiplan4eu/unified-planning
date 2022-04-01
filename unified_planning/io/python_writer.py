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


from fractions import Fraction
from itertools import count
import re
import sys
from unicodedata import name
import unified_planning as up
import unified_planning.walkers as walkers
from unified_planning.model.types import _UserType, _IntType, _RealType
from typing import Dict, IO, Optional, cast
from io import StringIO


class ConverterToPythonString(walkers.DagWalker):
    '''Expression converter to a Python string.'''

    def __init__(self, env: 'up.environment.Environment', names_mapping: Dict[str, str]):
        walkers.DagWalker.__init__(self)
        self._names_mapping = names_mapping

    def convert(self, expression):
        '''Converts the given expression to a PDDL string.'''
        if expression is None:
            return 'None'
        return self.walk(expression)

    def walk_exists(self, expression, args):
        assert len(args) == 1
        vars_string_list = [f'up.model.Variable("{v.name}", {_print_python_type(v.type, self._names_mapping)})' for v in expression.variables()]
        return f'emgr.Exists({args[0]}, {", ".join(vars_string_list)})'

    def walk_forall(self, expression, args):
        assert len(args) == 1
        vars_string_list = [f'up.model.Variable("{v.name}", {_print_python_type(v.type, self._names_mapping)})' for v in expression.variables()]
        return f'emgr.Forall({args[0]}, {", ".join(vars_string_list)})'

    def walk_variable_exp(self, expression, args):
        assert len(args) == 0
        v = expression.variable()
        return f'emgr.VariableExp(up.model.Variable("{v.name}", {_print_python_type(v.type, self._names_mapping)}))'

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
            return f'{_get_mangled_name(f"fluent_{fluent.name}", self._names_mapping)}({", ".join(args)})'
        return f'emgr.FluentExp({_get_mangled_name(f"fluent_{fluent.name}", self._names_mapping)})'

    def walk_param_exp(self, expression, args):
        assert len(args) == 0
        p = expression.parameter()
        return f'emgr.ParameterExp(up.model.Parameter("{p.name}", {_print_python_type(p.type, self._names_mapping)}))'

    def walk_object_exp(self, expression, args):
        assert len(args) == 0
        o = expression.object()
        return f'emgr.ObjectExp({_get_mangled_name(f"object_{o.name}", self._names_mapping)})'

    def walk_bool_constant(self, expression, args):
        assert len(args) == 0
        if expression.bool_constant_value():
            return 'emgr.TRUE()'
        else:
            return 'emgr.FALSE()'

    def walk_real_constant(self, expression, args):
        assert len(args) == 0
        return f'emgr.Real(Fraction({str(expression.real_constant_value().numerator)}, {str(expression.real_constant_value().denominator)}))'

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

    def __init__(self, problem: 'up.model.Problem'):
        self.problem = problem

    def _write_problem_code(self, out: IO[str]):

        names_mapping: Dict[str, str] = {}
        converter = ConverterToPythonString(self.problem.env, names_mapping)
        out.write('from fractions import Fraction\n')
        out.write('from collections import OrderedDict\n')
        out.write('import unified_planning as up\n')
        out.write('env = up.environment.get_env()\n')
        out.write('emgr = env.expression_manager\n')
        out.write('tm = env.type_manager\n')

        for type in self.problem.user_types: # define user_types
            utype = cast(_UserType, type)
            if utype.father is None:
                out.write(f'{_get_mangled_name(f"type_{utype.name}", names_mapping)} = tm.UserType("{utype.name}")\n')
            else:
                out.write(f'{_get_mangled_name(f"type_{utype.name}", names_mapping)} = tm.UserType("{utype.name}", {_get_mangled_name(f"type_{cast(_UserType, utype.father).name}", names_mapping)})\n')

        for f in self.problem.fluents: # define fluents
            params = ', '.join(f'("{p.name}", {_print_python_type(p.type, names_mapping)})' for p in f.signature)
            params = f'OrderedDict([{params}])'
            out.write(f'{_get_mangled_name(f"fluent_{f.name}", names_mapping)} = up.model.Fluent("{f.name}", {_print_python_type(f.type, names_mapping)}, _signature={params})\n')

        for o in self.problem.all_objects: # define objects
            out.write(f'{_get_mangled_name(f"object_{o.name}", names_mapping)} = up.model.Object("{o.name}", {_get_mangled_name(f"type_{cast(_UserType, o.type).name}", names_mapping)})\n')

        out.write('problem_initial_defaults = {}\n') # define initial_defaults
        for type, exp in self.problem.initial_defaults.items():
            out.write(f'problem_initial_defaults[{_print_python_type(type, names_mapping)}] = {converter.convert(exp)}\n')
        out.write(f'problem = up.model.Problem("{self.problem.name}", env, initial_defaults=problem_initial_defaults)\n')

        for o in self.problem.all_objects: # add objects to the problem
            out.write(f'problem.add_object({_get_mangled_name(f"object_{o.name}", names_mapping)})\n')

        for f in self.problem.fluents: # add fluents to the problem, with their fluents_default, if they have one
            default = self.problem.fluents_defaults.get(f, None)
            out.write(f'problem.add_fluent({_get_mangled_name(f"fluent_{f.name}", names_mapping)}')
            if default is not None: # the fluent has a default value
                out.write(f', default_initial_value={converter.convert(default)}')
            out.write(')\n')

        for a in self.problem.actions: # define actions and add them to the problem
            if isinstance(a, up.model.InstantaneousAction):
                params = ', '.join(f'("{p.name}", {_print_python_type(p.type, names_mapping)})' for p in a.parameters)
                params = f'OrderedDict([{params}])'
                out.write(f'{_get_mangled_name(f"act_{a.name}", names_mapping)} = up.model.InstantaneousAction("{a.name}", _parameters={params})\n')
                for p in a.preconditions:
                    out.write(f'{_get_mangled_name(f"act_{a.name}", names_mapping)}.add_precondition({converter.convert(p)})\n')
                for e in a.effects:
                    if e.is_increase():
                        out.write(f'{_get_mangled_name(f"act_{a.name}", names_mapping)}.add_increase_effect(fluent={converter.convert(e.fluent)}, value={converter.convert(e.value)}, condition={converter.convert(e.condition)})\n')
                    elif e.is_decrease():
                        out.write(f'{_get_mangled_name(f"act_{a.name}", names_mapping)}.add_decrease_effect(fluent={converter.convert(e.fluent)}, value={converter.convert(e.value)}, condition={converter.convert(e.condition)})\n')
                    else:
                        out.write(f'{_get_mangled_name(f"act_{a.name}", names_mapping)}.add_effect(fluent={converter.convert(e.fluent)}, value={converter.convert(e.value)}, condition={converter.convert(e.condition)})\n')
            elif isinstance(a, up.model.DurativeAction):
                out.write(f'{_get_mangled_name(f"act_{a.name}", names_mapping)} = up.model.DurativeAction("{a.name}"')
                for ap in a.parameters:
                    out.write(f', {ap.name}={_print_python_type(ap.type, names_mapping)}')
                out.write(')\n')
                for ap in a.parameters:
                    out.write(f'parameter_{ap.name} = {_get_mangled_name(f"act_{a.name}", names_mapping)}.parameter("{ap.name}")\n')
                out.write(f'{_get_mangled_name(f"act_{a.name}", names_mapping)}.set_duration_constraint({_convert_interval_duration(a.duration, converter)})\n')
                for i, cl in a.conditions.items():
                    for c in cl:
                        out.write(f'{_get_mangled_name(f"act_{a.name}", names_mapping)}.add_condition({_convert_interval(i)}, {converter.convert(c)})\n')
                for t, el in a.effects.items():
                    for e in el:
                        if e.is_increase():
                            out.write(f'{_get_mangled_name(f"act_{a.name}", names_mapping)}.add_increase_effect(timing={_convert_timing(t)}, fluent={converter.convert(e.fluent)}, value={converter.convert(e.value)}, condition={converter.convert(e.condition)})\n')
                        elif e.is_decrease():
                            out.write(f'{_get_mangled_name(f"act_{a.name}", names_mapping)}.add_decrease_effect(timing={_convert_timing(t)}, fluent={converter.convert(e.fluent)}, value={converter.convert(e.value)}, condition={converter.convert(e.condition)})\n')
                        else:
                            out.write(f'{_get_mangled_name(f"act_{a.name}", names_mapping)}.add_effect(timing={_convert_timing(t)}, fluent={converter.convert(e.fluent)}, value={converter.convert(e.value)}, condition={converter.convert(e.condition)})\n')
            else:
                raise NotImplementedError
            out.write(f'problem.add_action({_get_mangled_name(f"act_{a.name}", names_mapping)})\n')

        for f_exp, v_exp in self.problem.explicit_initial_values.items(): # add only previously added initial values
            out.write(f'problem.set_initial_value({converter.convert(f_exp)}, {converter.convert(v_exp)})\n')

        for t, el in self.problem.timed_effects.items(): # add timed effects
            for e in el:
                if e.is_increase():
                    out.write(f'problem.add_increase_effect(timing={_convert_timing(t)}, fluent={converter.convert(e.fluent)}, value={converter.convert(e.value)}, condition={converter.convert(e.condition)})\n')
                elif e.is_decrease():
                    out.write(f'problem.add_decrease_effect(timing={_convert_timing(t)}, fluent={converter.convert(e.fluent)}, value={converter.convert(e.value)}, condition={converter.convert(e.condition)})\n')
                else:
                    out.write(f'problem.add_timed_effect(timing={_convert_timing(t)}, fluent={converter.convert(e.fluent)}, value={converter.convert(e.value)}, condition={converter.convert(e.condition)})\n')

        for i, gl in self.problem.timed_goals.items(): # add timed goals
            for g in gl:
                out.write(f'problem.add_timed_goal(interval={_convert_interval(i)}, goal={converter.convert(g)})\n')

        for g in self.problem.goals: # add goals
            out.write(f'problem.add_goal(goal={converter.convert(g)})\n')

        for qm in self.problem.quality_metrics: # adding metrics
            if isinstance(qm, up.model.metrics.MinimizeActionCosts):
                out.write('costs = {}\n')
                for a, c in qm.costs.items():
                    out.write(f'costs[act_{a.name}] = {converter.convert(c)}\n')
            out.write('problem.add_quality_metric(')
            if isinstance(qm, up.model.metrics.MinimizeActionCosts):
                out.write(f'up.model.metrics.MinimizeActionCosts(costs, {qm.default})')
            elif isinstance(qm, up.model.metrics.MinimizeSequentialPlanLength):
                out.write('up.model.metrics.MinimizeSequentialPlanLength()')
            elif isinstance(qm, up.model.metrics.MinimizeMakespan):
                out.write('up.model.metrics.MinimizeMakespan()')
            elif isinstance(qm, up.model.metrics.MinimizeExpressionOnFinalState):
                out.write(f'up.model.metrics.MinimizeExpressionOnFinalState({converter.convert(qm.expression)})')
            elif isinstance(qm, up.model.metrics.MaximizeExpressionOnFinalState):
                out.write(f'up.model.metrics.MaximizeExpressionOnFinalState({converter.convert(qm.expression)})')
            else:
                raise NotImplementedError
            out.write(')\n')

    def print_problem_python_commands(self):
        '''Prints the string representing all the necessary commands to recreate the problem.'''
        self._write_problem_code(sys.stdout)

    def write_problem_code(self) -> str:
        '''Returns the string representing all the necessary commands to recreate the problem.'''
        out = StringIO()
        self._write_problem_code(out)
        return out.getvalue()

    def write_problem_code_to_file(self, filename: str):
        '''Dumps to file the PDDL domain.'''
        with open(filename, 'w') as f:
            self._write_problem_code(f)


def _get_mangled_name(original_name: str, names_mapping: Dict[str, str]) -> str:
    '''Important note: This method updates the nammes_mapping '''
    new_name: Optional[str] = names_mapping.get(original_name, None)
    if new_name is None: # The name is not in the map, so it must be added
        if not original_name.isidentifier(): # Make the name a python identifier
            new_name = re.sub('[^0-9a-zA-Z_]', '_', f'{original_name}')
        else:
            new_name = original_name
        test_name = new_name # Init values
        count = 0
        while test_name in names_mapping.values(): # Loop until we find a fresh name #NOTE is it a problem to always call names_mapping.values()? Is it better to define something like "invalid_names = [names_mapping.values()]" and use invalid_names instead?
            test_name = f'{new_name}_{str(count)}'
            count += 1
        new_name = test_name
        names_mapping[original_name] = new_name #Once a fresh valid name is found, update the map.
    assert new_name is not None
    assert new_name.isidentifier()
    return new_name

def _print_python_type(type: 'up.model.types.Type', names_mapping: Dict[str, str]) -> str:
    '''This method takes a type and returns how to use it from command line.
    For the user_types it assumes they have already been created and just refers to them.'''
    if type.is_user_type():
        return f'{_get_mangled_name(f"type_{cast(_UserType, type).name}", names_mapping)}'
    elif type.is_bool_type():
        return 'tm.BoolType()'
    elif type.is_int_type():
        itype = cast(_IntType, type)
        return f'tm.IntType({str(itype.lower_bound)}, {str(itype.upper_bound)})'
    elif type.is_real_type():
        rtype = cast(_RealType, type)
        return f'tm.RealType({str(rtype.lower_bound)}, {str(rtype.upper_bound)})'
    else:
        raise NotImplementedError

def _convert_timing(timing: up.model.Timing) -> str:
    delay: str = f'{str(timing.delay)}'
    if isinstance(timing.delay, Fraction):
        delay = f'Fraction({str(timing.delay.numerator)}, {str(timing.delay.denominator)})'
    if timing.is_from_start():
        return f'up.model.StartTiming({delay})'
    else:
        return f'up.model.EndTiming({delay})'

def _convert_interval(interval: up.model.TimeInterval) -> str:
    interval_feature: str = 'up.model.ClosedTimeInterval'
    if interval.is_left_open() and interval.is_right_open():
        interval_feature = 'up.model.OpenTimeInterval'
    elif interval.is_left_open() and not interval.is_right_open():
        interval_feature = 'up.model.LeftOpenTimeInterval'
    elif not interval.is_left_open() and interval.is_right_open():
        interval_feature = 'up.model.RightOpenTimeInterval'
    return f'{interval_feature}({_convert_timing(interval.lower)}, {_convert_timing(interval.upper)})'

def _convert_interval_duration(interval: up.model.DurationInterval, converter: ConverterToPythonString) -> str:
    interval_feature: str = 'up.model.ClosedDurationInterval'
    if interval.is_left_open() and interval.is_right_open():
        interval_feature = 'up.model.OpenDurationInterval'
    elif interval.is_left_open() and not interval.is_right_open():
        interval_feature = 'up.model.LeftOpenDurationInterval'
    elif not interval.is_left_open() and interval.is_right_open():
        interval_feature = 'up.model.RightOpenDurationInterval'
    return f'{interval_feature}({converter.convert(interval.lower)}, {converter.convert(interval.upper)})'
