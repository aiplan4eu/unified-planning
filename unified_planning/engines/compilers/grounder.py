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

from functools import partial
from itertools import product
from typing import Dict, Iterator, List, NamedTuple, Optional, Set, Tuple, cast

import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.compilers.utils import (
    create_action_with_given_subs,
    lift_action_instance,
    split_all_ands,
)
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model import (
    Action,
    Expression,
    FNode,
    MinimizeActionCosts,
    Parameter,
    Problem,
    ProblemKind,
    Type,
)
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.model.types import domain_item, domain_size
from unified_planning.model.walkers import Simplifier


class _AtomPattern(NamedTuple):
    """How one static-fluent atom's argument positions map onto an action's parameters.

    `param_positions` and `const_positions` list only the positions that constrain anything;
    an argument that is neither a bare parameter nor a constant (a nested expression, an
    object-fluent call) appears in neither and only sets `has_wildcard` -- the same blind spot
    the per-parameter fallback pruning has.
    """

    param_positions: List[Tuple[int, int]]  # (argument index, action-parameter column)
    const_positions: List[Tuple[int, FNode]]  # (argument index, value it must equal)
    columns: Set[int]  # the action-parameter columns this atom constrains
    has_wildcard: bool


def _classify_atom(atom: FNode, param_expr_to_column: Dict[FNode, int]) -> _AtomPattern:
    param_positions: List[Tuple[int, int]] = []
    const_positions: List[Tuple[int, FNode]] = []
    has_wildcard = False
    for i, arg in enumerate(atom.args):
        column = param_expr_to_column.get(arg)
        if column is not None:
            param_positions.append((i, column))
        elif arg.is_constant():
            const_positions.append((i, arg))
        else:
            has_wildcard = True
    return _AtomPattern(
        param_positions,
        const_positions,
        {column for _, column in param_positions},
        has_wildcard,
    )


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

    DEFAULT_JOIN_MAX_CANDIDATES = 1_000_000

    def __init__(
        self,
        problem: Problem,
        grounding_actions_map: Optional[Dict[Action, List[Tuple[FNode, ...]]]] = None,
        prune_actions: bool = True,
        join_max_candidates: int = DEFAULT_JOIN_MAX_CANDIDATES,
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
            parameter type, a candidate count above `join_max_candidates`, or any unexpected condition --
            that one action falls back to the weaker (but always sound) per-parameter-independent pruning:
            each parameter is narrowed, independently of the others, to the objects that appear at a
            matching argument position of some true static fluent in the action's precondition. If
            `False`, no pruning at all is done.
        :param join_max_candidates: Safety valve for the join part of `prune_actions`: for one
            action, once its running candidate count exceeds this, the join gives up and that
            action falls back to the per-parameter-independent pruning instead. A value `<= 0`
            disables the join outright (every action uses the fallback), which is mainly useful
            to test the fallback path itself in isolation.
        """
        assert isinstance(problem, Problem)
        self._problem = problem
        self._grounding_actions_map = grounding_actions_map
        self._prune_actions = prune_actions
        self._join_max_candidates = join_max_candidates
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
            "up.model.fluent.Fluent", Optional[List[Tuple[FNode, ...]]]
        ] = {}
        self._domain_items_cache: Dict[Type, List[FNode]] = {}
        self._valid_params_cache: Dict[
            Tuple["up.model.fluent.Fluent", int], Optional[Set[FNode]]
        ] = {}
        env = problem.environment
        if prune_actions:
            self._simplifier = Simplifier(env, problem)
        else:
            self._simplifier = env.simplifier

    @property
    def simplifier(self) -> Simplifier:
        return self._simplifier

    def ground_action(
        self, action: Action, parameters: Tuple[FNode, ...] = ()
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
                res: Iterator[Tuple[FNode, ...]] = iter([()])
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
                if self._prune_actions and isinstance(
                    action,
                    (
                        up.model.action.InstantaneousAction,
                        up.model.action.DurativeAction,
                    ),
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

    def _compute_join_pruned_parameters(
        self, action: Action, type_list: List[Type]
    ) -> Optional[List[Tuple[FNode, ...]]]:
        """Hash-joins `action`'s eligible static fluents (`_static_bool_fluents`) against their
        true argument tuples (`_fluent_true_arg_tuples`), incrementally building only the
        parameter tuples consistent with every joined fluent -- instead of pruning each
        parameter independently, which cannot see a static predicate
        that correlates several of the action's parameters together and so ends up enumerating
        their full cross product.

        Returns `None` if the join isn't applicable/safe for this action. Every documented
        bail-out stays silent: the join is disabled (`self._join_max_candidates <= 0`), the
        action type is unrecognized (a plain `return None`, not an exception), the candidate
        count exceeds `self._join_max_candidates`, or a parameter type is unbounded/
        unenumerable (`domain_size`/`domain_item` raise `UPProblemDefinitionError` for those --
        see `unified_planning/model/types.py`). Any other exception is treated as an internal
        bug rather than an expected bail-out and is left to propagate to the caller, instead
        of being swallowed into the same silent `None` as the documented bail-outs above.
        """
        if self._join_max_candidates <= 0:
            return None
        try:
            return self._compute_join_pruned_parameters_unsafe(action, type_list)
        except UPProblemDefinitionError:
            return None

    def _compute_join_pruned_parameters_unsafe(
        self, action: Action, type_list: List[Type]
    ) -> Optional[List[Tuple[FNode, ...]]]:
        """Given one action and the type domains of its parameters, return the exact
        list of parameter tuples that satisfy all of the action's static-boolean-fluent
        conditions -- computed via a relational hash-join instead of `_purge_items_list`'s
        per-parameter (independent) pruning. Returns `None` when it can't safely do this
        (unrecognized action, unbounded type, candidate blow-up, or any exception).

        It's a classic database join: each static fluent is a "table" of rows (the argument
        tuples it is true for), and they are folded in one at a time, joining on the
        action-parameter columns two fluents share and narrowing a running result set
        (`bindings`, a partial column -> object map per surviving row). Parameter columns no
        fluent ever constrains stay free and are cross-producted in at the end. Every step
        is bounded by `self._join_max_candidates`, which sends the whole action back to the
        per-parameter fallback rather than let an intermediate result blow up.

        Example -- `deliver(?r: Robot, ?l: Location, ?p: Package)`, columns 0=r, 1=l, 2=p,
        domains `Robot={r1,r2}`, `Location={l1,l2}`, `Package={p1,p2}`, static conditions
        `robot_can_carry(?r,?p)` true for `(r1,p1), (r1,p2), (r2,p1)` and `package_at(?p,?l)`
        true for `(p1,l1), (p2,l2)`. Per-parameter pruning shrinks nothing here, because each
        of the six objects does appear in some true tuple, so all 8 combinations survive --
        including `(r2, l2, p2)`, even though r2 never carries p2. The join folds in
        `robot_can_carry` to `{0:r1,2:p1}, {0:r1,2:p2}, {0:r2,2:p1}`, then joins `package_at`
        on their shared column 2, where `p1` only pairs with `l1` and `p2` only with `l2`,
        leaving the 3 jointly-consistent tuples `(r1,l1,p1), (r1,l2,p2), (r2,l1,p1)`.

        The finished tuples are sorted back into `itertools.product(*param_domains)` order, so
        an action the join doesn't improve on keeps exactly the ground-action naming and
        ordering the fallback would have given it.
        """
        params = list(action.parameters)
        num_params = len(params)
        if num_params == 0:
            return [()]
        static_fluents = self._static_bool_fluents(action)
        if static_fluents is None:
            # Not an InstantaneousAction/DurativeAction -- an action type this file doesn't
            # know how to read preconditions/conditions from.
            return None

        em = self._problem.environment.expression_manager
        param_domains = [self._get_domain_items(t) for t in type_list]
        domain_sets = [set(d) for d in param_domains]
        param_expr_to_column = {em.ParameterExp(p): i for i, p in enumerate(params)}

        # The running join result: each element maps a column index to the object bound there
        # by every atom folded in so far. The lone empty binding stands for "nothing
        # constrained yet", and folds into the first atom's rows as the identity.
        bindings: List[Dict[int, FNode]] = [{}]
        bound_columns: Set[int] = set()

        for static_fluent in static_fluents:
            pattern = _classify_atom(static_fluent, param_expr_to_column)
            if not pattern.columns:
                # Mentions no action parameter, so it can prune nothing.
                continue

            true_arg_tuples = self._fluent_true_arg_tuples(static_fluent.fluent())
            if true_arg_tuples is None:
                # Over budget to enumerate. Skipping one conjunct only ever weakens the
                # pruning, never makes it unsound, and it keeps the join's benefit for this
                # action's other atoms -- bailing out to `None` would throw that away too.
                continue

            rows = self._atom_rows(pattern, true_arg_tuples, domain_sets)
            if rows is None:
                return None
            merged = self._merge_bindings(
                bindings, bound_columns, rows, pattern.columns
            )
            if merged is None:
                return None
            bindings = merged
            bound_columns |= pattern.columns
            if not bindings:
                # Nothing can satisfy every atom folded in so far, so no later one matters.
                break

        # A column no atom constrained keeps its whole domain, exactly as the per-parameter
        # fallback leaves a column it cannot prune.
        free_columns = [i for i in range(num_params) if i not in bound_columns]
        free_domains = [param_domains[i] for i in free_columns]
        free_size = 1
        for domain in free_domains:
            free_size *= len(domain)
        if len(bindings) * free_size > self._join_max_candidates:
            # Even a small constrained part can blow the budget once every free column is
            # crossed in.
            return None

        tuples: List[Tuple[FNode, ...]] = []
        for binding in bindings:
            if free_columns:
                for combo in product(*free_domains):
                    full_binding = dict(binding)
                    full_binding.update(zip(free_columns, combo))
                    tuples.append(tuple(full_binding[i] for i in range(num_params)))
            else:
                tuples.append(tuple(binding[i] for i in range(num_params)))

        # Must match `itertools.product(*param_domains)`'s own order (lexicographic by each
        # parameter's index within its own type's domain), so ground-action naming and
        # ordering don't silently change for an action the join doesn't improve on.
        domain_position = [{obj: j for j, obj in enumerate(d)} for d in param_domains]
        tuples.sort(
            key=lambda ground_tuple: tuple(
                domain_position[i][ground_tuple[i]] for i in range(num_params)
            )
        )
        return tuples

    def _atom_rows(
        self,
        pattern: _AtomPattern,
        true_arg_tuples: List[Tuple[FNode, ...]],
        domain_sets: List[Set[FNode]],
    ) -> Optional[List[Dict[int, FNode]]]:
        """One atom's contribution to the join: the distinct column -> object bindings its
        true tuples allow, or `None` if there are more than `_join_max_candidates` of them.

        A `True`-default fluent over N objects has N**arity true tuples, so this is checked
        as the rows accumulate rather than after, and independently of how small `bindings`
        still is.
        """
        rows: List[Dict[int, FNode]] = []
        seen: Set[Tuple[FNode, ...]] = set()
        row_columns = sorted(pattern.columns)
        for true_args in true_arg_tuples:
            if any(true_args[i] != wanted for i, wanted in pattern.const_positions):
                continue
            binding: Dict[int, FNode] = {}
            for i, column in pattern.param_positions:
                value = true_args[i]
                # An object reached through this atom must belong to the ACTION PARAMETER's
                # own domain, not merely to the fluent's declared parameter type, which may
                # be a supertype of it; skipping this binds an ill-typed object.
                if value not in domain_sets[column]:
                    break
                # A parameter at more than one position of the same atom (`sym(?x, ?x)`) has
                # to agree with itself, not just be well-typed at each occurrence.
                if binding.setdefault(column, value) != value:
                    break
            else:
                if pattern.has_wildcard:
                    # A wildcard position is never projected into the binding, so two true
                    # tuples differing only there collapse onto one row. Left in, that row
                    # survives every later merge and the same parameter tuple gets grounded
                    # twice, which `Problem.add_action` rejects as a duplicate name. With no
                    # wildcard the projection is injective and there is nothing to catch.
                    key = tuple(binding[c] for c in row_columns)
                    if key in seen:
                        continue
                    seen.add(key)
                rows.append(binding)
                if len(rows) > self._join_max_candidates:
                    return None
        return rows

    def _merge_bindings(
        self,
        bindings: List[Dict[int, FNode]],
        bound_columns: Set[int],
        rows: List[Dict[int, FNode]],
        atom_columns: Set[int],
    ) -> Optional[List[Dict[int, FNode]]]:
        """Folds one atom's `rows` into the running `bindings`, or `None` if the result would
        exceed `_join_max_candidates`.

        Joins on the columns both sides constrain; with no column in common there is no join
        key and the two are crossed instead -- still correct, just not filtering.
        """
        shared_columns = sorted(bound_columns & atom_columns)
        if not shared_columns:
            # The size is exactly len(bindings) * len(rows), so check it before building.
            if len(bindings) * len(rows) > self._join_max_candidates:
                return None
            return [{**left, **right} for left in bindings for right in rows]

        # Index `rows` by their shared-column values once, then probe once per existing
        # binding, instead of testing every (binding, row) pair.
        rows_by_shared_key: Dict[Tuple[FNode, ...], List[Dict[int, FNode]]] = {}
        for row in rows:
            rows_by_shared_key.setdefault(
                tuple(row[i] for i in shared_columns), []
            ).append(row)
        joined_rows: List[Dict[int, FNode]] = []
        for left in bindings:
            for right in rows_by_shared_key.get(
                tuple(left[i] for i in shared_columns), ()
            ):
                joined_rows.append({**left, **right})
                # Checked as the result accumulates: a join of two large tables can blow the
                # budget well before either operand's own size would suggest.
                if len(joined_rows) > self._join_max_candidates:
                    return None
        return joined_rows

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
    ) -> Optional[List[Tuple[FNode, ...]]]:
        """Returns the argument tuples for which the given static boolean fluent is true, or
        `None` when building that list would cost more than `_join_max_candidates` rows -- in
        which case the caller must prune nothing with this fluent rather than pay for it.

        Avoids materializing ``Problem.initial_values`` (which enumerates every grounding of
        every fluent in the problem, and is documented as expensive to call), reproducing the
        same true/false-default semantics ``_bool_static_fluent_valid_parameters`` needs:
        - default True: every grounding is true except the explicitly-set non-True ones. This
          is the only case that has to enumerate all groundings, hence the only one that needs
          the budget check -- its size is the product of the argument types' domain sizes,
          N**arity for N objects, which is cheap to compute up front and is checked before
          anything is built. A type with no enumerable domain (``domain_size`` raises) can't
          be materialized at all and counts as over budget. Within budget, the enumeration
          itself is a product over each argument type's own cached domain-item list
          (``_get_domain_items``) rather than ``get_all_fluent_exp``, which would call
          ``fluent(*args)`` once per grounding and intern a fresh ``FNode`` for each into the
          `Environment`'s own memo (unbounded, and it outlives this `GrounderHelper` --
          usually forever, since most callers use the global environment) even though the
          budget check already bounds how many groundings that could be. Only the iteration
          order differs from ``get_all_fluent_exp``, which no caller observes: the join sorts
          its output canonically, and `_bool_static_fluent_valid_parameters` folds the result
          into a set.
        - default False, or no default at all: only the explicitly-set-True groundings are
          true; both cases are answered by ``explicit_initial_values`` alone (which the
          problem already holds, so there is nothing to bound), since a grounding with no
          explicit value and no default evaluates to `None` (absent), exactly like one with
          an explicit or defaulted False value.
        """
        if fluent in self._true_arg_tuples_cache:  # `None` is a real cached answer here
            return self._true_arg_tuples_cache[fluent]
        result: Optional[List[Tuple[FNode, ...]]]
        default_value = self._problem.fluents_defaults.get(fluent, None)
        if default_value is not None and default_value.is_true():
            budget = (
                self._join_max_candidates
                if self._join_max_candidates > 0
                else self.DEFAULT_JOIN_MAX_CANDIDATES
            )
            result = []
            size = 1
            for param in fluent.signature:
                try:
                    size *= domain_size(self._problem, param.type)
                except UPProblemDefinitionError:
                    result = None
                    break
                if size > budget:
                    result = None
                    break
            if result is not None:
                excluded = {
                    tuple(key.args)
                    for key, value in self._problem.explicit_initial_values.items()
                    if key.fluent() == fluent and not value.is_true()
                }
                domains = [self._get_domain_items(p.type) for p in fluent.signature]
                result = [args for args in product(*domains) if args not in excluded]
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
                        if valid_obj is not None:
                            temp_list = [obj for obj in temp_list if obj in valid_obj]
            return_list.append(temp_list)
        return return_list

    def _bool_static_fluent_valid_parameters(
        self, sf: FNode, sp: int
    ) -> Optional[Set[FNode]]:
        """The objects that may appear at argument position `sp` of the static boolean fluent
        expression `sf`, or `None` when that cannot be answered within
        `_fluent_true_arg_tuples`'s budget -- in which case the caller must prune nothing
        for this position rather than enumerate the relation.
        """
        # Keyed on (fluent, sp) rather than (sf, sp): the body below only ever depends on
        # sf.fluent() and sp, never on sf's actual arguments, so keying on the whole atom
        # missed cache hits across different atoms over the same fluent (and across actions).
        fluent = sf.fluent()
        cache_key = (fluent, sp)
        if cache_key in self._valid_params_cache:
            return self._valid_params_cache[cache_key]
        assert fluent in self._get_static_fluents()
        true_arg_tuples = self._fluent_true_arg_tuples(fluent)
        ret_val: Optional[Set[FNode]] = (
            None if true_arg_tuples is None else {tup[sp] for tup in true_arg_tuples}
        )
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
    actions exploiting the simplification of static fluents, and a `join_max_candidates` safety-valve
    threshold for that pruning's join -- see
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
        join_max_candidates: int = GrounderHelper.DEFAULT_JOIN_MAX_CANDIDATES,
    ):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.GROUNDING)
        self._grounding_actions_map = grounding_actions_map
        self._prune_actions = prune_actions
        self._join_max_candidates = join_max_candidates

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
            problem,
            self._grounding_actions_map,
            self._prune_actions,
            self._join_max_candidates,
        )
        trace_back_map: Dict[Action, Tuple[Action, List[FNode]]] = {}

        if type(problem) is Problem:
            # _clone_to_without_actions_and_metrics() skips deep-cloning every lifted action
            # (and drops quality metrics, rebuilt below via ground_minimize_action_costs_metric).
            # Restricted to the exact Problem class: Problem subclasses
            # like HierarchicalProblem/ContingentProblem hand-roll their own clone() that
            # _clone_to_without_actions_and_metrics() knows nothing about, and calling it
            # on one of them would silently drop its subclass-only state.
            new_problem = Problem(problem.name, problem.environment)
            problem._clone_to_without_actions_and_metrics(new_problem)
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
