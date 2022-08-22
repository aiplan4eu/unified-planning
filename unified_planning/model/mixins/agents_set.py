# Copyright 2022 AIPlan4EU project / Technion
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
from unified_planning.model.types import _UserType
from unified_planning.exceptions import UPProblemDefinitionError, UPValueError
from typing import List, Dict, Optional, cast
from unified_planning.model.agent import Agent


class AgentsSetMixin:
    """
    This class is a mixin that contains a set of agents with some related methods.

    NOTE: when this mixin is used in combination with other mixins that share some
    of the attributes (e.g. has_name_method), it is required to pass the very same
    arguments to the mixins constructors.
    """

    def __init__(self, env, has_name_method):
        self._env: "up.environment.Environment" = env
        self._has_name_method = has_name_method
        self._agents: List[Agent] = []

    @property
    def env(self) -> "up.environment.Environment":
        """Returns the problem environment."""
        return self._env

    def add_agent(self, agent: "Agent"):
        """This method adds an Agent"""
        if agent not in self._agents:
            t = cast(Agent, agent)
            if self._has_name_method(t._name):
                raise UPProblemDefinitionError(
                    f"The agent name {t._name} is already used in the problem"
                )
            self._agents.append(agent)

    @property
    def agents(self) -> List["Agent"]:
        """Returns the agents."""
        return self._agents

    def agent(self, name: str) -> "Agent":
        """Returns the agent with the given name."""
        for agent in self._agents:
            if agent._name == name:
                return agent
        raise UPValueError(f"Agent {name} is not defined!")

    def has_agent(self, name: str) -> bool:
        """Returns True iff the agent 'name' is defined."""
        for agent in self._agents:
            print(agent._name)
            if agent._name == name:
                return True
        return False
