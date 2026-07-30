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
lint:
    uv run ruff format --check unified_planning up_test_cases scripts

# Run the mypy type checker (configuration lives in pyproject.toml)
typecheck:
    uv run mypy

# Run every check expected before pushing
check: lint typecheck

# Run all the pre-commit hooks against the whole repo
precommit:
    uv run pre-commit run --all-files --show-diff-on-failure

# Check that every package and sub-package can be imported
check-imports:
    uv run --extra plot --extra tarski python scripts/test_imports.py

# Fail if the installed grpc version is not the one the committed bindings were generated against
check-protobuf-version:
    #!/usr/bin/env -S uv run --script
    import grpc
    assert grpc.__version__ == '1.76.0'

# Regenerate the protobuf and gRPC bindings in unified_planning/grpc/generated/
gen-protobuf: check-protobuf-version
    cd unified_planning/grpc && uv run -m grpc_tools.protoc -I. --python_out=generated/ --grpc_python_out=generated/ unified_planning.proto
    # rewrite the relative import in the gRPC module to an absolute one
    cd unified_planning/grpc && sed -i "s/import unified_planning_pb2 as unified__planning__pb2/import unified_planning.grpc.generated.unified_planning_pb2 as unified__planning__pb2/g" generated/unified_planning_pb2_grpc.py

# Run the unit tests with coverage + doctests (pytest options live in pyproject.toml)
test target="unified_planning" cov_report="term-missing":
    uv run pytest --cov=unified_planning --cov-report={{ cov_report }} {{ target }}

# Run the test-case report for one (or more) engines
test-engine +engine_name:
    uv run --extra engines up_test_cases/report.py {{ engine_name }}

# Run the python snippets embedded in the documentation
test-snippets:
    uv run bash scripts/test_code_snippets.sh

# Convert the documentation notebooks to python and run them
test-colab:
    uv run --group docs bash scripts/test_colab.sh

# Build the sdist + wheel into ./dist/
build:
    uv build

# Generate the documentation
build-doc target="html":
    uv run --group docs sphinx-build -M {{ target }} docs/ docs/_build -W --keep-going

# Open the local documentation in the browser
open-doc browser="firefox":
    {{ browser }} docs/_build/html/index.html

# Remove build, cache and coverage artifacts
# docs/api is deliberately left alone: it is gitignored but holds tracked .rst files
clean:
    rm -rf .mypy_cache .pytest_cache .ruff_cache .coverage coverage.xml dist docs/_build unified_planning.egg-info
