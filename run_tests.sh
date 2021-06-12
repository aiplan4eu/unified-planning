#!/bin/bash

python3 -m pytest --cov=upf --cov-report=xml -x upf/test
