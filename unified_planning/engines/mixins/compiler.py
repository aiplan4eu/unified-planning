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
from enum import Enum, auto


class CompilationKind(Enum):
    GROUNDING = auto()
    CONDITIONAL_EFFECTS_REMOVING = auto()
    DISJUNCTIVE_CONDITIONS_REMOVING = auto()
    NEGATIVE_CONDITIONS_REMOVING = auto()
    QUANTIFIERS_REMOVING = auto()


class CompilerMixin:
    @staticmethod
    def is_compiler() -> bool:
        return True

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        raise NotImplementedError

    def compile(
        self, problem: "up.model.AbstractProblem", compilation_kind: CompilationKind
    ) -> "up.engines.results.CompilerResult":
        assert isinstance(self, up.engines.engine.Engine)
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
