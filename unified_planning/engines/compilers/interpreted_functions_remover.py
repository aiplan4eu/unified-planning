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
from unified_planning.model.fluent import Fluent
from unified_planning.model.interpreted_function import InterpretedFunction
from unified_planning.model.mixins.timed_conds_effs import TimedCondsEffs
from unified_planning.model.object import Object
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
    UPUsageError,
)
from unified_planning.model import (
    Problem,
    ProblemKind,
    Action,
    InstantaneousAction,
    DurativeAction,
    AbstractProblem,
    FNode,
    action,
)
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
    check_and_simplify_preconditions,
    check_and_simplify_conditions,
    replace_action,
)
from unified_planning.plans.plan import ActionInstance
from unified_planning.shortcuts import BoolType, UserType
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
        self._use_old_algorithm = False
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
        actions_list: list = list()
        interpreted_functions_queue: deque = deque()
        temp_problem = problem.clone()  # used to get fresh names might not be necessary
        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_actions()
        # temp_problem.clear_actions()
        better_knowledge = elaborate_known_IFs(self._interpreted_functions_values)
        combined_knowledge = knowledge_combinations(better_knowledge)
        kNum_for_interpreted_functions = UserType(
            "kNum_for_interpreted_functions"
        )  # does this need to have a unique name?

        known_values_imply_list: list = list()
        fluent_function_dict: dict = dict()
        fluent_function_dict.clear()
        object_dict: dict = dict()
        object_dict.clear()
        fluents_assignments_tuple_list: list = list()  # (fluent, input, output)
        fluents_assignments_tuple_list.clear()
        print("Compiling...")
        for a in problem.actions:
            # TODO - clean up code
            print("---------- now on action: ----------")
            print(a)
            if isinstance(a, InstantaneousAction):

                if self._use_old_algorithm:
                    # print ("old algorithm, many small actions")
                    elaborated_actions = old_algorithm(
                        a,
                        new_problem,
                        self._interpreted_functions_values,
                        better_knowledge,
                    )
                    # print ("elaborated actions:")
                    # print (elaborated_actions)
                    for ea in elaborated_actions:
                        ea.name = get_fresh_name(new_problem, a.name)
                        new_to_old[ea] = a
                        new_problem.add_action(ea)

                    continue

                interpreted_functions_queue.clear()
                no_IF_action_base = a.clone()
                no_IF_action_base.clear_preconditions()
                fixed_preconditions = []
                all_ifs_in_instantaneous_action: list = list()
                all_ifs_in_instantaneous_action.clear()
                temp_a = a.clone()
                temp_a.clear_preconditions()
                for p in a.preconditions:
                    templist = _fix_precondition(p)
                    fixed_preconditions.extend(templist)
                for p in fixed_preconditions:
                    IFs = self.interpreted_functions_extractor.get(p)
                    if len(IFs) == 0:
                        no_IF_action_base.add_precondition(p)
                    else:
                        for f in IFs:
                            # print(f)
                            if f not in all_ifs_in_instantaneous_action:
                                # and append them in the key list if not already there
                                all_ifs_in_instantaneous_action.append(f)
                                interpreted_functions_queue.append(f)

                for p in fixed_preconditions:
                    temp_a.add_precondition(p)

                actions_list.clear()
                actions_list.append(temp_a)
                while len(interpreted_functions_queue) > 0:
                    IF_to_handle_now = interpreted_functions_queue.pop()
                    if (
                        IF_to_handle_now.interpreted_function()
                        in better_knowledge.keys()
                    ):
                        temp_action_list: list = list()
                        temp_action_list.clear()
                        for partially_elaborated_action in actions_list:
                            # print (partially_elaborated_action)

                            placeholder_function_name = get_fresh_name(
                                temp_problem,
                                ("f_" + IF_to_handle_now.interpreted_function().name),
                            )
                            placeholder_function_fluent = None
                            if placeholder_function_name in fluent_function_dict.keys():
                                placeholder_function_fluent = fluent_function_dict[
                                    placeholder_function_name
                                ]

                            else:
                                placeholder_function_fluent = Fluent(
                                    placeholder_function_name,
                                    IF_to_handle_now.interpreted_function().return_type,
                                    input_object=kNum_for_interpreted_functions,
                                )
                                fluent_function_dict[
                                    placeholder_function_name
                                ] = placeholder_function_fluent
                            argnamesstring = ""
                            for arg in IF_to_handle_now.args:
                                argnamesstring = argnamesstring + "_" + str(arg)

                            action_parameter_name = (
                                "P_" + placeholder_function_name + argnamesstring
                            )

                            action_for_known_values = (
                                _clone_instantaneous_add_parameter(
                                    partially_elaborated_action,
                                    action_parameter_name,
                                    kNum_for_interpreted_functions,
                                )
                            )
                            action_parameter = action_for_known_values.parameter(
                                action_parameter_name
                            )

                            # action_for_known_values = (partially_elaborated_action.clone())

                            # maybe can use new_problem but not sure

                            # input for placeholder is always one value, that might represent more than one input parameter for the original function
                            # function_placeholder = Fluent (placeholder_function_name)
                            # ---------------------------------------
                            # add parameter (Px:kNum)
                            # ? -> can I add this without reconstructing the action from scratch?
                            # ---------------------------------------

                            known_values_precondition_list: list = list()
                            known_values_precondition_list.clear()
                            known_values_imply_list.clear()
                            for known_value in better_knowledge[
                                IF_to_handle_now.interpreted_function()
                            ]:
                                compressed_input_name = "O"
                                argcounter_for_name = 0
                                while argcounter_for_name < len(IF_to_handle_now.args):
                                    compressed_input_name = (
                                        compressed_input_name
                                        + "_"
                                        + str(
                                            known_value.arg(
                                                argcounter_for_name
                                            ).constant_value()
                                        )
                                    )
                                    argcounter_for_name = argcounter_for_name + 1

                                # print("placeholder name before double checking")  # not sure double checking is necessary - the fluents have to be added only at the end I think
                                # print(compressed_input_name)
                                known_value_object = None
                                if compressed_input_name in object_dict.keys():
                                    known_value_object = object_dict[
                                        compressed_input_name
                                    ]
                                else:
                                    known_value_object = Object(
                                        compressed_input_name,
                                        kNum_for_interpreted_functions,
                                    )
                                    object_dict[
                                        compressed_input_name
                                    ] = known_value_object
                                # here add fluent assignment list
                                # placeholder_function_fluent(known_value_object) = VALUE
                                known_output_value = self._interpreted_functions_values[
                                    known_value
                                ]
                                fluents_assignments_tuple_list.append(
                                    (
                                        placeholder_function_fluent,
                                        known_value_object,
                                        known_output_value,
                                    )
                                )
                                argcounter = 0
                                known_values_precondition = None
                                imply_precondition = None
                                while argcounter < len(known_value.args):

                                    if known_values_precondition is None:
                                        known_values_precondition = _Equals_or_Iff(
                                            IF_to_handle_now.arg(argcounter),
                                            known_value.arg(argcounter),
                                            action_for_known_values,
                                        )
                                    else:
                                        temp_precondition = _Equals_or_Iff(
                                            IF_to_handle_now.arg(argcounter),
                                            known_value.arg(argcounter),
                                            action_for_known_values,
                                        )
                                        known_values_precondition = action_for_known_values.environment.expression_manager.And(
                                            known_values_precondition, temp_precondition
                                        )

                                    argcounter = argcounter + 1
                                # known_values_precondition implies that the value of the new action parameter is O_*knownvalue*

                                imply_precondition = action_for_known_values.environment.expression_manager.Implies(
                                    known_values_precondition,
                                    action_for_known_values.environment.expression_manager.Equals(
                                        action_parameter, known_value_object
                                    ),
                                )
                                known_values_imply_list.append(imply_precondition)
                                known_values_precondition_list.append(
                                    known_values_precondition
                                )
                            # end of for known_value in better knowledge

                            substitution_dict_instantaneous_action = dict()
                            placeholder_function_expression = (
                                placeholder_function_fluent(action_parameter)
                            )
                            substitution_dict_instantaneous_action[
                                IF_to_handle_now
                            ] = placeholder_function_expression
                            substituter_instantaneous_action: up.model.walkers.Substituter = up.model.walkers.Substituter(
                                action_for_known_values.environment
                            )
                            temp_preconditions_list = (
                                action_for_known_values.preconditions
                            )
                            action_for_known_values.clear_preconditions()
                            for p in temp_preconditions_list:
                                temp_precondition = (
                                    substituter_instantaneous_action.substitute(
                                        p, substitution_dict_instantaneous_action
                                    )
                                )
                                action_for_known_values.add_precondition(
                                    temp_precondition
                                )

                            for p in known_values_imply_list:
                                action_for_known_values.add_precondition(p)
                            Or_condition = None
                            for (
                                p
                            ) in known_values_precondition_list:  # we have to Or these
                                if Or_condition is None:
                                    Or_condition = p
                                else:
                                    Or_condition = action_for_known_values.environment.expression_manager.Or(
                                        Or_condition, p
                                    )
                            action_for_known_values.add_precondition(Or_condition)

                            # handle known values with usertype and object

                            temp_action_list.append(action_for_known_values)
                            action_for_known_values.name = get_fresh_name(
                                temp_problem, a.name
                            )  # might not be necessary - just for naming purposes
                            temp_problem.add_action(
                                action_for_known_values
                            )  # might not be necessary - just for naming purposes
                            # print ("now making action for unknown values ---")
                            # now add precondition for unknown values and remove the if
                            action_for_unknown_values = (
                                partially_elaborated_action.clone()
                            )
                            preconditions_for_unknown_values = (
                                action_for_unknown_values.preconditions
                            )
                            action_for_unknown_values.clear_preconditions()
                            # print (preconditions_for_unknown_values)
                            for p in preconditions_for_unknown_values:
                                # print (p)
                                # print ("has ifs:")
                                IFs = self.interpreted_functions_extractor.get(p)
                                # print (IFs)
                                if IF_to_handle_now not in IFs:
                                    # print("seems that this precondition does not contain our IF, we can add it back")
                                    # print(p)
                                    action_for_unknown_values.add_precondition(p)
                                # else:
                                #    print(p)
                                #    print(IF_to_handle_now)
                                #    print("this one is here")

                            # print("for unknown values we have to Not the preocnditions")
                            for p in known_values_precondition_list:
                                notp = action_for_unknown_values.environment.expression_manager.Not(
                                    p
                                )
                                action_for_unknown_values.add_precondition(notp)
                            temp_action_list.append(action_for_unknown_values)
                            # print ("end elaborating unknown values if")
                            action_for_unknown_values.name = get_fresh_name(
                                temp_problem, a.name
                            )  # might not be necessary - just for naming purposes
                            temp_problem.add_action(
                                action_for_unknown_values
                            )  # might not be necessary - just for naming purposes
                        actions_list.clear()
                        actions_list.extend(temp_action_list)
                    else:
                        temp_action_list = list()
                        temp_action_list.clear()
                        for partially_elaborated_action in actions_list:
                            preconditions_no_info = (
                                partially_elaborated_action.preconditions
                            )
                            partially_elaborated_action.clear_preconditions()

                            for p in preconditions_no_info:
                                IFs = self.interpreted_functions_extractor.get(p)
                                if IF_to_handle_now not in IFs:
                                    partially_elaborated_action.add_precondition(p)
                            temp_action_list.append(partially_elaborated_action)
                        actions_list.clear()
                        actions_list.extend(temp_action_list)
                print_debug = False
                if print_debug:
                    print("done!")
                    print("final list of actions:")
                    print(actions_list)
                    print("\ndict of fluents to add to the problem")
                    print(fluent_function_dict)
                    print("\ndict of objects to add to the problem")
                    print(object_dict)
                    print("\nlist of tuples of fluent values to add to the problem")
                    print(fluents_assignments_tuple_list)
                for final_action in actions_list:
                    final_action.name = get_fresh_name(new_problem, a.name)
                    new_to_old[final_action] = a
                    new_problem.add_action(final_action)

            elif isinstance(a, DurativeAction):
                # TODO - new algorithm for durative
                # print ("new action ---------------------------------------------------------------------------------")
                no_IF_action = a.clone()
                minduration: FNode | int = 1
                maxduration: FNode | int = 1000000
                IF_in_durations: list = list()
                IF_in_start_conditions: list = list()
                IF_in_end_conditions: list = list()
                IF_keys_in_durations: list = list()
                IF_keys_in_start_conditions: list = list()
                IF_keys_in_end_conditions: list = list()
                known_values_condition_list: list = list()
                base_action = a.clone()
                base_action.clear_conditions()
                new_actions_list: list = list()
                substituter_durative_action: up.model.walkers.Substituter = (
                    up.model.walkers.Substituter(a.environment)
                )

                IFs_from_conditions: list = list()
                IF_times_from_conditions: list = list()
                IFs_from_durations: list = list()

                for ii, cl in a.conditions.items():
                    # IFs_from_conditions[ii] = list()
                    for c in cl:
                        IFs = self.interpreted_functions_extractor.get(c)
                        for f in IFs:
                            if f not in IFs_from_conditions:
                                IFs_from_conditions.append(f)
                                IF_times_from_conditions.append(ii)
                                print("added function and timestamp")
                                print(IFs_from_conditions)
                                print(IF_times_from_conditions)
                        base_action.add_condition(ii, c)
                # print ("action with fixed conditions")
                # print (base_action)

                # print ("all ifs from conditions")
                # print (IFs_from_conditions)
                if (
                    not OperatorKind.INTERPRETED_FUNCTION_EXP
                    in self.operators_extractor.get(a.duration.lower)
                ):
                    minduration = a.duration.lower
                else:
                    IFs = self.interpreted_functions_extractor.get(a.duration.lower)
                    for f in IFs:
                        IFs_from_durations.append(f)
                if (
                    not OperatorKind.INTERPRETED_FUNCTION_EXP
                    in self.operators_extractor.get(a.duration.upper)
                ):
                    maxduration = a.duration.upper
                else:
                    IFs = self.interpreted_functions_extractor.get(a.duration.upper)
                    for f in IFs:
                        IFs_from_durations.append(f)
                # print ("all ifs from durations")
                # print (IFs_from_durations)

                actions_list.clear()
                actions_list.append(base_action)

                interpreted_functions_queue.clear()
                # start with durations part
                for f in IFs_from_durations:
                    interpreted_functions_queue.append(f)
                while len(interpreted_functions_queue) > 0:
                    IF_to_handle_now = interpreted_functions_queue.pop()
                    # print (IF_to_handle_now)
                    # print ("was found in a duration")
                    # print ("all our knowledge is")
                    # print (better_knowledge)
                    new_actions_list.clear()
                    if (
                        IF_to_handle_now.interpreted_function()
                        in better_knowledge.keys()
                    ):
                        # print ("we know something about this")
                        # print ("have to make two actions, one for known one for unknown")

                        for partially_elaborated_action in actions_list:
                            placeholder_function_name = get_fresh_name(
                                temp_problem,
                                ("f_" + IF_to_handle_now.interpreted_function().name),
                            )
                            placeholder_function_fluent = None
                            if placeholder_function_name in fluent_function_dict.keys():
                                placeholder_function_fluent = fluent_function_dict[
                                    placeholder_function_name
                                ]

                            else:
                                placeholder_function_fluent = Fluent(
                                    placeholder_function_name,
                                    IF_to_handle_now.interpreted_function().return_type,
                                    input_object=kNum_for_interpreted_functions,
                                )
                                fluent_function_dict[
                                    placeholder_function_name
                                ] = placeholder_function_fluent
                            argnamesstring = ""
                            for arg in IF_to_handle_now.args:
                                argnamesstring = argnamesstring + "_" + str(arg)
                            action_parameter_name = (
                                "P_" + placeholder_function_name + argnamesstring
                            )
                            action_for_known_values = _clone_durative_add_parameter(
                                partially_elaborated_action,
                                action_parameter_name,
                                kNum_for_interpreted_functions,
                            )
                            action_parameter = action_for_known_values.parameter(
                                action_parameter_name
                            )
                            # print ("test clone durative action")
                            # print (action_for_known_values)

                            known_values_condition_list.clear()
                            known_values_imply_list.clear()
                            for known_value in better_knowledge[
                                IF_to_handle_now.interpreted_function()
                            ]:
                                compressed_input_name = "O"
                                argcounter_for_name = 0
                                while argcounter_for_name < len(IF_to_handle_now.args):
                                    compressed_input_name = (
                                        compressed_input_name
                                        + "_"
                                        + str(
                                            known_value.arg(
                                                argcounter_for_name
                                            ).constant_value()
                                        )
                                    )
                                    argcounter_for_name = argcounter_for_name + 1
                                    # print("placeholder name before double checking")  # not sure double checking is necessary - the fluents have to be added only at the end I think
                                # print(compressed_input_name)
                                known_value_object = None
                                if compressed_input_name in object_dict.keys():
                                    known_value_object = object_dict[
                                        compressed_input_name
                                    ]
                                else:
                                    known_value_object = Object(
                                        compressed_input_name,
                                        kNum_for_interpreted_functions,
                                    )
                                    object_dict[
                                        compressed_input_name
                                    ] = known_value_object
                                # here add fluent assignment list
                                # placeholder_function_fluent(known_value_object) = VALUE
                                known_output_value = self._interpreted_functions_values[
                                    known_value
                                ]
                                fluents_assignments_tuple_list.append(
                                    (
                                        placeholder_function_fluent,
                                        known_value_object,
                                        known_output_value,
                                    )
                                )
                                argcounter = 0
                                known_values_condition = None
                                imply_condition = None
                                while argcounter < len(known_value.args):

                                    if known_values_condition is None:
                                        known_values_condition = _Equals_or_Iff(
                                            IF_to_handle_now.arg(argcounter),
                                            known_value.arg(argcounter),
                                            action_for_known_values,
                                        )
                                    else:
                                        temp_condition = _Equals_or_Iff(
                                            IF_to_handle_now.arg(argcounter),
                                            known_value.arg(argcounter),
                                            action_for_known_values,
                                        )
                                        known_values_condition = action_for_known_values.environment.expression_manager.And(
                                            known_values_condition, temp_condition
                                        )

                                    argcounter = argcounter + 1
                                # known_values_precondition implies that the value of the new action parameter is O_*knownvalue*

                                imply_condition = action_for_known_values.environment.expression_manager.Implies(
                                    known_values_condition,
                                    action_for_known_values.environment.expression_manager.Equals(
                                        action_parameter, known_value_object
                                    ),
                                )
                                known_values_imply_list.append(imply_condition)
                                known_values_condition_list.append(
                                    known_values_condition
                                )
                            # end of for known_value in better knowledge
                            substitution_dict_durative_action = dict()
                            placeholder_function_expression = (
                                placeholder_function_fluent(action_parameter)
                            )
                            substitution_dict_durative_action[
                                IF_to_handle_now
                            ] = placeholder_function_expression

                            lowtimeexp = action_for_known_values.duration.lower
                            uptimeexp = action_for_known_values.duration.upper
                            temp_low = substituter_durative_action.substitute(
                                lowtimeexp, substitution_dict_durative_action
                            )
                            temp_up = substituter_durative_action.substitute(
                                uptimeexp, substitution_dict_durative_action
                            )
                            action_for_known_values.set_closed_duration_interval(
                                temp_low, temp_up
                            )

                            for p in known_values_imply_list:
                                action_for_known_values.add_condition(StartTiming(), p)
                            Or_condition = None
                            for (
                                p
                            ) in (
                                known_values_condition_list
                            ):  # we have to Or these - TODO not checked or condition with complex problems
                                if Or_condition is None:
                                    Or_condition = p
                                else:
                                    Or_condition = action_for_known_values.environment.expression_manager.Or(
                                        Or_condition, p
                                    )
                            action_for_known_values.add_condition(
                                StartTiming(), Or_condition
                            )
                            # print ("action_for_known_values")
                            # print (action_for_known_values)
                            new_actions_list.append(action_for_known_values)
                            action_for_known_values.name = get_fresh_name(
                                temp_problem, a.name
                            )  # might not be necessary - just for naming purposes
                            temp_problem.add_action(
                                action_for_known_values
                            )  # might not be necessary - just for naming purposes

                            action_for_unknown_values = (
                                partially_elaborated_action.clone()
                            )
                            for p in known_values_condition_list:
                                notp = action_for_unknown_values.environment.expression_manager.Not(
                                    p
                                )
                                action_for_unknown_values.add_condition(
                                    StartTiming(), notp
                                )

                            IFs_in_lower = self.interpreted_functions_extractor.get(
                                action_for_unknown_values.duration.lower
                            )
                            IFs_in_upper = self.interpreted_functions_extractor.get(
                                action_for_unknown_values.duration.upper
                            )

                            lowtimeexp = action_for_known_values.duration.lower
                            uptimeexp = action_for_known_values.duration.upper

                            if IF_to_handle_now in IFs_in_lower:
                                lowtimeexp = minduration
                            if IF_to_handle_now in IFs_in_upper:
                                uptimeexp = maxduration

                            action_for_unknown_values.set_closed_duration_interval(
                                lowtimeexp, uptimeexp
                            )

                            # TODO - implement this
                            new_actions_list.append(action_for_unknown_values)
                            # print ("end elaborating unknown values if")
                            action_for_unknown_values.name = get_fresh_name(
                                temp_problem, a.name
                            )  # might not be necessary - just for naming purposes
                            temp_problem.add_action(
                                action_for_unknown_values
                            )  # might not be necessary - just for naming purposes

                    else:
                        for pea in actions_list:
                            ta = pea.clone()
                            ta.set_closed_duration_interval(minduration, maxduration)
                            new_actions_list.append(ta)

                        print("we have no knowledge of this")

                    actions_list.clear()
                    for pea in new_actions_list:
                        actions_list.append(pea)
                print("after elaborating durations, the list now is")
                print(actions_list)
                print("now elaborate conditions!")
                print("we have this from conditions:")
                print(IFs_from_conditions)

                # code seems to work up until here
                # TODO - finish this thing

                interpreted_functions_timestamps: deque = deque()
                qiter = 0
                while qiter < len(IFs_from_conditions):
                    interpreted_functions_queue.append(IFs_from_conditions[qiter])
                    interpreted_functions_timestamps.append(
                        IF_times_from_conditions[qiter]
                    )

                    qiter = qiter + 1
                print(interpreted_functions_queue)
                print(interpreted_functions_timestamps)
                while len(interpreted_functions_queue) > 0:
                    IF_to_handle_now = interpreted_functions_queue.pop()
                    IF_time = interpreted_functions_timestamps.pop()

                    new_actions_list.clear()
                    if (
                        IF_to_handle_now.interpreted_function()
                        in better_knowledge.keys()
                    ):
                        print("we know something about this one")
                        print(IF_to_handle_now)
                        print(better_knowledge[IF_to_handle_now.interpreted_function()])
                        new_actions_list.clear()
                        for partially_elaborated_action in actions_list:
                            placeholder_function_name = get_fresh_name(
                                temp_problem,
                                ("f_" + IF_to_handle_now.interpreted_function().name),
                            )
                            placeholder_function_fluent = None
                            if placeholder_function_name in fluent_function_dict.keys():
                                placeholder_function_fluent = fluent_function_dict[
                                    placeholder_function_name
                                ]
                            else:
                                placeholder_function_fluent = Fluent(
                                    placeholder_function_name,
                                    IF_to_handle_now.interpreted_function().return_type,
                                    input_object=kNum_for_interpreted_functions,
                                )
                                fluent_function_dict[
                                    placeholder_function_name
                                ] = placeholder_function_fluent
                            argnamesstring = ""
                            for arg in IF_to_handle_now.args:
                                argnamesstring = argnamesstring + "_" + str(arg)
                            action_parameter_name = (
                                "P_" + placeholder_function_name + argnamesstring
                            )
                            action_for_known_values = _clone_durative_add_parameter(
                                partially_elaborated_action,
                                action_parameter_name,
                                kNum_for_interpreted_functions,
                            )
                            action_parameter = action_for_known_values.parameter(
                                action_parameter_name
                            )
                            known_values_condition_list.clear()
                            known_values_imply_list.clear()
                            for known_value in better_knowledge[
                                IF_to_handle_now.interpreted_function()
                            ]:
                                compressed_input_name = "O"
                                argcounter_for_name = 0
                                while argcounter_for_name < len(IF_to_handle_now.args):
                                    compressed_input_name = (
                                        compressed_input_name
                                        + "_"
                                        + str(
                                            known_value.arg(
                                                argcounter_for_name
                                            ).constant_value()
                                        )
                                    )
                                    argcounter_for_name = argcounter_for_name + 1
                                known_value_object = None
                                if compressed_input_name in object_dict.keys():
                                    known_value_object = object_dict[
                                        compressed_input_name
                                    ]
                                else:
                                    known_value_object = Object(
                                        compressed_input_name,
                                        kNum_for_interpreted_functions,
                                    )
                                    object_dict[
                                        compressed_input_name
                                    ] = known_value_object
                                known_output_value = self._interpreted_functions_values[
                                    known_value
                                ]
                                fluents_assignments_tuple_list.append(
                                    (
                                        placeholder_function_fluent,
                                        known_value_object,
                                        known_output_value,
                                    )
                                )
                                argcounter = 0
                                known_values_condition = None
                                imply_condition = None
                                while argcounter < len(known_value.args):
                                    if known_values_condition is None:
                                        known_values_condition = _Equals_or_Iff(
                                            IF_to_handle_now.arg(argcounter),
                                            known_value.arg(argcounter),
                                            action_for_known_values,
                                        )
                                    else:
                                        temp_condition = _Equals_or_Iff(
                                            IF_to_handle_now.arg(argcounter),
                                            known_value.arg(argcounter),
                                            action_for_known_values,
                                        )
                                        known_values_condition = action_for_known_values.environment.expression_manager.And(
                                            known_values_condition, temp_condition
                                        )
                                    argcounter = argcounter + 1
                                imply_condition = action_for_known_values.environment.expression_manager.Implies(
                                    known_values_condition,
                                    action_for_known_values.environment.expression_manager.Equals(
                                        action_parameter, known_value_object
                                    ),
                                )
                                known_values_imply_list.append(imply_condition)
                                known_values_condition_list.append(
                                    known_values_condition
                                )
                            substitution_dict_durative_action = dict()
                            placeholder_function_expression = (
                                placeholder_function_fluent(action_parameter)
                            )
                            substitution_dict_durative_action[
                                IF_to_handle_now
                            ] = placeholder_function_expression
                            temp_conditions_list = (
                                action_for_known_values.conditions.items()
                            )
                            action_for_known_values.clear_conditions()
                            for ii, cl in temp_conditions_list:
                                for c in cl:
                                    temp_condition = (
                                        substituter_durative_action.substitute(
                                            c, substitution_dict_durative_action
                                        )
                                    )
                                    action_for_known_values.add_condition(
                                        ii, temp_condition
                                    )
                            for p in known_values_imply_list:
                                action_for_known_values.add_condition(StartTiming(), p)
                                # TODO this should be fine at start timing, but not sure, needs test/better implementation
                            Or_condition = None
                            for p in known_values_condition_list:
                                if Or_condition is None:
                                    Or_condition = p
                                else:

                                    Or_condition = action_for_known_values.environment.expression_manager.Or(
                                        Or_condition, p
                                    )
                            action_for_known_values.add_condition(
                                StartTiming(), Or_condition
                            )
                            # TODO, this probably needs better implementation, everything at start timing is not 100% correct
                            new_actions_list.append(action_for_known_values)
                            action_for_known_values.name = get_fresh_name(
                                temp_problem, a.name
                            )
                            temp_problem.add_action(action_for_known_values)
                            # now unknown
                            action_for_unknown_values = (
                                partially_elaborated_action.clone()
                            )
                            conditions_for_unknown_values = (
                                action_for_unknown_values.conditions.items()
                            )
                            action_for_unknown_values.clear_conditions()
                            for ii, cl in conditions_for_unknown_values:
                                for c in cl:
                                    IFs = self.interpreted_functions_extractor.get(c)
                                    if IF_to_handle_now not in IFs:
                                        action_for_unknown_values.add_condition(ii, c)
                            for p in known_values_condition_list:
                                notp = action_for_unknown_values.environment.expression_manager.Not(
                                    p
                                )
                                action_for_unknown_values.add_condition(
                                    StartTiming(), notp
                                )
                                # TODO - check correctness of this - starttiming is not good here
                            new_actions_list.append(action_for_unknown_values)
                            action_for_unknown_values.name = get_fresh_name(
                                temp_problem, a.name
                            )
                            temp_problem.add_action(action_for_unknown_values)
                        actions_list.clear()
                        actions_list.extend(new_actions_list)

                    else:
                        print("we know nothing about this one")
                        print(IF_to_handle_now)
                        print(better_knowledge)
                        print("at time")
                        print(IF_time)
                        new_actions_list.clear()
                        for partially_elaborated_action in actions_list:
                            conditions_no_info = (
                                partially_elaborated_action.conditions.items()
                            )
                            partially_elaborated_action.clear_conditions()
                            for ii, cl in conditions_no_info:
                                for c in cl:
                                    IFs = self.interpreted_functions_extractor.get(c)
                                    if IF_to_handle_now not in IFs:
                                        partially_elaborated_action.add_condition(ii, c)
                            new_actions_list.append(partially_elaborated_action)
                        actions_list.clear()
                        actions_list.extend(new_actions_list)
                for ca in actions_list:
                    ca.name = get_fresh_name(new_problem, a.name)
                    new_to_old[ca] = a
                    new_problem.add_action(ca)

                # TODO - bugfix - KeyError (?)

            else:
                raise NotImplementedError
        for fkey in fluent_function_dict:
            # change here if we need a specific default value
            if fluent_function_dict[fkey].type.is_bool_type():
                new_problem.add_fluent(fluent_function_dict[fkey])
            else:
                new_problem.add_fluent(fluent_function_dict[fkey])
        for okey in object_dict:
            new_problem.add_object(object_dict[okey])
        for ftuple in fluents_assignments_tuple_list:
            problem.set_initial_value(ftuple[0](ftuple[1]), ftuple[2])

        print_debug = False
        if print_debug:
            print("compilation complete!")
            print(new_problem)

        return CompilerResult(
            new_problem, partial(custom_replace, map=new_to_old), self.name
        )


def elaborate_known_IFs(ifvs):
    bk: OrderedDict = OrderedDict()
    for f in ifvs:
        if not (f.interpreted_function() in bk.keys()):
            bk[f.interpreted_function()] = OrderedDict()
        bk[f.interpreted_function()][f] = ifvs[f]

    return bk


def knowledge_combinations(d, kl=None):
    if len(d) == 0:
        return d
    akl = None
    if kl is None:
        akl = d.keys()
    else:
        akl = intersection(kl, d.keys())
    if len(akl) == 0:
        empd: OrderedDict = OrderedDict()
        return empd

    c = it.product(*(d[Name] for Name in akl))
    return list(c)


def add_empty_knowledge_values(d):
    for key in d:
        d[key][key] = key
    return d


def intersection(lst1, lst2):
    return list(set(lst1) & set(lst2))


def _Equals_or_Iff(exp1, exp2, action):
    ret_exp = None
    if exp1.type.is_bool_type():
        ret_exp = action.environment.expression_manager.Iff(exp1, exp2)
    else:
        ret_exp = action.environment.expression_manager.Equals(exp1, exp2)
    return ret_exp


def _clone_durative_add_parameter(action, new_parameter_name, param_type):
    new_params = OrderedDict(
        (param_name, param.type) for param_name, param in action._parameters.items()
    )

    if new_parameter_name in new_params.keys():
        print("could not add the new parameter")
        # TODO managing duplicate names

    else:
        new_params[new_parameter_name] = param_type
    # TODO without _variables
    new_durative_action = DurativeAction(action._name, new_params, action._environment)
    new_durative_action._duration = action._duration

    TimedCondsEffs._clone_to(action, new_durative_action)
    return new_durative_action


def _clone_instantaneous_add_parameter(action, new_parameter_name, param_type):
    # not sure how to do this without "private" variables
    new_params = OrderedDict(
        # TODO - action.parameters returns _parameters.values(), we need items()
        (param_name, param.type)
        for param_name, param in action._parameters.items()
    )

    if new_parameter_name in new_params.keys():
        print("could not add the new parameter")
        # TODO managing duplicate names
    else:
        new_params[new_parameter_name] = param_type
    new_instantaneous_action = InstantaneousAction(
        action._name, new_params, action._environment
    )
    # redo this without _variables TODO
    for p in action.preconditions:
        new_instantaneous_action.add_precondition(p)
    new_instantaneous_action._effects = [
        e.clone() for e in action.effects
    ]  # this is also strange
    new_instantaneous_action._fluents_assigned = (
        action._fluents_assigned.copy()
    )  # how to get this?
    new_instantaneous_action._fluents_inc_dec = (
        action._fluents_inc_dec.copy()
    )  # how to get this?
    new_instantaneous_action._simulated_effect = action.simulated_effect
    return new_instantaneous_action


def _fix_precondition(a):
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


def custom_replace(
    action_instance: ActionInstance,
    map: Dict["up.model.Action", Optional["up.model.Action"]],
) -> Optional[ActionInstance]:
    try:
        replaced_action = map[action_instance.action]
    except KeyError:
        raise UPUsageError(
            "The Action of the given ActionInstance does not have a valid replacement."
        )
    expected_amount = 0
    if replaced_action is not None:
        if replaced_action.parameters is not None:
            expected_amount = len(replaced_action.parameters)

    new_list: list = list()
    i = 0
    while i < expected_amount:
        new_list.append(action_instance.actual_parameters[i])
        i = i + 1
    # this might want a tuple instad of a list
    if replaced_action is not None:
        return ActionInstance(
            replaced_action,
            new_list,
            action_instance.agent,
            action_instance.motion_paths,
        )
    else:
        return None


def old_algorithm(a, new_problem, ifvs, better_knowledge):
    # print ("old algorithm called ----------------------------")

    oe: up.model.walkers.OperatorsExtractor = up.model.walkers.OperatorsExtractor()
    ife: up.model.walkers.InterpretedFunctionsExtractor = (
        up.model.walkers.InterpretedFunctionsExtractor()
    )
    sub: up.model.walkers.Substituter = up.model.walkers.Substituter(a.environment)

    return_list = list()
    interpreted_functions_queue: deque = deque()
    base_action = a.clone()
    base_action.clear_preconditions()
    no_IF_action_base = a.clone()
    no_IF_action_base.clear_preconditions()
    no_IF_action_preconditions_list: list = list()
    fixed_preconditions = []
    all_ifs_in_instantaneous_action: list = list()
    all_ifs_in_instantaneous_action.clear()
    for p in a.preconditions:
        templist = _fix_precondition(p)
        fixed_preconditions.extend(templist)
    for p in fixed_preconditions:
        base_action.add_precondition(p)
        IFs = ife.get(p)
        for f in IFs:
            if f not in all_ifs_in_instantaneous_action:
                all_ifs_in_instantaneous_action.append(f)
                interpreted_functions_queue.append(f)

    actions_list: list = list()
    new_actions_list: list = list()

    known_values_conditions: list = list()
    actions_list.clear()
    actions_list.append(base_action)
    while len(interpreted_functions_queue) > 0:
        new_actions_list.clear()
        IF_to_handle_now = interpreted_functions_queue.pop()
        if IF_to_handle_now.interpreted_function() not in better_knowledge.keys():
            for pea in actions_list:
                ta = pea.clone()
                ta.clear_preconditions()
                for precon in pea.preconditions:
                    IFP = ife.get(precon)
                    if IF_to_handle_now not in IFP:
                        ta.add_precondition(precon)
                new_actions_list.append(ta)

        else:
            # print ("we know something about")
            # print (IF_to_handle_now)
            # print (better_knowledge[IF_to_handle_now.interpreted_function()])
            # print ("first let's do the ones we know something about")
            known_values_conditions.clear()
            for b in better_knowledge[IF_to_handle_now.interpreted_function()]:
                # print (IF_to_handle_now) # thing to substitute
                # print (ifvs[b]) # value to put in its place
                arg_names = IF_to_handle_now.args
                arg_values = b.args
                # print (arg_names) # names of the arguments
                # print (arg_values) # arguments have to be equal to this
                subdict: dict = dict()
                subdict.clear()
                subdict[IF_to_handle_now] = ifvs[b]

                argcounter = 0
                arguments_precondition = None
                while argcounter < len(arg_names):
                    if arguments_precondition is None:
                        arguments_precondition = _Equals_or_Iff(
                            arg_names[argcounter], arg_values[argcounter], a
                        )
                    else:
                        temp_precondition = _Equals_or_Iff(
                            arg_names[argcounter], arg_values[argcounter], a
                        )
                        arguments_precondition = a.environment.expression_manager.And(
                            arguments_precondition, temp_precondition
                        )
                    argcounter = argcounter + 1
                known_values_conditions.append(arguments_precondition)
                for pea in actions_list:
                    ta = pea.clone()
                    ta.clear_preconditions()
                    for precon in pea.preconditions:
                        temp_con = sub.substitute(precon, subdict)
                        ta.add_precondition(temp_con)
                    ta.add_precondition(arguments_precondition)
                    new_actions_list.append(ta)

            # print ("then let's do the generic case")
            # print ("all these have to bet not")
            # print (known_values_conditions)
            for pea in actions_list:
                ta = pea.clone()
                ta.clear_preconditions()
                for precon in pea.preconditions:
                    IFP = ife.get(precon)
                    if IF_to_handle_now not in IFP:
                        ta.add_precondition(precon)
                for nprecon in known_values_conditions:
                    temp_precondition = ta.environment.expression_manager.Not(nprecon)
                    ta.add_precondition(temp_precondition)
                new_actions_list.append(ta)
        actions_list.clear()
        for ac in new_actions_list:
            actions_list.append(ac)

    return actions_list
