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


import threading
import typing
from typing import Any, Dict, List, NamedTuple, Optional

from lark import Lark, Token, Transformer
from lark.exceptions import UnexpectedEOF, UnexpectedInput

from unified_planning.exceptions import ANMLSyntaxError


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
TKS_FLOAT = ("float", "rational")  # NOTE both are possible here
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


# start, end, all and duration are plain names, the reader interprets them.
# Keywords are separate string terminals, so lark matches them only as whole names.
_GRAMMAR = r"""
start: (_stmt ";")+

_stmt: type_decl | instance_decl | constant_decl | fluent_decl | action_decl
     | top_block | goal_decl | top_timed

type_decl: "type" NAME ("<" NAME)*
instance_decl: "instance" type_ref NAME ("," NAME)*
constant_decl: "constant" type_ref NAME ["(" [params] ")"] [":=" expr]
fluent_decl: "fluent" type_ref NAME ["(" [params] ")"] [":=" expr]
action_decl: "action" NAME "(" [params] ")" [annotations] "{" (_action_item ";")* "}"
goal_decl: "goal" (top_timed | top_block | "{" ((top_block | top_timed) ";")+ "}")
top_block: block
top_timed: timed

_action_item: block | timed | in_assign
in_assign: NAME ":in" "[" [expr] "," [expr] "]"
annotations: "::" "(" annotation ("," annotation)* ")"
?annotation: NUMBER | TRUE | FALSE | STRING

type_ref: BOOLEAN_T -> primitive_type
        | INTEGER_T [int_bounds] -> primitive_type
        | (FLOAT_T | RATIONAL_T) [float_bounds] -> primitive_type
        | NAME -> user_type
int_bounds: int_lower "," int_upper
?int_lower: "[" NUMBER | "(" "-" INFINITY
?int_upper: NUMBER "]" | INFINITY ")"
float_bounds: "[" NUMBER "," NUMBER "]"
params: param ("," param)*
param: type_ref NAME

block: interval "{" (expr ";")+ "}"
timed: [interval] expr
interval: "[" _span "]" -> interval_cc
        | "[" _span ")" -> interval_co
        | "(" _span "]" -> interval_oc
        | "(" pair ")" -> interval_oo
        | ALL_INTERVAL -> interval_all
_span: point | pair
point: expr
pair: [expr] "," [expr]

?expr: when_expr | assign
when_expr: "when" timed "{" (timed ";")+ "}"
?assign: implies | assign ASSIGN_OP implies -> binary
?implies: or_expr | or_expr IMPLIES implies -> binary
?or_expr: not_expr | or_expr (AND | OR | XOR) not_expr -> binary
?not_expr: comparison | NOT not_expr -> unary
?comparison: sum | comparison COMP_OP sum -> binary
?sum: product | sum ADD_OP product -> binary
?product: unary_op | product MUL_OP unary_op -> binary
?unary_op: atom | ADD_OP unary_op -> unary
?atom: NUMBER -> constant
     | TRUE -> constant
     | FALSE -> constant
     | fluent_ref
     | quantified
     | "(" expr ")"
fluent_ref: NAME ["(" [args] ")"]
args: expr ("," expr)*
quantified: (FORALL | EXISTS) "(" [params] ")" "{" (expr ";")+ "}"

// "(e)" cannot be an interval in LALR, and "(all)" is the only such interval the reader accepts.
ALL_INTERVAL.2: /\(\s*all\s*\)/
BOOLEAN_T: "boolean"
INTEGER_T: "integer"
FLOAT_T: "float"
RATIONAL_T: "rational"
INFINITY: "infinity"
TRUE: "true"
FALSE: "false"
AND: "and"
OR: "or"
XOR: "xor"
NOT: "not"
IMPLIES: "implies"
FORALL: "forall"
EXISTS: "exists"
ASSIGN_OP: ":=" | ":+=" | ":-=" | ":increase" | ":decrease"
COMP_OP: "<=" | ">=" | "==" | "!=" | "<" | ">"
ADD_OP: "+" | "-"
MUL_OP: "*" | "/"
NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /[0-9]+(\.[0-9]+)?/
STRING: /"[a-zA-Z_][a-zA-Z0-9_]*"/

%ignore /\s+/
%ignore /\/\/[^\n]*/
"""


class _When(list):
    """A `when` expression; its tokens are spliced into the enclosing group."""


class _Block(NamedTuple):
    interval: List[Any]
    expressions: List[List[Any]]


def _group(expression) -> List[Any]:
    """The tokens of `Group(expression)` in the legacy pyparsing grammar."""
    return list(expression) if isinstance(expression, _When) else [expression]


class ANMLGrammar:
    """
    The declarations and statements of a parsed ANML problem, in source order, as nested lists.
    """

    def __init__(self):
        self.types: List[Dict[str, Any]] = []
        self.constant_fluents: List[Dict[str, Any]] = []
        self.fluents: List[Dict[str, Any]] = []
        self.actions: List[Dict[str, Any]] = []
        self.objects: List[Dict[str, Any]] = []
        self.timed_assignments_or_goals: List[List[Any]] = []
        self.timed_assignment_or_goal: List[List[Any]] = []


class _ToLists(Transformer):
    """Builds the nested lists the ANML reader consumes, mirroring the legacy pyparsing output."""

    def __default_token__(self, token: Token) -> str:
        return str(token)

    def start(self, statements):
        grammar = ANMLGrammar()
        for statement in statements:
            for kind, value in statement:
                getattr(grammar, kind).append(value)
        return grammar

    def type_decl(self, c):
        return [("types", {"name": c[0], "supertypes": c[1:]})]

    def instance_decl(self, c):
        return [("objects", {"type": c[0], "names": c[1:]})]

    def _fluent(self, c) -> Dict[str, Any]:
        res = {"type": c[0], "name": c[1], "parameters": c[2] or []}
        if c[3] is not None:
            res["init"] = _group(c[3])
        return res

    def constant_decl(self, c):
        return [("constant_fluents", self._fluent(c))]

    def fluent_decl(self, c):
        return [("fluents", self._fluent(c))]

    def action_decl(self, c):
        body: List[Any] = []
        blocks: List[Any] = []
        for item in c[3:]:
            if isinstance(item, _Block):
                # The legacy grammar moved the expressions of a block after the other ones.
                blocks.extend([item.interval, e] for e in item.expressions)
            else:
                body.append(item)
        action = {
            "name": c[0],
            "parameters": c[1] or [],
            "annotations": c[2] or [],
            "body": body + blocks,
        }
        return [("actions", action)]

    def goal_decl(self, c):
        return [pair for statement in c for pair in statement]

    def top_block(self, c):
        block = c[0]
        return [("timed_assignments_or_goals", [[block.interval, block.expressions]])]

    def top_timed(self, c):
        return [("timed_assignment_or_goal", c[0])]

    def in_assign(self, c):
        if c[0] != TK_DURATION:
            raise ANMLSyntaxError(f"Expected {TK_DURATION} before {TK_IN_ASSIGN}")
        bounds = [[] if b is None else [b] for b in c[1:]]
        return [TK_DURATION, TK_IN_ASSIGN, *bounds]

    def annotations(self, c):
        return list(c)

    def primitive_type(self, c):
        return [c[0]] if len(c) == 1 or c[1] is None else [c[0], c[1]]

    def user_type(self, c):
        return [c[0]]

    def int_bounds(self, c):
        return list(c)

    float_bounds = int_bounds

    def params(self, c):
        return list(c)

    def param(self, c):
        return [c[0], c[1]]

    def block(self, c):
        return _Block(c[0], [_group(e) for e in c[1:]])

    def timed(self, c):
        return [[] if c[0] is None else c[0], _group(c[1])]

    def interval_cc(self, c):
        return [TK_L_BRACKET, *c[0], TK_R_BRACKET]

    def interval_co(self, c):
        return [TK_L_BRACKET, *c[0], TK_R_PARENTHESIS]

    def interval_oc(self, c):
        return [TK_L_PARENTHESIS, *c[0], TK_R_BRACKET]

    def interval_oo(self, c):
        return [TK_L_PARENTHESIS, *c[0], TK_R_PARENTHESIS]

    def interval_all(self, c):
        return [TK_L_PARENTHESIS, [[TK_ALL, []]], TK_R_PARENTHESIS]

    def point(self, c):
        return [[c[0]]]

    def pair(self, c):
        return [[] if e is None else [e] for e in c]

    def when_expr(self, c):
        assignments = [token for timed in c[1:] for token in timed]
        return _When([TK_WHEN, c[0], assignments])

    def binary(self, c):
        return [c[0], c[1], c[2]]

    def unary(self, c):
        return [c[0], c[1]]

    def constant(self, c):
        return c[0]

    def fluent_ref(self, c):
        return [c[0], [] if c[1] is None else [[a] for a in c[1]]]

    def args(self, c):
        return list(c)

    def quantified(self, c):
        body = [token for e in c[2:] for token in _group(e)]
        return [c[0], c[1] or [], body]


_parser: Optional[Lark] = None
_parser_lock = threading.Lock()


def parse_anml(text: str) -> ANMLGrammar:
    """Parses an ANML problem; the lark tables are built on first use."""
    global _parser
    with _parser_lock:
        if _parser is None:
            _parser = Lark(
                _GRAMMAR,
                parser="lalr",
                transformer=_ToLists(),
                maybe_placeholders=True,
            )
    try:
        return typing.cast(ANMLGrammar, _parser.parse(text))
    except UnexpectedInput as e:
        token = getattr(e, "token", None)
        if isinstance(e, UnexpectedEOF) or (token is not None and token.type == "$END"):
            lines = text.split("\n")
            loc = f"line {len(lines)}, col {len(lines[-1]) + 1}"
            raise ANMLSyntaxError(f"Unexpected end of file at {loc}") from None
        found = token if token is not None else getattr(e, "char", "")
        raise ANMLSyntaxError(
            f"Unexpected {str(found)!r} at line {e.line}, col {e.column}"
        ) from None
