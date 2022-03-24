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
from unified_planning.grpc.converter import Converter, handles
import unified_planning.model
import unified_planning.plan
from unified_planning.model import Timing, TimeInterval, Effect
from unified_planning.shortcuts import BoolType, UserType, RealType, IntType

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
    def _convert_expression(self, msg, problem, param_map):
        if msg.atom is not None:
            atom = self.convert(msg.atom, problem)
            return atom # problem.env.expression_manager.create_node(msg.kind, tuple(), atom)

        args = []
        for arg_msg in msg.args:
            args.append(self.convert(arg_msg, problem, param_map))
        payload = self.convert(msg.payload, problem, param_map)

        return problem.env.expression_manager.create_node(kind, tuple(args), payload)

    @handles(unified_planning_pb2.Atom)
    def _convert_atom(self, msg, problem):
        field = msg.WhichOneof('content')
        value = getattr(msg, msg.WhichOneof('content'))
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
            if msg.parent_type is not None:
                parent = UserType(msg.parent_type)
            return UserType(msg.type_name, parent)



    # @handles(unified_planning_pb2.Payload)
    # def _convert_payload(self, msg, problem, param_map):
    #     p_type = msg.type
    #     p_data = msg.value
    #     if p_type == "none":
    #         return None
    #     elif p_type == "bool":
    #         return p_data == "True"
    #     elif p_type == "int":
    #         return int(p_data)
    #     elif p_type == "real":
    #         return float(p_data)
    #     elif "real" in p_type:
    #         return float(p_data)
    #     elif p_type == "fluent":
    #         return problem.fluent(p_data)
    #     elif p_type == "obj":
    #         return problem.object(p_data)
    #     elif p_type == "aparam":
    #         return param_map[p_data]
    #     else:
    #         return p_data

    # @handles(unified_planning_pb2.Assignment)
    # def _convert_assignment(self, msg, problem, param_map):
    #     x = self.convert(msg.x, problem, param_map)
    #     v = self.convert(msg.v, problem, param_map)
    #     return x, v
    #
    # @handles(unified_planning_pb2.InstantaneousAction)
    # def _convert_instantaneous_action(self, msg, problem):
    #     op_name = msg.name
    #     op_sig = {}
    #     for i in range(len(msg.parameters)):
    #         p_name = msg.parameters[i].name
    #         t_name = msg.parameters[i].typename
    #         if t_name not in problem.user_types().keys():
    #             raise ValueError("Unknown type: " + msg.signatures[i])
    #         op_sig[p_name] = problem.user_type(t_name) # TODO: deal with non user-defined types
    #
    #     op_unified_planning = unified_planning.model.InstantaneousAction(op_name, **op_sig)
    #     op_params = {}
    #     for k in op_sig.keys():
    #         op_params[k] = op_unified_planning.parameter(k)
    #
    #     for pre in msg.preconditions:
    #         op_unified_planning.add_precondition(self.convert(pre, problem, op_params))
    #
    #     for eff in msg.effects:
    #         fluent, value = self.convert(eff, problem, op_params)
    #         op_unified_planning.add_effect(fluent, value)
    #     return op_unified_planning
    #
    # @handles(unified_planning_pb2.TimedEffect)
    # def _convert_timed_effect(self, msg, problem):
    #     timing = self.convert(msg.timing, problem)
    #     effect = self.convert(msg.effect, problem)
    #     return timing, effect
    #
    # @handles(unified_planning_pb2.DurativeAction)
    # def _convert_durative_action(self, msg, problem):
    #     op_name = msg.name
    #     op_sig = {}
    #     for i in range(len(msg.parameters)):
    #         p_name = msg.parameters[i].name
    #         t_name = msg.parameters[i].typename
    #         if t_name not in problem.user_types().keys():
    #             raise ValueError("Unknown type: " + msg.signatures[i])
    #         op_sig[p_name] = problem.user_type(t_name) # TODO: deal with non user-defined types
    #     op_params = {}
    #     op_unified_planning = unified_planning.model.DurativeAction(op_name, **op_sig)
    #     for k in op_sig.keys():
    #         op_params[k] = op_unified_planning.parameter(k)
    #     op_unified_planning._duration = self.convert(msg.duration)
    #
    #     for con in msg.conditions:
    #         op_unified_planning.add_condition(self.convert(con))
    #
    #     for dc in msg.durativeConditions:
    #         op_unified_planning.add_durative_condition(self.convert(dc))
    #
    #     for eff in msg.effects:
    #         timing, effect = self.convert(eff)
    #         op_unified_planning.add_effect(timing, effect.fluent(), effect.value(), effect.condition())
    #
    #     return op_unified_planning
    #
    # @handles(unified_planning_pb2.Effect)
    # def _convert_fraction(self, msg, env=None):
    #     Effect(self.convert(msg.fluent), self.convert(msg.value), self.convert(msg.condition), msg.kind)
    #
    # @handles(unified_planning_pb2.Fraction)
    # def _convert_fraction(self, msg, env=None):
    #     fractions.Fraction(msg.n, msg.d)
    #
    # @handles(unified_planning_pb2.Timing)
    # def _convert_timing(self, msg, env=None):
    #     Timing(self.convert(msg.bound), msg.isFromStart)
    #
    # @handles(unified_planning_pb2.IntervalDuration)
    # def _convert_interval(self, msg, env=None):
    #     TimeInterval(self.convert(msg.lower), self.convert(msg.upper), msg.isLeftOpen, msg.isRightOpen)
    #
    # @handles(unified_planning_pb2.Interval)
    # def _convert_interval(self, msg, env=None):
    #     TimeInterval(self.convert(msg.lower), self.convert(msg.upper), msg.isLeftOpen, msg.isRightOpen)
    #
    # @handles(unified_planning_pb2.Problem)
    # def _convert_problem(self, msg, env=None):
    #     initial_defaults = [(m.typename, self.convert(m.default)) for m in msg.initialDefaults]
    #     fluents_defaults = [(self.convert(m.fluent), self.convert(m.default)) for m in msg.fluentDefaults]
    #
    #     problem = unified_planning.model.Problem(msg.name, env, initial_defaults, fluents_defaults)
    #     for fluent in msg.fluents:
    #         problem.add_fluent(self.convert(fluent, problem))
    #
    #     for obj in msg.objects:
    #         problem.add_object(self.convert(obj, problem))
    #
    #     for action in msg.actions:
    #         problem.add_action(self.convert(action, problem))
    #
    #     for sva in msg.initialState:
    #         fluent, value = self.convert(sva, problem, {})
    #         problem.set_initial_value(fluent, value)
    #
    #     for m_goal in msg.goals:
    #         goal = self.convert(m_goal, problem, {})
    #         problem.add_goal(goal)
    #
    #     durative_actions = [self.convert(a) for a in msg.durativeActions]
    #     for a in durative_actions:
    #         problem.add_action(a)
    #
    #     for x in msg.timedEffects:
    #         problem.add_timed_effect(self.convert(x.timing), self.convert(x.effect))
    #     for x in msg.timedGoals:
    #         problem.add_timed_goal(self.convert(x.timing), self.convert(x.condition))
    #     for x in msg.maintainGoals:
    #         problem.add_maintain_goal(self.convert(x.interval), self.convert(x.condition))
    #
    #     return problem
    #
    # @handles(unified_planning_pb2.ActionInstance)
    # def _convert_action_instance(self, msg, problem):
    #     a = self.convert(msg.action, problem)
    #     ps = tuple([self.convert(p, problem, {}) for p in msg.parameters])
    #     return unified_planning.plan.ActionInstance(a, ps)
    #
    # @handles(unified_planning_pb2.Answer)
    # def _convert_plan(self, msg, problem):
    #     if msg.status > 0:
    #         return None
    #     else:
    #         ais = [self.convert(ai, problem) for ai in msg.plan.actions]
    #         return unified_planning.plan.SequentialPlan(ais)