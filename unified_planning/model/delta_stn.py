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


from collections import deque
from dataclasses import dataclass
from numbers import Real
from typing import Deque, Dict, Optional, Any, Generic, TypeVar, cast


T = TypeVar("T", bound=Real)


@dataclass
class DeltaNeighbors(Generic[T]):
    """
    This data structure is used in the `DeltaSimpleTemporalNetwork` to
    represent the constraints. Every Neighbor has a destination (dst),
    a distance (bound) and optionally points to another Neighbor.
    """

    dst: Any
    bound: T
    next: Optional["DeltaNeighbors"]


class DeltaSimpleTemporalNetwork(Generic[T]):
    """
    This class represent a SimpleTemporalNetwork (STN). A STN is a data
    structure that contains temporal constraints between elements (called
    `Events` in this specific use-case).

    If the STN is consistent, it means that the added temporal constraints
    between the `Events` are feasible; in other words, for every `Event` in
    the STN, it exists a temporal assignment that does not violate any
    constraint. When the STN becomes inconsistent, it means that the added
    constraints are too restraining, therefore an assignment that does not
    violate any constraint does not exist.

    This specific implementation, called DeltaSTN, is specifically engineered
    to re-use previous calculations, using the incremental Bellman-Ford
    algorithm. This fits very well the planning use-case, where a lot of STN
    with small differences one-another are used.
    """

    def __init__(
        self,
        constraints: Optional[Dict[Any, Optional[DeltaNeighbors[T]]]] = None,
        distances: Optional[Dict[Any, T]] = None,
        is_sat: bool = True,
        epsilon: T = cast(T, 0),
    ):
        self._constraints: Dict[Any, Optional[DeltaNeighbors[T]]] = (
            constraints if constraints is not None else {}
        )
        self._distances: Dict[Any, T] = distances if distances is not None else {}
        self._is_sat = is_sat
        self._epsilon: T = epsilon

    def __repr__(self) -> str:
        res = []
        for k, v in self._constraints.items():
            while v is not None:
                res.append(f"{k} - {v.dst} <= {v.bound}")
                v = v.next
        return "\n".join(res)

    def __contains__(self, value: Any) -> bool:
        return value in self._distances

    def copy_stn(self) -> "DeltaSimpleTemporalNetwork":
        """
        Returns another STN with all the constraints already present
        in self.
        """
        return DeltaSimpleTemporalNetwork(
            self._constraints.copy(),
            self._distances.copy(),
            self._is_sat,
            self._epsilon,
        )

    def add(self, x: Any, y: Any, b: T):
        """
        Adds the constraint `x - y <= b`. This gives an upper bound
        to the distance from `x` to `y`. TODO explain  this better!
        """
        if self._is_sat:
            self._distances.setdefault(x, cast(T, 0))
            self._distances.setdefault(y, cast(T, 0))
            x_constraints = self._constraints.get(x, None)
            self._constraints.setdefault(y, None)
            if not self._is_subsumed(x, y, b):
                neighbor = DeltaNeighbors(y, b, x_constraints)
                self._constraints[x] = neighbor
                self._is_sat = self._inc_check(x, y, b)

    def check_stn(self) -> bool:
        """Checks the consistency of this STN."""
        return self._is_sat

    def get_stn_model(self, x: Any) -> T:
        return cast(T, -1 * self._distances[x])

    def _is_subsumed(self, x: Any, y: Any, b: T) -> bool:
        neighbor = self._constraints.get(x, None)
        while neighbor is not None:
            if neighbor.dst == y:
                return neighbor.bound <= b
            neighbor = neighbor.next
        return False

    def _inc_check(self, x: Any, y: Any, b: T) -> bool:
        if self._distances[x] + b < self._distances[y]:
            self._distances[y] = self._distances[x] + b
        else:
            return True
        queue: Deque[Any] = deque()
        queue.append(y)
        while queue:
            c = queue.popleft()
            n = self._constraints[c]
            while n is not None:
                if self._distances[c] + n.bound < self._distances[n.dst]:
                    if n.dst == y and abs(n.bound - b) <= self._epsilon:
                        return False
                    self._distances[n.dst] = self._distances[c] + n.bound
                    queue.append(n.dst)
                n = n.next
        return True
