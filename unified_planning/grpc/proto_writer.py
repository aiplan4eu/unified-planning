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

    @handles(unified_planning.model.fnode.FNode)
    def _convert_fnode(self, exp):
        payload = exp._content.payload
        args = exp.args()
        value = None
        if payload is None:
            p_type = "none"
            value = "-"
        elif isinstance(payload, bool):
            p_type = "bool"
        elif isinstance(payload, int):
            p_type = "int"
        elif isinstance(payload, float):
            p_type = "real"
        elif isinstance(payload, unified_planning.model.Fluent):
            p_type = "fluent"
            value = payload.name()
        elif isinstance(payload, unified_planning.model.Object):
            p_type = "obj"
            value = payload.name()
        elif isinstance(payload, unified_planning.model.ActionParameter):
            p_type = "aparam"
            value = payload.name()
        else:
            p_type = "str"
        if value is None:
            value = str(payload)

        if len(args) == 0:
            if isinstance(payload, bool):
                atom = unified_planning_pb2.Atom(boolean=payload)
            elif isinstance(payload, int):
                atom = unified_planning_pb2.Atom(int=payload)
            elif isinstance(payload, float):
                atom = unified_planning_pb2.Atom(float=payload)
            else:
                atom = unified_planning_pb2.Atom(symbol=str(payload))
            arg_list = None
        else:
            atom = None
            arg_list = [self.convert(a) for a in exp._content.args]

        # TODO: Missing FUNCTION_SYMBOL, STATE_VARIABLE, FUNCTION_APPLICATION
        if exp.is_constant():
            kind = unified_planning_pb2.ExpressionKind.Value("CONSTANT")
        elif exp.is_parameter_exp():
            kind = unified_planning_pb2.ExpressionKind.Value("PARAMETER")
        elif exp.is_fluent_exp():
            kind = unified_planning_pb2.ExpressionKind.Value("FLUENT_SYMBOL")
        else:
            kind = unified_planning_pb2.ExpressionKind.Value("UNKNOWN")

        value_type = op_to_str(exp.node_type())

        # TODO: fix value_type to represent function symbols
        return unified_planning_pb2.Expression(
            atom=atom, list=arg_list, type=value_type, kind=kind
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

        return unified_planning_pb2.Effect(
            effect=unified_planning_pb2.EffectExpression(
                kind=kind,
                fluent=self.convert(effect.fluent()),
                value=self.convert(effect.value()),
                condition=self.convert(effect.condition()),
            ),
            occurence_time=None,
        )  # TODO: Not clear where this is supposed to come from

    @handles(unified_planning.model.InstantaneousAction)
    def _convert_instantaneous_action(self, a):
        cost = None
        if a.cost() is not None:
            cost = self.convert(a.cost())

        return unified_planning_pb2.Action(
            name=a.name,
            parameters=[self.convert(p) for p in a.parameters()],
            duration=None,
            conditions=[
                unified_planning_pb2.Condition(cond=self.convert(c))
                for c in a.preconditions()
            ],
            effects=[self.convert(e) for e in a.effects()],
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
            domain_name=problem.name,  # TODO: fix
            problem_name=problem.name,  # TODO: fix
            types=[
                self.convert(t) for t in problem.user_types()
            ],  # TODO: only user types?
            fluents=[self.convert(f) for f in problem.fluents()],
            actions=[
                self.convert(a) for a in problem.actions()
            ],  # TODO: add durative actions
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
        return unified_planning_pb2.ActionInstance(
            action_name=a.action().name,
            parameters=[
                self.convert(p) for p in a.action()._parameters
            ],  # TODO: fix parameter name with parameter type
            start_time=0,  # TODO: fix temporal case
            end_time=0,  # TODO: fix temporal case
        )

    @handles(str)
    def _convert_str_atom(self, s):
        return unified_planning_pb2.Atom(symbol=s)

    @handles(unified_planning.plan.SequentialPlan)
    def _convert(self, plan):
        return unified_planning_pb2.Plan(
            actions=[self.convert(a) for a in plan.actions()]
        )
