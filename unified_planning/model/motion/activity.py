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
from unified_planning.exceptions import UPTypeError
from unified_planning.model.scheduling.activity import Activity
from unified_planning.model.mixins.motion_constraints_set import (
    MotionConstraintsSetMixin,
)
from typing import Optional, Dict


class MotionActivity(Activity, MotionConstraintsSetMixin):
    """This class represents a motion activity."""

    def __init__(
        self,
        name: str,
        duration: int = 1,
        optional: bool = False,
        _env: Optional[Environment] = None,
    ):
        Activity.__init__(self, name, duration, optional, _env)
        MotionConstraintsSetMixin.__init__(self)
        self._motion_effects: Dict["up.model.FNode", "up.model.FNode"] = {}

    def __eq__(self, oth: object) -> bool:
        if not isinstance(oth, MotionActivity):
            return False
        if self._motion_constraints_set != oth._motion_constraints_set:
            return False
        if self._motion_effects != oth._motion_effects:
            return False
        return super().__eq__(oth)

    def __hash__(self) -> int:
        res = super().__hash__()
        res += sum(map(hash, self.motion_constraints))
        res += sum(map(hash, self.motion_effects))
        return res

    def __repr__(self) -> str:
        s = ["motion-activity {"]
        s.append(super().__repr__().replace("/n", "\n  "))
        s.append("  motion-constraints")
        for c in self._motion_constraints:
            s.append(f"      {str(c)}\n")
        s.append("  motion-effects")
        for e in self._motion_effects:
            s.append(f"      {str(e)}\n")
        s.append("}")
        return "\n".join(s)

    def clone(self):
        new = MotionActivity(self.name, optional=self.optional, _env=self._environment)
        self._clone_to(new)
        new._duration = self._duration
        new._motion_constraints = self._motion_constraints.copy()
        new._motion_constraints_set = self._motion_constraints_set.copy()
        new._motion_effects = self.motion_effects.copy()
        return new

    @property
    def motion_effects(
        self,
    ) -> Dict["up.model.FNode", "up.model.FNode"]:
        """Returns the `dict` mapping each movable expression to its target configuration expression."""
        return self._motion_effects

    def clear_motion_effects(self):
        """Removes all `motion_effects`."""
        self._motion_effects = {}

    def add_motion_effect(
        self,
        movable: "up.model.expression.Expression",
        config: "up.model.expression.Expression",
    ):
        """
        Adds a motion effect setting the given movable object to the given configuration.

        :param movable: The expression of movable type whose configuration is set.
        :param config: The expression of configuration type assigned to the movable object.
        """
        movable_exp, config_exp = self._environment.expression_manager.auto_promote(
            movable, config
        )
        if not self._environment.type_checker.get_type(movable_exp).is_movable_type():
            raise UPTypeError("movable parameter must be of movable type!")
        if not self._environment.type_checker.get_type(
            config_exp
        ).is_configuration_type():
            raise UPTypeError("config parameter must be of configuration type!")

        self._motion_effects[movable_exp] = config_exp
