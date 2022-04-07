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
from typing import OrderedDict

import unified_planning.grpc.generated.unified_planning_pb2 as unified_planning_pb2
from unified_planning.grpc.converter import Converter, handles
import unified_planning.model
from unified_planning.model.effect import ASSIGN, INCREASE, DECREASE
import unified_planning.plan
from unified_planning.model import Effect, ActionParameter, Problem, DurativeAction
from unified_planning.shortcuts import BoolType, UserType, RealType, IntType


def convert_type_str(s, env):
    if s == "bool":
        value_type = env.type_manager.BoolType()
    elif s == "int":
        value_type = env.type_manager.IntType()  # TODO: deal with bounds
    elif s == "float":
        value_type = env.type_manager.RealType()  # TODO: deal with bounds
    elif "real" in s:
        a = float(s.split("[")[1].split(",")[0])
        b = float(s.split(",")[1].split("]")[0])
        value_type = env.type_manager.RealType(a, b)  # TODO: deal with bounds
    else:
        value_type = env.type_manager.UserType(s)
    return value_type


class ProtobufReader(Converter):
    @handles(unified_planning_pb2.Parameter)
    def _convert_parameter(self, msg, problem):
        # TODO: Convert parameter names into parameter types?
        return ActionParameter(msg.name, convert_type_str(msg.type, problem.env))

    @handles(unified_planning_pb2.Fluent)
    def _convert_fluent(self, msg, problem):
        value_type = convert_type_str(msg.value_type, problem.env)
        sig = []
        for p in msg.parameters:
            sig.append(
                convert_type_str(p.type, problem.env)
            )  # TODO: Ignores p.name from parameter message
        fluent = unified_planning.model.Fluent(msg.name, value_type, sig, problem.env)
        return fluent

    @handles(unified_planning_pb2.ObjectDeclaration)
    def _convert_object(self, msg, problem):
        obj = unified_planning.model.Object(
            msg.name, problem.env.type_manager.UserType(msg.type)
        )
        return obj

    @handles(unified_planning_pb2.Expression)
    def _convert_expression(self, msg, problem, param_map):
        if msg.atom is not None:
            atom = self.convert(msg.atom, problem)
            return atom  # problem.env.expression_manager.create_node(msg.kind, tuple(), atom)

        args = []
        for arg_msg in msg.args:
            args.append(self.convert(arg_msg, problem, param_map))
        payload = self.convert(msg.payload, problem, param_map)

        return problem.env.expression_manager.create_node(kind, tuple(args), payload)

    @handles(unified_planning_pb2.Atom)
    def _convert_atom(self, msg, problem):
        field = msg.WhichOneof("content")
        if field is None:
            return None

        value = getattr(msg, msg.WhichOneof("content"))
        # TODO: fix atom.value for whitespaces
        if field == "int":
            return problem.env.expression_manager.Int(value)
        elif field == "real":
            return problem.env.expression_manager.Real(value)
        elif field == "boolean":
            return problem.env.expression_manager.Bool(value)
        else:
            return problem.object(value)

    @handles(unified_planning_pb2.TypeDeclaration)
    def _convert_type_declaration(self, msg):
        if msg.type_name == "bool":
            return BoolType()
        elif msg.type_name.startswith("integer["):
            tmp = msg.type_name.split("[")[1].split("]")[0].split(", ")
            lb = None
            ub = None
            if tmp[0] != "-inf":
                lb = int(tmp[0])
            elif tmp[1] != "inf":
                ub = int(tmp[1])
            return IntType(lower_bound=lb, upper_bound=ub)
        elif msg.type_name.startswith("real["):
            tmp = msg.type_name.split("[")[1].split("]")[0].split(", ")
            lb = None
            ub = None
            if tmp[0] != "-inf":
                lb = fractions.Fraction(tmp[0])
            elif tmp[1] != "inf":
                ub = fractions.Fraction(tmp[1])
            return RealType(lower_bound=lb, upper_bound=ub)
        else:
            parent = None
            if parent != "":
                parent = UserType(msg.parent_type)
            return UserType(msg.type_name, parent)

    @handles(unified_planning_pb2.Problem)
    def _convert_problem(self, msg, problem):
        PROBLEM = Problem(name=msg.problem_name, env=problem.env)
        for obj in msg.objects:
            PROBLEM.add_object(self.convert(obj, problem))
        for f in msg.fluents:
            PROBLEM.add_fluent(self.convert(f, problem))
        for f in msg.actions:
            PROBLEM.add_action(self.convert(f, problem))
        for eff in msg.timed_effects:
            PROBLEM.add_timed_effect(self.convert(eff, problem))

        for assign in msg.initial_state:
            (fluent, value) = self.convert(assign, problem)
            PROBLEM.set_initial_value(fluent, value)

        for goal in msg.goals:
            PROBLEM.add_goal(self.convert(goal, problem))

        # TODO: add features

        return PROBLEM

    @handles(unified_planning_pb2.Assignment)
    def _convert_initial_state(self, msg, problem):
        return (self.convert(msg.fluent, problem), self.convert(msg.value, problem))

    @handles(unified_planning_pb2.Goal)
    def _convert_goal(self, msg, problem):
        goal = self.convert(msg.goal, problem)
        if msg.timing is not None:
            timing = self.convert(msg.timing)
            # TODO: deal with timed goals
            return goal
        else:
            return goal

    @handles(unified_planning_pb2.Action)
    def _convert_action(self, msg, problem):
        parameters = OrderedDict()
        conditions = {}
        effects = {}
        action: unified_planning.model.Action

        for param in msg.parameters:
            parameters[param.name] = self.convert(param, problem)

        for cond in msg.conditions:
            if cond.HasField("span"):
                conditions[self.convert(cond.span, problem)] = self.convert(
                    cond, problem
                )
            else:
                conditions.update(self.convert(cond, problem, parameters))
        for eff in msg.effects:
            if eff.HasField("occurence_time"):
                effects[
                    self.convert(eff.occurence_time, problem, parameters)
                ] = self.convert(eff.effect, problem, parameters)
            else:
                effects.update(self.convert(eff.effect, problem, parameters))

        if msg.HasField("duration"):
            action = DurativeAction(
                name=msg.name,
                parameters=parameters,
                conditions=conditions,
                effects=effects,
                duration=self.convert(msg.duration, problem),
            )
        else:
            action = unified_planning.model.InstantaneousAction(
                msg.name,
                parameters=parameters,
                conditions=conditions,
                effects=effects,
            )

        if msg.HasField("cost"):
            action.set_cost(self.convert(msg.cost, problem))

        return action

    @handles(unified_planning_pb2.EffectExpression)
    def _convert_effect(self, msg, problem, param_map):
        # EffectKind
        kind = 0
        if msg.kind == unified_planning_pb2.EffectExpression.EffectKind.Value("ASSIGN"):
            kind = ASSIGN
        elif msg.kind == unified_planning_pb2.EffectExpression.EffectKind.Value(
            "INCREASE"
        ):
            kind = INCREASE
        elif msg.kind == unified_planning_pb2.EffectExpression.EffectKind.Value(
            "DECREASE"
        ):
            kind = DECREASE

        if msg.HasField("condition"):
            return Effect(
                self.convert(msg.fluent, problem, param_map),
                self.convert(msg.value, problem, param_map),
                self.convert(msg.condition, problem, param_map),
                kind,
            )
        else:
            return Effect(
                self.convert(msg.fluent, problem, param_map),
                self.convert(msg.value, problem, param_map),
                kind,
            )

    @handles(unified_planning_pb2.TimeInterval)
    def _convert_timed_interval(self, msg):
        return unified_planning.model.TimeInterval(
            lower=self.convert(msg.lower),
            upper=self.convert(msg.upper),
            is_left_open=msg.is_left_open,
            is_right_open=msg.is_right_open,
        )

    @handles(unified_planning_pb2.Timing)
    def _convert_timing(self, msg):
        return unified_planning.model.Timing(
            delay=int(msg.delay), timepoint=self.convert(msg.timepoint)
        )

    @handles(unified_planning_pb2.Timepoint)
    def _convert_timepoint(self, msg):
        if msg.kind == unified_planning_pb2.Timepoint.TimepointKind.Value(
            "GLOBAL_START"
        ):
            return unified_planning.model.timing.Timepoint(
                kind=unified_planning.model.timing.GLOBAL_START
            )
        elif msg.kind == unified_planning_pb2.Timepoint.TimepointKind.Value(
            "GLOBAL_END"
        ):
            return unified_planning.model.timing.Timepoint(
                kind=unified_planning.model.timing.GLOBAL_END
            )
        elif msg.kind == unified_planning_pb2.Timepoint.TimepointKind.Value("START"):
            return unified_planning.model.timing.Timepoint(
                kind=unified_planning.model.timing.START
            )
        elif msg.kind == unified_planning_pb2.Timepoint.TimepointKind.Value("END"):
            return unified_planning.model.timing.Timepoint(
                kind=unified_planning.model.timing.END
            )

    @handles(unified_planning_pb2.Plan)
    def _convert_plan(self, msg, problem):
        return unified_planning.plan.SequentialPlan(
            actions=[self.convert(a, problem) for a in msg.actions]
        )

    @handles(unified_planning_pb2.ActionInstance)
    def _convert_action_instance(self, msg, problem):
        params = {}
        for param in msg.parameters:
            params[param.name] = self.convert(param, problem)
        # TODO: Get action instance parameters as user_types
        return unified_planning.plan.ActionInstance(
            problem.action(msg.action_name),
            params,
        )
