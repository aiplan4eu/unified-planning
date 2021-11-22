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
import upf.grpc.generated.upf_pb2 as upf_pb2
import upf.model
from upf.shortcuts import *
import upf.plan


class handles:
    def __init__(self, *what):
        self.what = what

    def __call__(self, func):
        func._what = self.what
        return func


class Converter:
    def __init__(self):
        self.functions = {}
        for k in dir(self):
            v = getattr(self, k)
            if hasattr(v, "_what"):
                for x in v._what:
                    self.functions[x] = v

    def convert(self, element):
        raise NotImplementedError


class ToProtobufConverter(Converter):

    def convert(self, element):
        f = self.functions[type(element)]
        return f(element)

    @handles(upf.model.Fluent)
    def _convert_fluent(self, fluent):
        name = fluent.name()
        sig = [str(t) for t in fluent.signature()]
        valType = str(fluent.type())
        return upf_pb2.Fluent(name=name, valueType=valType, signature=sig)

    @handles(upf.model.Object)
    def _convert_object(self, obj):
        return upf_pb2.Object(name=obj.name(), type=obj.type().name())

    @handles(upf.model.fnode.FNode)
    def _convert_expression(self, exp):
        payload = exp._content.payload
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
        elif isinstance(payload, upf.model.Fluent):
            p_type = "fluent"
            value = payload.name()
        elif isinstance(payload, upf.model.Object):
            p_type = "obj"
            value = payload.name()
        elif isinstance(payload, upf.model.ActionParameter):
            p_type = "aparam"
            value = payload.name()
        else:
            p_type = "str"
        if value is None:
            value = str(payload)
        return upf_pb2.Expression(
            type=exp._content.node_type,
            args=[self.convert(a) for a in exp._content.args],
            payload=upf_pb2.Payload(type=p_type, value=value)
        )

    @handles(upf.model.Effect)
    def _convert_effect(self, effect):
        x = effect.fluent()
        v = effect.value()
        return upf_pb2.Assignment(x=self.convert(x), v=self.convert(v))

    @handles(upf.model.InstantaneousAction)
    def _convert_instantaneous_action(self, a):
        return upf_pb2.Action(
            name=a.name(),
            parameters=[p.name() for p in a.parameters()],
            parameterTypes=[p.type().name() for p in a.parameters()],
            preconditions=[self.convert(p) for p in a.preconditions()],
            effects=[self.convert(t) for t in a.effects()]
        )

    @handles(upf.model.Problem)
    def _convert_problem(self, p):
        objs = []
        for t in p.user_types().keys():
            for o in p.objects(p.user_types()[t]):
                objs.append(o)

        t = p.env.expression_manager.TRUE()

        return upf_pb2.Problem(
            name=p.name(),
            fluents=[self.convert(p.fluent(f)) for f in p.fluents()],
            objects=[self.convert(o) for o in objs],
            actions=[self.convert(p.action(a)) for a in p.actions()],
            initialState=[self.convert(upf.model.Effect(x, v, t)) for x, v in p.initial_values().items()],
            goals=[self.convert(g) for g in p.goals()]
        )

    @handles(upf.plan.ActionInstance)
    def _convert_action_instance(self, ai):
        a_msg = self.convert(ai.action())
        p_msg = [self.convert(p) for p in ai.actual_parameters()]
        return upf_pb2.ActionInstance(action=a_msg, parameters=p_msg)

    @handles(upf.plan.SequentialPlan, type(None))
    def _convert_sequential_plan(self, p):
        if p is None:
            return upf_pb2.Answer(status=1, plan=[])
        else:
            ai_msgs = [self.convert(ai) for ai in p.actions()]
            r = upf_pb2.Answer(status=0, plan=upf_pb2.SequentialPlan(actions=ai_msgs))
            return r


class FromProtobufConverter(Converter):
    def __init__(self):
        Converter.__init__(self)
        self.p_env = None
        self.fluent_map = {}
        self.type_map = {}
        self.object_map = {}

    def convert(self, element, *args):
        f = self.functions[str(element.DESCRIPTOR.name)]
        return f(element, *args)

    @handles('Fluent')
    def _convert_fluent(self, msg):
        if msg.valueType == 'bool':
            value_type = self.type_map.setdefault(msg.valueType, self.p_env.type_manager.BoolType())
        elif msg.valueType == 'int':
            value_type = self.type_map.setdefault(msg.valueType, self.p_env.type_manager.IntType())  # TODO: deal with bounds
        elif msg.valueType == 'float':
            value_type = self.type_map.setdefault(msg.valueType, self.p_env.type_manager.RealType())  # TODO: deal with bounds
        elif 'real' in msg.valueType:
            a = float(msg.valueType.split("[")[1].split(",")[0])
            b = float(msg.valueType.split(",")[1].split("]")[0])
            value_type = self.type_map.setdefault(msg.valueType, self.p_env.type_manager.RealType(a, b))  # TODO: deal with bounds
        else:
            value_type = self.type_map.setdefault(msg.valueType, UserType(msg.valueType))
        sig = []
        for s_type in msg.signature:
            sig.append(self.type_map.setdefault(s_type, UserType(
                s_type)))  # TODO: Also here, there are the cases in wich s_type is not user-defined in principle...
        fluent = upf.model.Fluent(msg.name, value_type, sig)
        self.fluent_map[fluent.name()] = fluent
        return fluent

    @handles('Payload')
    def _convert_payload(self, msg, param_map):
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
            return self.fluent_map[p_data]
        elif p_type == "obj":
            return self.object_map[p_data]
        elif p_type == "aparam":
            return param_map[p_data]
        else:
            return p_data

    @handles('Object')
    def _convert_object(self, msg):
        obj = upf.model.Object(msg.name, self.type_map[msg.type])
        self.object_map[msg.name] = obj
        return obj

    @handles('Expression')
    def _convert_expression(self, msg, param_map):
        exp_type = msg.type
        args = []
        for arg_msg in msg.args:
            args.append(self.convert(arg_msg, param_map))
        payload = self.convert(msg.payload, param_map)
        return self.p_env.expression_manager.create_node(exp_type, tuple(args), payload)

    @handles('Assignment')
    def _convert_assignment(self, msg, param_map):
        x = self.convert(msg.x, param_map)
        v = self.convert(msg.v, param_map)
        return x, v

    @handles('Action')
    def _convert_action(self, msg):
        op_name = msg.name
        op_sig = {}
        for i in range(len(msg.parameters)):
            p_name = msg.parameters[i]
            t_name = msg.parameterTypes[i]
            if t_name not in self.type_map.keys():
                raise ValueError("Unknown type: " + msg.signatures[i])
            op_sig[p_name] = self.type_map[t_name]

        op_upf = upf.model.InstantaneousAction(op_name, **op_sig)
        op_params = {}
        for k in op_sig.keys():
            op_params[k] = op_upf.parameter(k)

        for pre in msg.preconditions:
            op_upf.add_precondition(self.convert(pre, op_params))

        for eff in msg.effects:
            fluent, value = self.convert(eff, op_params)
            op_upf.add_effect(fluent, value)
        return op_upf

    @handles('Problem')
    def _convert_problem(self, msg):
        problem = upf.model.Problem(msg.name)
        self.p_env = problem.env
        for fluent in msg.fluents:
            problem.add_fluent(self.convert(fluent))

        for obj in msg.objects:
            problem.add_object(self.convert(obj))

        for action in msg.actions:
            problem.add_action(self.convert(action))

        for sva in msg.initialState:
            fluent, value = self.convert(sva, {})
            problem.set_initial_value(fluent, value)

        for m_goal in msg.goals:
            goal = self.convert(m_goal, {})
            problem.add_goal(goal)

        return problem

    @handles('ActionInstance')
    def _convert_action_instance(self, m):
        a = self.convert(m.action)
        ps = tuple([self.convert(p, {}) for p in m.parameters])
        return upf.plan.ActionInstance(a, ps)

    @handles('Answer')
    def _convert_plan(self, p):
        if p.status > 0:
            return None
        else:
            ais = [self.convert(m) for m in p.plan.actions]
            return upf.plan.SequentialPlan(ais)
