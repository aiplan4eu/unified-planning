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

import unified_planning as up
import unified_planning.environment
import unified_planning.engines as engines
import unified_planning.engines.compilers
from unified_planning.plans import ActionInstance
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    Problem,
    ProblemKind,
    Action,
    Type,
    Expression,
    FNode,
    MinimizeActionCosts,
    Parameter,
)
from unified_planning.model.types import domain_size, domain_item
from unified_planning.model.walkers import Simplifier
from unified_planning.engines.compilers.utils import (
    lift_action_instance,
    create_action_with_given_subs,
)
from unified_planning.exceptions import UPUsageError
from typing import Dict, Iterable, List, Optional, Tuple, Iterator, cast
from itertools import product
from functools import partial


class GrounderHelper:
    """
    This class gives the capability of grounding a :class:`~unified_planning.model.Problem` by taking
    it at construction time.

    It offers the capability both of grounding the whole `Problem`, with the :func:`~unified_planning.engines.compilers.GrounderHelper.get_grounded_actions`
    function or offers the capability of grounding a single `Action` of the `Problem`, given the grounding parameters
    (with the :func:`~unified_planning.engines.compilers.GrounderHelper.ground_action` function).

    Important NOTE: This class caches the grounded actions created to avoid duplication; 2 different calls
    with the same parameters will return the same object!
    """

    def __init__(
        self,
        problem: Problem,
        grounding_actions_map: Optional[Dict[Action, List[Tuple[FNode, ...]]]] = None,
    ):
        """
        Creates an instance of the GrounderHelper.

        :param problem: The `Problem` to ground.
        :param grounding_actions_map: Optionally, a map from `Action` to a List of Tuples of expressions.
            When this map is set, it represents the groundings that this class does.
            So, for every key in the map, the `Action` is grounded with every `tuple of parameters` in the mapped value.
            For example, if the map is `{a: [(o1, o2), (o2, o3)], b: [(o3), (o4)]}`, the resulting grounded actions will be:
            * `a (o1, o2)`
            * `a (o2, o3)`
            * `b (o3)`
            * `b (o4)`
            If this map is `None`, the `unified_planning` grounding algorithm is applied.
        """
        assert isinstance(problem, Problem)
        self._problem = problem
        self._grounding_actions_map = grounding_actions_map
        # grounded_actions is a map from an Action of the original problem and it's parameters
        # to the grounded instance of the Action with the given parameters.
        # When the grounded instance of the Action is None, it means that the resulting grounding
        # of that action is a meaningless Action.
        # An Action is meaningless when:
        # - it has no effects
        # - his conditions create a contradiction
        # - the action has conflicting effects
        self._grounded_actions: Dict[
            Tuple[Action, Tuple[FNode, ...]], Optional[Action]
        ] = {}
        env = problem.environment
        self._simplifier = Simplifier(env, problem)

    @property
    def simplifier(self) -> Simplifier:
        return self._simplifier

    def ground_action(
        self, action: Action, parameters: Tuple[FNode, ...] = tuple()
    ) -> Optional[Action]:
        """
        Grounds the given action with the given parameters.
        An ``Action`` is grounded when it has no :func:`parameters <unified_planning.model.Action.parameters>`.

        The returned ``Action`` is cached, so if the same method is called twice with the same function parameters,
        the same object is returned, and the same object will be returned in the total problem grounding, so
        if the resulting ``Action`` or :class:`~unified_planning.model.Problem` are modified, all the copies
        returned by this class will be modified.

        :param action: The ``Action`` that must be grounded with the given ``parameters``.
        :param parameters: The tuple of expressions used to ground the given ``action``.
        :return: The ``action`` grounded with the given ``parameters`` or ``None`` if the grounded
            action does not have ``effects`` or the ``action conditions`` can be easily evaluated as a
            contradiction.
        """
        assert len(action.parameters) == len(
            parameters
        ), "The number of given parameters for the grounding is different from the action's parameters"
        key = (action, tuple(parameters))
        value = self._grounded_actions.get(key, 0)
        if value != 0:  # The action is already created
            assert isinstance(value, up.model.InstantaneousAction) or value is None
            return value
        else:
            # if the action does not have parameters, it does not need to be grounded.
            if len(action.parameters) == 0:
                if (
                    self._grounding_actions_map is None
                    or self._grounding_actions_map.get(action, None) is not None
                ):
                    new_action = action.clone()
                else:
                    new_action = None
            else:
                subs: Dict[Expression, Expression] = dict(
                    zip(action.parameters, list(parameters))
                )
                new_action = create_action_with_given_subs(
                    self._problem, action, self._simplifier, subs
                )
            self._grounded_actions[key] = new_action
            return new_action

    def get_grounded_actions(
        self,
    ) -> Iterator[Tuple[Action, Tuple[FNode, ...], Optional[Action]]]:
        """
        Returns an iterator over all the possible grounded actions of the problem given at construction time.
        Every resulting tuple is made of 3 elements: ``original_action``, ``parameters``, ``grounded_action`` where:

        * The ``original_action`` is the `Action` of the ``Problem`` that is grounded.
        * The ``parameters`` is the `Tuple of expressions` used to ground the ``original_action``.
        * The ``grounded_action`` is the `Action` created by grounding the ``original_action`` with the given ``parameters``;
        the ``grounded_action`` can be ``None`` if the grounding of the ``original_action`` with the given parameters
        creates an invalid or meaningless `Action` (invalid if it has conflicting `Effects`,
        meaningless if it has no `effects` or contradicting `conditions`).
        """
        for old_action in self._problem.actions:
            for grounded_params in self.get_possible_parameters(old_action):
                assert isinstance(grounded_params, tuple)
                new_action = self.ground_action(old_action, grounded_params)
                yield (old_action, grounded_params, new_action)

    def get_possible_parameters(self, action: Action) -> Iterator[Tuple[FNode, ...]]:
        """
        Takes in input an `Action` and returns the iterator over all the possible parameters compatible with the given
        action signature; this is computed in the domain of the :class:`~unified_planning.model.Problem` given at construction time.

        :param action: The `Action` providing the signature to get all the possible grounding parameters in the
            `Problem` 's domain.
        :return: An `Iterator` over all the possible `Tuple of expressions` that are compatible with the given `Action`.
        """
        # if the action does not have parameters, it does not need to be grounded.
        if len(action.parameters) == 0:
            if (
                self._grounding_actions_map is None
                or self._grounding_actions_map.get(action, None) is not None
            ):
                res: Iterator[Tuple[FNode, ...]] = iter([tuple()])
            else:
                res = iter([])
        else:
            # contains the type of every parameter of the action
            type_list: List[Type] = [param.type for param in action.parameters]
            if self._grounding_actions_map is None:
                # a list containing the list of object in the self._problem of the given type.
                # So, if the self._problem has 2 Locations l1 and l2, and 2 Robots r1 and r2, and
                # the action move_to takes as parameters a Robot and a Location,
                # the variable state at this point will be the following:
                # type_list = [Robot, Location]
                # objects_list = [[r1, r2], [l1, l2]]
                # the product of *objects_list will be:
                # [(r1, l1), (r1, l2), (r2, l1), (r2,l2)]
                ground_size = 1
                domain_sizes = []
                for t in type_list:
                    ds = domain_size(self._problem, t)
                    domain_sizes.append(ds)
                    ground_size *= ds
                items_list: List[List[FNode]] = []
                for size, type in zip(domain_sizes, type_list):
                    items_list.append(
                        [domain_item(self._problem, type, j) for j in range(size)]
                    )
                res = product(*items_list)
            else:
                # The grounding_actions_map is not None, therefore it must be used to ground
                res = iter(self._grounding_actions_map.get(action, []))
        return res


class Grounder(engines.engine.Engine, CompilerMixin):
    """
    Grounder class: the `Grounder` takes a :class:`~unified_planning.model.Problem` where the :class:`Actions <unified_planning.model.Action>`
    have :func:`Parameters <unified_planning.model.Action.parameters>` (meaning the `Actions` are lifted) and, through the :func:`~unified_planning.engines.mixins.CompilerMixin.compile`
    method, returns a `Problem` where every `Action` does not have `Parameters` (meaning the `Actions` are grounded).

    When an `Action` grounding creates an `Action` without :func:`Effects <unified_planning.model.InstantaneousAction.effects>`, or an `Action` with impossible
    :func:`conditions <unified_planning.model.InstantaneousAction.preconditions>`, the `Action` is discarded and not added to the final `Problem`.

    At construction time, the Grounder class can optionally take a map from `Action` to `List[Tuple[FNode, ...]]`. If this map is not None,
    it will be used for grounding instead of the implemented algorithm; the use of this parameter is mainly created to easily support
    the integration of external grounders inside the library. To see a practical example, checkout the :class:`~unified_planning.engines.compilers.TarskiGrounder` `_compile`
    implementation.

    This `Compiler` supports only the the `GROUNDING` :class:`~unified_planning.engines.CompilationKind`.
    """

    def __init__(
        self,
        grounding_actions_map: Optional[Dict[Action, List[Tuple[FNode, ...]]]] = None,
    ):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.GROUNDING)
        self._grounding_actions_map = grounding_actions_map

    @property
    def name(self):
        return "grounder"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_numbers("CONTINUOUS_NUMBERS")
        supported_kind.set_numbers("DISCRETE_NUMBERS")
        supported_kind.set_numbers("BOUNDED_TYPES")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_fluents_type("NUMERIC_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITY")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECT")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATION")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATION")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_constraints_kind("TRAJECTORY_CONSTRAINTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= Grounder.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.GROUNDING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        return ProblemKind(problem_kind.features)

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """
        Takes an instance of a :class:`~unified_planning.model.Problem` and the `GROUNDING` :class:`~unified_planning.engines.CompilationKind`
        and returns a `CompilerResult` where the problem does not have actions with parameters; so every action is grounded.

        :param problem: The instance of the `Problem` that must be grounded.
        :param compilation_kind: The `CompilationKind` that must be applied on the given problem;
            only `GROUNDING` is supported by this compiler
        :return: The resulting `CompilerResult` data structure.
        """
        assert isinstance(
            problem, Problem
        ), "The given problem is not a class supported by the Grounder"
        grounder_helper = GrounderHelper(problem, self._grounding_actions_map)
        trace_back_map: Dict[Action, Tuple[Action, List[FNode]]] = {}

        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_actions()
        for (
            old_action,
            parameters,
            new_action,
        ) in grounder_helper.get_grounded_actions():
            if new_action is not None:
                new_problem.add_action(new_action)
                trace_back_map[new_action] = (old_action, list(parameters))

        new_problem.clear_quality_metrics()
        for qm in problem.quality_metrics:
            if isinstance(qm, MinimizeActionCosts):
                simplifier = grounder_helper.simplifier
                new_costs: Dict["up.model.Action", "up.model.Expression"] = {}
                for new_action, (old_action, params) in trace_back_map.items():
                    subs = cast(
                        Dict[Expression, Expression],
                        dict(zip(old_action.parameters, params)),
                    )
                    old_cost = qm.get_action_cost(old_action)
                    if old_cost is not None:
                        new_costs[new_action] = simplifier.simplify(
                            old_cost.substitute(subs)
                        )
                new_problem.add_quality_metric(
                    MinimizeActionCosts(new_costs, environment=new_problem.environment)
                )
            else:
                new_problem.add_quality_metric(qm)

        return CompilerResult(
            new_problem,
            partial(lift_action_instance, map=trace_back_map),
            self.name,
        )
