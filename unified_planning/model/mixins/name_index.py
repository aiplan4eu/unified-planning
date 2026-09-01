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

"""A small self-validating name index shared by the `*SetMixin` classes.

`ActionsSetMixin`/`FluentsSetMixin`/`ObjectsSetMixin`/`UserTypesSetMixin` each keep their
elements in a plain `list` and used to look an element up by name with a linear scan
(`has_action`, `action(name)`, ...). Since every element is added through `add_action`/
`add_fluent`/..., adding N elements one at a time made that assembly step O(N^2).
"""

from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")

# Global counter bumped every time an already-indexed element has its name changed in place
# (see `Transition.name`'s setter). A `NameIndex(track_renames=True)` stamps the counter's
# current value onto itself whenever it (re)builds, and treats a mismatch at the next lookup
# as "stale, rebuild" -- exactly like its existing identity/length token, just for a change
# the list itself can't reveal. Deliberately global and coarse (one rename anywhere
# invalidates every opted-in index) rather than a per-element notification: there is only one
# indexed element kind with a mutable name (`Action`, via `Transition.name`), so a shared
# counter is simpler than wiring each index up as an observer of each of its elements.
_rename_epoch: int = 0


def note_renamed() -> None:
    """Call whenever an element some `NameIndex(track_renames=True)` may be holding has had
    its name changed in place, so the next lookup rebuilds instead of trusting a mapping that
    may now point at the wrong key."""
    global _rename_epoch
    _rename_epoch += 1


def current_rename_epoch() -> int:
    return _rename_epoch


def name_of(item: Any) -> str:
    """Default `NameIndex` key. Deliberately a module-level function and not a lambda: a
    `NameIndex` is instance state of a `Problem`/`Agent`, and whole problems are pickled to be
    sent to other processes (see `unified_planning/engines/parallel.py`, which uses the `spawn`
    start method outside Linux), which a closure defined inside `__init__` would break."""
    return item.name


class NameIndex(Generic[T]):
    """A lazily-rebuilt ``name -> element`` index over a list of named elements.

    The index is guarded by an identity+length token against the list it was built from, so
    it self-heals (at the cost of one O(n) rebuild) when the list is reassigned wholesale
    (every ``clone()``/``_clone_to``/``clear_*`` path in this library replaces the list
    outright) or changes length.

    That token is deliberately cheap, and cheap means it cannot see two kinds of change:

    * **In-place removal.** ``list.remove(...)`` followed by an append restores the original
      length on the same list object, so neither half of the token moves and the index keeps
      answering with the removed element while missing the appended one. Every remover must
      therefore call :func:`invalidate` -- which is why removing a fluent goes through
      ``FluentsSetMixin._remove_fluent`` rather than touching ``_fluents`` directly.
    * **Renaming an already-indexed element** (`Action.name` has a public setter) changes
      neither the list's identity nor its length either, and gets its own guard: pass
      ``track_renames=True`` and every indexed element is stamped (via its
      ``_note_indexed()``) so that its `name` setter can call :func:`note_renamed`, which
      this index checks against on every lookup (see :data:`_rename_epoch`). Only elements
      with a mutable ``name`` need this -- currently just `Action`/`DurativeAction` via
      `Transition.name` -- so only `ActionsSetMixin` passes ``track_renames=True``;
      `Fluent`/`Object`/the user-type index have no name setter and pay nothing extra.

    Preserves the original linear scan's first-occurrence semantics: when
    ``Environment.error_used_name`` is disabled, two elements may share a name, and both
    ``contains``/``get`` must agree with what a scan of the list in order would have found.
    """

    __slots__ = ("_key", "_index", "_items", "_len", "_track_renames", "_epoch")

    def __init__(
        self, key: Callable[[T], str] = name_of, track_renames: bool = False
    ) -> None:
        """:param key: Extracts the name from an element. Fixed for the lifetime of this
        index -- every element in the indexed list is expected to be named the same way.
        :param track_renames: Whether the indexed elements can have their name changed in
            place after being indexed; see the class docstring."""
        self._key = key
        self._index: Optional[Dict[str, T]] = None
        self._items: Optional[List[T]] = None
        self._len: int = -1
        self._track_renames = track_renames
        self._epoch: int = -1

    def __getstate__(self):
        # `_index`/`_items`/`_len`/`_epoch` are a pure cache over a list this object does not
        # own; don't carry them across a pickle round-trip (whole problems are sent to other
        # processes), just let the next lookup rebuild it.
        return (
            None,
            {
                "_key": self._key,
                "_index": None,
                "_items": None,
                "_len": -1,
                "_track_renames": self._track_renames,
                "_epoch": -1,
            },
        )

    def invalidate(self) -> None:
        """Drops the index, forcing a full rebuild on the next lookup. Must be called after
        any in-place change to the indexed list that leaves its identity and length intact --
        see the class docstring."""
        self._index = None
        self._items = None
        self._len = -1

    def _refresh(self, items: List[T]) -> None:
        stale_rename = self._track_renames and self._epoch != current_rename_epoch()
        if (
            self._index is None
            or self._items is not items
            or self._len != len(items)
            or stale_rename
        ):
            index: Dict[str, T] = {}
            for item in items:
                name = self._key(item)
                if name not in index:  # keep first occurrence, like a linear scan would
                    index[name] = item
                if self._track_renames:
                    item._note_indexed()  # type: ignore[attr-defined]
            self._index = index
            self._items = items
            self._len = len(items)
            self._epoch = current_rename_epoch()

    def contains(self, items: List[T], name: str) -> bool:
        self._refresh(items)
        assert self._index is not None
        return name in self._index

    def get(self, items: List[T], name: str) -> Optional[T]:
        self._refresh(items)
        assert self._index is not None
        return self._index.get(name)

    def note_appended(self, items: List[T]) -> None:
        """Call right after appending exactly one element to `items`, to keep the index
        O(1) amortized instead of forcing a full rebuild on the next lookup. Safe to call
        even when the index is stale or was never built: it then simply does nothing, and
        the next `contains`/`get` call rebuilds from scratch.

        Also does nothing (deferring to that same full rebuild) when `track_renames` is set
        and a rename has invalidated this index since it was last built: patching just the
        newly appended element in would leave every earlier element's stale entry in place,
        silently keeping it stale for another round instead of catching it up."""
        if (
            self._index is not None
            and self._items is items
            and self._len == len(items) - 1
            and not (self._track_renames and self._epoch != current_rename_epoch())
        ):
            last = items[-1]
            name = self._key(last)
            if name not in self._index:  # keep first occurrence
                self._index[name] = last
            if self._track_renames:
                last._note_indexed()  # type: ignore[attr-defined]
            self._len = len(items)
