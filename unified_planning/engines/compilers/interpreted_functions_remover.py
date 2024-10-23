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
        temp_problem = problem.clone()  # used to get fresh names might not be necessary
        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_actions()
        # temp_problem.clear_actions()
        better_knowledge = self.elaborate_known_IFs(self._interpreted_functions_values)
        combined_knowledge = self.knowledge_combinations(better_knowledge)
        kNum_for_interpreted_functions = UserType(
            "kNum_for_interpreted_functions"
        )  # does this need to have a unique name?

        fluent_function_dict: dict = dict()
        fluent_function_dict.clear()
        object_dict: dict = dict()
        object_dict.clear()
        fluents_assignments_tuple_list: list = list()  # (fluent, input, output)
        fluents_assignments_tuple_list.clear()
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
                interpreted_functions_queue: deque = deque()
                no_IF_action_base = a.clone()
                no_IF_action_base.clear_preconditions()
                no_IF_action_preconditions_list: list = list()
                fixed_preconditions = []
                for p in a.preconditions:
                    templist = self._fix_precondition(p)
                    fixed_preconditions.extend(templist)
                for p in fixed_preconditions:
                    IFs = self.interpreted_functions_extractor.get(p)
                    if len(IFs) == 0:
                        no_IF_action_base.add_precondition(p)

                all_combinations_for_this_action: OrderedDict = OrderedDict()

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
                temp_a.clear_preconditions()
                for p in fixed_preconditions:
                    temp_a.add_precondition(p)

                print(len(all_ifs_in_instantaneous_action))
                number_of_combinations = 2 ** len(all_ifs_in_instantaneous_action)
                print("there are")
                print(number_of_combinations)
                print("combinations")
                print(all_ifs_in_instantaneous_action)
                actions_list: list = list()
                actions_list.clear()
                actions_list.append(temp_a)
                # moved lists/dict assignments from here
                while len(interpreted_functions_queue) > 0:
                    IF_to_handle_now = interpreted_functions_queue.pop()
                    print(
                        "new if to handle ---------------------------------------------------"
                    )
                    if (
                        IF_to_handle_now.interpreted_function()
                        in better_knowledge.keys()
                    ):
                        print("we know some values for this one")
                        print(IF_to_handle_now)
                        print("is an instance of")
                        print(IF_to_handle_now.interpreted_function())
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
                            print(argnamesstring)
                            action_parameter_name = (
                                "P_" + placeholder_function_name + argnamesstring
                            )

                            action_for_known_values = (
                                self._clone_instantaneous_add_parameter(
                                    partially_elaborated_action,
                                    action_parameter_name,
                                    kNum_for_interpreted_functions,
                                )
                            )
                            action_parameter = action_for_known_values.parameter(
                                action_parameter_name
                            )
                            print("just cloned action")
                            print(action_for_known_values)

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
                            known_values_imply_list: list = list()
                            known_values_imply_list.clear()
                            for known_value in better_knowledge[
                                IF_to_handle_now.interpreted_function()
                            ]:
                                print("known value of")
                                print(known_value)
                                print("is")
                                print(self._interpreted_functions_values[known_value])
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
                                        known_values_precondition = self._Equals_or_Iff(
                                            IF_to_handle_now.arg(argcounter),
                                            known_value.arg(argcounter),
                                            action_for_known_values,
                                        )
                                    else:
                                        temp_precondition = self._Equals_or_Iff(
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

                            print(
                                "========================================================"
                            )
                            print("action for known values:")
                            print(action_for_known_values)
                            print(
                                "========================================================"
                            )
                            temp_action_list.append(action_for_known_values)
                            action_for_known_values.name = get_fresh_name(
                                temp_problem, a.name
                            )  # might not be necessary - just for naming purposes
                            temp_problem.add_action(
                                action_for_known_values
                            )  # might not be necessary - just for naming purposes
                            # unknown values ----------------------------------------------------------------
                            # unknown values ----------------------------------------------------------------
                            # unknown values ----------------------------------------------------------------
                            # unknown values ----------------------------------------------------------------
                            # unknown values ----------------------------------------------------------------
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
                            print("action for unknown values:")
                            print(action_for_unknown_values)

                            print(
                                "========================================================"
                            )
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
                        print("we have no info about this IF")
                        print(IF_to_handle_now)
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

                print(
                    "/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\"
                )
                print(
                    "\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/"
                )
                print(
                    "/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\"
                )
                print(
                    "\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/"
                )
                print(
                    "/\\                                                                              /\\"
                )
                print(
                    "\\/                                                                              \\/"
                )
                print("done!")
                print("final list of actions:")
                print(actions_list)
                print("\ndict of fluents to add to the problem")
                print(fluent_function_dict)
                print("\ndict of objects to add to the problem")
                print(object_dict)
                print("\nlist of tuples of fluent values to add to the problem")
                print(fluents_assignments_tuple_list)
                print(
                    "/\\                                                                              /\\"
                )
                print(
                    "\\/                                                                              \\/"
                )
                print(
                    "/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\"
                )
                print(
                    "\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/"
                )
                print(
                    "/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\"
                )
                print(
                    "\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/"
                )
                for final_action in actions_list:
                    final_action.name = get_fresh_name(new_problem, a.name)
                    new_to_old[final_action] = a
                    new_problem.add_action(final_action)

                continue
                # old implementation will be removed
                # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
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

                            substituter_instantaneous_action_old: up.model.walkers.Substituter = up.model.walkers.Substituter(
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
                                    substituter_instantaneous_action_old.substitute(
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
        # TODO
        # add fluents / objects / fluent tuples
        print("final part, content of fluent dict")
        for fkey in fluent_function_dict:
            # change here if we need a specific default value
            if fluent_function_dict[fkey].type.is_bool_type():
                new_problem.add_fluent(fluent_function_dict[fkey])
            else:
                new_problem.add_fluent(fluent_function_dict[fkey])
        for okey in object_dict:
            new_problem.add_object(object_dict[okey])
        for ftuple in fluents_assignments_tuple_list:
            print(ftuple)
            print(ftuple[0])
            print(ftuple[1])
            print(ftuple[2])
            problem.set_initial_value(ftuple[0](ftuple[1]), ftuple[2])

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

    def _Equals_or_Iff(self, exp1, exp2, action):
        ret_exp = None
        if exp1.type.is_bool_type():
            ret_exp = action.environment.expression_manager.Iff(exp1, exp2)
        else:
            ret_exp = action.environment.expression_manager.Equals(exp1, exp2)
        return ret_exp

    def _clone_instantaneous_add_parameter(
        self, action, new_parameter_name, param_type
    ):
        # not sure how to do this without "private" variables
        new_params = OrderedDict(
            (param_name, param.type) for param_name, param in action._parameters.items()
        )

        if new_parameter_name in new_params.keys():
            print("oopsie")
            print("could not add the new parameter")
        else:
            new_params[new_parameter_name] = param_type
        new_instantaneous_action = InstantaneousAction(
            action._name, new_params, action._environment
        )
        new_instantaneous_action._preconditions = action._preconditions[:]
        new_instantaneous_action._effects = [e.clone() for e in action._effects]
        new_instantaneous_action._fluents_assigned = action._fluents_assigned.copy()
        new_instantaneous_action._fluents_inc_dec = action._fluents_inc_dec.copy()
        new_instantaneous_action._simulated_effect = action._simulated_effect
        return new_instantaneous_action
