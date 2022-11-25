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
from unified_planning.model.state import UPCOWState


@dataclass
class DeltaNeighbors:
    dst: Any
    bound: Fraction


class DeltaSimpleTemporalNetwork:
    def __init__(
        self,
        constraints: Dict[Any, List[DeltaNeighbors]] = {},
        distances: Dict[Any, Fraction] = {},
        is_sat=True,
    ):
        self._constraints: Dict[Any, List[DeltaNeighbors]] = constraints
        self._distances: Dict[Any, Fraction] = distances
        self._is_sat = is_sat

    def copy_stn(self) -> "DeltaSimpleTemporalNetwork":
        return DeltaSimpleTemporalNetwork(
            self._constraints.copy(), self._distances.copy(), self._is_sat
        )

    def add(self, x: Any, y: Any, b: Fraction):
        if self._is_sat:
            self._distances.setdefault(x, Fraction(0))
            self._distances.setdefault(y, Fraction(0))
            x_constraints = self._constraints.setdefault(x, [])
            y_constraints = self._constraints.setdefault(y, [])
            if not self._is_subsumed(x, y, b):
                neighbor = DeltaNeighbors(y, b)
                x_constraints.insert(0, neighbor)
                self._is_sat = self._inc_check(x, y, b)

    def check_stn(self) -> bool:
        return self._is_sat

    def get_stn_model(self, x: Any) -> Fraction:
        return -1 * self._distances[x]

    def _is_subsumed(self, x: Any, y: Any, b: Fraction) -> bool:
        for neighbor in self._constraints[x]:
            if neighbor.dst == y:
                return neighbor.bound <= b
        return False

    def _inc_check(self, x: Any, y: Any, b: Fraction) -> bool:
        if self._distances[x] + b < self._distances[y]:
            self._distances[y] = self._distances[x] + b
        else:
            return True
        queue: Deque[Any] = deque()
        while queue:
            c = queue.popleft()
            for n in self._constraints[c]:
                if self._distances[c] + n.bound < self._distances[n.dst]:
                    if n.dst == y and n.bound == b:
                        return False
                    self._distances[n.dst] = self._distances[c] + n.bound
                    queue.append(n.dst)
        return True


class TemporalState(UPCOWState):
    def __init__(
        self,
        values: Dict["up.model.FNode", "up.model.FNode"],
        running_events: List[List["up.engines.mixins.simulator.Event"]],
        stn: "DeltaSimpleTemporalNetwork",
        durative_conditions: List["up.engines.mixins.simulator.Event"],
        last_event: "up.engines.mixins.simulator.Event",
        _father: Optional["TemporalState"] = None,
    ):
        UPCOWState.__init__(values, _father)
        self._running_events = running_events
        self._stn = stn
        self._durative_conditions = durative_conditions
        self._last_event = last_event

    @property
    def running_events(self) -> List[List["up.engines.mixins.simulator.Event"]]:
        return self._running_events

    @property
    def stn(self) -> DeltaSimpleTemporalNetwork:
        return self._stn

    @property
    def durative_conditions(self) -> List["up.engines.mixins.simulator.Event"]:
        return self._durative_conditions

    @property
    def last_event(self) -> "up.engines.mixins.simulator.Event":
        return self._last_event

    def make_child(
        self,
        updated_values: Dict["up.model.FNode", "up.model.FNode"],
        updated_running_events: List[Set["up.engines.mixins.simulator.Event"]],
        updated_stn: "DeltaSimpleTemporalNetwork",
        updated_durative_conditions: List["up.engines.mixins.simulator.Event"],
        updated_last_event: "up.engines.mixins.simulator.Event",
    ) -> "UPCOWState":
        return TemporalState(
            updated_values,
            updated_running_events,
            updated_stn,
            updated_durative_conditions,
            updated_last_event,
            self,
        )
