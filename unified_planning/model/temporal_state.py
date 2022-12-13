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
from fractions import Fraction
from typing import Deque, Dict, List, Optional, Any, Set
import unified_planning as up
from unified_planning.model.state import UPCOWState, COWState
from unified_planning.exceptions import UPUsageError


@dataclass
class DeltaNeighbors:
    dst: Any
    bound: Fraction
    next: Optional["DeltaNeighbors"]


class DeltaSimpleTemporalNetwork:
    def __init__(
        self,
        constraints: Dict[Any, DeltaNeighbors] = {},
        distances: Dict[Any, Fraction] = {},
        is_sat=True,
    ):
        self._constraints: Dict[Any, List[DeltaNeighbors]] = constraints
        self._distances: Dict[Any, Fraction] = distances
        self._is_sat = is_sat

    def __repr__(self) -> str:
        res = []
        for k, v in self._constraints.items():
            while v is not None:
                res.append(f"{k} - {v.dst} <= {v.bound}")
                v = v.next
        return "\n".join(res)

    def copy_stn(self) -> "DeltaSimpleTemporalNetwork":
        return DeltaSimpleTemporalNetwork(
            self._constraints.copy(), self._distances.copy(), self._is_sat
        )

    def add(self, x: Any, y: Any, b: Fraction):
        if self._is_sat:
            self._distances.setdefault(x, Fraction(0))
            self._distances.setdefault(y, Fraction(0))
            x_constraints = self._constraints.get(x, None)
            self._constraints.setdefault(y, None)
            if not self._is_subsumed(x, y, b):
                neighbor = DeltaNeighbors(y, b, x_constraints)
                self._constraints[x] = neighbor
                self._is_sat = self._inc_check(x, y, b)

    def check_stn(self) -> bool:
        return self._is_sat

    def get_stn_model(self, x: Any) -> Fraction:
        return -1 * self._distances[x]

    def _is_subsumed(self, x: Any, y: Any, b: Fraction) -> bool:
        neighbor = self._constraints.get(x, None)
        while neighbor is not None:
            if neighbor.dst == y:
                return neighbor.bound <= b
            neighbor = neighbor.next
        return False

    def _inc_check(self, x: Any, y: Any, b: Fraction) -> bool:
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
                    if n.dst == y and n.bound == b:
                        return False
                    self._distances[n.dst] = self._distances[c] + n.bound
                    queue.append(n.dst)
                n = n.next
        return True


class TemporalState(UPCOWState):
    MAX_ANCESTORS: Optional[int] = None

    def __init__(
        self,
        values: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"],
        running_events: List[List["up.engines.mixins.simulator.Event"]],
        stn: "DeltaSimpleTemporalNetwork",
        durative_conditions: List[List["up.model.fnode.FNode"]],
        last_events: Set["up.engines.mixins.simulator.Event"],
        _father: Optional["TemporalState"] = None,
    ):
        if type(self).MAX_ANCESTORS is not None:
            raise UPUsageError("A Temporal State needs the MAX_ANCESTORS to be None.")
        UPCOWState.__init__(self, values, _father)
        self._running_events = running_events
        self._stn = stn
        self._durative_conditions = durative_conditions
        self._last_events = last_events

    @property
    def running_events(self) -> List[List["up.engines.mixins.simulator.Event"]]:
        return self._running_events

    @property
    def stn(self) -> DeltaSimpleTemporalNetwork:
        return self._stn

    @property
    def durative_conditions(self) -> List[List["up.model.fnode.FNode"]]:
        return self._durative_conditions

    @property
    def last_events(self) -> Set["up.engines.mixins.simulator.Event"]:
        return self._last_events

    def make_child(
        self,
        updated_values: Dict["up.model.FNode", "up.model.FNode"],
        running_events: Optional[
            List[List["up.engines.mixins.simulator.Event"]]
        ] = None,
        stn: Optional["DeltaSimpleTemporalNetwork"] = None,
        durative_conditions: Optional[List[List["up.model.fnode.FNode"]]] = None,
        last_events: Optional[Set["up.engines.mixins.simulator.Event"]] = None,
    ) -> "TemporalState":
        if running_events is None:
            raise UPUsageError("running_events can't be None for TemporalStates!")
        if stn is None:
            raise UPUsageError("stn can't be None for TemporalStates!")
        if durative_conditions is None:
            raise UPUsageError("durative_conditions can't be None for TemporalStates!")
        if last_events is None:
            raise UPUsageError("last_events can't be None for TemporalStates!")
        return TemporalState(
            updated_values,
            running_events,
            stn,
            durative_conditions,
            last_events,
            self,
        )
