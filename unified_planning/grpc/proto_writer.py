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
import fractions
import unified_planning.grpc.generated.unified_planning_pb2 as unified_planning_pb2
from unified_planning import model
from unified_planning.grpc.converter import Converter, handles
from unified_planning.model.operators import (
    OperatorKind,
    RELATIONS,
    IRA_OPERATORS,
    BOOL_OPERATORS,
)
import unified_planning.model
from unified_planning.model.timing import TimepointKind
import unified_planning.plan


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


def map_feature(feature: str) -> unified_planning_pb2.Feature:
    pb_feature = unified_planning_pb2.Feature.Value(feature)
    if pb_feature is None:
        raise ValueError(f"Cannot convert feature to protobuf {feature}")
    return pb_feature


class ProtobufWriter(Converter):
    @handles(unified_planning.model.Fluent)
    def _convert_fluent(self, fluent, problem: model.Problem):
        name = fluent.name
        sig = [self.convert(t) for t in fluent.signature]
        return unified_planning_pb2.Fluent(
            name=name,
            value_type=str(fluent.type),
            parameters=sig,
            default_value=self.convert(problem.fluents_defaults[fluent]) if fluent in problem.fluents_defaults else None
        )

    @handles(unified_planning.model.Object)
    def _convert_object(self, obj):
        return unified_planning_pb2.ObjectDeclaration(name=obj.name, type=obj.type.name)

    @handles(unified_planning.model.FNode)
    def _convert_fnode(self, exp):
        node_type = exp._content.node_type
        args = exp._content.args
        payload = exp._content.payload

        if node_type == OperatorKind.BOOL_CONSTANT:
            return unified_planning_pb2.Expression(
                atom=unified_planning_pb2.Atom(boolean=payload),
                list=[],
                kind=unified_planning_pb2.ExpressionKind.Value("CONSTANT"),
                type="bool",
            )

        elif node_type == OperatorKind.INT_CONSTANT:
            return unified_planning_pb2.Expression(
                atom=unified_planning_pb2.Atom(int=payload),
                list=[],
                kind=unified_planning_pb2.ExpressionKind.Value("CONSTANT"),
                type="integer",
            )
        elif node_type == OperatorKind.REAL_CONSTANT:
            return unified_planning_pb2.Expression(
                atom=unified_planning_pb2.Atom(real=self._convert_to_real(payload)),
                list=[],
                kind=unified_planning_pb2.ExpressionKind.Value("CONSTANT"),
                type="real",
            )
        elif node_type == OperatorKind.OBJECT_EXP:
            return unified_planning_pb2.Expression(
                atom=unified_planning_pb2.Atom(symbol=payload.name),
                list=[],
                kind=unified_planning_pb2.ExpressionKind.Value("CONSTANT"),
                type=str(payload.type),
            )
        elif node_type == OperatorKind.PARAM_EXP:
            return unified_planning_pb2.Expression(
                atom=unified_planning_pb2.Atom(symbol=payload.name),
                list=[],
                kind=unified_planning_pb2.ExpressionKind.Value("PARAMETER"),
                type=str(payload.type),
            )
        elif node_type == OperatorKind.FLUENT_EXP:
            sub_list = []
            sub_list.append(
                unified_planning_pb2.Expression(
                    atom=unified_planning_pb2.Atom(symbol=payload.name),
                    kind=unified_planning_pb2.ExpressionKind.Value("FLUENT_SYMBOL"),
                    type=str(payload.type),
                )
            )
            sub_list.extend([self.convert(a) for a in args])
            return unified_planning_pb2.Expression(
                atom=None,
                list=sub_list,
                kind=unified_planning_pb2.ExpressionKind.Value("STATE_VARIABLE"),
                type=str(payload.type),
            )
        elif node_type in RELATIONS | BOOL_OPERATORS | IRA_OPERATORS:
            sub_list = []
            sub_list.append(
                unified_planning_pb2.Expression(
                    atom=unified_planning_pb2.Atom(symbol=map_operator(exp.node_type)),
                    list=[],
                    kind=unified_planning_pb2.ExpressionKind.Value("FUNCTION_SYMBOL"),
                    type="",
                )
            )
            # forall/exits: add the declared variables from the payload to the beginning of the parameter list.
            if node_type in [OperatorKind.EXISTS, OperatorKind.FORALL]:
                sub_list.extend([self.convert(p) for p in payload])

            sub_list.extend([self.convert(a) for a in args])
            return unified_planning_pb2.Expression(
                atom=None,
                list=sub_list,
                kind=unified_planning_pb2.ExpressionKind.Value("FUNCTION_APPLICATION"),
                type="",
            )
        elif node_type == OperatorKind.VARIABLE_EXP:
            return unified_planning_pb2.Expression(
                atom=unified_planning_pb2.Atom(symbol=payload.name),
                list=[],
                kind=unified_planning_pb2.ExpressionKind.Value("VARIABLE"),
                type=str(payload.type),
            )

        raise ValueError(f"Unable to handle expression of type {node_type}: {exp}")

    @handles(unified_planning.model.types._BoolType)
    def _convert_bool_type(self, t):
        return unified_planning_pb2.TypeDeclaration(type_name="bool")

    @handles(unified_planning.model.types._UserType)
    def _convert_user_type(self, t):
        return unified_planning_pb2.TypeDeclaration(
            type_name=t.name, parent_type=str(t.father)
        )

    @handles(unified_planning.model.types._IntType)
    def _convert_integer_type(self, t):
        return unified_planning_pb2.TypeDeclaration(type_name=str(t))

    @handles(unified_planning.model.types._RealType)
    def _convert_real(self, t):
        return unified_planning_pb2.TypeDeclaration(type_name=str(t))

    @handles(unified_planning.model.Effect)
    def _convert_effect(self, effect):
        kind = None
        if effect.is_assignment():
            kind = unified_planning_pb2.EffectExpression.EffectKind.Value("ASSIGN")
        elif effect.is_increase():
            kind = unified_planning_pb2.EffectExpression.EffectKind.Value("INCREASE")
        elif effect.is_decrease():
            kind = unified_planning_pb2.EffectExpression.EffectKind.Value("DECREASE")
        else:
            raise ValueError(f"Unsupported effect: {effect}")

        return unified_planning_pb2.EffectExpression(
            kind=kind,
            fluent=self.convert(effect.fluent),
            value=self.convert(effect.value),
            condition=self.convert(effect.condition),
        )

    @handles(unified_planning.model.InstantaneousAction)
    def _convert_instantaneous_action(self, a):
        cost = None
        effects = []
        conditions = []

        for cond in a.preconditions:
            conditions.append(
                unified_planning_pb2.Condition(
                    cond=self.convert(cond),
                    span=None,
                )
            )

        for eff in a.effects:
            effects.append(
                unified_planning_pb2.Effect(
                    effect=self.convert(eff), occurrence_time=None
                )
            )

        return unified_planning_pb2.Action(
            name=a.name,
            parameters=[self.convert(p) for p in a.parameters],
            duration=None,
            conditions=conditions,
            effects=effects,
        )

    @handles(unified_planning.model.DurativeAction)
    def _convert_durative_action(self, a):
        effects = []
        conditions = []

        for span, cond in a.conditions.items():
            span = self.convert(span)
            for c in cond:
                conditions.append(
                    unified_planning_pb2.Condition(
                        cond=self.convert(c),
                        span=span,
                    )
                )
        for ot, eff in a.effects.items():
            ot = self.convert(ot)
            for e in eff:
                effects.append(
                    unified_planning_pb2.Effect(
                        effect=self.convert(e),
                        occurrence_time=ot,
                    )
                )

        return unified_planning_pb2.Action(
            name=a.name,
            parameters=[self.convert(p) for p in a.parameters],
            duration=self.convert(a.duration),
            conditions=conditions,
            effects=effects,
        )

    @handles(unified_planning.model.timing.Timepoint)
    def _convert_timepoint(self, tp):
        if tp.kind == TimepointKind.START:
            kind = unified_planning_pb2.Timepoint.TimepointKind.Value("START")
        elif tp.kind == TimepointKind.END:
            kind = unified_planning_pb2.Timepoint.TimepointKind.Value("END")
        elif tp.kind == TimepointKind.GLOBAL_START:
            kind = unified_planning_pb2.Timepoint.TimepointKind.Value("GLOBAL_START")
        elif tp.kind == TimepointKind.GLOBAL_END:
            kind = unified_planning_pb2.Timepoint.TimepointKind.Value("GLOBAL_END")
        return unified_planning_pb2.Timepoint(kind=kind)

    @handles(unified_planning.model.Timing)
    def _convert_timing(self, timing):
        return unified_planning_pb2.Timing(
            timepoint=self.convert(timing._timepoint), delay=self._convert_to_real(timing.delay)
        )

    def _convert_to_real(self, element):
        return self.convert(fractions.Fraction(element))

    @handles(fractions.Fraction)
    def _convert_fraction(self, fraction):
        return unified_planning_pb2.Real(numerator=fraction.numerator, denominator=fraction.denominator)

    @handles(unified_planning.model.timing.Interval)
    def _convert_interval(self, interval):
        return unified_planning_pb2.Interval(
            is_left_open=interval.is_left_open(),
            lower=self.convert(interval.lower()),
            is_right_open=interval.is_right_open(),
            upper=self.convert(interval.lower()),
        )

    @handles(unified_planning.model.TimeInterval)
    def _convert_time_interval(self, interval):
        return unified_planning_pb2.TimeInterval(
            is_left_open=interval.is_left_open(),
            lower=self.convert(interval.lower),
            is_right_open=interval.is_right_open(),
            upper=self.convert(interval.upper),
        )

    @handles(unified_planning.model.DurationInterval)
    def _convert_duration_interval(self, interval):
        return unified_planning_pb2.Duration(
            controllable_in_bounds=unified_planning_pb2.Interval(
                is_left_open=interval.is_left_open(),
                lower=self.convert(interval.lower),
                is_right_open=interval.is_right_open(),
                upper=self.convert(interval.upper),
            )
        )

    @handles(unified_planning.model.Problem)
    def _convert_problem(self, problem):
        goals = [unified_planning_pb2.Goal(goal=self.convert(g)) for g in problem.goals]
        for (t, gs) in problem.timed_goals:
            goals += [
                unified_planning_pb2.Goal(goal=self.convert(g), timing=self.convert(t))
                for g in gs
            ]

        return unified_planning_pb2.Problem(
            domain_name=str(problem.name + "_domain"),
            problem_name=problem.name,
            types=[self.convert(t) for t in problem.user_types],
            fluents=[self.convert(f, problem) for f in problem.fluents],
            objects=[self.convert(o) for o in problem.all_objects],
            actions=[self.convert(a) for a in problem.actions],
            initial_state=[
                unified_planning_pb2.Assignment(
                    fluent=self.convert(x), value=self.convert(v)
                )
                for (x, v) in problem.initial_values.items()
            ],
            timed_effects=[self.convert(e) for e in problem.timed_effects],
            goals=goals,
            features=[map_feature(feature) for feature in problem.kind.features],
            metrics=[self.convert(m) for m in problem.quality_metrics],
        )

    @handles(unified_planning.model.metrics.MinimizeActionCosts)
    def _convert_minimize_action_costs(self, metric):
        action_costs = {}
        for action, cost in metric.costs.items():
            # TODO: Add default cost
            action_costs[action.name] = self.convert(cost)

        return unified_planning_pb2.Metric(
            kind=unified_planning_pb2.Metric.MINIMIZE_ACTION_COSTS,
            action_costs=action_costs,
        )

    @handles(unified_planning.model.metrics.MinimizeSequentialPlanLength)
    def _convert_minimize_sequential_plan_length(self, metric):
        return unified_planning_pb2.Metric(
            kind=unified_planning_pb2.Metric.MINIMIZE_SEQUENTIAL_PLAN_LENGTH,
        )

    @handles(unified_planning.model.metrics.MinimizeMakespan)
    def _convert_minimize_makespan(self, metric):
        return unified_planning_pb2.Metric(
            kind=unified_planning_pb2.Metric.MINIMIZE_MAKESPAN,
        )

    @handles(unified_planning.model.metrics.MinimizeExpressionOnFinalState)
    def _convert_minimize_expression_on_final_state(self, metric):
        return unified_planning_pb2.Metric(
            kind=unified_planning_pb2.Metric.MINIMIZE_EXPRESSION_ON_FINAL_STATE,
            expression=self.convert(metric.expression),
        )

    @handles(unified_planning.model.metrics.MaximizeExpressionOnFinalState)
    def _convert_maximize_expression_on_final_state(self, metric):
        return unified_planning_pb2.Metric(
            kind=unified_planning_pb2.Metric.MAXIMIZE_EXPRESSION_ON_FINAL_STATE,
            expression=self.convert(metric.expression),
        )

    @handles(unified_planning.model.Parameter)
    def _convert_action_parameter(self, p):
        return unified_planning_pb2.Parameter(name=p.name, type=str(p.type))

    @handles(unified_planning.model.Variable)
    def _convert_expression_variable(self, variable):
        # a variable declaration (in forall/exists) is converted directly as an expression
        return unified_planning_pb2.Expression(
                atom=unified_planning_pb2.Atom(symbol=variable.name),
                list=[],
                kind=unified_planning_pb2.ExpressionKind.Value("VARIABLE"),
                type=str(variable.type),
            )

    @handles(unified_planning.plan.ActionInstance)
    def _convert_action_instance(self, a, start_time=None, end_time=None):
        parameters = []
        for param in a.actual_parameters:
            # The parameters are OBJECT_EXP
            parameters.append(
                unified_planning_pb2.Atom(
                    symbol=param.object().name,
                )
            )

        return unified_planning_pb2.ActionInstance(
            action_name=a.action.name,
            parameters=parameters,
            start_time=start_time,
            end_time=end_time,
        )

    @handles(str)
    def _convert_str_atom(self, s):
        return unified_planning_pb2.Atom(symbol=s)

    @handles(unified_planning.plan.SequentialPlan)
    def _convert_sequential_plan(self, plan):
        return unified_planning_pb2.Plan(
            actions=[self.convert(a) for a in plan.actions]
        )

    @handles(unified_planning.plan.TimeTriggeredPlan)
    def _convert_time_triggered_plan(self, plan):
        action_instances = []

        for a in plan.actions:
            start_time = self.convert(a[0])
            end_time = self.convert(a[0] + a[2])
            instance = self._convert_action_instance(a[1], start_time=start_time, end_time=end_time)
            action_instances.append(instance)

        return unified_planning_pb2.Plan(actions=action_instances)

    @handles(unified_planning.solvers.PlanGenerationResult)
    def _convert_plan_generation_result(self, result):
        # FIXME: Logs and metrics are not supported yet
        return unified_planning_pb2.PlanGenerationResult(
            status=self.convert(result.status),
            plan=self.convert(result.plan),
            planner=unified_planning_pb2.Engine(name=result.planner_name),
            # metrics=result.metrics,
            # logs=[self.convert(log) for log in result.log_messages],
        )

    @handles(unified_planning.solvers.PlanGenerationResultStatus)
    def _convert_plan_generation_status(self, status):
        if (
            status
            == unified_planning.solvers.PlanGenerationResultStatus.SOLVED_SATISFICING
        ):
            return unified_planning_pb2.PlanGenerationResult.Status.Value(
                "SOLVED_SATISFICING"
            )

        elif (
            status
            == unified_planning.solvers.PlanGenerationResultStatus.SOLVED_OPTIMALLY
        ):
            return unified_planning_pb2.PlanGenerationResult.Status.Value(
                "SOLVED_OPTIMALLY"
            )
        elif (
            status
            == unified_planning.solvers.PlanGenerationResultStatus.UNSOLVABLE_PROVEN
        ):
            return unified_planning_pb2.PlanGenerationResult.Status.Value(
                "UNSOLVABLE_PROVEN"
            )
        elif (
            status
            == unified_planning.solvers.PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY
        ):
            return unified_planning_pb2.PlanGenerationResult.Status.Value(
                "UNSOLVABLE_INCOMPLETELY"
            )
        elif status == unified_planning.solvers.PlanGenerationResultStatus.TIMEOUT:
            return unified_planning_pb2.PlanGenerationResult.Status.Value("TIMEOUT")
        elif status == unified_planning.solvers.PlanGenerationResultStatus.MEMOUT:
            return unified_planning_pb2.PlanGenerationResult.Status.Value("MEMOUT")
        elif (
            status == unified_planning.solvers.PlanGenerationResultStatus.INTERNAL_ERROR
        ):
            return unified_planning_pb2.PlanGenerationResult.Status.Value(
                "INTERNAL_ERROR"
            )
        elif (
            status
            == unified_planning.solvers.PlanGenerationResultStatus.UNSUPPORTED_PROBLEM
        ):

            return unified_planning_pb2.PlanGenerationResult.Status.Value(
                "UNSUPPORTED_PROBLEM"
            )
        elif status == unified_planning.solvers.PlanGenerationResultStatus.INTERMEDIATE:
            return unified_planning_pb2.PlanGenerationResult.Status.Value(
                "INTERMEDIATE"
            )
        else:
            raise ValueError("Unknown status: {}".format(status))

    @handles(unified_planning.solvers.LogMessage)
    def _convert_log_messages(self, log):
        return unified_planning_pb2.LogMessage(
            level=int(log.level),
            message=str(log.message),
        )
