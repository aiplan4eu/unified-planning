set shell := ["bash", "-cu"]
# just spawns the shell via CreateProcess, which searches System32 before PATH: on Windows a
# bare "bash" resolves to the WSL launcher rather than to Git Bash.
set windows-shell := ["cmd.exe", "/c"]

# ENHSP release the CI configuration builds; the install-enhsp action passes the same value.
enhsp_tag := "enhsp20-0.15.0"
# Extras the ubuntu test job syncs, i.e. the widest set the test suite exercises.
ci_extras := "plot tarski tamerlite pyperplan"

# List the available recipes
default:
    @just --list

# Sync the environment from uv.lock (project + default dev group)
install:
    uv sync

# `--script` keeps the helper isolated from the project environment: a plain `uv run` re-syncs
# that environment exactly, and would prune the extras setup-ci had just installed.
# Build ENHSP into .planners/enhsp-20 (needs git and a JDK; a no-op once the jar is there)
install-enhsp tag=enhsp_tag:
    uv run --script scripts/install_enhsp.py {{ tag }}

# Set up the environment as the CI test jobs do: sync the extras, then build ENHSP
setup-ci *extras=ci_extras:
    uv sync --frozen {{ prepend('--extra ', extras) }}
    just install-enhsp

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

# Check that every package and sub-package can be imported. Runs in its own environment:
# `uv run --extra` syncs inexactly, so it would add plot and tarski to .venv permanently and
# every later `just typecheck` would see a different set of packages than CI does.
check-imports:
    UV_PROJECT_ENVIRONMENT=.venv-imports uv sync --frozen --extra plot --extra tarski
    UV_PROJECT_ENVIRONMENT=.venv-imports UV_NO_SYNC=1 uv run python scripts/test_imports.py

# Fail if the installed grpc version is not the one the committed bindings were generated
# against. Plain `uv run`, not `uv run --script`: the latter does not sync the project, so
# it only finds grpc when .venv happens to be populated already — never true in CI.
check-protobuf-version:
    uv run python -c "import grpc; assert grpc.__version__ == '1.76.0', f'grpc is {grpc.__version__}, the committed bindings need 1.76.0'"

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
    rm -rf .mypy_cache .pytest_cache .ruff_cache .coverage coverage.xml dist docs/_build unified_planning.egg-info .venv-imports
