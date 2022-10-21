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


from collections import OrderedDict
import unified_planning as up
import pyparsing
import networkx as nx
from unified_planning.io.anml_grammar import (
    TK_ALL,
    TK_AND,
    TK_ASSIGN,
    TK_DECREASE,
    TK_DIV,
    TK_DURATION,
    TK_END,
    TK_EQUALS,
    TK_FALSE,
    TK_FORALL,
    TK_EXISTS,
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
    TK_NOT_EQUALS,
    TK_OR,
    TK_PLUS,
    TK_R_BRACKET,
    TK_R_PARENTHESIS,
    TK_START,
    TK_TIMES,
    TK_TRUE,
    TK_WHEN,
    TK_XOR,
    ANMLGrammar,
    TK_BOOLEAN,
    TK_INTEGER,
    TK_FLOAT,
)
from unified_planning.environment import Environment, get_env
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model import (
    DurationInterval,
    Effect,
    EffectKind,
    FNode,
    StartTiming,
    GlobalStartTiming,
    EndTiming,
    GlobalEndTiming,
    FixedDuration,
    Timing,
    TimeInterval,
    Type,
    Parameter,
    Variable,
)
from fractions import Fraction
from typing import Dict, Set, Tuple, Union, Callable, List, Optional

if pyparsing.__version__ < "3.0.0":
    from pyparsing import ParseResults
else:
    from pyparsing.results import ParseResults


class ANMLReader:
    """
    Class that offers the capability, with the :func:`parse_problem <unified_planning.io.ANMLReader.parse_problem>`, to create a :class:`~unified_planning.model.Problem` from an
    `ANML` file.

    The assumptions made in order for this Reader to work are the followings:
    1. statements containing the duration of an action are not mixed with other statements ( `duration == 3 and at(l_from);` ).
    2. the action duration can be set with:
        - `duration == expression;`
        - `duration := expression;`
        - `duration CT expression and duration CT expression`, where CT are Compare Tokens, so `>`, `>=`, `<` and `<=`.
        All the other ways to define the duration of an Action are not supported.
    3. Statements containing both conditions and effects are not supported ( `(at(l_from) == true) := false);` or `(at(l_from) == true) and (at(l_from) := false);` ).
    4. Quantifier body does not support intervals, they can only be defined outside.
    5. Conditional effects are not supported inside an expression block.
    """

    def __init__(self, env: Optional[Environment] = None):
        self._env = get_env(env)
        self._em = self._env.expression_manager
        self._tm = self._env.type_manager

        self._operators: Dict[str, Callable] = {
            TK_AND: self._em.And,
            TK_OR: self._em.Or,
            TK_NOT: self._em.Not,
            TK_XOR: (
                lambda x, y: self._em.And(
                    self._em.Or(x, y), self._em.Or(self._em.Not(x), self._em.Not(y))
                )
            ),
            TK_IMPLIES: self._em.Implies,
            TK_GE: self._em.GE,
            TK_LE: self._em.LE,
            TK_GT: self._em.GT,
            TK_LT: self._em.LT,
            TK_EQUALS: self._em.Equals,
            TK_NOT_EQUALS: (lambda x, y: self._em.Not(self._em.Equals(x, y))),
            TK_PLUS: self._em.Plus,
            TK_MINUS: self._em.Minus,
            TK_DIV: self._em.Div,
            TK_TIMES: self._em.Times,
            TK_FORALL: self._em.Forall,
            TK_EXISTS: self._em.Exists,
        }

    def parse_problem(self, problem_filename: str) -> "up.model.Problem":
        """
        Takes in input a filename containing an `ANML` problem and returns the parsed `Problem`.

        Check the class documentation for the assumptions made for this parser to work.

        :param problem_filename: The path to the file containing the `ANML` problem.
        :return: The `Problem` parsed from the given anml file.
        """

        # create the grammar and populate it's data structures
        grammar = ANMLGrammar()
        grammar.problem.parseFile(problem_filename, parse_all=True)

        self._problem = up.model.Problem(
            problem_filename,
            self._env,
            initial_defaults={self._tm.BoolType(): self._em.FALSE()},
        )

        types_map: Dict[str, "up.model.Type"] = self._create_types_map(grammar.types)

        for fluent_res in grammar.fluents:
            (up_fluent, initial_default) = self._parse_fluent(fluent_res, types_map)
            if initial_default is not None:
                self._problem.add_fluent(
                    up_fluent, default_initial_value=initial_default
                )
            else:
                self._problem.add_fluent(up_fluent)

        for objects_res in grammar.objects:
            up_objects = self._parse_objects(objects_res, types_map)
            self._problem.add_objects(up_objects)

        for action_res in grammar.actions:
            up_action = self._parse_action(action_res, types_map)
            self._problem.add_action(up_action)

        # params is used in the expression parsing not to recreate an empty dict every time
        params: Dict[str, "Parameter"] = {}
        # global_start and global_end are used to check if the interval is at the beginning or at the end
        global_start = GlobalStartTiming()
        global_end = GlobalEndTiming()

        for interval_and_expression in grammar.timed_assignment_or_goal:
            self._add_goal_or_effect_to_problem(
                interval_and_expression[0],
                interval_and_expression[1],
                params,
                types_map,
                global_start,
                global_end,
            )

        for block_res in grammar.timed_assignments_or_goals:
            interval_and_expressions_res = block_res[0]
            assert (
                len(block_res) == 1 and len(interval_and_expressions_res) == 2
            ), "parsing error"
            for expression in interval_and_expressions_res[1]:
                assert (
                    expression[0] != TK_WHEN
                ), "Conditional effects inside an expression block are not supported"
                self._add_goal_or_effect_to_problem(
                    interval_and_expressions_res[0],
                    expression,
                    params,
                    types_map,
                    global_start,
                    global_end,
                )

        return self._problem

    def _create_types_map(self, types_res) -> Dict[str, "up.model.Type"]:
        # defined types stores the types explicitly defined.
        # Every type needs to be defined explicitly
        defined_types: Set[str] = set()
        # types_graph is used to compute a topological sorting of the type hierarchy,
        # needed to make sure a type is created (in the UP code) before being used as
        # a father of another type; this ordering is not granted by the ANML grammar
        types_graph = nx.DiGraph()
        for type_res in types_res:
            type_name = type_res["name"]
            defined_types.add(type_name)
            previous_element = type_name
            types_graph.add_node(type_name)
            for supertype in type_res["supertypes"]:
                assert isinstance(
                    supertype, str
                ), f"parsing error, type {type_res} is not valid"
                types_graph.add_node(supertype)
                types_graph.add_edge(supertype, previous_element)
                previous_element = supertype

        types_map: Dict[str, "up.model.Type"] = {}

        for type_name in nx.topological_sort(types_graph):
            assert (
                type_name in defined_types
            ), f"The type {type_name} is used in the type hierarchy but is never defined"
            fathers = list(types_graph.predecessors(type_name))
            len_fathers = len(fathers)
            if len_fathers == 0:
                father = None
            elif len_fathers == 1:
                father = types_map[fathers[0]]
            else:
                raise NotImplementedError(
                    f"The type {type_name} has more than one father. Currently this is not supported in the UP."
                )
            types_map[type_name] = self._tm.UserType(type_name, father)

        return types_map

    def _add_goal_or_effect_to_problem(
        self,
        interval: ParseResults,
        expression: ParseResults,
        parameters: Dict[str, "Parameter"],
        types_map: Dict[str, "Type"],
        global_start: "Timing",
        global_end: "Timing",
    ):
        relevant_words = {TK_DURATION, TK_ASSIGN, TK_INCREASE, TK_DECREASE, TK_WHEN}
        contained_words = count_instances(expression, relevant_words)
        c_duration = contained_words[TK_DURATION]
        c_when = contained_words[TK_WHEN]
        c_assign = contained_words[TK_ASSIGN]
        c_increase = contained_words[TK_INCREASE]
        c_decrease = contained_words[TK_DECREASE]
        assert c_duration == 0, "duration keyword can't be used outside of an action"
        if c_when > 0 or (c_assign + c_increase + c_decrease) > 0:  # effect
            interval_and_exp = ParseResults([interval, expression])
            up_timing, up_effect = self._parse_assignment(
                interval_and_exp, parameters, types_map, is_global=True
            )
            if (
                up_timing == global_start
                and not up_effect.is_conditional()
                and up_effect.is_assignment()
            ):
                self._problem.set_initial_value(up_effect.fluent, up_effect.value)
            else:
                self._problem._add_effect_instance(up_timing, up_effect)
        else:  # condition
            up_interval = self._parse_interval(interval, types_map, is_global=True)
            goal = self._parse_expression(expression, parameters, types_map)
            if up_interval == global_end:
                self._problem.add_goal(goal)
            else:
                self._problem.add_timed_goal(up_interval, goal)

    def _parse_type_reference(
        self, type_res: ParseResults, types_map: Dict[str, "up.model.Type"]
    ) -> "up.model.Type":
        name = type_res[0]
        assert isinstance(name, str)
        if name == TK_BOOLEAN:
            return self._tm.BoolType()
        elif name in (TK_INTEGER, TK_FLOAT):
            lower_bound, upper_bound = None, None
            if len(type_res) == 2:
                _p: Dict[str, "up.model.Parameter"] = {}
                interval = type_res[1]
                lower_bound_exp = self._parse_expression(
                    interval[0], parameters=_p, types_map=types_map
                )
                upper_bound_exp = self._parse_expression(
                    interval[1], parameters=_p, types_map=types_map
                )
                if (
                    lower_bound_exp.is_int_constant()
                    or lower_bound_exp.is_real_constant()
                ) and (
                    upper_bound_exp.is_int_constant()
                    or upper_bound_exp.is_real_constant()
                ):
                    lower_bound = lower_bound_exp.constant_value()
                    upper_bound = upper_bound_exp.constant_value()
                else:
                    raise UPProblemDefinitionError(
                        f"bounds of type {type_res} must be integer of real constants"
                    )
            else:
                assert len(type_res) == 1, "Parse error"
            if name == TK_INTEGER:
                assert not isinstance(lower_bound, Fraction) and not isinstance(
                    upper_bound, Fraction
                ), f"Integer bounds of {type_res} must be int expressions"
                return self._tm.IntType(lower_bound, upper_bound)
            else:
                if isinstance(lower_bound, int):
                    lower_bound = Fraction(lower_bound)
                if isinstance(upper_bound, int):
                    upper_bound = Fraction(upper_bound)
                return self._tm.RealType(lower_bound, upper_bound)
        else:
            ret_type = types_map.get(name, None)
            if ret_type is not None:
                return ret_type
            else:
                raise UPProblemDefinitionError(
                    f"UserType {name} is referenced but never defined."
                )

    def _parse_fluent(
        self, fluent_res: ParseResults, types_map: Dict[str, "up.model.Type"]
    ) -> Tuple["up.model.Fluent", Optional["FNode"]]:
        fluent_type = self._parse_type_reference(fluent_res["type"], types_map)
        fluent_name = fluent_res["name"]
        params: "OrderedDict[str, up.model.Type]" = self._parse_parameters_def(
            fluent_res["parameters"], types_map
        )
        if "init" in fluent_res:
            initial_default = self._parse_expression(fluent_res["init"], {}, types_map)
        else:
            initial_default = None
        return (
            up.model.Fluent(fluent_name, fluent_type, _signature=params),
            initial_default,
        )

    def _parse_objects(
        self, objects_res: ParseResults, types_map: Dict[str, "up.model.Type"]
    ) -> List["up.model.Object"]:
        objects_type = self._parse_type_reference(objects_res["type"], types_map)
        up_objects: List["up.model.Object"] = []
        for name in objects_res["names"]:
            assert isinstance(name, str), "parsing error"
            up_objects.append(up.model.Object(name, objects_type))
        return up_objects

    def _parse_action(
        self, action_res: ParseResults, types_map: Dict[str, "up.model.Type"]
    ) -> "up.model.Action":
        name = action_res["name"]
        assert isinstance(name, str), "parsing error"
        params = self._parse_parameters_def(action_res["parameters"], types_map)
        action = up.model.DurativeAction(name, _parameters=params)
        action_parameters: Dict[str, "up.model.Parameter"] = {
            n: action.parameter(n) for n in params
        }
        self._populate_parsed_action_body(
            action, action_res["body"], action_parameters, types_map
        )
        return action

    def _populate_parsed_action_body(
        self,
        action: "up.model.DurativeAction",
        action_body_res: ParseResults,
        action_parameters: Dict[str, "up.model.Parameter"],
        types_map: Dict[str, "Type"],
    ) -> None:
        for interval_and_exp in action_body_res:
            relevant_words = {TK_DURATION, TK_ASSIGN, TK_INCREASE, TK_DECREASE, TK_WHEN}
            contained_words = count_instances(interval_and_exp, relevant_words)
            c_duration = contained_words[TK_DURATION]
            c_when = contained_words[TK_WHEN]
            c_assign = contained_words[TK_ASSIGN]
            c_increase = contained_words[TK_INCREASE]
            c_decrease = contained_words[TK_DECREASE]

            if c_duration > 0:  # handle duration
                assert c_when == 0
                assert c_increase == 0
                assert c_decrease == 0
                duration_exp = interval_and_exp[1][0]
                if c_assign > 0:  # duration assignment
                    assert duration_exp[0][0] == TK_DURATION
                    assert duration_exp[1] == TK_ASSIGN
                    action.set_duration_constraint(
                        FixedDuration(
                            self._parse_expression(
                                duration_exp[2], action_parameters, types_map
                            )
                        )
                    )
                else:
                    if duration_exp[1] == TK_EQUALS:  # duration == exp
                        assert duration_exp[0][0] == TK_DURATION
                        action.set_duration_constraint(
                            FixedDuration(
                                self._parse_expression(
                                    duration_exp[2], action_parameters, types_map
                                )
                            )
                        )
                    else:
                        assert duration_exp[1] == TK_AND
                        left_bound = duration_exp[0]
                        right_bound = duration_exp[2]
                        assert left_bound[0][0] == TK_DURATION
                        assert right_bound[0][0] == TK_DURATION
                        if left_bound[1] not in (TK_GT, TK_GE):
                            left_bound, right_bound = right_bound, left_bound
                        assert left_bound[1] in (TK_GT, TK_GE)
                        assert right_bound[1] in (TK_LT, TK_LE)
                        is_left_open = left_bound[1] == TK_GT
                        is_right_open = right_bound[1] == TK_LT
                        l_bound_exp = self._parse_expression(
                            left_bound[2], action_parameters, types_map
                        )
                        r_bound_exp = self._parse_expression(
                            right_bound[2], action_parameters, types_map
                        )
                        action.set_duration_constraint(
                            DurationInterval(
                                l_bound_exp, r_bound_exp, is_left_open, is_right_open
                            )
                        )
            # end handle duration
            elif c_assign + c_increase + c_decrease > 0:  # handle effects
                up_timing, up_effect = self._parse_assignment(
                    interval_and_exp, action_parameters, types_map
                )
                action._add_effect_instance(up_timing, up_effect)
            # end handle effects
            else:  # handle condition
                assert c_when == 0, "when keyword used in an action precondition"
                up_interval = self._parse_interval(interval_and_exp[0], types_map)
                exp_res = interval_and_exp[1][0]
                condition = self._parse_expression(
                    exp_res, action_parameters, types_map
                )
                action.add_condition(up_interval, condition)

    def _parse_parameters_def(
        self, parameters_res: ParseResults, types_map: Dict[str, "Type"]
    ) -> "OrderedDict[str, Type]":
        up_params: "OrderedDict[str, Type]" = OrderedDict()
        for parameter_res in parameters_res:
            param_type_res = parameter_res[0]
            param_name_res = parameter_res[1]
            assert isinstance(param_name_res, str)
            up_params[param_name_res] = self._parse_type_reference(
                param_type_res, types_map
            )
        return up_params

    def _parse_interval(
        self,
        interval_res: ParseResults,
        types_map: Dict[str, "Type"],
        is_global: bool = False,
    ) -> Union["Timing", "TimeInterval"]:
        if len(interval_res) == 0:
            if is_global:
                # TODO: decide/understand if an undefined interval outside of an action really means GlobalStartTiming or not
                return GlobalStartTiming()
            else:
                return StartTiming()

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
                return self._parse_timing(timing_and_exp, types_map, is_global)
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
            start = self._parse_timing(interval_res[1], types_map, is_global)
            end = self._parse_timing(interval_res[2], types_map, is_global)
            r_par = interval_res[3]

        if l_par == TK_L_BRACKET and r_par == TK_R_BRACKET:
            return up.model.ClosedTimeInterval(start, end)
        elif l_par == TK_L_BRACKET:
            return up.model.RightOpenTimeInterval(start, end)
        elif r_par == TK_R_BRACKET:
            return up.model.LeftOpenTimeInterval(start, end)
        return up.model.OpenTimeInterval(start, end)

    def _parse_timing(
        self,
        timing_and_exp: ParseResults,
        types_map: Dict[str, "Type"],
        is_global: bool = False,
    ) -> "up.model.Timing":
        delay_position = None
        timing_type = timing_and_exp[0]
        delay = self._em.Int(0)
        if len(timing_and_exp) > 1:  # There is a delay
            assert len(timing_and_exp) == 2, "unexpected parsing error"
            delay_position = 1
        else:
            assert len(timing_and_exp) == 1, "parsing error"
            if timing_type not in (TK_START, TK_END):  # interval of the form [10]
                delay_position = 0
                timing_type = TK_START
                assert (
                    is_global
                ), "interval [x] is not valid in an action, try [start + x]"
        if delay_position is not None:
            up_exp = self._parse_expression(
                timing_and_exp[delay_position], parameters={}, types_map=types_map
            )
            delay = up_exp.simplify()
            assert (
                delay.is_int_constant() or delay.is_real_constant()
            ), "Timing delay must simplify as a numeric constant"

        if timing_type == TK_START:
            d = delay.constant_value()
            assert (
                d >= 0
            ), "A negative delay on a start Timing is not supported in the UP"
            if is_global:
                return up.model.GlobalStartTiming(d)
            else:
                return up.model.StartTiming(d)
        elif timing_type == TK_END:
            d = delay.constant_value()
            d = d * -1
            assert (
                d >= 0
            ), "An ANML positive delay on an end Timing is not supported in the UP"
            if is_global:
                return up.model.GlobalEndTiming(delay.constant_value())
            else:
                return up.model.EndTiming(delay.constant_value())
        else:
            raise NotImplementedError(
                f"Currently the unified planning does not support the timing {timing_type}"
            )

    def _parse_assignment(
        self,
        interval_and_effect: ParseResults,
        parameters: Dict[str, "up.model.Parameter"],
        types_map: Dict[str, "Type"],
        is_global: bool = False,
    ) -> Tuple["Timing", "Effect"]:
        interval_res = interval_and_effect[0]
        effect_res = interval_and_effect[1]
        if effect_res[0] == TK_WHEN:  # Conditional effect
            condition_interval = effect_res[1][0]
            condition_exp_res = effect_res[1][1]
            effect_interval = effect_res[2][0]
            effect_exp = effect_res[2][1][0]
            if str(condition_interval) != str(effect_interval):
                raise UPProblemDefinitionError(
                    "In conditional effect parsing the "
                    + "condition time interval and the effect time interval are different, "
                    + "this is not supported by the UP."
                )
            if len(interval_res) > 0:
                raise UPProblemDefinitionError(
                    "A conditional effect can not have an interval specified before the when keyword."
                )
            condition = self._parse_expression(condition_exp_res, parameters, types_map)
            interval_res = condition_interval
        else:
            condition = self._em.TRUE()
            effect_exp = effect_res[0]
        up_interval = self._parse_interval(interval_res, types_map, is_global)
        fluent_ref = effect_exp[0]
        assignment_operator = effect_exp[1]
        assigned_expression = effect_exp[2]
        up_fluent = self._parse_expression(fluent_ref, parameters, types_map)
        assert (
            up_fluent.is_fluent_exp()
        ), "left side of the assignment is not a valid fluent"
        up_value = self._parse_expression(assigned_expression, parameters, types_map)
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
        assert isinstance(
            up_interval, Timing
        ), "An effect with a durative interval is not supported"
        return (up_interval, Effect(up_fluent, up_value, condition, kind=kind))

    def _parse_expression(
        self,
        expression: Union[ParseResults, List, str],
        parameters: Dict[str, "up.model.Parameter"],
        types_map: Dict[str, "Type"],
    ) -> "up.model.FNode":
        # A string here means it is a number or a boolean token. To avoid code duplication, just
        # wrap it in a temporary list and let the stack management handle it.
        if isinstance(expression, str):
            expression = [expression]
        stack: List[Tuple[Union[ParseResults, List], bool, Dict[str, "Variable"]]] = [
            (expression, False, {})
        ]
        solved: List[FNode] = []
        while 1:
            try:
                exp, already_expanded, vars = stack.pop()
            except IndexError:
                break
            if already_expanded:
                assert isinstance(exp, ParseResults) or isinstance(exp, List)
                if len(exp) <= 1:
                    assert len(exp) == 1, "algorithm error"
                    pass
                elif len(exp) == 2:
                    first_elem = exp[0]
                    if isinstance(first_elem, List) or isinstance(
                        first_elem, ParseResults
                    ):  # parameters list
                        second_elem = exp[1]
                        assert isinstance(second_elem, List) or isinstance(
                            second_elem, ParseResults
                        )
                        pass
                    elif first_elem == TK_MINUS:  # unary minus
                        solved.append(self._em.Times(-1, solved.pop()))
                    elif first_elem == TK_PLUS:  # unary plus
                        pass  # already ok, nothing to do -> 0+x = x
                    elif first_elem == TK_NOT:  # negation
                        solved.append(self._em.Not(solved.pop()))
                    elif first_elem in vars:  # quantifier variable
                        solved.append(self._em.VariableExp(vars[first_elem]))
                    elif first_elem in parameters:  # parameter exp
                        solved.append(self._em.ParameterExp(parameters[first_elem]))
                    elif self._problem.has_fluent(first_elem):  # fluent exp
                        fluent = self._problem.fluent(first_elem)
                        fluent_args = tuple(solved.pop() for _ in range(fluent.arity))
                        solved.append(self._em.FluentExp(fluent, fluent_args))
                    elif self._problem.has_object(first_elem):  # object exp
                        solved.append(
                            self._em.ObjectExp(self._problem.object(first_elem))
                        )
                    else:
                        raise NotImplementedError(
                            f"Currently the UP does not support the expression {exp}"
                        )
                elif len(exp) == 3:  # binary operator or parameters list
                    first_token = exp[0]
                    if isinstance(first_token, str) and first_token in (
                        TK_FORALL,
                        TK_EXISTS,
                    ):
                        assert isinstance(exp, ParseResults)
                        quantified_expressions = [
                            solved.pop() for _ in exp["quantifier_body"]
                        ]
                        solved.append(
                            self._operators[first_token](
                                self._em.And(quantified_expressions), *vars.values()
                            )
                        )
                    else:
                        operator = exp[1]
                        if isinstance(operator, List):  # parameters list
                            assert isinstance(exp[0], List) and isinstance(exp[2], List)
                            pass
                        elif isinstance(operator, str):  # binary operator
                            # '==' needs special care, because in ANML it can both mean '==' or 'Iff',
                            # but in the UP those 2 cases are handled differently.
                            if operator == TK_EQUALS:
                                first_arg = solved.pop()
                                second_arg = solved.pop()
                                if first_arg.type.is_bool_type():
                                    solved.append(self._em.Iff(first_arg, second_arg))
                                else:
                                    solved.append(
                                        self._em.Equals(first_arg, second_arg)
                                    )
                            else:
                                func = self._operators.get(operator, None)
                                if func is not None:
                                    first_arg = solved.pop()
                                    second_arg = solved.pop()
                                    solved.append(func(first_arg, second_arg))
                                else:
                                    raise NotImplementedError(
                                        f"Currently the UP does not support the parsing of the {operator} operator."
                                    )
                        else:
                            raise NotImplementedError(
                                f"Currently the UP does not support the expression {exp}"
                            )
                else:  # expression longer than 3, must be a parameters list
                    for e in exp:
                        assert isinstance(e, List) or isinstance(
                            e, ParseResults
                        ), f"expression {exp} is expected to be a parameters list, but it's not"
                        pass
            else:  # not solved
                if isinstance(exp, ParseResults) or isinstance(exp, List):
                    first_token = exp[0]
                    if isinstance(first_token, str) and first_token in (
                        TK_FORALL,
                        TK_EXISTS,
                    ):  # quantifier
                        assert isinstance(exp, ParseResults)
                        name_type = self._parse_parameters_def(
                            exp["quantifier_variables"], types_map
                        )
                        new_vars = {n: Variable(n, t) for n, t in name_type.items()}
                        stack.append((exp, True, new_vars))
                        all_vars = vars.copy()
                        all_vars.update(new_vars)
                        for e in exp["quantifier_body"]:
                            stack.append((e, False, all_vars))
                    else:
                        stack.append((exp, True, vars))
                        for e in exp:
                            if not isinstance(e, str):  # nested structure
                                if len(e) > 0:
                                    stack.append((e, False, vars))
                            elif e.isnumeric():  # int
                                solved.append(self._em.Int(int(e)))
                            elif is_float(e):  # float
                                solved.append(self._em.Real(Fraction(float(e))))
                            elif e == TK_TRUE:  # true
                                solved.append(self._em.TRUE())
                            elif e == TK_FALSE:  # false
                                solved.append(self._em.FALSE())
                elif isinstance(exp, str):
                    assert False, "problem, should not have strings here"
                else:
                    raise NotImplementedError
        assert len(stack) == 0
        assert len(solved) == 1, f"{expression}"
        res = solved.pop()
        return res.simplify()


def is_float(string: str) -> bool:
    try:
        float(string)
        return True
    except ValueError:
        return False


def count_instances(
    result: Union[ParseResults, List], strings: Set[str]
) -> Dict[str, int]:
    stack: List[Union[ParseResults, List]] = [result]
    counters: Dict[str, int] = {s: 0 for s in strings}
    while 1:
        try:
            res = stack.pop()
        except IndexError:
            break
        for word in res:
            if isinstance(word, ParseResults) or isinstance(word, List):
                stack.append(word)
            else:
                assert isinstance(word, str)
                count_s = counters.get(word, None)
                if count_s is not None:
                    counters[word] = count_s + 1
    return counters
