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


import unified_planning.model.walkers as walkers

import unified_planning.environment
from unified_planning.model.walkers.identitydag import IdentityDagWalker
from unified_planning.model.fnode import FNode
from unified_planning.model.operators import OperatorKind
from unified_planning.model.expression import Expression
from unified_planning.exceptions import UPTypeError
from typing import List, Dict


class FluentsSubstituter(IdentityDagWalker):
    """Performs substitution into an expression"""

    def __init__(
        self,
        fluents: Dict[
            "unified_planning.model.fluent.Fluent",
            "unified_planning.model.fluent.Fluent",
        ],
        environment: "unified_planning.environment.Environment",
    ):
        IdentityDagWalker.__init__(self, environment, True)
        self.environment = environment
        self.manager = environment.expression_manager
        self.type_checker = environment.type_checker
        self._fluents = fluents

    def substitute_fluents(self, expression: FNode) -> FNode:
        """ """
        return self.walk(expression)

    def walk_fluent_exp(
        self,
        expression: FNode,
        args: List[FNode],
        **kwargs,
    ) -> FNode:
        fluent = self._fluents.get(expression.fluent(), expression.fluent())
        return self.manager.FluentExp(fluent, args)
