from upf.grpc.server import UpfGrpcServer


def __main__(self, port):
    server = UpfGrpcServer(port)
    server.start()
    server.wait_for_termination()


__main__(8061)
