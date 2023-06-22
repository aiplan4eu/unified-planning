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
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.exceptions import UPUsageError
from unified_planning.plans import ActionInstance
from typing import List, Callable, Optional
from functools import partial
from warnings import warn


class CompilersPipeline(engines.engine.Engine, CompilerMixin):
    """
    This engine implements a compilers pipeline.
    A list of compilers is given in the class constructor and the engine implements
    the compile operation mode executing the pipeline of the given compilers.
    """

    def __init__(self, compilers: List[engines.engine.Engine]):
        CompilerMixin.__init__(self)
        self._compilers = compilers

    @property
    def name(self):
        return f"CompilersPipeline[{', '.join([e.name for e in self._compilers])}]"

    @staticmethod
    def supported_kind() -> "up.model.ProblemKind":
        raise UPUsageError(
            "The supported kind depends on the actual compilers of the pipeline"
        )

    @staticmethod
    def supports(problem_kind: "up.model.ProblemKind") -> bool:
        raise UPUsageError(
            "The supported kind depends on the actual compilers of the pipeline"
        )

    @staticmethod
    def supports_compilation(compilation_kind: "up.engines.CompilationKind") -> bool:
        raise UPUsageError(
            "The supported compilation depends on the actual compilers of the pipeline"
        )

    @staticmethod
    def resulting_problem_kind(
        problem_kind: "up.model.ProblemKind",
        compilation_kind: Optional["up.engines.CompilationKind"] = None,
    ) -> "up.model.ProblemKind":
        raise UPUsageError(
            "The resulting problem kind depends on the actual compilers of the pipeline"
        )

    def compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: Optional["up.engines.CompilationKind"] = None,
    ) -> "up.engines.results.CompilerResult":
        assert isinstance(self, engines.engine.Engine)
        if compilation_kind is not None:
            raise UPUsageError(
                "Compilers pipeline ignores the compilation_kind parameter"
            )
        new_problem: "up.model.AbstractProblem" = problem
        map_back_functions = []
        for engine in self._compilers:
            assert isinstance(engine, CompilerMixin)
            if not engine.supports(new_problem.kind):
                raise UPUsageError(f"{engine.name} cannot handle this kind of problem!")
            res = engine.compile(new_problem)
            map_back_functions.append(res.map_back_action_instance)
            if res.problem is None:
                return CompilerResult(None, None, self.name)
            new_problem = res.problem
        map_back_functions.reverse()
        return CompilerResult(
            new_problem,
            partial(map_back_action_instance, map_back_functions=map_back_functions),
            self.name,
        )

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> "up.engines.results.CompilerResult":
        """Method called by :func:`~unified_planning.engines.mixins.CompilerMixin.compile` to get the returned :class:`~unified_planning.engines.CompilerResult`."""
        raise UPUsageError(
            "The CompilersPipeline does not implement the _compile method but overrides the compile method directly."
        )


def map_back_action_instance(
    action: ActionInstance,
    map_back_functions: List[Callable[[ActionInstance], ActionInstance]],
) -> Optional[ActionInstance]:
    for f in map_back_functions:
        action = f(action)
        if action is None:
            break
    return action
