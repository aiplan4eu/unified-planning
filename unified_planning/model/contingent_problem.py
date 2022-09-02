# Copyright 2022 AIPlan4EU project
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
from unified_planning.model.problem import Problem
from unified_planning.model.expression import ConstantExpression
from unified_planning.model.types import domain_size
from typing import Dict, Sequence, Set, List, Union


class ContingentProblem(Problem):
    def __init__(
        self,
        name: str = None,
        env: "up.environment.Environment" = None,
        *,
        initial_defaults: Dict["up.model.types.Type", "ConstantExpression"] = {},
    ):
        Problem.__init__(self, name, env, initial_defaults=initial_defaults)
        self._hidden_fluents: Set["up.model.fnode.FNode"] = set()
        self._or_initial_constraints: List[List["up.model.fnode.FNode"]] = []
        self._oneof_initial_constraints: List[List["up.model.fnode.FNode"]] = []

    def __repr__(self) -> str:
        s = []
        s.append(super().__repr__())
        s.append("initial constraints = [\n")
        for c in self._or_initial_constraints:
            s.append(f"  (or {' '.join(c)})\n")
        for c in self._oneof_initial_constraints:
            s.append(f"  (oneof {' '.join(c)})\n")
        s.append("]\n\n")
        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if not isinstance(oth, ContingentProblem):
            return False
        elif not super().__eq__(oth):
            return False
        elif self._hidden_fluents != oth._hidden_fluents:
            return False
        elif set([set(c) for c in self._or_initial_constraints]) != set(
            [set(c) for c in oth._or_initial_constraints]
        ):
            return False
        elif set([set(c) for c in self._oneof_initial_constraints]) != set(
            [set(c) for c in oth._oneof_initial_constraints]
        ):
            return False
        else:
            return True

    def __hash__(self) -> int:
        res = super().__hash__()
        for c in self._or_initial_constraints:
            for f in c:
                res += hash(f)
        for c in self._oneof_initial_constraints:
            for f in c:
                res += hash(f)
        return res

    def clone(self):
        new_p = ContingentProblem(self._name, self._env)
        new_p._fluents = self._fluents[:]
        new_p._actions = [a.clone() for a in self._actions]
        new_p._user_types = self._user_types[:]
        new_p._user_types_hierarchy = self._user_types_hierarchy.copy()
        new_p._objects = self._objects[:]
        new_p._initial_value = self._initial_value.copy()
        new_p._timed_effects = {
            t: [e.clone() for e in el] for t, el in self._timed_effects.items()
        }
        new_p._timed_goals = {i: [g for g in gl] for i, gl in self._timed_goals.items()}
        new_p._goals = self._goals[:]
        new_p._metrics = []
        for m in self._metrics:
            if isinstance(m, up.model.metrics.MinimizeActionCosts):
                costs = {new_p.action(a.name): c for a, c in m.costs.items()}
                new_p._metrics.append(up.model.metrics.MinimizeActionCosts(costs))
            else:
                new_p._metrics.append(m)
        new_p._initial_defaults = self._initial_defaults.copy()
        new_p._fluents_defaults = self._fluents_defaults.copy()
        new_p._hidden_fluents = self._hidden_fluents.copy()
        new_p._or_initial_constraints = self._or_initial_constraints.copy()
        new_p._oneof_initial_constraints = self._oneof_initial_constraints.copy()
        return new_p

    def add_oneof_initial_constraint(
        self, fluents: Sequence[Union["up.model.fnode.FNode", "up.model.fluent.Fluent"]]
    ):
        em = self._env.expression_manager
        c = []
        for f in fluents:
            (f_exp,) = em.auto_promote(f)
            self._hidden_fluents.add(f_exp)
            c.append(f_exp)
        self._oneof_initial_constraints.append(c)

    def add_or_initial_constraint(
        self, fluents: Sequence[Union["up.model.fnode.FNode", "up.model.fluent.Fluent"]]
    ):
        em = self._env.expression_manager
        c = []
        for f in fluents:
            (f_exp,) = em.auto_promote(f)
            self._hidden_fluents.add(f_exp)
            c.append(f_exp)
        self._or_initial_constraints.append(c)

    def add_unknown_initial_constraint(
        self, fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"]
    ):
        em = self._env.expression_manager
        (fluent_exp,) = em.auto_promote(fluent)
        self._hidden_fluents.add(fluent_exp)
        self._hidden_fluents.add(em.Not(fluent_exp))
        c = [em.Not(fluent_exp), fluent_exp]
        self._or_initial_constraints.append(c)

    @property
    def initial_values(self) -> Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]:
        """Gets the initial value of the fluents.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible."""
        res = self._initial_value
        for f in self._fluents:
            if f.arity == 0:
                f_exp = self._env.expression_manager.FluentExp(f)
                res[f_exp] = self.initial_value(f_exp)
            else:
                ground_size = 1
                domain_sizes = []
                for p in f.signature:
                    ds = domain_size(self, p.type)
                    domain_sizes.append(ds)
                    ground_size *= ds
                for i in range(ground_size):
                    f_exp = self._get_ith_fluent_exp(f, domain_sizes, i)
                    if f_exp not in self._hidden_fluents:
                        res[f_exp] = self.initial_value(f_exp)
        return res

    @property
    def kind(self) -> "up.model.problem_kind.ProblemKind":
        """Returns the problem kind of this planning problem.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        minimum time as possible."""
        self._kind = super().kind
        self._kind.set_problem_class("CONTINGENT")
        return self._kind

    @property
    def or_constraints(self) -> List[List["up.model.fnode.FNode"]]:
        return self._or_initial_constraints

    @property
    def oneof_constraints(self) -> List[List["up.model.fnode.FNode"]]:
        return self._oneof_initial_constraints

    @property
    def hidden(self) -> Set["up.model.fnode.FNode"]:
        return self._hidden_fluents
