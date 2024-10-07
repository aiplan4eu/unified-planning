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

from collections import OrderedDict
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.model.interpreted_function import InterpretedFunction
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

    def __init__(
        self, interpreted_functions_values=None
    ):  # IF_values - va aggiunto qui
        engines.engine.Engine.__init__(self)
        self.operators_extractor: up.model.walkers.OperatorsExtractor = (
            up.model.walkers.OperatorsExtractor()
        )
        self.interpreted_functions_extractor: up.model.walkers.InterpretedFunctionsExtractor = (
            up.model.walkers.InterpretedFunctionsExtractor()
        )
        self._interpreted_functions_values = interpreted_functions_values
        # print("what we got in I_F_V")
        # print(self._interpreted_functions_values)
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
        # print("what we got in I_F_V")
        # print(self._interpreted_functions_values)

        new_to_old: Dict[Action, Optional[Action]] = {}
        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_actions()
        better_knowledge = self.elaborate_known_IFs(self._interpreted_functions_values)
        knowledge_with_placeholders = self.add_empty_knowledge_values(better_knowledge)
        combined_knowledge = self.knowledge_combinations(knowledge_with_placeholders)

        # better way: function comb (dict, list of keys to combine) -> combination of those keys
        print("combinations of functions knowledge:")
        for debugprintstuff in combined_knowledge:
            print(debugprintstuff)
        for a in problem.actions:
            if isinstance(a, InstantaneousAction):
                no_IF_action = a.clone()
                no_IF_action.name = get_fresh_name(new_problem, a.name)
                no_IF_action.clear_preconditions()
                fixed_preconditions = []
                for p in a.preconditions:
                    templist = self._fix_precondition(p)
                    fixed_preconditions.extend(templist)
                for p in fixed_preconditions:
                    IFs = self.interpreted_functions_extractor.get(p)
                    if len(IFs) == 0:
                        no_IF_action.add_precondition(p)

                found_to_substitute = list()
                new_vals_to_substitute = list()
                for p in fixed_preconditions:  # for each precondition
                    IFs = self.interpreted_functions_extractor.get(p)
                    if len(IFs) != 0:  # get all the IFs in the precondition
                        # print(knowledge_with_placeholders.keys())
                        print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
                        print("now on action")
                        print(a)
                        print("with knowledge")
                        print(self._interpreted_functions_values)
                        ifaskeys = list()
                        ifaskeys.clear()
                        for f in IFs:
                            # print (f._content.payload)
                            ifaskeys.append(f._content.payload)
                        print("this action contains IFs:")
                        print(ifaskeys)
                        thisfcombine = self.knowledge_combinations(
                            knowledge_with_placeholders, ifaskeys
                        )
                        print("if combinations")
                        print(thisfcombine)
                        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

                        print("kfc iterating on")
                        print(thisfcombine)
                        for kfc in thisfcombine:
                            # for each possible combination (known function combinations)
                            print("kf iterating on")
                            print(kfc)
                            for kf in kfc:
                                # for each known function in the combination
                                for f in IFs:
                                    print("f and kf")
                                    print(f)
                                    print(kf)
                                    if f._content.payload.__eq__(kf):
                                        print("placeholder found")
                                    elif f._content.payload.__eq__(kf._content.payload):
                                        print("known value found")
                        # ----------old code undere here-------------------------------------
                        for f in IFs:  # for each of those IFs

                            for key in self._interpreted_functions_values:
                                if f._content.payload.__eq__(key._content.payload):
                                    found_to_substitute.append(f._content.args)
                                    new_vals_to_substitute.append(key._content.args)

                                    # print (f._content.args) # this is as expected
                                    # print (key._content.args) # this is as expected
                                    # print (f._content.payload) # this is as expected
                                    # print (key._content.payload) # this is as expected

                                    # here we should clone the initial action
                                    a_known_value = a.clone()
                                    # make a condition where the values correspond with the current values in f._content.args and key._content.args
                                    # essentially the new action must have f._content.args == key._content.args
                                    argindex = 0
                                    new_condition = None
                                    errorfound = False
                                    if len(f._content.args) != len(key._content.args):
                                        errorfound = True
                                        print("you should not be here")
                                    while (argindex < len(f._content.args)) and not (
                                        errorfound
                                    ):
                                        if argindex == 0:
                                            new_condition = no_IF_action.environment.expression_manager.Equals(
                                                f._content.args[argindex],
                                                key._content.args[argindex],
                                            )
                                        else:
                                            new_condition = no_IF_action.environment.expression_manager.And(
                                                new_condition,
                                                no_IF_action.environment.expression_manager.Equals(
                                                    f._content.args[argindex],
                                                    key._content.args[argindex],
                                                ),
                                            )

                                        argindex = argindex + 1
                                    # print(new_condition) # this is as expected
                                    # add the precondition
                                    a_known_value.add_precondition(new_condition)
                                    # substitute the instance of the function with its result
                                    # function instance is: f._content.payload or key._content.payload - they should be the same
                                    # result is: self._interpreted_functions_values[key]
                                    # print (f.is_interpreted_function_exp()) # this is the expression
                                    # add the new action to the problem

                                    # add the new action to the map

                j = 0
                errorfound = False
                if len(found_to_substitute) != len(new_vals_to_substitute):
                    errorfound = True
                    print("you should not be here")
                while (j < len(found_to_substitute)) and not (errorfound):
                    i = 0
                    new_condition = None
                    key = found_to_substitute[j]
                    while i < len(key):
                        if i == 0:
                            new_condition = (
                                no_IF_action.environment.expression_manager.Equals(
                                    key[i], new_vals_to_substitute[j][i]
                                )
                            )
                        else:
                            new_condition = (
                                no_IF_action.environment.expression_manager.And(
                                    new_condition,
                                    no_IF_action.environment.expression_manager.Equals(
                                        key[i], new_vals_to_substitute[j][i]
                                    ),
                                )
                            )

                        i = i + 1
                    new_condition = no_IF_action.environment.expression_manager.Not(
                        new_condition
                    )
                    # print (new_condition)
                    no_IF_action.add_precondition(new_condition)
                    j = j + 1
                new_to_old[no_IF_action] = a

                # print("---------------processed action----------------")
                # print(no_IF_action)
            elif isinstance(a, DurativeAction):
                no_IF_action = a.clone()
                if (
                    OperatorKind.INTERPRETED_FUNCTION_EXP
                    in self.operators_extractor.get(a.duration.lower)
                ) or (
                    OperatorKind.INTERPRETED_FUNCTION_EXP
                    in self.operators_extractor.get(a.duration.upper)
                ):

                    no_IF_action.set_closed_duration_interval(1, 1000000)

                no_IF_action.name = get_fresh_name(new_problem, a.name)
                no_IF_action.clear_conditions()
                for ii, cl in a.conditions.items():

                    fixed_conditions = []
                    for c in cl:
                        templist = self._fix_precondition(c)
                        fixed_conditions.extend(templist)
                    for fc in fixed_conditions:

                        precondition_operators = self.operators_extractor.get(fc)
                        if not (
                            OperatorKind.INTERPRETED_FUNCTION_EXP
                            in precondition_operators
                        ):
                            no_IF_action.add_condition(ii, fc)
                new_to_old[no_IF_action] = a
            else:
                raise NotImplementedError

            new_problem.add_action(no_IF_action)

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )

    def elaborate_known_IFs(self, ifvs):
        # print ("now elaborating (>.<)")
        bk: OrderedDict = OrderedDict()
        for f in ifvs:
            # print (f._content.payload)
            # print (bk.keys())
            # print (ifvs[f])
            if not (f._content.payload in bk.keys()):
                bk[f._content.payload] = OrderedDict()
                # bk[f._content.payload]["placeholder_f_and_vnames"] = "placeholder_outval"
                # placeholdernode = InterpretedFunction (f._content.payload.name)
                # print (f._content.payload.name)
                # bk[f._content.payload]["placeholder_unknown_val"] = f._content.payload
            bk[f._content.payload][f] = ifvs[f]

        return bk

    def knowledge_combinations(self, d, kl=None):
        # print ("now in combination function+++++++++++++++++++++++++++=")
        # print (d)
        if len(d) == 0:
            print("empty d")
            return d
        akl = None
        if kl is None:
            akl = d.keys()
        else:
            akl = self.intersection(kl, d.keys())
            # print (akl)
        if len(akl) == 0:
            print("our knowledge does not help us with this condition")
            empd = OrderedDict()
            return empd

        c = it.product(*(d[Name] for Name in akl))
        return list(c)

    def add_empty_knowledge_values(self, d):
        for key in d:
            d[key][key] = key
        return d

    def intersection(self, lst1, lst2):
        return list(set(lst1) & set(lst2))
