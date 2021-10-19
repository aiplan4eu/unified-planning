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

from functools import partialmethod
from typing import Set


# TODO: This features map needs to be extended with all the problem characterizations.
FEATURES = {
    'TIME' : ['CONTINUOUS_TIME', 'DISCRETE_TIME', 'ICE'],
    'NUMBERS' : ['CONTINUOUS_NUMBERS', 'DISCRETE_NUMBERS'],
    'CONDITIONS_KIND' : ['NEGATIVE_CONDITIONS', 'DISJUNCTIVE_CONDITIONS', 'EQUALITY', 'EXISTENTIAL_PRECONDITIONS', 'UNIVERSAL_PRECONDITIONS'],
    'EFFECTS_KIND' : ['CONDITIONAL_EFFECTS', 'INCREASE_EFFECTS', 'DECREASE_EFFECTS'],
    'TYPING' : ['FLAT_TYPING']
}


class ProblemKindMeta(type):
    '''Meta class used to interpret the nodehandler decorator.'''
    def __new__(cls, name, bases, dct):
        def _set(self, feature, possible_features):
            assert feature in possible_features
            self._features.add(feature)

        def _has(self, feature):
            return feature in self._features

        obj = type.__new__(cls, name, bases, dct)
        for m, l in FEATURES.items():
            setattr(obj, "set_" + m.lower(), partialmethod(_set, possible_features=l))
            for f in l:
                setattr(obj, "has_" + f.lower(), partialmethod(_has, feature=f))
        return obj


class ProblemKind(metaclass=ProblemKindMeta):
    def __init__(self):
        self._features: Set[str] = set()

    def features(self) -> Set[str]:
        return self._features
