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


def name_of(item: Any) -> str:
    """Default `NameIndex` key. Deliberately a module-level function and not a lambda: a
    `NameIndex` is instance state of a `Problem`/`Agent`, and whole problems are pickled to be
    sent to other processes (see `unified_planning/engines/parallel.py`, which uses the `spawn`
    start method outside Linux), which a closure defined inside `__init__` would break."""
    return item.name


class NameIndex(Generic[T]):
    """A lazily-rebuilt ``name -> element`` index over a list of named elements.

    The index is guarded by an identity+length token against the list it was built from, so
    it self-heals (at the cost of one O(n) rebuild) against every way the underlying list can
    change without going through :func:`note_appended`: wholesale reassignment (every
    ``clone()``/``_clone_to`` path in this library replaces the list outright) or in-place
    removal (``list.remove(...)``, used to drop a fluent). The one case this does not catch is
    renaming an already-indexed element in place without changing the list's identity or
    length (`Action.name` has a public setter) -- that was already unguarded before this index
    existed, so this does not regress anything.

    Preserves the original linear scan's first-occurrence semantics: when
    ``Environment.error_used_name`` is disabled, two elements may share a name, and both
    ``contains``/``get`` must agree with what a scan of the list in order would have found.
    """

    __slots__ = ("_key", "_index", "_items", "_len")

    def __init__(self, key: Callable[[T], str] = name_of) -> None:
        """:param key: Extracts the name from an element. Fixed for the lifetime of this
        index -- every element in the indexed list is expected to be named the same way."""
        self._key = key
        self._index: Optional[Dict[str, T]] = None
        self._items: Optional[List[T]] = None
        self._len: int = -1

    def __getstate__(self):
        # `_index`/`_items`/`_len` are a pure cache over a list this object does not own; don't
        # carry them across a pickle round-trip (whole problems are sent to other processes),
        # just let the next lookup rebuild it.
        return (None, {"_key": self._key, "_index": None, "_items": None, "_len": -1})

    def _refresh(self, items: List[T]) -> None:
        if self._index is None or self._items is not items or self._len != len(items):
            index: Dict[str, T] = {}
            for item in items:
                name = self._key(item)
                if name not in index:  # keep first occurrence, like a linear scan would
                    index[name] = item
            self._index = index
            self._items = items
            self._len = len(items)

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
        the next `contains`/`get` call rebuilds from scratch."""
        if (
            self._index is not None
            and self._items is items
            and self._len == len(items) - 1
        ):
            last = items[-1]
            name = self._key(last)
            if name not in self._index:  # keep first occurrence
                self._index[name] = last
            self._len = len(items)
