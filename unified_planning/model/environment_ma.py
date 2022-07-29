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
from typing import List, OrderedDict, Optional, Union
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
    """Represents a Environment_ma."""

    def __init__(
        self,
        env: "up.environment.Environment" = None,
        *,
        initial_defaults: Dict["up.model.types.Type", "ConstantExpression"] = {},
    ):
        self._env = get_env(env)
        FluentsSetMixin.__init__(self, self.env, self.has_name, initial_defaults)

    def has_name(self, name: str) -> bool:
        """Returns true if the name is in the problem."""
        return (self.has_fluent(name))

