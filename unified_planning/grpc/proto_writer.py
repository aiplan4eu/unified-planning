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

import unified_planning.grpc.generated.unified_planning_pb2 as proto
import unified_planning.model
import unified_planning.plan
import unified_planning.walkers as walkers
from unified_planning import model
from unified_planning.exceptions import UPException
from unified_planning.grpc.converter import Converter, handles
from unified_planning.model.operators import (
    BOOL_OPERATORS,
    IRA_OPERATORS,
    RELATIONS,
    OperatorKind,
)
from unified_planning.model.timing import TimepointKind
from typing import List


def map_operator(op: int) -> str:
    if op == OperatorKind.PLUS:
        return "+"
    elif op == OperatorKind.MINUS:
        return "-"
    elif op == OperatorKind.TIMES:
        return "*"
    elif op == OperatorKind.DIV:
        return "/"
    elif op == OperatorKind.LE:
        return "<="
    elif op == OperatorKind.LT:
        return "<"
    elif op == OperatorKind.EQUALS:
        return "="
    elif op == OperatorKind.AND:
        return "and"
    elif op == OperatorKind.OR:
        return "or"
    elif op == OperatorKind.NOT:
        return "not"
    elif op == OperatorKind.IMPLIES:
        return "implies"
    elif op == OperatorKind.IFF:
        return "iff"
    elif op == OperatorKind.EXISTS:
        return "exists"
    elif op == OperatorKind.FORALL:
        return "forall"
    raise ValueError(f"Unknown operator `{op}`")


class FNode2Protobuf(walkers.DagWalker):
    def __init__(self, protobuf_writer):
        super().__init__()
        self._protobuf_writer = protobuf_writer

    def convert(self, expression: model.FNode) -> proto.Expression:
        return self.walk(expression)

    def walk_bool_constant(self, expression: model.FNode,
                           args: List[proto.Expression]) -> proto.Expression:
        return proto.Expression(
            atom=proto.Atom(boolean=expression.bool_constant_value()),
            list=[],
            kind=proto.ExpressionKind.Value("CONSTANT"),
            type="bool",
        )

    def walk_int_constant(self, expression: model.FNode,
                          args: List[proto.Expression]) -> proto.Expression:
        return proto.Expression(
            atom=proto.Atom(int=expression.int_constant_value()),
            list=[],
            kind=proto.ExpressionKind.Value("CONSTANT"),
            type="integer",
        )

    def walk_real_constant(self, expression: model.FNode,
                           args: List[proto.Expression]) -> proto.Expression:
        return proto.Expression(
            atom=proto.Atom(real=self._protobuf_writer.convert(expression.real_constant_value())),
            list=[],
            kind=proto.ExpressionKind.Value("CONSTANT"),
            type="real",
        )

    def walk_param_exp(self, expression: model.FNode,
                       args: List[proto.Expression]) -> proto.Expression:
        return proto.Expression(
            atom=proto.Atom(symbol=expression.parameter().name),
            list=[],
            kind=proto.ExpressionKind.Value("PARAMETER"),
            type=str(expression.parameter().type),
        )

    def walk_variable_exp(self, expression: model.FNode,
                          args: List[proto.Expression]) -> proto.Expression:
        return proto.Expression(
            atom=proto.Atom(symbol=expression.variable().name),
            list=[],
            kind=proto.ExpressionKind.Value("VARIABLE"),
            type=str(expression.variable().type),
        )

    def walk_object_exp(self, expression: model.FNode,
                        args: List[proto.Expression]) -> proto.Expression:
        return proto.Expression(
            atom=proto.Atom(symbol=expression.object().name),
            list=[],
            kind=proto.ExpressionKind.Value("CONSTANT"),
            type=str(expression.object().type),
        )

    def walk_fluent_exp(self, expression: model.FNode,
                        args: List[proto.Expression]) -> proto.Expression:
        sub_list = []
        sub_list.append(
            proto.Expression(
                atom=proto.Atom(symbol=expression.fluent().name),
                kind=proto.ExpressionKind.Value("FLUENT_SYMBOL"),
                type=str(expression.fluent().type),
            )
        )
        sub_list.extend(args)
        return proto.Expression(
            atom=None,
            list=sub_list,
            kind=proto.ExpressionKind.Value("STATE_VARIABLE"),
            type=str(expression.fluent().type),
        )

    @walkers.handles(BOOL_OPERATORS.union(IRA_OPERATORS).union(RELATIONS))
    def walk_operator(self, expression: model.FNode,
                      args: List[proto.Expression]) -> proto.Expression:
        sub_list = []
        sub_list.append(
            proto.Expression(
                atom=proto.Atom(symbol=map_operator(expression.node_type)),
                list=[],
                kind=proto.ExpressionKind.Value("FUNCTION_SYMBOL"),
                type="",
            )
        )
        # forall/exists: add the declared variables from the payload to the beginning of the parameter list.
        if expression.is_exists() or expression.is_forall():
            sub_list.extend([self._protobuf_writer.convert(p) for p in expression.variables()])

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
    def __init__(self):
        super().__init__()
        self._fnode2proto = FNode2Protobuf(self)

    @handles(model.Fluent)
    def _convert_fluent(self, fluent: model.Fluent, problem: model.Problem) -> proto.Fluent:
        name = fluent.name
        sig = [self.convert(t) for t in fluent.signature]
        return proto.Fluent(
            name=name,
            value_type=str(fluent.type),
            parameters=sig,
            default_value=self.convert(problem.fluents_defaults[fluent])
            if fluent in problem.fluents_defaults
            else None,
        )

    @handles(model.Object)
    def _convert_object(self, obj: model.Object) -> proto.ObjectDeclaration:
        return proto.ObjectDeclaration(name=obj.name, type=str(obj.type))

    @handles(model.FNode)
    def _convert_fnode(self, exp: model.FNode) -> proto.Expression:
        return self._fnode2proto.convert(exp)

    @handles(model.types._BoolType)
    def _convert_bool_type(self, _: model.types._BoolType) -> proto.TypeDeclaration:
        return proto.TypeDeclaration(type_name="bool")

    @handles(model.types._UserType)
    def _convert_user_type(self, t: model.types._UserType) -> proto.TypeDeclaration:
        return proto.TypeDeclaration(
            type_name=t.name, parent_type='' if t.father is None else str(t.father.name)
        )

    @handles(model.types._IntType)
    def _convert_integer_type(self, t: model.types._IntType) -> proto.TypeDeclaration:
        return proto.TypeDeclaration(type_name=str(t))

    @handles(model.types._RealType)
    def _convert_real(self, t: model.types._RealType) -> proto.TypeDeclaration:
        return proto.TypeDeclaration(type_name=str(t))

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
    def _convert_instantaneous_action(self, a: model.InstantaneousAction) -> proto.Action:
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
            effects.append(
                proto.Effect(
                    effect=self.convert(eff), occurrence_time=None
                )
            )

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
        return proto.Timepoint(kind=kind)

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
    def _convert_time_interval(self, interval: model.TimeInterval) -> proto.TimeInterval:
        return proto.TimeInterval(
            is_left_open=interval.is_left_open(),
            lower=self.convert(interval.lower),
            is_right_open=interval.is_right_open(),
            upper=self.convert(interval.upper),
        )

    @handles(model.DurationInterval)
    def _convert_duration_interval(self, interval: model.DurationInterval) -> proto.Interval:
        return proto.Duration(
            controllable_in_bounds=proto.Interval(
                is_left_open=interval.is_left_open(),
                lower=self.convert(interval.lower),
                is_right_open=interval.is_right_open(),
                upper=self.convert(interval.upper),
            )
        )

    @handles(model.Problem)
    def _convert_problem(self, problem: model.Problem) -> proto.Problem:
        goals = [proto.Goal(goal=self.convert(g)) for g in problem.goals]
        for (t, gs) in problem.timed_goals:
            goals += [
                proto.Goal(goal=self.convert(g), timing=self.convert(t))
                for g in gs
            ]

        return proto.Problem(
            domain_name=str(problem.name + "_domain"),
            problem_name=problem.name,
            types=[self.convert(t) for t in problem.user_types],
            fluents=[self.convert(f, problem) for f in problem.fluents],
            objects=[self.convert(o) for o in problem.all_objects],
            actions=[self.convert(a) for a in problem.actions],
            initial_state=[
                proto.Assignment(
                    fluent=self.convert(x), value=self.convert(v)
                )
                for (x, v) in problem.initial_values.items()
            ],
            timed_effects=[self.convert(e) for e in problem.timed_effects],
            goals=goals,
            features=[map_feature(feature) for feature in problem.kind.features],
            metrics=[self.convert(m) for m in problem.quality_metrics],
        )

    @handles(model.metrics.MinimizeActionCosts)
    def _convert_minimize_action_costs(self, metric: model.metrics.MinimizeActionCosts) -> proto.Metric:
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
    def _convert_minimize_expression_on_final_state(self, metric: model.metrics.MinimizeExpressionOnFinalState) -> proto.Metric:
        return proto.Metric(
            kind=proto.Metric.MINIMIZE_EXPRESSION_ON_FINAL_STATE,
            expression=self.convert(metric.expression),
        )

    @handles(model.metrics.MaximizeExpressionOnFinalState)
    def _convert_maximize_expression_on_final_state(self, metric: model.metrics.MaximizeExpressionOnFinalState) -> proto.Metric:
        return proto.Metric(
            kind=proto.Metric.MAXIMIZE_EXPRESSION_ON_FINAL_STATE,
            expression=self.convert(metric.expression),
        )

    @handles(model.Parameter)
    def _convert_action_parameter(self, p: model.Parameter) -> proto.Parameter:
        return proto.Parameter(name=p.name, type=str(p.type))

    @handles(model.Variable)
    def _convert_expression_variable(self, variable: model.Variable) -> proto.Expression:
        # a variable declaration (in forall/exists) is converted directly as an expression
        return proto.Expression(
            atom=proto.Atom(symbol=variable.name),
            list=[],
            kind=proto.ExpressionKind.Value("VARIABLE"),
            type=str(variable.type),
        )

    @handles(unified_planning.plan.ActionInstance)
    def _convert_action_instance(self, a: unified_planning.plan.ActionInstance, start_time=None, end_time=None) -> proto.ActionInstance:
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

    @handles(unified_planning.plan.SequentialPlan)
    def _convert_sequential_plan(self, plan: unified_planning.plan.SequentialPlan) -> proto.Plan:
        return proto.Plan(
            actions=[self.convert(a) for a in plan.actions]
        )

    @handles(unified_planning.plan.TimeTriggeredPlan)
    def _convert_time_triggered_plan(self, plan: unified_planning.plan.TimeTriggeredPlan) -> proto.Plan:
        action_instances = []

        for a in plan.actions:
            start_time = self.convert(a[0])
            end_time = self.convert(a[0] + a[2])
            instance = self._convert_action_instance(
                a[1], start_time=start_time, end_time=end_time
            )
            action_instances.append(instance)

        return proto.Plan(actions=action_instances)

    @handles(unified_planning.solvers.PlanGenerationResult)
    def _convert_plan_generation_result(self, result: unified_planning.solvers.PlanGenerationResult) -> proto.PlanGenerationResult:
        # TODO: Extend the protobuf convertors to handle metrics and logs in results
        return proto.PlanGenerationResult(
            status=self.convert(result.status),
            plan=self.convert(result.plan),
            engine=proto.Engine(name=result.planner_name),
            # metrics=result.metrics,
            # logs=[self.convert(log) for log in result.log_messages],
        )

    @handles(unified_planning.solvers.PlanGenerationResultStatus)
    def _convert_plan_generation_status(self, status: unified_planning.solvers.PlanGenerationResultStatus) -> proto.PlanGenerationResult.Status:
        if (
            status
            == unified_planning.solvers.PlanGenerationResultStatus.SOLVED_SATISFICING
        ):
            return proto.PlanGenerationResult.Status.Value(
                "SOLVED_SATISFICING"
            )

        elif (
            status
            == unified_planning.solvers.PlanGenerationResultStatus.SOLVED_OPTIMALLY
        ):
            return proto.PlanGenerationResult.Status.Value(
                "SOLVED_OPTIMALLY"
            )
        elif (
            status
            == unified_planning.solvers.PlanGenerationResultStatus.UNSOLVABLE_PROVEN
        ):
            return proto.PlanGenerationResult.Status.Value(
                "UNSOLVABLE_PROVEN"
            )
        elif (
            status
            == unified_planning.solvers.PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY
        ):
            return proto.PlanGenerationResult.Status.Value(
                "UNSOLVABLE_INCOMPLETELY"
            )
        elif status == unified_planning.solvers.PlanGenerationResultStatus.TIMEOUT:
            return proto.PlanGenerationResult.Status.Value("TIMEOUT")
        elif status == unified_planning.solvers.PlanGenerationResultStatus.MEMOUT:
            return proto.PlanGenerationResult.Status.Value("MEMOUT")
        elif (
            status == unified_planning.solvers.PlanGenerationResultStatus.INTERNAL_ERROR
        ):
            return proto.PlanGenerationResult.Status.Value(
                "INTERNAL_ERROR"
            )
        elif (
            status
            == unified_planning.solvers.PlanGenerationResultStatus.UNSUPPORTED_PROBLEM
        ):

            return proto.PlanGenerationResult.Status.Value(
                "UNSUPPORTED_PROBLEM"
            )
        elif status == unified_planning.solvers.PlanGenerationResultStatus.INTERMEDIATE:
            return proto.PlanGenerationResult.Status.Value(
                "INTERMEDIATE"
            )
        else:
            raise ValueError("Unknown status: {}".format(status))

    @handles(unified_planning.solvers.LogMessage)
    def _convert_log_messages(self, log: unified_planning.solvers.LogMessage) -> proto.LogMessage:
        if log.level == unified_planning.solvers.LogLevel.INFO:
            level = proto.LogMessage.LogLevel.Value("INFO")
        elif log.level == unified_planning.solvers.LogLevel.WARNING:
            level = proto.LogMessage.LogLevel.Value("WARNING")
        elif log.level == unified_planning.solvers.LogLevel.ERROR:
            level = proto.LogMessage.LogLevel.Value("ERROR")
        elif log.level == unified_planning.solvers.LogLevel.DEBUG:
            level = proto.LogMessage.LogLevel.Value("DEBUG")
        else:
            raise UPException(f"Unknown log level: {log.level}")

        return proto.LogMessage(
            level=level,
            message=str(log.message),
        )

    @handles(unified_planning.solvers.GroundingResult)
    def _convert_grounding_result(self, result: unified_planning.solvers.GroundingResult) -> proto.GroundingResult:
        map: Dict[str, proto.ActionInstance]= {}
        if result.lift_action_instance is not None:
            for grounded_action in result.problem.actions:
                map[grounded_action.name] = self.convert(result.lift_action_instance(unified_planning.plan.ActionInstance(grounded_action)))
        return proto.GroundingResult(
            problem=self.convert(result.problem),
            map_to_lift_plan=map,
            logs=[self.convert(log) for log in result.log_messages],
            engine=proto.Engine(name=result.engine_name)
        )

    @handles(unified_planning.solvers.ValidationResult)
    def _convert_validation_result(self, result: unified_planning.solvers.ValidationResult) -> proto.ValidationResult:
        return proto.ValidationResult(
            status=self.convert(result.status),
            logs=[self.convert(log) for log in result.log_messages],
            engine=proto.Engine(name=result.engine_name)
        )

    @handles(unified_planning.solvers.ValidationResultStatus)
    def _convert_validation_result_status(self, status: unified_planning.solvers.ValidationResultStatus) -> proto.ValidationResult.ValidationResultStatus:
        if status == unified_planning.solvers.ValidationResultStatus.VALID:
            return proto.ValidationResult.ValidationResultStatus.Value("VALID")
        elif status == unified_planning.solvers.ValidationResultStatus.INVALID:
            return proto.ValidationResult.ValidationResultStatus.Value("INVALID")
        else:
            raise UPException(f"Unknown result status: {status}")
