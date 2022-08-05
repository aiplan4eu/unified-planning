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

from warnings import warn
import unified_planning as up
from unified_planning.model import ProblemKind
from enum import Enum, auto
from typing import Optional


class CompilationKind(Enum):
    GROUNDING = auto()
    CONDITIONAL_EFFECTS_REMOVING = auto()
    DISJUNCTIVE_CONDITIONS_REMOVING = auto()
    NEGATIVE_CONDITIONS_REMOVING = auto()
    QUANTIFIERS_REMOVING = auto()


class CompilerMixin:
    def __init__(self, default: Optional[CompilationKind] = None):
        self._default = default

    @property
    def default(self) -> CompilationKind:
        """Returns the default compilation kind.

        :return: The default compilation kind.
        """
        return self._default

    @default.setter
    def default(self, default: Optional[CompilationKind] = None):
        """Sets the default compilation kind.

        :default: The default compilation kind to set.
        """
        self._default = default

    @staticmethod
    def is_compiler() -> bool:
        return True

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        raise NotImplementedError

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: CompilationKind
    ) -> ProblemKind:
        """Returns the problem kind of a problem resulting by the given compilation
        applied to a problem that has the given problem kind.

        :param problem_kind: The given problem kind.
        :param compilation_kind: The given compilation kind.
        :return: The resulting problem kind.
        """
        raise NotImplementedError

    def compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: Optional[CompilationKind] = None,
    ) -> "up.engines.results.CompilerResult":
        """
        Takes an instance of a up.model.AbstractProblem and a supported
        up.engines.CompilationKind and returns the data structure
        containing the compiled problem, a function that allows the rewriting
        of a plan from the compiled problem to the original one and
        some compiler info, like the name and some logs on the compiling.

        If the compilation_kind is not specified, the default is used.

        :param problem: The instance of the up.model.AbstractProblem on which the compilation is applied.
        :param compilation_kind: The up.engines.CompilationKind that must be applied on the given problem.
        :return: The resulting up.engines.results.CompilerResult data structure.
        """
        assert isinstance(self, up.engines.engine.Engine)
        if compilation_kind is None:
            compilation_kind = self._default
        if compilation_kind is None:
            raise up.exceptions.UPUsageError(f"Compilation kind needs to be specified!")
        if not self.skip_checks and not self.supports(problem.kind):
            msg = f"{self.name} cannot handle this kind of problem!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warn(msg)
        if not self.supports_compilation(compilation_kind):
            msg = f"{self.name} cannot handle this kind of compilation!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warn(msg)
        return self._compile(problem, compilation_kind)

    def _compile(
        self, problem: "up.model.AbstractProblem", compilation_kind: CompilationKind
    ) -> "up.engines.results.CompilerResult":
        raise NotImplementedError
