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
# type: ignore[valid-type]
import fractions
from itertools import product
from typing import List

import unified_planning.grpc.generated.unified_planning_pb2 as proto
from unified_planning import model
import unified_planning.model.htn
import unified_planning.model.walkers as walkers
from unified_planning.model.types import domain_size, domain_item
from unified_planning.exceptions import UPException
from unified_planning.grpc.converter import Converter, handles
from unified_planning.model.operators import (
    BOOL_OPERATORS,
    IRA_OPERATORS,
    RELATIONS,
    OperatorKind,
)
from unified_planning.model.timing import TimepointKind


def map_operator(op: int) -> str:
    if op == OperatorKind.PLUS:
        return "up:plus"
    elif op == OperatorKind.MINUS:
        return "up:minus"
    elif op == OperatorKind.TIMES:
        return "up:times"
    elif op == OperatorKind.DIV:
        return "up:div"
    elif op == OperatorKind.LE:
        return "up:le"
    elif op == OperatorKind.LT:
        return "up:lt"
    elif op == OperatorKind.EQUALS:
        return "up:equals"
    elif op == OperatorKind.AND:
        return "up:and"
    elif op == OperatorKind.OR:
        return "up:or"
    elif op == OperatorKind.NOT:
        return "up:not"
    elif op == OperatorKind.IMPLIES:
        return "up:implies"
    elif op == OperatorKind.IFF:
        return "up:iff"
    elif op == OperatorKind.EXISTS:
        return "up:exists"
    elif op == OperatorKind.FORALL:
        return "up:forall"
    raise ValueError(f"Unknown operator `{op}`")


def proto_type(tpe: model.Type) -> str:
    if tpe.is_bool_type():
        return "up:bool"
    elif tpe.is_time_type():
        return "up:time"
    elif tpe.is_int_type() or tpe.is_real_type():
        return f"up:{tpe}"
    elif isinstance(tpe, model.types._UserType):
        return str(tpe.name)


class FNode2Protobuf(walkers.DagWalker):
    def __init__(self, protobuf_writer):
        super().__init__()
        self._protobuf_writer = protobuf_writer

    def convert(self, expression: model.FNode) -> proto.Expression:
        return self.walk(expression)

    def walk_bool_constant(
        self, expression: model.FNode, args: List[proto.Expression]
    ) -> proto.Expression:
        return proto.Expression(
            atom=proto.Atom(boolean=expression.bool_constant_value()),
            list=[],
            kind=proto.ExpressionKind.Value("CONSTANT"),
            type="up:bool",
        )

    def walk_int_constant(
        self, expression: model.FNode, args: List[proto.Expression]
    ) -> proto.Expression:
        return proto.Expression(
            atom=proto.Atom(int=expression.int_constant_value()),
            list=[],
            kind=proto.ExpressionKind.Value("CONSTANT"),
            type="up:integer",
        )

    def walk_real_constant(
        self, expression: model.FNode, args: List[proto.Expression]
    ) -> proto.Expression:
        return proto.Expression(
            atom=proto.Atom(
                real=self._protobuf_writer.convert(expression.real_constant_value())
            ),
            list=[],
            kind=proto.ExpressionKind.Value("CONSTANT"),
            type="up:real",
        )

    def walk_param_exp(
        self, expression: model.FNode, args: List[proto.Expression]
    ) -> proto.Expression:
        return proto.Expression(
            atom=proto.Atom(symbol=expression.parameter().name),
            list=[],
            kind=proto.ExpressionKind.Value("PARAMETER"),
            type=proto_type(expression.parameter().type),
        )

    def walk_variable_exp(
        self, expression: model.FNode, args: List[proto.Expression]
    ) -> proto.Expression:
        return proto.Expression(
            atom=proto.Atom(symbol=expression.variable().name),
            list=[],
            kind=proto.ExpressionKind.Value("VARIABLE"),
            type=proto_type(expression.variable().type),
        )

    def walk_object_exp(
        self, expression: model.FNode, args: List[proto.Expression]
    ) -> proto.Expression:
        return proto.Expression(
            atom=proto.Atom(symbol=expression.object().name),
            list=[],
            kind=proto.ExpressionKind.Value("CONSTANT"),
            type=proto_type(expression.object().type),
        )

    def walk_timing_exp(
        self, expression: model.FNode, args: List[proto.Expression]
    ) -> proto.Expression:
        timing = expression.timing()
        tp = timing.timepoint
        if timing.timepoint.container is not None:
            args = [
                proto.Expression(
                    atom=proto.Atom(symbol=timing.timepoint.container),
                    type="up:container",
                    kind=proto.ExpressionKind.Value("CONTAINER_ID"),
                )
            ]
        else:
            args = []
        if tp.kind == TimepointKind.GLOBAL_START:
            fn = "up:global_start"
        elif tp.kind == TimepointKind.GLOBAL_END:
            fn = "up:global_end"
        elif tp.kind == TimepointKind.START:
            fn = "up:start"
        elif tp.kind == TimepointKind.END:
            fn = "up:end"
        else:
            raise ValueError(f"Unknown timepoint kind: {tp.kind}")
        fn_exp = proto.Expression(
            atom=proto.Atom(symbol=fn),
            kind=proto.ExpressionKind.Value("FUNCTION_SYMBOL"),
        )
        tp_exp = proto.Expression(
            list=[fn_exp] + args,
            type="up:time",
            kind=proto.ExpressionKind.Value("FUNCTION_APPLICATION"),
        )
        assert timing.delay == 0
        return tp_exp

    def walk_fluent_exp(
        self, expression: model.FNode, args: List[proto.Expression]
    ) -> proto.Expression:
        sub_list = []
        sub_list.append(
            proto.Expression(
                atom=proto.Atom(symbol=expression.fluent().name),
                kind=proto.ExpressionKind.Value("FLUENT_SYMBOL"),
                type=proto_type(expression.fluent().type),
            )
        )
        sub_list.extend(args)
        return proto.Expression(
            atom=None,
            list=sub_list,
            kind=proto.ExpressionKind.Value("STATE_VARIABLE"),
            type=proto_type(expression.fluent().type),
        )

    @walkers.handles(BOOL_OPERATORS.union(IRA_OPERATORS).union(RELATIONS))
    def walk_operator(
        self, expression: model.FNode, args: List[proto.Expression]
    ) -> proto.Expression:
        sub_list = []
        sub_list.append(
            proto.Expression(
                atom=proto.Atom(symbol=map_operator(expression.node_type)),
                list=[],
                kind=proto.ExpressionKind.Value("FUNCTION_SYMBOL"),
                type="up:operator",
            )
        )
        # forall/exists: add the declared variables from the payload to the beginning of the parameter list.
        if expression.is_exists() or expression.is_forall():
            sub_list.extend(
                [self._protobuf_writer.convert(p) for p in expression.variables()]
            )

        sub_list.extend(args)
        return proto.Expression(
            atom=None,
            list=sub_list,
            kind=proto.ExpressionKind.Value("FUNCTION_APPLICATION"),
            type="",
        )


def map_feature(feature: str) -> proto.Feature:
    pb_feature = proto.Feature.Value(feature)
    if pb_feature is None:
        raise ValueError(f"Cannot convert feature to protobuf {feature}")
    return pb_feature


class ProtobufWriter(Converter):
    """
    ProtoWriter: This class uses the convert method to take a unified_planning Problem instance
    and return the equivalent protobuf representation.
    """

    def __init__(self):
        super().__init__()
        self._fnode2proto = FNode2Protobuf(self)

    @handles(model.Fluent)
    def _convert_fluent(
        self, fluent: model.Fluent, problem: model.Problem
    ) -> proto.Fluent:
        name = fluent.name
        sig = [self.convert(t) for t in fluent.signature]
        return proto.Fluent(
            name=name,
            value_type=proto_type(fluent.type),
            parameters=sig,
            default_value=self.convert(problem.fluents_defaults[fluent])
            if fluent in problem.fluents_defaults
            else None,
        )

    @handles(model.Object)
    def _convert_object(self, obj: model.Object) -> proto.ObjectDeclaration:
        return proto.ObjectDeclaration(name=obj.name, type=proto_type(obj.type))

    @handles(model.FNode)
    def _convert_fnode(self, exp: model.FNode) -> proto.Expression:
        return self._fnode2proto.convert(exp)

    @handles(model.types._BoolType)
    def _convert_bool_type(self, tpe: model.types._BoolType) -> proto.TypeDeclaration:
        return proto.TypeDeclaration(type_name=proto_type(tpe))

    @handles(model.types._UserType)
    def _convert_user_type(self, t: model.types._UserType) -> proto.TypeDeclaration:
        return proto.TypeDeclaration(
            type_name=proto_type(t),
            parent_type="" if t.father is None else proto_type(t.father),
        )

    @handles(model.types._IntType)
    def _convert_integer_type(self, t: model.types._IntType) -> proto.TypeDeclaration:
        return proto.TypeDeclaration(type_name=proto_type(t))

    @handles(model.types._RealType)
    def _convert_real(self, t: model.types._RealType) -> proto.TypeDeclaration:
        return proto.TypeDeclaration(type_name=proto_type(t))

    @handles(model.Effect)
    def _convert_effect(self, effect: model.Effect) -> proto.Effect:
        kind = None
        if effect.is_assignment():
            kind = proto.EffectExpression.EffectKind.Value("ASSIGN")
        elif effect.is_increase():
            kind = proto.EffectExpression.EffectKind.Value("INCREASE")
        elif effect.is_decrease():
            kind = proto.EffectExpression.EffectKind.Value("DECREASE")
        else:
            raise ValueError(f"Unsupported effect: {effect}")

        return proto.EffectExpression(
            kind=kind,
            fluent=self.convert(effect.fluent),
            value=self.convert(effect.value),
            condition=self.convert(effect.condition),
        )

    @handles(model.InstantaneousAction)
    def _convert_instantaneous_action(
        self, a: model.InstantaneousAction
    ) -> proto.Action:
        effects = []
        conditions = []

        for cond in a.preconditions:
            conditions.append(
                proto.Condition(
                    cond=self.convert(cond),
                    span=None,
                )
            )

        for eff in a.effects:
            effects.append(proto.Effect(effect=self.convert(eff), occurrence_time=None))

        return proto.Action(
            name=a.name,
            parameters=[self.convert(p) for p in a.parameters],
            duration=None,
            conditions=conditions,
            effects=effects,
        )

    @handles(model.DurativeAction)
    def _convert_durative_action(self, a: model.DurativeAction) -> proto.Action:
        effects = []
        conditions = []

        for span, cond in a.conditions.items():
            span = self.convert(span)
            for c in cond:
                conditions.append(
                    proto.Condition(
                        cond=self.convert(c),
                        span=span,
                    )
                )
        for ot, eff in a.effects.items():
            ot = self.convert(ot)
            for e in eff:
                effects.append(
                    proto.Effect(
                        effect=self.convert(e),
                        occurrence_time=ot,
                    )
                )

        return proto.Action(
            name=a.name,
            parameters=[self.convert(p) for p in a.parameters],
            duration=self.convert(a.duration),
            conditions=conditions,
            effects=effects,
        )

    @handles(model.timing.Timepoint)
    def _convert_timepoint(self, tp: model.timing.Timepoint) -> proto.Timepoint:
        if tp.kind == TimepointKind.START:
            kind = proto.Timepoint.TimepointKind.Value("START")
        elif tp.kind == TimepointKind.END:
            kind = proto.Timepoint.TimepointKind.Value("END")
        elif tp.kind == TimepointKind.GLOBAL_START:
            kind = proto.Timepoint.TimepointKind.Value("GLOBAL_START")
        elif tp.kind == TimepointKind.GLOBAL_END:
            kind = proto.Timepoint.TimepointKind.Value("GLOBAL_END")
        return proto.Timepoint(kind=kind, container_id=tp.container)

    @handles(model.Timing)
    def _convert_timing(self, timing: model.Timing) -> proto.Timing:
        return proto.Timing(
            timepoint=self.convert(timing._timepoint),
            delay=self.convert(fractions.Fraction(timing.delay)),
        )

    @handles(fractions.Fraction)
    def _convert_fraction(self, fraction: fractions.Fraction) -> float:
        return proto.Real(
            numerator=fraction.numerator, denominator=fraction.denominator
        )

    @handles(model.timing.Interval)
    def _convert_interval(self, interval: model.timing.Interval) -> proto.Interval:
        return proto.Interval(
            is_left_open=interval.is_left_open(),
            lower=self.convert(interval.lower()),
            is_right_open=interval.is_right_open(),
            upper=self.convert(interval.lower()),
        )

    @handles(model.TimeInterval)
    def _convert_time_interval(
        self, interval: model.TimeInterval
    ) -> proto.TimeInterval:
        return proto.TimeInterval(
            is_left_open=interval.is_left_open(),
            lower=self.convert(interval.lower),
            is_right_open=interval.is_right_open(),
            upper=self.convert(interval.upper),
        )

    @handles(model.DurationInterval)
    def _convert_duration_interval(
        self, interval: model.DurationInterval
    ) -> proto.Interval:
        return proto.Duration(
            controllable_in_bounds=proto.Interval(
                is_left_open=interval.is_left_open(),
                lower=self.convert(interval.lower),
                is_right_open=interval.is_right_open(),
                upper=self.convert(interval.upper),
            )
        )

    @handles(model.htn.Task)
    def _convert_abstract_task(
        self, task: model.htn.Task
    ) -> proto.AbstractTaskDeclaration:
        return proto.AbstractTaskDeclaration(
            name=task.name, parameters=[self.convert(p) for p in task.parameters]
        )

    @handles(model.htn.ParameterizedTask)
    def _convert_parameterized_task(
        self, task: model.htn.ParameterizedTask
    ) -> proto.Task:
        parameters = []
        for p in task.parameters:
            parameters.append(
                proto.Expression(
                    atom=proto.Atom(symbol=p.name),
                    list=[],
                    kind=proto.ExpressionKind.Value("PARAMETER"),
                    type=proto_type(p.type),
                )
            )
        return proto.Task(id="", task_name=task.task.name, parameters=parameters)

    @handles(model.htn.Subtask)
    def _convert_subtask(self, subtask: model.htn.Subtask) -> proto.Task:
        return proto.Task(
            id=subtask.identifier,
            task_name=subtask.task.name,
            parameters=[self.convert(p) for p in subtask.parameters],
        )

    @handles(model.htn.Method)
    def _convert_method(self, method: model.htn.Method) -> proto.Method:
        return proto.Method(
            name=method.name,
            parameters=[self.convert(p) for p in method.parameters],
            achieved_task=self.convert(method.achieved_task),
            subtasks=[self.convert(st) for st in method.subtasks],
            constraints=[self.convert(c) for c in method.constraints],
            conditions=[
                proto.Condition(cond=self.convert(c)) for c in method.preconditions
            ],
        )

    @handles(model.htn.TaskNetwork)
    def _convert_task_network(self, tn: model.htn.TaskNetwork) -> proto.TaskNetwork:
        return proto.TaskNetwork(
            variables=[self.convert(v) for v in tn.variables],
            subtasks=[self.convert(st) for st in tn.subtasks],
            constraints=[self.convert(c) for c in tn.constraints],
        )

    def build_hierarchy(
        self, problem: model.htn.HierarchicalProblem
    ) -> proto.Hierarchy:
        return proto.Hierarchy(
            initial_task_network=self.convert(problem.task_network),
            abstract_tasks=[self.convert(t) for t in problem.tasks],
            methods=[self.convert(m) for m in problem.methods],
        )

    @handles(model.Problem, model.htn.HierarchicalProblem)
    def _convert_problem(self, problem: model.Problem) -> proto.Problem:
        goals = [proto.Goal(goal=self.convert(g)) for g in problem.goals]
        for (t, gs) in problem.timed_goals:
            goals += [
                proto.Goal(goal=self.convert(g), timing=self.convert(t)) for g in gs
            ]

        problem_name = str(problem.name) if problem.name is not None else ""
        hierarchy = None
        if isinstance(problem, model.htn.HierarchicalProblem):
            hierarchy = self.build_hierarchy(problem)

        return proto.Problem(
            domain_name=problem_name + "_domain",
            problem_name=problem_name,
            types=[self.convert(t) for t in problem.user_types],
            fluents=[self.convert(f, problem) for f in problem.fluents],
            objects=[self.convert(o) for o in problem.all_objects],
            actions=[self.convert(a) for a in problem.actions],
            initial_state=[
                proto.Assignment(fluent=self.convert(x), value=self.convert(v))
                for (x, v) in problem.initial_values.items()
            ],
            timed_effects=[self.convert(e) for e in problem.timed_effects],
            goals=goals,
            features=[map_feature(feature) for feature in problem.kind.features],
            metrics=[self.convert(m) for m in problem.quality_metrics],
            hierarchy=hierarchy,
        )

    @handles(model.metrics.MinimizeActionCosts)
    def _convert_minimize_action_costs(
        self, metric: model.metrics.MinimizeActionCosts
    ) -> proto.Metric:
        action_costs = {}
        for action, cost in metric.costs.items():
            action_costs[action.name] = self.convert(cost)

        return proto.Metric(
            kind=proto.Metric.MINIMIZE_ACTION_COSTS,
            action_costs=action_costs,
            default_action_cost=self.convert(metric.default)
            if metric.default is not None
            else None,
        )

    @handles(model.metrics.MinimizeSequentialPlanLength)
    def _convert_minimize_sequential_plan_length(self, _) -> proto.Metric:
        return proto.Metric(
            kind=proto.Metric.MINIMIZE_SEQUENTIAL_PLAN_LENGTH,
        )

    @handles(model.metrics.MinimizeMakespan)
    def _convert_minimize_makespan(self, _) -> proto.Metric:
        return proto.Metric(
            kind=proto.Metric.MINIMIZE_MAKESPAN,
        )

    @handles(model.metrics.MinimizeExpressionOnFinalState)
    def _convert_minimize_expression_on_final_state(
        self, metric: model.metrics.MinimizeExpressionOnFinalState
    ) -> proto.Metric:
        return proto.Metric(
            kind=proto.Metric.MINIMIZE_EXPRESSION_ON_FINAL_STATE,
            expression=self.convert(metric.expression),
        )

    @handles(model.metrics.MaximizeExpressionOnFinalState)
    def _convert_maximize_expression_on_final_state(
        self, metric: model.metrics.MaximizeExpressionOnFinalState
    ) -> proto.Metric:
        return proto.Metric(
            kind=proto.Metric.MAXIMIZE_EXPRESSION_ON_FINAL_STATE,
            expression=self.convert(metric.expression),
        )

    @handles(model.metrics.Oversubscription)
    def _convert_oversubscription_metric(
        self, metric: model.metrics.Oversubscription
    ) -> proto.Metric:
        goals = []
        for g, c in metric.goals.items():
            goals.append(
                proto.GoalWithCost(
                    goal=self.convert(g), cost=self.convert(fractions.Fraction(c))
                )
            )
        return proto.Metric(
            kind=proto.Metric.OVERSUBSCRIPTION,
            goals=goals,
        )

    @handles(model.Parameter)
    def _convert_action_parameter(self, p: model.Parameter) -> proto.Parameter:
        return proto.Parameter(name=p.name, type=proto_type(p.type))

    @handles(model.Variable)
    def _convert_expression_variable(
        self, variable: model.Variable
    ) -> proto.Expression:
        # a variable declaration (in forall/exists) is converted directly as an expression
        return proto.Expression(
            atom=proto.Atom(symbol=variable.name),
            list=[],
            kind=proto.ExpressionKind.Value("VARIABLE"),
            type=proto_type(variable.type),
        )

    @handles(unified_planning.plans.ActionInstance)
    def _convert_action_instance(
        self, a: unified_planning.plans.ActionInstance, start_time=None, end_time=None
    ) -> proto.ActionInstance:
        parameters = []
        for param in a.actual_parameters:
            # The parameters are atoms
            parameters.append(self.convert(param).atom)

        return proto.ActionInstance(
            action_name=a.action.name,
            parameters=parameters,
            start_time=start_time,
            end_time=end_time,
        )

    @handles(str)
    def _convert_str_atom(self, s: str) -> proto.Atom:
        return proto.Atom(symbol=s)

    @handles(unified_planning.plans.SequentialPlan)
    def _convert_sequential_plan(
        self, plan: unified_planning.plans.SequentialPlan
    ) -> proto.Plan:
        return proto.Plan(actions=[self.convert(a) for a in plan.actions])

    @handles(unified_planning.plans.TimeTriggeredPlan)
    def _convert_time_triggered_plan(
        self, plan: unified_planning.plans.TimeTriggeredPlan
    ) -> proto.Plan:
        action_instances = []

        for a in plan.timed_actions:
            start_time = self.convert(a[0])
            end_time = self.convert(a[0] + a[2])
            instance = self._convert_action_instance(
                a[1], start_time=start_time, end_time=end_time
            )
            action_instances.append(instance)

        return proto.Plan(actions=action_instances)

    @handles(unified_planning.engines.PlanGenerationResult)
    def _convert_plan_generation_result(
        self, result: unified_planning.engines.PlanGenerationResult
    ) -> proto.PlanGenerationResult:
        log_messages = None
        if result.log_messages is not None:
            log_messages = [self.convert(log) for log in result.log_messages]

        return proto.PlanGenerationResult(
            status=self.convert(result.status),
            plan=self.convert(result.plan),
            engine=proto.Engine(name=result.engine_name),
            metrics=result.metrics,
            log_messages=log_messages,
        )

    @handles(unified_planning.engines.PlanGenerationResultStatus)
    def _convert_plan_generation_status(
        self, status: unified_planning.engines.PlanGenerationResultStatus
    ) -> proto.PlanGenerationResult.Status:
        if (
            status
            == unified_planning.engines.PlanGenerationResultStatus.SOLVED_SATISFICING
        ):
            return proto.PlanGenerationResult.Status.Value("SOLVED_SATISFICING")

        elif (
            status
            == unified_planning.engines.PlanGenerationResultStatus.SOLVED_OPTIMALLY
        ):
            return proto.PlanGenerationResult.Status.Value("SOLVED_OPTIMALLY")
        elif (
            status
            == unified_planning.engines.PlanGenerationResultStatus.UNSOLVABLE_PROVEN
        ):
            return proto.PlanGenerationResult.Status.Value("UNSOLVABLE_PROVEN")
        elif (
            status
            == unified_planning.engines.PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY
        ):
            return proto.PlanGenerationResult.Status.Value("UNSOLVABLE_INCOMPLETELY")
        elif status == unified_planning.engines.PlanGenerationResultStatus.TIMEOUT:
            return proto.PlanGenerationResult.Status.Value("TIMEOUT")
        elif status == unified_planning.engines.PlanGenerationResultStatus.MEMOUT:
            return proto.PlanGenerationResult.Status.Value("MEMOUT")
        elif (
            status == unified_planning.engines.PlanGenerationResultStatus.INTERNAL_ERROR
        ):
            return proto.PlanGenerationResult.Status.Value("INTERNAL_ERROR")
        elif (
            status
            == unified_planning.engines.PlanGenerationResultStatus.UNSUPPORTED_PROBLEM
        ):

            return proto.PlanGenerationResult.Status.Value("UNSUPPORTED_PROBLEM")
        elif status == unified_planning.engines.PlanGenerationResultStatus.INTERMEDIATE:
            return proto.PlanGenerationResult.Status.Value("INTERMEDIATE")
        else:
            raise ValueError("Unknown status: {}".format(status))

    @handles(unified_planning.engines.LogMessage)
    def _convert_log_messages(
        self, log: unified_planning.engines.LogMessage
    ) -> proto.LogMessage:
        if log.level == unified_planning.engines.LogLevel.INFO:
            level = proto.LogMessage.LogLevel.Value("INFO")
        elif log.level == unified_planning.engines.LogLevel.WARNING:
            level = proto.LogMessage.LogLevel.Value("WARNING")
        elif log.level == unified_planning.engines.LogLevel.ERROR:
            level = proto.LogMessage.LogLevel.Value("ERROR")
        elif log.level == unified_planning.engines.LogLevel.DEBUG:
            level = proto.LogMessage.LogLevel.Value("DEBUG")
        else:
            raise UPException(f"Unknown log level: {log.level}")

        return proto.LogMessage(
            level=level,
            message=str(log.message),
        )

    @handles(unified_planning.engines.CompilerResult)
    def _convert_compiler_result(
        self, result: unified_planning.engines.CompilerResult
    ) -> proto.CompilerResult:
        map: Dict[str, proto.ActionInstance] = {}
        log_messages = result.log_messages
        if log_messages is None:
            log_messages = []
        if result.map_back_action_instance is not None:
            for compiled_action in result.problem.actions:
                type_list = [param.type for param in compiled_action.parameters]
                if len(type_list) == 0:
                    ai = unified_planning.plans.ActionInstance(compiled_action)
                    map[str(ai)] = self.convert(result.map_back_action_instance(ai))
                    continue
                ground_size = 1
                domain_sizes = []
                for t in type_list:
                    ds = domain_size(result.problem, t)
                    domain_sizes.append(ds)
                    ground_size *= ds
                items_list: List[List[FNode]] = []
                for size, type in zip(domain_sizes, type_list):
                    items_list.append(
                        [domain_item(result.problem, type, j) for j in range(size)]
                    )
                grounded_params_list = product(*items_list)
                for grounded_params in grounded_params_list:
                    ai = unified_planning.plans.ActionInstance(
                        compiled_action, tuple(grounded_params)
                    )
                    map[str(ai)] = self.convert(result.map_back_action_instance(ai))
        return proto.CompilerResult(
            problem=self.convert(result.problem),
            map_back_plan=map,
            log_messages=[self.convert(log) for log in log_messages],
            engine=proto.Engine(name=result.engine_name),
        )

    @handles(unified_planning.engines.ValidationResult)
    def _convert_validation_result(
        self, result: unified_planning.engines.ValidationResult
    ) -> proto.ValidationResult:
        return proto.ValidationResult(
            status=self.convert(result.status),
            log_messages=[self.convert(log) for log in result.log_messages],
            engine=proto.Engine(name=result.engine_name),
        )

    @handles(unified_planning.engines.ValidationResultStatus)
    def _convert_validation_result_status(
        self, status: unified_planning.engines.ValidationResultStatus
    ) -> proto.ValidationResult.ValidationResultStatus:
        if status == unified_planning.engines.ValidationResultStatus.VALID:
            return proto.ValidationResult.ValidationResultStatus.Value("VALID")
        elif status == unified_planning.engines.ValidationResultStatus.INVALID:
            return proto.ValidationResult.ValidationResultStatus.Value("INVALID")
        else:
            raise UPException(f"Unknown result status: {status}")
