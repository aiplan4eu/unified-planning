#!/bin/bash

# This script will generate the protobuf bindings based on the `unified_planning.proto` file.

set -e

cd unified_planning/grpc/

echo "Generating python bindings with protoc"
python3 -m grpc_tools.protoc --version

# generate bindings for protobuf and gRPC in the unified_planning/grpc/generated folder
python3 -m grpc_tools.protoc -I. --python_out=generated/ --grpc_python_out=generated/ unified_planning.proto

# change the relative import to an absolute one in the gRPC module
sed -i "s/import unified_planning_pb2 as unified__planning__pb2/import unified_planning.grpc.generated.unified_planning_pb2 as unified__planning__pb2/g" generated/unified_planning_pb2_grpc.py