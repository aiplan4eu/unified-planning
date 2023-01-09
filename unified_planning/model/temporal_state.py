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


from typing import Dict, List, Optional, Set
import unified_planning as up
from unified_planning.model.state import UPCOWState
from unified_planning.exceptions import UPUsageError


class TemporalState(UPCOWState):
    MAX_ANCESTORS: Optional[int] = None

    def __init__(
        self,
        values: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"],
        running_events: List[List["up.engines.mixins.simulator.Event"]],
        stn: "up.model.delta_stn.DeltaSimpleTemporalNetwork",
        durative_conditions: List["up.model.fnode.FNode"],
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
        """
        Returns the running events of the `TemporalState`.

        The running_events is a `List` of `Elements`, where each `Element` is a `List` containing
        `Events` that, in the same order that they appear in the `List`, must be applied before
        the end of the simulation.

        For example, when an `ACTION_START` `Event` is applied to the `State`, the `List` containing
        all the `Events` in which the given action is split, is added to the `running_events`.

        Every time an `Event` that is not an `ACTION_START` `Event` is applied to the `State`, it must be
        the first element of one of the `Lists` in the `running_events`; if it is, it is popped and
        applied.
        """
        return self._running_events

    @property
    def stn(self) -> "up.model.delta_stn.DeltaSimpleTemporalNetwork":
        """
        Returns the DeltaSTN corresponding to this TemporalState.

        A SimpleTemporalNetwork is a data structure that contains the time constraints between the
        Events that are applied in the State. AN STN is said consistent if every Event applied does
        not violate a time constraint, it is said inconsistent otherwise.

        The DeltaSTN is a specific implementation of STN specifically engineered for planning purposes;
        it's main point is the capability of creating a lot of different DeltaSTN, that have a small
        difference one-another, without having to re-do all the calculations about the STN consistency.

        Also, being a persistent data-structure, it also optimizes the memory usage.
        """
        return self._stn

    @property
    def durative_conditions(self) -> List["up.model.fnode.FNode"]:
        """
        Returns the `durative_conditions` of this `State`.

        For a `State` to be valid, every `durative_condition` must be evaluated to `True`.

        `durative_conditions` are added from the `START_CONDITION` `Event` and are removed
        by the `END_CONDITION` `Event`.
        """
        return self._durative_conditions

    @property
    def last_events(self) -> Set["up.engines.mixins.simulator.Event"]:
        """
        Returns the `Set` of `Events` that were applied to create this `State` from the `State`;
        the one given to the `Simulator` `apply` -or `apply_unsafe`- method.
        """
        return self._last_events

    def make_child(
        self,
        updated_values: Dict["up.model.FNode", "up.model.FNode"],
        running_events: Optional[
            List[List["up.engines.mixins.simulator.Event"]]
        ] = None,
        stn: Optional["up.model.delta_stn.DeltaSimpleTemporalNetwork"] = None,
        durative_conditions: Optional[List["up.model.fnode.FNode"]] = None,
        last_events: Optional[Set["up.engines.mixins.simulator.Event"]] = None,
    ) -> "TemporalState":
        """
        Returns a different `TemporalState` in which every value in updated_values.keys() is evaluated as his mapping
        in new the `updated_values` dict and every other value is evaluated as in `self`.
        All the other parameters are the ones that will be set in the new `TemporalState`.

        :param updated_values: The dictionary that contains the `values` that need to be updated in the new `State`.
        :param running_events: The running_events of the created TemporalState.
        :param stn: The `DeltaSimpleTemporalNetwork` representing the time constraints of the created `TemporalState`.
        :param durative_conditions: The `List` of conditions that must evaluate to True in the created `TemporalState`.
        :param last_events: The `Set` of events that are applied to this `TemporalState` in order to get the
            `TemporalState` that is returned.
        :return: The new `State` created.
        """
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
