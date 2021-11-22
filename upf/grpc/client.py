import grpc
import upf.grpc.generated.upf_pb2_grpc as upf_pb2_grpc
from upf.grpc.factory import FromProtobufConverter, ToProtobufConverter


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
            self.from_protobuf.convert(req) # TODO: Workaround to assure that fluent map is populated

            answer = stub.plan(req)

            r = self.from_protobuf.convert(answer)
            return r
