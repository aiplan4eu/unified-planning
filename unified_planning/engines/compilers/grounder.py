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

import unified_planning as up
import unified_planning.environment
import unified_planning.engines as engines
import unified_planning.engines.compilers
from unified_planning.plans import ActionInstance
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import Problem, ProblemKind, Action, Type, Expression, FNode
from unified_planning.model.types import domain_size, domain_item
from unified_planning.model.walkers import Substituter, Simplifier
from unified_planning.engines.compilers.utils import (
    lift_action_instance,
    create_action_with_given_subs,
)
from typing import Dict, List, Optional, Tuple, Iterator
from itertools import product
from functools import partial


class Grounder(engines.engine.Engine, CompilerMixin):
    """Performs action grounding."""

    def __init__(
        self,
        grounding_actions_map: Optional[Dict[Action, List[Tuple[FNode, ...]]]] = None,
    ):
        engines.engine.Engine.__init__(self)
        self._grounding_actions_map = grounding_actions_map

    @property
    def name(self):
        return "grounder"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_numbers("CONTINUOUS_NUMBERS")
        supported_kind.set_numbers("DISCRETE_NUMBERS")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
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
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= Grounder.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.GROUNDING

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        assert isinstance(problem, Problem)

        env = problem.env
        substituter = Substituter(env)
        simplifier = Simplifier(env, problem)
        trace_back_map: Dict[Action, Tuple[Action, List[FNode]]] = {}

        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_actions()
        for old_action in problem.actions:
            # contains the type of every parameter of the action
            type_list: List[Type] = [param.type for param in old_action.parameters]
            # if the action does not have parameters, it does not need to be grounded.
            if len(type_list) == 0:
                if (
                    self._grounding_actions_map is None
                    or self._grounding_actions_map.get(old_action, None) is not None
                ):
                    new_action = old_action.clone()
                    new_problem.add_action(new_action)
                    trace_back_map[new_action] = (old_action, [])
                continue
            grounded_params_list: Optional[Iterator[Tuple[FNode, ...]]] = None
            if self._grounding_actions_map is None:
                # a list containing the list of object in the problem of the given type.
                # So, if the problem has 2 Locations l1 and l2, and 2 Robots r1 and r2, and
                # the action move_to takes as parameters a Robot and a Location,
                # the variable state at this point will be the following:
                # type_list = [Robot, Location]
                # objects_list = [[r1, r2], [l1, l2]]
                # the product of *objects_list will be:
                # [(r1, l1), (r1, l2), (r2, l1), (r2,l2)]
                ground_size = 1
                domain_sizes = []
                for t in type_list:
                    ds = domain_size(new_problem, t)
                    domain_sizes.append(ds)
                    ground_size *= ds
                items_list: List[List[FNode]] = []
                for size, type in zip(domain_sizes, type_list):
                    items_list.append(
                        [domain_item(new_problem, type, j) for j in range(size)]
                    )
                grounded_params_list = product(*items_list)
            else:
                # The grounding_actions_map is not None, therefore it must be used to ground
                grounded_params_list = iter(self._grounding_actions_map[old_action])
            assert grounded_params_list is not None
            for grounded_params in grounded_params_list:
                subs: Dict[Expression, Expression] = dict(
                    zip(old_action.parameters, list(grounded_params))
                )
                new_action = create_action_with_given_subs(
                    problem, old_action, simplifier, substituter, subs
                )
                # when the action is None it means it is not feasible,
                # it's conditions are in contraddiction within one another.
                if new_action is not None:
                    trace_back_map[new_action] = (
                        old_action,
                        env.expression_manager.auto_promote(subs.values()),
                    )
                    new_problem.add_action(new_action)

        return CompilerResult(
            new_problem, partial(lift_action_instance, map=trace_back_map), self.name
        )
