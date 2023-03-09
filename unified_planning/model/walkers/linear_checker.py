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
from unified_planning.environment import get_environment
from unified_planning.exceptions import UPUsageError
from unified_planning.model.walkers.dag import DagWalker
from unified_planning.model.operators import OperatorKind
from unified_planning.model.types import _IntType, _RealType
from typing import List, Optional, Set, Tuple


class LinearChecker(DagWalker):
    """
    Checks if the given expression is linear or not and returns the `set` of the `fluents` appearing in the expression.

    Optionally takes a :class:`~unified_planning.model.Problem` to consider static `fluents` as constants.

    Important NOTE:
    After the initialization, the problem given as input can not be modified
    or the `LinearChecker` behavior is undefined.
    """

    def __init__(
        self,
        problem: Optional["up.model.problem.Problem"] = None,
        environment: Optional["up.environment.Environment"] = None,
    ):
        DagWalker.__init__(self)
        if problem is not None:
            if environment is not None:
                assert (
                    problem.environment == environment
                ), "The given environemt is different from the given problem environment"
            self._static_fluents: Set[
                "up.model.fluent.Fluent"
            ] = problem.get_static_fluents()
            self._env = problem.environment
            self._simplifier = walkers.Simplifier(self._env, problem)
        else:
            self._static_fluents = set()
            self._env = get_environment(environment)
            self._simplifier = self._env.simplifier

    def get_fluents(
        self, expression: "up.model.fnode.FNode"
    ) -> Tuple[bool, Set["up.model.fnode.FNode"], Set["up.model.fnode.FNode"]]:
        """
        Returns the tuple containing a flag saying if the expression is linear or not,
        the `set` of the `fluent_expressions` appearing with a positive sign in the expression
        and the `set` of the `fluent_expressions` appearing with a negative sign in the expression .
        """
        if expression.type.is_undefined_type():
            raise UPUsageError(
                "It makes no sense to check the linearity of an expression containing Undefined"
            )
        return self.walk(self._simplifier.simplify(expression))

    @walkers.handles(
        set(OperatorKind)
        - set(
            {
                OperatorKind.TIMES,
                OperatorKind.DIV,
                OperatorKind.MINUS,
                OperatorKind.FLUENT_EXP,
            }
        )
    )
    def walk_default(
        self,
        expression: "up.model.fnode.FNode",
        args: List[
            Tuple[bool, Set["up.model.fnode.FNode"], Set["up.model.fnode.FNode"]]
        ],
    ) -> Tuple[bool, Set["up.model.fnode.FNode"], Set["up.model.fnode.FNode"]]:
        is_linear = True
        positive_fluents: Set["up.model.fnode.FNode"] = set()
        negative_fluents: Set["up.model.fnode.FNode"] = set()
        for b, spf, snf in args:
            # If one of the args is not linear, the whole expression is not linear
            is_linear = is_linear and b
            # Update the positive and negative fluents appearing in the arguments
            positive_fluents |= spf
            negative_fluents |= snf
        return (is_linear, positive_fluents, negative_fluents)

    def walk_times(
        self,
        expression: "up.model.fnode.FNode",
        args: List[
            Tuple[bool, Set["up.model.fnode.FNode"], Set["up.model.fnode.FNode"]]
        ],
    ) -> Tuple[bool, Set["up.model.fnode.FNode"], Set["up.model.fnode.FNode"]]:
        is_linear = True
        arg_with_fluents_found = False  # We must check that at most 1 of the arguments contains fluent_expression
        positivity = True
        positivity_unknown = False
        positive_fluents: Set["up.model.fnode.FNode"] = set()
        negative_fluents: Set["up.model.fnode.FNode"] = set()
        tc = self._env.type_checker
        for i, (b, spf, snf) in enumerate(args):
            is_linear = is_linear and b
            if len(spf) > 0 or len(snf) > 0:
                if (
                    not arg_with_fluents_found
                ):  # First arg that contains fluent_expressions
                    arg_with_fluents_found = True
                else:  # Second argument that contains fluent_expressions
                    is_linear = False
                positive_fluents |= spf
                negative_fluents |= snf
            else:
                t = tc.get_type(expression.arg(i))
                assert isinstance(t, _IntType) or isinstance(t, _RealType)
                if t.lower_bound is None or t.upper_bound is None:
                    positivity_unknown = True
                elif t.lower_bound > 0:
                    pass
                elif t.upper_bound < 0:
                    positivity = not positivity
                else:
                    positivity_unknown = True
        if not is_linear:
            return (is_linear, set(), set())
        if positivity_unknown:
            fluents = positive_fluents | negative_fluents
            return (is_linear, fluents, fluents)
        elif positivity:
            return (is_linear, positive_fluents, negative_fluents)
        else:
            return (is_linear, negative_fluents, positive_fluents)

    def walk_div(
        self,
        expression: "up.model.fnode.FNode",
        args: List[
            Tuple[bool, Set["up.model.fnode.FNode"], Set["up.model.fnode.FNode"]]
        ],
    ) -> Tuple[bool, Set["up.model.fnode.FNode"], Set["up.model.fnode.FNode"]]:
        assert len(args) == 2
        (
            numerator_is_linear,
            numerator_positive_fluents,
            numerator_negative_fluents,
        ) = args[0]
        (
            denominator_is_linear,
            denominator_positive_fluents,
            denominator_negative_fluents,
        ) = args[1]

        # A division is linear only if both numerators and denominator as linear and the denominator does not have fluents
        is_linear = (
            numerator_is_linear
            and denominator_is_linear
            and len(denominator_positive_fluents) == 0
            and len(denominator_negative_fluents) == 0
        )
        if not is_linear:
            return (is_linear, set(), set())

        positive_fluents: Set["up.model.fnode.FNode"] = (
            numerator_positive_fluents | denominator_positive_fluents
        )
        negative_fluents: Set["up.model.fnode.FNode"] = (
            numerator_negative_fluents | denominator_negative_fluents
        )
        positivity = True
        for a in expression.args:
            if (a.is_int_constant() or a.is_real_constant()) and a.constant_value() < 0:
                positivity = not positivity

        if positivity:
            return (is_linear, positive_fluents, negative_fluents)
        else:
            return (is_linear, negative_fluents, positive_fluents)

    def walk_minus(
        self,
        expression: "up.model.fnode.FNode",
        args: List[
            Tuple[bool, Set["up.model.fnode.FNode"], Set["up.model.fnode.FNode"]]
        ],
    ) -> Tuple[bool, Set["up.model.fnode.FNode"], Set["up.model.fnode.FNode"]]:
        assert len(args) == 2
        is_linear = True
        positive_fluents: Set["up.model.fnode.FNode"] = set()
        negative_fluents: Set["up.model.fnode.FNode"] = set()
        # First argument is like the default
        b, spf, snf = args[0]
        is_linear = is_linear and b
        positive_fluents |= spf
        negative_fluents |= snf
        # Second argument swap positive and negative fluents
        b, spf, snf = args[1]
        is_linear = is_linear and b
        negative_fluents |= spf
        positive_fluents |= snf
        if not is_linear:
            return (is_linear, set(), set())
        else:
            return (is_linear, positive_fluents, negative_fluents)

    def walk_fluent_exp(
        self,
        expression: "up.model.fnode.FNode",
        args: List[
            Tuple[bool, Set["up.model.fnode.FNode"], Set["up.model.fnode.FNode"]]
        ],
    ) -> Tuple[bool, Set["up.model.fnode.FNode"], Set["up.model.fnode.FNode"]]:
        is_linear = True
        for b, spf, snf in args:
            is_linear = is_linear and b
        return (is_linear, {expression}, set())
