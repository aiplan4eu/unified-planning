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

import time
import unified_planning as up
import unified_planning.engines.mixins as mixins
import unified_planning.engines.results
from unified_planning.model import ProblemKind
from unified_planning.engines.engine import Engine
from unified_planning.engines.meta_engine import MetaEngine
from unified_planning.engines.mixins.oneshot_planner import OptimalityGuarantee
from unified_planning.utils import powerset
from typing import Type, IO, Callable, Optional, Union, List, Tuple
from fractions import Fraction


class OversubscriptionPlanner(MetaEngine, mixins.OneshotPlannerMixin):
    def __init__(self, *args, **kwargs):
        MetaEngine.__init__(self, *args, **kwargs)
        mixins.OneshotPlannerMixin.__init__(self)

    @property
    def name(self) -> str:
        return f"OversubscriptionPlanner[{self.engine.name}]"

    @staticmethod
    def satisfies(optimality_guarantee: OptimalityGuarantee) -> bool:
        return True

    @staticmethod
    def is_compatible_engine(engine: Type[Engine]) -> bool:
        return engine.is_oneshot_planner()  # type: ignore

    @staticmethod
    def _supported_kind(engine: Type[Engine]) -> "ProblemKind":
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_numbers("CONTINUOUS_NUMBERS")
        supported_kind.set_numbers("DISCRETE_NUMBERS")
        supported_kind.set_fluents_type("NUMERIC_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITY")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECT")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATION")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATION")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        final_supported_kind = supported_kind.intersection(engine.supported_kind())
        final_supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        return final_supported_kind

    @staticmethod
    def _supports(problem_kind: "ProblemKind", engine: Type[Engine]) -> bool:
        return problem_kind <= OversubscriptionPlanner._supported_kind(engine)

    def _solve(
        self,
        problem: "up.model.AbstractProblem",
        callback: Optional[
            Callable[["up.engines.results.PlanGenerationResult"], None]
        ] = None,
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> "up.engines.results.PlanGenerationResult":
        assert isinstance(problem, up.model.Problem)
        assert isinstance(self.engine, mixins.OneshotPlannerMixin)
        if len(problem.quality_metrics) == 0:
            goals: List[Tuple["up.model.FNode", Union[Fraction, int]]] = []
        else:
            assert len(problem.quality_metrics) == 1
            qm = problem.quality_metrics[0]
            assert isinstance(qm, up.model.metrics.Oversubscription)
            goals = list(qm.goals.items())
        q = []
        for l in powerset(goals):
            cost: Union[Fraction, int] = 0
            sg = []
            for g, c in l:
                cost += c
                sg.append(g)
            q.append((cost, sg))
        p.sort(reverse=True, key=lambda t: t[0])
        while t in p:
            new_problem = problem.clone()
            new_problem.clear_quality_metrics()
            for g in t[1]:
                new_problem.add_goal(g)
            start = time.time()
            res = self.engine.solve(new_problem, callback, timeout, output_stream)
            if timeout is not None:
                timeout -= time.time() - start
            if res.status in up.engines.results.POSITIVE_OUTCOMES:
                return res
        return res
