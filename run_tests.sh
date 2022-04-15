#!/bin/bash

python3 -m pytest -x --cov=unified_planning --cov-report=xml unified_planning/test
