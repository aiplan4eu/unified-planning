

# Format the code base
format:
    python3 -m black --exclude=unified_planning/grpc/generated/ .

# Check that the code base is correctly formated
check-format:
    python3 -m black --check --exclude=unified_planning/grpc/generated/ .

# Run mypy linter on the code base
check-mypy:
    python3 -m mypy unified_planning

# Generate protobuf bindings
gen-protobuf:
    pip show grpcio-tools | grep "Version: 1.54.2"  # Check installed version for reproducibility
    bash scripts/generate_protobuf_bindings.sh

# Test one (or more) engine with report
test-engine +engine_name:
    python3 up_test_cases/report.py {{engine_name}}

# Generate the documentation
build-doc target="html":
    pip install -r docs/requirements.txt
    sphinx-build -M {{target}} docs/ docs/_build -W --keep-going

# Open local documentation in the browser
open-doc browser="firefox":
    {{browser}} docs/_build/html/index.html

# Install unified-planning from sources
install:
    pip install .