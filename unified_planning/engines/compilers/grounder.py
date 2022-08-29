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
from unified_planning.model import Problem, ProblemKind, Action, Type, Expression, FNode
from unified_planning.model.types import domain_size, domain_item
from unified_planning.model.walkers import Substituter, Simplifier
from unified_planning.engines.compilers.utils import (
    lift_action_instance,
    create_action_with_given_subs,
)
from typing import Dict, List, Optional, Tuple, Iterator
from itertools import product
from functools import partial


class GroundingSupport:
    """
    TODO check
    This class gives the capability of grounding a :class:`~unified_planning.model.Problem` by taking
    it at construction time.

    It offers the capability both of grounding a whole problem, like the :class:`~unified_planning.engines.compilers.Grounder`
    in the :func:`~unified_planning.engines.compilers.Grounder.compile` method (with the :func:`~unified_planning.engines.compilers.GroundingSupport.ground_problem`
    method) or offers the capability of grounding a single Action of the Problem given the grounding parameters
    (with the :func:`~unified_planning.engines.compilers.GroundingSupport.ground_action` method).

    This class also caches the grounded actions so it avoids duplication.
    """

    def __init__(
        self,
        problem: Problem,
        grounding_actions_map: Optional[Dict[Action, List[Tuple[FNode, ...]]]] = None,
    ):
        """
        Creates an instance of the GroundingSupport.

        :param problem: The `Problem` to ground.
        :param grounding_actions_map: Optionally, a map from `Action` to a List of Tuples of expressions.
            When this map is set, it represents the groundings that this class does.
            So, for every key in the map, the `Action` is grounded with every `tuple of parameters` in the mapped value.
            For example, if the map is `{a: [(o1, o2), (o2, o3)], b: [(o3), (o4)]}`, the resulting grounded actions will be:
            - `a (o1, o2)`
            - `a (o2, o3)`
            - `b (o3)`
            - `b (o4)`
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
        env = problem.env
        self._substituter = Substituter(env)
        self._simplifier = Simplifier(env, problem)

    def ground_action(
        self, action: Action, parameters: Tuple[FNode, ...] = tuple()
    ) -> Optional[Action]:
        """
        TODO check
        Grounds the given `action` with the given `parameters`.
        An `Action` is grounded when it has no :func:`parameters <unified_planning.model.Action.parameters>`.

        The returned `Action` is cached, so if the same method is called twice with the same function parameters,
        the same object is returned, and the same object will be returned in the total problem grounding, so
        if the resulting `Action` or :class:`~unified_planning.model.Problem` are modified, all the copies
        returned by this class will be modified.

        :param action: The `Action` that must be grounded with the given `parameters`.
        :param parameters: The tuple of expressions used to ground the given `action`.
        :return: The `action` grounded with the given `parameters` or `None` if the grounded
            action does not have `effects` or the `action conditions` can be easily evaluated as a
            contradiction.
        """
        assert len(action.parameters) == len(
            parameters
        ), "The number of given parameters for the grounding is different from the action's parameters"
        key = (action, tuple(parameters))
        if key in self._grounded_actions:  # The action is already created
            return self._grounded_actions[key]
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
                    self._problem, action, self._simplifier, self._substituter, subs
                )
            self._grounded_actions[key] = new_action
            return new_action

    def get_grounded_actions(
        self,
    ) -> Iterator[Tuple[Action, Tuple[FNode, ...], Optional[Action]]]:
        """
        TODO
        """
        for old_action in self._problem.actions:
            for grounded_params in self.get_possible_parameters(old_action):
                assert isinstance(grounded_params, tuple)
                new_action = self.ground_action(old_action, grounded_params)
                yield (old_action, grounded_params, new_action)

    def get_possible_parameters(self, action: Action) -> Iterator[Tuple[FNode, ...]]:
        """
        TODO
        """
        # if the action does not have parameters, it does not need to be grounded.
        if len(action.parameters) == 0:
            if (
                self._grounding_actions_map is None
                or self._grounding_actions_map.get(action, None) is not None
            ):
                return iter([tuple()])
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
                grounded_params_iter: Iterator[Tuple[FNode, ...]] = product(*items_list)
            else:
                # The grounding_actions_map is not None, therefore it must be used to ground
                grounded_params_iter = iter(self._grounding_actions_map.get(action, []))
            return grounded_params_iter


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
        supported_kind.set_time("TIMED_EFFECT")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
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
        gs = GroundingSupport(problem, self._grounding_actions_map)
        trace_back_map: Dict[Action, Tuple[Action, List[FNode]]] = {}

        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_actions()
        for old_action, parameters, new_action in gs.get_grounded_actions():
            if new_action is not None:
                new_problem.add_action(new_action)
                trace_back_map[new_action] = (old_action, list(parameters))

        return CompilerResult(
            new_problem,
            partial(lift_action_instance, map=trace_back_map),
            self.name,
        )
