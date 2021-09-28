from concurrent import futures
import grpc

from upf.shortcuts import *
import upf.grpc.upf_pb2_grpc as upf_pb2_grpc
from upf.grpc.factory import ProtoFactory

class UpfGrpcServer(upf_pb2_grpc.UpfServicer):
    def __init__(self, port):
        self.server = None
        self.port = port
        self.factory = ProtoFactory()

    def plan(self, request, context):
        problem = self.factory.message2problem(request)
        
        with OneshotPlanner(name='tamer', params={'weight': 0.8}) as planner:
            plan = planner.solve(problem)
            answer = self.factory.plan2message(plan)
            return answer
        return None

    def start(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        upf_pb2_grpc.add_UpfServicer_to_server(
            self, self.server)
        self.server.add_insecure_port('0.0.0.0:%d' % self.port)
        self.server.start()

    def wait_for_termination(self):
        self.server.wait_for_termination()
