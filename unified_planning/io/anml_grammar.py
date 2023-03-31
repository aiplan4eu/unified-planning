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


import unified_planning as up
from typing import List
from pyparsing import Word, alphanums, alphas, nums, ZeroOrMore, OneOrMore
from pyparsing import (
    Optional,
    Suppress,
    Group,
    restOfLine,
    Combine,
    Forward,
    infixNotation,
    opAssoc,
    ParserElement,
    Literal,
    oneOf,
)
from pyparsing import ParseResults

ParserElement.enablePackrat()

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
TK_EXISTS = "exists"
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
TK_FLOAT = oneOf(["float", "rational"])  # NOTE both are possible here
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
TK_COMMENT = "//"
TK_WHEN = "when"


class ANMLGrammar:
    """
    This class defines the grammar used from the :class:`~unified_planning.io.ANMLReader`
    to parse a :class:`~unified_planning.model.Problem` from an ANML file.
    """

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

        # Negative numbers are defined with the unary minus operator
        integer = Word(nums)
        real = Combine(Word(nums) + "." + Word(nums))
        float_const = real | integer
        boolean_const = oneOf([TK_TRUE, TK_FALSE])

        # Expression definitions
        interval = Forward()
        boolean_expression = Forward()
        quantified_expression = Forward()

        expression_list = Optional(Group(boolean_expression)) - ZeroOrMore(
            Suppress(TK_COMMA) - Group(boolean_expression)
        )
        fluent_ref = Group(
            identifier
            - Group(
                Optional(
                    Suppress(TK_L_PARENTHESIS)
                    - expression_list
                    - Suppress(TK_R_PARENTHESIS)
                )
            )
        )

        arithmetic_expression = infixNotation(
            boolean_const | float_const | fluent_ref,
            [
                (oneOf([TK_PLUS, TK_MINUS]), 1, opAssoc.RIGHT),
                (oneOf([TK_TIMES, TK_DIV]), 2, opAssoc.LEFT, group_binary),
                (oneOf([TK_PLUS, TK_MINUS]), 2, opAssoc.LEFT, group_binary),
            ],
        )
        relations_expression = infixNotation(
            arithmetic_expression,
            [
                (
                    oneOf([TK_LT, TK_LE, TK_GT, TK_GE, TK_EQUALS, TK_NOT_EQUALS]),
                    2,
                    opAssoc.LEFT,
                    group_binary,
                ),
            ],
        )
        boolean_expression <<= infixNotation(
            quantified_expression | relations_expression | boolean_const,
            [
                (TK_NOT, 1, opAssoc.RIGHT),
                (oneOf([TK_AND, TK_OR, TK_XOR]), 2, opAssoc.LEFT, group_binary),
                (
                    oneOf([TK_ASSIGN, TK_INCREASE, TK_DECREASE]),
                    2,
                    opAssoc.LEFT,
                    group_binary,
                ),
            ],
        )
        conditional_expression = Forward()
        expression = conditional_expression | boolean_expression

        timed_expression = Group(Optional(interval)).setResultsName("interval") + Group(
            expression
        ).setResultsName("expression")

        conditional_expression <<= (
            TK_WHEN
            - Group(timed_expression).set_results_name("condition")
            - Suppress(TK_L_BRACE)
            - Group(OneOrMore(timed_expression - Suppress(TK_SEMI))).set_results_name(
                "assignments"
            )
            - Suppress(TK_R_BRACE)
        )

        expression_block_body = OneOrMore(Group(expression) - Suppress(TK_SEMI))
        expression_block = Group(
            Group(interval).setResultsName("interval")
            + Suppress(TK_L_BRACE)
            + Group(expression_block_body).setResultsName("body")
            + Suppress(TK_R_BRACE)
        )
        expression_block.setParseAction(parse_exp_block_as_exp_sequence)

        temporal_expression = Optional(arithmetic_expression)

        in_assignment_expression = (
            oneOf((TK_DURATION,))
            - Literal(TK_IN_ASSIGN)
            - Suppress(TK_L_BRACKET)
            - Group(temporal_expression).setResultsName("left_bound")
            - Suppress(TK_COMMA)
            - Group(temporal_expression).setResultsName("right_bound")
            - Suppress(TK_R_BRACKET)
        )
        action_body = ZeroOrMore(
            Group((expression_block | timed_expression | in_assignment_expression))
            - Suppress(TK_SEMI)
        )
        action_body.setParseAction(restore_tagged_exp_block)

        type_decl = (
            Suppress(TK_TYPE)
            - identifier.setResultsName("name")
            - Group(ZeroOrMore(Suppress(TK_LT) - identifier)).setResultsName(
                "supertypes"
            )
        )
        type_decl.setParseAction(self.types.append)
        identifier_list = identifier - ZeroOrMore(Suppress(TK_COMMA) - identifier)
        primitive_type = (
            Literal(TK_BOOLEAN).setResultsName("name")
            | (
                Literal(TK_INTEGER).setResultsName("name")
                - Optional(
                    Group(
                        Suppress(TK_L_BRACKET)
                        - integer.setResultsName("left_bound")
                        - Suppress(TK_COMMA)
                        - integer.setResultsName("right_bound")
                        - Suppress(TK_R_BRACKET)
                    )
                )
            )
            | (
                TK_FLOAT.setResultsName("name")
                - Optional(
                    Group(
                        Suppress(TK_L_BRACKET)
                        - real.setResultsName("left_bound")
                        - Suppress(TK_COMMA)
                        - real.setResultsName("right_bound")
                        - Suppress(TK_R_BRACKET)
                    )
                )
            )
        )
        type_ref = primitive_type | identifier
        instance_decl = (
            Suppress(TK_INSTANCE)
            - type_ref.setResultsName("type")
            - Group(identifier_list).setResultsName("names")
        )
        instance_decl.setParseAction(self.objects.append)

        parameter_list = Optional(Group(Group(type_ref) - identifier)) - ZeroOrMore(
            Suppress(TK_COMMA) - Group(Group(type_ref) - identifier)
        )
        fluent_decl = (
            Suppress(oneOf([TK_FLUENT, TK_CONSTANT]))
            - type_ref.setResultsName("type")
            - identifier.setResultsName("name")
            - Group(
                Optional(
                    Suppress(TK_L_PARENTHESIS)
                    - parameter_list
                    - Suppress(TK_R_PARENTHESIS)
                )
            ).setResultsName("parameters")
            - Optional(Suppress(TK_ASSIGN) - Group(expression)).setResultsName("init")
        )
        fluent_decl.setParseAction(self.fluents.append)
        action_decl = (
            Suppress("action")
            - identifier.setResultsName("name")
            - Suppress(TK_L_PARENTHESIS)
            - Group(parameter_list).setResultsName("parameters")
            - Suppress(TK_R_PARENTHESIS)
            - Suppress(TK_L_BRACE)
            - Group(action_body).setResultsName("body")
            - Suppress(TK_R_BRACE)
        )
        action_decl.setParseAction(self.actions.append)
        interval <<= (
            oneOf([TK_L_BRACKET, TK_L_PARENTHESIS])
            + (
                (
                    Group(temporal_expression)
                    + Optional(Suppress(TK_COMMA) + Group(temporal_expression))
                )
            )
            + oneOf([TK_R_BRACKET, TK_R_PARENTHESIS])
        )
        quantified_expression <<= Group(
            oneOf([TK_FORALL, TK_EXISTS])
            - Suppress(TK_L_PARENTHESIS)
            - Group(parameter_list).setResultsName("quantifier_variables")
            - Suppress(TK_R_PARENTHESIS)
            - Suppress(TK_L_BRACE)
            - Group(OneOrMore(boolean_expression - Suppress(TK_SEMI))).setResultsName(
                "quantifier_body"
            )
            - Suppress(TK_R_BRACE)
        )

        # Standalone expressions are defined to handle differently expressions
        # defined inside an action from the expressions defined outside an action
        standalone_timed_expression = timed_expression.copy()
        standalone_timed_expression.setParseAction(self.timed_assignment_or_goal.append)
        standalone_expression_block = expression_block.copy()
        standalone_expression_block.setParseAction(
            self.timed_assignments_or_goals.append
        )

        goal_body = OneOrMore(
            (standalone_expression_block | standalone_timed_expression)
            - Suppress(TK_SEMI)
        )
        goal_decl = TK_GOAL - (
            standalone_timed_expression
            | standalone_expression_block
            | TK_L_BRACE - goal_body - TK_R_BRACE
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

        anml_body = OneOrMore(Group(anml_stmt - Suppress(TK_SEMI)))
        anml_body.ignore(TK_COMMENT - restOfLine)

        self._problem = anml_body

    @property
    def problem(self):
        return self._problem


# Utility functions
def operatorOperands(tokenlist):
    "generator to extract operators and operands in pairs"
    it = iter(tokenlist)
    while 1:
        try:
            yield (next(it), next(it))
        except StopIteration:
            break


def group_binary(parse_res: ParseResults):
    """
    Helper function that organizes the parsed expression's flat tree, parsed by the
    pyparsing.infixNotation, in a binary tree.

    ES: 3 + 2 - (5 - 4)
    is parsed as: [[[['3', '+', '2'], '-', ['5', '-', '4']]]
    instead of:   [[['3', '+', '2', '-', ['5', '-', '4']]]
    """
    parsed_tokens = parse_res[0]
    assert len(parsed_tokens) % 2 == 1, "expected an odd number of tokens"
    tokens_list = [t for t in parsed_tokens.as_list()]
    first_element = tokens_list[0]
    for operator, operand in operatorOperands(tokens_list[1:]):
        first_element = ParseResults([first_element, operator, operand])
    parse_res[0] = first_element


def parse_exp_block_as_exp_sequence(parse_res: ParseResults):
    """
    This function parses a block in the form:
        [start] {
            exp1;
            exp2;
            exp3
        }
    as:
        {
            [start] exp1;
            [start] exp2;
            [start] exp3;
        }
    and tags it in the first element. Tag is removed by the restore_tagged_exp_block
    utility function.
    """
    exp_block_res = parse_res[0]
    interval = exp_block_res[0]
    exps = exp_block_res[1]
    new_exps_sequence: List[ParseResults] = [
        ParseResults([interval, exp]) for i, exp in enumerate(exps)
    ]
    parse_res[0] = ParseResults(new_exps_sequence)
    parse_res.insert(0, "tag_expression_block")


def restore_tagged_exp_block(parse_res: ParseResults):
    """
    Removes the tag from an expression block and removes the elements inside it,
    readding them as different exp and not as a whole block, for example:
    we have:
        [start] {exp1; exp2; exp3}
        [end] exp4;
    it is parsed like: (thanks to the parse_exp_block_as_exp_sequence method)
        {{tagged block: {[start] exp1; [start] exp2; [start] exp3;}}, [end] exp4;}
    This method returns:
        {[start] exp1;[start] exp2;[start] exp3;[end]exp4;}
    So, in the resulting ParseResults, there is no difference in temporal expressions
    parsed in a block or outside the block.
    """
    to_add: List[ParseResults] = []
    for i, res in enumerate(parse_res):
        if res[0] == "tag_expression_block":
            intervals_and_exps = res[1]
            parse_res.pop(i)
            to_add.extend(intervals_and_exps)
    parse_res.extend(to_add)
