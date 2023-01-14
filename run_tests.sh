#!/bin/bash


python3 -m pytest \
  --cov=unified_planning --cov-report=xml \
  --doctest-modules \
  --ignore=unified_planning/grpc \
  --ignore=unified_planning/interop \
  --ignore=unified_planning/engines \
  unified_planning
