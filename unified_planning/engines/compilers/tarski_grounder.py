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
"""This module implements the grounder that uses tarski."""


import shutil
from typing import Optional, Tuple, Dict, List
import tarski
import unified_planning as up
import unified_planning.interop
from unified_planning.interop.from_tarski import convert_tarski_formula
from unified_planning.model import Action, FNode, Problem, ProblemKind
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.engine import Engine, Credits
from unified_planning.engines.results import CompilerResult
from unified_planning.engines.compilers.grounder import Grounder
from unified_planning.exceptions import UPUsageError
from tarski.grounding import LPGroundingStrategy


gringo = shutil.which("gringo")
if gringo is None:
    raise ImportError("Tarski grounder needs gringo installed")

credits = Credits(
    "Tarski grounder",
    "Artificial Intelligence and Machine Learning Group - Universitat Pompeu Fabra",
    "info-ai@upf.edu",
    "https://github.com/aig-upf/tarski",
    "Apache 2.0",
    "Tarski grounder, more information available on the given website.",
    "Tarski grounder, more information available on the given website.",
)


class TarskiGrounder(Engine, CompilerMixin):
    """
    Implements a Grounder using `tarski <https://github.com/aig-upf/tarski>`_ .
    For more details about Grounding check the :class:`~unified_planning.engines.compilers.Grounder`
    documentation.
    """

    def __init__(self, **kwargs):
        Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.GROUNDING)
        if len(kwargs) > 0:
            raise ValueError(f"Unknown parameters passed to TarskiGrounder: {kwargs}")

    @property
    def name(self) -> str:
        return "tarski_grounder"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_constraints_kind("STATE_INVARIANTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        return supported_kind

    @staticmethod
    def supports(problem_kind: "unified_planning.model.ProblemKind") -> bool:
        return problem_kind <= TarskiGrounder.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.GROUNDING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        return ProblemKind(problem_kind.features)

    def _compile(
        self, problem: "up.model.AbstractProblem", compilation_kind: "CompilationKind"
    ) -> CompilerResult:
        """
        Takes an instance of a :class:`~unified_planning.model.Problem` and the `GROUNDING` :class:`~unified_planning.engines.CompilationKind`
        and returns a `CompilerResult` where the problem does not have actions with parameters; so every action is grounded.

        :param problem: The instance of the `Problem` that must be grounded.
        :param compilation_kind: The `CompilationKind` that must be applied on the given problem;
            only `GROUNDING` is supported by this compiler
        :return: The resulting `CompilerResult` data structure.
        """
        assert isinstance(problem, Problem)

        tarski_problem = up.interop.convert_problem_to_tarski(problem)
        actions = None
        try:
            lpgs = LPGroundingStrategy(tarski_problem)
            actions = lpgs.ground_actions()
        except tarski.grounding.errors.ReachabilityLPUnsolvable:
            raise up.exceptions.UPUsageError(
                "tarski grounder can not find a solvable grounding."
            )
        grounded_actions_map: Dict[Action, List[Tuple[FNode, ...]]] = {}
        fluents = {fluent.name: fluent for fluent in problem.fluents}
        objects = {object.name: object for object in problem.all_objects}
        types: Dict[str, Optional["up.model.Type"]] = {}
        if not problem.has_type("object"):
            types[
                "object"
            ] = None  # we set object as None, so when it is the father of a type in tarski, in UP it will be None.
        for action_name, list_of_tuple_of_parameters in actions.items():
            action = problem.action(action_name)
            parameters = {parameter.name: parameter for parameter in action.parameters}
            grounded_actions_map[action] = []
            for tuple_of_parameters in list_of_tuple_of_parameters:
                temp_list_of_converted_parameters = []
                for p in tuple_of_parameters:
                    if isinstance(p, str):
                        temp_list_of_converted_parameters.append(
                            problem.environment.expression_manager.ObjectExp(
                                problem.object(p)
                            )
                        )
                    else:
                        temp_list_of_converted_parameters.append(
                            convert_tarski_formula(
                                problem.environment,
                                fluents,
                                objects,
                                parameters,
                                types,
                                p,
                            )
                        )
                grounded_actions_map[action].append(
                    tuple(temp_list_of_converted_parameters)
                )
        up_grounder = Grounder(grounding_actions_map=grounded_actions_map)
        up_res = up_grounder.compile(problem, compilation_kind)
        return CompilerResult(
            up_res.problem, up_res.map_back_action_instance, self.name
        )

    @staticmethod
    def get_credits(**kwargs) -> Optional[Credits]:
        """Returns the up.engines.engine.Credits instance created for the TarskiGrounder."""
        return credits

    def destroy(self):
        pass
