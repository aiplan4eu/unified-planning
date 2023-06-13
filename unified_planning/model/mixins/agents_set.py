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

from warnings import warn
import unified_planning as up
from unified_planning.model.types import _UserType
from unified_planning.exceptions import UPProblemDefinitionError, UPValueError
from typing import List, Dict, Optional, cast


class AgentsSetMixin:
    """
    This class is a mixin that contains a set of agents with some related methods.

    NOTE: when this mixin is used in combination with other mixins that share some
    of the attributes (e.g. has_name_method), it is required to pass the very same
    arguments to the mixins constructors.
    """

    def __init__(self, environment, has_name_method):
        self._env: "up.environment.Environment" = environment
        self._has_name_method = has_name_method
        self._agents: List["up.model.multi_agent.Agent"] = []

    @property
    def environment(self) -> "up.environment.Environment":
        """Returns the problem environment."""
        return self._env

    def add_agent(self, agent: "up.model.multi_agent.Agent"):
        """This method adds an Agent"""
        if agent not in self._agents:
            if self._has_name_method(agent.name):
                msg = f"The agent name {agent.name} is already used in the problem!  Different elements of a problem can have the same name if the environment flag error_used_named is disabled."
                if self._env.error_used_name or any(
                    agent.name == a.name for a in self._agents
                ):
                    raise UPProblemDefinitionError(msg)
                else:
                    warn(msg)
            self._agents.append(agent)

    @property
    def agents(self) -> List["up.model.multi_agent.Agent"]:
        """Returns the agents."""
        return self._agents

    def agent(self, name: str) -> "up.model.multi_agent.Agent":
        """Returns the agent with the given name."""
        for agent in self._agents:
            if agent._name == name:
                return agent
        raise UPValueError(f"Agent {name} is not defined!")

    def has_agent(self, name: str) -> bool:
        """Returns True iff the agent 'name' is defined."""
        for agent in self._agents:
            if agent.name == name:
                return True
        return False
