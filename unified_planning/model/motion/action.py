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
from unified_planning.environment import Environment
from unified_planning.model.action import InstantaneousAction, DurativeAction
from unified_planning.model.mixins.motion_constraints_set import (
    MotionConstraintsSetMixin,
)
from unified_planning.model.mixins.timed_conds_effs import TimedCondsEffs
from typing import Optional
from collections import OrderedDict


class InstantaneousMotionAction(InstantaneousAction, MotionConstraintsSetMixin):
    """This class represents an instantaneous motion action."""

    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _environment: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        InstantaneousAction.__init__(self, _name, _parameters, _environment, **kwargs)
        MotionConstraintsSetMixin.__init__(self)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, InstantaneousMotionAction):
            return (
                super().__eq__(oth)
                and self._motion_constraints_set == oth._motion_constraints_set
            )
        else:
            return False

    def __hash__(self) -> int:
        res = super().__hash__()
        for of in self._motion_constraints:
            res += hash(of)
        return res

    def __repr__(self) -> str:
        b = InstantaneousAction.__repr__(self)[0:-3]
        s = ["motion-", b]
        s.append("    motion constraints = [\n")
        for e in self._motion_constraints:
            s.append(f"      {str(e)}\n")
        s.append("    ]\n")
        s.append("  }")
        return "".join(s)

    def clone(self):
        new_params = OrderedDict()
        for param_name, param in self._parameters.items():
            new_params[param_name] = param.type
        new_motion_action = InstantaneousMotionAction(
            self._name, new_params, self._environment
        )
        new_motion_action._preconditions = self._preconditions[:]
        new_motion_action._effects = [e.clone() for e in self._effects]
        new_motion_action._fluents_assigned = self._fluents_assigned.copy()
        new_motion_action._fluents_inc_dec = self._fluents_inc_dec.copy()
        new_motion_action._simulated_effect = self._simulated_effect
        new_motion_action._motion_constraints = self._motion_constraints.copy()
        new_motion_action._motion_constraints_set = self._motion_constraints_set.copy()
        return new_motion_action


class DurativeMotionAction(DurativeAction, MotionConstraintsSetMixin):
    """This class represents a durative motion action."""

    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _environment: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        DurativeAction.__init__(self, _name, _parameters, _environment, **kwargs)
        MotionConstraintsSetMixin.__init__(self)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, DurativeMotionAction):
            return (
                super().__eq__(oth)
                and self._motion_constraints_set == oth._motion_constraints_set
            )
        else:
            return False

    def __hash__(self) -> int:
        res = super().__hash__()
        for of in self._motion_constraints:
            res += hash(of)
        return res

    def __repr__(self) -> str:
        b = DurativeAction.__repr__(self)[0:-3]
        s = ["motion-", b]

        s.append("    motion constraints = [\n")
        for e in self._motion_constraints:
            s.append(f"      {str(e)}\n")
        s.append("    ]\n")
        s.append("  }\n")
        return "".join(s)

    def clone(self):
        new_params = OrderedDict(
            (param_name, param.type) for param_name, param in self._parameters.items()
        )
        new_durative_motion_action = DurativeMotionAction(
            self._name, new_params, self._environment
        )
        new_durative_motion_action._duration = self._duration
        TimedCondsEffs._clone_to(self, new_durative_motion_action)
        new_durative_motion_action._motion_constraints = self._motion_constraints.copy()
        new_durative_motion_action._motion_constraints_set = (
            self._motion_constraints_set.copy()
        )
        return new_durative_motion_action
