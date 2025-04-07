

# Format the code base
format:
    python3 -m black --exclude=unified_planning/grpc/generated/ .

# Check that the code base is correctly formated
check-format:
    python3 -m black --check --exclude=unified_planning/grpc/generated/ .

# Run mypy linter on the code base
check-mypy:
    python3 -m mypy unified_planning


# Simple job that will fail if the installed grpc version is not the one expected for binding generation (old for wide compatibility)
check-protobuf-version:
    #!/usr/bin/env python
    import grpc
    assert grpc.__version__ == '1.66.2'

# Generate protobuf bindings
gen-protobuf: check-protobuf-version
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
    uv pip install .
