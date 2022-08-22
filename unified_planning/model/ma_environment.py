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

import unified_planning as up
from unified_planning.environment import get_env, Environment
import unified_planning.model.operators as op
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPTypeError,
    UPValueError,
    UPExpressionDefinitionError,
)
from unified_planning.model.walkers import OperatorsExtractor
from unified_planning.model.expression import ConstantExpression
from fractions import Fraction
from typing import List, Dict, Set, Union, Optional
from unified_planning.model.mixins import (
    FluentsSetMixin,
)


class MAEnvironment(
    FluentsSetMixin,
):
    """Represents a MAEnvironment."""

    def __init__(
        self,
        ma_problem: "up.model.MultiAgentProblem",
    ):
        self._name = 'MA_Environment'
        self._ma_problem = ma_problem
        self._env = up.environment.get_env(self._ma_problem.env)
        FluentsSetMixin.__init__(self, self.env, self._ma_problem._add_user_type_method, self.has_name, self._ma_problem._initial_defaults)

    def has_name(self, name: str) -> bool:
        """Returns true if the name is in the problem."""
        return (self.has_fluent(name) or self._ma_problem.has_name(name))

    @property
    def name(self) -> str:
        """Returns the MA-environment name."""
        return self._name

    @property
    def environment(self) -> "Environment":
        """Returns the MA-environment environment."""
        return self._env

    def __repr__(self) -> str:
        s = []
        s.append(f"{str(self._name)}\n\n")
        s.append("fluents = [\n")
        for f in self._fluents:
            s.append(f" {str(f)}\n")
        s.append("]\n\n")
        return "".join(s)
