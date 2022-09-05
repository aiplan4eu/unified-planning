#!/bin/bash

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${SCRIPTS_DIR}/../

# Create package files
python3 setup.py sdist --format=gztar

# Wheel file
python3 setup.py bdist_wheel
