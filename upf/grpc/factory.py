from concurrent import futures
import time
import math
import logging

import grpc

import upf.grpc.upf_pb2 as upf_pb2
import upf.grpc.upf_pb2_grpc as upf_pb2_grpc

import upf
from upf.shortcuts import *
from upf.plan import ActionInstance
from upf.plan import SequentialPlan
from upf.expression import ExpressionManager

from upf.test.examples import get_example_problems


class ProtoFactory:
    def __init__(self):
        self.p_env = None
        self.fluent_map = {}
        self.type_map = {}
        self.object_map = {}

    def message2fluent(self, msg):
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
        fluent = upf.Fluent(msg.name, value_type, sig)
        self.fluent_map[fluent.name()] = fluent
        return fluent

    def fluent2message(self, fluent):
        name = fluent.name()
        sig = [str(t) for t in fluent.signature()]
        valType = str(fluent.type())
        return upf_pb2.Fluent(name=name, valueType=valType, signature=sig)

    def fluents2message(self, fluents):
        return [self.fluent2message(f) for f in fluents]

    def message2payload(self, msg, param_map):
        type = msg.type
        data = msg.value
        if type == "none":
            return None
        elif type == "bool":
            return data == "True"
        elif type == "int":
            return int(data)
        elif type == "real":
            return float(data)
        elif "real" in type:
            return float(data)
        elif type == "fluent":
            return self.fluent_map[data]
        elif type == "obj":
            return self.object_map[data]
        elif type == "aparam":
            return param_map[data]
        else:
            return data


    def payload2message(self, payload):
        value = None
        if payload is None:
            type = "none"
            value = "-"
        elif isinstance(payload, bool):
            type = "bool"
        elif isinstance(payload, int):
            type = "int"
        elif isinstance(payload, float):
            type = "real"
        elif isinstance(payload, upf.Fluent):
            type = "fluent"
            value = payload.name()
        elif isinstance(payload, upf.Object):
            type = "obj"
            value = payload.name()
        elif isinstance(payload, upf.ActionParameter):
            type = "aparam"
            value = payload.name()
        else:
            type = "str"
        if value is None:
            value = str(payload)

        return upf_pb2.Payload(type=type, value=value)


    def message2object(self, msg):
        obj = upf.Object(msg.name, self.type_map[msg.type])
        self.object_map[msg.name] = obj
        return obj


    def object2message(self, obj):
        return upf_pb2.Object(name=obj.name(), type=obj.type().name())


    def message2expression(self, msg, param_map):
        expType = msg.type
        args = []
        for argMsg in msg.args:
            args.append(self.message2expression(argMsg, param_map))
        payload = self.message2payload(msg.payload, param_map)
        return self.p_env.expression_manager.create_node(expType, tuple(args), payload)


    def expression2message(self, exp):
        return upf_pb2.Expression(
            type=exp._content.node_type,
            args=[self.expression2message(a) for a in exp._content.args],
            payload=self.payload2message(exp._content.payload)
        )


    def message2assignment(self, msg, param_map):
        x = self.message2expression(msg.x, param_map)
        v = self.message2expression(msg.v, param_map)
        return (x, v)

    def assignment2message(self, x, v):
        return upf_pb2.Assignment(
            x=self.expression2message(x),
            v=self.expression2message(v)
        )

    def message2action(self, msg):
        op_name = msg.name
        op_sig = {}
        for i in range(len(msg.parameters)):
            p_name = msg.parameters[i]
            t_name = msg.parameterTypes[i]
            if t_name not in self.type_map.keys():
                raise ValueError("Unknown type: " + msg.signatures[i])
            op_sig[p_name] = self.type_map[t_name]

        op_upf = upf.Action(op_name, **op_sig)
        op_params = {}
        for k in op_sig.keys():
            op_params[k] = op_upf.parameter(k)

        for pre in msg.preconditions:
            op_upf.add_precondition(self.message2expression(pre, op_params))

        for eff in msg.effects:
            fluent, value = self.message2assignment(eff, op_params)
            op_upf.add_effect(fluent, value)
        return op_upf

    def action2message(self, a):
        return upf_pb2.Action(
            name=a.name(),
            parameters=[p.name() for p in a.parameters()],
            parameterTypes=[p.type().name() for p in a.parameters()],
            preconditions=[self.expression2message(p) for p in a.preconditions()],
            effects=[self.assignment2message(*t) for t in a.effects()]
        )

    def message2problem(self, msg):
        problem = upf.Problem(msg.name)
        self.p_env = problem.env
        for fluent in msg.fluents:
            problem.add_fluent(self.message2fluent(fluent))

        for obj in msg.objects:
            problem.add_object(self.message2object(obj))

        for action in msg.actions:
            problem.add_action(self.message2action(action))

        for sva in msg.initialState:
            fluent, value = self.message2assignment(sva, {})
            problem.set_initial_value(fluent, value)

        for m_goal in msg.goals:
            goal = self.message2expression(m_goal, {})
            problem.add_goal(goal)

        return problem

    def problem2message(self, p):
        objs = []
        for t in p.user_types().keys():
            for o in p.objects(p.user_types()[t]):
                objs.append(o)

        return upf_pb2.Problem(
            name=p.name(),
            fluents=[self.fluent2message(p.fluent(f)) for f in p.fluents()],
            objects=[self.object2message(o) for o in objs],
            actions=[self.action2message(p.action(a)) for a in p.actions()],
            initialState=[self.assignment2message(x, p.initial_value(x)) for x in p.initial_values().keys()],
            goals=[self.expression2message(g) for g in p.goals()]
        )

    def action_instance2msg(self, ai):
        a_msg = self.action2message(ai.action())
        p_msg = [self.expression2message(p) for p in ai.parameters()]
        return upf_pb2.ActionInstance(action=a_msg, parameters=p_msg)

    def plan2message(self, p):
        if p is None:
            return upf_pb2.Answer(status=1, plan=[])
        else:
            ai_msgs = [self.action_instance2msg(ai) for ai in p.actions()]
            r = upf_pb2.Answer(status=0, plan=upf_pb2.SequentialPlan(actions=ai_msgs))
            return r

    def message2action_instance(self, m):
        a = self.message2action(m.action)
        ps = [self.message2expression(p, {}) for p in m.parameters]
        return ActionInstance(a, ps)

    def message2plan(self, p):
        if p.status > 0:
            return None
        else:
            ais = [self.message2action_instance(m) for m in p.plan.actions]
            return SequentialPlan(ais)
