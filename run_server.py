from unified_planning.grpc.server import UpGrpcServer


def __main__(self, port):
    server = UpGrpcServer(port)
    server.start()
    server.wait_for_termination()


__main__(8061)
