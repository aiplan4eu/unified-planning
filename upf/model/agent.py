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


import upf
from upf.shortcuts import *


class Agent:
    def __init__(
            self,
            ID =  None,
            obs_individual_fluents = None,
            obs_public_fluents = None,
            actions = None,
            goals = None,
            location = None
    ):
        self.ID =  ID
        if obs_individual_fluents is None:
            self.obs_individual_fluents = []
        if obs_public_fluents is None:
            self.obs_public_fluents = []
        if actions is None:
            self.actions = []
        if goals is None:
            self.goals = []
        if location is None:
            self.location = []

    def add_individual_fluent(self, Fluent):
        #idx = len(self.obs_individual_fluents)
        #setattr(Fluent, '_name', str(Fluent._name) + (self.ID))
        self.obs_individual_fluents.append(Fluent)

    def get_individual_fluents(self):
        return self.obs_individual_fluents

    def add_public_fluent(self, Fluent):
        self.obs_public_fluents.append(Fluent)

    def get_public_fluents(self):
        return self.obs_public_fluents

    def add_action(self, Action):
        self.actions.append(Action)

    def get_actions(self):
        return self.actions

    def add_goal(self, Goal):
        self.goals.append(ObjectExp(Goal))

    def get_goals(self):
        return self.goals

    def add_location(self, Location):
        self.location.append(Location)

    def get_location(self):
        return self.location