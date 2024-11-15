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


from typing import OrderedDict
import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_example_problems():
    problems = {}
    # the more generic interpreted functions are defined at the start and used in more test cases
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
    s_simple_always_false["ind"] = BoolType()
    IF_simple_always_false = InterpretedFunction(
        "simple_always_false", BoolType(), s_simple_always_false, simple_always_false
    )

    g = Fluent("g", IntType(0, 20))
    ione = Fluent("ione", IntType(0, 20))
    itwo = Fluent("itwo", IntType(0, 20))
    ithree = Fluent("ithree", IntType(0, 20))
    ifour = Fluent("ifour", BoolType())
    a = InstantaneousAction("a")
    a.add_precondition(And(IF_integers_to_bool(ione, itwo), LT(ione, 15)))
    a.add_precondition(LT(g, 10))
    a.add_effect(g, Plus(g, 3))
    b = InstantaneousAction("b")
    b.add_precondition(
        And(
            And(IF_integers_to_bool(itwo, itwo), GT(IF_simple_int_to_int(ithree), 5)),
            True,
        )
    )
    b.add_effect(g, Plus(g, 5))
    c = InstantaneousAction("c")
    c.add_effect(ione, Plus(ione, 1))
    d = InstantaneousAction("d")
    d.add_effect(ione, Minus(ione, 1))
    e = InstantaneousAction("e")
    e.add_precondition(IF_simple_always_false(ifour))
    e.add_effect(g, 5)
    f = InstantaneousAction("f")
    f.add_precondition(And(GT(ione, IF_simple_int_to_int(ithree))))
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
    problem.set_initial_value(ifour, False)
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

    def time_to_go_home(israining, basetime):
        r = basetime
        if israining:
            r = r * 2
        return r

    signature_time_to_go_home = OrderedDict()
    signature_time_to_go_home["israining"] = BoolType()
    signature_time_to_go_home["basetime"] = IntType()
    time_to_go_home_if = InterpretedFunction(
        "time_to_go_home", IntType(), signature_time_to_go_home, time_to_go_home
    )

    def wet(israining, haveumbrella):
        r = False
        if israining and not haveumbrella:
            r = True
        return r

    signature_wet_if = OrderedDict()
    signature_wet_if["israining"] = BoolType()
    signature_wet_if["haveumbrella"] = BoolType()
    wet_if = InterpretedFunction("wet_if", BoolType(), signature_wet_if, wet)
    athome = Fluent("athome")
    atwork = Fluent("atwork")
    wet_clothes = Fluent("wet_clothes")
    house_wet = Fluent("house_wet")
    rain = Fluent("rain")
    have_umbrella = Fluent("have_umbrella")
    normaltime = Fluent("normaltime", IntType(0, 20))
    gohome = DurativeAction("gohome")
    # when you go home
    gohome.add_condition(StartTiming(), Not(athome))
    gohome.add_condition(StartTiming(), atwork)
    # you start from work
    gohome.add_effect(StartTiming(), atwork, False)
    # you leave work
    gohome.add_effect(EndTiming(), athome, True)
    # and you will end up at home
    gohome.add_effect(EndTiming(), house_wet, wet_clothes)
    # if your clothes are wet you will wet your house
    gohome.add_effect(StartTiming(), wet_clothes, wet_if(rain, have_umbrella))
    # if it rains and you don't have an umbrella you will wet your clothes
    gohome.set_fixed_duration(time_to_go_home_if(rain, normaltime))
    # it takes longer if it's raining
    takeumbrella = DurativeAction("takeumbrella")
    takeumbrella.add_condition(StartTiming(), atwork)
    # take the umbrella when you still are at work
    takeumbrella.add_effect(EndTiming(), have_umbrella, True)
    takeumbrella.set_fixed_duration(1)
    problem = Problem("go_home_with_rain_and_interpreted_functions")
    problem.add_fluent(athome)
    problem.add_fluent(atwork)
    problem.add_fluent(house_wet)
    problem.add_fluent(wet_clothes)
    problem.add_fluent(rain)
    problem.add_fluent(have_umbrella)
    problem.add_fluent(normaltime)
    problem.add_action(gohome)
    problem.add_action(takeumbrella)
    problem.set_initial_value(have_umbrella, False)
    problem.set_initial_value(wet_clothes, False)
    problem.set_initial_value(athome, False)
    problem.set_initial_value(atwork, True)
    problem.set_initial_value(house_wet, False)
    problem.set_initial_value(rain, True)
    problem.set_initial_value(normaltime, 10)
    problem.add_goal(And(athome, Not(house_wet)))

    ifproblem = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=[
            up.plans.TimeTriggeredPlan(
                [
                    (Fraction(0), takeumbrella(), Fraction(1)),
                    (Fraction(101, 100), gohome(), Fraction(20)),
                ]
            ),
        ],
        invalid_plans=[
            up.plans.TimeTriggeredPlan([(Fraction(0), gohome(), Fraction(1, 1))]),
        ],
    )
    problems["go_home_with_rain_and_interpreted_functions"] = ifproblem

    def if_cut_a_slice(in_val):
        out_val = Fraction(0, 1)
        if in_val >= Fraction(1, 8):
            out_val = Fraction(in_val - Fraction(1, 8))
        return out_val

    def if_is_there_enough_pizza(in_val):
        if in_val >= Fraction(1, 8):
            return True
        else:
            return False

    signature_if_both = OrderedDict()
    signature_if_both["i_one"] = RealType()
    if_cut = InterpretedFunction(
        "if_cut", RealType(), signature_if_both, if_cut_a_slice
    )
    if_available = InterpretedFunction(
        "if_available", BoolType(), signature_if_both, if_is_there_enough_pizza
    )

    pizza = Fluent("pizza", RealType())
    hunger = Fluent("hunger", IntType())
    slices = Fluent("slices", IntType())

    buy = InstantaneousAction("buy")
    buy.add_effect(pizza, 1)

    cut = InstantaneousAction("cut")
    cut.add_effect(pizza, if_cut(pizza))
    cut.add_effect(slices, Plus(slices, 1))
    cut.add_precondition(if_available(pizza))

    eat = InstantaneousAction("eat")
    eat.add_effect(hunger, Minus(hunger, 1))
    eat.add_effect(slices, Minus(slices, 1))
    eat.add_precondition(GT(slices, 0))

    problem = Problem("if_reals_condition_effect_pizza")
    problem.add_fluent(pizza)
    problem.add_fluent(hunger)
    problem.add_fluent(slices)
    problem.add_action(eat)
    problem.add_action(cut)
    problem.add_action(buy)
    problem.set_initial_value(pizza, Fraction(1, 8))
    problem.set_initial_value(hunger, 11)
    problem.set_initial_value(slices, 0)
    problem.add_goal(LE(hunger, 0))
    ifproblem = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=[
            up.plans.SequentialPlan(
                [
                    cut(),
                    eat(),
                    buy(),
                    cut(),
                    eat(),
                    cut(),
                    eat(),
                    cut(),
                    eat(),
                    cut(),
                    eat(),
                    cut(),
                    eat(),
                    cut(),
                    eat(),
                    cut(),
                    eat(),
                    cut(),
                    eat(),
                    buy(),
                    cut(),
                    eat(),
                    cut(),
                    eat(),
                ]
            )
        ],
        invalid_plans=[
            up.plans.SequentialPlan([eat()]),
        ],
    )
    problems["if_reals_condition_effect_pizza"] = ifproblem

    return problems
