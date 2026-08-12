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


from typing import List

from pyparsing import (
    Combine,
    Forward,
    Group,
    Keyword,
    Literal,
    MatchFirst,
    OneOrMore,
    OpAssoc,
    Optional,
    ParserElement,
    ParseResults,
    Suppress,
    Word,
    ZeroOrMore,
    alphanums,
    alphas,
    infix_notation,
    nums,
    one_of,
    rest_of_line,
)

import unified_planning as up

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
TK_FLOAT = MatchFirst(
    [Keyword("float"), Keyword("rational")]
)  # NOTE both are possible here
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


def keyword(*words: str) -> ParserElement:
    """
    Returns a parser element matching any of the given keywords.

    Keywords are matched only at word boundaries, so an identifier that merely
    starts with a keyword (``goal_X``, ``typewriter``, ``instanceof``, ...) is
    not split into a keyword plus the rest of the name.
    """
    if len(words) == 1:
        return Keyword(words[0])
    return MatchFirst([Keyword(w) for w in words])


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
        boolean_const = keyword(TK_TRUE, TK_FALSE)

        string_const = Combine('"' + identifier + '"')

        annotation_item = float_const | boolean_const | string_const

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
                (keyword(TK_NOT), 1, OpAssoc.RIGHT),
                (keyword(TK_AND, TK_OR, TK_XOR), 2, OpAssoc.LEFT, group_binary),
                (keyword(TK_IMPLIES), 2, OpAssoc.RIGHT, group_binary),
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

        timed_expression = Group(Optional(interval)).set_results_name(
            "interval"
        ) + Group(expression).set_results_name("expression")

        conditional_expression <<= (
            keyword(TK_WHEN)
            - Group(timed_expression).set_results_name("condition")
            - Suppress(TK_L_BRACE)
            - Group(OneOrMore(timed_expression - Suppress(TK_SEMI))).set_results_name(
                "assignments"
            )
            - Suppress(TK_R_BRACE)
        )

        expression_block_body = OneOrMore(Group(expression) - Suppress(TK_SEMI))
        expression_block = Group(
            Group(interval).set_results_name("interval")
            + Suppress(TK_L_BRACE)
            + Group(expression_block_body).set_results_name("body")
            + Suppress(TK_R_BRACE)
        )
        expression_block.set_parse_action(parse_exp_block_as_exp_sequence)

        temporal_expression = Optional(arithmetic_expression)

        in_assignment_expression = (
            keyword(TK_DURATION)
            - Literal(TK_IN_ASSIGN)
            - Suppress(TK_L_BRACKET)
            - Group(temporal_expression).set_results_name("left_bound")
            - Suppress(TK_COMMA)
            - Group(temporal_expression).set_results_name("right_bound")
            - Suppress(TK_R_BRACKET)
        )
        action_body = ZeroOrMore(
            Group((expression_block | timed_expression | in_assignment_expression))
            - Suppress(TK_SEMI)
        )
        action_body.set_parse_action(restore_tagged_exp_block)

        type_decl = (
            Suppress(keyword(TK_TYPE))
            - identifier.set_results_name("name")
            - Group(ZeroOrMore(Suppress(TK_LT) - identifier)).set_results_name(
                "supertypes"
            )
        )
        type_decl.set_parse_action(self.types.append)
        identifier_list = identifier - ZeroOrMore(Suppress(TK_COMMA) - identifier)
        primitive_type = (
            keyword(TK_BOOLEAN).set_results_name("name")
            | (
                keyword(TK_INTEGER).set_results_name("name")
                - Optional(
                    Group(
                        (
                            (
                                Suppress(TK_L_BRACKET)
                                - integer.set_results_name("left_bound")
                            )
                            | (
                                Suppress(TK_L_PARENTHESIS)
                                - Suppress("-")
                                - keyword(TK_INFINITY).set_results_name("left_bound")
                            )
                        )
                        - Suppress(TK_COMMA)
                        - (
                            (
                                integer.set_results_name("right_bound")
                                - Suppress(TK_R_BRACKET)
                            )
                            | (
                                keyword(TK_INFINITY).set_results_name("right_bound")
                                - Suppress(TK_R_PARENTHESIS)
                            )
                        )
                    )
                )
            )
            | (
                TK_FLOAT.set_results_name("name")
                - Optional(
                    Group(
                        Suppress(TK_L_BRACKET)
                        - real.set_results_name("left_bound")
                        - Suppress(TK_COMMA)
                        - real.set_results_name("right_bound")
                        - Suppress(TK_R_BRACKET)
                    )
                )
            )
        )
        type_ref = primitive_type | identifier
        instance_decl = (
            Suppress(keyword(TK_INSTANCE))
            - type_ref.set_results_name("type")
            - Group(identifier_list).set_results_name("names")
        )
        instance_decl.set_parse_action(self.objects.append)

        parameter_list = Optional(Group(Group(type_ref) - identifier)) - ZeroOrMore(
            Suppress(TK_COMMA) - Group(Group(type_ref) - identifier)
        )
        annotations_list = annotation_item - ZeroOrMore(
            Suppress(TK_COMMA) - annotation_item
        )
        constant_decl = (
            Suppress(keyword(TK_CONSTANT))
            - type_ref.set_results_name("type")
            - identifier.set_results_name("name")
            - Group(
                Optional(
                    Suppress(TK_L_PARENTHESIS)
                    - parameter_list
                    - Suppress(TK_R_PARENTHESIS)
                )
            ).set_results_name("parameters")
            - Optional(Suppress(TK_ASSIGN) - Group(expression)).set_results_name("init")
        )
        constant_decl.set_parse_action(self.constant_fluents.append)
        fluent_decl = (
            Suppress(keyword(TK_FLUENT))
            - type_ref.set_results_name("type")
            - identifier.set_results_name("name")
            - Group(
                Optional(
                    Suppress(TK_L_PARENTHESIS)
                    - parameter_list
                    - Suppress(TK_R_PARENTHESIS)
                )
            ).set_results_name("parameters")
            - Optional(Suppress(TK_ASSIGN) - Group(expression)).set_results_name("init")
        )
        fluent_decl.set_parse_action(self.fluents.append)
        action_decl = (
            Suppress(keyword(TK_ACTION))
            - identifier.set_results_name("name")
            - Suppress(TK_L_PARENTHESIS)
            - Group(parameter_list).set_results_name("parameters")
            - Suppress(TK_R_PARENTHESIS)
            - Group(
                Optional(
                    Suppress(TK_ANNOTATION)
                    - Suppress(TK_L_PARENTHESIS)
                    - annotations_list
                    - Suppress(TK_R_PARENTHESIS)
                )
            ).set_results_name("annotations")
            - Suppress(TK_L_BRACE)
            - Group(action_body).set_results_name("body")
            - Suppress(TK_R_BRACE)
        )
        action_decl.set_parse_action(self.actions.append)
        interval <<= (
            one_of([TK_L_BRACKET, TK_L_PARENTHESIS])
            + (
                Group(temporal_expression)
                + Optional(Suppress(TK_COMMA) + Group(temporal_expression))
            )
            + one_of([TK_R_BRACKET, TK_R_PARENTHESIS])
        )
        quantified_expression_def = Group(
            keyword(TK_FORALL, TK_EXISTS)
            - Suppress(TK_L_PARENTHESIS)
            - Group(parameter_list).set_results_name("quantifier_variables")
            - Suppress(TK_R_PARENTHESIS)
            - Suppress(TK_L_BRACE)
            - Group(OneOrMore(expression - Suppress(TK_SEMI))).set_results_name(
                "quantifier_body"
            )
            - Suppress(TK_R_BRACE)
        )
        quantified_expression <<= infix_notation(quantified_expression_def, [])

        # Standalone expressions are defined to handle differently expressions
        # defined inside an action from the expressions defined outside an action
        standalone_timed_expression = timed_expression.copy()
        standalone_timed_expression.set_parse_action(
            self.timed_assignment_or_goal.append
        )
        standalone_expression_block = expression_block.copy()
        standalone_expression_block.set_parse_action(
            self.timed_assignments_or_goals.append
        )

        goal_body = OneOrMore(
            (standalone_expression_block | standalone_timed_expression)
            - Suppress(TK_SEMI)
        )
        goal_decl = keyword(TK_GOAL) - (
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
