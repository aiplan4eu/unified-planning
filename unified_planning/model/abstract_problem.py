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
"""This module defines an abstract problem class."""

import unified_planning as up
from typing import Optional


class AbstractProblem:
    """This is an abstract class that represents a generic planning problem"""

    def __init__(self, name: str = None, env: "up.environment.Environment" = None):
        self._env = up.environment.get_env(env)
        self._name = name

    @property
    def env(self) -> "up.environment.Environment":
        """Returns the problem environment."""
        return self._env

    @property
    def name(self) -> Optional[str]:
        """Returns the problem name."""
        return self._name

    @name.setter
    def name(self, new_name: str):
        """Sets the problem name."""
        self._name = new_name

    def clone(self):
        raise NotImplementedError

    @property
    def kind(self) -> "up.model.problem_kind.ProblemKind":
        """Returns the ProblemKind of this problem."""
        raise NotImplementedError

    def has_name(self, name: str) -> bool:
        """Returns True iff the given name is already used inside this problem."""
        raise NotImplementedError

    def normalize_plan(self, plan: "up.plans.Plan") -> "up.plans.Plan":
        """Normalizes the given plan, that is potentially the result of another
        problem, updating the object references present in it with the ones of
        this problem which are syntactically equal."""
        raise NotImplementedError
