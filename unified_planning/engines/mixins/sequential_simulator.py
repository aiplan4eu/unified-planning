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

import inspect
from typing import Iterator, List, Optional, Tuple, Union, Sequence
from warnings import warn
import unified_planning as up
from unified_planning.exceptions import UPUsageError, UPInvalidActionError


class SequentialSimulatorMixin:
    """
    SequentialSimulatorMixin abstract class.
    This class defines the interface that an :class:`~unified_planning.engines.Engine`
    that is also a `SequentialSimulator` must implement.

    Important NOTE: The `AbstractProblem` instance is given at the constructor.
    """

    def __init__(self, problem: "up.model.AbstractProblem") -> None:
        """
        Takes an instance of a `problem` and eventually some parameters, that represent
        some specific settings of the `SequentialSimulatorMixin`.

        :param problem: the `problem` that defines the domain in which the simulation exists.
        """
        self._problem = problem
        self_class = type(self)
        assert issubclass(
            self_class, up.engines.engine.Engine
        ), "SequentialSimulatorMixin does not implement the up.engines.Engine class"
        assert isinstance(self, up.engines.engine.Engine)
        if not self.skip_checks and not self_class.supports(problem.kind):
            msg = f"We cannot establish whether {self.name} is able to handle this problem!"
            if self.error_on_failed_checks:
                raise UPUsageError(msg)
            else:
                warn(msg)

    def _get_action_and_parameters(
        self,
        action_or_action_instance: Union["up.model.Action", "up.plans.ActionInstance"],
        parameters: Optional[Sequence["up.model.Expression"]] = None,
    ) -> Tuple["up.model.Action", Tuple["up.model.FNode", ...]]:
        """
        This is a utility method to handle the methods polymorphism.

        :param action_or_action_instance: The ActionInstance given to the method or the
            Action.
        :param parameters: The parameter or the Sequence of parameters. The length of this
            field must be equal to the len of the action's parameters. If action_or_action_instance
            is an ActionInstance this param must be None.
        :param method name: The name of the original method. Used for better error indexing.
        :return: The couple of the Action together with it's parameters.
        """
        if isinstance(action_or_action_instance, up.plans.ActionInstance):
            if parameters is not None:
                method_name = inspect.stack()[1].function
                assert isinstance(self, up.engines.engine.Engine)
                raise UPUsageError(
                    f"{self.name}.{method_name} method does not accept an ActionInstance and also the parameters."
                )
            act = action_or_action_instance.action
            params = action_or_action_instance.actual_parameters
            return act, params
        act = action_or_action_instance
        assert isinstance(act, up.model.Action), "Typing not respected"
        auto_promote = self._problem.environment.expression_manager.auto_promote
        if parameters is None:
            params = tuple()
        else:
            assert isinstance(parameters, Sequence), "Typing not respected"
            params = tuple(auto_promote(parameters))
        if len(params) != len(act.parameters) or any(
            not ap.type.is_compatible(p.type) for p, ap in zip(params, act.parameters)
        ):
            method_name = inspect.stack()[1].function
            assert isinstance(self, up.engines.engine.Engine)
            raise UPUsageError(
                f"The parameters given to the {self.name}.{method_name} method are ",
                "not compatible with the given action's parameters.",
            )
        return act, params

    def get_initial_state(self) -> "up.model.State":
        """
        Returns the problem's initial state.

        NOTE: Every different SequentialSimulator might assume that the State class
        implementation given to it's other methods is the same returned by this method.
        """
        return self._get_initial_state()

    def _get_initial_state(self) -> "up.model.State":
        """Method called by the up.engines.mixins.sequential_simulator.SequentialSimulatorMixin.get_initial_state."""
        raise NotImplementedError

    def is_applicable(
        self,
        state: "up.model.State",
        action_or_action_instance: Union["up.model.Action", "up.plans.ActionInstance"],
        parameters: Optional[Sequence["up.model.Expression"]] = None,
    ) -> bool:
        """
        Returns `True` if the given `action conditions` are evaluated as `True` in the given `state`;
        returns `False` otherwise.

        :param state: The state in which the given action is checked for applicability.
        :param action_or_action_instance: The `ActionInstance` or the `Action` that must be checked
            for applicability.
        :param parameters: The parameters to ground the given `Action`. This param must be `None` if
            an `ActionInstance` is given instead.
        :return: Whether or not the action is applicable in the given `state`.
        """
        act, params = self._get_action_and_parameters(
            action_or_action_instance,
            parameters,
        )
        return self._is_applicable(state, act, params)

    def _is_applicable(
        self,
        state: "up.model.State",
        action: "up.model.Action",
        parameters: Tuple["up.model.FNode", ...],
    ) -> bool:
        """
        Method called by the up.engines.mixins.sequential_simulator.SequentialSimulatorMixin.is_applicable.
        """
        raise NotImplementedError

    def apply(
        self,
        state: "up.model.State",
        action_or_action_instance: Union["up.model.Action", "up.plans.ActionInstance"],
        parameters: Optional[Sequence["up.model.Expression"]] = None,
    ) -> Optional["up.model.State"]:
        """
        Returns `None` if the given `action` is not applicable in the given `state`, otherwise returns a new `State`,
        which is a copy of the given `state` where the `applicable effects` of the `action` are applied; therefore
        some `fluent values` are updated.

        :param state: The state in which the given action's conditions are checked and the effects evaluated.
        :param action_or_action_instance: The `ActionInstance` or the `Action` of which conditions are checked
            and effects evaluated.
        :param parameters: The parameters to ground the given `Action`. This param must be `None` if
            an `ActionInstance` is given instead.
        :return: `None` if the `action` is not applicable in the given `state`, the new State generated
            if the action is applicable.
        """
        act, params = self._get_action_and_parameters(
            action_or_action_instance,
            parameters,
        )
        return self._apply(state, act, params)

    def _apply(
        self,
        state: "up.model.State",
        action: "up.model.Action",
        parameters: Tuple["up.model.FNode", ...],
    ) -> Optional["up.model.State"]:
        """
        Method called by the up.engines.mixins.sequential_simulator.SequentialSimulatorMixin.apply.
        """
        raise NotImplementedError

    def get_applicable_actions(
        self, state: "up.model.State"
    ) -> Iterator[Tuple["up.model.Action", Tuple["up.model.FNode", ...]]]:
        """
        Returns a view over all the `action + parameters` that are applicable in the given `State`.

        :param state: the `state` where the formulas are evaluated.
        :return: an `Iterator` of applicable actions + parameters.
        """
        return self._get_applicable_actions(state)

    def _get_applicable_actions(
        self, state: "up.model.State"
    ) -> Iterator[Tuple["up.model.Action", Tuple["up.model.FNode", ...]]]:
        """
        Method called by the up.engines.mixins.sequential_simulator.SequentialSimulatorMixin.get_applicable_actions.
        """
        raise NotImplementedError

    @staticmethod
    def is_sequential_simulator():
        return True

    def is_goal(self, state: "up.model.State") -> bool:
        """
        Returns `True` if the given `state` satisfies the :class:`~unified_planning.model.AbstractProblem` :func:`goals <unified_planning.model.Problem.goals>`.

        NOTE: This method does not consider the :func:`quality_metrics <unified_planning.model.Problem.quality_metrics>` of the problem.

        :param state: the `State` in which the `problem goals` are evaluated.
        :return: `True` if the evaluation of every `goal` is `True`, `False` otherwise.
        """
        return self._is_goal(state)

    def _is_goal(self, state: "up.model.State") -> bool:
        """
        Method called by the up.engines.mixins.sequential_simulator.SequentialSimulatorMixin.is_goal.
        """
        raise NotImplementedError
