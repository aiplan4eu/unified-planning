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


import contextlib

import unified_planning.model.walkers as walkers

import unified_planning.environment
from unified_planning.model.walkers.generic import nt_to_fun
from unified_planning.model.walkers.identitydag import IdentityDagWalker
from unified_planning.model.fnode import FNode
from unified_planning.model.operators import OperatorKind
from unified_planning.model.expression import Expression
from unified_planning.exceptions import UPTypeError
from typing import Dict, List


class Substituter(IdentityDagWalker):
    """Performs substitution into an expression"""

    def __init__(self, environment: "unified_planning.environment.Environment"):
        IdentityDagWalker.__init__(self, environment, True)
        self.environment = environment
        self.manager = environment.expression_manager
        self.type_checker = environment.type_checker
        self._in_batch = False
        # Resolve IdentityDagWalker's own walk_* handlers once, keyed by node type, instead of
        # walk_replace_or_identity() re-deriving the method name (nt_to_fun: a string format +
        # replace + lower call) and re-resolving it with getattr() via
        # `IdentityDagWalker.super(...)` on every single node visited by every substitute()
        # call. Every OperatorKind has a corresponding walk_* method on IdentityDagWalker (this
        # is the same lookup `super()` performed, just done once instead of per node).
        self._identity_functions = {
            nt: getattr(IdentityDagWalker, nt_to_fun(nt)) for nt in OperatorKind
        }

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

    def promote_substitutions(
        self, substitutions: Dict[Expression, Expression]
    ) -> Dict[FNode, FNode]:
        """Type-checks and auto-promotes a raw ``substitutions`` mapping into the
        ``Dict[FNode, FNode]`` form ``walk()`` needs. Factored out of :meth:`substitute` so a
        caller that will substitute the *same* mapping into many expressions (e.g. the
        grounder, once per ground-action candidate: one ``subs`` dict, dozens of
        preconditions/effect fields) can promote it once via this method and then call
        :meth:`substitute_promoted` repeatedly, instead of re-promoting on every call.
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
        return self.substitute_promoted(
            expression, self.promote_substitutions(substitutions)
        )

    def substitute_promoted(
        self, expression: FNode, promoted_substitutions: Dict[FNode, FNode]
    ) -> FNode:
        """Like :meth:`substitute`, but ``promoted_substitutions`` must already be a
        ``Dict[FNode, FNode]`` (typically produced by :meth:`promote_substitutions`) -- skips
        the per-call auto-promotion/type-compatibility pass over the whole mapping. Intended
        for a caller that substitutes one fixed mapping into many expressions in a row.
        """
        if len(promoted_substitutions) == 0:
            return expression
        return self.walk(expression, subs=promoted_substitutions)

    @contextlib.contextmanager
    def same_subs_batch(self):
        """Scope in which every :meth:`substitute`/:meth:`substitute_promoted` call is
        guaranteed by the caller to use the exact same substitutions mapping.

        ``Substituter`` is constructed with ``invalidate_memoization=True``
        (see :meth:`__init__`) because :meth:`_get_key` deliberately ignores ``subs`` --
        two calls for the same lifted ``expression`` but *different* substitution maps must
        not share a memoized result. That correctness requirement is exactly why the DAG
        memoization is normally thrown away after every single top-level walk, forcing a full
        re-walk of the whole (sub-)expression on every call even when nothing about the
        substitution changed.

        Within this scope, that invalidation is suspended, so repeated substitutions of the
        *same* mapping into different (but possibly overlapping) expressions reuse the DAG
        memoization instead of recomputing shared sub-expressions from scratch -- the
        grounder's own hot path: one ``subs`` dict, substituted into every precondition and
        every effect field of one ground-action candidate. The memo is always cleared on exit,
        so it is never observed by a subsequent, unrelated substitution mapping.

        Only enter this scope when every ``substitute``/``substitute_promoted`` call made
        inside it truly shares one substitutions mapping -- violating that silently returns
        stale results instead of raising.
        """
        self._in_batch = True
        try:
            yield
        finally:
            self._in_batch = False
            self.memoization.clear()

    def walk(self, expression: FNode, **kwargs) -> FNode:
        if expression in self.memoization:
            return self.memoization[expression]
        res = self.iter_walk(expression, **kwargs)
        if self.invalidate_memoization and not self._in_batch:
            self.memoization.clear()
        return res

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
            return self._identity_functions[expression.node_type](
                self, expression, args, **kwargs
            )
