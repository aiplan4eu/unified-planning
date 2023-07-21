# Copyright 2021-2023 AIPlan4EU project
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
from unified_planning.io.utils import set_results_name, set_parse_action
from typing import List

import pyparsing
from pyparsing import Word, alphanums, alphas, nums, ZeroOrMore, OneOrMore
from pyparsing import Optional, Suppress, Group, Combine, Forward, Literal
from pyparsing import ParseResults, ParserElement

if pyparsing.__version__ < "3.0.0":
    from pyparsing import infixNotation as infix_notation
    from pyparsing import restOfLine as rest_of_line
    from pyparsing import oneOf as one_of
    from pyparsing import opAssoc as OpAssoc

    ParserElement.enablePackrat()
else:
    from pyparsing import infix_notation
    from pyparsing import rest_of_line
    from pyparsing import one_of
    from pyparsing import OpAssoc

    ParserElement.enable_packrat()


# ANMl keywords definition as tokens
TK_COMMA = ","
TK_SEMI = ";"
TK_COLON = ":"
TK_ASSIGN = ":="
TKS_INCREASE = (":+=", ":increase")
TKS_DECREASE = (":-=", ":decrease")
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
TK_COMMENT = "//"
TK_WHEN = "when"
TK_INFINITY = "infinity"


class ANMLGrammar:
    """
    This class defines the grammar used from the :class:`~unified_planning.io.ANMLReader`
    to parse a :class:`~unified_planning.model.Problem` from an ANML file.
    """

    def __init__(self):

        # Data structures to populate while parsing
        self.types: List[ParseResults] = []
        self.constant_fluents: List[ParseResults] = []
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
        boolean_const = one_of([TK_TRUE, TK_FALSE])

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

        arithmetic_expression = infix_notation(
            boolean_const | float_const | fluent_ref,
            [
                (one_of([TK_PLUS, TK_MINUS]), 1, OpAssoc.RIGHT),
                (one_of([TK_TIMES, TK_DIV]), 2, OpAssoc.LEFT, group_binary),
                (one_of([TK_PLUS, TK_MINUS]), 2, OpAssoc.LEFT, group_binary),
            ],
        )
        relations_expression = infix_notation(
            arithmetic_expression,
            [
                (
                    one_of([TK_LT, TK_LE, TK_GT, TK_GE, TK_EQUALS, TK_NOT_EQUALS]),
                    2,
                    OpAssoc.LEFT,
                    group_binary,
                ),
            ],
        )
        boolean_expression <<= infix_notation(
            quantified_expression | relations_expression | boolean_const,
            [
                (TK_NOT, 1, OpAssoc.RIGHT),
                (one_of([TK_AND, TK_OR, TK_XOR]), 2, OpAssoc.LEFT, group_binary),
                (TK_IMPLIES, 2, OpAssoc.RIGHT, group_binary),
                (
                    one_of([TK_ASSIGN, *TKS_INCREASE, *TKS_DECREASE]),
                    2,
                    OpAssoc.LEFT,
                    group_binary,
                ),
            ],
        )
        conditional_expression = Forward()
        expression = conditional_expression | boolean_expression

        timed_expression = set_results_name(
            Group(Optional(interval)), "interval"
        ) + set_results_name(Group(expression), "expression")

        conditional_expression <<= (
            TK_WHEN
            - set_results_name(Group(timed_expression), "condition")
            - Suppress(TK_L_BRACE)
            - set_results_name(
                Group(OneOrMore(timed_expression - Suppress(TK_SEMI))), "assignments"
            )
            - Suppress(TK_R_BRACE)
        )

        expression_block_body = OneOrMore(Group(expression) - Suppress(TK_SEMI))
        expression_block = Group(
            set_results_name(Group(interval), "interval")
            + Suppress(TK_L_BRACE)
            + set_results_name(Group(expression_block_body), "body")
            + Suppress(TK_R_BRACE)
        )
        set_parse_action(expression_block, parse_exp_block_as_exp_sequence)

        temporal_expression = Optional(arithmetic_expression)

        in_assignment_expression = (
            one_of((TK_DURATION,))
            - Literal(TK_IN_ASSIGN)
            - Suppress(TK_L_BRACKET)
            - set_results_name(Group(temporal_expression), "left_bound")
            - Suppress(TK_COMMA)
            - set_results_name(Group(temporal_expression), "right_bound")
            - Suppress(TK_R_BRACKET)
        )
        action_body = ZeroOrMore(
            Group((expression_block | timed_expression | in_assignment_expression))
            - Suppress(TK_SEMI)
        )
        set_parse_action(action_body, restore_tagged_exp_block)

        type_decl = (
            Suppress(TK_TYPE)
            - set_results_name(identifier, "name")
            - set_results_name(
                Group(ZeroOrMore(Suppress(TK_LT) - identifier)), "supertypes"
            )
        )
        set_parse_action(type_decl, self.types.append)
        identifier_list = identifier - ZeroOrMore(Suppress(TK_COMMA) - identifier)
        primitive_type = (
            set_results_name(Literal(TK_BOOLEAN), "name")
            | (
                set_results_name(Literal(TK_INTEGER), "name")
                - Optional(
                    Group(
                        (
                            (
                                Suppress(TK_L_BRACKET)
                                - set_results_name(integer, "left_bound")
                            )
                            | (
                                Suppress(TK_L_PARENTHESIS)
                                - Suppress("-")
                                - set_results_name(Literal(TK_INFINITY), "left_bound")
                            )
                        )
                        - Suppress(TK_COMMA)
                        - (
                            (
                                set_results_name(integer, "right_bound")
                                - Suppress(TK_R_BRACKET)
                            )
                            | (
                                set_results_name(Literal(TK_INFINITY), "right_bound")
                                - Suppress(TK_R_PARENTHESIS)
                            )
                        )
                    )
                )
            )
            | (
                set_results_name(TK_FLOAT, "name")
                - Optional(
                    Group(
                        Suppress(TK_L_BRACKET)
                        - set_results_name(real, "left_bound")
                        - Suppress(TK_COMMA)
                        - set_results_name(real, "right_bound")
                        - Suppress(TK_R_BRACKET)
                    )
                )
            )
        )
        type_ref = primitive_type | identifier
        instance_decl = (
            Suppress(TK_INSTANCE)
            - set_results_name(type_ref, "type")
            - set_results_name(Group(identifier_list), "names")
        )
        set_parse_action(instance_decl, self.objects.append)

        parameter_list = Optional(Group(Group(type_ref) - identifier)) - ZeroOrMore(
            Suppress(TK_COMMA) - Group(Group(type_ref) - identifier)
        )
        constant_decl = (
            Suppress(TK_CONSTANT)
            - set_results_name(type_ref, "type")
            - set_results_name(identifier, "name")
            - set_results_name(
                Group(
                    Optional(
                        Suppress(TK_L_PARENTHESIS)
                        - parameter_list
                        - Suppress(TK_R_PARENTHESIS)
                    )
                ),
                "parameters",
            )
            - set_results_name(
                Optional(Suppress(TK_ASSIGN) - Group(expression)), "init"
            )
        )
        set_parse_action(constant_decl, self.constant_fluents.append)
        fluent_decl = (
            Suppress(TK_FLUENT)
            - set_results_name(type_ref, "type")
            - set_results_name(identifier, "name")
            - set_results_name(
                Group(
                    Optional(
                        Suppress(TK_L_PARENTHESIS)
                        - parameter_list
                        - Suppress(TK_R_PARENTHESIS)
                    )
                ),
                "parameters",
            )
            - set_results_name(
                Optional(Suppress(TK_ASSIGN) - Group(expression)), "init"
            )
        )
        set_parse_action(fluent_decl, self.fluents.append)
        action_decl = (
            Suppress("action")
            - set_results_name(identifier, "name")
            - Suppress(TK_L_PARENTHESIS)
            - set_results_name(Group(parameter_list), "parameters")
            - Suppress(TK_R_PARENTHESIS)
            - Suppress(TK_L_BRACE)
            - set_results_name(Group(action_body), "body")
            - Suppress(TK_R_BRACE)
        )
        set_parse_action(action_decl, self.actions.append)
        interval <<= (
            one_of([TK_L_BRACKET, TK_L_PARENTHESIS])
            + (
                (
                    Group(temporal_expression)
                    + Optional(Suppress(TK_COMMA) + Group(temporal_expression))
                )
            )
            + one_of([TK_R_BRACKET, TK_R_PARENTHESIS])
        )
        quantified_expression_def = Group(
            one_of([TK_FORALL, TK_EXISTS])
            - Suppress(TK_L_PARENTHESIS)
            - set_results_name(Group(parameter_list), "quantifier_variables")
            - Suppress(TK_R_PARENTHESIS)
            - Suppress(TK_L_BRACE)
            - set_results_name(
                Group(OneOrMore(expression - Suppress(TK_SEMI))),
                "quantifier_body",
            )
            - Suppress(TK_R_BRACE)
        )
        quantified_expression <<= infix_notation(quantified_expression_def, [])

        # Standalone expressions are defined to handle differently expressions
        # defined inside an action from the expressions defined outside an action
        standalone_timed_expression = timed_expression.copy()
        set_parse_action(
            standalone_timed_expression, self.timed_assignment_or_goal.append
        )
        standalone_expression_block = expression_block.copy()
        set_parse_action(
            standalone_expression_block, self.timed_assignments_or_goals.append
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
            | constant_decl
            | fluent_decl
            | action_decl
            | standalone_expression_block
            | goal_decl
            | standalone_timed_expression
        )

        anml_body = OneOrMore(Group(anml_stmt - Suppress(TK_SEMI)))
        anml_body.ignore(TK_COMMENT - rest_of_line)

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
    pyparsing.infix_notation, in a binary tree.

    ES: 3 + 2 - (5 - 4)
    is parsed as: [[[['3', '+', '2'], '-', ['5', '-', '4']]]
    instead of:   [[['3', '+', '2', '-', ['5', '-', '4']]]
    """
    parsed_tokens = parse_res[0]
    assert len(parsed_tokens) % 2 == 1, "expected an odd number of tokens"
    if pyparsing.__version__ < "3.0.0":
        tokens_list = [t for t in parsed_tokens.asList()]
    else:
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
