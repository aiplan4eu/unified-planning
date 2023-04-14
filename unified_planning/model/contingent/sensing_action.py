# Copyright 2023 AIPlan4EU project
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
from unified_planning.environment import Environment
from typing import List, Optional, Iterable
from collections import OrderedDict
from unified_planning.model.action import InstantaneousAction


class SensingAction(InstantaneousAction):
    """This class represents a sensing action."""

    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _env: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        InstantaneousAction.__init__(self, _name, _parameters, _env, **kwargs)
        self._observed_fluents: List["up.model.fnode.FNode"] = []

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, SensingAction):
            return super().__eq__(oth) and set(self._observed_fluents) == set(
                oth._observed_fluents
            )
        else:
            return False

    def __hash__(self) -> int:
        res = super().__hash__()
        for of in self._observed_fluents:
            res += hash(of)
        return res

    def clone(self):
        new_params = OrderedDict()
        for param_name, param in self._parameters.items():
            new_params[param_name] = param.type
        new_sensing_action = SensingAction(self._name, new_params, self._environment)
        new_sensing_action._preconditions = self._preconditions[:]
        new_sensing_action._effects = [e.clone() for e in self._effects]
        new_sensing_action._fluents_assigned = self._fluents_assigned.copy()
        new_sensing_action._fluents_inc_dec = self._fluents_inc_dec.copy()
        new_sensing_action._simulated_effect = self._simulated_effect
        new_sensing_action._observed_fluents = self._observed_fluents.copy()
        return new_sensing_action

    def add_observed_fluents(self, observed_fluents: Iterable["up.model.fnode.FNode"]):
        """
        Adds the given list of observed fluents.

        :param observed_fluents: The list of observed fluents that must be added.
        """
        for of in observed_fluents:
            self.add_observed_fluent(of)

    def add_observed_fluent(self, observed_fluent: "up.model.fnode.FNode"):
        """
        Adds the given observed fluent.

        :param observed_fluent: The observed fluent that must be added.
        """
        self._observed_fluents.append(observed_fluent)

    @property
    def observed_fluents(self) -> List["up.model.fnode.FNode"]:
        """Returns the `list` observed fluents."""
        return self._observed_fluents

    def __repr__(self) -> str:
        b = InstantaneousAction.__repr__(self)[0:-3]
        s = ["sensing-", b]
        s.append("    observations = [\n")
        for e in self._observed_fluents:
            s.append(f"      {str(e)}\n")
        s.append("    ]\n")
        s.append("  }")
        return "".join(s)
