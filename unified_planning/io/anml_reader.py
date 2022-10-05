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
    infixNotation,
    opAssoc,
    ParserElement,
    Literal,
)

if pyparsing.__version__ < "3.0.0":
    from pyparsing import oneOf as one_of
    from pyparsing import ParseResults
else:
    from pyparsing.results import ParseResults
    from pyparsing import one_of

# ANMl keywords definition as tokens
TK_COMMA = ","
TK_SEMI = ";"
TK_COLON = ":"
TK_ASSIGN = ":="
TK_INCREASE = ":+="
TK_DECREASE = ":-="
TK_IN_ASSIGN = ":in"
TK_ANNOTATION = "::"
TK_L_BRACE = "{"
TK_R_BRACE = "}"
TK_L_BRACKET = "["
TK_R_BRACKET = "]"
TK_L_PARENTHESIS = "("
TK_R_PARENTHESIS = ")"
TK_MINUS = "-"
TK_SQRT = "sqrt"
TK_PLUS = "+"
TK_TIMES = "*"
TK_DIV = "/"
TK_LE = "<="
TK_GE = ">="
TK_GT = ">"
TK_LT = "<"
TK_EQUALS = "=="
TK_NOT_EQUALS = "!="
TK_DOT = "."
TK_FORALL = "forall"
TK_IN = "in"
TK_SUBSET = "subset"
TK_UNION = "union"
TK_INTERSECTION = "intersection"
TK_DIFFERENCE = "\\"
TK_ACTION = "action"
TK_PROCESS = "process"
TK_TYPE = "type"
TK_INSTANCE = "instance"
TK_FLUENT = "fluent"
TK_CONSTANT = "constant"
TK_WITH = "with"
TK_GOAL = "goal"
TK_CONTAINS = "contains"
TK_BOOLEAN = "boolean"
TK_INTEGER = "integer"
TK_FLOAT = one_of(["float", "rational"])  # NOTE both are possible here
TK_SET = "set"
TK_ALL = "all"
TK_START = "start"
TK_END = "end"
TK_DURATION = "duration"
TK_TIME = "#t"
TK_AND = "and"
TK_OR = "or"
TK_XOR = "xor"
TK_IMPLIES = "implies"
TK_NOT = "not"
TK_TRUE = "true"
TK_FALSE = "false"


class ANMLGrammar:
    def __init__(self):

        # Data structures to populate while parsing
        self.types: List[ParseResults] = []
        self.fluents: List[ParseResults] = []
        self.actions: List[ParseResults] = []
        self.objects: List[ParseResults] = []
        self.timed_assignments_or_goals: List[ParseResults] = []
        self.timed_assignment_or_goal: List[ParseResults] = []

        # Base Expression elements
        identifier = Word(alphas + "_", alphanums + "_")
        integer = Word(nums)  # | Combine("-" + Word(nums))
        real = Combine(
            Word(nums) + "." + Word(nums)
        )  # | Combine("-" + Word(nums) + "." + Word(nums))
        float_const = integer | real
        boolean_const = one_of([TK_TRUE, TK_FALSE])

        # Expression definitions
        interval = Forward()
        boolean_expression = Forward()
        forall_expression = Forward()

        expression_list = Optional(Group(boolean_expression)) + ZeroOrMore(
            Suppress(TK_COMMA) + Group(boolean_expression)
        )
        fluent_ref = identifier + Group(
            Optional(  # missing dot definitions
                Suppress(TK_L_PARENTHESIS)
                + expression_list
                + Suppress(TK_R_PARENTHESIS)
            )
        )

        arithmetic_expression = infixNotation(
            boolean_const
            | Literal(TK_START)
            | Literal(TK_END)
            | float_const
            | fluent_ref,
            [
                (one_of([TK_PLUS, TK_MINUS]), 1, opAssoc.RIGHT),
                (one_of([TK_TIMES, TK_DIV]), 2, opAssoc.LEFT),
                (one_of([TK_PLUS, TK_MINUS]), 2, opAssoc.LEFT),
            ],
        )
        relations_expression = infixNotation(
            arithmetic_expression,
            [
                (
                    one_of([TK_LT, TK_LE, TK_GT, TK_GE, TK_EQUALS, TK_NOT_EQUALS]),
                    2,
                    opAssoc.LEFT,
                ),  # IN, SUBSET, UNION, INTERSECTION, DIFFERENCE missing #TODO check if they go there
                (one_of([TK_ASSIGN, TK_INCREASE, TK_DECREASE]), 2, opAssoc.LEFT),
            ],
        )
        boolean_expression <<= infixNotation(
            relations_expression | boolean_const,
            [
                (TK_NOT, 1, opAssoc.RIGHT),
                (one_of([TK_AND, TK_OR]), 2, opAssoc.LEFT),
            ],
        )
        expression = boolean_expression | forall_expression

        timed_expression = Group(Optional(interval)).setResultsName("interval") + Group(
            expression
        ).setResultsName("expression")

        expression_block_body = OneOrMore(Group(expression) + Suppress(TK_SEMI))
        expression_block = (
            Group(interval).setResultsName("interval")
            + TK_L_BRACE
            + Group(expression_block_body).setResultsName("body")
            + TK_R_BRACE
        )

        temporal_expression = arithmetic_expression

        in_assignment_expression = (
            TK_DURATION
            + TK_IN_ASSIGN
            + TK_L_BRACKET
            + Group(temporal_expression).setResultsName("left_bound")
            + TK_COMMA
            + Group(temporal_expression).setResultsName("right_bound")
            + TK_R_BRACKET
        )
        action_body = ZeroOrMore(
            (expression_block | timed_expression | in_assignment_expression)
            + Suppress(TK_SEMI)
        )

        # missing class stmt and class body definitions
        type_decl = Group(  # missing "TK_TYPE TK_IDENTIFIER opt_inheritance_list TK_WITH TK_L_BRACE class_body TK_R_BRACE"
            Suppress(TK_TYPE)
            + identifier.setResultsName("name")
            + Group(ZeroOrMore(Suppress(TK_LT) + identifier)).setResultsName(
                "supertypes"
            )
        )
        type_decl.setParseAction(lambda x: self.types.append(x))
        identifier_list = identifier + ZeroOrMore(Suppress(TK_COMMA) + identifier)
        primitive_type = (
            Literal(TK_BOOLEAN).setResultsName("type_name")
            | (
                Literal(TK_INTEGER).setResultsName("type_name")
                + Optional(
                    Group(
                        TK_L_BRACKET
                        + integer.setResultsName("left_bound")
                        + TK_COMMA
                        + integer.setResultsName("right_bound")
                        + TK_R_BRACKET
                    )
                )
            )
            | (
                TK_FLOAT.setResultsName("type_name")
                + Optional(
                    Group(
                        TK_L_BRACKET
                        + real.setResultsName("left_bound")
                        + TK_COMMA
                        + real.setResultsName("right_bound")
                        + TK_R_BRACKET
                    )
                )
            )
        )
        type_ref = (
            primitive_type | identifier
        )  # | "set" + "(" + type_ref + ")" -> TODO get the meaning of set()
        instance_decl = Group(Suppress(TK_INSTANCE) + type_ref + Group(identifier_list))
        instance_decl.setParseAction(lambda x: self.objects.append(x))

        parameter_list = Optional(Group(type_ref) + identifier) + ZeroOrMore(
            Suppress(TK_COMMA) + Group(type_ref) + identifier
        )
        fluent_decl = Group(
            Suppress(one_of([TK_FLUENT, TK_CONSTANT]))
            + type_ref
            + identifier
            + Optional(
                Suppress(TK_L_PARENTHESIS)
                + Group(parameter_list)
                + Suppress(TK_R_PARENTHESIS)
            )
            # + Optional(TK_ASSIGN + Group(expression))
        )
        fluent_decl.setParseAction(lambda x: self.fluents.append(x))
        # annotation list... TODO
        action_decl = Group(
            Suppress("action")
            + identifier
            + Suppress(TK_L_PARENTHESIS)
            + Group(parameter_list)
            + Suppress(TK_R_PARENTHESIS)
            + Suppress(TK_L_BRACE)
            + Group(action_body)
            + Suppress(TK_R_BRACE)
        )  # TODO: MISSING annotation and process
        action_decl.setParseAction(lambda x: self.actions.append(x))
        interval <<= (
            one_of([TK_L_BRACKET, TK_L_PARENTHESIS])
            + (
                (
                    Group(temporal_expression)
                    + Optional(TK_COMMA + Group(temporal_expression))
                )
                | TK_ALL
            )
            + one_of([TK_R_BRACKET, TK_R_PARENTHESIS])
        )  # | (
        #     interval
        #     + (
        #         (
        #             TK_CONTAINS
        #             + Optional(
        #                 TK_L_BRACKET + Group(arithmetic_expression) + TK_R_BRACKET
        #             )
        #         )
        #         | identifier + TK_COLON
        #     )
        # )
        forall_expression <<= (
            TK_FORALL
            + TK_L_PARENTHESIS
            + Group(parameter_list)
            + TK_R_PARENTHESIS
            + TK_L_BRACE
            + action_body
            + TK_R_BRACE
        )
        # Standalone expressions are defined to handle differently expressions
        # defined inside an action from the expressions defined outside an action
        standalone_timed_expression = timed_expression.copy()
        standalone_timed_expression.setParseAction(
            lambda x: self.timed_assignment_or_goal.append(x)
        )
        standalone_expression_block = expression_block.copy()
        standalone_expression_block.setParseAction(
            lambda x: self.timed_assignments_or_goals.append(x)
        )

        goal_body = OneOrMore(
            (standalone_expression_block | standalone_timed_expression)
            + Suppress(TK_SEMI)
        )
        goal_decl = TK_GOAL + (
            standalone_timed_expression
            | standalone_expression_block
            | TK_L_BRACE + goal_body + TK_R_BRACE
        )
        anml_stmt = (
            instance_decl
            | type_decl
            | fluent_decl
            | action_decl
            | standalone_expression_block
            | goal_decl
            | standalone_timed_expression
        )
        # annotation_decl)

        anml_body = OneOrMore(Group(anml_stmt + Suppress(TK_SEMI)))

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

        # print(str(self.grammar.types).replace("ParseResults", ""))
        # print(str(self.grammar.fluents).replace("ParseResults", ""))
        # print(str(self.grammar.actions).replace("ParseResults", ""))
        # print(str(self.grammar.objects).replace("ParseResults", ""))
        print(str(self.grammar.timed_assignment_or_goal).replace("ParseResults", ""))
        # print(str(self.grammar.timed_assignments_or_goals).replace("ParseResults", ""))
        for pr in self.grammar.timed_assignment_or_goal:
            print(pr["interval"])

        return problem
