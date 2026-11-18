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


from collections import OrderedDict
from fractions import Fraction
import re
from typing import Dict, Union, Callable, List, cast, Tuple
import typing
import unified_planning as up
import unified_planning.model.htn as htn
from unified_planning.model.contingent import ContingentProblem
from unified_planning.environment import Environment, get_environment
from unified_planning.exceptions import (
    PDDLSyntaxError,
    UPException,
    UPUnsupportedProblemTypeError,
)


def lineno(loc: int, s: str) -> int:
    return s.count("\n", 0, loc) + 1


def col(loc: int, s: str) -> int:
    return loc - s.rfind("\n", 0, loc)


class CustomParseResults:
    """A PDDL s-expression node: an atom (`value` is a str) or a list of nodes, with its source span."""

    __slots__ = ("value", "locn_start", "locn_end")

    def __init__(self, value, locn_start: int, locn_end: int):
        self.value = value
        self.locn_start = locn_start
        self.locn_end = locn_end

    def __iter__(self):
        return iter(self.value)

    def __getitem__(self, i):
        return self.value[i]

    def __len__(self):
        return len(self.value)

    def __contains__(self, string: str):
        if isinstance(self.value, str):
            return self.value == string
        return any(string in e for e in self.value)

    def __str__(self):
        if isinstance(self.value, str):
            return self.value
        return f"[{', '.join(map(str, self.value))}]"

    def line_start(self, complete_str: str) -> int:
        return lineno(self.locn_start, complete_str)

    def col_start(self, complete_str: str) -> int:
        return col(self.locn_start, complete_str)

    def line_end(self, complete_str: str) -> int:
        return lineno(self.locn_end, complete_str)

    def col_end(self, complete_str: str) -> int:
        return col(self.locn_end, complete_str)


Object = "object"
TypesMap = Dict[str, up.model.Type]

# Skips whitespace and ";" comments, then captures a parenthesis or an atom.
_TOKEN = re.compile(r"(?:\s+|;[^\n]*)*([()]|[^\s();]+)")

# Names as the legacy grammar accepted them; the input is already lower case.
_NAME = re.compile(r"[a-z][a-z0-9_-]*\Z")

_REQUIREMENTS = frozenset(
    ":strips :typing :negative-preconditions :disjunctive-preconditions :equality"
    " :existential-preconditions :universal-preconditions :quantified-preconditions"
    " :conditional-effects :fluents :numeric-fluents :object-fluents :adl"
    " :durative-actions :duration-inequalities :timed-initial-literals"
    " :timed-initial-effects :action-costs :hierarchy :method-preconditions"
    " :constraints :contingent :preferences :time :continuous-effects".split()
)

# Accepted keywords of each section, mapped to the key they are stored under.
_ACTION_FIELDS = {
    ":parameters": "params",
    ":precondition": "pre",
    ":effect": "eff",
    ":observe": "obs",
}
_PROCESS_FIELDS = {":parameters": "params", ":precondition": "pre", ":effect": "eff"}
_DURATIVE_FIELDS = {
    ":parameters": "params",
    ":duration": "duration",
    ":condition": "cond",
    ":effect": "eff",
}
_TASK_FIELDS = {":parameters": "params"}
_METHOD_FIELDS = {
    ":parameters": "params",
    ":task": "task",
    ":precondition": "precondition",
    ":ordered-subtasks": "ordered-subtasks",
    ":ordered-tasks": "ordered-subtasks",
    ":subtasks": "subtasks",
    ":tasks": "subtasks",
    ":ordering": "ordering",
    ":constraints": "constraints",
}
_HTN_FIELDS = {
    ":parameters": "params",
    ":ordered-tasks": "ordered-tasks",
    ":ordered-subtasks": "ordered-tasks",
    ":tasks": "tasks",
    ":subtasks": "tasks",
    ":ordering": "ordering",
    ":constraints": "constraints",
}


def _error(msg: str, loc: int, s: str) -> PDDLSyntaxError:
    return PDDLSyntaxError(f"{msg} at line {lineno(loc, s)}, col {col(loc, s)}")


def _atom(node: CustomParseResults, s: str, what: str) -> str:
    if not isinstance(node.value, str):
        raise _error(f"Expected {what}, found {node}", node.locn_start, s)
    return node.value


def _typed_list(
    nodes: List[CustomParseResults], s: str, variables: bool
) -> List[CustomParseResults]:
    """Parses `a b - t c` into nodes whose value is `[names]` or `[names, type]`."""
    groups = []
    names: List[str] = []
    first_start = last_end = 0
    i = 0
    while i < len(nodes):
        tok = _atom(nodes[i], s, "a name")
        if tok[0] == "-":
            # Names start with a letter, so "-t" is the type annotation "- t".
            if tok == "-" and i + 1 < len(nodes):
                type_node = nodes[i + 1]
                t = _atom(type_node, s, "a type name")
                i += 2
            else:
                type_node, t = nodes[i], tok[1:]
                i += 1
            if not names or not t:
                raise _error("Misplaced '-' in typed list", nodes[i - 1].locn_start, s)
            groups.append(
                CustomParseResults([names, t], first_start, type_node.locn_end)
            )
            names = []
            continue
        if variables:
            if tok[0] != "?" or len(tok) == 1:
                raise _error(
                    f"Expected a variable, found {tok}", nodes[i].locn_start, s
                )
            tok = tok[1:]
        if not names:
            first_start = nodes[i].locn_start
        names.append(tok)
        last_end = nodes[i].locn_end
        i += 1
    if names:
        groups.append(CustomParseResults([names], first_start, last_end))
    return groups


_DOMAIN_STRUCTURES = {
    ":action": ("actions", _ACTION_FIELDS, (":parameters",)),
    ":durative-action": (
        "actions",
        _DURATIVE_FIELDS,
        (":parameters", ":duration", ":effect"),
    ),
    ":process": ("processes", _PROCESS_FIELDS, (":parameters",)),
    ":event": ("events", _PROCESS_FIELDS, (":parameters",)),
    ":task": ("tasks", _TASK_FIELDS, (":parameters",)),
    ":method": ("methods", _METHOD_FIELDS, (":parameters", ":task")),
}


class _Parser:
    """Recursive descent over the PDDL tokens, so that errors point where the structure breaks."""

    def __init__(self, s: str):
        self.s = s
        self.toks = [(m.group(1), m.start(1)) for m in _TOKEN.finditer(s)]
        self.i = 0

    def peek(self, ahead: int = 0) -> typing.Optional[str]:
        i = self.i + ahead
        return self.toks[i][0] if i < len(self.toks) else None

    def loc(self) -> int:
        return self.toks[self.i][1] if self.i < len(self.toks) else len(self.s)

    def error(self, msg: str) -> PDDLSyntaxError:
        tok = self.peek()
        found = "end of file" if tok is None else repr(tok)
        return _error(f"{msg}, found {found}", self.loc(), self.s)

    def expect(self, tok: str):
        if self.peek() != tok:
            raise self.error(f"Expected '{tok}'")
        self.i += 1

    def atom(self, what: str) -> CustomParseResults:
        tok = self.peek()
        if tok is None or tok == "(" or tok == ")":
            raise self.error(f"Expected {what}")
        start = self.toks[self.i][1]
        self.i += 1
        return CustomParseResults(tok, start, start + len(tok))

    def nested(self) -> CustomParseResults:
        """Parses a balanced parenthesized expression into a tree of nodes."""
        if self.peek() != "(":
            raise self.error("Expected '('")
        toks, i = self.toks, self.i
        stack: List[Tuple[int, List[CustomParseResults]]] = []
        children: List[CustomParseResults] = []
        while i < len(toks):
            tok, start = toks[i]
            i += 1
            if tok == "(":
                stack.append((start, children))
                children = []
            elif tok == ")":
                list_start, parent = stack.pop()
                node = CustomParseResults(children, list_start, start + 1)
                parent.append(node)
                children = parent
                if not stack:
                    self.i = i
                    return node
            else:
                children.append(CustomParseResults(tok, start, start + len(tok)))
        self.i = i
        raise self.error("Expected ')'")

    def nested_list(self) -> List[CustomParseResults]:
        """Parses `(...) (...) ...)` and consumes the closing ')'."""
        res = []
        while self.peek() == "(":
            res.append(self.nested())
        self.expect(")")
        return res

    def typed_list(self, variables: bool) -> List[CustomParseResults]:
        """Parses `a b - t c` up to the closing ')', which is not consumed."""
        what = "a variable" if variables else "a name"
        nodes = []
        while self.peek() != ")":
            tok = self.peek() or ""
            bare = tok[1:] if tok[:1] in ("?", "-") else tok
            if tok != "-" and not _NAME.match(bare):
                raise self.error(f"Expected {what}")
            nodes.append(self.atom(what))
        return _typed_list(nodes, self.s, variables)

    def at_predicate(self) -> bool:
        return self.peek() == "(" and _NAME.match(self.peek(1) or "") is not None

    def predicate(self) -> List[typing.Any]:
        start = self.loc()
        try:
            self.expect("(")
            res = [self.atom("a predicate name").value, self.typed_list(True)]
            self.expect(")")
        except PDDLSyntaxError as e:
            # Blame the declaration, as the legacy grammar did, and keep the detail.
            loc = f"line {lineno(start, self.s)}, col {col(start, self.s)}"
            raise PDDLSyntaxError(f"Invalid declaration at {loc}: {e}") from None
        return res

    def requirements(self) -> List[str]:
        res = []
        while self.peek() != ")":
            if self.peek() not in _REQUIREMENTS:
                raise self.error("Expected a requirement")
            res.append(self.atom("a requirement").value)
        self.i += 1
        return res

    def fields(
        self,
        fields: Dict[str, str],
        required: Tuple[str, ...],
        kind: str,
        start: int,
        has_name: bool = True,
    ) -> Dict[str, typing.Any]:
        """Parses `name :keyword (...) ...)` into a dict keyed by `fields`."""
        res: Dict[str, typing.Any] = {}
        if has_name:
            if not _NAME.match(self.peek() or ""):
                raise self.error("Expected a name")
            res["name"] = self.atom("a name").value
        while self.peek() != ")":
            field = fields.get(typing.cast(str, self.peek()))
            if field is None:
                raise self.error(f"Unexpected token in ({kind}")
            if field in res:
                raise self.error(f"Duplicate {self.peek()} in ({kind}")
            self.i += 1
            if field == "params":
                self.expect("(")
                res[field] = self.typed_list(True)
                self.expect(")")
            else:
                res[field] = self.nested()
        for keyword in required:
            if fields[keyword] not in res:
                raise self.error(f"Missing {keyword} in ({kind}")
        self.i += 1
        return res

    def header(self, kind: str) -> str:
        """Parses `(define (kind name)` and returns the name."""
        self.expect("(")
        self.expect("define")
        self.expect("(")
        self.expect(kind)
        name = self.atom(f"the {kind} name").value
        self.expect(")")
        return name

    def sections(self) -> typing.Iterator[Tuple[str, int]]:
        """Yields the keyword and start of each section; the caller parses its body."""
        while self.peek() != ")":
            start = self.loc()
            self.expect("(")
            yield self.atom("a section keyword").value, start
        self.i += 1
        if self.i != len(self.toks):
            raise self.error("Expected end of file")


def _parse_domain(s: str) -> Dict[str, typing.Any]:
    p = _Parser(s)
    res: Dict[str, typing.Any] = {"name": p.header("domain")}
    for key in ("tasks", "methods", "actions", "processes", "events"):
        res[key] = []
    for kind, start in p.sections():
        if kind == ":requirements":
            res["features"] = p.requirements()
        elif kind in (":types", ":constants"):
            res[kind[1:]] = p.typed_list(False)
            p.expect(")")
        elif kind == ":predicates":
            res["predicates"] = []
            while p.at_predicate():
                res["predicates"].append(p.predicate())
            p.expect(")")
        elif kind == ":functions":
            res["functions"] = []
            while p.at_predicate():
                function: List[typing.Any] = [p.predicate()]
                tok = p.peek()
                if tok is not None and tok[0] == "-":
                    # Names start with a letter, so "-t" is the type annotation "- t".
                    p.i += 1
                    function.append(
                        p.atom("a type name").value if tok == "-" else tok[1:]
                    )
                res["functions"].append(function)
            p.expect(")")
        elif kind in _DOMAIN_STRUCTURES:
            key, fields, required = _DOMAIN_STRUCTURES[kind]
            res[key].append(p.fields(fields, required, kind, start))
        else:
            raise _error(f"Unknown domain section ({kind}", start, s)
    return res


def _parse_problem_sexpr(s: str) -> Dict[str, typing.Any]:
    p = _Parser(s)
    res: Dict[str, typing.Any] = {"name": p.header("problem")}
    for kind, start in p.sections():
        if kind == ":domain":
            p.atom("the domain name")
            p.expect(")")
        elif kind == ":requirements":
            p.requirements()
        elif kind == ":objects":
            res["objects"] = p.typed_list(False)
            p.expect(")")
        elif kind == ":htn":
            res["htn"] = p.fields(_HTN_FIELDS, (), kind, start, has_name=False)
        elif kind == ":init":
            res["init"] = p.nested_list()
        elif kind == ":goal":
            res["goal"] = p.nested()
            p.expect(")")
        elif kind == ":constraints":
            res["constraints"] = p.nested_list()
        elif kind == ":metric":
            if p.peek() not in ("minimize", "maximize"):
                raise p.error("Expected 'minimize' or 'maximize'")
            res["optimization"] = p.atom("an optimization").value
            if p.peek() == "(":
                res["metric"] = p.nested()
            else:  # a bare name, as in (total-time)
                a = p.atom("a metric")
                res["metric"] = CustomParseResults([a], a.locn_start, a.locn_end)
            p.expect(")")
        else:
            raise _error(f"Unknown problem section ({kind}", start, s)
    return res


class UPPDDLReader:
    """
    Parse a `PDDL` domain file and, optionally, a `PDDL` problem file and generate the equivalent :class:`~unified_planning.model.Problem`.

    Note: in the error report messages, a tabulation counts as one column; and due to PDDL case-insensitivity, everything in the
    PDDL files will be turned to lower case, so the names of fluents, actions etc. and the error report
    will all be in lower-case.
    """

    def __init__(self, environment: typing.Optional[Environment] = None):
        self._env = get_environment(environment)
        self._em = self._env.expression_manager
        self._tm = self._env.type_manager
        self._operators: Dict[str, Callable] = {
            "and": self._em.And,
            "or": self._em.Or,
            "not": self._em.Not,
            "imply": self._em.Implies,
            ">=": self._em.GE,
            "<=": self._em.LE,
            ">": self._em.GT,
            "<": self._em.LT,
            "=": self._em.Equals,
            "+": self._em.Plus,
            "-": self._em.Minus,
            "/": self._em.Div,
            "*": self._em.Times,
        }
        self._trajectory_constraints: Dict[str, Callable] = {
            "always": self._em.Always,
            "sometime": self._em.Sometime,
            "sometime-before": self._em.SometimeBefore,
            "sometime-after": self._em.SometimeAfter,
            "at-most-once": self._em.AtMostOnce,
        }
        self._fve = self._env.free_vars_extractor
        self._totalcost: typing.Optional[up.model.FNode] = None

    def _parse_exp(
        self,
        problem: up.model.Problem,
        act: typing.Optional[Union[up.model.Transition, htn.Method, htn.TaskNetwork]],
        types_map: TypesMap,
        var: Dict[str, up.model.Variable],
        exp: CustomParseResults,
        complete_str: str,
    ) -> up.model.FNode:
        stack = [(var, exp, False)]
        solved: List[up.model.FNode] = []
        while len(stack) > 0:
            var, exp, status = stack.pop()
            if status:
                if exp[0].value == "-" and len(exp) == 2:  # unary minus
                    solved.append(self._em.Times(-1, solved.pop()))
                elif exp[0].value in self._operators:  # n-ary operators
                    op: Callable = self._operators[exp[0].value]
                    solved.append(op(*[solved.pop() for _ in range(1, len(exp))]))
                elif exp[0].value in ["exists", "forall"]:  # quantifier operators
                    q_op: Callable = (
                        self._em.Exists if exp[0].value == "exists" else self._em.Forall
                    )
                    solved.append(q_op(solved.pop(), *var.values()))
                elif (
                    exp[0].value in self._trajectory_constraints
                ):  # trajectory_constraints reference
                    t_op: Callable = self._trajectory_constraints[exp[0].value]
                    solved.append(t_op(*[solved.pop() for _ in range(1, len(exp))]))
                elif problem.has_fluent(exp[0].value):  # fluent reference
                    f = problem.fluent(exp[0].value)
                    args = [solved.pop() for _ in range(1, len(exp))]
                    try:
                        solved.append(self._em.FluentExp(f, tuple(args)))
                    except Exception as e:
                        start_line, start_col = (
                            exp.line_start(complete_str),
                            exp.col_start(complete_str),
                        )
                        end_line, end_col = (
                            exp.line_end(complete_str),
                            exp.col_end(complete_str),
                        )
                        raise PDDLSyntaxError(
                            repr(e)
                            + f"\nError from line: {start_line}, col {start_col} to line: {end_line}, col {end_col}"
                        )
                else:
                    start_line, start_col = (
                        exp.line_start(complete_str),
                        exp.col_start(complete_str),
                    )
                    end_line, end_col = (
                        exp.line_end(complete_str),
                        exp.col_end(complete_str),
                    )
                    raise up.exceptions.UPUnreachableCodeError(
                        f"Invalid expression from line: {start_line}, col {start_col} to line: {end_line}, col {end_col}"
                    )
            else:
                if isinstance(exp.value, list):
                    if len(exp) == 0:  # empty precodition
                        solved.append(self._em.TRUE())
                    elif exp[0].value == "-" and len(exp) == 2:  # unary minus
                        stack.append((var, exp, True))
                        stack.append((var, exp[1], False))
                    elif exp[0].value in self._operators:  # n-ary operators
                        stack.append((var, exp, True))
                        for i in range(1, len(exp)):
                            stack.append((var, exp[i], False))
                    elif exp[0].value in ["exists", "forall"]:  # quantifier operators
                        vars_res = _typed_list(exp[1].value, complete_str, True)
                        new_vars = {}
                        for g in vars_res:
                            try:
                                t = types_map[
                                    g.value[1] if len(g.value) > 1 else Object
                                ]
                            except KeyError:
                                g_start_line, g_start_col = (
                                    lineno(g.locn_start, complete_str),
                                    col(g.locn_start, complete_str),
                                )
                                g_end_line, g_end_col = (
                                    lineno(g.locn_end, complete_str),
                                    col(g.locn_end, complete_str),
                                )
                                raise PDDLSyntaxError(
                                    f"Undefined variable's type: {g[1]}."
                                    + f"\nError from line: {g_start_line}, col: {g_start_col} to line: {g_end_line}, col: {g_end_col}."
                                )
                            for o in g.value[0]:
                                new_vars[o] = up.model.Variable(o, t, self._env)
                        # new_vars are the variables defined by the quantifier currently being solved
                        # all_vars are the variables defined by all the quantifiers around this expression
                        stack.append((new_vars, exp, True))
                        all_vars = var.copy()
                        all_vars.update(new_vars)
                        stack.append((all_vars, exp[2], False))
                    elif (
                        exp[0].value in self._trajectory_constraints
                    ):  # trajectory_constraints reference
                        stack.append((var, exp, True))
                        for i in range(1, len(exp)):
                            stack.append((var, exp[i], False))
                    elif problem.has_fluent(exp[0].value):  # fluent reference
                        stack.append((var, exp, True))
                        for i in range(1, len(exp)):
                            stack.append((var, exp[i], False))
                    elif len(exp) == 1:  # expand an element inside brackets
                        stack.append((var, exp[0], False))
                    else:
                        start_line, start_col = (
                            exp.line_start(complete_str),
                            exp.col_start(complete_str),
                        )
                        end_line, end_col = (
                            exp.line_end(complete_str),
                            exp.col_end(complete_str),
                        )
                        raise PDDLSyntaxError(
                            f"Not able to handle: {complete_str[exp.locn_start : exp.locn_end]} found at line: {start_line}, col {start_col} to line: {end_line}, col {end_col}"
                        )
                elif isinstance(exp.value, str):
                    if (
                        exp.value[0] == "?" and exp.value[1:] in var
                    ):  # variable in a quantifier expression
                        solved.append(self._em.VariableExp(var[exp.value[1:]]))
                    elif exp.value[0] == "?":  # action parameter
                        assert act is not None
                        try:
                            solved.append(
                                self._em.ParameterExp(act.parameter(exp.value[1:]))
                            )
                        except ValueError:
                            start_line, start_col = (
                                exp.line_start(complete_str),
                                exp.col_start(complete_str),
                            )
                            end_line, end_col = (
                                exp.line_end(complete_str),
                                exp.col_end(complete_str),
                            )
                            raise PDDLSyntaxError(
                                f"Undefined name found: {exp.value[1:]}.\nError in expression from"
                                + f" line: {start_line}, col {start_col} to line: {end_line}, col {end_col}"
                            )
                    elif problem.has_fluent(exp.value):  # fluent
                        solved.append(self._em.FluentExp(problem.fluent(exp.value)))
                    elif problem.has_object(exp.value):  # object
                        solved.append(self._em.ObjectExp(problem.object(exp.value)))
                    else:  # number
                        try:
                            n = Fraction(exp.value)
                        except ValueError:
                            start_line, start_col = (
                                exp.line_start(complete_str),
                                exp.col_start(complete_str),
                            )
                            end_line, end_col = (
                                exp.line_end(complete_str),
                                exp.col_end(complete_str),
                            )
                            raise PDDLSyntaxError(
                                f"Found invalid expression: {complete_str[exp.locn_start : exp.locn_end]}. From line: {start_line}, col {start_col} to line: {end_line}, col {end_col}"
                            )
                        if n.denominator == 1:
                            solved.append(self._em.Int(n.numerator))
                        else:
                            solved.append(self._em.Real(n))
                else:
                    start_line, start_col = (
                        exp.line_start(complete_str),
                        exp.col_start(complete_str),
                    )
                    end_line, end_col = (
                        exp.line_end(complete_str),
                        exp.col_end(complete_str),
                    )
                    raise PDDLSyntaxError(
                        f"Not able to handle: {exp}, from line: {start_line}, col {start_col} to line: {end_line}, col {end_col}"
                    )
        assert len(solved) == 1  # sanity check
        return solved.pop()

    def _add_effect(
        self,
        problem: up.model.Problem,
        act: Union[
            up.model.InstantaneousAction,
            up.model.DurativeAction,
            up.model.Process,
            up.model.Event,
        ],
        types_map: TypesMap,
        exp: CustomParseResults,
        complete_str: str,
        cond: Union[up.model.FNode, bool] = True,
        timing: typing.Optional[
            Union[up.model.Timing, up.model.timing.TimeInterval]
        ] = None,
        forall_variables: typing.Optional[Dict[str, up.model.Variable]] = None,
    ):
        if forall_variables is None:
            forall_variables = {}
        to_add = [(exp, cond, forall_variables)]
        while to_add:
            exp, cond, forall_variables = to_add.pop(0)
            assert forall_variables is not None
            if len(exp) == 0:
                continue  # ignore the case where the effect list is empty, e.g., `:effect ()`
            op = exp[0].value
            if op == "and":
                for i in range(1, len(exp)):
                    to_add.append((exp[i], cond, forall_variables))
            elif op == "when":
                cond = self._parse_exp(
                    problem, act, types_map, forall_variables, exp[1], complete_str
                )
                cond = cond.simplify()
                if not cond.is_false():
                    to_add.append((exp[2], cond, forall_variables))
            elif op == "not":
                exp = exp[1]
                eff: Tuple[
                    up.model.FNode, up.model.FNode, Union[up.model.FNode, bool]
                ] = (
                    self._parse_exp(
                        problem, act, types_map, forall_variables, exp, complete_str
                    ),
                    self._em.FALSE(),
                    cond,
                )
                act.add_effect(
                    *eff if timing is None else (timing, *eff),
                    forall=tuple(forall_variables.values()),
                )  # type: ignore
            elif op == "assign":
                eff = (
                    self._parse_exp(
                        problem, act, types_map, forall_variables, exp[1], complete_str
                    ),
                    self._parse_exp(
                        problem, act, types_map, forall_variables, exp[2], complete_str
                    ),
                    cond,
                )
                act.add_effect(
                    *eff if timing is None else (timing, *eff),
                    forall=tuple(forall_variables.values()),
                )  # type: ignore
            elif op == "increase":
                if "#t" in exp:
                    if not (
                        isinstance(act, up.model.Process)
                        or isinstance(act, up.model.DurativeAction)
                    ):
                        raise UPUnsupportedProblemTypeError(
                            "Continuous change is supported only in processes and durative actions"
                        )
                    if (
                        len(exp) == 3
                        and len(exp[2]) == 3
                        and exp[2][0].value == "*"
                        and exp[2][1].value == "#t"
                    ):
                        con_eff = (
                            self._parse_exp(
                                problem,
                                act,
                                types_map,
                                forall_variables,
                                exp[1],
                                complete_str,
                            ),
                            self._parse_exp(
                                problem,
                                act,
                                types_map,
                                forall_variables,
                                exp[2][2],
                                complete_str,
                            ),
                        )
                        if forall_variables:
                            raise UPUnsupportedProblemTypeError(
                                "Continuous change with forall effects is not supported"
                            )
                        if isinstance(act, up.model.Process):
                            act.add_increase_continuous_effect(*con_eff)
                        elif isinstance(act, up.model.DurativeAction):
                            assert isinstance(timing, up.model.timing.TimeInterval)
                            act.add_increase_continuous_effect(timing, *con_eff)
                    elif (
                        len(exp) == 3
                        and len(exp[2]) == 3
                        and exp[2][0].value == "*"
                        and exp[2][2].value == "#t"
                    ):
                        con_eff = (
                            self._parse_exp(
                                problem,
                                act,
                                types_map,
                                forall_variables,
                                exp[1],
                                complete_str,
                            ),
                            self._parse_exp(
                                problem,
                                act,
                                types_map,
                                forall_variables,
                                exp[2][1],
                                complete_str,
                            ),
                        )

                        if forall_variables:
                            raise UPUnsupportedProblemTypeError(
                                "Continuous change with forall effects is not supported"
                            )
                        if isinstance(act, up.model.Process):
                            act.add_increase_continuous_effect(*con_eff)
                        elif isinstance(act, up.model.DurativeAction):
                            assert isinstance(timing, up.model.timing.TimeInterval)
                            act.add_increase_continuous_effect(timing, *con_eff)
                    elif len(exp) == 3 and exp[2].value == "#t":
                        con_eff_without = (
                            self._parse_exp(
                                problem,
                                act,
                                types_map,
                                forall_variables,
                                exp[1],
                                complete_str,
                            ),
                            1,
                        )

                        if isinstance(act, up.model.Process):
                            act.add_increase_continuous_effect(*con_eff_without)
                        elif isinstance(act, up.model.DurativeAction):
                            assert isinstance(timing, up.model.timing.TimeInterval)
                            act.add_increase_continuous_effect(timing, *con_eff_without)
                    else:
                        raise PDDLSyntaxError(
                            "Continuous change syntax is not correct!"
                        )

                else:
                    eff = (
                        self._parse_exp(
                            problem,
                            act,
                            types_map,
                            forall_variables,
                            exp[1],
                            complete_str,
                        ),
                        self._parse_exp(
                            problem,
                            act,
                            types_map,
                            forall_variables,
                            exp[2],
                            complete_str,
                        ),
                        cond,
                    )
                    act.add_increase_effect(
                        *eff if timing is None else (timing, *eff),
                        forall=tuple(forall_variables.values()),
                    )  # type: ignore
            elif op == "decrease":
                if "#t" in exp:
                    if not (
                        isinstance(act, up.model.Process)
                        or isinstance(act, up.model.DurativeAction)
                    ):
                        raise UPUnsupportedProblemTypeError(
                            "Continuous change is supported only in processes and durative actions"
                        )
                    if (
                        len(exp) == 3
                        and len(exp[2]) == 3
                        and exp[2][0].value == "*"
                        and exp[2][1].value == "#t"
                    ):
                        con_eff = (
                            self._parse_exp(
                                problem,
                                act,
                                types_map,
                                forall_variables,
                                exp[1],
                                complete_str,
                            ),
                            self._parse_exp(
                                problem,
                                act,
                                types_map,
                                forall_variables,
                                exp[2][2],
                                complete_str,
                            ),
                        )

                        if forall_variables:
                            raise UPUnsupportedProblemTypeError(
                                "Continuous change with forall effects is not supported"
                            )
                        if isinstance(act, up.model.Process):
                            act.add_decrease_continuous_effect(*con_eff)
                        elif isinstance(act, up.model.DurativeAction):
                            assert isinstance(timing, up.model.timing.TimeInterval)
                            act.add_decrease_continuous_effect(timing, *con_eff)
                    elif (
                        len(exp) == 3
                        and len(exp[2]) == 3
                        and exp[2][0].value == "*"
                        and exp[2][2].value == "#t"
                    ):
                        con_eff = (
                            self._parse_exp(
                                problem,
                                act,
                                types_map,
                                forall_variables,
                                exp[1],
                                complete_str,
                            ),
                            self._parse_exp(
                                problem,
                                act,
                                types_map,
                                forall_variables,
                                exp[2][1],
                                complete_str,
                            ),
                        )

                        if forall_variables:
                            raise UPUnsupportedProblemTypeError(
                                "Continuous change with forall effects is not supported"
                            )
                        if isinstance(act, up.model.Process):
                            act.add_decrease_continuous_effect(*con_eff)
                        elif isinstance(act, up.model.DurativeAction):
                            assert isinstance(timing, up.model.timing.TimeInterval)
                            act.add_decrease_continuous_effect(timing, *con_eff)
                    elif len(exp) == 3 and exp[2].value == "#t":
                        con_eff_without = (
                            self._parse_exp(
                                problem,
                                act,
                                types_map,
                                forall_variables,
                                exp[1],
                                complete_str,
                            ),
                            1,
                        )

                        if forall_variables:
                            raise UPUnsupportedProblemTypeError(
                                "Continuous change with forall effects is not supported"
                            )
                        if isinstance(act, up.model.Process):
                            act.add_increase_continuous_effect(*con_eff_without)
                        elif isinstance(act, up.model.DurativeAction):
                            assert isinstance(timing, up.model.timing.TimeInterval)
                            act.add_increase_continuous_effect(timing, *con_eff_without)
                    else:
                        raise PDDLSyntaxError(
                            "Continuous change syntax is not correct!"
                        )

                else:
                    eff = (
                        self._parse_exp(
                            problem,
                            act,
                            types_map,
                            forall_variables,
                            exp[1],
                            complete_str,
                        ),
                        self._parse_exp(
                            problem,
                            act,
                            types_map,
                            forall_variables,
                            exp[2],
                            complete_str,
                        ),
                        cond,
                    )
                    act.add_decrease_effect(
                        *eff if timing is None else (timing, *eff),
                        forall=tuple(forall_variables.values()),
                    )  # type: ignore
            elif op == "forall":
                assert isinstance(exp, CustomParseResults)
                if forall_variables:
                    raise UPUnsupportedProblemTypeError(
                        "Nested forall on effects are not supported."
                    )
                forall_variables = forall_variables.copy()
                vars_res = _typed_list(exp[1].value, complete_str, True)
                for g in vars_res:
                    t = types_map[g.value[1] if len(g.value) > 1 else Object]
                    for o in g.value[0]:
                        forall_variables[o] = up.model.Variable(o, t, self._env)
                to_add.append((exp[2], cond, forall_variables))
            else:
                eff = (
                    self._parse_exp(
                        problem, act, types_map, forall_variables, exp, complete_str
                    ),
                    self._em.TRUE(),
                    cond,
                )
                act.add_effect(
                    *eff if timing is None else (timing, *eff),
                    forall=tuple(forall_variables.values()),
                )  # type: ignore

    def _add_condition(
        self,
        problem: up.model.Problem,
        act: up.model.DurativeAction,
        exp: CustomParseResults,
        types_map: TypesMap,
        complete_str: str,
        vars: typing.Optional[Dict[str, up.model.Variable]] = None,
    ):
        to_add = [(exp, vars)]
        while to_add:
            exp, vars = to_add.pop(0)
            if len(exp) == 0:
                continue
            op = exp[0].value
            if op == "and":
                for i in range(1, len(exp)):
                    to_add.append((exp[i], vars))
            elif op == "forall":
                vars_res = _typed_list(exp[1].value, complete_str, True)
                if vars is None:
                    vars = {}
                for g in vars_res:
                    try:
                        t = types_map[g.value[1] if len(g.value) > 1 else Object]
                    except KeyError:
                        g_start_line, g_start_col = (
                            lineno(g.locn_start, complete_str),
                            col(g.locn_start, complete_str),
                        )
                        g_end_line, g_end_col = (
                            lineno(g.locn_end, complete_str),
                            col(g.locn_end, complete_str),
                        )
                        raise PDDLSyntaxError(
                            f"Undefined variable's type: {g[1]}."
                            + f"\nError from line: {g_start_line}, col: {g_start_col} to line: {g_end_line}, col: {g_end_col}."
                        )
                    for o in g.value[0]:
                        vars[o] = up.model.Variable(o, t, self._env)
                to_add.append((exp[2], vars))
            elif len(exp) == 3 and op == "at" and exp[1].value == "start":
                cond = self._parse_exp(
                    problem,
                    act,
                    types_map,
                    {} if vars is None else vars,
                    exp[2],
                    complete_str,
                )
                if vars is not None:
                    cond = self._em.Forall(cond, *vars.values())
                act.add_condition(up.model.StartTiming(), cond)
            elif len(exp) == 3 and op == "at" and exp[1].value == "end":
                cond = self._parse_exp(
                    problem,
                    act,
                    types_map,
                    {} if vars is None else vars,
                    exp[2],
                    complete_str,
                )
                if vars is not None:
                    cond = self._em.Forall(cond, *vars.values())
                act.add_condition(up.model.EndTiming(), cond)
            elif len(exp) == 3 and op == "over" and exp[1].value == "all":
                t_all = up.model.OpenTimeInterval(
                    up.model.StartTiming(), up.model.EndTiming()
                )
                cond = self._parse_exp(
                    problem,
                    act,
                    types_map,
                    {} if vars is None else vars,
                    exp[2],
                    complete_str,
                )
                if vars is not None:
                    cond = self._em.Forall(cond, *vars.values())
                act.add_condition(t_all, cond)
            else:
                start_line, start_col = (
                    exp.line_start(complete_str),
                    exp.col_start(complete_str),
                )
                end_line, end_col = (
                    exp.line_end(complete_str),
                    exp.col_end(complete_str),
                )
                raise PDDLSyntaxError(
                    f"Not able to handle: {exp}, from line: {start_line}, col {start_col} to line: {end_line}, col {end_col}"
                )

    def _add_timed_effects(
        self,
        problem: up.model.Problem,
        act: up.model.DurativeAction,
        types_map: TypesMap,
        eff: CustomParseResults,
        complete_str: str,
    ):
        to_add: List[Tuple[CustomParseResults, Dict[str, up.model.Variable]]] = [
            (eff, {})
        ]
        while to_add:
            eff, forall_variables = to_add.pop(0)
            op = eff[0].value
            if op == "and":
                for i in range(1, len(eff)):
                    to_add.append((eff[i], forall_variables))
            elif op == "when":
                if (
                    len(eff) == 3
                    and eff[1][0].value == "at"
                    and eff[1][1].value == "start"
                ):
                    cond = self._parse_exp(
                        problem,
                        act,
                        types_map,
                        forall_variables,
                        eff[1][2],
                        complete_str,
                    )
                    if len(eff[2]) == 3 and not "#t" in eff[2] and "start" in eff[2]:
                        self._add_effect(
                            problem,
                            act,
                            types_map,
                            eff[2][2],
                            complete_str,
                            cond,
                            timing=up.model.StartTiming(),
                            forall_variables=forall_variables,
                        )
                    elif "#t" in eff[2]:
                        self._add_effect(
                            problem,
                            act,
                            types_map,
                            eff[2],
                            complete_str,
                            cond,
                            timing=up.model.timing.ClosedTimeInterval(
                                up.model.timing.StartTiming(),
                                up.model.timing.EndTiming(),
                            ),
                            forall_variables=forall_variables,
                        )
                    else:
                        raise UPUnsupportedProblemTypeError(
                            "Conditional effects with different timing are not supported."
                        )
                elif (
                    len(eff) == 3
                    and eff[1][0].value == "at"
                    and eff[1][1].value == "end"
                ):
                    cond = self._parse_exp(
                        problem,
                        act,
                        types_map,
                        forall_variables,
                        eff[1][2],
                        complete_str,
                    )
                    if len(eff[2]) == 3 and "end" in eff[2]:
                        self._add_effect(
                            problem,
                            act,
                            types_map,
                            eff[2][2],
                            complete_str,
                            cond,
                            timing=up.model.EndTiming(),
                            forall_variables=forall_variables,
                        )
                    else:
                        raise UPUnsupportedProblemTypeError(
                            "Conditional effects with different timing are not supported."
                        )
                else:
                    raise UPUnsupportedProblemTypeError(
                        "Conditional durative effects syntax is not correct."
                    )
            elif len(eff) == 3 and op == "at" and eff[1].value == "start":
                self._add_effect(
                    problem,
                    act,
                    types_map,
                    eff[2],
                    complete_str,
                    timing=up.model.StartTiming(),
                    forall_variables=forall_variables,
                )
            elif len(eff) == 3 and op == "at" and eff[1].value == "end":
                self._add_effect(
                    problem,
                    act,
                    types_map,
                    eff[2],
                    complete_str,
                    timing=up.model.EndTiming(),
                    forall_variables=forall_variables,
                )
            elif "#t" in eff:
                self._add_effect(
                    problem,
                    act,
                    types_map,
                    eff,
                    complete_str,
                    timing=up.model.timing.ClosedTimeInterval(
                        up.model.timing.StartTiming(), up.model.timing.EndTiming()
                    ),
                    forall_variables=forall_variables,
                )
            elif len(eff) == 3 and op == "forall":
                assert isinstance(eff, CustomParseResults)
                if forall_variables:
                    raise UPUnsupportedProblemTypeError(
                        "Nested forall on effects are not supported."
                    )
                forall_variables = forall_variables.copy()
                vars_res = _typed_list(eff[1].value, complete_str, True)
                for g in vars_res:
                    t = types_map[g.value[1] if len(g.value) > 1 else Object]
                    for o in g.value[0]:
                        forall_variables[o] = up.model.Variable(o, t, self._env)
                to_add.append((eff[2], forall_variables))
            else:
                start_line, start_col = (
                    eff.line_start(complete_str),
                    eff.col_start(complete_str),
                )
                end_line, end_col = (
                    eff.line_end(complete_str),
                    eff.col_end(complete_str),
                )
                raise PDDLSyntaxError(
                    f"Not able to handle: {eff.value}, from line: {start_line}, col {start_col} to line: {end_line}, col {end_col}"
                )

    def _get_params(self, a: dict, types_map: TypesMap, domain_str: str):
        a_params = OrderedDict()
        for g in a.get("params", []):
            try:
                t = types_map[g.value[1] if len(g.value) > 1 else Object]
            except KeyError:
                g_start_line, g_start_col = (
                    lineno(g.locn_start, domain_str),
                    col(g.locn_start, domain_str),
                )
                g_end_line, g_end_col = (
                    lineno(g.locn_end, domain_str),
                    col(g.locn_end, domain_str),
                )
                raise PDDLSyntaxError(
                    f"Undefined parameter's type: {g.value[1]}."
                    + f"\nError from line: {g_start_line}, col: {g_start_col} to line: {g_end_line}, col: {g_end_col}."
                )
            for p in g.value[0]:
                a_params[p] = t
        return a_params

    def _parse_subtask(
        self,
        e,
        method: typing.Optional[Union[htn.Method, htn.TaskNetwork]],
        problem: htn.HierarchicalProblem,
        types_map: TypesMap,
        complete_str: str,
    ) -> typing.Optional[htn.Subtask]:
        """Returns the Subtask corresponding to the given expression e or
        None if the expression cannot be interpreted as a subtask."""
        if len(e) == 0:
            return None

        task_name = e[0].value
        if problem.has_task(task_name) or problem.has_action(task_name):
            # check the form '(task_name param1 param2...)'
            task: Union[htn.Task, up.model.Action]
            if problem.has_task(task_name):
                task = problem.get_task(task_name)
            else:
                task = problem.action(task_name)
            assert isinstance(task, htn.Task) or isinstance(task, up.model.Action)
            parameters = [
                self._parse_exp(problem, method, types_map, {}, e[i], complete_str)
                for i in range(1, len(e))
            ]
            return htn.Subtask(task, *parameters, _env=self._env)
        elif len(e) == 2 and e[0].value != "and":
            # check the form "(task_id (task param1 param2...))"
            task_id = e[0].value
            subtask = self._parse_subtask(
                e[1], method, problem, types_map, complete_str
            )
            if subtask is not None:
                # the second element of the list is a valid subtask,
                # return the subtask, with the given identifier
                return htn.Subtask(
                    subtask.task, *subtask.parameters, ident=task_id, _env=self._env
                )
            else:
                return None
        else:
            return None

    def _parse_subtasks(
        self,
        e: CustomParseResults,
        method: typing.Optional[Union[htn.Method, htn.TaskNetwork]],
        problem: htn.HierarchicalProblem,
        types_map: TypesMap,
        complete_str: str,
    ) -> List[htn.Subtask]:
        """Returns the list of subtasks of the expression"""
        single_task = self._parse_subtask(e, method, problem, types_map, complete_str)
        if single_task is not None:
            return [single_task]
        elif len(e) == 0:
            return []
        elif e[0].value == "and":
            return [
                subtask
                for i in range(1, len(e))
                for subtask in self._parse_subtasks(
                    e[i], method, problem, types_map, complete_str
                )
            ]
        else:
            start_line, start_col = (
                e.line_start(complete_str),
                e.col_start(complete_str),
            )
            end_line, end_col = e.line_end(complete_str), e.col_end(complete_str)
            raise PDDLSyntaxError(
                f"Could not parse the subtasks list: {e}, from line: {start_line}, col {start_col} to line: {end_line}, col {end_col}"
            )

    def _check_if_object_type_is_needed(self, domain_res) -> bool:
        for p in domain_res.get("predicates", []):
            for g in p[1]:
                if len(g.value) <= 1 or g.value[1] == Object:
                    return True
        for p in domain_res.get("functions", []):
            pred = p[0]  # predicate part: [name, [params...]]
            for g in pred[1]:
                if len(g.value) <= 1 or g.value[1] == Object:
                    return True
        for g in domain_res.get("constants", []):
            if len(g.value) <= 1 or g.value[1] == Object:
                return True
        for a in domain_res.get("actions", []):
            for g in a.get("params", []):
                if len(g.value) <= 1 or g.value[1] == Object:
                    return True
        for a in domain_res.get("tasks", []):
            for g in a.get("params", []):
                if len(g.value) <= 1 or g.value[1] == Object:
                    return True
        for a in domain_res.get("methods", []):
            for g in a.get("params", []):
                if len(g.value) <= 1 or g.value[1] == Object:
                    return True
        return False

    def _durative_action_has_cost(self, dur_act: up.model.DurativeAction):
        if self._totalcost in self._fve.get(
            dur_act.duration.lower
        ) or self._totalcost in self._fve.get(dur_act.duration.upper):
            return False
        for _, cl in dur_act.conditions.items():
            for c in cl:
                if self._totalcost in self._fve.get(c):
                    return False
        cost_found = False
        for _, el in dur_act.effects.items():
            for e in el:
                if self._totalcost in self._fve.get(e.fluent):
                    if cost_found:
                        return False
                    cost_found = True
                if self._totalcost in self._fve.get(
                    e.value
                ) or self._totalcost in self._fve.get(e.condition):
                    return False
        return True

    def _instantaneous_action_has_cost(self, act: up.model.InstantaneousAction):
        for c in act.preconditions:
            if self._totalcost in self._fve.get(c):
                return False
        for e in act.effects:
            if self._totalcost in self._fve.get(
                e.value
            ) or self._totalcost in self._fve.get(e.condition):
                return False
            if e.fluent == self._totalcost:
                if not e.is_increase() or not e.condition.is_true():
                    return False
        return True

    def _problem_has_actions_cost(self, problem: up.model.Problem):
        if self._totalcost is None:
            return False
        initial_value = problem.initial_value(self._totalcost)
        if initial_value is None:
            return False
        if initial_value.constant_value() != 0:
            return False
        for _, el in problem.timed_effects.items():
            for e in el:
                if (
                    self._totalcost in self._fve.get(e.fluent)
                    or self._totalcost in self._fve.get(e.value)
                    or self._totalcost in self._fve.get(e.condition)
                ):
                    return False
        for c in problem.goals:
            if self._totalcost in self._fve.get(c):
                return False
        return True

    def _parse_problem(
        self,
        domain_res: Dict[str, typing.Any],
        domain_str: str,
        problem_res: typing.Optional[Dict[str, typing.Any]],
        problem_str=typing.Optional[str],
    ) -> "up.model.Problem":
        problem: up.model.Problem
        if ":hierarchy" in set(domain_res.get("features", [])):
            problem = htn.HierarchicalProblem(
                domain_res["name"],
                self._env,
                initial_defaults={self._tm.BoolType(): self._em.FALSE()},
            )
        elif ":contingent" in set(domain_res.get("features", [])):
            problem = ContingentProblem(
                domain_res["name"],
                self._env,
                initial_defaults={self._tm.BoolType(): self._em.FALSE()},
            )
        else:
            problem = up.model.Problem(
                domain_res["name"],
                self._env,
                initial_defaults={self._tm.BoolType(): self._em.FALSE()},
            )

        types_map: TypesMap = {}
        object_type_needed: bool = self._check_if_object_type_is_needed(domain_res)

        # extract all type declarations into a dictionary
        type_declarations: Dict[str, typing.Optional[str]] = {}
        for type_line in domain_res.get("types", []):
            father_name = None if len(type_line) <= 1 else str(type_line[1])
            if father_name is None and object_type_needed:
                father_name = Object
            for declared_type in type_line[0]:
                declared_type = str(declared_type)
                if declared_type in type_declarations:
                    raise PDDLSyntaxError(
                        f"Type {declared_type} is declared more than once"
                    )
                if declared_type == Object:
                    father_name = None
                type_declarations[declared_type] = father_name

        # Processes a type and adds it to the `types_map`.
        # If the father was not previously declared, it will be recursively declared as well.
        def declare_type(
            type: str,
            father_name: typing.Optional[str],
        ):
            if type in types_map:
                # type was already processed which might happen if it already appeared as the parent of another type
                return
            father: typing.Optional["up.model.Type"]
            if father_name is None:
                father = None
            elif father_name in types_map:
                father = types_map[father_name]
            elif father_name in type_declarations:
                if type == father_name:
                    raise PDDLSyntaxError(
                        f"Type '{type}' is defined as a subtype of itself"
                    )
                # father exists but was not processed yet. Force processing immediately
                declare_type(father_name, type_declarations[father_name])
                father = types_map[father_name]
            elif father_name == Object and not object_type_needed:
                father = None
            else:  # not "object" and not explicitly declared
                father = self._env.type_manager.UserType(str(father_name), None)
                types_map[father_name] = father
            # we identified the father, add the type to our map
            types_map[type] = self._env.type_manager.UserType(str(type), father)
            # Force declaration of the type in the `Problem`, even if it is not explicitly used yet
            problem._add_user_type(types_map[type])

        # declare all types
        for declared_type, father_name in type_declarations.items():
            declare_type(declared_type, father_name)

        if object_type_needed and Object not in types_map:
            # The object type is needed, but has not been defined explicitly. We manually define it
            types_map[Object] = self._env.type_manager.UserType("object", None)

        has_actions_cost = False

        for p in domain_res.get("predicates", []):
            n = p[0]
            params = OrderedDict()
            for g in p[1]:
                try:
                    param_type = types_map[g.value[1] if len(g.value) > 1 else Object]
                except KeyError:
                    g_start_line, g_start_col = (
                        lineno(g.locn_start, domain_str),
                        col(g.locn_start, domain_str),
                    )
                    g_end_line, g_end_col = (
                        lineno(g.locn_end, domain_str),
                        col(g.locn_end, domain_str),
                    )
                    raise PDDLSyntaxError(
                        f"Undefined parameter's type: {g.value[1]}."
                        + f"\nError from line: {g_start_line}, col: {g_start_col} to line: {g_end_line}, col: {g_end_col}."
                    )
                for param_name in g.value[0]:
                    params[param_name] = param_type
            f = up.model.Fluent(n, self._tm.BoolType(), params, self._env)
            problem.add_fluent(f)

        for p in domain_res.get("functions", []):
            pred = p[0]  # predicate part: [name, [params...]]
            n = pred[0]
            params = OrderedDict()
            for g in pred[1]:
                g_start_line, g_start_col = (
                    lineno(g.locn_start, domain_str),
                    col(g.locn_start, domain_str),
                )
                g_end_line, g_end_col = (
                    lineno(g.locn_end, domain_str),
                    col(g.locn_end, domain_str),
                )
                try:
                    param_type = types_map[g.value[1] if len(g.value) > 1 else Object]
                except KeyError:
                    raise PDDLSyntaxError(
                        f"Undefined parameter's type: {g.value[1]}."
                        + f"\nError from line: {g_start_line}, col: {g_start_col} to line: {g_end_line}, col: {g_end_col}."
                    )
                for param_name in g.value[0]:
                    if param_name not in params:
                        params[param_name] = param_type
                    else:
                        g_start_line, g_start_col = (
                            lineno(g.locn_start, domain_str),
                            col(g.locn_start, domain_str),
                        )
                        g_end_line, g_end_col = (
                            lineno(g.locn_end, domain_str),
                            col(g.locn_end, domain_str),
                        )
                        raise PDDLSyntaxError(
                            f"In definition of function {n} the parameter {param_name} "
                            + f"is defined twice.\nError from line: {g_start_line}, col: {g_start_col}"
                            + f" to line: {g_end_line}, col: {g_end_col}."
                        )
            # Determine return type: object type if annotated, else RealType
            if len(p) > 1:
                ret_type_name = str(p[1])
                if ret_type_name == "number":
                    fluent_type = self._tm.RealType()
                elif ret_type_name in types_map:
                    fluent_type = types_map[ret_type_name]
                else:
                    raise PDDLSyntaxError(
                        f"Undefined return type '{ret_type_name}' for function '{n}'."
                    )
            else:
                fluent_type = self._tm.RealType()
            f = up.model.Fluent(n, fluent_type, params, self._env)
            if n == "total-cost":
                has_actions_cost = True
                self._totalcost = cast(up.model.FNode, self._em.FluentExp(f))
            problem.add_fluent(f)

        for g in domain_res.get("constants", []):
            try:
                t = types_map[g.value[1] if len(g.value) > 1 else Object]
            except KeyError:
                g_start_line, g_start_col = (
                    lineno(g.locn_start, domain_str),
                    col(g.locn_start, domain_str),
                )
                g_end_line, g_end_col = (
                    lineno(g.locn_end, domain_str),
                    col(g.locn_end, domain_str),
                )
                raise PDDLSyntaxError(
                    f"Undefined variable's type: {g.value[1]}."
                    + f"\nError from line: {g_start_line}, col: {g_start_col} to line: {g_end_line}, col: {g_end_col}."
                )
            for o in g.value[0]:
                problem.add_object(up.model.Object(o, t, problem.environment))

        for task in domain_res.get("tasks", []):
            assert isinstance(problem, htn.HierarchicalProblem)
            name = task["name"]
            task_params = OrderedDict()
            for g in task.get("params", []):
                try:
                    t = types_map[g.value[1] if len(g.value) > 1 else Object]
                except KeyError:
                    g_start_line, g_start_col = (
                        lineno(g.locn_start, domain_str),
                        col(g.locn_start, domain_str),
                    )
                    g_end_line, g_end_col = (
                        lineno(g.locn_end, domain_str),
                        col(g.locn_end, domain_str),
                    )
                    raise PDDLSyntaxError(
                        f"Undefined parameter's type: {g.value[1]}."
                        + f"\nError from line: {g_start_line}, col: {g_start_col} to line: {g_end_line}, col: {g_end_col}."
                    )
                for p in g.value[0]:
                    task_params[p] = t
            task = htn.Task(name, task_params, self._env)
            problem.add_task(task)
        for a in domain_res.get("processes", []):
            n = a["name"]
            a_params = self._get_params(a, types_map, domain_str)
            proc = up.model.Process(n, a_params, self._env)
            if "pre" in a:
                proc.add_precondition(
                    self._parse_exp(
                        problem,
                        proc,
                        types_map,
                        {},
                        a["pre"],
                        domain_str,
                    )
                )
            if "eff" in a:
                self._add_effect(
                    problem,
                    proc,
                    types_map,
                    a["eff"],
                    domain_str,
                )
            problem.add_process(proc)

        for a in domain_res.get("events", []):
            n = a["name"]
            a_params = self._get_params(a, types_map, domain_str)
            evt = up.model.Event(n, a_params, self._env)
            if "pre" in a:
                evt.add_precondition(
                    self._parse_exp(
                        problem,
                        evt,
                        types_map,
                        {},
                        a["pre"],
                        domain_str,
                    )
                )
            if "eff" in a:
                self._add_effect(
                    problem,
                    evt,
                    types_map,
                    a["eff"],
                    domain_str,
                )
            problem.add_event(evt)

        for a in domain_res.get("actions", []):
            n = a["name"]
            a_params = self._get_params(a, types_map, domain_str)
            if "duration" in a:
                dur_act = up.model.DurativeAction(n, a_params, self._env)
                dur = a["duration"]
                if dur[0].value == "=":
                    dur_act.set_fixed_duration(
                        self._parse_exp(
                            problem, dur_act, types_map, {}, dur[2], domain_str
                        )
                    )
                elif dur[0].value == "and":
                    upper = None
                    lower = None
                    is_left_open = None
                    is_right_open = None
                    for j in range(1, len(dur)):
                        if dur[j][0].value in (">=", ">") and lower is None:
                            lower = self._parse_exp(
                                problem, dur_act, types_map, {}, dur[j][2], domain_str
                            )
                            is_left_open = dur[j][0].value == ">"
                        elif dur[j][0].value in ("<=", "<") and upper is None:
                            upper = self._parse_exp(
                                problem, dur_act, types_map, {}, dur[j][2], domain_str
                            )
                            is_right_open = dur[j][0].value == "<"
                        else:
                            raise PDDLSyntaxError(
                                f"Not able to handle duration constraint of action {n}"
                                + f"Line: {dur.line_start(domain_str)}, col: {dur.col_start(domain_str)}",
                            )
                    if lower is None or upper is None:
                        raise PDDLSyntaxError(
                            f"Not able to handle duration constraint of action {n}"
                            + f"Line: {dur.line_start(domain_str)}, col: {dur.col_start(domain_str)}",
                        )
                    assert is_left_open is not None and is_right_open is not None
                    d = up.model.DurationInterval(
                        lower, upper, is_left_open, is_right_open
                    )
                    dur_act.set_duration_constraint(d)
                else:
                    raise PDDLSyntaxError(
                        f"Not able to handle duration constraint of action {n}"
                        + f"Line: {dur.line_start(domain_str)}, col: {dur.col_start(domain_str)}",
                    )
                if "cond" in a:
                    cond = a["cond"]
                    self._add_condition(problem, dur_act, cond, types_map, domain_str)
                eff = a["eff"]
                self._add_timed_effects(problem, dur_act, types_map, eff, domain_str)
                problem.add_action(dur_act)
                has_actions_cost = has_actions_cost and self._durative_action_has_cost(
                    dur_act
                )
            else:
                act: typing.Optional[
                    Union[
                        up.model.contingent.SensingAction, up.model.InstantaneousAction
                    ]
                ] = None
                if "obs" in a:
                    act = up.model.contingent.SensingAction(n, a_params, self._env)
                    obs_fluent = a["obs"]
                    if obs_fluent[0].value == "and":  # more than 1 fluent
                        for i in range(1, len(obs_fluent)):
                            act.add_observed_fluent(
                                self._parse_exp(
                                    problem,
                                    act,
                                    types_map,
                                    {},
                                    obs_fluent[i],
                                    domain_str,
                                )
                            )
                    else:
                        act.add_observed_fluent(
                            self._parse_exp(
                                problem, act, types_map, {}, obs_fluent, domain_str
                            )
                        )
                else:
                    act = up.model.InstantaneousAction(n, a_params, self._env)
                if "pre" in a:
                    act.add_precondition(
                        self._parse_exp(
                            problem,
                            act,
                            types_map,
                            {},
                            a["pre"],
                            domain_str,
                        )
                    )
                if "eff" in a:
                    self._add_effect(
                        problem,
                        act,
                        types_map,
                        a["eff"],
                        domain_str,
                    )
                problem.add_action(act)
                has_actions_cost = (
                    has_actions_cost and self._instantaneous_action_has_cost(act)
                )
        for m in domain_res.get("methods", []):
            assert isinstance(problem, htn.HierarchicalProblem)
            name = m["name"]
            method_params = OrderedDict()
            for g in m.get("params", []):
                t = types_map[g.value[1] if len(g.value) > 1 else Object]
                for p in g.value[0]:
                    method_params[p] = t

            method = htn.Method(name, method_params, self._env)
            achieved_task = m["task"]
            pnames = []
            for i in range(1, len(achieved_task)):
                pname = achieved_task[i].value
                if pname[0] != "?":
                    raise PDDLSyntaxError(
                        f"All arguments of the task {achieved_task} should be parameters."
                        + f"Line: {achieved_task.line_start(domain_str)}, col: {achieved_task.col_start(domain_str)}",
                    )
                pnames.append(pname)
            achieved_task_params = [method.parameter(pname[1:]) for pname in pnames]
            method.set_task(
                problem.get_task(achieved_task[0].value), *achieved_task_params
            )
            if "ordered-subtasks" in m:
                ost = m.get("ordered-subtasks")
                ord_subs = self._parse_subtasks(
                    ost, method, problem, types_map, domain_str
                )
                for s in ord_subs:
                    method.add_subtask(s)
                method.set_ordered(*ord_subs)
            if "subtasks" in m:
                st = m.get("subtasks")
                subs = self._parse_subtasks(st, method, problem, types_map, domain_str)
                for s in subs:
                    method.add_subtask(s)
            if "ordering" in m:
                stack = [m.get("ordering")]
                while stack:
                    ordering = stack.pop(0)
                    if len(ordering) == 0:
                        pass
                    elif ordering[0].value == "and":
                        # add the rest of the expression to the queue
                        for i in range(1, len(ordering)):
                            stack.append(ordering[i])
                    elif ordering[0].value == "<":
                        if len(ordering) != 3:
                            raise PDDLSyntaxError(
                                f"Wrong number of parameters in ordering relation: {ordering}"
                                + f"Line: {ordering.line_start(domain_str)}, col: {ordering.col_start(domain_str)}",
                            )
                        left = method.get_subtask(ordering[1].value)
                        right = method.get_subtask(ordering[2].value)
                        method.set_strictly_before(left, right)
                    else:
                        raise PDDLSyntaxError(
                            f"Invalid expression in ordering, expected 'and' or '<' but got '{ordering[0]}"
                            + f"Line: {ordering.line_start(domain_str)}, col: {ordering.col_start(domain_str)}",
                        )
            if "precondition" in m:
                method.add_precondition(
                    self._parse_exp(
                        problem,
                        method,
                        types_map,
                        {},
                        m["precondition"],
                        domain_str,
                    )
                )
            problem.add_method(method)

        if problem_res is not None:
            assert problem_str is not None
            problem.name = problem_res["name"]

            for g in problem_res.get("objects", []):
                t = types_map[g[1] if len(g) > 1 else Object]
                for o in g[0]:
                    problem.add_object(up.model.Object(o, t, problem.environment))

            tasknet = problem_res.get("htn", None)
            if tasknet is not None:
                assert isinstance(problem, htn.HierarchicalProblem)

                for tn_variables in tasknet.get("params", []):
                    tn_var_type = types_map[
                        tn_variables.value[1] if len(tn_variables.value) > 1 else Object
                    ]
                    for tn_var_name in tn_variables.value[0]:
                        problem.task_network.add_variable(tn_var_name, tn_var_type)

                ta = tasknet.get("tasks", None)
                if ta:
                    subtasks = self._parse_subtasks(
                        ta,
                        problem.task_network,
                        problem,
                        types_map,
                        problem_str,
                    )
                    for task in subtasks:
                        problem.task_network.add_subtask(task)

                ot = tasknet.get("ordered-tasks", None)
                if ot:
                    subtasks = self._parse_subtasks(
                        ot,
                        problem.task_network,
                        problem,
                        types_map,
                        problem_str,
                    )
                    prev = None
                    for task in subtasks:
                        cur = problem.task_network.add_subtask(task)
                        if prev is not None:
                            problem.task_network.set_strictly_before(prev, cur)
                        prev = cur

                oq = tasknet.get("ordering", None)
                stack = []
                if oq:
                    stack.append(oq)
                while len(stack) > 0:
                    ordering = stack.pop(0)
                    if len(ordering) == 0:
                        pass
                    elif ordering[0].value == "and":
                        # add the rest of the expression to the queue
                        for i in range(1, len(ordering)):
                            stack.append(ordering[i])
                    elif ordering[0].value == "<":
                        if len(ordering) != 3:
                            raise PDDLSyntaxError(
                                f"Wrong number of parameters in ordering relation: {ordering}"
                                + f"Line: {ordering.line_start(domain_str)}, col: {ordering.col_start(domain_str)}",
                            )
                        left = problem.task_network.get_subtask(ordering[1].value)
                        right = problem.task_network.get_subtask(ordering[2].value)
                        problem.task_network.set_strictly_before(left, right)
                    else:
                        raise PDDLSyntaxError(
                            f"Invalid expression in ordering, expected 'and' or '<' but got '{ordering[0]}"
                            + f"Line: {ordering.line_start(domain_str)}, col: {ordering.col_start(domain_str)}",
                        )

                cs = tasknet.get("constraints", None)
                if cs:
                    constraints = cs
                    for i in range(len(constraints)):
                        constraint = constraints[i]
                        problem.task_network.add_constraint(
                            self._parse_exp(
                                problem,
                                problem.task_network,
                                types_map,
                                {},
                                constraint,
                                problem_str,
                            )
                        )

            init_list = problem_res.get("init", [])
            if (
                len(init_list) == 1
                and init_list[0].value
                and init_list[0][0].value == "and"
            ):
                init_list = init_list[0].value[1:]
            for j in init_list:
                init = j
                operator = init[0].value
                if operator == "=":
                    problem.set_initial_value(
                        self._parse_exp(
                            problem, None, types_map, {}, init[1], problem_str
                        ),
                        self._parse_exp(
                            problem, None, types_map, {}, init[2], problem_str
                        ),
                    )
                elif (
                    len(init) == 3
                    and operator == "at"
                    and init[1].value.replace(".", "", 1).isdigit()
                ):
                    try:
                        ti = up.model.StartTiming(Fraction(init[1].value))
                    except ValueError:
                        start_line, start_col = (
                            init.line_start(problem_str),
                            init.col_start(problem_str),
                        )
                        end_line, end_col = (
                            init.line_end(problem_str),
                            init.col_end(problem_str),
                        )
                        raise PDDLSyntaxError(
                            f"Expected number, found {init[1].value} in expression from line: {start_line}, col {start_col} to line: {end_line}, col {end_col}"
                        )
                    if init[2][0].value in ["assign", "increase", "decrease"]:
                        fe = self._parse_exp(
                            problem, None, types_map, {}, init[2][1], problem_str
                        )
                        va = self._parse_exp(
                            problem, None, types_map, {}, init[2][2], problem_str
                        )
                        if init[2][0].value == "assign":
                            problem.add_timed_effect(ti, fe, va)
                        elif init[2][0].value == "increase":
                            problem.add_increase_effect(ti, fe, va)
                        elif init[2][0].value == "decrease":
                            problem.add_decrease_effect(ti, fe, va)
                    else:
                        va = self._parse_exp(
                            problem, None, types_map, {}, init[2], problem_str
                        )
                        if va.is_fluent_exp():
                            problem.add_timed_effect(ti, va, self._em.TRUE())
                        elif va.is_not():
                            problem.add_timed_effect(ti, va.arg(0), self._em.FALSE())
                        else:
                            raise PDDLSyntaxError(
                                f"Not able to handle this TIL {init}"
                                + f"Line: {init.line_start(problem_str)}, col: {init.col_start(problem_str)}",
                            )
                elif operator == "oneof":
                    assert isinstance(problem, ContingentProblem)
                    fluents = [
                        self._parse_exp(
                            problem, None, types_map, {}, init[x], problem_str
                        )
                        for x in range(1, len(init))
                    ]
                    problem.add_oneof_initial_constraint(fluents)
                elif operator == "or":
                    assert isinstance(problem, ContingentProblem)
                    fluents = [
                        self._parse_exp(
                            problem, None, types_map, {}, init[x], problem_str
                        )
                        for x in range(1, len(init))
                    ]
                    problem.add_or_initial_constraint(fluents)
                elif operator == "unknown":
                    assert isinstance(problem, ContingentProblem)
                    if len(init) != 2:
                        raise PDDLSyntaxError(
                            "`unknown` constraint requires exactly one argument."
                            + f"Line: {init.line_start(problem_str)}, col: {init.col_start(problem_str)}",
                        )
                    arg = self._parse_exp(
                        problem, None, types_map, {}, init[1], problem_str
                    )
                    problem.add_unknown_initial_constraint(arg)
                else:
                    exp = self._parse_exp(
                        problem, None, types_map, {}, init, problem_str
                    )
                    if not exp.is_not():
                        if not exp.is_fluent_exp():
                            raise PDDLSyntaxError(
                                f"In init expected predicate, found {exp}\n"
                                + f"Line: {init.line_start(problem_str)}, col: {init.col_start(problem_str)}",
                            )
                        problem.set_initial_value(
                            exp,
                            self._em.TRUE(),
                        )
                    elif not exp.arg(0).is_fluent_exp():
                        raise PDDLSyntaxError(
                            f"In init expected (not predicate), found {exp}\n"
                            + f"Line: {init.line_start(problem_str)}, col: {init.col_start(problem_str)}",
                        )
            if "goal" in problem_res:
                problem.add_goal(
                    self._parse_exp(
                        problem,
                        None,
                        types_map,
                        {},
                        problem_res["goal"],
                        problem_str,
                    )
                )
            elif not isinstance(problem, htn.HierarchicalProblem):
                raise PDDLSyntaxError("Missing goal section in problem file.")

            if "constraints" in problem_res:
                for tc in problem_res["constraints"]:
                    problem.add_trajectory_constraint(
                        self._parse_exp(
                            problem,
                            None,
                            types_map,
                            {},
                            tc,
                            problem_str,
                        )
                    )

            has_actions_cost = has_actions_cost and self._problem_has_actions_cost(
                problem
            )
            optimization = problem_res.get("optimization", None)
            m = problem_res.get("metric", None)

            if m is not None:
                metric = m
                if (
                    optimization == "minimize"
                    and len(metric) == 1
                    and metric[0].value == "total-time"
                ):
                    problem.add_quality_metric(
                        up.model.metrics.MinimizeMakespan(self._env)
                    )
                else:
                    metric_exp = self._parse_exp(
                        problem, None, types_map, {}, metric, problem_str
                    )
                    if (
                        has_actions_cost
                        and optimization == "minimize"
                        and metric_exp == self._totalcost
                    ):
                        costs: Dict[up.model.Action, up.model.Expression] = {}
                        # cleared below unless every action costs exactly 1
                        use_plan_length = True
                        problem._remove_fluent(self._totalcost.fluent())
                        if self._totalcost in problem._initial_value:
                            problem._initial_value.pop(self._totalcost)
                        start_timing, end_timing = (
                            up.model.StartTiming(),
                            up.model.EndTiming(),
                        )
                        for a in problem.actions:
                            if isinstance(a, up.model.InstantaneousAction):
                                cost = None
                                for e in a.effects:
                                    if e.fluent == self._totalcost:
                                        cost = e
                                        break
                                if cost is not None:
                                    costs[a] = cost.value
                                    a._effects.remove(cost)
                                    if not (
                                        cost.value.is_int_constant()
                                        and cost.value.constant_value() == 1
                                    ):
                                        use_plan_length = False
                                else:
                                    use_plan_length = False
                            else:
                                assert isinstance(a, up.model.DurativeAction)
                                use_plan_length = False
                                cost, effects_list = None, None
                                for timing, el in a.effects.items():
                                    if timing in (start_timing, end_timing):
                                        for e in el:
                                            if e.fluent == self._totalcost:
                                                if cost is not None:
                                                    raise UPUnsupportedProblemTypeError(
                                                        f"Action {a.name} has more than one effect modifying it's cost"
                                                    )
                                                cost, effects_list = e, el
                                                break
                                if cost is not None:
                                    assert effects_list is not None
                                    costs[a] = cost.value
                                    effects_list.remove(cost)
                                else:
                                    use_plan_length = False
                        if use_plan_length:
                            problem.add_quality_metric(
                                up.model.metrics.MinimizeSequentialPlanLength(self._env)
                            )
                        else:
                            problem.add_quality_metric(
                                up.model.metrics.MinimizeActionCosts(
                                    costs, self._em.Int(0), self._env
                                )
                            )
                    else:
                        if optimization == "minimize":
                            problem.add_quality_metric(
                                up.model.metrics.MinimizeExpressionOnFinalState(
                                    metric_exp, self._env
                                )
                            )
                        elif optimization == "maximize":
                            problem.add_quality_metric(
                                up.model.metrics.MaximizeExpressionOnFinalState(
                                    metric_exp, self._env
                                )
                            )
        return problem

    def parse_problem(
        self, domain_filename: str, problem_filename: typing.Optional[str] = None
    ) -> "up.model.Problem":
        """
        Takes in input a filename containing the `PDDL` domain and optionally a filename
        containing the `PDDL` problem and returns the parsed `Problem`.

        Note: that if the `problem_filename` is `None`, an incomplete `Problem` will be returned.

        Note: due to PDDL case-insensitivity, everything in the PDDL files will be turned to
        lower case, so the names of fluents, actions etc. and the error report will all be
        in lower-case.

        :param domain_filename: The path to the file containing the `PDDL` domain.
        :param problem_filename: Optionally the path to the file containing the `PDDL` problem.
        :return: The `Problem` parsed from the given pddl domain + problem.
        """
        with open(domain_filename, encoding="utf-8-sig") as domain_file:
            domain_str = domain_file.read()

        problem_str = None
        if problem_filename is not None:
            with open(problem_filename, encoding="utf-8-sig") as problem_file:
                problem_str = problem_file.read()

        return self.parse_problem_string(domain_str, problem_str)

    def parse_problem_string(
        self, domain_str: str, problem_str: typing.Optional[str] = None
    ) -> "up.model.Problem":
        """
        Takes in input a str representing the `PDDL` domain and optionally a str
        representing the `PDDL` problem and returns the parsed `Problem`.

        Note that if the `problem_str` is `None`, an incomplete `Problem` will be returned.

        Note: due to PDDL case-insensitivity, everything in the PDDL files will be turned to
        lower case, so the names of fluents, actions etc. and the error report will all be
        in lower-case.

        :param domain_filename: The string representing the `PDDL` domain.
        :param problem_filename: Optionally the string representing the `PDDL` problem.
        :return: The `Problem` parsed from the given pddl domain + problem.
        """
        domain_str = domain_str.replace("\t", " ").lower()
        domain_res = _parse_domain(domain_str)

        if problem_str is not None:
            problem_str = problem_str.replace("\t", " ").lower()
            problem_res = _parse_problem_sexpr(problem_str)
        else:
            problem_res = None

        return self._parse_problem(domain_res, domain_str, problem_res, problem_str)

    def parse_plan(
        self,
        problem: "up.model.Problem",
        plan_filename: str,
        get_item_named: typing.Optional[
            Callable[
                [str],
                "up.io.pddl_writer.WithName",
            ]
        ] = None,
    ) -> "up.plans.Plan":
        """
        Takes a problem, a filename and optionally a map of renaming and returns the plan parsed from the file.

        The format of the file must be:
        ``(action-name param1 param2 ... paramN)`` in each line for SequentialPlans
        ``start-time: (action-name param1 param2 ... paramN) [duration]`` in each line for TimeTriggeredPlans,
        where ``[duration]`` is optional and not specified for InstantaneousActions.

        :param problem: The up.model.problem.Problem instance for which the plan is generated.
        :param plan_filename: The path of the file in which the plan is written.
        :param get_item_named: A function that takes a name and returns the original up.model element instance
            linked to that renaming; if None the problem is used to retrieve the actions and objects in the
            plan from their name.
        :return: The up.plans.Plan corresponding to the parsed plan from the file
        """
        with open(plan_filename, encoding="utf-8-sig") as plan:
            return self.parse_plan_string(problem, plan.read(), get_item_named)

    def parse_plan_string(
        self,
        problem: "up.model.Problem",
        plan_str: str,
        get_item_named: typing.Optional[
            Callable[
                [str],
                "up.io.pddl_writer.WithName",
            ]
        ] = None,
    ) -> "up.plans.Plan":
        """
        Takes a problem, a string and optionally a map of renaming and returns the plan parsed from the string.

        The format of the file must be:
        ``(action-name param1 param2 ... paramN)`` in each line for SequentialPlans
        ``start-time: (action-name param1 param2 ... paramN) [duration]`` in each line for TimeTriggeredPlans,
        where ``[duration]`` is optional and not specified for InstantaneousActions.

        :param problem: The up.model.problem.Problem instance for which the plan is generated.
        :param plan_str: The plan in string.
        :param get_item_named: A function that takes a name and returns the original up.model element instance
            linked to that renaming; if None the problem is used to retrieve the actions and objects in the
            plan from their name.:return: The up.plans.Plan corresponding to the parsed plan from the string
        """
        actions: List = []
        is_tt = False
        for line in plan_str.splitlines():
            if re.match(r"^\s*(;.*)?$", line):
                continue
            line = line.lower()
            s_ai = re.match(r"^\s*\(\s*([\w?-]+)((\s+[\w?-]+)*)\s*\)\s*$", line)
            t_ai = re.match(
                r"^\s*(\d+\.?\d*)\s*:\s*\(\s*([\w?-]+)((\s+[\w?-]+)*)\s*\)\s*(\[\s*(\d+\.?\d*)\s*\])?\s*$",
                line,
            )
            if s_ai:
                assert is_tt == False
                name = s_ai.group(1)
                params_name = s_ai.group(2).split()
            elif t_ai:
                is_tt = True
                start = Fraction(t_ai.group(1))
                name = t_ai.group(2)
                params_name = t_ai.group(3).split()
                dur = None
                if t_ai.group(6) is not None:
                    dur = Fraction(t_ai.group(6))
            else:
                raise UPException(
                    "Error parsing plan generated by "
                    + self.__class__.__name__
                    + ". Cannot interpret "
                    + line
                )

            action = (
                get_item_named(name)
                if get_item_named is not None
                else problem.action(name)
            )
            assert isinstance(action, up.model.Action), "Wrong plan or renaming."
            parameters = []
            for p in params_name:
                obj = (
                    get_item_named(p)
                    if get_item_named is not None
                    else problem.object(p)
                )
                assert isinstance(obj, up.model.Object), "Wrong plan or renaming."
                parameters.append(problem.environment.expression_manager.ObjectExp(obj))
            act_instance = up.plans.ActionInstance(action, tuple(parameters))
            if is_tt:
                actions.append((start, act_instance, dur))
            else:
                actions.append(act_instance)
        if is_tt:
            return up.plans.TimeTriggeredPlan(actions)
        else:
            return up.plans.SequentialPlan(actions)
