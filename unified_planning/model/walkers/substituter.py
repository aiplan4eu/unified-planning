# Copyright 2021-2023 AIPlan4EU project
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


class Substituter(IdentityDagWalker):
    """Performs substitution into an expression"""

    def __init__(self, environment: "unified_planning.environment.Environment"):
        IdentityDagWalker.__init__(self, environment, True)
        self.environment = environment
        self.manager = environment.expression_manager
        self.type_checker = environment.type_checker

    def _get_key(self, expression, **kwargs):
        return expression

    def _push_with_children_to_stack(self, expression: FNode, **kwargs):
        """Add children to the stack."""

        # Deal with quantifiers
        if expression.is_exists() or expression.is_forall():
            # 1. We create a new substitution in which we remove the
            #    bound variables from the substitution map
            substitutions: Dict[FNode, FNode] = kwargs["subs"]
            new_subs: Dict[Expression, Expression] = {}
            for k, v in substitutions.items():
                # If at least one bound variable is in the cone of k,
                # we do not consider this substitution in the body of
                # the quantifier.
                if all(
                    m not in expression.variables()
                    for m in self.environment.free_vars_oracle.get_free_variables(k)
                ):
                    new_subs[k] = v

            # 2. We apply the substitution on the quantifier body with
            #    the new 'reduced' map
            sub = self.__class__(self.environment)
            res_expression = sub.substitute(expression.arg(0), new_subs)

            # 3. We invoke the relevant function (walk_exists or
            #    walk_forall) to compute the substitution
            fun = self.functions[expression.node_type]
            res = fun(expression, args=[res_expression], **kwargs)

            # 4. We memoize the result
            key = self._get_key(expression, **kwargs)
            self.memoization[key] = res
        else:
            IdentityDagWalker._push_with_children_to_stack(self, expression, **kwargs)

    def substitute(
        self, expression: FNode, substitutions: Dict[Expression, Expression] = {}
    ) -> FNode:
        """
        Performs substitution into the given expression.

        The substitutions are made top-down in the expression tree and the substitution is not
        applied to the substituted expressions.

        :param expression: The target expression for the substitution.
        :param substitutions: The map containing the substitutions, every time a key is found,
            it is substituted with it's value.
        :return: The expression where every key expression is substituted with it's value.

        Lets consider the examples:
        f = a & b
        subs = {a -> c, (c & b) -> d, (a & b) -> c}
        substitute(f, subs) = c

        f = a
        subs = {a -> c, c -> d}
        substitute(f, subs) = c

        f = a & b
        subs = {a -> 5, b -> c}
        substitute(f, subs) raises an UPTypeError

        Note that, since subs is a dictionary:
        f = a
        subs = {a -> b, a -> c}
        substitute(f, subs) = c
        """

        if len(substitutions) == 0:
            return expression
        return self.walk(expression, subs=self.normalize_substitutions(substitutions))

    def normalize_substitutions(
        self, substitutions: Dict[Expression, Expression] = {}
    ) -> Dict[FNode, FNode]:
        """
        Auto-promotes and type-checks every entry of the given substitutions map, returning the
        `FNode -> FNode` dictionary that :func:`substitute` would build internally on every call.

        Factored out of :func:`substitute` so a caller that calls :func:`substitute_normalized`
        (or :func:`walk` directly, with ``subs=...``) in a loop with the same substitutions can
        build this dictionary once instead of paying the `auto_promote`/type-check pass again for
        every expression -- see :func:`substitute_normalized`.

        :param substitutions: The map containing the substitutions, every time a key is found,
            it is substituted with it's value.
        :return: The equivalent `FNode -> FNode` substitutions map.
        """
        new_substitutions: Dict[FNode, FNode] = {}
        for k, v in substitutions.items():
            new_k, new_v = self.manager.auto_promote(k, v)
            if new_k.type.is_compatible(new_v.type):
                new_substitutions[new_k] = new_v
            else:
                raise UPTypeError(
                    f"The expression type of {str(k)} is not compatible with the given substitution {str(v)}"
                )
        return new_substitutions

    def substitute_normalized(
        self, expression: FNode, substitutions: Dict[FNode, FNode]
    ) -> FNode:
        """
        Same as :func:`substitute`, but skips the `auto_promote`/type-check rebuild of
        ``substitutions`` on every call: ``substitutions`` must already be an `FNode -> FNode`
        dictionary produced by :func:`normalize_substitutions` (or an equivalent one, built by
        hand from `FNode`s only).

        Intended for a caller that substitutes the same (typically large) map into many
        expressions in a loop -- e.g. one problem's whole
        :func:`initial_values <unified_planning.model.mixins.InitialStateMixin.initial_values>`
        substituted into many separate constraints -- where :func:`substitute` would otherwise
        redo that rebuild once per expression.

        :param expression: The target expression for the substitution.
        :param substitutions: The already-normalized map containing the substitutions.
        :return: The expression where every key expression is substituted with it's value.
        """
        if len(substitutions) == 0:
            return expression
        return self.walk(expression, subs=substitutions)

    @walkers.handles(OperatorKind)
    def walk_replace_or_identity(
        self,
        expression: FNode,
        args: List[FNode],
        subs: Dict[FNode, FNode] = {},
        **kwargs,
    ) -> FNode:
        res = subs.get(expression, None)
        if res is not None:
            return res
        else:
            return IdentityDagWalker.super(self, expression, args, **kwargs)
