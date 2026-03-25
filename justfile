

# Format the code base
format:
    uv run black --exclude=unified_planning/grpc/generated/ unified_planning/

# Check that the code base is correctly formated
check-format:
    uv run black --check --exclude=unified_planning/grpc/generated/ unified_planning/

# Run mypy linter on the code base
check-mypy:
    uv run mypy unified_planning


# Simple job that will fail if the installed grpc version is not the one expected for binding generation (old for wide compatibility)
check-protobuf-version:
    #!/usr/bin/env -S uv run --script
    import grpc
    assert grpc.__version__ == '1.66.2'

# Generate protobuf bindings
gen-protobuf: check-protobuf-version
    # generate bindings for protobuf and gRPC in the unified_planning/grpc/generated folder
    cd unified_planning/grpc && uv run -m grpc_tools.protoc -I. --python_out=generated/ --grpc_python_out=generated/ unified_planning.proto
    # change the relative import to an absolute one in the gRPC module
    cd unified_planning/grpc && sed -i "s/import unified_planning_pb2 as unified__planning__pb2/import unified_planning.grpc.generated.unified_planning_pb2 as unified__planning__pb2/g" generated/unified_planning_pb2_grpc.py

run-tests target="unified_planning/":
    uv run pytest {{ target }}

# Test one (or more) engine with report
test-engine +engine_name:
    uv run --group up --extra planners up_test_cases/report.py {{engine_name}}

# Generate the documentation
build-doc target="html":
    uv run --group docs sphinx-build -M {{target}} docs/ docs/_build -W --keep-going

# Open local documentation in the browser
open-doc browser="firefox":
    {{browser}} docs/_build/html/index.html
