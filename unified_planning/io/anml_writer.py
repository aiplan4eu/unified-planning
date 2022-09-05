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
import unified_planning as up
import unified_planning.environment
import unified_planning.model.walkers as walkers
from unified_planning.model import (
    DurativeAction,
    InstantaneousAction,
    Fluent,
    Parameter,
    Object,
)
from unified_planning.model.types import _UserType, _RealType, _IntType
from typing import IO, Dict, List, Optional, cast, Union
from io import StringIO

ANML_KEYWORDS = {
    "action",
    "and",
    "constant",
    "duration",
    "else",
    "fact",
    "fluent",
    "function",
    "goal",
    "in",
    "instance",
    "motivated",
    "predicate",
    "symbol",
    "variable",
    "when",
    "with",
    "decomposition",
    "use",
    "coincident",
    "comprise",
    "comprises",
    "contain",
    "contains",
    "exists",
    "forall",
    "implies",
    "iff",
    "not",
    "or",
    "ordered",
    "unordered",
    "xor",
    "UNDEFINED",
    "all",
    "end",
    "false",
    "infinity",
    "object",
    "start",
    "true",
    "boolean",
    "float",
    "rational",
    "integer",
    "string",
    "type",
    "set",
    "subset",
    "powerset",
    "intersect",
    "union",
    "elt",
}

# The following map is used to mangle the invalid names by their class.
INITIAL_LETTER: Dict[type, str] = {
    InstantaneousAction: "a",
    DurativeAction: "a",
    Fluent: "f",
    Parameter: "p",
    Object: "o",
}


class ConverterToANMLString(walkers.DagWalker):
    """Expression converter to an ANML string."""

    def __init__(
        self,
        names_mapping: Dict[
            Union[
                "up.model.Type",
                "up.model.Action",
                "up.model.Parameter",
                "up.model.Fluent",
                "up.model.Object",
            ],
            str,
        ],
        env: "up.environment.Environment",
    ):
        walkers.DagWalker.__init__(self)
        self._names_mapping = names_mapping
        self.simplifier = env.simplifier

    def convert(self, expression):
        """Converts the given expression to a ANML string."""
        return self.walk(
            self.simplifier.simplify(expression)
        )  # NOTE maybe the converter could remove the first and last char, if they are '(' and ')'

    def walk_exists(self, expression, args):
        assert len(args) == 1
        vars_string_gen = (
            f"{_get_anml_name(v.type, self._names_mapping)} {_get_anml_name(v, self._names_mapping)}"
            for v in expression.variables()
        )
        return f'(exists({", ".join(vars_string_gen)}) {{ {args[0]} }})'

    def walk_forall(self, expression, args):
        assert len(args) == 1
        vars_string_gen = (
            f"{_get_anml_name(v.type, self._names_mapping)} {_get_anml_name(v, self._names_mapping)}"
            for v in expression.variables()
        )
        return f'(forall({", ".join(vars_string_gen)}) {{ {args[0]} }})'

    def walk_variable_exp(self, expression, args):
        assert len(args) == 0
        return _get_anml_name(expression.variable(), self._names_mapping)

    def walk_and(self, expression, args):
        assert len(args) > 1
        return f'({" and ".join(args)})'

    def walk_or(self, expression, args):
        assert len(args) > 1
        return f'({" or ".join(args)})'

    def walk_not(self, expression, args):
        assert len(args) == 1
        return f"(not {args[0]})"

    def walk_implies(self, expression, args):
        assert len(args) == 2
        return f"({args[0]} implies {args[1]})"

    def walk_iff(self, expression, args):
        assert len(args) == 2
        return f"({args[0]} iff {args[1]})"

    def walk_fluent_exp(self, expression, args):
        if len(args) == 0:
            return self._names_mapping[expression.fluent()]
        else:
            return f'{self._names_mapping[expression.fluent()]}({", ".join(args)})'

    def walk_param_exp(self, expression, args):
        assert len(args) == 0
        return _get_anml_name(expression.parameter(), self._names_mapping)

    def walk_object_exp(self, expression, args):
        assert len(args) == 0
        return _get_anml_name(expression.object(), self._names_mapping)

    def walk_bool_constant(self, expression, args):
        assert len(args) == 0
        if expression.bool_constant_value():
            return "true"
        return "false"

    def walk_real_constant(self, expression, args):
        assert len(args) == 0
        frac = cast(Fraction, expression.constant_value())
        return f"({frac.numerator}/{frac.denominator})"

    def walk_int_constant(self, expression, args):
        assert len(args) == 0
        return str(expression.constant_value())

    def walk_plus(self, expression, args):
        assert len(args) > 1
        return f"({' + '.join(args)})"

    def walk_minus(self, expression, args):
        assert len(args) == 2
        return f"({args[0]} - {args[1]})"

    def walk_times(self, expression, args):
        assert len(args) > 1
        return f"({' * '.join(args)})"

    def walk_div(self, expression, args):
        assert len(args) == 2
        return f"({args[0]} / {args[1]})"

    def walk_le(self, expression, args):
        assert len(args) == 2
        return f"({args[0]} <= {args[1]})"

    def walk_lt(self, expression, args):
        assert len(args) == 2
        return f"({args[0]} < {args[1]})"

    def walk_equals(self, expression, args):
        assert len(args) == 2
        return f"({args[0]} == {args[1]})"


class ANMLWriter:
    """This class is used to write a :class:`~unified_planning.model.Problem` in `ANML`."""

    def __init__(self, problem: "up.model.Problem"):
        self.problem = problem

    def _write_problem(self, out: IO[str]):
        """
        Writes the `ANML` problem in the given IO[str].

        :param out: The `IO[str]` object on which the `ANML` problem is written.
        """
        names_mapping: Dict[
            Union[
                "up.model.Type",
                "up.model.Action",
                "up.model.Parameter",
                "up.model.Fluent",
                "up.model.Object",
            ],
            str,
        ] = {}
        # Init names_mapping.
        names_mapping[self.problem.env.type_manager.BoolType()] = "boolean"
        names_mapping[self.problem.env.type_manager.IntType()] = "integer"
        names_mapping[self.problem.env.type_manager.RealType()] = "float"
        for t in self.problem.user_types:
            ut = cast(_UserType, t)
            if _is_valid_anml_name(ut.name):  # No renaming needed
                names_mapping[t] = ut.name
        for a in self.problem.actions:
            if _is_valid_anml_name(a.name):  # No renaming needed
                names_mapping[a] = a.name
        for f in self.problem.fluents:
            if _is_valid_anml_name(f.name):  # No renaming needed
                names_mapping[f] = f.name
        for o in self.problem.all_objects:
            if _is_valid_anml_name(o.name):  # No renaming needed
                names_mapping[o] = o.name

        for t in self.problem.user_types:
            anml_type_name = _get_anml_name(t, names_mapping)
            out.write(f"type {anml_type_name}")
            if cast(_UserType, t).father is None:
                out.write(";\n")
            else:
                # For construction in the Problem, the father of a UserType is always added before the UserType itself.
                father = cast(_UserType, t).father
                assert father is not None
                assert names_mapping[father] is not None
                out.write(f" < {names_mapping[father]};\n")
        static_fluents = self.problem.get_static_fluents()
        for f in self.problem.fluents:
            parameters = [
                f"{_get_anml_name(ap.type, names_mapping)} {_get_anml_name(ap, names_mapping)}"
                for ap in f.signature
            ]
            params_written = f'({", ".join(parameters)})' if len(parameters) > 0 else ""
            if f in static_fluents:
                out.write(
                    f"constant {_get_anml_name(f.type, names_mapping)} {_get_anml_name(f, names_mapping)}{params_written};\n"
                )
            else:
                out.write(
                    f"fluent {_get_anml_name(f.type, names_mapping)} {_get_anml_name(f, names_mapping)}{params_written};\n"
                )

        converter = ConverterToANMLString(names_mapping, self.problem.env)

        for a in self.problem.actions:
            if isinstance(a, up.model.InstantaneousAction):
                parameters = [
                    f"{_get_anml_name(ap.type, names_mapping)} {_get_anml_name(ap, names_mapping)}"
                    for ap in a.parameters
                ]
                out.write(
                    f'action {_get_anml_name(a, names_mapping)}({", ".join(parameters)}) {{\n'
                )
                for p in a.preconditions:
                    out.write(f"   [ start ] {converter.convert(p)};\n")
                for e in a.effects:
                    out.write(f"   {self._convert_effect(e, converter, None, 3)}")
                out.write("};\n")
            elif isinstance(a, DurativeAction):
                parameters = [
                    f"{_get_anml_name(ap.type, names_mapping)} {_get_anml_name(ap, names_mapping)}"
                    for ap in a.parameters
                ]
                out.write(
                    f'action {_get_anml_name(a, names_mapping)}({", ".join(parameters)}) {{\n'
                )
                left_bound = " > " if a.duration.is_left_open() else " >= "
                right_bound = " < " if a.duration.is_right_open() else " <= "
                out.write(
                    f"   duration{left_bound}{converter.convert(a.duration.lower)} and "
                )
                out.write(
                    f"duration{right_bound}{converter.convert(a.duration.upper)};\n"
                )
                for i, cl in a.conditions.items():
                    for c in cl:
                        out.write(
                            f"   {self._convert_anml_interval(i)} {converter.convert(c)};\n"
                        )
                for ti, el in a.effects.items():
                    for e in el:
                        out.write(f"   {self._convert_effect(e, converter, ti, 3)}")
                out.write("};\n")
            else:
                raise NotImplementedError

        for t in self.problem.user_types:  # Define objects
            obj_names = [
                _get_anml_name(o, names_mapping)
                for o in self.problem.objects(t)
                if o.type == t
            ]
            if len(obj_names) > 0:
                out.write(
                    f'instance {_get_anml_name(t, names_mapping)} {", ".join(obj_names)};\n'
                )

        for fe, v in self.problem.initial_values.items():
            assert fe.is_fluent_exp()
            if fe.fluent() in static_fluents:
                out.write(f"{converter.convert(fe)} := {converter.convert(v)};\n")
            else:
                out.write(
                    f"[ start ] {converter.convert(fe)} := {converter.convert(v)};\n"
                )

        for ti, el in self.problem.timed_effects.items():
            for e in el:
                out.write(self._convert_effect(e, converter, ti))

        for g in self.problem.goals:
            out.write(f"[ end ] {converter.convert(g)};\n")

        for i, gl in self.problem.timed_goals.items():
            for g in gl:
                out.write(f"{self._convert_anml_interval(i)} {converter.convert(g)};\n")

    def print_problem(self):
        """Prints to std output the `ANML` problem."""
        self._write_problem(sys.stdout)

    def get_problem(self) -> str:
        """Returns the `ANML` problem."""
        out = StringIO()
        self._write_problem(out)
        return out.getvalue()

    def write_problem(self, filename: str):
        """
        Dumps to file the `ANML` problem.

        :param filename: The path to the file where the `ANML` problem must be written.
        """
        with open(filename, "w") as f:
            self._write_problem(f)

    def _convert_effect(
        self,
        effect: "up.model.Effect",
        converter: ConverterToANMLString,
        timing: "up.model.Timing" = None,
        spaces_from_left: int = 0,
    ) -> str:
        results: List[str] = []
        anml_timing = (
            self._convert_anml_timing(timing) if timing is not None else "start"
        )
        if effect.is_conditional():
            results.append(
                f'when [ {anml_timing} ] {converter.convert(effect.condition)}\n{spaces_from_left*" "}{{'
            )
        results.append(f"[ {anml_timing} ] ")
        results.append(converter.convert(effect.fluent))
        if effect.is_assignment():
            results.append(" := ")
        elif effect.is_increase():
            results.append(f" :increase ")
        elif effect.is_decrease():
            results.append(f" :decrease ")
        else:
            raise NotImplementedError
        results.append(f"{converter.convert(effect.value)};\n")
        if effect.is_conditional():
            results.append(f'{spaces_from_left*" "}}}\n')
        return "".join(results)

    def _convert_anml_timing(self, timing: "up.model.Timing") -> str:
        time = "start" if timing.is_from_start() else "end"
        if timing.delay > 0:
            return f"{time} + {str(timing.delay)}"
        elif timing.delay == 0:
            return time
        else:  # timing.delay < 0
            return f"{time} - {str(timing.delay * (-1))}"

    def _convert_anml_interval(self, interval: "up.model.TimeInterval") -> str:
        left_bracket = "(" if interval.is_left_open() else "["
        right_bracket = ")" if interval.is_left_open() else "]"
        return f"{left_bracket} {self._convert_anml_timing(interval.lower)}, {self._convert_anml_timing(interval.upper)} {right_bracket}"


def _is_valid_anml_name(name: str) -> bool:
    regex = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*")
    if (
        re.match(regex, name) is None or name in ANML_KEYWORDS
    ):  # If the name does not start with an alphabetic char or is a keyword
        return False
    return True


def _get_anml_valid_name(
    item: Union[
        "up.model.Type",
        "up.model.Action",
        "up.model.Parameter",
        "up.model.Fluent",
        "up.model.Object",
    ]
) -> str:
    """This function returns a valid ANML name."""
    if isinstance(item, up.model.Type):
        assert item.is_user_type()
        name = cast(_UserType, item).name
    else:
        name = item.name
    regex = re.compile(r"^[a-zA-Z]+.*")
    if (
        re.match(regex, name) is None
    ):  # If the name does not start with an alphabetic char, we make it start with one.
        name = f'{INITIAL_LETTER.get(type(item), "x")}_{name}'
    name = re.sub("[^0-9a-zA-Z_]", "_", name)  # Substitute non-valid elements with "_"
    while (
        name in ANML_KEYWORDS
    ):  # If the name is in the keywords, apply an underscore at the end until it is not a keyword anymore.
        name = f"{name}_"
    return name


def _get_anml_name(
    item: Union[
        "up.model.Type",
        "up.model.Action",
        "up.model.Parameter",
        "up.model.Fluent",
        "up.model.Object",
    ],
    names_mapping: Dict[
        Union[
            "up.model.Type",
            "up.model.Action",
            "up.model.Parameter",
            "up.model.Fluent",
            "up.model.Object",
        ],
        str,
    ],
) -> str:
    """Important note: This method updates the names_mapping"""
    new_name: Optional[str] = names_mapping.get(item, None)
    if new_name is None:  # The type is not in the dictionary, so his name must be added
        if isinstance(item, up.model.Type) and item.is_int_type():
            num_type = cast(_IntType, item)
            left_bound = (
                "(-infinity"
                if num_type.lower_bound is None
                else f"[{str(num_type.lower_bound)}"
            )
            right_bound = (
                "infinity)"
                if num_type.upper_bound is None
                else f"{str(num_type.upper_bound)}]"
            )
            new_name = f"integer {left_bound}, {right_bound}"
        elif isinstance(item, up.model.Type) and item.is_real_type():
            num_real_type = cast(_RealType, item)
            if num_real_type.lower_bound is None:
                left_bound = "(-infinity"
            elif num_real_type.lower_bound.denominator == 1:
                left_bound = f"[{str(num_real_type.lower_bound)}.0"
            else:
                left_bound = f"[{str(num_real_type.lower_bound)}"
            if num_real_type.upper_bound is None:
                right_bound = "infinity)"
            elif num_real_type.upper_bound.denominator == 1:
                right_bound = f"{str(num_real_type.upper_bound)}.0]"
            else:
                right_bound = f"{str(num_real_type.upper_bound)}]"
            new_name = f"float {left_bound}, {right_bound}"
        else:  # We mangle the name and get a fresh one
            new_name = _get_anml_valid_name(item)
            test_name = new_name  # Init values
            count = 0
            while (
                test_name in names_mapping.values()
            ):  # Loop until we find a fresh name
                test_name = f"{new_name}_{str(count)}"
                count += 1
            new_name = test_name
            assert _is_valid_anml_name(new_name)
        names_mapping[
            item
        ] = new_name  # Once a fresh valid name is found, update the map.
    return cast(str, new_name)
