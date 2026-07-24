set shell := ["bash", "-cu"]
# just spawns the shell via CreateProcess, which searches System32 before PATH: on Windows a
# bare "bash" resolves to the WSL launcher rather than to Git Bash.
set windows-shell := ["cmd.exe", "/c"]

# List the available recipes
default:
    @just --list

# Sync the environment from uv.lock (project + default dev group)
install:
    uv sync

# Format the code base (ruff, drop-in replacement for black)
format:
    uv run ruff format unified_planning up_test_cases scripts

# Check that the code base is correctly formatted
check-format:
    uv run ruff format --check unified_planning up_test_cases scripts

# Run the mypy type checker (configuration lives in pyproject.toml)
check-mypy:
    uv run mypy

# Fail if the installed grpc version is not the one expected for binding generation (old for wide compatibility)
check-protobuf-version:
    #!/usr/bin/env -S uv run --script
    import grpc
    assert grpc.__version__ == '1.66.2'

# Regenerate the protobuf and gRPC bindings in unified_planning/grpc/generated/
gen-protobuf: check-protobuf-version
    cd unified_planning/grpc && uv run -m grpc_tools.protoc -I. --python_out=generated/ --grpc_python_out=generated/ unified_planning.proto
    # rewrite the relative import in the gRPC module to an absolute one
    cd unified_planning/grpc && sed -i "s/import unified_planning_pb2 as unified__planning__pb2/import unified_planning.grpc.generated.unified_planning_pb2 as unified__planning__pb2/g" generated/unified_planning_pb2_grpc.py

# Run the unit tests with coverage + doctests (matches the former run_tests.sh)
run-tests target="unified_planning":
    uv run pytest \
        --cov=unified_planning --cov-report=xml \
        --doctest-modules \
        --ignore=unified_planning/grpc \
        --ignore=unified_planning/interop \
        --ignore=unified_planning/engines \
        {{ target }}

# Run the test-case report for one (or more) engines
test-engine +engine_name:
    uv run --extra engines up_test_cases/report.py {{ engine_name }}

# Build the sdist + wheel into ./dist/
build:
    uv build

# Generate the documentation
build-doc target="html":
    uv run --group docs sphinx-build -M {{ target }} docs/ docs/_build -W --keep-going

# Open the local documentation in the browser
open-doc browser="firefox":
    {{ browser }} docs/_build/html/index.html
