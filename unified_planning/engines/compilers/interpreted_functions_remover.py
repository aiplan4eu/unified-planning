# Copyright 2021-2023 AIPlan4EU project
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
# copyright info is not up to date as of september 27th 2024
"""This module defines the interpreted functions effects remover class."""

import itertools as it

from collections import OrderedDict, deque
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.model.interpreted_function import InterpretedFunction
from unified_planning.model.timing import EndTiming, StartTiming, TimepointKind
from unified_planning.model.walkers.substituter import Substituter
from unified_planning.model.walkers.operators_extractor import OperatorsExtractor
from unified_planning.model.operators import OperatorKind
from unified_planning.model.expression import Expression, ExpressionManager
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.compilers.utils import updated_minimize_action_costs
from unified_planning.engines.results import CompilerResult
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPConflictingEffectsException,
)
from unified_planning.model import (
    Problem,
    ProblemKind,
    Action,
    InstantaneousAction,
    DurativeAction,
    AbstractProblem,
    FNode,
)
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
    check_and_simplify_preconditions,
    check_and_simplify_conditions,
    replace_action,
)
from unified_planning.utils import powerset
from typing import List, Dict, Tuple, Optional, Iterator
from functools import partial


class InterpretedFunctionsRemover(engines.engine.Engine, CompilerMixin):
    """
    Interpreted functions remover class: this class offers the capability
    to transform a :class:`~unified_planning.model.Problem` with interpreted functions used as conditions`
    into a `Problem` without interpreted functions in action conditions. This capability is offered by the :meth:`~unified_planning.engines.compilers.InterpretedFunctionsRemover.compile`
    method, that returns a :class:`~unified_planning.engines.CompilerResult` in which the :meth:`problem <unified_planning.engines.CompilerResult.problem>` field
    is the compiled Problem.

    This is done by changing every evaluation of an expression that contains an interpreted function to true.

    This `Compiler` supports only the the `INTERPRETED_FUNCTIONS_REMOVER` :class:`~unified_planning.engines.CompilationKind`.
    """

    def __init__(self, interpreted_functions_values=None):
        engines.engine.Engine.__init__(self)
        self.operators_extractor: up.model.walkers.OperatorsExtractor = (
            up.model.walkers.OperatorsExtractor()
        )
        self.interpreted_functions_extractor: up.model.walkers.InterpretedFunctionsExtractor = (
            up.model.walkers.InterpretedFunctionsExtractor()
        )

        self._interpreted_functions_values = interpreted_functions_values

        CompilerMixin.__init__(self, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING)

    @property
    def name(self):
        return "ifrm"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("REAL_ACTION_PARAMETERS")
        supported_kind.set_numbers("BOUNDED_TYPES")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_fluents_type("INT_FLUENTS")
        supported_kind.set_fluents_type("REAL_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind(
            "INTERPRETED_FUNCTIONS_IN_CONDITIONS"
        )  # added this
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FORALL_EFFECTS")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECTS")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_time("SELF_OVERLAPPING")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("INT_TYPE_DURATIONS")
        supported_kind.set_expression_duration("REAL_TYPE_DURATIONS")
        supported_kind.set_expression_duration(
            "INTERPRETED_FUNCTIONS_IN_DURATIONS"
        )  # added this
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_constraints_kind("STATE_INVARIANTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        # supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        # supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= InterpretedFunctionsRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.INTERPRETED_FUNCTIONS_REMOVING

    def _fix_precondition(self, a):
        # should we check for always true preconditions?
        # simplified_precondition = simplifier.simplify(p)
        # precondition_operators = operators_extractor.get(simplified_precondition)
        # operators_extractor: up.model.walkers.OperatorsExtractor = (
        #    up.model.walkers.OperatorsExtractor()
        # )
        templist = []
        if a.is_and():
            for sub in a.args:
                templist.append(sub)
        else:
            templist.append(a)
        return templist

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        assert isinstance(problem_kind, ProblemKind)
        new_kind = problem_kind.clone()
        if new_kind.has_interpreted_functions_in_conditions():
            new_kind.unset_conditions_kind("INTERPRETED_FUNCTIONS_IN_CONDITIONS")
        if new_kind.has_interpreted_functions_in_durations():
            new_kind.unset_expression_duration("INTERPRETED_FUNCTIONS_IN_DURATIONS")
            new_kind.set_expression_duration("INT_TYPE_DURATIONS")

        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
        #        IF_values: Optional[Dict[FNode, FNode]] = None # vedi grounder
    ) -> CompilerResult:
        """
        :param problem: The instance of the :class:`~unified_planning.model.Problem` that must be compiled.
        :param compilation_kind: The :class:`~unified_planning.engines.CompilationKind` that must be applied on the given problem;
            only :class:`~unified_planning.engines.CompilationKind.INTERPRETED_FUNCTIONS_REMOVER` is supported by this compiler
        :return: The resulting :class:`~unified_planning.engines.results.CompilerResult` data structure.
        :raises: :exc:`~unified_planning.exceptions.UPProblemDefinitionError` when the :meth:`condition<unified_planning.model.Effect.condition>` of an
            :class:`~unified_planning.model.Effect` can't be removed without changing the :class:`~unified_planning.model.Problem` semantic.
        """
        assert isinstance(problem, Problem)
        env = problem.environment
        simplifier = env.simplifier
        if self._interpreted_functions_values is None:
            self._interpreted_functions_values = OrderedDict()

        new_to_old: Dict[Action, Optional[Action]] = {}
        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_actions()
        better_knowledge = self.elaborate_known_IFs(self._interpreted_functions_values)
        combined_knowledge = self.knowledge_combinations(better_knowledge)

        for a in problem.actions:
            print(
                "---------------------------------------------------------------------"
            )
            print("now working on:")
            print(a.name)
            print(
                "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv"
            )
            if isinstance(a, InstantaneousAction):
                interpreted_functions_queue = deque()
                no_IF_action_base = a.clone()
                no_IF_action_base.clear_preconditions()
                no_IF_action_preconditions_list = list()
                fixed_preconditions = []
                for p in a.preconditions:
                    templist = self._fix_precondition(p)
                    fixed_preconditions.extend(templist)
                for p in fixed_preconditions:
                    IFs = self.interpreted_functions_extractor.get(p)
                    if len(IFs) == 0:
                        no_IF_action_base.add_precondition(p)

                all_combinations_for_this_action = OrderedDict()

                all_ifs_in_instantaneous_action: list = list()
                all_ifs_in_instantaneous_action.clear()
                for p in fixed_preconditions:  # for each precondition
                    IFs = self.interpreted_functions_extractor.get(p)
                    if len(IFs) != 0:  # get all the IFs in the precondition

                        for f in IFs:
                            print(f)
                            if f not in all_ifs_in_instantaneous_action:
                                # and append them in the key list if not already there
                                all_ifs_in_instantaneous_action.append(f)
                                interpreted_functions_queue.append(f)
                # alternative implementation -----------------------------------------------------------------
                temp_a = a.clone()
                action_cases_list = list()
                action_cases_list.append(temp_a)
                while len(interpreted_functions_queue) > 0:

                    print("this action has IFs")

                    print("we have some IFs")
                    print(interpreted_functions_queue)
                    print("pop from the queue:")
                    IF_we_want_to_test = interpreted_functions_queue.pop()
                    print(IF_we_want_to_test)
                    print("do we know anything about this one?")
                    print("its key is")
                    print(IF_we_want_to_test.interpreted_function())
                    if (
                        IF_we_want_to_test.interpreted_function()
                        in better_knowledge.keys()
                    ):
                        print("yep:")
                        for partially_elaborated_action in action_cases_list:
                            for known_function in better_knowledge[
                                IF_we_want_to_test.interpreted_function()
                            ]:
                                temp_action = partially_elaborated_action.clone()
                                substituter_instantaneous_action: up.model.walkers.Substituter = up.model.walkers.Substituter(
                                    temp_action.environment
                                )
                                # add this case as a new action to the list
                                # print (known_function)
                                # print ("is")
                                # print (better_knowledge[IF_we_want_to_test.interpreted_function()][known_function])
                                substitution_dict = dict()
                                substitution_dict[known_function] = better_knowledge[
                                    IF_we_want_to_test.interpreted_function()
                                ][known_function]
                                print("substitution_dict")
                                print(substitution_dict)
                                print("the found function args are:")
                                print(IF_we_want_to_test.args)
                                print("we have to make them equal to:")
                                print(known_function.args)
                                # add constraint precondition
                                # keep track of all the known values
                                # add to new temp action list
                            # add generic case for IF_we_want_to_test
                        # now, outside the for loop on the actions list
                        # delete old action list, new action list <- temp action list
                    else:
                        print("nope, we found")
                        print(IF_we_want_to_test.interpreted_function())
                        print("but better knowledge keys is")
                        print(better_knowledge.keys())
                # end of alternative implementation --------------------------------------------------------

                if len(all_ifs_in_instantaneous_action) != 0:
                    ifs_as_keys_instantaneous: list = list()
                    ifs_as_keys_instantaneous.clear()
                    for f in all_ifs_in_instantaneous_action:
                        ifs_as_keys_instantaneous.append(f.interpreted_function())

                    all_combinations_for_this_action = self.knowledge_combinations(
                        better_knowledge, ifs_as_keys_instantaneous
                    )

                    for kfc in all_combinations_for_this_action:
                        # for each possible combination (known function combinations)
                        new_action = a.clone()
                        new_action.name = get_fresh_name(new_problem, a.name)

                        new_condition = None
                        new_precondition_list = list()

                        for kf in kfc:

                            substituter_instantaneous_action: up.model.walkers.Substituter = up.model.walkers.Substituter(
                                new_action.environment
                            )

                            subdict = dict()
                            for fun in all_ifs_in_instantaneous_action:

                                if (
                                    fun.interpreted_function()
                                    == kf.interpreted_function()
                                ):
                                    subdict[fun] = self._interpreted_functions_values[
                                        kf
                                    ]

                            if len(subdict) == 0:
                                print(
                                    "sub dict is empty ;-;\nif you got here it means there is a bug in the code"
                                )

                            preconditions_to_substitute_list = new_action.preconditions
                            new_action.clear_preconditions()
                            for pre in preconditions_to_substitute_list:

                                new_precondition = (
                                    substituter_instantaneous_action.substitute(
                                        pre, subdict
                                    )
                                )
                                new_action.add_precondition(new_precondition)

                            argumentcounter = 0
                            while argumentcounter < len(kf.args):
                                for aif in all_ifs_in_instantaneous_action:
                                    if (
                                        aif.interpreted_function()
                                        == kf.interpreted_function()
                                    ):
                                        new_precondition_list.append(
                                            [
                                                aif.args[argumentcounter],
                                                kf.args[argumentcounter],
                                            ]
                                        )
                                        if new_condition is None:
                                            if aif.args[
                                                argumentcounter
                                            ].type.is_bool_type():
                                                new_condition = new_action.environment.expression_manager.Iff(
                                                    aif.args[argumentcounter],
                                                    kf.args[argumentcounter],
                                                )
                                            else:
                                                new_condition = new_action.environment.expression_manager.Equals(
                                                    aif.args[argumentcounter],
                                                    kf.args[argumentcounter],
                                                )

                                        else:
                                            if aif.args[
                                                argumentcounter
                                            ].type.is_bool_type():
                                                new_condition = new_action.environment.expression_manager.And(
                                                    new_condition,
                                                    new_action.environment.expression_manager.Iff(
                                                        aif.args[argumentcounter],
                                                        kf.args[argumentcounter],
                                                    ),
                                                )
                                            else:
                                                new_condition = new_action.environment.expression_manager.And(
                                                    new_condition,
                                                    new_action.environment.expression_manager.Equals(
                                                        aif.args[argumentcounter],
                                                        kf.args[argumentcounter],
                                                    ),
                                                )

                                argumentcounter = argumentcounter + 1
                            # new_action.add_precondition(new_condition)
                            # base_not_precondition = (
                            #    no_IF_action_base.environment.expression_manager.Not(
                            #        new_condition
                            #    )
                            # )
                            # no_IF_action_base.add_precondition(base_not_precondition)

                            no_IF_action_preconditions_list.append(
                                new_precondition_list
                            )
                        new_action.add_precondition(new_condition)
                        base_not_precondition = (
                            no_IF_action_base.environment.expression_manager.Not(
                                new_condition
                            )
                        )
                        no_IF_action_base.add_precondition(base_not_precondition)
                        new_to_old[new_action] = a
                        new_problem.add_action(new_action)
                    no_IF_action_base.name = get_fresh_name(new_problem, a.name)
                    new_to_old[no_IF_action_base] = a
                    new_problem.add_action(no_IF_action_base)
                else:
                    new_to_old[a] = a
                    new_problem.add_action(a)

            elif isinstance(a, DurativeAction):
                # print ("new action ---------------------------------------------------------------------------------")
                no_IF_action = a.clone()
                minduration: FNode | int = 1
                maxduration: FNode | int = 1000000
                IF_in_durations = list()
                IF_in_start_conditions = list()
                IF_in_end_conditions = list()
                IF_keys_in_durations = list()
                IF_keys_in_start_conditions = list()
                IF_keys_in_end_conditions = list()

                actions_start_conditions: list = list()
                # check for ifs in lower duration, add them to if in durations
                if not (
                    OperatorKind.INTERPRETED_FUNCTION_EXP
                    in self.operators_extractor.get(a.duration.lower)
                ):
                    minduration = (
                        a.duration.lower
                    )  # this is the min duration for unknown values
                else:
                    IFs = self.interpreted_functions_extractor.get(a.duration.lower)
                    if len(IFs) != 0:
                        for f in IFs:
                            if f not in IF_in_durations:
                                IF_in_durations.append(f)
                            if f.interpreted_function() not in IF_keys_in_durations:
                                IF_keys_in_durations.append(f.interpreted_function())
                IFs = None
                # check for ifs in upper duration, add them to if in durations
                if not (
                    OperatorKind.INTERPRETED_FUNCTION_EXP
                    in self.operators_extractor.get(a.duration.upper)
                ):
                    maxduration = (
                        a.duration.upper
                    )  # this is the max duration for unknown values
                else:
                    IFs = self.interpreted_functions_extractor.get(a.duration.upper)
                    if len(IFs) != 0:
                        for f in IFs:
                            if f not in IF_in_durations:
                                IF_in_durations.append(f)
                            if f.interpreted_function() not in IF_keys_in_durations:
                                IF_keys_in_durations.append(f.interpreted_function())

                no_IF_action.set_closed_duration_interval(minduration, maxduration)

                no_IF_action.clear_conditions()
                fixed_conditions: list = []
                fixed_conditions_i: list = []
                map_if_to_time: dict = dict()
                for ii, cl in a.conditions.items():
                    for c in cl:
                        if ii.lower.is_from_start():
                            IFs = self.interpreted_functions_extractor.get(c)
                            if len(IFs) != 0:
                                for f in IFs:
                                    if f not in IF_in_start_conditions:
                                        IF_in_start_conditions.append(f)
                                    if (
                                        f.interpreted_function()
                                        not in IF_keys_in_start_conditions
                                    ):
                                        IF_keys_in_start_conditions.append(
                                            f.interpreted_function()
                                        )
                        elif ii.upper.is_from_end():
                            IFs = self.interpreted_functions_extractor.get(c)
                            if len(IFs) != 0:
                                for f in IFs:
                                    if f not in IF_in_end_conditions:
                                        IF_in_end_conditions.append(f)
                                    if (
                                        f.interpreted_function()
                                        not in IF_keys_in_end_conditions
                                    ):
                                        IF_keys_in_end_conditions.append(
                                            f.interpreted_function()
                                        )
                        else:
                            print(
                                "this should not happen aaaaaaaaaaaaaaaaaaahhhhhhhhhhhh"
                            )
                        #
                        # let's skip using the fixed conditions for now
                        #
                        # templist = self._fix_precondition(c)
                        # for fc in templist:
                        #    fixed_conditions.append(fc)
                        #    fixed_conditions_i.append(ii)

                # print ("action:")
                # print (a)
                # print ("found functions:")
                # print ("IF_in_durations")
                # print (IF_in_durations)
                # print ("IF_in_start_conditions")
                # print (IF_in_start_conditions)
                # print ("IF_in_end_conditions")
                # print (IF_in_end_conditions)
                # print ("found functions keys:")
                # print ("IF_keys_in_durations")
                # print (IF_keys_in_durations)
                # print ("IF_keys_in_start_conditions")
                # print (IF_keys_in_start_conditions)
                # print ("IF_keys_in_end_conditions")
                # print (IF_keys_in_end_conditions)
                # --------------------------------------
                # start elaboration for start conditions
                # --------------------------------------
                IF_to_check_at_start = list()
                IF_keys_to_check_at_start = list()
                for f in IF_in_start_conditions:
                    if f not in IF_to_check_at_start:
                        IF_to_check_at_start.append(f)
                    if f.interpreted_function() not in IF_keys_to_check_at_start:
                        IF_keys_to_check_at_start.append(f.interpreted_function())
                for f in IF_in_durations:
                    if f not in IF_to_check_at_start:
                        IF_to_check_at_start.append(f)
                    if f.interpreted_function() not in IF_keys_to_check_at_start:
                        IF_keys_to_check_at_start.append(f.interpreted_function())

                start_combinations = OrderedDict()

                start_combinations = self.knowledge_combinations(
                    better_knowledge, IF_keys_to_check_at_start
                )

                generic_action_start_condition_list = list()
                for known_function_combination_start in start_combinations:
                    temp_action_start = a.clone()
                    substitution_dict_start: dict = dict()
                    substitution_dict_start.clear()
                    combination_condition = None
                    for known_function_start in known_function_combination_start:
                        for f in IF_to_check_at_start:
                            if (
                                f.interpreted_function()
                                == known_function_start.interpreted_function()
                            ):
                                substitution_dict_start[
                                    f
                                ] = self._interpreted_functions_values[
                                    known_function_start
                                ]
                                argumentcounter = 0
                                while argumentcounter < len(known_function_start.args):
                                    if combination_condition is None:
                                        if (
                                            f.args[argumentcounter]
                                        ).type.is_bool_type():
                                            combination_condition = temp_action_start.environment.expression_manager.Iff(
                                                f.args[argumentcounter],
                                                known_function_start.args[
                                                    argumentcounter
                                                ],
                                            )
                                        else:
                                            combination_condition = temp_action_start.environment.expression_manager.Equals(
                                                f.args[argumentcounter],
                                                known_function_start.args[
                                                    argumentcounter
                                                ],
                                            )
                                    else:
                                        if (
                                            f.args[argumentcounter]
                                        ).type.is_bool_type():
                                            combination_condition = temp_action_start.environment.expression_manager.And(
                                                combination_condition,
                                                temp_action_start.environment.expression_manager.Iff(
                                                    f.args[argumentcounter],
                                                    known_function_start.args[
                                                        argumentcounter
                                                    ],
                                                ),
                                            )
                                        else:
                                            combination_condition = temp_action_start.environment.expression_manager.And(
                                                combination_condition,
                                                temp_action_start.environment.expression_manager.Equals(
                                                    f.args[argumentcounter],
                                                    known_function_start.args[
                                                        argumentcounter
                                                    ],
                                                ),
                                            )
                                    argumentcounter = argumentcounter + 1

                    substituter_durative_action_start: up.model.walkers.Substituter = (
                        up.model.walkers.Substituter(temp_action_start.environment)
                    )
                    new_conditions_list = temp_action_start.conditions
                    temp_action_start.clear_conditions()
                    # conditions substitution stuff
                    for ii, cl in new_conditions_list.items():
                        # ii stands for interval, cl for conditions list
                        for c in cl:
                            if ii.lower.is_from_start():
                                # if it's from start we edit it, if it end we just copy it
                                new_condition = (
                                    substituter_durative_action_start.substitute(
                                        c, substitution_dict_start
                                    )
                                )
                            else:
                                new_condition = c
                            temp_action_start.add_condition(ii, new_condition)
                    # durations substitution stuff
                    new_maxduration = substituter_durative_action_start.substitute(
                        temp_action_start.duration.upper, substitution_dict_start
                    )
                    new_minduration = substituter_durative_action_start.substitute(
                        temp_action_start.duration.lower, substitution_dict_start
                    )
                    temp_action_start.set_closed_duration_interval(
                        new_minduration, new_maxduration
                    )
                    temp_action_start.add_condition(
                        StartTiming(), combination_condition
                    )
                    generic_action_start_condition_list.append(combination_condition)
                    # print ("we finished elaborating this combination, the action is:")
                    # print (temp_action_start)
                    actions_start_conditions.append(temp_action_start)

                start_generic_action = a.clone()
                generic_minduration = 1
                generic_maxduration = 1000000
                if not (
                    OperatorKind.INTERPRETED_FUNCTION_EXP
                    in self.operators_extractor.get(start_generic_action.duration.lower)
                ):
                    generic_minduration = start_generic_action.duration.lower
                if not (
                    OperatorKind.INTERPRETED_FUNCTION_EXP
                    in self.operators_extractor.get(start_generic_action.duration.upper)
                ):
                    generic_maxduration = start_generic_action.duration.upper
                start_generic_action.set_closed_duration_interval(
                    generic_minduration, generic_maxduration
                )
                new_generic_conditions_list = start_generic_action.conditions
                start_generic_action.clear_conditions()
                for ii, cl in new_generic_conditions_list.items():
                    for c in cl:
                        if ii.lower.is_from_start():
                            # if it's start
                            if not (
                                OperatorKind.INTERPRETED_FUNCTION_EXP
                                in self.operators_extractor.get(c)
                            ):
                                # if it has no IF add it
                                start_generic_action.add_condition(ii, c)
                            # if it has ifs ignore it
                        else:
                            # if it's not from start (so it should be at end), just add it
                            start_generic_action.add_condition(ii, c)

                for (
                    known_values_exclusion_conditions
                ) in generic_action_start_condition_list:
                    start_not_condition = (
                        start_generic_action.environment.expression_manager.Not(
                            known_values_exclusion_conditions
                        )
                    )
                    start_generic_action.add_condition(
                        StartTiming(), start_not_condition
                    )
                # print ("generic action compiled:")
                # print (start_generic_action)
                actions_start_conditions.append(start_generic_action)

                # ------------------------------------
                # end elaboration for start conditions
                # ------------------------------------
                # print("checkpoint! We are about to go to end conditions compilation")
                # print("currently we have some actions in actions_start_conditions")
                # print(len(actions_start_conditions))
                # print(actions_start_conditions)

                # ------------------------------------
                # start elaboration for end conditions
                # ------------------------------------

                IF_to_check_at_end = list()
                IF_keys_to_check_at_end = list()
                for f in IF_in_end_conditions:
                    if f not in IF_to_check_at_end:
                        IF_to_check_at_end.append(f)
                    if f.interpreted_function() not in IF_keys_to_check_at_end:
                        IF_keys_to_check_at_end.append(f.interpreted_function())

                end_combinations = OrderedDict()

                end_combinations = self.knowledge_combinations(
                    better_knowledge, IF_keys_to_check_at_end
                )
                # print("end_combinations")
                # print(end_combinations)
                all_actions_compiled = list()
                for sa in actions_start_conditions:
                    # print ("now working on action sa:")
                    # print (sa)
                    generic_action_end_condition_list: list = list()
                    generic_action_end_condition_list.clear()
                    for known_function_combination_end in end_combinations:
                        # print ("known_function_combination_end")
                        # print (known_function_combination_end)
                        temp_action_end = sa.clone()
                        substitution_dict_end: dict = dict()
                        substitution_dict_end.clear()
                        combination_condition = None
                        for known_function_end in known_function_combination_end:
                            # print ("known_function_end")
                            # print (known_function_end)
                            for f in IF_to_check_at_end:
                                # print ("f found in end ifs")
                                # print (f)
                                if (
                                    f.interpreted_function()
                                    == known_function_end.interpreted_function()
                                ):
                                    substitution_dict_end[
                                        f
                                    ] = self._interpreted_functions_values[
                                        known_function_end
                                    ]
                                    # print ("substitution dict")
                                    # print (substitution_dict_end)
                                    argumentcounter = 0
                                    while argumentcounter < len(
                                        known_function_end.args
                                    ):
                                        if combination_condition is None:
                                            if (
                                                f.args[argumentcounter]
                                            ).type.is_bool_type():
                                                combination_condition = temp_action_end.environment.expression_manager.Iff(
                                                    f.args[argumentcounter],
                                                    known_function_end.args[
                                                        argumentcounter
                                                    ],
                                                )
                                            else:
                                                combination_condition = temp_action_end.environment.expression_manager.Equals(
                                                    f.args[argumentcounter],
                                                    known_function_end.args[
                                                        argumentcounter
                                                    ],
                                                )
                                        else:
                                            if (
                                                f.args[argumentcounter]
                                            ).type.is_bool_type():
                                                combination_condition = temp_action_end.environment.expression_manager.And(
                                                    combination_condition,
                                                    temp_action_end.environment.expression_manager.Iff(
                                                        f.args[argumentcounter],
                                                        known_function_end.args[
                                                            argumentcounter
                                                        ],
                                                    ),
                                                )
                                            else:
                                                combination_condition = temp_action_end.environment.expression_manager.And(
                                                    combination_condition,
                                                    temp_action_end.environment.expression_manager.Equals(
                                                        f.args[argumentcounter],
                                                        known_function_end.args[
                                                            argumentcounter
                                                        ],
                                                    ),
                                                )
                                        argumentcounter = argumentcounter + 1
                        substituter_durative_action_end: up.model.walkers.Substituter = up.model.walkers.Substituter(
                            temp_action_end.environment
                        )
                        new_conditions_list = temp_action_end.conditions
                        temp_action_end.clear_conditions()
                        for ii, cl in new_conditions_list.items():
                            for c in cl:
                                if ii.upper.is_from_end():
                                    new_condition = (
                                        substituter_durative_action_end.substitute(
                                            c, substitution_dict_end
                                        )
                                    )
                                else:
                                    new_condition = c
                                temp_action_end.add_condition(ii, new_condition)
                        generic_action_end_condition_list.append(combination_condition)
                        # print ("adding final action")
                        # print (temp_action_end)
                        all_actions_compiled.append(temp_action_end)
                    end_generic_action = sa.clone()
                    new_generic_conditions_list = end_generic_action.conditions
                    end_generic_action.clear_conditions()
                    for ii, cl in new_generic_conditions_list.items():
                        for c in cl:
                            if ii.lower.is_from_end():
                                # if it's end
                                if not (
                                    OperatorKind.INTERPRETED_FUNCTION_EXP
                                    in self.operators_extractor.get(c)
                                ):
                                    # if it has no IF add it
                                    end_generic_action.add_condition(ii, c)
                                # if it has ifs ignore it
                            else:
                                # if it's not from end (so it should be at start), just add it
                                end_generic_action.add_condition(ii, c)

                    for (
                        known_values_exclusion_conditions
                    ) in generic_action_end_condition_list:
                        end_not_condition = (
                            end_generic_action.environment.expression_manager.Not(
                                known_values_exclusion_conditions
                            )
                        )
                        end_generic_action.add_condition(EndTiming(), end_not_condition)
                    all_actions_compiled.append(end_generic_action)
                # print ("-----------------------------")
                # print ("here is the all actions list:")
                # print ("-----------------------------")
                # print (all_actions_compiled)
                for compiled_action in all_actions_compiled:
                    compiled_action.name = get_fresh_name(new_problem, a.name)
                    new_to_old[compiled_action] = a
                    new_problem.add_action(compiled_action)

            else:
                raise NotImplementedError
        print("compilation complete!")
        print(new_problem)
        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )

    def elaborate_known_IFs(self, ifvs):
        bk: OrderedDict = OrderedDict()
        for f in ifvs:
            if not (f.interpreted_function() in bk.keys()):
                bk[f.interpreted_function()] = OrderedDict()
            bk[f.interpreted_function()][f] = ifvs[f]

        return bk

    def knowledge_combinations(self, d, kl=None):
        if len(d) == 0:
            return d
        akl = None
        if kl is None:
            akl = d.keys()
        else:
            akl = self.intersection(kl, d.keys())
        if len(akl) == 0:
            empd: OrderedDict = OrderedDict()
            return empd

        c = it.product(*(d[Name] for Name in akl))
        return list(c)

    def add_empty_knowledge_values(self, d):
        for key in d:
            d[key][key] = key
        return d

    def intersection(self, lst1, lst2):
        return list(set(lst1) & set(lst2))
