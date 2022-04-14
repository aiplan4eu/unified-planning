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
import re
import sys

from decimal import Decimal, localcontext
from warnings import warn

import unified_planning as up
import unified_planning.environment
import unified_planning.walkers as walkers
from unified_planning.model import DurativeAction
from unified_planning.model.types import _UserType, _IntType, _RealType
from unified_planning.exceptions import UPTypeError, UPProblemDefinitionError
from typing import IO, Dict, List, Optional, cast
from io import StringIO
from functools import reduce


class ConverterToANMLString(walkers.DagWalker):
    '''Expression converter to an ANML string.'''

    DECIMAL_PRECISION = 10 # Number of decimal places to print real constants

    def __init__(self, env: 'up.environment.Environment'):
        walkers.DagWalker.__init__(self)
        self.simplifier = walkers.Simplifier(env)

    def convert(self, expression):
        '''Converts the given expression to a ANML string.'''
        return self.walk(self.simplifier.simplify(expression)) #NOTE maybe the converter could remove the first and last char, if they are '(' and ')'

    def walk_exists(self, expression, args):
        assert len(args) == 1
        vars_string_list = [f'{str(cast(_UserType, v.type).name)} {v.name}' for v in expression.variables()]
        return f'(exists({", ".join(vars_string_list)}) {{ {args[0]} }})' #NOTE i assumed vars are divided by ', '. #TODO check it

    def walk_forall(self, expression, args):
        assert len(args) == 1
        vars_string_list = [f'{str(cast(_UserType, v.type).name)} {v.name}' for v in expression.variables()]
        return f'(forall({", ".join(vars_string_list)}) {{ {args[0]} }})'

    def walk_variable_exp(self, expression, args):
        assert len(args) == 0
        return expression.variable().name

    def walk_and(self, expression, args):
        assert len(args) > 1
        return f'({" and ".join(args)})'

    def walk_or(self, expression, args):
        assert len(args) > 1
        return f'({" or ".join(args)})'

    def walk_not(self, expression, args):
        assert len(args) == 1
        return f'(not {args[0]})'

    def walk_implies(self, expression, args):
        assert len(args) == 2
        return f'({args[0]} implies {args[1]})'

    def walk_iff(self, expression, args):
        assert len(args) == 2
        return f'({args[0]} iff {args[1]})'

    def walk_fluent_exp(self, expression, args):
        fluent = expression.fluent()
        if len(args) == 0:
            return fluent.name
        else:
            return f'{fluent.name}({", ".join(args)})'

    def walk_param_exp(self, expression, args):
        assert len(args) == 0
        return expression.parameter().name

    def walk_object_exp(self, expression, args):
        assert len(args) == 0
        return expression.object().name

    def walk_bool_constant(self, expression, args):
        assert len(args) == 0
        if expression.bool_constant_value():
            return 'true'
        return 'false'

    def walk_real_constant(self, expression, args):#NOTE is this right? Same ANML Implementation
        assert len(args) == 0
        frac = expression.constant_value()

        with localcontext() as ctx:
            ctx.prec = self.DECIMAL_PRECISION
            dec = frac.numerator / Decimal(frac.denominator, ctx)

            if Fraction(dec) != frac:
                warn("The ANML printer cannot exactly represent the real constant '%s'" % frac)
            return str(dec)

    def walk_int_constant(self, expression, args):
        assert len(args) == 0
        return str(expression.constant_value())

    def walk_plus(self, expression, args):
        assert len(args) > 1
        return f"({' + '.join(args)})"

    def walk_minus(self, expression, args):
        assert len(args) == 2
        return f'({args[0]} - {args[1]})'

    def walk_times(self, expression, args):
        assert len(args) > 1
        return f"({' * '.join(args)})"

    def walk_div(self, expression, args):
        assert len(args) == 2
        return f'({args[0]} / {args[1]})'

    def walk_le(self, expression, args):
        assert len(args) == 2
        return f'({args[0]} <= {args[1]})'

    def walk_lt(self, expression, args):
        assert len(args) == 2
        return f'({args[0]} < {args[1]})'

    def walk_equals(self, expression, args):
        assert len(args) == 2
        return f'({args[0]} == {args[1]})'


class ANMLWriter:
    '''This class can be used to write a Problem in ANML.'''

    def __init__(self, problem: 'up.model.Problem'):
        self.problem = problem

    def _write_problem(self, out: IO[str]):
        types_mapping: Dict['up.model.Type', str] = {}
        # Init types_mapping.
        types_mapping[self.problem.env.type_manager.IntType()] = 'integer'
        types_mapping[self.problem.env.type_manager.RealType()] = 'rational'
        for t in self.problem.user_types:
            ut = cast(_UserType, t)
            if _is_valid_anml_name(ut.name): # No renaming needed
                types_mapping[t] = ut.name

        for t in self.problem.all_types:
            #NOTE If ANML does not accept a re-defintion of 'integer' or 'rational' or maybe also 'boolean', they must be skipped
            anml_type_name = _get_mangled_type_name(t, types_mapping)
            out.write(f'type {anml_type_name}')
            if t.is_bool_type() or (t.is_user_type() and cast(_UserType, t).father is None):
                out.write(';\n')
            elif t.is_user_type(): # and cast(_UserType, t).father is not None:
                # For construction in the Problem, the father of a UserType is always added before the UserType itself.
                father = cast(_UserType, t).father
                assert father is not None
                assert types_mapping[father] is not None
                out.write(f' < {types_mapping[father]};\n')
            elif (t.is_int_type() or t.is_real_type()) and cast(_IntType, t).lower_bound is None and cast(_IntType, t).upper_bound is None: #If first NOTE is True, this if is impossible
                out.write(';\n')
            elif t.is_int_type() and cast(_IntType, t).upper_bound is None: # and t.lower is not None
                out.write(f' < integer [{str(cast(_IntType, t).lower_bound)}, infinity);\n')
            elif  t.is_int_type() and cast(_IntType, t).lower_bound is None: # and t.upper is not None
                out.write(f' < integer (-infinity, {str(cast(_IntType, t).upper_bound)}];\n')
            elif t.is_int_type(): # and t.upper is not None and t.upper is not None
                out.write(f' < integer [{str(cast(_IntType, t).lower_bound)}, {str(cast(_IntType, t).upper_bound)}];\n')
            elif t.is_real_type() and cast(_RealType, t).upper_bound is None: # and t.lower is not None
                out.write(f' < rational [{str(cast(_RealType, t).lower_bound)}, infinity);\n')
            elif t.is_real_type() and cast(_RealType, t).lower_bound is None: # and t.upper is not None
                out.write(f' < rational (-infinity, {str(cast(_RealType, t).upper_bound)}];\n')
            elif t.is_real_type(): # and t.upper is not None and t.upper is not None
                out.write(f' < rational [{str(cast(_RealType, t).lower_bound)}, {str(cast(_RealType, t).upper_bound)}];\n')
            else:
                raise NotImplementedError

        for f in self.problem.fluents:
            out.write(f'fluent {_get_mangled_type_name(f.type, types_mapping)} {f.name};\n')
            #NOTE It could be nice to get the static fluents of the problem and define them as constants, if we do, also initial_values should change

        converter = ConverterToANMLString(self.problem.env)

        for a in self.problem.actions:
            if isinstance(a, up.model.InstantaneousAction):
                parameters = [f'{_get_mangled_type_name(ap.type, types_mapping)} {ap.name}' for ap in a.parameters]
                out.write(f'action {a.name}({", ".join(parameters)}) {{\n')
                for p in a.preconditions:
                    out.write(f'   [ start ] {converter.convert(p)};\n')
                for e in a.effects:
                    out.write(f'   {_convert_effect(e, converter)}')
                out.write('}\n')
            elif isinstance(a, DurativeAction):
                parameters = [f'{_get_mangled_type_name(ap.type, types_mapping)} {ap.name}' for ap in a.parameters]
                out.write(f'action {a.name}({", ".join(parameters)}) {{\n')
                out.write
                for i, cl in a.conditions.items():
                    for c in cl:
                        out.write(f'   {_convert_anml_interval(i)} {converter.convert(c)};\n')
                for ti, el in a.effects.items():
                    for e in el:
                        out.write(f'   {_convert_effect(e, converter, ti)}')
                out.write('}\n')
            else:
                raise NotImplementedError

        for t in self.problem.user_types: # Define objects
            objects: List['unified_planning.model.Object'] = list(self.problem.objects(t))
            obj_names = [o.name for o in self.problem.objects(t)]
            if len(objects) > 0:
                out.write(f'instance {_get_mangled_type_name(t, types_mapping)} {", ".join(obj_names)};\n')

        for fe, v in self.problem.initial_values.items():
            out.write(f'[ start ] {converter.convert(fe)} := {converter.convert(v)};\n')

        for ti, el in self.problem.timed_effects.items():
            for e in el:
                out.write(_convert_effect(e, converter, ti))

        for g in self.problem.goals:
            out.write(f'[ end ] {converter.convert(g)};\n')

        for i, gl in self.problem.timed_goals.items():
            for g in gl:
                out.write(f'{_convert_anml_interval(i)} {converter.convert(g)};\n')

    def print_problem(self):
        '''Prints to std output the ANML problem.'''
        self._write_problem(sys.stdout)

    def get_problem(self) -> str:
        '''Returns the ANML problem.'''
        out = StringIO()
        self._write_problem(out)
        return out.getvalue()

    def write_problem(self, filename: str):
        '''Dumps to file the ANML problem.'''
        with open(filename, 'w') as f:
            self._write_problem(f)

def _convert_effect(effect: 'up.model.Effect', converter: ConverterToANMLString, timing: 'up.model.Timing' = None) -> str:
    results: List[str] = []
    if effect.is_conditional():
        results.append(f'when [ all ] {converter.convert(effect.condition)}\n{{')
    if timing is not None:
        results.append(f'[ {_convert_anml_timing(timing)} ] ')
    else:
        results.append('[ start ] ')
    results.append(converter.convert(effect.fluent))
    if effect.is_assignment():
        results.append(' := ')
    elif effect.is_increase():
        results.append(' :+= ')
    elif effect.is_decrease():
        results.append(' :-= ')
    else:
        raise NotImplementedError
    results.append(f'{converter.convert(effect.value)};\n')
    if effect.is_conditional():
        results.append('}\n')
    return ''.join(results)

def _convert_anml_timing(timing: 'up.model.Timing') -> str:
    time = 'start' if timing.is_from_start() else 'end'
    if timing.delay > 0:
        return f'{time} + {str(timing.delay)}'
    elif timing.delay == 0:
        return time
    else: #timing.delay < 0
        return f'{time} - {str(timing.delay * (-1))}'

def _convert_anml_interval(interval: 'up.model.TimeInterval') -> str:
    left_bracket = '(' if interval.is_left_open() else '['
    right_bracket = ')' if interval.is_left_open() else ']'
    return f'{left_bracket} {_convert_anml_timing(interval.lower)}, {_convert_anml_timing(interval.upper)} {right_bracket}'

def _is_valid_anml_name(name: str) -> bool:
    regex = re.compile('^[a-zA-Z]+.*')
    if re.match(regex, name) is None: # If the name does not start with an alphabetic char.
        return False
    return name.isidentifier() #NOTE Here I am creating a dependency between python identifiers and ANML names. For now they are (almost) the same, but in future versions?

def _get_anml_valid_name(type) -> str:
    '''This function returns a valid ANML name.'''
    if type.is_bool_type():
        return 'boolean'
    elif type.is_user_type():
        name = cast(_UserType, type).name
        regex = re.compile('^[a-zA-Z]+.*')
        if re.match(regex, name) is None: # If the name does not start with an alphabetic char, we make it start with one.
            name = f't_{name}'
        return re.sub('[^0-9a-zA-Z_]', '_', name) #Substitute non-valid elements with "_"
    elif type.is_int_type():
        return 'integer'
    elif type.is_real_type():
        return 'rational'
    else:
        raise NotImplementedError

def _get_mangled_type_name(type: 'up.model.Type', types_mapping: Dict['up.model.Type', str]) -> str:
    '''Important note: This method updates the types_mapping '''
    new_name: Optional[str] = types_mapping.get(type, None)
    if new_name is None: # The type is not in the dictionary, so his name must be mangled and added
        new_name = _get_anml_valid_name(type)
        test_name = new_name # Init values
        count = 0
        while test_name in types_mapping.values(): # Loop until we find a fresh name
            test_name = f'{new_name}_{str(count)}'
            count += 1
        new_name = test_name
        types_mapping[type] = new_name # Once a fresh valid name is found, update the map.
    assert _is_valid_anml_name(new_name)
    return cast(str, new_name)
