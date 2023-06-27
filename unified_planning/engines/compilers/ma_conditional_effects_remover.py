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
"""This module defines the multi-agent conditional effects remover class."""

import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.compilers.utils import replace_action
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    ProblemKind,
)
from functools import partial
from unified_planning.engines.compilers.conditional_effects_remover import (
    ConditionalEffectsRemover,
)
from unified_planning.model.multi_agent.ma_problem import MultiAgentProblem

from unified_planning.model import ProblemKind
from unified_planning.engines.compilers.utils import (
    replace_action,
)


class MAConditionalEffectsRemover(ConditionalEffectsRemover):
    """
    Conditional effects remover class: this class offers the capability
    to transform a :class:`~unified_planning.model.MultiAgentProblem` with conditional :class:`Effects <unified_planning.model.Effect>`
    into a `Problem` without conditional `Effects`. This capability is offered by the :meth:`~unified_planning.engines.compilers.MAConditionalEffectsRemover.compile`
    method, that returns a :class:`~unified_planning.engines.CompilerResult` in which the :meth:`problem <unified_planning.engines.CompilerResult.problem>` field
    is the compiled Problem.

    This is done by substituting every conditional :class:`~unified_planning.model.Action` with different
    actions representing every possible branch of the original action.

    When it is not possible to remove a conditional Effect without changing the semantic of the resulting Problem,
    an :exc:`~unified_planning.exceptions.UPProblemDefinitionError` is raised.

    This `Compiler` supports only the the `CONDITIONAL_EFFECTS_REMOVING` :class:`~unified_planning.engines.CompilationKind`.
    """

    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.CONDITIONAL_EFFECTS_REMOVING)

    @property
    def name(self):
        return "ma_cerm"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ConditionalEffectsRemover.supported_kind()
        supported_kind.unset_problem_class("ACTION_BASED")
        supported_kind.set_problem_class("ACTION_BASED_MULTI_AGENT")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= MAConditionalEffectsRemover.supported_kind()

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """
        Takes an instance of a :class:`~unified_planning.model.MultiAgentProblem` and the wanted :class:`~unified_planning.engines.CompilationKind`
        and returns a :class:`~unified_planning.engines.results.CompilerResult` where the :meth:`problem<unified_planning.engines.results.CompilerResult.problem>` field does not have conditional effects.

        :param problem: The instance of the :class:`~unified_planning.model.MultiAgentProblem` that must be returned without conditional effects.
        :param compilation_kind: The :class:`~unified_planning.engines.CompilationKind` that must be applied on the given problem;
            only :class:`~unified_planning.engines.CompilationKind.CONDITIONAL_EFFECTS_REMOVING` is supported by this compiler
        :return: The resulting :class:`~unified_planning.engines.results.CompilerResult` data structure.
        :raises: :exc:`~unified_planning.exceptions.UPProblemDefinitionError` when the :meth:`condition<unified_planning.model.Effect.condition>` of an
            :class:`~unified_planning.model.Effect` can't be removed without changing the :class:`~unified_planning.model.Problem` semantic.
        """
        assert isinstance(problem, MultiAgentProblem)

        new_to_old = {}

        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"

        for ag in problem.agents:
            new_ag = new_problem.agent(ag.name)
            new_ag.clear_actions()
            for ua in ag.unconditional_actions:
                new_uncond_action = ua.clone()
                new_ag.add_action(new_uncond_action)
                new_to_old[new_uncond_action] = ua
            for action in ag.conditional_actions:
                for new_action in self._create_unconditional_actions(
                    action, new_problem
                ):
                    new_to_old[new_action] = action
                    new_ag.add_action(new_action)
            new_problem.add_agent(new_ag)

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )
