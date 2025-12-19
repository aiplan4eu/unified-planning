# Copyright 2024 Unified Planning library and its maintainers
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


import pytest
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model import GlobalStartTiming
from unified_planning.model.problem_kind import (
    classical_kind,
    full_classical_kind,
    basic_temporal_kind,
)
from unified_planning.test import skipIfEngineNotAvailable, unittest_TestCase, main
from unified_planning.test import (
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.engines.compilers import ConditionalEffectsRemover
from unified_planning.engines.compilers.interpreted_functions_remover import (
    InterpretedFunctionsRemover,
)
from unified_planning.engines import CompilationKind
from collections import OrderedDict


class TestInterpretedFunctionsRemover(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_expected_kind(self):

        problem1 = self.problems["interpreted_functions_in_conditions"].problem
        problem2 = self.problems["go_home_with_rain_and_interpreted_functions"].problem
        problem3 = self.problems["if_reals_condition_effect_pizza"].problem
        with Compiler(
            problem_kind=problem1.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            kind1 = if_remover.resulting_problem_kind(
                problem1.kind, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
            self.assertTrue(problem1.kind.has_interpreted_functions_in_conditions())
            self.assertFalse(kind1.has_interpreted_functions_in_conditions())
        with Compiler(
            problem_kind=problem2.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            kind2 = if_remover.resulting_problem_kind(
                problem2.kind, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
            self.assertTrue(problem2.kind.has_interpreted_functions_in_durations())
            self.assertFalse(kind2.has_interpreted_functions_in_durations())
        with Compiler(
            problem_kind=problem3.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            kind3 = if_remover.resulting_problem_kind(
                problem2.kind, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
            self.assertTrue(
                problem3.kind.has_interpreted_functions_in_numeric_assignments()
            )
            self.assertFalse(kind3.has_interpreted_functions_in_numeric_assignments())

    def test_interpreted_functions_in_preconditions_remover_simple(self):
        problem = self.problems["interpreted_functions_in_conditions"].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            ifr = if_remover.compile(
                problem, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
        compiled_problem = ifr.problem

        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())
        self.assertTrue(problem.kind.has_general_numeric_planning())
        self.assertFalse(
            compiled_problem.kind.has_interpreted_functions_in_conditions()
        )

        self.assertTrue(compiled_problem.kind.has_general_numeric_planning())

    def test_interpreted_functions_in_preconditions_remover_always_impossible(self):
        problem = self.problems[
            "interpreted_functions_in_conditions_always_impossible"
        ].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            ifr = if_remover.compile(
                problem, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
        compiled_problem = ifr.problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())
        self.assertFalse(
            compiled_problem.kind.has_interpreted_functions_in_conditions()
        )

    def test_interpreted_functions_in_durative_conditions_remover(self):
        problem = self.problems["interpreted_functions_in_durative_conditions"].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            ifr = if_remover.compile(
                problem, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
        compiled_problem = ifr.problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(
            compiled_problem.kind.has_interpreted_functions_in_conditions()
        )

    def test_interpreted_functions_in_durations_remover(self):

        problem = self.problems["go_home_with_rain_and_interpreted_functions"].problem
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            expectedkind = if_remover.resulting_problem_kind(
                problem.kind, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
            ifr = if_remover.compile(
                problem, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
        compiled_problem = ifr.problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_durations())
        self.assertTrue(expectedkind.has_int_type_durations())
        self.assertFalse(expectedkind.has_interpreted_functions_in_durations())
        self.assertFalse(compiled_problem.kind.has_interpreted_functions_in_durations())
        self.assertTrue(problem.kind.has_interpreted_functions_in_boolean_assignments())
        self.assertFalse(
            compiled_problem.kind.has_interpreted_functions_in_boolean_assignments()
        )
        self.assertFalse(
            compiled_problem.kind.has_interpreted_functions_in_numeric_assignments()
        )

    def test_interpreted_function_remover_quantifier(self):
        sem = UserType("Semaphore")
        x = Fluent("x")

        def y_callable(semaphore):
            return False

        signature_map = OrderedDict()
        signature_map["semaphore"] = sem

        y = InterpretedFunction("y", BoolType(), signature_map, y_callable)

        o1 = Object("o1", sem)
        o2 = Object("o2", sem)
        s_var = Variable("s", sem)
        a = InstantaneousAction("a")
        a.add_precondition(Exists(InterpretedFunctionExp(y, [s_var]), s_var))
        a.add_effect(x, True)
        basic_exists_if = Problem("basic_exists_if")
        basic_exists_if.add_fluent(x)
        basic_exists_if.add_object(o1)
        basic_exists_if.add_object(o2)
        basic_exists_if.add_action(a)
        basic_exists_if.set_initial_value(x, False)

        c_a = InstantaneousAction("a")
        c_a.add_effect(x, True)

        with InterpretedFunctionsRemover() as if_remover:
            ifr = if_remover.compile(
                basic_exists_if, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
            self.assertEqual(ifr.problem.action("a"), c_a)

        k_t = {}
        if_exp_1 = InterpretedFunctionExp(y, [o1])
        if_exp_2 = InterpretedFunctionExp(y, [o2])
        k_t[if_exp_1] = TRUE()
        k_t[if_exp_2] = TRUE()

        knum_y = UserType("kNum_y")

        with InterpretedFunctionsRemover(k_t) as if_remover:
            # we can check with just one knowledge case as the action is compiled the same way
            # what changes are the initial values of the _f_y fluent
            ifr = if_remover.compile(
                basic_exists_if, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
            par_1 = Parameter("_p_y_1", knum_y)
            exp_12_right = ObjectExp(Object("_o_kNum_y", knum_y))
            par_2 = Parameter("_p_y_2", knum_y)
            exp_3_f = Fluent("_f_y", BoolType(), p=knum_y)

            # the order of the arguments in the expressions can change with no real difference
            # but this means we can't just check that they are Equal
            es_eq_diff_args = set([ParameterExp(par_1), ParameterExp(par_2)])
            es_eq_common_arg = exp_12_right
            e_or_args = set([FluentExp(exp_3_f, [par_1]), FluentExp(exp_3_f, [par_2])])

            self.assertEqual(len(ifr.problem.action("a").preconditions), 3)
            for condition in ifr.problem.action("a").preconditions:
                self.assertEqual(len(condition.args), 2)
                if condition.is_or():
                    for arg in condition.args:
                        self.assertIn(arg, e_or_args)
                        e_or_args.remove(arg)
                elif condition.is_equals():
                    found_common = False
                    for arg in condition.args:
                        if (arg == es_eq_common_arg) and not found_common:
                            found_common = True
                        else:
                            self.assertIn(arg, es_eq_diff_args)
                            es_eq_diff_args.remove(arg)
                else:
                    assert False
