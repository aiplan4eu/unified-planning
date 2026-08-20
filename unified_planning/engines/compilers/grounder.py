# Copyright 2021-2023 AIPlan4EU project
# Copyright 2024-2026 Unified Planning library and its maintainers
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
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    Problem,
    ProblemKind,
    Action,
    Type,
    Expression,
    FNode,
    MinimizeActionCosts,
    Parameter,
)
from unified_planning.model.types import domain_size, domain_item
from unified_planning.model.walkers import Simplifier
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.compilers.utils import (
    lift_action_instance,
    create_action_with_given_subs,
    split_all_ands,
)
from typing import Any, Dict, List, Optional, Set, Tuple, Iterator, cast
from itertools import product
from functools import partial


class GrounderHelper:
    """
    This class gives the capability of grounding a :class:`~unified_planning.model.Problem` by taking
    it at construction time.

    It offers the capability both of grounding the whole `Problem`, with the :func:`~unified_planning.engines.compilers.GrounderHelper.get_grounded_actions`
    function or offers the capability of grounding a single `Action` of the `Problem`, given the grounding parameters
    (with the :func:`~unified_planning.engines.compilers.GrounderHelper.ground_action` function).

    Important NOTE: This class caches the grounded actions created to avoid duplication; 2 different calls
    with the same parameters will return the same object!
    """

    def __init__(
        self,
        problem: Problem,
        grounding_actions_map: Optional[Dict[Action, List[Tuple[FNode, ...]]]] = None,
        prune_actions: bool = True,
    ):
        """
        Creates an instance of the GrounderHelper.

        :param problem: The `Problem` to ground.
        :param grounding_actions_map: Optionally, a map from `Action` to a List of Tuples of expressions.
            When this map is set, it represents the groundings that this class does.
            So, for every key in the map, the `Action` is grounded with every `tuple of parameters` in the mapped value.
            For example, if the map is `{a: [(o1, o2), (o2, o3)], b: [(o3), (o4)]}`, the resulting grounded actions will be:
            * `a (o1, o2)`
            * `a (o2, o3)`
            * `b (o3)`
            * `b (o4)`
            If this map is `None`, the `unified_planning` grounding algorithm is applied.
        :param prune_actions: If `True` (the default), actions are pruned exploiting the simplification of
            static fluents: the action's eligible static fluents are hash-joined together (correctly
            handling hierarchical typing), so a static predicate that jointly constrains several of the
            action's parameters together (e.g. a lookup table relating them) is pruned down to the handful
            of parameter tuples actually consistent with it, rather than enumerating (and then rejecting)
            their full cross product. If the join isn't applicable/safe for a given action -- an unbounded
            parameter type, a candidate count above an internal safety cap, or any unexpected condition --
            that one action falls back to the weaker (but always sound) per-parameter-independent pruning:
            each parameter is narrowed, independently of the others, to the objects that appear at a
            matching argument position of some true static fluent in the action's precondition. If
            `False`, no pruning at all is done.
        """
        assert isinstance(problem, Problem)
        self._problem = problem
        self._grounding_actions_map = grounding_actions_map
        self._prune_actions = prune_actions
        if grounding_actions_map is not None:
            for action, params_list in grounding_actions_map.items():
                for params in params_list:
                    assert len(action.parameters) == len(params), (
                        f"Action {action.name} has {len(action.parameters)} parameters but {len(params)} are given in the map.\n{action.parameters}\n{params}"
                    )
        # grounded_actions is a map from an Action of the original problem and it's parameters
        # to the grounded instance of the Action with the given parameters.
        # When the grounded instance of the Action is None, it means that the resulting grounding
        # of that action is a meaningless Action.
        # An Action is meaningless when:
        # - his conditions create a contradiction
        # - the action has conflicting effects
        # - for a DurativeAction, its duration interval simplifies to an empty interval
        # Note: an action with no effects is NOT rejected; it is grounded as-is.
        self._grounded_actions: Dict[
            Tuple[str, Tuple[FNode, ...]], Optional[Action]
        ] = {}
        # Caches reused across every lifted action grounded by this instance. The problem is
        # documented as immutable for the lifetime of this class (grounding relies on it, same
        # as Simplifier's own "problem must not be modified" contract below), so these are safe
        # to compute once instead of once per action / per (parameter, static-fluent) pair.
        self._static_fluents_cache: Optional[Set["up.model.fluent.Fluent"]] = None
        self._true_arg_tuples_cache: Dict[
            "up.model.fluent.Fluent", List[Tuple[FNode, ...]]
        ] = {}
        self._domain_items_cache: Dict[Type, List[FNode]] = {}
        self._valid_params_cache: Dict[Tuple[FNode, int], Set[FNode]] = {}
        env = problem.environment
        if prune_actions:
            self._simplifier = Simplifier(env, problem)
        else:
            self._simplifier = env.simplifier

    @property
    def simplifier(self) -> Simplifier:
        return self._simplifier

    def ground_action(
        self, action: Action, parameters: Tuple[FNode, ...] = tuple()
    ) -> Optional[Action]:
        """
        Grounds the given action with the given parameters.
        An ``Action`` is grounded when it has no :func:`parameters <unified_planning.model.Action.parameters>`.

        The returned ``Action`` is cached, so if the same method is called twice with the same function parameters,
        the same object is returned, and the same object will be returned in the total problem grounding, so
        if the resulting ``Action`` or :class:`~unified_planning.model.Problem` are modified, all the copies
        returned by this class will be modified.

        :param action: The ``Action`` that must be grounded with the given ``parameters``.
        :param parameters: The tuple of expressions used to ground the given ``action``.
        :return: The ``action`` grounded with the given ``parameters`` or ``None`` if the grounded
            action does not have ``effects`` or the ``action conditions`` can be easily evaluated as a
            contradiction.
        """
        assert len(action.parameters) == len(parameters), (
            "The number of given parameters for the grounding is different from the action's parameters"
        )
        key = (action.name, tuple(parameters))
        value = self._grounded_actions.get(key, 0)
        if value != 0:  # The action is already created
            assert isinstance(value, Action) or value is None
            return value
        else:
            # if the action does not have parameters, it does not need to be grounded.
            if len(action.parameters) == 0:
                if (
                    self._grounding_actions_map is None
                    or self._grounding_actions_map.get(action, None) is not None
                ):
                    new_action = create_action_with_given_subs(
                        self._problem, action, self._simplifier, {}
                    )
                else:
                    new_action = None
            else:
                subs: Dict[Expression, Expression] = dict(
                    zip(action.parameters, list(parameters))
                )
                new_action = create_action_with_given_subs(
                    self._problem, action, self._simplifier, subs
                )
            self._grounded_actions[key] = new_action
            return new_action

    def get_grounded_actions(
        self,
    ) -> Iterator[Tuple[Action, Tuple[FNode, ...], Optional[Action]]]:
        """
        Returns an iterator over all the possible grounded actions of the problem given at construction time.
        Every resulting tuple is made of 3 elements: ``original_action``, ``parameters``, ``grounded_action`` where:

        * The ``original_action`` is the `Action` of the ``Problem`` that is grounded.
        * The ``parameters`` is the `Tuple of expressions` used to ground the ``original_action``.
        * The ``grounded_action`` is the `Action` created by grounding the ``original_action`` with the given ``parameters``;
            the ``grounded_action`` can be ``None`` if the grounding of the ``original_action`` with the given parameters
            creates an invalid or meaningless `Action` (invalid if it has conflicting `Effects`,
            meaningless if its conditions create a contradiction, or, for a `DurativeAction`,
            if its duration interval simplifies to an empty interval).
        """
        for old_action in self._problem.actions:
            for grounded_params in self.get_possible_parameters(old_action):
                assert isinstance(grounded_params, tuple)
                new_action = self.ground_action(old_action, grounded_params)
                yield (old_action, grounded_params, new_action)

    def get_possible_parameters(self, action: Action) -> Iterator[Tuple[FNode, ...]]:
        """
        Takes in input an `Action` and returns the iterator over all the possible parameters compatible with the given
        action signature; this is computed in the domain of the :class:`~unified_planning.model.Problem` given at construction time.

        :param action: The `Action` providing the signature to get all the possible grounding parameters in the
            `Problem` 's domain.
        :return: An `Iterator` over all the possible `Tuple of expressions` that are compatible with the given `Action`.
        """
        # if the action does not have parameters, it does not need to be grounded.
        if len(action.parameters) == 0:
            if (
                self._grounding_actions_map is None
                or self._grounding_actions_map.get(action, None) is not None
            ):
                res: Iterator[Tuple[FNode, ...]] = iter([tuple()])
            else:
                res = iter([])
        else:
            # contains the type of every parameter of the action
            type_list: List[Type] = [param.type for param in action.parameters]
            if self._grounding_actions_map is None:
                # a list containing the list of object in the self._problem of the given type.
                # So, if the self._problem has 2 Locations l1 and l2, and 2 Robots r1 and r2, and
                # the action move_to takes as parameters a Robot and a Location,
                # the variable state at this point will be the following:
                # type_list = [Robot, Location]
                # objects_list = [[r1, r2], [l1, l2]]
                # the product of *objects_list will be:
                # [(r1, l1), (r1, l2), (r2, l1), (r2,l2)]
                if self._prune_actions:
                    joined = self._compute_join_pruned_parameters(action, type_list)
                    if joined is not None:
                        return iter(joined)
                    # else: the join wasn't applicable/safe for this action -- fall through
                    # to the per-parameter-independent cross-product path below, for this
                    # action only.

                items_list: List[List[FNode]] = [
                    self._get_domain_items(t) for t in type_list
                ]
                if self._prune_actions and (
                    isinstance(action, up.model.action.InstantaneousAction)
                    or isinstance(action, up.model.action.DurativeAction)
                ):
                    bool_conditions = self._static_bool_fluents(action) or []
                    items_list = self._purge_items_list(
                        items_list=items_list,
                        params=action.parameters,
                        conds=bool_conditions,
                    )
                res = product(*items_list)
            else:
                # The grounding_actions_map is not None, therefore it must be used to ground
                res = iter(self._grounding_actions_map.get(action, []))
        return res

    # Safety valve for the join: bail out to the per-parameter cross-product fallback for
    # one action if its running candidate count exceeds this. The reference dataset this
    # algorithm was validated against never got close to it (largest was ~52k).
    _JOIN_MAX_CANDIDATES = 1_000_000

    def _compute_join_pruned_parameters(
        self, action: Action, type_list: List[Type]
    ) -> Optional[List[Tuple[FNode, ...]]]:
        """Hash-joins `action`'s eligible static fluents (`_static_bool_fluents`) against their
        true argument tuples (`_fluent_true_arg_tuples`), incrementally building only the
        parameter tuples consistent with every joined fluent -- instead of pruning each
        parameter independently, which cannot see a static predicate
        that correlates several of the action's parameters together and so ends up enumerating
        their full cross product.

        Returns `None` if the join isn't applicable/safe for this action, including when the
        action type is unrecognized, the parameter type is unbounded or unenumerable, the
        candidate count exceeds _JOIN_MAX_CANDIDATES, or an unexpected exception occurs.
        """
        try:
            return self._compute_join_pruned_parameters_unsafe(action, type_list)
        except Exception:
            return None

    def _compute_join_pruned_parameters_unsafe(
        self, action: Action, type_list: List[Type]
    ) -> Optional[List[Tuple[FNode, ...]]]:
        """Given one action and the type domains of its parameters, return the exact
        list of parameter tuples that satisfy all of the action's static-boolean-fluent
        conditions -- computed via a relational hash-join instead of `_purge_items_list`'s
        per-parameter (independent) pruning. Returns `None` when it can't safely do this
        (unrecognized action, unbounded type, candidate blow-up, or any exception).

        High-level shape: it's a classic database join -- each static fluent in
        `static_fluents` is a "table" of rows (the argument tuples for which that fluent is
        true), and the algorithm joins these tables together on the action-parameter columns
        they share, incrementally narrowing a running result set (`bindings`). Any parameter
        columns never touched by a joinable fluent are left free and cross-producted in at
        the end.

        Step-by-step:

        1. Trivial cases: get `action.parameters` into `params`; if `num_params` is 0,
            return `[()]`. Fetch the action's eligible static fluents via
            `_static_bool_fluents`; if `None` (action type not recognized), bail out.
        2. Set up per-parameter domains:
            - `param_domains`: each action parameter's candidate objects (via
              `_get_domain_items`).
            - `domain_sets`: same, as sets, for fast membership checks.
            - `domain_position`: object -> index within its own domain, needed later for
              canonical ordering.
            - `param_expr_to_column`: maps each parameter's `ParameterExp` to its column
              index -- this is how a fluent's argument is recognized as "this is action
              parameter #i" versus a constant or a nested/object-fluent expression.
        3. Fold loop over static fluents -- this is the core. State carried across
            iterations:
            - `bindings`: `None` until the first fluent folds in, then a list of partial
              bindings (`Dict[column_index, FNode]`), one per surviving candidate row.
            - `bound_columns`: which parameter columns have been constrained so far.

            For each fluent:
            - Classify each argument as `("p", col)` if it's an action parameter,
              `("c", value)` if it's a constant, or `("*", None)` (wildcard) if it's anything
              else (nested/object-fluent arg -- same blind spot `_purge_items_list`'s
              per-parameter pruning has).
            - Skip fluents that touch no parameter column -- nothing to join on.
            - Materialize this fluent's rows: pull its true argument-tuples via
              `_fluent_true_arg_tuples`, and for each tuple build a `binding` dict from
              parameter-columns to values, rejecting the tuple if a constant position
              doesn't match, if a parameter-column value falls outside that parameter's own
              domain (the hierarchical-typing guard), or if the fluent binds the same column
              twice inconsistently (handles `sym(?x, ?x)`-style repeated parameters within
              one fluent).
            - Merge into `bindings`:
              - First fluent: `bindings` just becomes `rows`.
              - Later fluents: find `shared_columns` already bound vs. this fluent's
                columns. If there's overlap, do an actual indexed hash-join on those shared
                columns (`rows_by_shared_key`, built once, then probed once per existing
                binding into `joined_rows`). If no overlap, it's a cross-product merge
                (`{**left, **right}` for every pair) -- still correct, just not a filtering
                join.
            - Early exits: if `bindings` became empty, stop early (nothing will ever match).
              If it exceeds `_JOIN_MAX_CANDIDATES`, give up and return `None` (safety valve
              back to per-parameter pruning for this action).
        4. Handle free (never-bound) columns: any parameter column no fluent constrained is
            a `free_column`; its full domain (`free_domains`) must be cross-producted in.
            Compute the prospective final size (`len(bindings) * free_size`) and bail to
            `None` if it would exceed the candidate cap.
        5. Expand into full parameter tuples: for each surviving binding, cross the free
            columns' domains in (via `product`) and assemble one full
            `(param_0_value, ..., param_n_value)` tuple per combination into `tuples`. If
            there are no free columns, just read the binding straight through.
        6. Canonical sort: sort `tuples` by each parameter's index within its own domain
            (`domain_position`) -- this matches the enumeration order
            `itertools.product(*param_domains)` would produce, so the join doesn't silently
            reorder/rename ground actions relative to the per-parameter fallback.
        7. Return the final `tuples` list -- the exact, jointly-consistent set of parameter
            tuples for this action.

        Example: action `deliver(?r: Robot, ?l: Location, ?p: Package)` -- columns 0=r,
        1=l, 2=p -- with domains `Robot={r1,r2}`, `Location={l1,l2}`, `Package={p1,p2}` (8
        combinations, unpruned) and static conditions `robot_can_carry(?r,?p)` true for
        `(r1,p1), (r1,p2), (r2,p1)`, and `package_at(?p,?l)` true for `(p1,l1), (p2,l2)`.
        Per-parameter pruning can't shrink anything here: `r1`, `r2`, `l1`, `l2`, `p1`, `p2`
        each appear in at least one true tuple, so all 8 combinations -- including invalid
        ones like `(r2, l2, p2)`, since r2 never carries p2 -- would still be
        cross-producted. The join instead folds in `robot_can_carry` first, producing
        partial bindings `{0:r1,2:p1}, {0:r1,2:p2}, {0:r2,2:p1}`; then folds in
        `package_at`, joining on their shared column 2 (`p`): `shared_columns = [2]`, and
        `p1` only pairs with `l1`, `p2` only with `l2`, leaving
        `bindings = [{0:r1,2:p1,1:l1}, {0:r1,2:p2,1:l2}, {0:r2,2:p1,1:l1}]`. Both columns 0
        and 1 are already bound here, so there are no free columns left to cross in, and
        step 5 just reads each binding straight through into
        `tuples = [(r1,l1,p1), (r1,l2,p2), (r2,l1,p1)]` -- the 3 combinations that are
        jointly consistent with both conditions.

        The essential idea: rather than pruning each parameter's candidate list independently,
        this builds up joint bindings fluent-by-fluent, joining on whatever columns two fluents
        happen to share, and only falls back to a full cross product for the columns nothing
        constrains.
        """
        params = list(action.parameters)
        num_params = len(params)
        if num_params == 0:
            return [tuple()]
        static_fluents = self._static_bool_fluents(action)
        if static_fluents is None:
            # Not an InstantaneousAction/DurativeAction -- an action type this file doesn't
            # know how to read preconditions/conditions from.
            return None

        em = self._problem.environment.expression_manager
        # Every parameter's full type domain
        param_domains = [self._get_domain_items(t) for t in type_list]
        domain_sets = [set(d) for d in param_domains]
        # Each object's position within its own type's domain -- used only at the very end,
        # to sort the finished tuples back into the same order the caller's plain
        # `itertools.product` over `param_domains` would have produced them in.
        domain_position = [{obj: j for j, obj in enumerate(d)} for d in param_domains]
        # Lets an atom argument that's a bare action parameter (as opposed to a constant or a
        # nested expression) be recognized and traced back to its column index below.
        param_expr_to_column = {em.ParameterExp(p): i for i, p in enumerate(params)}

        # `bindings` is the running join result: each element maps a column index to the
        # object bound there by every static fluent folded in so far. `None` means "no fluent
        # folded in yet", i.e. fully unconstrained -- distinct from "folded in one and it left
        # zero rows", which ends the loop early via the `if not bindings: break` below.
        bindings: Optional[List[Dict[int, FNode]]] = None
        bound_columns: Set[int] = set()

        # Fold in one static fluent at a time, narrowing `bindings` after each one.
        for static_fluent in static_fluents:
            # Classify each argument of this one fluent: a bound action parameter (record its
            # column), a literal constant, or -- falling through -- an unconstrained wildcard.
            pattern: List[Tuple[str, Any]] = []
            for arg in static_fluent.args:
                if arg in param_expr_to_column:
                    pattern.append(("p", param_expr_to_column[arg]))
                elif arg.is_constant():
                    pattern.append(("c", arg))
                else:
                    # nested/object-fluent argument: a wildcard, unconstrained -- same as
                    # the per-parameter fallback pruning, which can't handle these either.
                    pattern.append(("*", None))

            fluent_columns: Set[int] = {i for kind, i in pattern if kind == "p"}
            if not fluent_columns:
                # Every argument was a constant/wildcard: this fluent doesn't mention any
                # action parameter, so it has nothing to prune -- skip it (same blind spot
                # the per-parameter fallback pruning already has).
                continue

            # Check every argument tuple this fluent is actually true for against the
            # pattern; each one that's consistent becomes one candidate binding *for this
            # fluent alone* (not yet folded together with any other fluent's bindings).
            rows: List[Dict[int, FNode]] = []
            for true_args in self._fluent_true_arg_tuples(static_fluent.fluent()):
                binding: Dict[int, FNode] = {}
                is_consistent = True
                for (kind, payload), arg_value in zip(pattern, true_args):
                    if kind == "c":
                        if arg_value != payload:
                            # TODO: can we enter here?
                            is_consistent = False
                            break
                    elif kind == "p":
                        col: int = payload
                        if arg_value not in domain_sets[col]:
                            # Hierarchical-typing guard: an object matched via a static fluent's argument
                            # position must be a member of the ACTION PARAMETER's own type domain, not just the
                            # static fluent's declared parameter type -- the fluent's declared type may be a
                            # supertype of the action parameter it's being matched against.
                            # Omitting this intersection would bind an object that's ill-typed for the action
                            # parameter.
                            is_consistent = False
                            break
                        # The same parameter appearing at more than one position of this one
                        # fluent (e.g. `sym(?x, ?x)`) must agree with itself at every
                        # occurrence, not just be individually well-typed at each one.
                        if col in binding and binding[col] != arg_value:
                            # TODO: can we enter here?
                            is_consistent = False
                            break
                        binding[col] = arg_value
                if is_consistent:
                    rows.append(binding)

            if bindings is None:
                # First fluent processed: nothing to join against yet, so its own rows become
                # the running result outright.
                bindings, bound_columns = rows, set(fluent_columns)
            else:
                # Columns already bound by an earlier fluent that this fluent constrains too
                # -- the actual join key. Two fluents that don't share any column have no key
                # to join on at all (handled in the `else` branch below).
                shared_columns = sorted(bound_columns & fluent_columns)
                if shared_columns:
                    # A real hash join: index this fluent's rows by their shared-column
                    # values once, then probe that index once per existing binding, instead
                    # of comparing every (existing binding, new row) pair against each other.
                    rows_by_shared_key: Dict[
                        Tuple[FNode, ...], List[Dict[int, FNode]]
                    ] = {}
                    for row in rows:
                        key = tuple(row[i] for i in shared_columns)
                        rows_by_shared_key.setdefault(key, []).append(row)
                    joined_rows = []
                    for left in bindings:
                        key = tuple(left[i] for i in shared_columns)
                        for right in rows_by_shared_key.get(key, ()):
                            merged = dict(left)
                            merged.update(right)
                            joined_rows.append(merged)
                    bindings = joined_rows
                else:
                    # No shared column: this fluent constrains entirely different
                    # parameters than anything folded in so far, so there is nothing to join
                    # on -- cross every existing binding with every one of this fluent's rows.
                    bindings = [
                        {**left, **right} for left in bindings for right in rows
                    ]
                bound_columns |= fluent_columns

            if not bindings:
                # Zero rows survived: no combination can ever satisfy every fluent folded in
                # so far, so no later fluent can matter either -- stop early.
                break
            if len(bindings) > self._JOIN_MAX_CANDIDATES:
                # Safety valve: give up on the join for this action and let the caller fall
                # back to the (always bounded, if weaker) per-parameter pruning instead.
                return None

        # Any parameter no static fluent ever constrained keeps its entire type domain --
        # this reproduces the per-parameter fallback's own behavior exactly for a column
        # that can't be pruned at all.
        free_columns = [i for i in range(num_params) if i not in bound_columns]
        free_domains = [param_domains[i] for i in free_columns]
        if bindings is None:
            # No fluent was ever eligible to fold in (e.g. every one hit the `continue`
            # above): one empty binding, to be crossed with the full free-column domains
            # below exactly like a plain, unpruned cross product would be.
            bindings = [{}]
        free_size = 1
        for domain in free_domains:
            free_size *= len(domain)
        if len(bindings) * free_size > self._JOIN_MAX_CANDIDATES:
            # Second safety check: even when the constrained part of `bindings` stayed
            # small, cross-joining in every free column could still blow the budget.
            return None

        # Expand every surviving (possibly partial) binding with every combination of the
        # still-free columns' domains, turning each into a full length-`num_params` tuple.
        tuples: List[Tuple[FNode, ...]] = []
        for binding in bindings:
            if free_columns:
                for combo in product(*free_domains):
                    full_binding = dict(binding)
                    full_binding.update(zip(free_columns, combo))
                    tuples.append(tuple(full_binding[i] for i in range(num_params)))
            else:
                tuples.append(tuple(binding[i] for i in range(num_params)))

        # Canonical order -- must match itertools.product(*items_list)'s own enumeration
        # order (lexicographic by each parameter's index within its own type's domain) so
        # actions the join doesn't improve on stay order-identical to the fallback pruning:
        # ground action naming/ordering must not silently change for a domain that doesn't
        # even benefit from the join.
        tuples.sort(
            key=lambda ground_tuple: tuple(
                domain_position[i][ground_tuple[i]] for i in range(num_params)
            )
        )
        return tuples

    def _static_bool_fluents(self, action: Action) -> Optional[List[FNode]]:
        """Returns the top-level-AND positive boolean static-fluent expressions in `action`'s
        preconditions (`InstantaneousAction`) or conditions (`DurativeAction`) -- the same
        static-fluent selection the per-parameter fallback pruning (`_purge_items_list`'s
        caller, below) has always used, factored out so the join (below) agrees on exactly
        which static fluents are eligible and differs only in how it uses them. Returns
        `None` for an action type this file doesn't recognize.

        Negative literals, non-boolean static fluents, and static-fluent expressions nested
        inside `Or`/`Exists`/`Forall`/`Not` are deliberately excluded here, matching the
        fallback pruning's existing blind spots (`split_all_ands` only flattens top-level
        `And`; a static fluent that doesn't have to hold for the *whole* action to be
        applicable can't be used to filter parameters the way a top-level conjunct can).
        """
        if isinstance(action, up.model.action.InstantaneousAction):
            conds = list(action.preconditions)
        elif isinstance(action, up.model.action.DurativeAction):
            conds = []
            for _, cl in action.conditions.items():
                conds.extend(cl)
        else:
            return None
        problem_static_fluents = self._get_static_fluents()
        return [
            c
            for c in split_all_ands(conds)
            if c.is_fluent_exp()
            and c.fluent().type.is_bool_type()
            and c.fluent() in problem_static_fluents
        ]

    def _get_static_fluents(self) -> Set["up.model.fluent.Fluent"]:
        """Cached version of ``self._problem.get_static_fluents()``: that method rescans
        every action/effect/condition/metric in the problem on every call, but the set cannot
        change across a single grounding (the problem must not be modified after this class is
        constructed, same assumption `Simplifier` already makes)."""
        if self._static_fluents_cache is None:
            self._static_fluents_cache = self._problem.get_static_fluents()
        return self._static_fluents_cache

    def _get_domain_items(self, type: Type) -> List[FNode]:
        """Cached version of ``[domain_item(problem, type, j) for j in range(domain_size(...))]``:
        ``domain_item`` re-materializes ``list(objects_set.objects(typename))`` on every single
        call, so building one parameter's domain list this way is quadratic in its size."""
        cached = self._domain_items_cache.get(type)
        if cached is None:
            cached = [
                domain_item(self._problem, type, j)
                for j in range(domain_size(self._problem, type))
            ]
            self._domain_items_cache[type] = cached
        return cached

    def _fluent_true_arg_tuples(
        self, fluent: "up.model.fluent.Fluent"
    ) -> List[Tuple[FNode, ...]]:
        """Returns the argument tuples for which the given static boolean fluent is true,
        without materializing ``Problem.initial_values`` (which enumerates every grounding of
        every fluent in the problem, and is documented as expensive to call). Reproduces the
        same true/false-default semantics ``_bool_static_fluent_valid_parameters`` needs:
        - default True: every grounding is true except the explicitly-set non-True ones (the
          only case that needs to enumerate all groundings, via ``get_all_fluent_exp``).
        - default False, or no default at all: only the explicitly-set-True groundings are
          true; both cases are answered by ``explicit_initial_values`` alone, since a grounding
          with no explicit value and no default evaluates to `None` (absent), exactly like one
          with an explicit or defaulted False value.
        """
        cached = self._true_arg_tuples_cache.get(fluent)
        if cached is not None:
            return cached
        default_value = self._problem.fluents_defaults.get(fluent, None)
        result: List[Tuple[FNode, ...]]
        if default_value is not None and default_value.is_true():
            excluded = {
                tuple(key.args)
                for key, value in self._problem.explicit_initial_values.items()
                if key.fluent() == fluent and not value.is_true()
            }
            result = [
                tuple(exp.args)
                for exp in up.model.fluent.get_all_fluent_exp(self._problem, fluent)
                if tuple(exp.args) not in excluded
            ]
        else:
            result = [
                tuple(key.args)
                for key, value in self._problem.explicit_initial_values.items()
                if key.fluent() == fluent and value.is_true()
            ]
        self._true_arg_tuples_cache[fluent] = result
        return result

    def _purge_items_list(
        self, items_list: List[List[FNode]], params: List[Parameter], conds: List[FNode]
    ) -> List[List[FNode]]:
        """
        Calculates the combination of viable parameters to ground an action.
        Removes from the input items_list the objects that would always be not viable due to static fluents's values.

        :param items_list: The List of Lists of FNodes containing all the possible objects for the parameters.
        :param params: The List of Parameters for the action we are grounding.
        :param conds: The List of FNodes that represent the conditions we want to verify the validity of the parameters for.
        :return: the items_list input pruned off of the objects that would generate always invalid actions.
        """
        # NOTE: if a static fluent mentions the same parameter at more than one argument
        # position (e.g. a symmetric predicate applied as `sym(?x, ?x)`), every matching
        # position is intersected in, not just the first one found -- each is independently
        # sound, and using all of them is strictly stronger pruning than using only one.
        em = self._problem.environment.expression_manager
        return_list = []
        for param, object_list in zip(params, items_list):
            temp_list = list(object_list)
            param_exp = em.ParameterExp(param)
            for static_fluent in conds:
                for i, fp in enumerate(static_fluent.args):
                    if fp == param_exp:
                        valid_obj = self._bool_static_fluent_valid_parameters(
                            static_fluent, i
                        )
                        temp_list = [obj for obj in temp_list if obj in valid_obj]
            return_list.append(temp_list)
        return return_list

    def _bool_static_fluent_valid_parameters(self, sf: FNode, sp: int) -> Set[FNode]:
        cache_key = (sf, sp)
        cached = self._valid_params_cache.get(cache_key)
        if cached is not None:
            return cached
        fluent = sf.fluent()
        assert fluent in self._get_static_fluents()
        ret_val = {tup[sp] for tup in self._fluent_true_arg_tuples(fluent)}
        self._valid_params_cache[cache_key] = ret_val
        return ret_val


class Grounder(engines.engine.Engine, CompilerMixin):
    """
    Grounder class: the `Grounder` takes a :class:`~unified_planning.model.Problem` where the :class:`Actions <unified_planning.model.Action>`
    have :func:`Parameters <unified_planning.model.Action.parameters>` (meaning the `Actions` are lifted) and, through the :func:`~unified_planning.engines.mixins.CompilerMixin.compile`
    method, returns a `Problem` where every `Action` does not have `Parameters` (meaning the `Actions` are grounded).

    When an `Action` grounding creates an `Action` with conflicting :func:`Effects <unified_planning.model.InstantaneousAction.effects>`, or an `Action` with impossible
    :func:`conditions <unified_planning.model.InstantaneousAction.preconditions>`, the `Action` is discarded and not added to the final `Problem`.
    An `Action` grounding with no `Effects` at all is *not* discarded; it is added to the final `Problem` as-is.

    At construction time, the Grounder class can optionally take a map from `Action` to `List[Tuple[FNode, ...]]`. If this map is not None,
    it will be used for grounding instead of the implemented algorithm; the use of this parameter is mainly created to easily support
    the integration of external grounders inside the library. To see a practical example, checkout the :class:`~unified_planning.engines.compilers.TarskiGrounder` `_compile`
    implementation.
    The Grounder class can also optionally take a `prune_actions` flag to enable/disable the pruning of
    actions exploiting the simplification of static fluents -- see
    :func:`GrounderHelper.__init__ <unified_planning.engines.compilers.GrounderHelper>` for details.

    Interpreted functions are treated as ordinary sub-expressions: calls appearing in conditions, effect
    values and duration bounds have their arguments rewritten by the parameter substitution, exactly like
    any other fluent-based expression. Once an interpreted function call's arguments are all constant, the
    grounder's simplifier evaluates it and replaces the call with its value; while any argument is not
    constant, the call is left unevaluated.

    This `Compiler` supports only the `GROUNDING` :class:`~unified_planning.engines.CompilationKind`.
    """

    def __init__(
        self,
        grounding_actions_map: Optional[Dict[Action, List[Tuple[FNode, ...]]]] = None,
        prune_actions: bool = True,
    ):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.GROUNDING)
        self._grounding_actions_map = grounding_actions_map
        self._prune_actions = prune_actions

    @property
    def name(self):
        return "grounder"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_numbers("BOUNDED_TYPES")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_fluents_type("INT_FLUENTS")
        supported_kind.set_fluents_type("REAL_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_conditions_kind("INTERPRETED_FUNCTIONS_IN_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_effects_kind("FORALL_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("INTERPRETED_FUNCTIONS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("INTERPRETED_FUNCTIONS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("INTERPRETED_FUNCTIONS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECTS")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_time("SELF_OVERLAPPING")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("INT_TYPE_DURATIONS")
        supported_kind.set_expression_duration("REAL_TYPE_DURATIONS")
        supported_kind.set_expression_duration("INTERPRETED_FUNCTIONS_IN_DURATIONS")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_constraints_kind("STATE_INVARIANTS")
        supported_kind.set_constraints_kind("TRAJECTORY_CONSTRAINTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_initial_state("UNDEFINED_INITIAL_SYMBOLIC")
        supported_kind.set_initial_state("UNDEFINED_INITIAL_NUMERIC")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= Grounder.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.GROUNDING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        return problem_kind.clone()

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """
        Takes an instance of a :class:`~unified_planning.model.Problem` and the `GROUNDING` :class:`~unified_planning.engines.CompilationKind`
        and returns a `CompilerResult` where the problem does not have actions with parameters; so every action is grounded.

        :param problem: The instance of the `Problem` that must be grounded.
        :param compilation_kind: The `CompilationKind` that must be applied on the given problem;
            only `GROUNDING` is supported by this compiler
        :return: The resulting `CompilerResult` data structure.
        """
        assert isinstance(problem, Problem), (
            "The given problem is not a class supported by the Grounder"
        )
        grounder_helper = GrounderHelper(
            problem, self._grounding_actions_map, self._prune_actions
        )
        trace_back_map: Dict[Action, Tuple[Action, List[FNode]]] = {}

        if type(problem) is Problem:
            # _clone_without_actions() skips deep-cloning every lifted action.
            # Restricted to the exact Problem class: Problem subclasses
            # like HierarchicalProblem/ContingentProblem hand-roll their own clone() that
            # _clone_without_actions() knows nothing about, and calling the inherited
            # Problem._clone_without_actions() on one of them would silently construct a
            # plain Problem, downgrading it and dropping its subclass-only state.
            new_problem = problem._clone_without_actions()
        else:
            new_problem = problem.clone()
            new_problem.clear_actions()
        new_problem.name = f"{self.name}_{problem.name}"
        for (
            old_action,
            parameters,
            new_action,
        ) in grounder_helper.get_grounded_actions():
            if new_action is not None:
                new_problem.add_action(new_action)
                trace_back_map[new_action] = (old_action, list(parameters))

        new_problem.clear_quality_metrics()
        for qm in problem.quality_metrics:
            if qm.is_minimize_action_costs():
                assert isinstance(qm, MinimizeActionCosts)
                new_metric = ground_minimize_action_costs_metric(
                    qm, trace_back_map, grounder_helper.simplifier
                )
                new_problem.add_quality_metric(new_metric)
            else:
                new_problem.add_quality_metric(qm)

        return CompilerResult(
            new_problem,
            partial(lift_action_instance, map=trace_back_map),
            self.name,
        )


def ground_minimize_action_costs_metric(
    metric: MinimizeActionCosts,
    trace_back_map: Dict[Action, Tuple[Action, List[FNode]]],
    simplifier: Simplifier,
) -> MinimizeActionCosts:
    """
    Support method for a grounder to handle the MinimizeActionCosts metric.

    :param metric: The metric to convert.
    :param trace_back_map: The grounding map from a grounded Action to the Action
        and parameters that created the grounded action.
    :param simplifier: The simplifier used to evaluate the cost; if this simplifier
        has the Instance of the problem at construction time, it will also substitute
        the static fluents in the action cost with their value.
    :return: The equivalent MinimizeActionCosts metric for the grounded problem.
    """
    new_costs: Dict[Action, Expression] = {}
    for new_action, (old_action, params) in trace_back_map.items():
        subs = cast(
            Dict[Expression, Expression],
            dict(zip(old_action.parameters, params)),
        )
        old_cost = metric.get_action_cost(old_action)
        if old_cost is not None:
            new_costs[new_action] = simplifier.simplify(old_cost.substitute(subs))
    return MinimizeActionCosts(new_costs)
