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
import grpc
import upf.grpc.generated.upf_pb2_grpc as upf_pb2_grpc
from upf.grpc.from_protobuf_converter import FromProtobufConverter
from upf.grpc.to_protobuf_converter import ToProtobufConverter


class UpfGrpcClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.from_protobuf = FromProtobufConverter()
        self.to_protobuf = ToProtobufConverter()

    def __call__(self, problem):
        with grpc.insecure_channel('%s:%d' % (self.host, self.port)) as channel:
            stub = upf_pb2_grpc.UpfStub(channel)
            req = self.to_protobuf.convert(problem)

            answer = stub.plan(req)

            r = self.from_protobuf.convert(answer, problem)
            return r
