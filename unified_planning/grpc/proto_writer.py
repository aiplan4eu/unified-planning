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
import unified_planning.grpc.generated.unified_planning_pb2 as unified_planning_pb2
from unified_planning.grpc.converter import Converter, handles
from unified_planning.model.operators import op_to_str
import unified_planning.model
import unified_planning.plan


def map_operator(op: int) -> str:
    # TODO: Not all operators are added currently
    op = op_to_str(op)
    if op == "PLUS":
        return "+"
    elif op == "MINUS":
        return "-"
    elif op == "TIMES":
        return "*"
    elif op == "DIV":
        return "/"
    elif op == "LE":
        return "<="
    elif op == "LT":
        return "<"
    elif op == "EQUALS":
        return "="
    elif op == "AND":
        return "and"
    elif op == "OR":
        return "or"
    elif op == "NOT":
        return "not"


class ProtobufWriter(Converter):
    @handles(unified_planning.model.Fluent)
    def _convert_fluent(self, fluent):
        name = fluent.name()
        sig = [
            unified_planning_pb2.Parameter(name="", type=str(t))
            for t in fluent.signature()
        ]
        valType = str(fluent.type())
        return unified_planning_pb2.Fluent(
            name=name, value_type=valType, parameters=sig
        )

    @handles(unified_planning.model.Object)
    def _convert_object(self, obj):
        return unified_planning_pb2.ObjectDeclaration(
            name=obj.name(), type=obj.type().name()
        )

    @handles(unified_planning.model.FNode)
    def _convert_fnode(self, exp):
        payload = exp._content.payload
        args = exp._content.args
        atom = None
        p_type = ""
        kind = unified_planning_pb2.ExpressionKind.Value("UNKNOWN")
        arg_list = []

        if isinstance(payload, bool):
            atom = unified_planning_pb2.Atom(boolean=payload)
            kind = unified_planning_pb2.ExpressionKind.Value("CONSTANT")
            p_type = "bool"
        elif isinstance(payload, int):
            atom = unified_planning_pb2.Atom(int=payload)
            kind = unified_planning_pb2.ExpressionKind.Value("CONSTANT")
            p_type = "int"
        elif isinstance(payload, float):
            atom = unified_planning_pb2.Atom(float=payload)
            kind = unified_planning_pb2.ExpressionKind.Value("CONSTANT")
            p_type = "real"
        elif isinstance(payload, str):
            atom = unified_planning_pb2.Atom(symbol=payload)
        elif isinstance(payload, unified_planning.model.Fluent):
            kind = unified_planning_pb2.ExpressionKind.Value("FLUENT_SYMBOL")
            atom = unified_planning_pb2.Atom(symbol=payload.name())
            p_type = str(payload.type())
        elif isinstance(payload, unified_planning.model.Object):
            # TODO: check if first element is fluent symbol
            kind = unified_planning_pb2.ExpressionKind.Value("STATE_VARIABLE")
            atom = unified_planning_pb2.Atom(symbol=payload.name())
        elif isinstance(payload, unified_planning.model.ActionParameter):
            kind = unified_planning_pb2.ExpressionKind.Value("PARAMETER")
            p_type = str(payload.type())
            atom = unified_planning_pb2.Atom(symbol=payload.name())
        else:
            kind = unified_planning_pb2.ExpressionKind.Value("FUNCTION_SYMBOL")
            atom = unified_planning_pb2.Atom(symbol=map_operator(exp.node_type()))

        for arg in args:
            arg_list.append(self.convert(arg))

        return unified_planning_pb2.Expression(
            atom=atom, list=arg_list, kind=kind, type=p_type
        )

    @handles(unified_planning.model.types._BoolType)
    def _convert_bool_type(self, t):
        return unified_planning_pb2.TypeDeclaration(type_name="bool")

    @handles(unified_planning.model.types._UserType)
    def _convert_user_type(self, t):
        return unified_planning_pb2.TypeDeclaration(
            type_name=t.name(), parent_type=str(t.father())
        )

    @handles(unified_planning.model.types._IntType)
    def _convert_integer_type(self, t):
        return unified_planning_pb2.TypeDeclaration(type_name=str(t))

    @handles(unified_planning.model.types._RealType)
    def _convert_real(self, t):
        return unified_planning_pb2.TypeDeclaration(type_name=str(t))

    @handles(unified_planning.model.Effect)
    def _convert_effect(self, effect):
        kind = unified_planning_pb2.EffectExpression.EffectKind.Value("UNDEFINED")
        if effect.is_assignment():
            kind = unified_planning_pb2.EffectExpression.EffectKind.Value("ASSIGN")
        elif effect.is_increase():
            kind = unified_planning_pb2.EffectExpression.EffectKind.Value("INCREASE")
        elif effect.is_decrease():
            kind = unified_planning_pb2.EffectExpression.EffectKind.Value("DECREASE")

        return unified_planning_pb2.EffectExpression(
            kind=kind,
            fluent=self.convert(effect.fluent()),
            value=self.convert(effect.value()),
            condition=self.convert(effect.condition()),
        )

    @handles(unified_planning.model.InstantaneousAction)
    def _convert_instantaneous_action(self, a):
        cost = None
        effects = []
        conditions = []
        if a.cost() is not None:
            cost = self.convert(a.cost())

        for cond in a.preconditions():
            conditions.append(
                unified_planning_pb2.Condition(
                    cond=self.convert(cond),
                    span=None,
                )
            )

        for eff in a.effects():
            effects.append(
                unified_planning_pb2.Effect(
                    effect=self.convert(eff), occurence_time=None
                )
            )

        return unified_planning_pb2.Action(
            name=a.name,
            parameters=[self.convert(p) for p in a.parameters()],
            duration=None,
            conditions=conditions,
            effects=effects,
            cost=cost,
        )

    @handles(unified_planning.model.DurativeAction)
    def _convert_durative_action(self, a):
        cost = None
        effects = []
        conditions = []
        if a.cost() is not None:
            cost = self.convert(a.cost())

        for span, cond in a.conditions().items():
            conditions.append(
                unified_planning_pb2.Condition(
                    cond=self.convert(cond),
                    span=self.convert(span),
                )
            )
        for ot, eff in a.effects().items():
            effects.append(
                unified_planning_pb2.Effect(
                    effect=self.convert(eff),
                    occurence_time=self.convert(ot),
                )
            )

        return unified_planning_pb2.Action(
            name=a.name,
            parameters=[self.convert(p) for p in a.parameters()],
            duration=self.convert(a.duration()),
            conditions=conditions,
            effects=effects,
            cost=cost,
        )

    @handles(unified_planning.model.timing.Timepoint)
    def _convert_timepoint(self, tp):
        return unified_planning_pb2.Timepoint(kind=tp.kind())

    @handles(unified_planning.model.Timing)
    def _convert_timing(self, timing):
        return unified_planning_pb2.Timing(
            timepoint=self.convert(timing._timepoint), delay=float(timing.delay())
        )  # TODO: Will change fraction or int to float because of current PB definition

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
        return unified_planning_pb2.Interval(
            is_left_open=interval.is_left_open(),
            lower=self.convert(interval.lower()),
            is_right_open=interval.is_right_open(),
            upper=self.convert(interval.lower()),
        )

    @handles(unified_planning.model.DurationInterval)
    def _convert_duration_interval(self, interval):
        return unified_planning_pb2.Duration(
            controllable_in_bounds=unified_planning_pb2.Interval(
                s_left_open=interval.is_left_open(),
                lower=self.convert(interval.lower()),
                is_right_open=interval.is_right_open(),
                upper=self.convert(interval.lower()),
            )
        )

    @handles(unified_planning.model.Problem)
    def _convert_problem(self, problem):
        goals = [
            unified_planning_pb2.Goal(goal=self.convert(g)) for g in problem.goals()
        ]
        for (t, gs) in problem.timed_goals():
            goals += [
                unified_planning_pb2.Goal(goal=self.convert(g), timing=self.convert(t))
                for g in gs
            ]

        return unified_planning_pb2.Problem(
            domain_name=str(problem.name + "_domain"),
            problem_name=problem.name,
            types=[
                self.convert(t) for t in problem.user_types()
            ],  # TODO: only user types?
            fluents=[self.convert(f) for f in problem.fluents()],
            actions=[self.convert(a) for a in problem.actions()],
            initial_state=[
                unified_planning_pb2.Assignment(
                    fluent=self.convert(x), value=self.convert(v)
                )
                for (x, v) in problem.initial_values().items()
            ],
            timed_effects=[],  # TODO: Add
            goals=goals,
        )

    @handles(unified_planning.model.ActionParameter)
    def _convert_action_parameter(self, p):
        return unified_planning_pb2.Parameter(name=p.name(), type=str(p.type()))

    @handles(unified_planning.plan.ActionInstance)
    def _convert_action_instance(
        self,
        a: unified_planning_pb2.ActionInstance,
    ):
        action = self.convert(a.action())
        start_time = 0  # TODO:fix action instance start time
        end_time = (
            0
            if action.duration is None
            else 0
            # else start_time + action.duration.controllable_in_bounds.upper  # TODO: fix
        )

        parameters = []
        for param in a.actual_parameters():
            param_expr = self.convert(param)
            if param_expr.kind == unified_planning_pb2.ExpressionKind.Value(
                "STATE_VARIABLE"
            ):
                parameters.append(param_expr.atom)
            else:
                raise ValueError(f"Unsupported parameter type: {param_expr.type}")

        return unified_planning_pb2.ActionInstance(
            action_name=action.name,
            parameters=parameters,
            start_time=start_time,
            end_time=end_time,
        )

    @handles(str)
    def _convert_str_atom(self, s):
        return unified_planning_pb2.Atom(symbol=s)

    @handles(unified_planning.plan.SequentialPlan)
    def _convert(self, plan):
        return unified_planning_pb2.Plan(
            actions=[self.convert(a) for a in plan.actions()]
        )
