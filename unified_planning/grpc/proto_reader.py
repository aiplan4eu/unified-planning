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
from collections import OrderedDict

import unified_planning.grpc.generated.unified_planning_pb2 as unified_planning_pb2
from unified_planning.grpc.converter import Converter, handles
import unified_planning.model
import unified_planning.plan
from unified_planning.model import Timing, TimeInterval, Effect, DurativeAction, InstantaneousAction
from unified_planning.shortcuts import BoolType, UserType, RealType, IntType
from unified_planning.model.effect import ASSIGN
from unified_planning.model.effect import INCREASE
from unified_planning.model.effect import DECREASE

def convert_type_str(s, env):
    if s == 'bool':
        value_type = env.type_manager.BoolType()
    elif s == 'int':
        value_type = env.type_manager.IntType()  # TODO: deal with bounds
    elif s == 'float':
        value_type = env.type_manager.RealType()  # TODO: deal with bounds
    elif 'real' in s:
        a = float(s.split("[")[1].split(",")[0])
        b = float(s.split(",")[1].split("]")[0])
        value_type = env.type_manager.RealType(a, b)  # TODO: deal with bounds
    else:
        value_type = env.type_manager.UserType(s)
    return value_type


class ProtobufReader(Converter):
    @handles(unified_planning_pb2.Parameter)
    def _convert_parameter(self, msg, problem):
        pass

    @handles(unified_planning_pb2.Fluent)
    def _convert_fluent(self, msg, problem):
        value_type = convert_type_str(msg.value_type, problem.env)
        sig = []
        for p in msg.parameters:
            sig.append(convert_type_str(p.type))  # TODO: Ignores p.name from parameter message
        fluent = unified_planning.model.Fluent(msg.name, value_type, sig, problem.env)
        return fluent

    @handles(unified_planning_pb2.ObjectDeclaration)
    def _convert_object(self, msg, problem):
        obj = unified_planning.model.Object(msg.name, problem.env.type_manager.UserType(msg.type))
        return obj

    @handles(unified_planning_pb2.Expression)
    def _convert_expression(self, msg, problem):
        if msg.HasField('atom'):
            atom = self.convert(msg.atom, problem)
            return atom # problem.env.expression_manager.create_node(msg.kind, tuple(), atom)

        args = []
        for arg_msg in msg.list:
            args.append(self.convert(arg_msg, problem))
        kind = args[0]
        args = args[1:]

        return problem.env.expression_manager.create_node(kind.int_constant_value(), tuple(args))

    @handles(unified_planning_pb2.Atom)
    def _convert_atom(self, msg, problem):
        field = msg.WhichOneof('content')
        value = getattr(msg, field)
        if field == "int":
            return problem.env.expression_manager.Int(value)
        elif field == "real":
            return problem.env.expression_manager.Real(value)
        elif field == "boolean":
            return problem.env.expression_manager.Bool(value)
        else:
            if problem.has_object(value):
                return problem.object(value)
            return problem.env.expression_manager.FluentExp(problem.fluent(value))

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

    @handles(unified_planning_pb2.Condition)
    def _convert_condition(self, msg, problem):
        if not msg.HasField('span'):
            return self.convert(msg.cond, problem)
        else:
            return (self.convert(msg.cond, problem), self.convert(msg.span))

    @handles(unified_planning_pb2.EffectExpression)
    def _convert_effect_expression(self, msg, problem):
        return (msg.kind-1, (self.convert(msg.fluent, problem),
                             self.convert(msg.value, problem),
                             self.convert(msg.condition, problem)))

    @handles(unified_planning_pb2.Effect)
    def _convert_effect(self, msg, problem):
        if not msg.HasField('occurence_time'):
            return self.convert(msg.effect, problem)
        else:
            return (self.convert(msg.effect, problem), self.convert(msg.occurence_time))


    @handles(unified_planning_pb2.Action)
    def _convert_action(self, msg, problem):
        name = msg.name
        params = OrderedDict()
        for p in msg.parameters:
            params[p.name] = convert_type_str(p.type, env)

        if not msg.HasField("duration"):
            a = InstantaneousAction(name, params)
            for c in msg.conditions:
                cond = self.convert(c, problem)
                a.add_precondition(cond)
            for e in msg.effects:
                (kind, args) = self.convert(e, problem)
                if kind == ASSIGN:
                    a.add_effect(*args)
                elif kind == INCREASE:
                    a.add_increase_effect(*args)
                elif kind == DECREASE:
                    a.add_increase_effect(*args)

        else:
            a = DurativeAction(name, params)
            a.set_duration_constraint(self.convert(msg.duration))
            for c in msg.conditions:
                a.add_condition(self.convert(c.span), self.convert(c.cond, problem))
            for e in msg.effects:
                a.add_effect(self.convert(e.occurence_time), self.convert(e.effect, problem))
        if msg.HasField("cost"):
            a.set_cost(self.convert(msg.cost))

        return a

