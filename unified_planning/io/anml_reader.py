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

from itertools import product
import unified_planning as up
import unified_planning.model.htn as htn
import unified_planning.model.walkers
import pyparsing
import typing
from unified_planning.environment import Environment, get_env
from unified_planning.exceptions import UPUsageError
from unified_planning.model import FNode
from collections import OrderedDict
from fractions import Fraction
from typing import Dict, Union, Callable, List, cast
from pyparsing import Word, alphanums, alphas, nums, ZeroOrMore, OneOrMore, Keyword
from pyparsing import (
    Optional,
    Suppress,
    nestedExpr,
    Group,
    restOfLine,
    Combine,
    Forward,
)

if pyparsing.__version__ < "3.0.0":
    from pyparsing import oneOf as one_of
    from pyparsing import ParseResults
else:
    from pyparsing.results import ParseResults
    from pyparsing import one_of


class ANMLGrammar:
    def __init__(self):

        # Data structures to populate while parsing
        self.types: List[ParseResults] = []
        self.fluents: List[ParseResults] = []
        self.actions: List[ParseResults] = []
        self.objects: List[ParseResults] = []
        self.initial_values: List[ParseResults] = []
        self.goals: List[ParseResults] = []

        # supporting definitions
        L_PARENTHESIS, R_PARENTHESIS = map(Suppress, "()")
        L_BRACKET, R_BRACKET = map(Suppress, "[]")
        L_BRACE, R_BRACE = map(Suppress, "{}")
        SEMICOLON = Suppress(";")
        COMMA = Suppress(",")
        TK_ASSIGN = ":="
        TK_GOAL = "goal"
        name = Word(alphas + "_", alphanums + "_")
        parameters_decl = (
            L_PARENTHESIS
            + Optional(
                Group(Group(name + name) + ZeroOrMore(COMMA + Group(name + name)))
            )
            + R_PARENTHESIS
        )
        parameters_ref = Forward()

        # numeric expressions (with fluents and booleans)
        expr = Forward()
        integer = Word(nums)  # | Combine("-" + Word(nums))
        real = Combine(
            Word(nums) + "." + Word(nums)
        )  # | Combine("-" + Word(nums) + "." + Word(nums))
        fluent_ref = name + Optional(parameters_ref)  # TODO missing some definitions
        operand = real | integer | fluent_ref | "true" | "false"
        factor = operand | Group(L_PARENTHESIS + expr + R_PARENTHESIS)
        term = factor + ZeroOrMore(one_of("* /") + factor)
        assignment_expression = (
            fluent_ref + one_of([TK_ASSIGN, "increase", "decrease"]) + expr
        )
        expr <<= term + ZeroOrMore(one_of("+ -") + term) | assignment_expression
        parameters_ref = (
            L_PARENTHESIS + Group(ZeroOrMore(expr + Optional(COMMA))) + R_PARENTHESIS
        )

        # definitions supporting action body
        # duration_assignment = "duration :=" + Group(expr) + SEMICOLON #TODO Add interval assignment
        # assignment = fluent_ref + ":=" + Group(expr) + SEMICOLON
        # condition = (Group(expr) + "==" + Group(expr) | Group(fluent_ref)) + SEMICOLON
        # interval = L_BRACKET + one_of("start end all") + R_BRACKET
        # action_body = OneOrMore( # SHOULD be OneOrMore, just for testing is zero
        #     duration_assignment |
        #     Group(interval + Group(assignment)) |
        #     Group(interval + Group(condition))
        # )

        # type_def = Suppress("type") + name + SEMICOLON
        # type_def.setParseAction(lambda x: self.types.append(x))
        # fluent_def = SuppresALERT_DESCRIPTION_DECOMPRESSION_FAILURE= interval + L_BRACE + Group(OneOrMore(assignment)) + R_BRACE + SEMICOLON
        # initial_values_def.setParseAction(lambda x: self.initial_values.append(x))
        # goal_def = Suppress("goal") + interval + L_BRACE + Group(OneOrMore(condition)) + R_BRACE + SEMICOLON
        # goal_def.setParseAction(lambda x: self.goals.append(x))

        # element = (Group(type_def) |
        #             Group(fluent_def) |
        #             Group(action_def) |
        #             Group(objects_def) |
        #             Group(initial_values_def) |
        #             Group(goal_def))

        # problem = OneOrMore(element)

        ## 1 on 1 copy with the tamer anml parser

        interval = (
            one_of(["[", "("])
            + (Group(expr) | "all" | "start" | "end")
            + Optional(COMMA + Group(expr))
            + one_of(["]", ")"])
        )  # TODO missing last 3 definitions
        in_assignment_expression = ("duration :in" + interval) | ("duration :=" + expr)
        timed_expression = Optional(interval) + Group(expr)
        expression_block_body = ZeroOrMore(expr + SEMICOLON)
        expression_block = interval + L_BRACE + Group(expression_block_body) + R_BRACE
        action_body = ZeroOrMore(
            (expression_block | timed_expression | in_assignment_expression) + SEMICOLON
        )
        action_decl = Group(
            Suppress("action")
            + name
            + parameters_decl
            + L_BRACE
            + action_body
            + R_BRACE
        )  # TODO: MISSING annotation and process
        action_decl.setParseAction(lambda x: self.actions.append(x))
        primitive_type = (
            "boolean"
            | "integer"
            + Optional(Group(L_BRACKET + integer + COMMA + integer + R_BRACKET))
            | one_of(["float", "rational"])
            + Optional(Group(L_BRACKET + real + COMMA + real + R_BRACKET))
        )
        type_ref = (
            primitive_type | name
        )  # | "set" + "(" + type_ref + ")" -> TODO get the meaning of set()
        fluent_decl = Group(
            Suppress(one_of(["fluent", "constant"]))
            + type_ref
            + name
            + Group(Optional(parameters_decl))
            + Group(Optional(TK_ASSIGN + expr))
        )
        fluent_decl.setParseAction(lambda x: self.fluents.append(x))
        instance_decl = Group(
            Suppress("instance") + type_ref + Group(name + ZeroOrMore(COMMA + name))
        )
        instance_decl.setParseAction(lambda x: self.objects.append(x))
        type_decl = Group(
            Suppress("type") + name + ZeroOrMore(Group(Suppress("<") + name))
        )
        type_decl.setParseAction(lambda x: self.types.append(x))
        goal_body = OneOrMore(
            expression_block + SEMICOLON | timed_expression + SEMICOLON
        )
        goal_decl = TK_GOAL + (
            timed_expression | expression_block | L_BRACE + goal_body + R_BRACE
        )

        anml_stmt = (
            type_decl
            | fluent_decl
            | action_decl
            | instance_decl
            | timed_expression
            | expression_block
            | goal_decl
        )
        # annotation_decl)

        anml_body = OneOrMore(Group(anml_stmt + SEMICOLON))

        self._problem = anml_body

    @property
    def problem(self):
        return self._problem


class ANMLReader:
    """
    Parse a `PDDL` domain file and, optionally, a `PDDL` problem file and generate the equivalent :class:`~unified_planning.model.Problem`.
    """

    def __init__(self, env: typing.Optional[Environment] = None):
        self._env = get_env(env)
        self._em = self._env.expression_manager
        self._tm = self._env.type_manager
        grammar = ANMLGrammar()
        self.grammar = grammar
        self._pp_problem = grammar.problem
        self._fve = self._env.free_vars_extractor

    def parse_problem(self, problem_filename: str) -> "up.model.Problem":
        """
        Takes in input a filename containing the `PDDL` domain and optionally a filename
        containing the `PDDL` problem and returns the parsed `Problem`.

        Note that if the `problem_filename` is `None`, an incomplete `Problem` will be returned.

        :param domain_filename: The path to the file containing the `PDDL` domain.
        :param problem_filename: Optionally the path to the file containing the `PDDL` problem.
        :return: The `Problem` parsed from the given pddl domain + problem.
        """
        problem_res = self._pp_problem.parseFile(problem_filename)

        problem = up.model.Problem(
            problem_filename,
            self._env,
            initial_defaults={self._tm.BoolType(): self._em.FALSE()},
        )

        types_map: Dict[str, "up.model.Type"] = {}

        print(self.grammar.types)
        print(self.grammar.fluents)
        print(self.grammar.actions)
        print(self.grammar.objects)
        print(self.grammar.initial_values)
        print(self.grammar.goals)
        return problem
