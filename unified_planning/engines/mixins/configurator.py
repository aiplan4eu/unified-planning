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
from typing import Any, Dict, Type


class ConfiguratorMixin:
    """Base class that must be extended by an :class:`~unified_planning.engines.Engine` that is also a `Configurator`."""

    def __init__(self, EngineClass: Type):
        if not issubclass(EngineClass, up.engines.engine.Engine):
            raise up.exceptions.UPUsageError(
                "The given EngineClass is not a subclass of up.engines.Engine!"
            )
        self._engine_class = EngineClass

    @staticmethod
    def is_configurator() -> bool:
        return True

    @staticmethod
    def supports_operation_mode_for_configuration(
        operation_mode: "up.engines.engine.OperationMode", EngineClass: Type
    ) -> bool:
        """
        :param operation_mode: The `operation_mode` that must be supported for the given EngineClass.
        :param EngineClass: The class of the `Engine` to test for the given `OperationMode`.
        :return: `True` if the `Configurator` implementation supports the given
            `operation_mode` for the given EngineClass, `False` otherwise.
        """
        return False

    def get_best_parameters(
        self,
        problem: "up.model.AbstractProblem",
        operation_mode: "up.engines.engine.OperationMode",
    ) -> Dict[str, Any]:
        """
        This method takes an `AbstractProblem` and an operation_mode and returns the best parameters
        to give to the EngineClass taken at construction time to solve the given problem.

        When using the Configurator operation mode (from the factory or the shortcuts), the EngineClass
        is given trough the engine_name argument (the first one).

        :param problem: the problem on which the performance parameters must be tuned.
        :param operation_mode: the Operation Mode in which the Engine Class is supposed to work.
        :return: The best parameters to instantiate the given EngineClass to solve the given problem.
        """
        assert isinstance(self, up.engines.engine.Engine)
        problem_kind = problem.kind
        if not self.skip_checks and not self.supports(problem_kind):
            msg = f"{self.name} cannot configure this kind of problem!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warn(msg)
        if not self.skip_checks and not self.supports_operation_mode_for_configuration(
            operation_mode, self._engine_class
        ):
            msg = f"{self.name} does not support the {operation_mode}!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warn(msg)
        return self._get_best_parameters(problem, operation_mode)

    def _get_best_parameters(
        self,
        problem: "up.model.AbstractProblem",
        operation_mode: "up.engines.engine.OperationMode",
    ) -> Dict[str, Any]:
        """Method called by the PortfolioSelectorMixin.get_best_engines method."""
        raise NotImplementedError
