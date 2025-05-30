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
# type: ignore
from functools import partial
from typing import Tuple, Union, Optional
import fractions
from typing import OrderedDict

import unified_planning.grpc.generated.unified_planning_pb2 as proto
from unified_planning.exceptions import UPException
from unified_planning import Environment
from unified_planning import model
from unified_planning.model import metrics, TimePointInterval, GlobalEndTiming
import unified_planning.plans
from unified_planning.grpc.converter import Converter, handles
from unified_planning.model import (
    DurativeAction,
    Effect,
    InstantaneousAction,
    Parameter,
    Problem,
    Variable,
)
from unified_planning.model.effect import EffectKind
from unified_planning.model.operators import OperatorKind
from unified_planning.plans import ActionInstance
from unified_planning.plans.hierarchical_plan import MethodInstance, Decomposition
from unified_planning.model.htn.hierarchical_problem import HierarchicalProblem


def convert_type_str(s: str, problem: Problem) -> model.types.Type:
    if s == "up:bool":
        return problem.environment.type_manager.BoolType()
    elif s == "up:integer":
        return problem.environment.type_manager.IntType()
    elif "up:integer[" in s:
        str_lb = s.split("[")[1].split(",")[0]
        lb = None if "-inf" in str_lb else int(str_lb)
        str_ub = s.split(",")[1].split("]")[0]
        ub = None if "inf" in str_ub else int(str_ub)
        return problem.environment.type_manager.IntType(lb, ub)
    elif s == "up:real":
        return problem.environment.type_manager.RealType()
    elif "up:real[" in s:
        return problem.environment.type_manager.RealType(
            lower_bound=fractions.Fraction(s.split("[")[1].split(",")[0]),
            upper_bound=fractions.Fraction(s.split(",")[1].split("]")[0]),
        )
    else:
        assert not s.startswith("up:"), f"Unhandled builtin type: {s}"
        return problem.user_type(s)


# The operators are based on SExpressions supported in PDDL.
def op_to_node_type(op: str) -> OperatorKind:
    if op == "up:plus":
        return OperatorKind.PLUS
    elif op == "up:minus":
        return OperatorKind.MINUS
    elif op == "up:times":
        return OperatorKind.TIMES
    elif op == "up:div":
        return OperatorKind.DIV
    elif op == "up:equals":
        return OperatorKind.EQUALS
    elif op == "up:le":
        return OperatorKind.LE
    elif op == "up:lt":
        return OperatorKind.LT
    elif op == "up:and":
        return OperatorKind.AND
    elif op == "up:or":
        return OperatorKind.OR
    elif op == "up:not":
        return OperatorKind.NOT
    elif op == "up:exists":
        return OperatorKind.EXISTS
    elif op == "up:forall":
        return OperatorKind.FORALL
    elif op == "up:implies":
        return OperatorKind.IMPLIES
    elif op == "up:iff":
        return OperatorKind.IFF
    elif op == "up:always":
        return OperatorKind.ALWAYS
    elif op == "up:at_most_once":
        return OperatorKind.AT_MOST_ONCE
    elif op == "up:sometime":
        return OperatorKind.SOMETIME
    elif op == "up:sometime_after":
        return OperatorKind.SOMETIME_AFTER
    elif op == "up:sometime_before":
        return OperatorKind.SOMETIME_BEFORE
    elif op == "up:present":
        return OperatorKind.IS_PRESENT_EXP
    raise ValueError(f"Unknown operator `{op}`")


class ProtobufReader(Converter):
    """
    ProtobufReader: This class uses the convert method to take the protobuf representation of a
    unified_planning Problem and return the equivalent unified_planning Problem instance.
    """

    @handles(proto.Parameter)
    def _convert_parameter(
        self, msg: proto.Parameter, problem: Problem
    ) -> model.Parameter:
        return model.Parameter(
            msg.name, convert_type_str(msg.type, problem), problem.environment
        )

    @handles(proto.Fluent)
    def _convert_fluent(self, msg: proto.Fluent, problem: Problem) -> model.Fluent:
        value_type: model.types.Type = convert_type_str(msg.value_type, problem)
        sig: list = []
        for p in msg.parameters:
            sig.append(self.convert(p, problem))
        fluent = model.Fluent(msg.name, value_type, sig, problem.environment)
        return fluent

    @handles(proto.ObjectDeclaration)
    def _convert_object(
        self, msg: proto.ObjectDeclaration, problem: Problem
    ) -> model.Object:
        return model.Object(msg.name, convert_type_str(msg.type, problem))

    @handles(proto.Expression)
    def _convert_expression(
        self, msg: proto.Expression, problem: Problem
    ) -> model.Expression:
        if msg.kind == proto.ExpressionKind.Value("CONSTANT"):
            assert msg.atom is not None
            return self.convert(msg.atom, problem)

        elif msg.kind == proto.ExpressionKind.Value("PARAMETER"):
            return problem.environment.expression_manager.ParameterExp(
                param=Parameter(
                    msg.atom.symbol,
                    convert_type_str(msg.type, problem),
                    problem.environment,
                ),
            )
        elif msg.kind == proto.ExpressionKind.Value("VARIABLE"):
            return problem.environment.expression_manager.VariableExp(
                var=Variable(
                    msg.atom.symbol,
                    convert_type_str(msg.type, problem),
                    problem.environment,
                ),
            )
        elif msg.kind == proto.ExpressionKind.Value("STATE_VARIABLE"):
            args = []
            payload = None

            fluent = msg.list.pop(0)
            if fluent.kind == proto.ExpressionKind.Value("FLUENT_SYMBOL"):
                payload = self.convert(fluent.atom, problem)

            args.extend([self.convert(m, problem) for m in msg.list])
            if payload is not None:
                return problem.environment.expression_manager.FluentExp(
                    payload, tuple(args)
                )
            else:
                raise UPException(f"Unable to form fluent expression {msg}")
        elif (
            msg.kind == proto.ExpressionKind.Value("FUNCTION_APPLICATION")
            and msg.list[0].atom.symbol == "up:present"
        ):
            container = msg.list[1].atom.symbol
            presence = model.Presence(container)
            return problem.environment.expression_manager.PresentExp(presence)
        elif (
            msg.kind == proto.ExpressionKind.Value("FUNCTION_APPLICATION")
            and msg.type != "up:time"
        ):
            node_type = None
            args = []
            payload = None

            symbol = msg.list.pop(0)
            if symbol.kind == proto.ExpressionKind.Value("FUNCTION_SYMBOL"):
                node_type = op_to_node_type(symbol.atom.symbol)

            if node_type in [OperatorKind.EXISTS, OperatorKind.FORALL]:
                variables = msg.list[:-1]
                quantified_expression = msg.list[-1]
                args.append(self.convert(quantified_expression, problem))
                payload = tuple(
                    [self.convert(var, problem).variable() for var in variables]
                )
            elif node_type == OperatorKind.IS_PRESENT_EXP:
                print(msg)
                container = msg.list[1].atom.symbol
                print(container)
                assert False
            else:
                print("-----------------")
                print(msg)
                print("-----------------")
                args.extend([self.convert(m, problem) for m in msg.list])

            assert node_type is not None

            return problem.environment.expression_manager.create_node(
                node_type=node_type,
                args=tuple(args),
                payload=payload,
            )
        elif (
            msg.kind == proto.ExpressionKind.Value("FUNCTION_APPLICATION")
            and msg.type == "up:time"
        ):
            if (
                len(msg.list) == 3
            ):  # Expect something of the form (up:plus (QUALIFIER [CONTAINER]) DELAY)
                assert (
                    msg.list[0].atom.symbol == "up:plus"
                ), f"Unexpected expression {msg.list[0].atom.symbol}"
                if msg.list[2].type == "up:integer":
                    dl = int(msg.list[2].atom.int)
                elif msg.list[2].type == "up:real":
                    dl = self.convert(msg.list[2].atom.real)
                else:
                    raise ValueError(f"Invalid delay type {msg.list[2].type}")
                timepoint_expr = msg.list[1].list
            else:  # Expects a single timepoint of the form (QUALIFIER [CONTAINER])
                dl = 0
                timepoint_expr = msg.list

            fn = timepoint_expr[0].atom.symbol
            if fn == "up:start":
                kd = model.TimepointKind.START
            elif fn == "up:end":
                kd = model.TimepointKind.END
            elif fn == "up:global_start":
                kd = model.TimepointKind.GLOBAL_START
            elif fn == "up:global_end":
                kd = model.TimepointKind.GLOBAL_END
            else:
                raise ValueError(f"Invalid temporal qualifier {fn}")
            container = None
            if len(timepoint_expr) > 1:
                container = timepoint_expr[1].atom.symbol
            tp = model.timing.Timepoint(kd, container)
            return problem.environment.expression_manager.TimingExp(
                model.Timing(dl, tp)
            )

        raise ValueError(f"Unknown expression kind `{msg.kind}`")

    @handles(proto.Atom)
    def _convert_atom(
        self, msg: proto.Atom, problem: Problem
    ) -> Union[model.FNode, model.Fluent, model.Object]:
        field = msg.WhichOneof("content")

        value = getattr(msg, field)
        if field == "int":
            return problem.environment.expression_manager.Int(value)
        elif field == "real":
            return problem.environment.expression_manager.Real(
                fractions.Fraction(value.numerator, value.denominator)
            )
        elif field == "boolean":
            return problem.environment.expression_manager.Bool(value)
        else:
            # If atom symbols, return the equivalent UP alternative
            # Note that parameters are directly handled at expression level
            if problem.has_object(value):
                return problem.environment.expression_manager.ObjectExp(
                    obj=problem.object(value)
                )
            else:
                return problem.fluent(value)

    @handles(proto.TypeDeclaration)
    def _convert_type_declaration(
        self, msg: proto.TypeDeclaration, problem: Problem
    ) -> model.Type:
        if msg.type_name == "up:bool":
            return problem.environment.type_manager.BoolType()
        elif msg.type_name.startswith("up:integer["):
            tmp = msg.type_name.split("[")[1].split("]")[0].split(", ")
            return problem.environment.type_manager.IntType(
                lower_bound=int(tmp[0]) if tmp[0] != "-inf" else None,
                upper_bound=int(tmp[1]) if tmp[1] != "inf" else None,
            )
        elif msg.type_name.startswith("up:real["):
            tmp = msg.type_name.split("[")[1].split("]")[0].split(", ")
            lower_bound = fractions.Fraction(tmp[0]) if tmp[0] != "-inf" else None
            upper_bound = fractions.Fraction(tmp[1]) if tmp[1] != "inf" else None
            return problem.environment.type_manager.RealType(
                lower_bound=lower_bound, upper_bound=upper_bound
            )
        else:
            father = (
                problem.user_type(msg.parent_type) if msg.parent_type != "" else None
            )
            return problem.environment.type_manager.UserType(
                name=msg.type_name, father=father
            )

    @handles(proto.Problem)
    def _convert_problem(
        self, msg: proto.Problem, environment: Optional[Environment] = None
    ) -> model.AbstractProblem:
        if msg.HasField("scheduling_extension"):
            return self._convert_scheduling_problem(msg, environment)
        problem_name = str(msg.problem_name) if str(msg.problem_name) != "" else None
        if msg.HasField("hierarchy"):
            problem = model.htn.HierarchicalProblem(
                name=problem_name, environment=environment
            )
        else:
            problem = Problem(name=problem_name, environment=environment)

        for t in msg.types:
            problem._add_user_type(self.convert(t, problem))
        for obj in msg.objects:
            problem.add_object(self.convert(obj, problem))
        for f in msg.fluents:
            problem.add_fluent(
                self.convert(f, problem),
                default_initial_value=self.convert(f.default_value, problem)
                if f.HasField("default_value")
                else None,
            )
        for f in msg.actions:
            problem.add_action(self.convert(f, problem))
        for eff in msg.timed_effects:
            ot = self.convert(eff.occurrence_time, problem)
            effect = self.convert(eff.effect, problem)
            problem._add_effect_instance(ot, effect)

        for assign in msg.initial_state:
            problem.set_initial_value(
                fluent=self.convert(assign.fluent, problem),
                value=self.convert(assign.value, problem),
            )

        for g in msg.goals:
            goal = self.convert(g.goal, problem)
            if not g.HasField("timing"):
                problem.add_goal(goal)
            else:
                timing = self.convert(g.timing)
                problem.add_timed_goal(interval=timing, goal=goal)

        for tc in msg.trajectory_constraints:
            problem.add_trajectory_constraint(self.convert(tc, problem))

        for metric in msg.metrics:
            problem.add_quality_metric(self.convert(metric, problem))

        if msg.HasField("hierarchy"):
            for task in msg.hierarchy.abstract_tasks:
                problem.add_task(self.convert(task, problem))
            for method in msg.hierarchy.methods:
                problem.add_method(self.convert(method, problem))
            problem._initial_task_network = self.convert(
                msg.hierarchy.initial_task_network, problem
            )

        problem.discrete_time = msg.discrete_time
        problem.self_overlapping = msg.self_overlapping
        if msg.HasField("epsilon"):
            problem.epsilon = self.convert(msg.epsilon)

        return problem

    def _convert_scheduling_problem(
        self, msg: proto.Problem, environment: Optional[Environment] = None
    ) -> model.scheduling.SchedulingProblem:
        problem_name = str(msg.problem_name) if str(msg.problem_name) != "" else None
        problem = model.scheduling.SchedulingProblem(
            name=problem_name, environment=environment
        )

        for t in msg.types:
            problem._add_user_type(self.convert(t, problem))
        for obj in msg.objects:
            problem.add_object(self.convert(obj, problem))
        for f in msg.fluents:
            problem.add_fluent(
                self.convert(f, problem),
                default_initial_value=self.convert(f.default_value, problem)
                if f.HasField("default_value")
                else None,
            )
        for eff in msg.timed_effects:
            ot = self.convert(eff.occurrence_time, problem)
            effect = self.convert(eff.effect, problem)
            problem._base._add_effect_instance(timing=ot, effect=effect)
        for assign in msg.initial_state:
            problem.set_initial_value(
                fluent=self.convert(assign.fluent, problem),
                value=self.convert(assign.value, problem),
            )

        for g in msg.goals:
            goal = self.convert(g.goal, problem)
            if not g.HasField("timing"):
                problem.add_condition(TimePointInterval(GlobalEndTiming()), goal)
            else:
                timing = self.convert(g.timing)
                problem.add_condition(self.convert(timing), goal)

        for sc in msg.scheduling_extension.scoped_constraints:  # TODO: scoped
            c = self.convert(sc.constraint, problem)
            print(">>>>> ", sc.scope)
            scope = [self.convert(sc_item, problem) for sc_item in sc.scope]
            print("<<<<<")

            problem.add_constraint(c, scope)

        assert len(msg.trajectory_constraints) == 0

        for metric in msg.metrics:
            problem.add_quality_metric(self.convert(metric, problem))

        assert not msg.HasField("hierarchy")
        ext = msg.scheduling_extension
        for pa in ext.activities:
            a = problem.add_activity(pa.name)
            a._set_duration_constraint(self._convert_duration(pa.duration, problem))
            for p in pa.parameters:
                prefix = pa.name + "."
                assert p.name.startswith(prefix)
                name = p.name[len(prefix) :]  # remove prefix
                a.add_parameter(name, convert_type_str(p.type, problem))
            for cond in pa.conditions:
                a.add_condition(
                    self.convert(cond.span, problem), self.convert(cond.cond, problem)
                )
            for eff in pa.effects:
                timing = self._convert_timing(eff.occurrence_time)
                effect = self._convert_effect(eff.effect, problem)
                a._add_effect_instance(timing, effect)
            for c in pa.constraints:
                a.add_constraint(self.convert(c, problem))

        problem.discrete_time = msg.discrete_time
        problem.self_overlapping = msg.self_overlapping
        if msg.HasField("epsilon"):
            problem.epsilon = self.convert(msg.epsilon)

        return problem

    @handles(proto.AbstractTaskDeclaration)
    def _convert_abstract_task(
        self, msg: proto.AbstractTaskDeclaration, problem: Problem
    ):
        return model.htn.Task(
            msg.name,
            [self.convert(p, problem) for p in msg.parameters],
            problem.environment,
        )

    @handles(proto.Task)
    def _convert_task(
        self, msg: proto.Task, problem: model.htn.HierarchicalProblem
    ) -> model.htn.Subtask:
        if problem.has_task(msg.task_name):
            task = problem.get_task(msg.task_name)
        elif problem.has_action(msg.task_name):
            task = problem.action(msg.task_name)
        else:
            raise ValueError(f"Unknown task name: {msg.task_name}")
        parameters = [self.convert(p, problem) for p in msg.parameters]
        return model.htn.Subtask(
            task, *parameters, ident=msg.id, _env=problem.environment
        )

    @handles(proto.Method)
    def _convert_method(
        self, msg: proto.Method, problem: model.htn.HierarchicalProblem
    ) -> model.htn.Method:
        method = model.htn.Method(
            msg.name,
            [self.convert(p, problem) for p in msg.parameters],
            problem.environment,
        )
        achieved_task_params = []
        for p in msg.achieved_task.parameters:
            achieved_task_params.append(method.parameter(p.atom.symbol))
        method.set_task(
            problem.get_task(msg.achieved_task.task_name), *achieved_task_params
        )
        for st in msg.subtasks:
            method.add_subtask(self.convert(st, problem))
        for c in msg.constraints:
            method.add_constraint(self.convert(c, problem))
        for c in msg.conditions:
            assert not c.HasField("span"), "Timed conditions are currently unsupported."
            method.add_precondition(self.convert(c.cond, problem))
        return method

    @handles(proto.TaskNetwork)
    def _convert_task_network(
        self, msg: proto.TaskNetwork, problem: model.htn.HierarchicalProblem
    ) -> model.htn.TaskNetwork:
        tn = model.htn.TaskNetwork(problem.environment)
        for v in msg.variables:
            tn.add_variable(v.name, convert_type_str(v.type, problem))
        for st in msg.subtasks:
            tn.add_subtask(self.convert(st, problem))
        for c in msg.constraints:
            tn.add_constraint(self.convert(c, problem))

        return tn

    @handles(proto.Metric)
    def _convert_metric(
        self, msg: proto.Metric, problem: Problem
    ) -> Union[
        metrics.MinimizeActionCosts,
        metrics.MinimizeSequentialPlanLength,
        metrics.MinimizeMakespan,
        metrics.MinimizeExpressionOnFinalState,
        metrics.MaximizeExpressionOnFinalState,
        metrics.Oversubscription,
        metrics.TemporalOversubscription,
    ]:
        if msg.kind == proto.Metric.MINIMIZE_ACTION_COSTS:
            costs = {}
            for a, cost in msg.action_costs.items():
                costs[problem.action(a)] = self.convert(cost, problem)
            return metrics.MinimizeActionCosts(
                costs=costs,
                default=self.convert(msg.default_action_cost, problem)
                if msg.HasField("default_action_cost")
                else None,
            )

        elif msg.kind == proto.Metric.MINIMIZE_SEQUENTIAL_PLAN_LENGTH:
            return metrics.MinimizeSequentialPlanLength()

        elif msg.kind == proto.Metric.MINIMIZE_MAKESPAN:
            return metrics.MinimizeMakespan()

        elif msg.kind == proto.Metric.MINIMIZE_EXPRESSION_ON_FINAL_STATE:
            return metrics.MinimizeExpressionOnFinalState(
                expression=self.convert(msg.expression, problem)
            )

        elif msg.kind == proto.Metric.MAXIMIZE_EXPRESSION_ON_FINAL_STATE:
            return metrics.MaximizeExpressionOnFinalState(
                expression=self.convert(msg.expression, problem)
            )
        elif msg.kind == proto.Metric.OVERSUBSCRIPTION:
            goals = {}
            for g in msg.goals:
                goals[self.convert(g.goal, problem)] = self.convert(g.weight)
            return metrics.Oversubscription(goals)
        elif msg.kind == proto.Metric.TEMPORAL_OVERSUBSCRIPTION:
            timed_goals = {}
            for g in msg.timed_goals:
                timed_goals[
                    (self.convert(g.timing, problem), self.convert(g.goal, problem))
                ] = self.convert(g.weight)
            return metrics.TemporalOversubscription(timed_goals)
        else:
            raise UPException(f"Unknown metric kind `{msg.kind}`")

    @handles(proto.Action)
    def _convert_action(self, msg: proto.Action, problem: Problem) -> model.Action:
        action: model.Action

        parameters = OrderedDict()
        for param in msg.parameters:
            parameters[param.name] = convert_type_str(param.type, problem)

        if msg.HasField("duration"):
            action = DurativeAction(msg.name, parameters)
            action.set_duration_constraint(self.convert(msg.duration, problem))
        else:
            action = InstantaneousAction(msg.name, parameters)

        conditions = []
        for condition in msg.conditions:
            cond = self.convert(condition.cond, problem)
            span = self.convert(condition.span) if condition.HasField("span") else None
            conditions.append((cond, span))

        effects = []
        for effect in msg.effects:
            eff = self.convert(effect.effect, problem)
            time = (
                self.convert(effect.occurrence_time)
                if effect.HasField("occurrence_time")
                else None
            )
            effects.append((eff, time))

        if isinstance(action, DurativeAction):
            for c, span in conditions:
                action.add_condition(span, c)
            for e, ot in effects:
                if e.kind == EffectKind.ASSIGN:
                    action.add_effect(ot, e.fluent, e.value, e.condition, e.forall)
                elif e.kind == EffectKind.DECREASE:
                    action.add_decrease_effect(
                        ot, e.fluent, e.value, e.condition, e.forall
                    )
                elif e.kind == EffectKind.INCREASE:
                    action.add_increase_effect(
                        ot, e.fluent, e.value, e.condition, e.forall
                    )
        elif isinstance(action, InstantaneousAction):
            for c, _ in conditions:
                action.add_precondition(c)
            for e, _ in effects:
                if e.kind == EffectKind.ASSIGN:
                    action.add_effect(e.fluent, e.value, e.condition, e.forall)
                elif e.kind == EffectKind.DECREASE:
                    action.add_decrease_effect(e.fluent, e.value, e.condition, e.forall)
                elif e.kind == EffectKind.INCREASE:
                    action.add_increase_effect(e.fluent, e.value, e.condition, e.forall)

        return action

    @handles(proto.EffectExpression)
    def _convert_effect(
        self, msg: proto.EffectExpression, problem: Problem
    ) -> model.Effect:
        # EffectKind
        if msg.kind == proto.EffectExpression.EffectKind.Value("INCREASE"):
            kind = EffectKind.INCREASE
        elif msg.kind == proto.EffectExpression.EffectKind.Value("DECREASE"):
            kind = EffectKind.DECREASE
        else:
            kind = EffectKind.ASSIGN

        return Effect(
            fluent=self.convert(msg.fluent, problem),
            value=self.convert(msg.value, problem),
            condition=self.convert(msg.condition, problem),
            kind=kind,
            forall=(self.convert(var, problem).variable() for var in msg.forall),
        )

    @handles(proto.Duration)
    def _convert_duration(
        self, msg: proto.Duration, problem: Problem
    ) -> model.timing.DurationInterval:
        return model.timing.DurationInterval(
            lower=self.convert(msg.controllable_in_bounds.lower, problem),
            upper=self.convert(msg.controllable_in_bounds.upper, problem),
            is_left_open=bool(msg.controllable_in_bounds.is_left_open),
            is_right_open=bool(msg.controllable_in_bounds.is_right_open),
        )

    @handles(proto.TimeInterval)
    def _convert_timed_interval(
        self, msg: proto.TimeInterval, _problem: Optional[Problem] = None
    ) -> model.TimeInterval:
        return model.TimeInterval(
            lower=self.convert(msg.lower),
            upper=self.convert(msg.upper),
            is_left_open=msg.is_left_open,
            is_right_open=msg.is_right_open,
        )

    @handles(proto.Timing)
    def _convert_timing(
        self, msg: proto.Timing, _problem: Optional[Problem] = None
    ) -> model.timing.Timing:
        return model.Timing(
            delay=self.convert(msg.delay)
            if msg.HasField("delay")
            else fractions.Fraction(0),
            timepoint=self.convert(msg.timepoint),
        )

    @handles(proto.Real)
    def _convert_real(self, msg: proto.Real) -> fractions.Fraction:
        return fractions.Fraction(msg.numerator, msg.denominator)

    @handles(proto.Timepoint)
    def _convert_timepoint(self, msg: proto.Timepoint) -> model.timing.Timepoint:
        if msg.kind == proto.Timepoint.TimepointKind.Value("GLOBAL_START"):
            kind = model.timing.TimepointKind.GLOBAL_START
        elif msg.kind == proto.Timepoint.TimepointKind.Value("GLOBAL_END"):
            kind = model.timing.TimepointKind.GLOBAL_END
        elif msg.kind == proto.Timepoint.TimepointKind.Value("START"):
            kind = model.timing.TimepointKind.START
        elif msg.kind == proto.Timepoint.TimepointKind.Value("END"):
            kind = model.timing.TimepointKind.END
        else:
            raise UPException("Unknown timepoint kind: {}".format(msg.kind))
        container = msg.container_id if msg.container_id != "" else None
        return model.timing.Timepoint(kind, container)

    @handles(proto.Plan)
    def _convert_plan(
        self, msg: proto.Plan, problem: Problem
    ) -> unified_planning.plans.Plan:
        if msg.HasField("schedule"):
            assert not msg.HasField("hierarchy")
            assert len(msg.actions) == 0
            return self._convert_schedule(msg.schedule, problem)
        actions = [self._convert_action_instance(a, problem) for a in msg.actions]
        if all(a[2] is not None for a in actions):
            # If all actions have temporal term, we can assume that they are
            # (id, action, (absolute start time, duration))
            time_triggered_actions = [
                (start, action, duration) for _, action, (start, duration) in actions
            ]
            flat_plan = unified_planning.plans.TimeTriggeredPlan(time_triggered_actions)
        else:
            # Otherwise, we assume they are a sequence of actions (id, action, None)
            action_sequence = [action for _, action, _ in actions]
            flat_plan = unified_planning.plans.SequentialPlan(actions=action_sequence)

        if msg.HasField("hierarchy"):
            assert isinstance(problem, HierarchicalProblem)
            # map each action/method ID with the correcponding instance
            instances = {id: action for id, action, _ in actions}

            # return the Action/Method with the given id
            # this recursively build any needed instance.
            def instance_with_id(id: str) -> Union[ActionInstance, MethodInstance]:
                if id not in instances:
                    proto_method = next(
                        filter(lambda m: m.id == id, msg.hierarchy.methods)
                    )
                    method = problem.method(proto_method.method_name)
                    parameters = tuple(
                        [
                            self._convert_atom(param, problem)
                            for param in proto_method.parameters
                        ]
                    )
                    subtasks = {
                        id: instance_with_id(impl)
                        for id, impl in proto_method.subtasks.items()
                    }
                    instance = MethodInstance(
                        method, parameters, Decomposition(subtasks)
                    )
                    instances[id] = instance
                return instances[id]

            decomposition = Decomposition(
                {
                    id: instance_with_id(impl)
                    for id, impl in msg.hierarchy.root_tasks.items()
                }
            )

            return unified_planning.plans.HierarchicalPlan(flat_plan, decomposition)

        else:
            return flat_plan

    @handles(proto.ActionInstance)
    def _convert_action_instance(
        self, msg: proto.ActionInstance, problem: Problem
    ) -> Tuple[
        str,
        ActionInstance,
        Optional[Tuple[fractions.Fraction, Optional[fractions.Fraction]]],
    ]:
        # action instance parameters are atoms but in UP they are FNodes
        # converting to up.model.FNode
        parameters = tuple([self.convert(param, problem) for param in msg.parameters])

        id = msg.id
        action_instance = unified_planning.plans.ActionInstance(
            problem.action(msg.action_name),
            parameters,
        )

        if msg.HasField("start_time") and msg.HasField("end_time"):
            start_time = self.convert(msg.start_time)
            end_time = self.convert(msg.end_time)
            duration = end_time - start_time
            return (
                id,
                action_instance,
                (start_time, None if duration == 0 else duration),
            )
        else:
            return id, action_instance, None

    def _convert_schedule(
        self, msg: proto.Schedule, problem: model.scheduling.SchedulingProblem
    ) -> unified_planning.plans.Schedule:
        activities = [problem.get_activity(act_name) for act_name in msg.activities]
        assignment = {}
        for var, val in msg.variable_assignments.items():
            if "." in var:
                activity_name, parameter_name = var.split(".")
                activity = problem.get_activity(activity_name)
                if parameter_name == "start":
                    param = activity.start
                elif parameter_name == "end":
                    param = activity.end
                else:
                    param = activity.get_parameter(parameter_name)
            else:
                param = problem.get_variable(var)
            val = self._convert_atom(val, problem)
            assignment[param] = val
        return unified_planning.plans.Schedule(
            assignment=assignment, activities=activities
        )

    @handles(proto.PlanGenerationResult)
    def _convert_plan_generation_result(
        self, result: proto.PlanGenerationResult, problem: Problem
    ) -> unified_planning.engines.PlanGenerationResult:
        if result.status == proto.PlanGenerationResult.Status.Value(
            "SOLVED_SATISFICING"
        ):
            status = (
                unified_planning.engines.results.PlanGenerationResultStatus.SOLVED_SATISFICING
            )
        elif result.status == proto.PlanGenerationResult.Status.Value(
            "SOLVED_OPTIMALLY"
        ):
            status = (
                unified_planning.engines.results.PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
        elif result.status == proto.PlanGenerationResult.Status.Value(
            "UNSOLVABLE_PROVEN"
        ):
            status = (
                unified_planning.engines.results.PlanGenerationResultStatus.UNSOLVABLE_PROVEN
            )
        elif result.status == proto.PlanGenerationResult.Status.Value(
            "UNSOLVABLE_INCOMPLETELY"
        ):
            status = (
                unified_planning.engines.results.PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY
            )
        elif result.status == proto.PlanGenerationResult.Status.Value("TIMEOUT"):
            status = unified_planning.engines.results.PlanGenerationResultStatus.TIMEOUT
        elif result.status == proto.PlanGenerationResult.Status.Value("MEMOUT"):
            status = unified_planning.engines.results.PlanGenerationResultStatus.MEMOUT
        elif result.status == proto.PlanGenerationResult.Status.Value("INTERNAL_ERROR"):
            status = (
                unified_planning.engines.results.PlanGenerationResultStatus.INTERNAL_ERROR
            )
        elif result.status == proto.PlanGenerationResult.Status.Value(
            "UNSUPPORTED_PROBLEM"
        ):
            status = (
                unified_planning.engines.results.PlanGenerationResultStatus.UNSUPPORTED_PROBLEM
            )
        elif result.status == proto.PlanGenerationResult.Status.Value("INTERMEDIATE"):
            status = (
                unified_planning.engines.results.PlanGenerationResultStatus.INTERMEDIATE
            )
        else:
            raise UPException(f"Unknown Planner Status: {result.status}")

        log_messages = None
        engine_metrics = None

        if bool(result.metrics):
            engine_metrics = dict(result.metrics)

        if len(result.log_messages) > 0:
            log_messages = [self.convert(log) for log in result.log_messages]

        return unified_planning.engines.PlanGenerationResult(
            status=status,
            plan=self.convert(result.plan, problem)
            if result.HasField("plan")
            else None,
            engine_name=result.engine.name,
            metrics=engine_metrics,
            log_messages=log_messages,
        )

    @handles(proto.LogMessage)
    def _convert_log_message(
        self, log: proto.LogMessage
    ) -> unified_planning.engines.LogMessage:
        if log.level == proto.LogMessage.LogLevel.Value("INFO"):
            return unified_planning.engines.LogMessage(
                level=unified_planning.engines.LogLevel.INFO,
                message=log.message,
            )
        elif log.level == proto.LogMessage.LogLevel.Value("WARNING"):
            return unified_planning.engines.LogMessage(
                level=unified_planning.engines.LogLevel.WARNING,
                message=log.message,
            )
        elif log.level == proto.LogMessage.LogLevel.Value("ERROR"):
            return unified_planning.engines.LogMessage(
                level=unified_planning.engines.LogLevel.ERROR,
                message=log.message,
            )
        elif log.level == proto.LogMessage.LogLevel.Value("DEBUG"):
            return unified_planning.engines.LogMessage(
                level=unified_planning.engines.LogLevel.DEBUG,
                message=log.message,
            )
        else:
            raise UPException(f"Unexpected Log Level: {log.level}")

    @handles(proto.CompilerResult)
    def _convert_compiler_result(
        self,
        result: proto.CompilerResult,
        lifted_problem: unified_planning.model.Problem,
    ) -> unified_planning.engines.CompilerResult:
        problem = self.convert(result.problem, lifted_problem.environment)
        map: Dict[
            unified_planning.model.Action,
            Tuple[unified_planning.model.Action, List[unified_planning.model.FNode]],
        ] = {}
        for grounded_action in problem.actions:
            original_action_instance = self.convert(
                result.map_back_plan[grounded_action.name], lifted_problem
            )[1]
            map[grounded_action] = (
                original_action_instance.action,
                original_action_instance.actual_parameters,
            )
        engine_metrics = None
        if bool(result.metrics):
            engine_metrics = dict(result.metrics)
        return unified_planning.engines.CompilerResult(
            problem=problem,
            map_back_action_instance=partial(
                unified_planning.engines.compilers.utils.lift_action_instance, map=map
            ),
            engine_name=result.engine.name,
            metrics=engine_metrics,
            log_messages=[self.convert(log) for log in result.log_messages],
        )

    @handles(proto.ValidationResult)
    def _convert_validation_result(
        self, result: proto.ValidationResult
    ) -> unified_planning.engines.ValidationResult:
        if result.status == proto.ValidationResult.ValidationResultStatus.Value(
            "VALID"
        ):
            r_status = unified_planning.engines.ValidationResultStatus.VALID
        elif result.status == proto.ValidationResult.ValidationResultStatus.Value(
            "INVALID"
        ):
            r_status = unified_planning.engines.ValidationResultStatus.INVALID
        elif result.status == proto.ValidationResult.ValidationResultStatus.Value(
            "UNKNOWN"
        ):
            r_status = unified_planning.engines.ValidationResultStatus.UNKNOWN
        else:
            raise UPException(f"Unexpected ValidationResult status: {result.status}")
        engine_metrics = None
        if bool(result.metrics):
            engine_metrics = dict(result.metrics)
        return unified_planning.engines.ValidationResult(
            status=r_status,
            engine_name=result.engine.name,
            metrics=engine_metrics,
            log_messages=[self.convert(log) for log in result.log_messages],
        )
