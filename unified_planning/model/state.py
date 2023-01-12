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
from unified_planning.exceptions import UPUsageError, UPValueError


class ROState:
    """This is an abstract class representing a classical `Read Only state`"""

    def get_value(self, value: "up.model.FNode") -> "up.model.FNode":
        """
        This method retrieves the value in the state.
        NOTE that the searched value must be set in the state.

        :param value: The value searched for in the state.
        :return: The set value.
        """
        raise NotImplementedError


class COWState(ROState):
    """
    Implementation of the `ROState` interface offering also the 'CopyOnWrite' feature.
    This class has an optional field `MAX_ANCESTORS` set to 20.

    The higher this number is, the less memory the data structure will use.
    The lower this number is, the less time the data structure will need to retrieve a value.

    To set your own number just extend this class and re-define the `MAX_ANCESTORS` value. It must be `> 0`

    If `MAX_ANCESTORS` is set to `None`, the data structure will always remain
    persistent with all the hierarchy created.
    """

    MAX_ANCESTORS: Optional[int] = 20

    def __init__(
        self,
        values: Dict["up.model.FNode", "up.model.FNode"],
        _father: Optional["COWState"] = None,
    ):
        """
        Creates a new `COWState` where the map values represents the get_value
        method. The parameter `_father` is for internal use only.
        """
        max_ancestors = type(self).MAX_ANCESTORS
        if max_ancestors is not None and max_ancestors < 1:
            raise UPValueError(
                "The max_ancestor field of a class extending COWState must be > 0:",
                f"in the class {type(self)} it is set to {type(self).MAX_ANCESTORS}",
            )
        self._father = _father
        self._values = values
        if _father is None:
            self._ancestors = 0
        else:
            self._ancestors = _father._ancestors + 1

    def __repr__(self) -> str:
        current_instance: Optional[COWState] = self
        retval = []
        while current_instance is not None:
            retval.append(f"{str(current_instance._values)}")
            current_instance = current_instance._father
        return "\n".join(retval)

    def _has_local_value(self, value: "up.model.FNode") -> bool:
        """
        Method for internal use only.
        This method returns True if the parameter value is in this specific instance;
        NOTE that if self._has_local_value(x) returns False does not mean that self.get_value(x) will not retrieve any value.

        :param value: The value searched in this instance of the class.
        :return: True if this instance holds the value, False otherwise.
        """
        return value in self._values

    def get_value(self, value: "up.model.FNode") -> "up.model.FNode":
        """
        This method retrieves the value in the `State`.
        NOTE that the searched value must be set in the state.

        :params value: The value searched for in the `State`.
        :return: The set value.
        """
        right_instance: Optional[COWState] = self
        while right_instance is not None:
            if right_instance._has_local_value(value):
                return right_instance._values[value]
            right_instance = right_instance._father
        raise UPUsageError(
            f"The state {self} does not have a value for the value {value}"
        )

    def make_child(
        self,
        updated_values: Dict["up.model.FNode", "up.model.FNode"],
        agenda: Optional[List[List["up.engines.mixins.simulator.Event"]]] = None,
        stn: Optional["up.model.delta_stn.DeltaSimpleTemporalNetwork"] = None,
        durative_conditions: Optional[List["up.model.fnode.FNode"]] = None,
        last_events: Optional[Set["up.engines.mixins.simulator.Event"]] = None,
    ) -> "COWState":
        """
        Returns a different `UPCOWState` in which every value in updated_values.keys() is evaluated as his mapping
        in new the `updated_values` dict and every other value is evaluated as in `self`.

        :param updated_values: The dictionary that contains the `values` that need to be updated in the new `State`.
        :param agenda: Not supported; makes sense only for temporal states.
        :param stn: Not supported; makes sense only for temporal states.
        :param durative_conditions: Not supported; makes sense only for temporal states.
        :param last_events: Not supported; makes sense only for temporal states.
        :return: The new `State` created.
        """
        # input validation
        if (
            agenda is not None
            or stn is not None
            or durative_conditions is not None
            or last_events is not None
        ):
            raise UPUsageError(
                f"{type(self)} supports only the updated_values parameters!"
            )
        # If the number of ancestors is less that the given threshold (or it's None) it just creates a new state with self set as the father.
        max_ancestors = type(self).MAX_ANCESTORS
        if max_ancestors is None or self._ancestors < max_ancestors:
            return COWState(updated_values, self)
        # Otherwise we retrieve every ancestor, and from the oldest to the newest we update the "complete_values" dict
        else:
            current_element: Optional[COWState] = self
            complete_values = updated_values.copy()
            while current_element is not None:
                for k, v in current_element._values.items():
                    complete_values.setdefault(k, v)
                current_element = current_element._father
            return COWState(complete_values)
