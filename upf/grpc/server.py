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
from concurrent import futures
import grpc

from upf.shortcuts import *
import upf.grpc.generated.upf_pb2_grpc as upf_pb2_grpc
from upf.grpc.factory import FromProtobufConverter, ToProtobufConverter


class UpfGrpcServer(upf_pb2_grpc.UpfServicer):
    def __init__(self, port):
        self.server = None
        self.port = port
        self.from_protobuf = FromProtobufConverter()
        self.to_protobuf = ToProtobufConverter()

    def plan(self, request, context):
        problem = self.from_protobuf.convert(request)

        with OneshotPlanner(name='tamer', params={'weight': 0.8}) as planner:
            plan = planner.solve(problem)
            answer = self.to_protobuf.convert(plan)
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
