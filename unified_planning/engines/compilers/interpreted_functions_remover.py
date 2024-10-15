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
from unified_planning.model.timing import StartTiming
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
            if isinstance(a, InstantaneousAction):
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
                allifs: list = list()
                allifs.clear()
                for p in fixed_preconditions:  # for each precondition
                    IFs = self.interpreted_functions_extractor.get(p)
                    if len(IFs) != 0:  # get all the IFs in the precondition
                        for f in IFs:
                            if f not in allifs:
                                # and append them in the key list if not already there
                                allifs.append(f)
                if len(allifs) != 0:

                    ifaskeys: list = list()
                    ifaskeys.clear()
                    for f in allifs:
                        ifaskeys.append(f.interpreted_function())

                    all_combinations_for_this_action = self.knowledge_combinations(
                        better_knowledge, ifaskeys
                    )

                    for kfc in all_combinations_for_this_action:
                        # for each possible combination (known function combinations)
                        new_action = a.clone()
                        new_action.name = get_fresh_name(new_problem, a.name)
                        for kf in kfc:

                            subhere: up.model.walkers.Substituter = (
                                up.model.walkers.Substituter(new_action.environment)
                            )

                            subdict = dict()
                            tempfun = None
                            for fun in allifs:

                                if fun.interpreted_function().__eq__(
                                    kf.interpreted_function()
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

                                test = subhere.substitute(pre, subdict)
                                pre = test
                                new_action.add_precondition(pre)

                            argumentcounter = 0
                            new_condition = None
                            new_precondition_list = list()
                            while argumentcounter < len(kf.args):
                                for aif in allifs:
                                    if aif.interpreted_function().__eq__(
                                        kf.interpreted_function()
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
                                                # is this ok?
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
                                                # is this ok?
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
                            new_action.add_precondition(new_condition)
                            base_not_precondition = (
                                no_IF_action_base.environment.expression_manager.Not(
                                    new_condition
                                )
                            )
                            no_IF_action_base.add_precondition(base_not_precondition)

                            no_IF_action_preconditions_list.append(
                                new_precondition_list
                            )

                        new_to_old[new_action] = a
                        new_problem.add_action(new_action)
                    no_IF_action_base.name = get_fresh_name(new_problem, a.name)
                    new_to_old[no_IF_action_base] = a
                    new_problem.add_action(no_IF_action_base)
                else:
                    new_to_old[a] = a
                    new_problem.add_action(a)

            elif isinstance(a, DurativeAction):
                no_IF_action = a.clone()
                minduration: FNode | int = 1
                maxduration: FNode | int = 1000000
                IF_in_durations = list()
                IF_in_conditions = list()

                if not (
                    OperatorKind.INTERPRETED_FUNCTION_EXP
                    in self.operators_extractor.get(a.duration.lower)
                ):
                    minduration = a.duration.lower
                else:
                    IFs = self.interpreted_functions_extractor.get(a.duration.lower)
                    if len(IFs) != 0:
                        for f in IFs:
                            if f not in IF_in_durations:
                                IF_in_durations.append(f)
                IFs = None
                if not (
                    OperatorKind.INTERPRETED_FUNCTION_EXP
                    in self.operators_extractor.get(a.duration.upper)
                ):
                    maxduration = a.duration.upper
                else:
                    IFs = self.interpreted_functions_extractor.get(a.duration.upper)
                    if len(IFs) != 0:
                        for f in IFs:
                            if f not in IF_in_durations:
                                IF_in_durations.append(f)

                no_IF_action.set_closed_duration_interval(minduration, maxduration)

                no_IF_action.clear_conditions()
                fixed_conditions = []
                fixed_conditions_i = []
                for ii, cl in a.conditions.items():
                    for c in cl:
                        templist = self._fix_precondition(c)
                        for fc in templist:
                            fixed_conditions.append(fc)
                            fixed_conditions_i.append(ii)
                # print(fixed_conditions)
                # print(fixed_conditions_i)
                condcounter = 0
                while condcounter < len(fixed_conditions):
                    if not (
                        OperatorKind.INTERPRETED_FUNCTION_EXP
                        in self.operators_extractor.get(fixed_conditions[condcounter])
                    ):
                        no_IF_action.add_condition(
                            fixed_conditions_i[condcounter],
                            fixed_conditions[condcounter],
                        )
                    else:
                        IFs = None
                        IFs = self.interpreted_functions_extractor.get(
                            fixed_conditions[condcounter]
                        )
                        if len(IFs) != 0:  # get all the IFs in the precondition
                            for f in IFs:
                                if f not in IF_in_conditions:
                                    # and append them in the key list if not already there
                                    IF_in_conditions.append(f)
                    condcounter = +1

                # print(IF_in_durations)
                # print(IF_in_conditions)
                # print(self._interpreted_functions_values)
                all_combinations_for_this_action = OrderedDict()
                allifs: list = list()
                allifs.clear()
                IFkeys_in_durations = []
                IFkeys_in_conditions = []
                for ifid in IF_in_durations:
                    if ifid not in allifs:
                        allifs.append(ifid)
                        IFkeys_in_durations.append(ifid.interpreted_function())
                for ific in IF_in_conditions:
                    if ific not in allifs:
                        allifs.append(ific)
                        IFkeys_in_conditions.append(ific.interpreted_function())

                if len(allifs) != 0:
                    ifaskeys: list = list()
                    ifaskeys.clear()
                    for f in allifs:
                        ifaskeys.append(f.interpreted_function())
                    all_combinations_for_this_action = self.knowledge_combinations(
                        better_knowledge, ifaskeys
                    )

                    for kfc in all_combinations_for_this_action:
                        new_action = a.clone()
                        new_action.name = get_fresh_name(new_problem, a.name)
                        new_condition = None
                        for kf in kfc:

                            subhere: up.model.walkers.Substituter = (
                                up.model.walkers.Substituter(new_action.environment)
                            )

                            subdict = dict()
                            tempfun = None
                            for fun in allifs:

                                if fun.interpreted_function().__eq__(
                                    kf.interpreted_function()
                                ):
                                    subdict[fun] = self._interpreted_functions_values[
                                        kf
                                    ]

                            if len(subdict) == 0:
                                print(
                                    "sub dict is empty ;-;\nif you got here it means there is a bug in the code"
                                )

                            preconditions_to_substitute_list = new_action.conditions
                            new_action.clear_conditions()
                            print("durative - substitution dictionary is")
                            print(subdict)
                            for ii, cl in preconditions_to_substitute_list.items():
                                for c in cl:

                                    test = subhere.substitute(c, subdict)
                                    c = test
                                    new_action.add_condition(ii, c)
                            test = subhere.substitute(
                                new_action.duration.upper, subdict
                            )
                            new_maxduration = test
                            test = subhere.substitute(
                                new_action.duration.lower, subdict
                            )
                            new_minduration = test

                            new_action.set_closed_duration_interval(
                                new_minduration, new_maxduration
                            )
                            argumentcounter = 0

                            new_condition = None
                            new_precondition_list = list()
                            while argumentcounter < len(kf.args):
                                for aif in allifs:
                                    if aif.interpreted_function().__eq__(
                                        kf.interpreted_function()
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
                                                # is this ok?
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
                                                # is this ok?
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
                            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                            #!!!!!THIS PUTS ALL CONDITIONS ON START TIME!!!!!!!!
                            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                            #!!!!!THIS PUTS ALL CONDITIONS ON START TIME!!!!!!!!
                            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                            #!!!!!THIS PUTS ALL CONDITIONS ON START TIME!!!!!!!!
                            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                            #!!!!!THIS PUTS ALL CONDITIONS ON START TIME!!!!!!!!
                            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                            # print("kf and if in durations")
                            # print(kf)
                            # print(IF_in_durations)
                            if kf.interpreted_function() in IFkeys_in_durations:
                                print(
                                    "this if was in a duration, condition should apply at start time"
                                )

                                new_action.add_condition(StartTiming(), new_condition)
                            else:
                                print("for now all other cases are at starttime")
                                new_action.add_condition(StartTiming(), new_condition)

                            base_not_precondition = (
                                no_IF_action.environment.expression_manager.Not(
                                    new_condition
                                )
                            )
                            no_IF_action.add_condition(
                                StartTiming(), base_not_precondition
                            )

                            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                            #!!!!!THIS PUTS ALL CONDITIONS ON START TIME!!!!!!!!
                            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                            #!!!!!THIS PUTS ALL CONDITIONS ON START TIME!!!!!!!!
                            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                            #!!!!!THIS PUTS ALL CONDITIONS ON START TIME!!!!!!!!
                            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                            #!!!!!THIS PUTS ALL CONDITIONS ON START TIME!!!!!!!!
                            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

                        new_to_old[new_action] = a
                        new_problem.add_action(new_action)
                    # no_IF_action.add_condition(StartTiming(), condition_to_avoid_for_duration_purposes)
                    no_IF_action.name = get_fresh_name(new_problem, a.name)
                    new_to_old[no_IF_action] = a
                    new_problem.add_action(no_IF_action)
                else:
                    new_to_old[a] = a
                    new_problem.add_action(a)
            else:
                raise NotImplementedError
        print("compilation complete!")
        # print(new_problem)
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
            print("len is zero womp womp")
            return d
        akl = None
        if kl is None:
            akl = d.keys()
        else:
            akl = self.intersection(kl, d.keys())
        if len(akl) == 0:
            print("calculated length is zero womp womp")
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
