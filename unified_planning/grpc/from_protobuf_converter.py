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
import unified_planning.grpc.generated.unified_planning_pb2 as up_pb2
from unified_planning.grpc.converter import Converter, handles
import unified_planning.model
import unified_planning.plan


class FromProtobufConverter(Converter):

    @handles(up_pb2.Fluent)
    def _convert_fluent(self, msg, problem):
        env = problem.env
        if msg.valueType == 'bool':
            value_type = env.type_manager.BoolType()
        elif msg.valueType == 'int':
            value_type = env.type_manager.IntType()  # TODO: deal with bounds
        elif msg.valueType == 'float':
            value_type = env.type_manager.RealType()  # TODO: deal with bounds
        elif 'real' in msg.valueType:
            a = float(msg.valueType.split("[")[1].split(",")[0])
            b = float(msg.valueType.split(",")[1].split("]")[0])
            value_type = env.type_manager.RealType(a, b)  # TODO: deal with bounds
        else:
            value_type = env.type_manager.UserType(msg.valueType)
        sig = []
        for s_type in msg.signature:
            sig.append(env.type_manager.UserType(s_type))  # TODO: Also here, there are the cases in wich s_type is not user-defined in principle...
        fluent = unified_planning.model.Fluent(msg.name, value_type, sig)
        return fluent

    @handles(up_pb2.Payload)
    def _convert_payload(self, msg, problem, param_map):
        p_type = msg.type
        p_data = msg.value
        if p_type == "none":
            return None
        elif p_type == "bool":
            return p_data == "True"
        elif p_type == "int":
            return int(p_data)
        elif p_type == "real":
            return float(p_data)
        elif "real" in p_type:
            return float(p_data)
        elif p_type == "fluent":
            return problem.fluent(p_data)
        elif p_type == "obj":
            return problem.object(p_data)
        elif p_type == "aparam":
            return param_map[p_data]
        else:
            return p_data

    @handles(up_pb2.Object)
    def _convert_object(self, msg, problem):
        obj = unified_planning.model.Object(msg.name, problem.env.type_manager.UserType(msg.type))
        return obj

    @handles(up_pb2.Expression)
    def _convert_expression(self, msg, problem, param_map):
        exp_type = msg.type
        args = []
        for arg_msg in msg.args:
            args.append(self.convert(arg_msg, problem, param_map))
        payload = self.convert(msg.payload, problem, param_map)
        return problem.env.expression_manager.create_node(exp_type, tuple(args), payload)

    @handles(up_pb2.Assignment)
    def _convert_assignment(self, msg, problem, param_map):
        x = self.convert(msg.x, problem, param_map)
        v = self.convert(msg.v, problem, param_map)
        return x, v

    @handles(up_pb2.Action)
    def _convert_action(self, msg, problem):
        op_name = msg.name
        op_sig = {}
        for i in range(len(msg.parameters)):
            p_name = msg.parameters[i]
            t_name = msg.parameterTypes[i]
            if t_name not in problem.user_types().keys():
                raise ValueError("Unknown type: " + msg.signatures[i])
            op_sig[p_name] = problem.user_type(t_name) # TODO: deal with non user-defined types

        op_up = unified_planning.model.InstantaneousAction(op_name, **op_sig)
        op_params = {}
        for k in op_sig.keys():
            op_params[k] = op_up.parameter(k)

        for pre in msg.preconditions:
            op_up.add_precondition(self.convert(pre, problem, op_params))

        for eff in msg.effects:
            fluent, value = self.convert(eff, problem, op_params)
            op_up.add_effect(fluent, value)
        return op_up

    @handles(up_pb2.Problem)
    def _convert_problem(self, msg, env=None):
        problem = unified_planning.model.Problem(msg.name, env)
        for fluent in msg.fluents:
            problem.add_fluent(self.convert(fluent, problem))

        for obj in msg.objects:
            problem.add_object(self.convert(obj, problem))

        for action in msg.actions:
            problem.add_action(self.convert(action, problem))

        for sva in msg.initialState:
            fluent, value = self.convert(sva, problem, {})
            problem.set_initial_value(fluent, value)

        for m_goal in msg.goals:
            goal = self.convert(m_goal, problem, {})
            problem.add_goal(goal)

        return problem

    @handles(up_pb2.ActionInstance)
    def _convert_action_instance(self, msg, problem):
        a = self.convert(msg.action, problem)
        ps = tuple([self.convert(p, problem, {}) for p in msg.parameters])
        return unified_planning.plan.ActionInstance(a, ps)

    @handles(up_pb2.Answer)
    def _convert_plan(self, msg, problem):
        if msg.status > 0:
            return None
        else:
            ais = [self.convert(ai, problem) for ai in msg.plan.actions]
            return unified_planning.plan.SequentialPlan(ais)
