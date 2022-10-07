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
from pprint import pprint
import unified_planning as up
import unified_planning.model.htn as htn
import unified_planning.model.walkers
import pyparsing
import typing
from unified_planning.io.anml_grammar import (
    TK_ALL,
    TK_AND,
    TK_ASSIGN,
    TK_DECREASE,
    TK_DIV,
    TK_END,
    TK_EQUALS,
    TK_GE,
    TK_GT,
    TK_IMPLIES,
    TK_INCREASE,
    TK_L_BRACKET,
    TK_L_PARENTHESIS,
    TK_LE,
    TK_LT,
    TK_MINUS,
    TK_NOT,
    TK_OR,
    TK_PLUS,
    TK_R_BRACKET,
    TK_R_PARENTHESIS,
    TK_START,
    TK_TIMES,
    ANMLGrammar,
    TK_BOOLEAN,
    TK_INTEGER,
    TK_FLOAT,
)
from unified_planning.environment import Environment, get_env
from unified_planning.model.types import _UserType as UT
from unified_planning.exceptions import UPUsageError
from unified_planning.model import (
    Effect,
    EffectKind,
    FNode,
    StartTiming,
    GlobalStartTiming,
    EndTiming,
    GlobalEndTiming,
    ClosedTimeInterval,
    OpenTimeInterval,
    LeftOpenTimeInterval,
    RightOpenTimeInterval,
)
from collections import OrderedDict, deque
from fractions import Fraction
from typing import Deque, Dict, Tuple, Union, Callable, List, cast
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


class ANMLReader:
    """
    Parse a `PDDL` domain file and, optionally, a `PDDL` problem file and generate the equivalent :class:`~unified_planning.model.Problem`.
    """

    def __init__(self, env: typing.Optional[Environment] = None):
        self._env = get_env(env)
        self._em = self._env.expression_manager
        self._tm = self._env.type_manager
        self.grammar = ANMLGrammar()
        self._pp_problem = self.grammar.problem
        self._fve = self._env.free_vars_extractor

        self._operators: Dict[str, Callable] = {
            TK_AND: self._em.And,
            TK_OR: self._em.Or,
            TK_NOT: self._em.Not,
            TK_IMPLIES: self._em.Implies,
            TK_GE: self._em.GE,
            TK_LE: self._em.LE,
            TK_GT: self._em.GT,
            TK_LT: self._em.LT,
            TK_EQUALS: self._em.Equals,
            TK_PLUS: self._em.Plus,
            TK_MINUS: self._em.Minus,
            TK_DIV: self._em.Div,
            TK_TIMES: self._em.Times,
        }

    def parse_problem(self, problem_filename: str) -> "up.model.Problem":
        """
        Takes in input a filename containing the `PDDL` domain and optionally a filename
        containing the `PDDL` problem and returns the parsed `Problem`.

        Note that if the `problem_filename` is `None`, an incomplete `Problem` will be returned.

        :param domain_filename: The path to the file containing the `PDDL` domain.
        :param problem_filename: Optionally the path to the file containing the `PDDL` problem.
        :return: The `Problem` parsed from the given pddl domain + problem.
        """
        problem_res = self._pp_problem.parseFile(problem_filename, parse_all=True)

        self._problem = up.model.Problem(
            problem_filename,
            self._env,
            initial_defaults={self._tm.BoolType(): self._em.FALSE()},
        )

        self._types_map: Dict[str, "up.model.Type"] = {}
        for type_res in self.grammar.types:
            up_type = self.parse_type_def(type_res)
            assert up_type.is_user_type()
            self._types_map[cast(UT, up_type).name] = up_type

        for fluent_res in self.grammar.fluents:
            up_fluent = self.parse_fluent(fluent_res)
            self._problem.add_fluent(up_fluent)

        for objects_res in self.grammar.objects:
            up_objects = self.parse_objects(objects_res)
            self._problem.add_objects(up_objects)

        for action_res in self.grammar.actions:
            up_action = self.parse_action(action_res)
            self._problem.add_action(up_action)

        # print(str(self.grammar.types).replace("ParseResults", ""))
        # print(str(self.grammar.fluents).replace("ParseResults", ""))
        # print(str(self.grammar.actions).replace("ParseResults", ""))
        # print(str(self.grammar.objects).replace("ParseResults", ""))
        # print(str(self.grammar.timed_assignment_or_goal).replace("ParseResults", ""))
        # pprint([g.as_list() for g in self.grammar.timed_assignments_or_goals])
        return self._problem

    def parse_type_def(self, type_res: ParseResults) -> "up.model.Type":
        # TODO: handle typing hierarchy
        if len(type_res["supertypes"]) != 0:
            raise NotImplementedError
        return self._tm.UserType(type_res["name"])

    def parse_type_ref(self, type_res: ParseResults) -> "up.model.Type":
        # TODO handle integer and real
        name = type_res[0]
        assert isinstance(name, str)
        if name == TK_BOOLEAN:
            return self._tm.BoolType()
        elif name in (TK_INTEGER, TK_FLOAT):
            raise NotImplementedError
        else:  # TODO handle keyError
            return self._types_map[name]

    def parse_fluent(self, fluent_res: ParseResults) -> "up.model.Fluent":
        fluent_type = self.parse_type_ref(fluent_res["type"])
        fluent_name = fluent_res["name"]
        params: Dict[str, "up.model.Type"] = self.parse_parameters_def(
            fluent_res["parameters"]
        )
        return up.model.Fluent(fluent_name, fluent_type, _signature=params)

    def parse_objects(self, objects_res: ParseResults) -> List["up.model.Object"]:
        objects_type = self.parse_type_ref(objects_res["type"])
        up_objects: List["up.model.Object"] = []
        for name in objects_res["names"]:
            assert isinstance(name, str), "parsing error"
            up_objects.append(up.model.Object(name, objects_type))
        return up_objects

    def parse_action(self, action_res: ParseResults) -> "up.model.Action":
        name = action_res["name"]
        assert isinstance(name, str), "parsing error"
        params = self.parse_parameters_def(action_res["parameters"])
        action = up.model.DurativeAction(name, _parameters=params)
        action_parameters: Dict[str, "up.model.Parameters"] = {
            n: action.parameter(n) for n in params
        }
        self.populate_parsed_action_body(action, action_res["body"], action_parameters)
        return action

    def populate_parsed_action_body(
        self,
        action: "up.model.DurativeAction",
        action_body_res: ParseResults,
        action_parameters: Dict[str, "up.model.Parameters"],
    ) -> None:
        for interval_and_exp in action_body_res:
            up_interval = self.parse_interval(interval_and_exp[0])
            exp_res = interval_and_exp[1][0]
            if exp_res[1] in (TK_ASSIGN, TK_INCREASE, TK_DECREASE):
                assert isinstance(
                    up_interval, up.model.Timing
                ), "Assignments can't have intervals"
                effect = self.parse_assignment(
                    exp_res[0], exp_res[2], exp_res[1], action_parameters
                )
                action._add_effect_instance(up_interval, effect)
            else:
                condition = self.parse_expression(exp_res, action_parameters)
                action.add_condition(up_interval, condition)

    def parse_parameters_def(
        self, parameters_res: ParseResults
    ) -> OrderedDict[str, "up.model.Type"]:
        up_params: OrderedDict[str, "up.model.Type"] = OrderedDict()
        for parameter_res in parameters_res:
            param_type_res = parameter_res[0]
            param_name_res = parameter_res[1]
            assert isinstance(param_name_res, str)
            up_params[param_name_res] = self.parse_type_ref(param_type_res)
        return up_params

    def parse_interval(
        self, interval_res: ParseResults, is_global: bool = False
    ) -> Union["up.model.Timing", "up.model.TimeInterval"]:
        if len(interval_res) == 0:
            if is_global:
                return up.model.GlobalStartTiming()
            else:
                return up.model.StartTiming()

        elif len(interval_res) == 3:
            l_par = interval_res[0]
            timing_and_exp = interval_res[1]
            r_par = interval_res[2]
            timing_type = timing_and_exp[0]

            assert l_par in (TK_L_PARENTHESIS, TK_L_BRACKET) and r_par in (
                TK_R_PARENTHESIS,
                TK_R_BRACKET,
            ), "parsing error"

            if timing_type != TK_ALL:
                assert (
                    l_par == TK_L_BRACKET
                ), "point intervals can't have '('; use '[' instead"
                assert (
                    r_par == TK_R_BRACKET
                ), "point intervals can't have ')'; use ']' instead"
                return self.parse_timing(timing_and_exp)
            else:  # timing_type == TK_ALL, just define start and end
                start, end = (
                    (GlobalStartTiming(), GlobalEndTiming())
                    if is_global
                    else (StartTiming(), EndTiming())
                )
                assert (
                    len(timing_and_exp) == 1
                ), f"with the {TK_ALL} timing no expression is accepted"
        else:
            assert len(interval_res) == 4, "Parsing error, not able to handle"
            l_par = interval_res[0]
            start = self.parse_timing(interval_res[1])
            end = self.parse_timing(interval_res[2])
            r_par = interval_res[3]

        if l_par == TK_L_BRACKET and r_par == TK_R_BRACKET:
            return up.model.ClosedTimeInterval(start, end)
        elif l_par == TK_L_BRACKET:
            return up.model.RightOpenTimeInterval(start, end)
        elif r_par == TK_R_BRACKET:
            return up.model.LeftOpenTimeInterval(start, end)
        return up.model.OpenTimeInterval(start, end)

    def parse_timing(
        self, timing_and_exp: ParseResults, is_global: bool = False
    ) -> "up.model.Timing":
        timing_type = timing_and_exp[0]
        delay = 0
        if len(timing_and_exp) > 1:  # There is a delay
            assert len(timing_and_exp) == 2, "unexpected parsing error"
            up_exp = self.parse_expression(timing_and_exp[1])
            delay = up_exp.simplify()
            assert (
                delay.is_int_constant() or delay.is_real_constant()
            ), "Timing delay must simplify as a numeric constant"

        if timing_type == TK_START and is_global:
            return up.model.GlobalStartTiming(delay)
        elif timing_type == TK_START:
            return up.model.StartTiming(delay)
        elif timing_type == TK_END and is_global:
            return up.model.GlobalEndTiming(delay)
        elif timing_type == TK_END:
            return up.model.EndTiming(delay)
        else:
            raise NotImplementedError(
                f"Currently the unified planning does not support the timing {timing_type}"
            )

    def parse_assignment(
        self,
        fluent_ref: ParseResults,
        assigned_expression: ParseResults,
        assignment_operator: str,
        parameters: Dict[str, "up.model.Parameters"],
    ) -> "up.model.Effect":
        up_fluent = self.parse_expression(fluent_ref, parameters)
        assert (
            up_fluent.is_fluent_exp()
        ), "left side of the assignment is not a valid fluent"
        up_value = self.parse_expression(assigned_expression, parameters)
        if assignment_operator == TK_ASSIGN:
            kind = EffectKind.ASSIGN
        elif assignment_operator == TK_INCREASE:
            kind = EffectKind.INCREASE
        elif assignment_operator == TK_DECREASE:
            kind = EffectKind.DECREASE
        else:
            raise NotImplementedError(
                f"Currently the unified planning does not support the assignment operator {assignment_operator}"
            )
        return Effect(up_fluent, up_value, kind=kind)

    def parse_expression(
        self, expression: ParseResults, parameters: Dict[str, "up.model.Parameters"]
    ) -> "up.model.FNode":
        stack: Deque[Tuple[ParseResults, bool]] = deque()
        solved: Deque[FNode] = deque()
        print(expression)
        print(len(expression))
        stack.append(expression)
        while 1:
            try:
                exp, solved = stack.pop()
            except IndexError:
                break
            if solved:
                pass
            else:
                if isinstance(exp, ParseResults):
                    stack.append((exp, True))
                    for e in exp:
                        stack.append(e, False)
                elif isinstance(exp, str):
                    param = parameters.get(exp, None)
                    if param is not None:
                        solved.append(self._em.ParameterExp(param))

                else:
                    raise NotImplementedError
