# Copyright 2021 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""This module defines the solver interface."""

import upf
from upf.problem_kind import ProblemKind


class Solver:
    """Represents the solver interface."""

    def is_oneshot_planner(self) -> bool:
        return False

    def is_plan_validator(self) -> bool:
        return False

    def support(self, problem_kind: 'ProblemKind') -> bool:
        return len(problem_kind.features()) == 0

    def solve(self, problem: 'upf.Problem') -> 'upf.Plan':
        raise NotImplementedError

    def validate(self, problem: 'upf.Problem', plan: 'upf.Plan') -> bool:
        raise NotImplementedError

    def destroy(self):
        raise NotImplementedError
