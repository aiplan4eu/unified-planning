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
"""
This module defines the base class `Axiom'.
An `Axiom' has a `head' which is a single `Parameter' and a `body' which is a single `Condition'.
"""

from unified_planning.model.action import *
from unified_planning.environment import get_environment, Environment


class Axiom(InstantaneousAction):
    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _env: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        InstantaneousAction.__init__(self, _name, _parameters, _env, **kwargs)

    def set_head(self, fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"]):
        if not fluent.type.is_derived_bool_type():
            raise UPTypeError("The head of an axiom must be of type DerivedBoolType!")

        self.add_effect(fluent)

    def add_body_condition(
        self,
        precondition: Union[
            "up.model.fnode.FNode",
            "up.model.fluent.Fluent",
            "up.model.parameter.Parameter",
            bool,
        ],
    ):
        super().add_precondition(precondition)

    def add_effect(
        self,
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression" = True,
        condition: "up.model.expression.BoolExpression" = True,
        forall: Iterable["up.model.variable.Variable"] = tuple(),
    ):
        if value != True:
            raise UPUsageError("value can only be true for an axiom")
        if condition != True:
            raise UPUsageError("the effect of an axiom can not include a condition")
        if len(forall) > 0:
            raise UPUsageError("the effect of an axiom can not a forall")

        (
            fluent_exp,
            value_exp,
            condition_exp,
        ) = self._environment.expression_manager.auto_promote(fluent, value, condition)

        if not fluent_exp.is_fluent_exp():
            raise UPUsageError("head/effect of an axiom must be a fluent expression")

        fluent_exp_params = [p.parameter() for p in fluent_exp.args]
        if self.parameters != fluent_exp_params:
            raise UPUsageError(
                f"parameters of axiom and this fluent expression do not match: {self.parameters} vs. {fluent_exp_params}"
            )

        self.clear_effects()
        self._add_effect_instance(
            up.model.effect.Effect(fluent_exp, value_exp, condition_exp, forall=forall)
        )

    @property
    def head(self) -> List["up.model.fluent.Fluent"]:
        """Returns the `head` of the `Axiom`."""
        return self._effects[0]

    @property
    def body(self) -> List["up.model.fnode.FNode"]:
        """Returns the `list` of the `Axiom` `body`."""
        return self._preconditions

    def __repr__(self) -> str:
        s = []
        s.append(f"axiom {self.name}")
        first = True
        for p in self.parameters:
            if first:
                s.append("(")
                first = False
            else:
                s.append(", ")
            s.append(str(p))
        if not first:
            s.append(")")
        s.append("{\n")
        s.append(f"   head = {self.head}\n")
        s.append(f"   body = {self.body}\n")
        s.append("  }")
        return "".join(s)
