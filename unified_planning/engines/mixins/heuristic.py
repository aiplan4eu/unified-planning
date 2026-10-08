# Copyright 2026 Unified Planning library and its maintainers
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

from abc import ABC, abstractmethod
from enum import Flag, auto
from fractions import Fraction
from typing import Optional, Union
from warnings import warn

import unified_planning as up
from unified_planning.exceptions import UPUsageError


class HeuristicGuarantee(Flag):
    """
    Properties that a ``Heuristic`` engine can guarantee on the values it returns.
    Members can be combined with ``|``, e.g. ``GOAL_AWARE | SAFE``.

    *   | ``ADMISSIBLE``: the value never overestimates the optimal remaining cost.
    *   | ``CONSISTENT``: ``h(s) <= c(s, a) + h(s')`` for every transition from ``s`` to ``s'``.
    *   | ``GOAL_AWARE``: the value is ``0`` on every goal state.
    *   | ``SAFE``: ``None`` is returned only on states from which no goal state is reachable.
    """

    ADMISSIBLE = auto()
    CONSISTENT = auto()
    GOAL_AWARE = auto()
    SAFE = auto()


class HeuristicMixin(ABC):
    """
    HeuristicMixin abstract class.
    This class defines the interface that an :class:`~unified_planning.engines.Engine`
    that is also a `Heuristic` must implement.

    The value estimates the remaining cost to reach the goals of the problem,
    measured with its quality metric, or the number of actions if it has none.

    Important NOTE: The `AbstractProblem` instance is given at the constructor.
    """

    def __init__(
        self, problem: "up.model.AbstractProblem", error_on_failed_checks: bool
    ) -> None:
        """
        :param problem: the `problem` whose goals and metric the heuristic estimates.
        """
        self._problem = problem
        self_class = type(self)
        assert issubclass(self_class, up.engines.engine.Engine), (
            "HeuristicMixin does not implement the up.engines.Engine class"
        )
        assert isinstance(self, up.engines.engine.Engine)
        self._error_on_failed_checks: bool = error_on_failed_checks
        if not self.skip_checks and not self_class.supports(problem.kind):
            msg = f"We cannot establish whether {self.name} is able to handle this problem!"
            if self.error_on_failed_checks:
                raise UPUsageError(msg)
            else:
                warn(msg)

    @staticmethod
    def is_heuristic() -> bool:
        return True

    @staticmethod
    def satisfies(heuristic_guarantee: HeuristicGuarantee) -> bool:
        """
        Implementations should test containment (``heuristic_guarantee in ...``), not
        equality, so that a combination such as ``GOAL_AWARE | SAFE`` is accepted when
        every one of its members is satisfied.
        An engine that also implements other mixins defining ``satisfies`` (e.g.
        ``OneshotPlannerMixin``) must override it and dispatch on the argument type.

        :param heuristic_guarantee: The ``heuristic_guarantee`` that must be satisfied,
            possibly a combination of members.
        :return: ``True`` if the ``HeuristicMixin`` implementation satisfies all the
            given guarantees, ``False`` otherwise.
        """
        # By default only the empty requirement HeuristicGuarantee(0) is satisfied.
        return heuristic_guarantee in HeuristicGuarantee(0)

    def value(self, state: "up.model.State") -> Optional[Union[int, Fraction]]:
        """
        Returns the heuristic value of the given `state`, or `None` if the
        heuristic detects that no goal state is reachable from it.

        The `state` can come from any `SequentialSimulator`: it is only read
        through `state.get_value`, and it is not validated, for performance.

        :param state: the `State` to evaluate.
        :return: the estimated remaining cost, or `None` for a dead end.
        """
        return self._value(state)

    @abstractmethod
    def _value(self, state: "up.model.State") -> Optional[Union[int, Fraction]]:
        """Method called by the HeuristicMixin.value method."""
        raise NotImplementedError
