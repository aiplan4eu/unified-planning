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
import unified_planning.engines.mixins as mixins
from unified_planning.model import ProblemKind
from unified_planning.engines.engine import Engine
from unified_planning.engines.meta_engine import MetaEngine
from unified_planning.engines.results import (
    PlanGenerationResultStatus,
    PlanGenerationResult,
)
from unified_planning.engines.mixins.oneshot_planner import OptimalityGuarantee
from typing import Type, IO, Callable, Optional, Union, List, Tuple
from fractions import Fraction


class Replanner(MetaEngine, mixins.ReplannerMixin):
    """
    This :class:`~unified_planning.engines.MetaEngine` implements the :func:`~unified_planning.engines.Factory.Replanner>` operation mode starting
    a new oneshot planning query with the updated :class:`~unified_planning.model.AbstractProblem` instance.
    """

    def __init__(self, problem: "up.model.AbstractProblem", *args, **kwargs):
        MetaEngine.__init__(self, *args, **kwargs)
        mixins.ReplannerMixin.__init__(self, problem)

    @property
    def name(self) -> str:
        return f"Replanner[{self.engine.name}]"

    @staticmethod
    def is_compatible_engine(engine: Type[Engine]) -> bool:
        return engine.is_oneshot_planner() and engine.supports(ProblemKind({"ACTION_BASED"}))  # type: ignore

    @staticmethod
    def satisfies(optimality_guarantee: OptimalityGuarantee) -> bool:
        return False

    @staticmethod
    def _supported_kind(engine: Type[Engine]) -> "ProblemKind":
        features = set(engine.supported_kind().features)
        features.discard("HIERARCHICAL")
        supported_kind = ProblemKind(features)
        return supported_kind

    @staticmethod
    def _supports(problem_kind: "ProblemKind", engine: Type[Engine]) -> bool:
        return problem_kind <= Replanner._supported_kind(engine)

    def _resolve(
        self,
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> "up.engines.results.PlanGenerationResult":
        assert isinstance(self._problem, up.model.Problem)
        assert isinstance(self.engine, mixins.OneshotPlannerMixin)
        return self.engine.solve(
            self._problem, timeout=timeout, output_stream=output_stream
        )

    def _update_initial_value(
        self,
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: Union[
            "up.model.fnode.FNode",
            "up.model.fluent.Fluent",
            "up.model.object.Object",
            bool,
            int,
            float,
            Fraction,
        ],
    ):
        assert isinstance(self._problem, up.model.Problem)
        self._problem.set_initial_value(fluent, value)

    def _add_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        assert isinstance(self._problem, up.model.Problem)
        self._problem.add_goal(goal)

    def _remove_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        assert isinstance(self._problem, up.model.Problem)
        (goal_exp,) = self._problem.env.expression_manager.auto_promote(goal)
        goals = self._problem.goals
        self._problem.clear_goals()
        for g in goals:
            if not g is goal_exp:
                self._problem.add_goal(g)

    def _add_action(self, action: "up.model.action.Action"):
        assert isinstance(self._problem, up.model.Problem)
        self._problem.add_action(action)

    def _remove_action(self, name: str):
        assert isinstance(self._problem, up.model.Problem)
        actions = self._problem.actions
        self._problem.clear_actions()
        for a in actions:
            if a.name != name:
                self._problem.add_action(a)
