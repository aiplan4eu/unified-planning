#!/bin/bash


python3.11 -m pytest \
  --cov=unified_planning --cov-report term-missing\
  --doctest-modules \
  --ignore=unified_planning/grpc \
  --ignore=unified_planning/interop \
  --ignore=unified_planning/engines \
  unified_planning
