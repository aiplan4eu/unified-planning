#!/bin/bash

# Create package files
python3 setup.py sdist --format=gztar

# Wheel file
python3 setup.py bdist_wheel
