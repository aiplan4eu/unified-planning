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
from unified_planning.model import ProblemKind
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional
from warnings import warn


class CompilationKind(Enum):
    """Enum representing the available compilation kinds currently in the library."""

    GROUNDING = auto()
    CONDITIONAL_EFFECTS_REMOVING = auto()
    DISJUNCTIVE_CONDITIONS_REMOVING = auto()
    NEGATIVE_CONDITIONS_REMOVING = auto()
    QUANTIFIERS_REMOVING = auto()
    TRAJECTORY_CONSTRAINTS_REMOVING = auto()
    USERTYPE_FLUENTS_REMOVING = auto()
    BOUNDED_TYPES_REMOVING = auto()


class CompilerMixin(ABC):
    """Generic class for a compiler defining it's interface."""

    def __init__(self, default: Optional[CompilationKind] = None):
        self._default = default

    def compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: Optional[CompilationKind] = None,
    ) -> "up.engines.results.CompilerResult":
        """
        Takes an instance of an `AbstractProblem` and a supported
        `CompilationKind` and returns the generated `CompilerResult`; a data structure
        containing the compiled `AbstractProblem`, a function that allows the rewriting
        of a :class:`~unified_planning.plans.Plan` generated for the compiled `AbstractProblem` to a `Plan`
        for the original `AbstractProblem` and some compiler info, like the name and some logs on the compiling.

        If the `compilation_kind` is not specified, the `default` is used.

        For more information about the `CompilerResult` returned, read the class documentation
        above.

        :param problem: The instance of the `AbstractProblem` on which the compilation is applied.
        :param compilation_kind: The `CompilationKind` that must be applied on the given problem.
        :return: The resulting `CompilerResult`.
        :raises: :exc:`~unified_planning.exceptions.UPUsageError` if the given `compilation_kind` is None and the
            :func:`default<unified_planning.engines.mixins.CompilerMixin.default>` is None or
            if the given `compilation_kind` is not supported by the
            :func:`~unified_planning.engines.mixins.CompilerMixin.supports_compilation` method or
            if the :func:`problem_kind <unified_planning.model.Problem.kind>` is not supported by the
            :func:`~unified_planning.engines.Engine.supports` method.
        """
        assert isinstance(self, up.engines.engine.Engine)
        if compilation_kind is None:
            compilation_kind = self._default
        if compilation_kind is None:
            raise up.exceptions.UPUsageError(f"Compilation kind needs to be specified!")
        if not self.skip_checks and not self.supports(problem.kind):
            msg = f"We cannot establish whether {self.name} can handle this problem!"
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

    @property
    def default(self) -> Optional[CompilationKind]:
        """
        Returns the default compilation kind for this compiler.
        When a compiler is returned with the :meth:`~unified_planning.engines.Factory.Compiler` operation mode
        with a `CompilationKind` as parameter, the given `CompilationKind` is set as the `default`.

        :return: The `CompilationKind` set as default.
        """
        return self._default

    @default.setter
    def default(self, default: Optional[CompilationKind]):
        """
        Sets the default compilation kind.

        :default: The default compilation kind to set.
        """
        self._default = default

    @staticmethod
    def is_compiler() -> bool:
        """Returns True."""
        return True

    @staticmethod
    @abstractmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        """
        :param compilation_kind: The tested `CompilationKind`.
        :return: True if the given `CompilationKind` is supported
            by this compiler, False otherwise.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        """
        Returns the `ProblemKind` of an :class:`~unified_planning.model.AbstractProblem` which is returned by the
        :meth:`~unified_planning.engines.mixins.compiler.CompilerMixin.compile` method with the given `CompilationKind`.

        :param problem_kind: The given `ProblemKind`.
        :param compilation_kind: The `CompilationKind` applied to modify the `ProblemKind`.
        :return: The resulting `ProblemKind`.
        """
        raise NotImplementedError

    @abstractmethod
    def _compile(
        self, problem: "up.model.AbstractProblem", compilation_kind: CompilationKind
    ) -> "up.engines.results.CompilerResult":
        """Method called by :func:`~unified_planning.engines.mixins.CompilerMixin.compile` to get the returned :class:`~unified_planning.engines.CompilerResult`."""
        raise NotImplementedError
