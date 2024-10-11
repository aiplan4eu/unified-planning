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


from typing import OrderedDict
import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_example_problems():
    problems = {}
    # the interpreted functions are defined at the start and used in more test cases
    def simple_integers_to_bool(ina, inb):
        return (ina * inb) == 60

    s_simple_integers_to_bool = OrderedDict()
    s_simple_integers_to_bool["ina"] = IntType()
    s_simple_integers_to_bool["inb"] = IntType()
    IF_integers_to_bool = InterpretedFunction(
        "integers_to_bool",
        BoolType(),
        s_simple_integers_to_bool,
        simple_integers_to_bool,
    )

    def simple_int_to_int(inc):
        retval = inc - 2
        return retval

    s_simple_int_to_int = OrderedDict()
    s_simple_int_to_int["inc"] = IntType()
    IF_simple_int_to_int = InterpretedFunction(
        "simple_int_to_int", IntType(), s_simple_int_to_int, simple_int_to_int
    )

    def simple_always_false(ind):
        return False

    s_simple_always_false = OrderedDict()
    s_simple_always_false["ind"] = IntType()
    IF_simple_always_false = InterpretedFunction(
        "simple_always_false", BoolType(), s_simple_always_false, simple_always_false
    )

    g = Fluent("g", IntType(0, 20))
    ione = Fluent("ione", IntType(0, 20))
    itwo = Fluent("itwo", IntType(0, 20))
    ithree = Fluent("ithree", IntType(0, 20))
    ifour = Fluent("ifour", IntType(0, 20))
    a = InstantaneousAction("a")
    a.add_precondition(And(IF_integers_to_bool(ione, itwo), LT(ione, 15)))
    a.add_precondition(LT(g, 10))
    a.add_effect(g, Plus(g, 3))
    b = InstantaneousAction("b")
    b.add_precondition(
        And(
            And(IF_integers_to_bool(itwo, itwo), GT(simple_int_to_int(ithree), 5)), True
        )
    )
    b.add_effect(g, Plus(g, 5))
    c = InstantaneousAction("c")
    c.add_effect(ione, Plus(ione, 1))
    d = InstantaneousAction("d")
    d.add_effect(ione, Minus(ione, 1))
    e = InstantaneousAction("e")
    e.add_precondition(simple_always_false(ifour))
    e.add_effect(g, 5)
    f = InstantaneousAction("f")
    f.add_precondition(And(GT(ione, simple_int_to_int(ithree))))
    f.add_effect(itwo, 5)
    problem = Problem("IF_in_conditions_complex_1")
    problem.add_fluent(g)
    problem.add_fluent(ione)
    problem.add_fluent(itwo)
    problem.add_fluent(ithree)
    problem.add_fluent(ifour)
    problem.add_action(a)
    problem.add_action(b)
    problem.add_action(c)
    problem.add_action(d)
    problem.add_action(e)
    problem.add_action(f)
    problem.set_initial_value(g, 1)
    problem.set_initial_value(ione, 11)
    problem.set_initial_value(itwo, 1)
    problem.set_initial_value(ithree, 15)
    problem.set_initial_value(ifour, 15)
    problem.add_goal(GE(g, 5))

    ifproblem = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=[
            up.plans.SequentialPlan([c(), c(), c(), f(), d(), d(), a(), a()]),
        ],
        invalid_plans=[
            up.plans.SequentialPlan([b()]),
        ],
    )
    problems["IF_in_conditions_complex_1"] = ifproblem

    return problems
