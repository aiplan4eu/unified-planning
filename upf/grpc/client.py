try:
    import grpc
    import upf.grpc.upf_pb2_grpc as upf_pb2_grpc
    from upf.grpc.factory import ProtoFactory


    class UpfGrpcClient:
        def __init__(self, host, port):
            self.host = host
            self.port = port
            self.factory = ProtoFactory()

        def __call__(self, problem):
            with grpc.insecure_channel('%s:%d' % (self.host, self.port)) as channel:
                stub = upf_pb2_grpc.UpfStub(channel)
                req = self.factory.problem2message(problem)
                self.factory.message2problem(req) # TODO: Workaround to assure that fluent map is populated

                answer = stub.plan(req)

                r = self.factory.message2plan(answer)
                return r
except ImportError:
    print("grpc module not found")
