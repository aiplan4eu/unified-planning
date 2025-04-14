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

from typing import Optional, List, OrderedDict, Union, Tuple

from unified_planning.model.fnode import FNode
from unified_planning.model.expression import BoolExpression
import unified_planning as up
from unified_planning import Environment
from unified_planning.model import Parameter
from unified_planning.model.mixins.timed_conds_effs import TimedCondsEffs
from unified_planning.model.types import Type


Scope = List[FNode]
Constraint = Union[
    "up.model.fnode.FNode",
    "up.model.fluent.Fluent",
    "up.model.parameter.Parameter",
    bool,
]


class Chronicle(TimedCondsEffs):
    """Core structure to represent a set of variables, constraints, timed conditions and effects in scheduling problems."""

    def __init__(
        self,
        name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _env: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):
        TimedCondsEffs.__init__(self, _env)
        self._name = name
        self._constraints: List[Tuple["up.model.fnode.FNode", Scope]] = []
        self._parameters: "OrderedDict[str, up.model.parameter.Parameter]" = (
            OrderedDict()
        )

        if _parameters is not None:
            assert len(kwargs) == 0
            for n, t in _parameters.items():
                assert self._environment.type_manager.has_type(
                    t
                ), "type of parameter does not belong to the same environment of the action"
                self._parameters[n] = up.model.parameter.Parameter(
                    n, t, self._environment
                )
        else:
            for n, t in kwargs.items():
                assert self._environment.type_manager.has_type(
                    t
                ), "type of parameter does not belong to the same environment of the action"
                self._parameters[n] = up.model.parameter.Parameter(
                    n, t, self._environment
                )

    def __repr__(self) -> str:
        s = []
        s.append(f"{self.name}")
        if len(self.parameters) > 0:
            s += ["(", ", ".join(map(str, self.parameters)), ")"]
        if hasattr(self, "optional") and self.optional:
            s.append(" (optional) ")
        s.append(" {\n")
        if hasattr(self, "duration"):
            s.append(f"    duration = {str(self.duration)}\n")
        if len(self._constraints) > 0:
            s.append("    constraints = [\n")
            for (c, scope) in self._constraints:
                s.append(f"      {str(c)} {str(scope)}\n")
            s.append("    ]\n")
        if len(self.conditions) > 0:
            s.append("    conditions = [\n")
            for i, cl in self.conditions.items():
                s.append(f"      {str(i)}:\n")
                for c in cl:
                    s.append(f"        {str(c)}\n")
            s.append("    ]\n")
        if len(self.effects) > 0:
            s.append("    effects = [\n")
            for t, el in self.effects.items():
                s.append(f"      {str(t)}:\n")
                for e in el:
                    s.append(f"        {str(e)}\n")
            s.append("    ]\n")
        s.append("  }")
        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if not isinstance(oth, Chronicle):
            return False
        if (
            self._environment != oth._environment
            or self._parameters != oth._parameters
            or self._name != oth._name
        ):
            return False

        # if set((c, set(scope)) for (c,scope) in self._constraints) != set((c, set(scope)) for (c,scope) in oth._constraints):
        #     return False
        if len(self._constraints) != len(
            oth._constraints
        ):  # TODO: just comparing length here
            print("=== self ==")
            for c in self._constraints:
                print(c)
            print("=== other =")
            for c in oth._constraints:
                print(c)
            print("===========")
            return False
        if not TimedCondsEffs.__eq__(self, oth):
            return False
        return True

    def __hash__(self) -> int:
        res = hash(self._name)
        res += sum(map(hash, self._parameters.items()))
        # res += sum(map(hash, self._constraints))
        res += TimedCondsEffs.__hash__(self)
        return res

    @property
    def name(self) -> str:
        """Returns the `Chronicle` `name`."""
        return self._name

    def _clone_to(self, other: "Chronicle"):  # type: ignore[override]
        other._parameters = self._parameters.copy()
        other._constraints = self._constraints.copy()
        TimedCondsEffs._clone_to(self, other)

    def clone(self):
        new = Chronicle(self._name, _env=self._environment)
        self._clone_to(new)
        return new

    def add_parameter(self, name: str, tpe: Type) -> Parameter:
        """Adds a new decision variable associated to this activity.
        The resulting parameter's identifier will be prefixed with the activity's name but may be
        used outside the activity itself. For instance, it could appear in global constraints or
        constraints involving more than one activity."""
        assert "." not in name, f"Usage of '.' is forbidden in names: {name}"
        assert name not in [
            "start",
            "end",
        ], f"Usage of parameter name {name} is reserved"
        scoped_name = f"{self.name}.{name}"
        if name in self._parameters:
            raise ValueError(f"Name '{name}' already used in chronicle '{self.name}'")
        param = Parameter(scoped_name, tpe)
        self._parameters[name] = param
        return param

    def get_parameter(self, name: str) -> Parameter:
        """Returns the parameter with the given name."""
        if name not in self._parameters:
            raise ValueError(
                f"Unknown parameter '{name}. Available parameters: {list(self._parameters.keys())}"
            )
        return self._parameters[name]

    def __getattr__(self, parameter_name: str) -> "up.model.parameter.Parameter":
        if parameter_name.startswith("_"):
            # guard access as pickling relies on attribute error to be thrown even when
            # no attributes of the object have been set.
            # In this case accessing `self._name` or `self._parameters`, would re-invoke __getattr__
            raise AttributeError(f"Transition has no attribute '{parameter_name}'")
        if parameter_name not in self._parameters:
            print(self._parameters)
            raise AttributeError(
                f"Transition '{self.name}' has no attribute or parameter '{parameter_name}'"
            )
        return self._parameters[parameter_name]

    @property
    def parameters(self) -> List["up.model.parameter.Parameter"]:
        """Returns the `list` of the `Action parameters`."""
        return list(self._parameters.values())

    def _add_constraint(self, constraint: Constraint, scope: List[BoolExpression]):
        """
        Adds the given expression to the `chronicle's constraints`.
        """
        (constraint_exp,) = self._environment.expression_manager.auto_promote(
            constraint
        )
        scope_exprs = self._environment.expression_manager.auto_promote(scope)
        assert self._environment.type_checker.get_type(constraint_exp).is_bool_type()
        assert all(
            self._environment.type_checker.get_type(scope_expr).is_bool_type()
            for scope_expr in scope_exprs
        )
        self._constraints.append((constraint_exp, scope_exprs))

    @property
    def constraints(self) -> List[FNode]:
        assert all(
            (len(scope) == 0 for (_, scope) in self._constraints)
        ), f"At least one constraint has a non-empty scope.: {self._constraints}"
        return [c for (c, scope) in self._constraints if len(scope) == 0]

    @property
    def scoped_constraints(self) -> List[Tuple[FNode, Scope]]:
        return self._constraints
