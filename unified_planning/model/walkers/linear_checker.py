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
import unified_planning.model.walkers as walkers
from unified_planning.model.walkers.dag import DagWalker
from unified_planning.model.operators import OperatorKind
from typing import List, Optional, Set, Tuple


class LinearChecker(DagWalker):
    """Checks if the given expression is linear or not and returns the set of the fluents appearing in the expression.

    Optionally takes a problem to consider static fluents as constants."""

    def __init__(self, problem: Optional["up.model.problem.Problem"] = None):
        DagWalker.__init__(self)
        self._problem = problem

    def get_fluents(
        self, expression: "up.model.fnode.FNode"
    ) -> Tuple[bool, Set["up.model.fnode.FNode"]]:
        """Returns the tuple containing a flag saying if the expression is linear or not and the set of the fluent_expressions appearing in the expression."""
        return self.walk(expression)

    @walkers.handles(
        set(OperatorKind)
        - set({OperatorKind.TIMES, OperatorKind.DIV, OperatorKind.FLUENT_EXP})
    )
    def walk_default(
        self,
        expression: "up.model.fnode.FNode",
        args: List[Tuple[bool, Set["up.model.fnode.FNode"]]],
    ) -> Tuple[bool, Set["up.model.fnode.FNode"]]:
        is_linear = True
        fluents: Set["up.model.fnode.FNode"] = set()
        for b, sf in args:
            # If one of the args is not linear, the whole expression is not linear
            is_linear = is_linear and b
            fluents |= sf  # Update the fluents appearing in the arguments
        return (is_linear, fluents)

    def walk_times(
        self,
        expression: "up.model.fnode.FNode",
        args: List[Tuple[bool, Set["up.model.fnode.FNode"]]],
    ) -> Tuple[bool, Set["up.model.fnode.FNode"]]:
        is_linear = True
        arg_with_fluents_found = False  # We must check that at most 1 of the arguments contains fluent_expression
        fluents: Set["up.model.fnode.FNode"] = set()
        for b, sf in args:
            is_linear = is_linear and b
            if (
                len(sf) > 0 and not arg_with_fluents_found
            ):  # First arg that contains fluent_expressions
                arg_with_fluents_found = True
            elif (
                len(sf) > 0 and arg_with_fluents_found
            ):  # Second argument that contains fluent_expressions
                is_linear = False
            fluents |= sf
        return (is_linear, fluents)

    def walk_div(
        self,
        expression: "up.model.fnode.FNode",
        args: List[Tuple[bool, Set["up.model.fnode.FNode"]]],
    ) -> Tuple[bool, Set["up.model.fnode.FNode"]]:
        assert len(args) == 2
        numerator_is_linear, numerator_fluents = args[0]
        denominator_is_linear, denominator_fluents = args[1]
        fluents: Set["up.model.fnode.FNode"] = numerator_fluents | denominator_fluents
        # A division is linear only if both numerators and denominator as linear and the denominator does not have fluents
        return (
            numerator_is_linear
            and denominator_is_linear
            and len(denominator_fluents) == 0,
            fluents,
        )

    def walk_fluent_exp(
        self,
        expression: "up.model.fnode.FNode",
        args: List[Tuple[bool, Set["up.model.fnode.FNode"]]],
    ) -> Tuple[bool, Set["up.model.fnode.FNode"]]:
        is_linear = True
        fluents: Set["up.model.fnode.FNode"] = set()
        # If the problem is not given or the fluent is not in the problem's static fluents,
        # it must be added to the expression fluents
        if (
            self._problem is None
            or expression.fluent() not in self._problem.get_static_fluents()
        ):
            fluents.add(expression)
        for b, sf in args:
            is_linear = is_linear and b
            fluents |= sf
        return (is_linear, fluents)
