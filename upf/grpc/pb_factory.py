from concurrent import futures
import time
import math
import logging

import grpc

import upf.grpc.upf_pb2 as upf_pb2
import upf.grpc.upf_pb2_grpc as upf_pb2_grpc


import upf
from upf.shortcuts import *
from upf.expression import ExpressionManager

from upf.test.examples import get_example_problems

def message2fluent( msg, fluent_map, type_map, p_env):
    if msg.valueType == 'bool':
        value_type = type_map.setdefault(msg.valueType, p_env.type_manager.BoolType())
    elif msg.valueType == 'int':   
        value_type = type_map.setdefault(msg.valueType, p_env.type_manager.IntType()) #TODO: deal with bounds
    elif msg.valueType == 'float':
        value_type = type_map.setdefault(msg.valueType, p_env.type_manager.RealType()) #TODO: deal with bounds
    elif 'real' in msg.valueType:
        print(msg.valueType)
        a = float(msg.valueType.split("[")[1].split(",")[0])
        b = float(msg.valueType.split(",")[1].split("]")[0])
        value_type = type_map.setdefault(msg.valueType, p_env.type_manager.RealType(a,b)) #TODO: deal with bounds    
    else:
        value_type = type_map.setdefault(msg.valueType, UserType(msg.valueType))
    sig = []
    for s_type in msg.signature:
        sig.append(type_map.setdefault(s_type, UserType(s_type))) #TODO: Also here, there are the cases in wich s_type is not user-defined in principle...
    fluent = upf.Fluent(msg.name, value_type, sig)
    fluent_map[fluent.name()] = fluent
    return fluent

def fluent2message( fluent ):
    name = fluent.name()
    sig = [ str(t) for t in fluent.signature()  ]
    valType = str(fluent.type())
    return upf_pb2.Fluent(name=name, valueType=valType, signature=sig)

def fluents2message( fluents ):
    return [ fluent2message(f) for f in fluents ]

def message2payload( msg, fluent_map, obj_map, param_map ):
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
        return fluent_map[data]
    elif type == "obj":
        print(obj_map)
        print("Fetching:", data, obj_map[data])
        return obj_map[data]
    elif type == "aparam":
        print(param_map)
        print("Fetching:", data, param_map[data])
        return param_map[data]
    else:
        return data

def payload2message( payload ):
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

def message2object( msg, object_map, type_map ):
    obj = upf.Object(msg.name, type_map[msg.type])
    object_map[msg.name] = obj
    return obj

def object2message( obj ):
    return upf_pb2.Object(name=obj.name(), type=obj.type().name())

def message2expression( msg, fluent_map, obj_map, param_map, p_env ):
    expType = msg.type
    args = []
    for argMsg in msg.args:
        args.append(message2expression(argMsg, fluent_map, obj_map, param_map, p_env))
    payload = message2payload(msg.payload, fluent_map, obj_map, param_map)
    return p_env.expression_manager.create_node(expType, tuple(args), payload)

def expression2message( exp ):
    return upf_pb2.Expression(
        type = exp._content.node_type,
        args = [expression2message(a) for a in exp._content.args],
        payload = payload2message(exp._content.payload)
    )

def message2assignment( msg, fluent_map, obj_map, param_map, p_env ):
    x = message2expression(msg.x, fluent_map, obj_map, param_map, p_env )
    v = message2expression(msg.v, fluent_map, obj_map, param_map, p_env )
    return (x, v)

def assignment2message( x, v ):
    return upf_pb2.Assignment(
        x=expression2message(x),
        v=expression2message(v)
    )

def message2action( msg, fluent_map, object_map, type_map, p_env ):
    op_name = msg.name
    op_sig = {}
    for i in range(len(msg.parameters)):
        p_name = msg.parameters[i]
        t_name = msg.parameterTypes[i]
        if t_name not in type_map.keys():
            raise ValueError("Unknown type: " + msg.signatures[i])
        op_sig[p_name] = type_map[t_name]
    
    op_upf = upf.Action(op_name, **op_sig)
    op_params = {}
    for k in op_sig.keys():
        op_params[k] = op_upf.parameter(k)

    for pre in msg.preconditions:
        op_upf.add_precondition(message2expression(pre, fluent_map, object_map, op_params, p_env))

    for eff in msg.effects:
        fluent, value = message2assignment(eff, fluent_map, object_map, op_params, p_env)
        op_upf.add_effect(fluent, value)
    return op_upf

def action2message( a ):
    return upf_pb2.Action(
        name = a.name(),
        parameters = [ p.name() for p in a.parameters() ],
        parameterTypes = [ p.type().name() for p in a.parameters() ],
        preconditions = [ expression2message(p) for p in a.preconditions() ],
        effects = [ assignment2message(*t) for t in a.effects() ]
    )

def message2problem(msg):
    problem = upf.Problem(msg.name)
    fluent_map = {}
    type_map = {}
    object_map = {}
    for fluent in msg.fluents:
        problem.add_fluent(message2fluent(fluent, fluent_map, type_map, problem.env))

    for object in msg.objects:
        problem.add_object(message2object(object, object_map, type_map))

    for action in msg.actions:
        problem.add_action(message2action(action, fluent_map, object_map, type_map, problem.env))

    for sva in msg.initialState:
        fluent, value = message2assignment(sva, fluent_map, object_map, {}, problem.env)
        problem.set_initial_value(fluent, value)

    for m_goal in msg.goals:
        goal = message2expression(m_goal, fluent_map, object_map, {}, problem.env)
        problem.add_goal(goal)

    return problem

def problem2message(p):
    objs = []
    for t in p.user_types().keys():
        for o in p.objects(p.user_types()[t]):
            objs.append(o)

    return upf_pb2.Problem(
        name = p.name(),
        fluents = [ fluent2message(p.fluent(f)) for f in p.fluents() ],
        objects = [ object2message(o) for o in objs ],
        actions = [ action2message(p.action(a)) for a in p.actions() ],
        initialState = [ assignment2message(x, p.initial_value(x)) for x in p.initial_values().keys() ],
        goals = [ expression2message(g) for g in p.goals() ]
    )

