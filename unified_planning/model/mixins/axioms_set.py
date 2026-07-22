# Copyright 2021-2023 AIPlan4EU project
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
from typing import List, Iterable


class AxiomsSetMixin:
    """
    This class is a mixin that contains a `set` of `axiom` with some related methods.
    """

    def __init__(self, environment):
        self._env = environment
        self._axioms: List["up.model.axiom.Axiom"] = []

    @property
    def environment(self) -> "up.environment.Environment":
        """Returns the `Problem` environment."""
        return self._env

    @property
    def axioms(self) -> List["up.model.axiom.Axiom"]:
        """Returns the list of the `Axioms` in the `Problem`."""
        return self._axioms

    def clear_axioms(self):
        """Removes all the `Problem` `Axioms`."""
        self._axioms = []

    def add_axiom(self, axiom: "up.model.axiom.Axiom"):
        """
        Adds the given `axiom` to the `problem`.

        :param axiom: The `axiom` that must be added to the `problem`.
        """
        assert (
            axiom.environment == self._env
        ), "Axiom does not have the same environment of the problem"
        self._axioms.append(axiom)

    def add_axioms(self, axioms: Iterable["up.model.axiom.Axiom"]):
        """
        Adds the given `axioms` to the `problem`.

        :param axioms: The `axioms` that must be added to the `problem`.
        """
        for axiom in axioms:
            self.add_axiom(axiom)
