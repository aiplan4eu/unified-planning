#!/bin/bash


python3 -m pytest \
  --cov=unified_planning --cov-report=xml \
  --doctest-modules --ignore=unified_planning/grpc/generated \
  unified_planning
