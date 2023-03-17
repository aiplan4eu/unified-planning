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

from typing import Iterator, List, Optional, Tuple, Union, Sequence
from warnings import warn
import unified_planning as up
from unified_planning.exceptions import UPUsageError, UPInvalidActionError


class SequentialSimulatorMixin:
    """
    SequentialSimulatorMixin abstract class.
    This class defines the interface that an :class:`~unified_planning.engines.Engine`
    that is also a `Simulator` must implement.

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

    def _handle_action_or_action_instance_polymorphism(
        self,
        action_or_action_instance: Union["up.model.Action", "up.plans.ActionInstance"],
        parameters: Optional[
            Union["up.model.Expression", Sequence["up.model.Expression"]]
        ],
        method_name: str,
    ) -> Tuple["up.model.Action", Tuple["up.model.FNode", ...]]:
        """TODO"""
        if isinstance(action_or_action_instance, up.plans.ActionInstance):
            if parameters is not None:
                raise UPUsageError(
                    f"{type(self)}.{method_name} method does not accept an ActionInstance and also the parameters."
                )
            act = action_or_action_instance.action
            params = action_or_action_instance.actual_parameters
            return act, params
        act = action_or_action_instance
        assert isinstance(act, up.model.Action), "Typing not respected"
        auto_promote = self._problem.environment.expression_manager.auto_promote
        if parameters is None:
            params = tuple()
        elif isinstance(parameters, Sequence):
            params = tuple(auto_promote(parameters))
        else:
            params = tuple(auto_promote([parameters]))
        if len(params) != len(act.parameters) or any(
            not ap.type.is_compatible(p.type) for p, ap in zip(params, act.parameters)
        ):
            raise UPUsageError(
                f"The parameters given to the {type(self)}.{method_name} method are ",
                "not compatible with the given action's parameters.",
            )
        return act, params

    def get_initial_state(self) -> "up.model.State":
        """TODO"""
        return self._get_initial_state()

    def _get_initial_state(self) -> "up.model.State":
        """Method called by the up.engines.mixins.sequential_simulator.SequentialSimulatorMixin.get_initial_state."""
        raise NotImplementedError

    def is_applicable(
        self,
        state: "up.model.State",
        action_or_action_instance: Union["up.model.Action", "up.plans.ActionInstance"],
        parameters: Optional[
            Union["up.model.Expression", Sequence["up.model.Expression"]]
        ] = None,
    ) -> bool:
        """
        Returns `True` if the given `event conditions` are evaluated as `True` in the given `state`;
        returns `False` otherwise.

        :param state: the `state` where the `event conditions` are checked.
        :param event: the `event` whose `conditions` are checked.
        :return: Whether or not the `event` is applicable in the given `state`.
        """
        act, params = self._handle_action_or_action_instance_polymorphism(
            action_or_action_instance,
            parameters,
            "is_applicable",
        )
        return self._is_applicable(state, act, params)

    def _is_applicable(
        self,
        state: "up.model.State",
        action: "up.model.Action",
        parameters: Tuple["up.model.FNode", ...],
    ) -> bool:
        try:
            is_applicable = (
                len(
                    self.get_unsatisfied_conditions(
                        state, action, parameters, early_termination=True
                    )
                )
                == 0
            )
        except UPInvalidActionError:
            is_applicable = False
        return is_applicable

    def get_unsatisfied_conditions(
        self,
        state: "up.model.State",
        action_or_action_instance: Union["up.model.Action", "up.plans.ActionInstance"],
        parameters: Optional[
            Union["up.model.Expression", Sequence["up.model.Expression"]]
        ] = None,
        early_termination: bool = False,
    ) -> List["up.model.FNode"]:
        """
        Returns the list of `unsatisfied event conditions` evaluated in the given `state`.
        If the flag `early_termination` is set, the method ends and returns at the first `unsatisfied condition`.

        :param state: The `State` in which the `event conditions` are evaluated.
        :param early_termination: Flag deciding if the method ends and returns at the first `unsatisfied condition`.
        :return: The list of all the `event conditions` that evaluated to `False` or the list containing the first
            `condition` evaluated to `False` if the flag `early_termination` is set.
        """
        act, params = self._handle_action_or_action_instance_polymorphism(
            action_or_action_instance,
            parameters,
            "get_unsatisfied_conditions",
        )
        return self._get_unsatisfied_conditions(
            state, act, params, early_termination=early_termination
        )

    def _get_unsatisfied_conditions(
        self,
        state: "up.model.State",
        action: "up.model.Action",
        parameters: Tuple["up.model.FNode", ...],
        early_termination: bool = False,
    ) -> List["up.model.FNode"]:
        """
        Method called by the up.engines.mixins.sequential_simulator.SequentialSimulatorMixin.get_unsatisfied_conditions.
        """
        raise NotImplementedError

    def apply(
        self,
        state: "up.model.State",
        action_or_action_instance: Union["up.model.Action", "up.plans.ActionInstance"],
        parameters: Optional[
            Union["up.model.Expression", Sequence["up.model.Expression"]]
        ] = None,
    ) -> Optional["up.model.State"]:
        """
        Returns `None` if the `event` is not applicable in the given `state`, otherwise returns a new `State`,
        which is a copy of the given `state` where the `applicable effects` of the `event` are applied; therefore
        some `fluent values` are updated.

        :param state: the `state` where the event formulas are calculated.
        :param event: the `event` that has the information about the `conditions` to check and the `effects` to apply.
        :return: `None` if the `event` is not applicable in the given `state`, a new `State` with some updated `values`
            if the `event` is applicable.
        """
        act, params = self._handle_action_or_action_instance_polymorphism(
            action_or_action_instance,
            parameters,
            "apply",
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

    def apply_unsafe(
        self,
        state: "up.model.State",
        action_or_action_instance: Union["up.model.Action", "up.plans.ActionInstance"],
        parameters: Optional[
            Union["up.model.Expression", Sequence["up.model.Expression"]]
        ] = None,
    ) -> "up.model.State":
        """
        Returns a new `State`, which is a copy of the given `state` but the applicable `effects` of the
        `event` are applied; therefore some `fluent` values are updated.
        IMPORTANT NOTE: Assumes that `self.is_applicable(state, event)` returns `True`.

        :param state: the `state` where the `event formulas` are evaluated.
        :param event: the `event` that has the information about the `effects` to apply.
        :return: A new `State` with some updated values.
        """
        act, params = self._handle_action_or_action_instance_polymorphism(
            action_or_action_instance,
            parameters,
            "apply_unsafe",
        )
        return self._apply_unsafe(state, act, params)

    def _apply_unsafe(
        self,
        state: "up.model.State",
        action: "up.model.Action",
        parameters: Tuple["up.model.FNode", ...],
    ) -> "up.model.State":
        """
        Method called by the up.engines.mixins.sequential_simulator.SequentialSimulatorMixin.apply_unsafe.
        """
        raise NotImplementedError

    def get_applicable_actions(
        self, state: "up.model.State"
    ) -> Iterator[Tuple["up.model.Action", Tuple["up.model.FNode", ...]]]:
        """
        Returns a view over all the `events` that are applicable in the given `State`;
        an `Event` is considered applicable in a given `State`, when all the `Event condition`
        simplify as `True` when evaluated in the `State`.

        :param state: the `state` where the formulas are evaluated.
        :return: an `Iterator` of applicable `Events`.
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
    def is_simulator():
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
        return len(self.get_unsatisfied_goals(state, early_termination=True)) == 0

    def get_unsatisfied_goals(
        self, state: "up.model.State", early_termination: bool = False
    ) -> List["up.model.FNode"]:
        """
        Returns the list of `unsatisfied goals` evaluated in the given `state`.
        If the flag `early_termination` is set, the method ends and returns at the first `unsatisfied goal`.

        :param state: The `State` in which the `problem goals` are evaluated.
        :param early_termination: Flag deciding if the method ends and returns at the first `unsatisfied goal`.
        :return: The list of all the `goals` that evaluated to `False` or the list containing the first `goal` evaluated to `False` if the flag `early_termination` is set.
        """
        return self._get_unsatisfied_goals(state, early_termination)

    def _get_unsatisfied_goals(
        self, state: "up.model.State", early_termination: bool = False
    ) -> List["up.model.FNode"]:
        """
        Method called by the up.engines.mixins.sequential_simulator.SequentialSimulatorMixin.get_unsatisfied_goals.
        """
        raise NotImplementedError

    def evaluate_quality_metric(
        self,
        state: "up.model.State",
        quality_metric: Optional["up.model.PlanQualityMetric"] = None,
    ) -> "up.model.FNode":
        """TODO"""
        if quality_metric is None:
            try:
                qm = self._problem.quality_metrics  # type: ignore[attr-defined]
            except AttributeError:
                raise UPUsageError(
                    "Can't establish a default metric if the given problem class does not have a quality_metrics field."
                )
            if len(qm) == 0:
                raise UPUsageError(
                    "Can't establish a default metric if the given problem does not have any quality_metric."
                )
            elif len(qm) > 1:
                raise NotImplementedError(
                    "UP does not support multiple quality metrics."
                )
            else:
                assert len(qm) == 1
            quality_metric = qm[0]
        return self._evaluate_quality_metric(state, quality_metric)

    def _evaluate_quality_metric(
        self, state: "up.model.State", quality_metric: "up.model.PlanQualityMetric"
    ) -> "up.model.FNode":
        """TODO"""
        raise NotImplementedError
