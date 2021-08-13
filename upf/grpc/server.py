from concurrent import futures
import time
import math
import logging

import grpc

import upf_pb2
import upf_pb2_grpc

import upf
from upf.shortcuts import *
from upf.expression import ExpressionManager

from upf.pb_factory import message2problem


class UpfServicer(upf_pb2_grpc.UpfServicer):
    def __init__(self, port):
        self.port = port

    def Plan(self, request, context):
        problem = message2problem(request)
        
        with OneshotPlanner(name='tamer', params={'weight': 0.8}) as planner:
            plan = planner.solve(problem)

        result = upf_pb2.SequentialPlan(status=0, result=action_list)
        return result

    def start(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        upf_pb2_grpc.add_UpfServicer_to_server(
            self, self.server)
        self.server.add_insecure_port('0.0.0.0:%d' % (self.port))
        self.server.start()

    def wait_for_termination(self):
        self.server.wait_for_termination()
