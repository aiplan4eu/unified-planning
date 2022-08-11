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
"""This module defines the meta engine interface."""

from unified_planning.exceptions import UPUsageError
from unified_planning.engines.engine import Engine, EngineMeta
from unified_planning.model import ProblemKind
from functools import partial
from typing import Type


class MetaEngineMeta(EngineMeta):
    def __getitem__(self, engine_class: Type[Engine]):
        assert issubclass(self, MetaEngine)
        if not self.is_compatible_engine(engine_class):  # type: ignore
            raise UPUsageError(f"{engine_class.name} is not compatible with the meta engine {self.name}")  # type: ignore

        class MetaEngineImpl(self):  # type: ignore
            _engine_class = engine_class

            @staticmethod
            def supported_kind() -> ProblemKind:
                return self._supported_kind(engine_class)  # type: ignore

            @staticmethod
            def supports(problem_kind: ProblemKind) -> bool:
                return self._supports(problem_kind, engine_class)  # type: ignore

        return MetaEngineImpl


class MetaEngine(Engine, metaclass=MetaEngineMeta):
    """
    This class represents a meta engine.
    A meta engine is an `Engine` that can be instantiated over a generic `Engine`.

    e.g. `OversubscriptionPlanner[Tamer]` is an `Engine class` that use the `MetaEngine`
    `OversubscriptionPlanner` over the `Tamer Engine`.
    """

    def __init__(self, *args, **kwargs):
        Engine.__init__(self)
        self._engine = self._engine_class(*args, **kwargs)

    @property
    def engine(self) -> Engine:
        """Returns the engine used by this `MetaEngine` class"""
        return self._engine

    @property
    def skip_checks(self) -> bool:
        """Same as :func:`skip_checks <unified_planning.engines.Engine.skip_checks>`"""
        return self._skip_checks

    @skip_checks.setter
    def skip_checks(self, new_value: bool):
        """Same as :func:`skip_checks <unified_planning.engines.Engine.skip_checks>`"""
        self._skip_checks = new_value
        self._engine.skip_checks = new_value

    @property
    def error_on_failed_checks(self) -> bool:
        """Same as :func:`error_on_failed_checks <unified_planning.engines.Engine.error_on_failed_checks>`"""
        return self._error_on_failed_checks

    @error_on_failed_checks.setter
    def error_on_failed_checks(self, new_value: bool):
        """Same as :func:`error_on_failed_checks <unified_planning.engines.Engine.error_on_failed_checks>`"""
        self._error_on_failed_checks = new_value
        self.engine.error_on_failed_checks = new_value

    @staticmethod
    def is_compatible_engine(engine: Type[Engine]) -> bool:
        """
        Returns `True` iff the given `engine` is compatible with this `MetaEngine`.

        :param engine: The `Engine` Class tested for compatibility.
        :return: `True` iff the given `engine` is compatible with this `MetaEngine`
        """
        raise NotImplementedError

    @staticmethod
    def _supported_kind(engine: Type[Engine]) -> ProblemKind:
        """Returns the supported kind of this meta engine with the given engine"""
        raise NotImplementedError

    @staticmethod
    def _supports(problem_kind: ProblemKind, engine: Type[Engine]) -> bool:
        """Returns true iff the given problem kind is supported by this meta
        engine with the given engine"""
        raise NotImplementedError
