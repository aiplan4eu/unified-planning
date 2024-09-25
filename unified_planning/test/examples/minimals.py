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

    # basic
    x = Fluent("x")
    a = InstantaneousAction("a")
    a.add_precondition(Not(x))
    a.add_effect(x, True)
    problem = Problem("basic")
    problem.add_fluent(x)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.add_goal(x)
    plan = up.plans.SequentialPlan([up.plans.ActionInstance(a)])
    basic = TestCase(problem=problem, solvable=True, valid_plans=[plan])
    problems["basic"] = basic

    # basic conditional
    x = Fluent("x")
    y = Fluent("y")
    a_x = InstantaneousAction("a_x")
    a_y = InstantaneousAction("a_y")
    a_x.add_precondition(Not(x))
    a_x.add_effect(x, True, y)
    a_y.add_precondition(Not(y))
    a_y.add_effect(y, True)
    problem = Problem("basic_conditional")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(a_x)
    problem.add_action(a_y)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, False)
    problem.add_goal(x)
    plan = up.plans.SequentialPlan(
        [up.plans.ActionInstance(a_y), up.plans.ActionInstance(a_x)]
    )
    basic_conditional = TestCase(problem=problem, solvable=True, valid_plans=[plan])
    problems["basic_conditional"] = basic_conditional

    # basic oversubscription
    x = Fluent("x")
    a = InstantaneousAction("a")
    a.add_precondition(Not(x))
    a.add_effect(x, True)
    problem = Problem("basic_oversubscription")
    problem.add_fluent(x)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    qm = up.model.metrics.Oversubscription({FluentExp(x): 10})
    problem.add_quality_metric(qm)
    plan = up.plans.SequentialPlan([up.plans.ActionInstance(a)])
    basic_oversubscription = TestCase(
        problem=problem, solvable=True, valid_plans=[plan], optimum=10
    )
    problems["basic_oversubscription"] = basic_oversubscription

    # basic tils (timed initial literals)
    x = Fluent("x")
    y = Fluent("y")
    da = DurativeAction("a")
    da.set_fixed_duration(1)
    da.add_effect(EndTiming(), x, True)
    da.add_condition(TimeInterval(StartTiming(), EndTiming()), y)
    problem = Problem("basic_tils")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(da)
    problem.set_initial_value(x, False)
    problem.add_timed_effect(GlobalStartTiming(5), x, False)
    problem.set_initial_value(y, False)
    problem.add_timed_effect(GlobalStartTiming(2), y, True)
    problem.add_timed_effect(GlobalStartTiming(8), y, False)
    problem.add_goal(x)
    t_plan = up.plans.TimeTriggeredPlan([(Fraction(6), da(), Fraction(1))])
    invalid_t_plans: List[up.plans.Plan] = [
        # condition not established
        up.plans.TimeTriggeredPlan([(Fraction(1), da(), Fraction(1))]),
        # effect would be undone by TIL
        up.plans.TimeTriggeredPlan([(Fraction(3), da(), Fraction(1))]),
        # effect would collide with TIL
        up.plans.TimeTriggeredPlan([(Fraction(4), da(), Fraction(1))]),
        # condition not established
        up.plans.TimeTriggeredPlan([(Fraction(9), da(), Fraction(1))]),
    ]

    basic_tils = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=[t_plan],
        invalid_plans=invalid_t_plans,
    )
    problems["basic_tils"] = basic_tils

    # complex conditional
    fluent_a = Fluent("fluent_a")
    fluent_b = Fluent("fluent_b")
    fluent_c = Fluent("fluent_c")
    fluent_d = Fluent("fluent_d")
    fluent_k = Fluent("fluent_k")
    fluent_x = Fluent("fluent_x")
    fluent_y = Fluent("fluent_y")
    fluent_z = Fluent("fluent_z")
    a_act = InstantaneousAction("act")
    a_0_act = InstantaneousAction("act_0")
    a_1_act = InstantaneousAction("act_1")
    a_2_act = InstantaneousAction("act_2")
    a_act.add_precondition(Not(fluent_a))
    a_act.add_effect(fluent_a, TRUE())
    a_act.add_effect(fluent_k, TRUE(), fluent_b)
    a_act.add_effect(fluent_x, TRUE(), Not(fluent_c))
    a_act.add_effect(fluent_y, FALSE(), fluent_d)
    a_0_act.add_precondition(Not(fluent_a))
    a_0_act.add_precondition(fluent_d)
    a_0_act.add_effect(fluent_b, TRUE())
    a_1_act.add_precondition(Not(fluent_a))
    a_1_act.add_precondition(fluent_d)
    a_1_act.add_precondition(fluent_b)
    a_1_act.add_effect(fluent_c, FALSE(), fluent_c)
    a_1_act.add_effect(fluent_c, TRUE(), Not(fluent_c))
    a_2_act.add_effect(fluent_a, FALSE())
    a_2_act.add_effect(fluent_d, TRUE())
    a_2_act.add_effect(fluent_z, FALSE(), fluent_z)
    a_2_act.add_effect(fluent_z, TRUE(), Not(fluent_z))
    problem = Problem("complex_conditional")
    problem.add_fluent(fluent_a)
    problem.add_fluent(fluent_b)
    problem.add_fluent(fluent_c)
    problem.add_fluent(fluent_d)
    problem.add_fluent(fluent_k)
    problem.add_fluent(fluent_x)
    problem.add_fluent(fluent_y)
    problem.add_fluent(fluent_z)
    problem.add_action(a_act)
    problem.add_action(a_0_act)
    problem.add_action(a_1_act)
    problem.add_action(a_2_act)
    problem.set_initial_value(fluent_a, True)
    problem.set_initial_value(fluent_b, False)
    problem.set_initial_value(fluent_c, True)
    problem.set_initial_value(fluent_d, False)
    problem.set_initial_value(fluent_k, False)
    problem.set_initial_value(fluent_x, False)
    problem.set_initial_value(fluent_y, True)
    problem.set_initial_value(fluent_z, False)
    problem.add_goal(fluent_a)
    problem.add_goal(fluent_b)
    problem.add_goal(Not(fluent_c))
    problem.add_goal(fluent_d)
    problem.add_goal(fluent_k)
    problem.add_goal(fluent_x)
    problem.add_goal(Not(fluent_y))
    problem.add_goal(fluent_z)
    plan = up.plans.SequentialPlan(
        [
            up.plans.ActionInstance(a_2_act),
            up.plans.ActionInstance(a_0_act),
            up.plans.ActionInstance(a_1_act),
            up.plans.ActionInstance(a_act),
        ]
    )
    complex_conditional = TestCase(problem=problem, solvable=True, valid_plans=[plan])
    problems["complex_conditional"] = complex_conditional

    # basic without negative preconditions
    x = Fluent("x")
    y = Fluent("y")
    a = InstantaneousAction("a")
    a.add_precondition(y)
    a.add_effect(x, True)
    problem = Problem("basic_without_negative_preconditions")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, True)
    problem.add_goal(x)
    plan = up.plans.SequentialPlan([up.plans.ActionInstance(a)])
    basic_without_negative_preconditions = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
    problems[
        "basic_without_negative_preconditions"
    ] = basic_without_negative_preconditions

    # basic nested conjunctions
    problem = Problem("basic_nested_conjunctions")
    x = problem.add_fluent("x")
    y = problem.add_fluent("y")
    z = problem.add_fluent("z")
    j = problem.add_fluent("j")
    k = problem.add_fluent("k")

    a = InstantaneousAction("a")
    a.add_precondition(And(y, And(z, j, k)))
    a.add_effect(x, True)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, True)
    problem.set_initial_value(z, True)
    problem.set_initial_value(j, True)
    problem.set_initial_value(k, True)
    problem.add_goal(And(x, And(y, z, And(j, k))))
    plan = up.plans.SequentialPlan([up.plans.ActionInstance(a)])
    basic_nested_conjunctions = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
    problems["basic_nested_conjunctions"] = basic_nested_conjunctions

    # basic exists
    sem = UserType("Semaphore")
    x = Fluent("x")
    y = Fluent("y", BoolType(), semaphore=sem)
    o1 = Object("o1", sem)
    o2 = Object("o2", sem)
    s_var = Variable("s", sem)
    a = InstantaneousAction("a")
    a.add_precondition(Exists(FluentExp(y, [s_var]), s_var))
    a.add_effect(x, True)
    problem = Problem("basic_exists")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_object(o1)
    problem.add_object(o2)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y(o1), True)
    problem.set_initial_value(y(o2), False)
    problem.add_goal(x)
    plan = up.plans.SequentialPlan([up.plans.ActionInstance(a)])
    basic_exists = TestCase(problem=problem, solvable=True, valid_plans=[plan])
    problems["basic_exists"] = basic_exists

    # basic forall
    sem = UserType("Semaphore")
    x = Fluent("x")
    y = Fluent("y", BoolType(), semaphore=sem)
    s_var = Variable("s", sem)
    a = InstantaneousAction("a")
    a.add_precondition(Forall(Not(y(s_var)), s_var))
    a.add_effect(x, True)
    problem = Problem("basic_forall")
    problem.add_fluent(x)
    problem.add_fluent(y)
    o1 = problem.add_object("o1", sem)
    o2 = problem.add_object("o2", sem)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y(o1), False)
    problem.set_initial_value(y(o2), False)
    problem.add_goal(x)
    plan = up.plans.SequentialPlan([up.plans.ActionInstance(a)])
    basic_forall = TestCase(problem=problem, solvable=True, valid_plans=[plan])
    problems["basic_forall"] = basic_forall

    # temporal conditional
    Obj = UserType("Obj")
    is_same_obj = Fluent("is_same_obj", BoolType(), object_1=Obj, object_2=Obj)
    is_ok = Fluent("is_ok", BoolType(), test=Obj)
    is_ok_giver = Fluent("is_ok_giver", BoolType(), test=Obj)
    ok_given = Fluent("ok_given")
    set_giver = DurativeAction("set_giver", param_y=Obj)
    param_y = set_giver.parameter("param_y")
    set_giver.set_fixed_duration(2)
    set_giver.add_condition(StartTiming(), Not(is_ok_giver(param_y)))
    set_giver.add_effect(StartTiming(), is_ok_giver(param_y), True)
    set_giver.add_effect(EndTiming(), is_ok_giver(param_y), False)
    take_ok = DurativeAction("take_ok", param_x=Obj, param_y=Obj)
    param_x = take_ok.parameter("param_x")
    param_y = take_ok.parameter("param_y")
    take_ok.set_fixed_duration(3)
    take_ok.add_condition(StartTiming(), Not(is_ok(param_x)))
    take_ok.add_condition(StartTiming(), Not(is_ok_giver(param_y)))
    take_ok.add_condition(
        StartTiming(), Not(FluentExp(is_same_obj, [param_x, param_y]))
    )
    take_ok.add_effect(EndTiming(), is_ok(param_x), True, is_ok_giver(param_y))
    take_ok.add_effect(EndTiming(), ok_given, True)
    o1 = Object("o1", Obj)
    o2 = Object("o2", Obj)
    problem = Problem("temporal_conditional")
    problem.add_fluent(is_same_obj, default_initial_value=False)
    problem.add_fluent(is_ok, default_initial_value=False)
    problem.add_fluent(is_ok_giver, default_initial_value=False)
    problem.add_fluent(ok_given, default_initial_value=False)
    problem.add_action(set_giver)
    problem.add_action(take_ok)
    problem.add_object(o1)
    problem.add_object(o2)
    problem.add_goal(is_ok(o1))
    problem.set_initial_value(is_same_obj(o1, o1), True)
    problem.set_initial_value(is_same_obj(o2, o2), True)
    t_plan = up.plans.TimeTriggeredPlan(
        [
            (
                Fraction(0, 1),
                up.plans.ActionInstance(take_ok, (ObjectExp(o1), ObjectExp(o2))),
                Fraction(3, 1),
            ),
            (
                Fraction(1, 1),
                up.plans.ActionInstance(set_giver, (ObjectExp(o2),)),
                Fraction(2, 1),
            ),
        ]
    )
    temporal_conditional = TestCase(
        problem=problem, solvable=True, valid_plans=[t_plan]
    )
    problems["temporal_conditional"] = temporal_conditional

    # basic with actions cost
    x = Fluent("x")
    y = Fluent("y")
    act_a = InstantaneousAction("a")
    act_a.add_precondition(Not(x))
    act_a.add_effect(x, True)
    act_b = InstantaneousAction("act_b")
    act_b.add_precondition(Not(y))
    act_b.add_effect(y, True)
    act_c = InstantaneousAction("act_c")
    act_c.add_precondition(y)
    act_c.add_effect(x, True)
    problem = Problem("basic_with_costs")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(act_a)
    problem.add_action(act_b)
    problem.add_action(act_c)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, False)
    problem.add_goal(x)
    problem.add_quality_metric(
        up.model.metrics.MinimizeActionCosts(
            {act_a: Int(10), act_b: Int(1), act_c: Int(1)}
        )
    )
    plan = up.plans.SequentialPlan(
        [up.plans.ActionInstance(act_b), up.plans.ActionInstance(act_c)]
    )
    basic_with_costs = TestCase(
        problem=problem, solvable=True, valid_plans=[plan], optimum=2
    )
    problems["basic_with_costs"] = basic_with_costs

    # basic with defaults
    problem = Problem("basic_with_default_values")
    object = UserType("object")
    objects = [problem.add_object(f"o{i}", object) for i in range(0, 5)]
    available = Fluent("available", BoolType(), a=object)

    on = Fluent("on", object, a=object)
    problem.add_fluent(available, default_initial_value=True)
    problem.add_fluent(on, default_initial_value=objects[0])
    goal = problem.add_fluent("g", default_initial_value=False)
    for i in [0, 1, 3, 4]:  # override default for all but objects[2]
        problem.set_initial_value(on(objects[i]), objects[4])
    act_a = InstantaneousAction("a", obj=object)
    act_a.add_precondition(available(objects[0]))
    act_a.add_precondition(Equals(on(act_a.obj), objects[0]))
    act_a.add_effect(goal, True)
    problem.add_action(act_a)
    problem.add_goal(goal)

    problems["basic_with_default_values"] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=[up.plans.SequentialPlan([act_a(objects[2])])],
    )

    # counter
    counter_1 = Fluent("counter_1", IntType(0, 10))
    counter_2 = Fluent("counter_2", IntType(0, 10))
    fake_counter = Fluent("fake_counter", RealType(0, 10))
    increase = InstantaneousAction("increase")
    increase.add_increase_effect(counter_1, 1)
    increase.add_effect(counter_2, Plus(counter_2, 1))
    increase.add_effect(fake_counter, Div(Times(fake_counter, 2), 2))
    problem = Problem("counter")
    problem.add_fluent(counter_1)
    problem.add_fluent(counter_2)
    problem.add_fluent(fake_counter)
    problem.add_action(increase)
    problem.set_initial_value(counter_1, 0)
    problem.set_initial_value(counter_2, 0)
    problem.set_initial_value(fake_counter, 1)
    problem.add_goal(Iff(LT(fake_counter, counter_1), LT(counter_2, 3)))
    plan = up.plans.SequentialPlan(
        [up.plans.ActionInstance(increase), up.plans.ActionInstance(increase)]
    )
    counter = TestCase(problem=problem, solvable=True, valid_plans=[plan])
    problems["counter"] = counter

    # counter to 50
    counter_f = Fluent("counter", IntType(0, 100))
    increase = InstantaneousAction("increase")
    increase.add_increase_effect(counter_f, 1)
    problem = Problem("counter_to_50")
    problem.add_fluent(counter_f)
    problem.add_action(increase)
    problem.set_initial_value(counter_f, 0)
    problem.add_goal(Equals(counter_f, 50))
    # Make a plan of 50 action instances of "increase"
    plan = up.plans.SequentialPlan(
        [up.plans.ActionInstance(increase) for _ in range(50)]
    )
    counter_to_50 = TestCase(problem=problem, solvable=True, valid_plans=[plan])
    problems["counter_to_50"] = counter_to_50

    # temporal counter
    counter_f = Fluent("counter", IntType(0, 100))
    d_increase = DurativeAction("increase")
    d_increase.set_fixed_duration(1)
    d_increase.add_condition(StartTiming(), LT(counter_f, 99))
    d_increase.add_increase_effect(EndTiming(), counter_f, 2)
    d_decrease = DurativeAction("decrease")
    d_decrease.set_fixed_duration(1)
    d_decrease.add_condition(StartTiming(), GT(counter_f, 0))
    d_decrease.add_decrease_effect(EndTiming(), counter_f, 1)
    problem = Problem("temporal_counter")
    problem.add_fluent(counter_f)
    problem.add_action(d_increase)
    problem.add_action(d_decrease)
    problem.set_initial_value(counter_f, 0)
    problem.add_goal(Equals(counter_f, 1))
    ttplan = up.plans.TimeTriggeredPlan(
        [
            (Fraction(0, 1), up.plans.ActionInstance(d_increase), Fraction(1, 1)),
            (Fraction(2, 1), up.plans.ActionInstance(d_decrease), Fraction(1, 1)),
        ]
    )
    t_counter = TestCase(problem=problem, solvable=True, valid_plans=[ttplan])
    problems["temporal_counter"] = t_counter

    # basic with object constant
    Location = UserType("Location")
    is_at = Fluent("is_at", BoolType(), loc=Location)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(is_at(l_from))
    move.add_precondition(Not(is_at(l_to)))
    move.add_effect(is_at(l_from), False)
    move.add_effect(is_at(l_to), True)
    move_to_l1 = InstantaneousAction("move_to_l1", l_from=Location)
    l_from = move_to_l1.parameter("l_from")
    move_to_l1.add_precondition(is_at(l_from))
    move_to_l1.add_precondition(Not(is_at(l1)))
    move_to_l1.add_effect(is_at(l_from), False)
    move_to_l1.add_effect(is_at(l1), True)
    problem = Problem("basic_with_object_constant")
    problem.add_fluent(is_at)
    problem.add_objects([l1, l2])
    problem.add_action(move)
    problem.add_action(move_to_l1)
    problem.set_initial_value(is_at(l1), True)
    problem.set_initial_value(is_at(l2), False)
    problem.add_goal(is_at(l2))
    plan = up.plans.SequentialPlan(
        [up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)))]
    )
    basic_with_object_constant = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
    problems["basic_with_object_constant"] = basic_with_object_constant

    # basic numeric
    value = Fluent("value", IntType())
    task = InstantaneousAction("task")
    task.add_precondition(Equals(value, 1))
    task.add_effect(value, 2)
    problem = Problem("basic_numeric")
    problem.add_fluent(value)
    problem.add_action(task)
    problem.set_initial_value(value, 1)
    problem.add_goal(Equals(value, 2))
    plan = up.plans.SequentialPlan([up.plans.ActionInstance(task)])
    problems["basic_numeric"] = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )

    # basic numeric with timed effect
    value = Fluent("value", IntType())
    task = InstantaneousAction("task")
    task.add_precondition(Equals(value, 1))
    task.add_effect(value, 2)
    problem = Problem("basic_numeric_with_timed_effect")
    problem.add_fluent(value)
    problem.add_action(task)
    problem.set_initial_value(value, 1)
    problem.add_goal(Equals(value, 2))
    problem.add_timed_effect(GlobalStartTiming(1), value, 1)
    t_plan = up.plans.TimeTriggeredPlan(
        [(Fraction(2), up.plans.ActionInstance(task), None)]
    )
    problems["basic_numeric_with_timed_effect"] = TestCase(
        problem=problem, solvable=True, valid_plans=[t_plan]
    )

    problem = Problem("basic_undef_bool")
    fluent1 = problem.add_fluent("fluent1", BoolType())
    problem.set_initial_value(fluent1(), False)
    fluent2 = problem.add_fluent("fluent2", BoolType())
    problem.add_goal(fluent1())

    a1 = InstantaneousAction("a1")
    a1.add_precondition(Not(fluent1()))
    a1.add_effect(fluent1(), True)
    problem.add_action(a1)
    a2 = InstantaneousAction("set_b")
    a2.add_precondition(
        Or(Not(fluent1()), Not(fluent2()))
    )  # never valid under PDDL semantics as fluent2() is undefined
    a2.add_effect(fluent1(), True)
    problem.add_action(a2)
    problems["basic_undef_bool"] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=[up.plans.SequentialPlan([a1()])],
        invalid_plans=[
            # Under PDDL semantics, invalid plans contain actions that rely on undefined values
            # The following are commented out as we do not wish enforce strict PDDL semantics when validating planner integration
            # up.plans.SequentialPlan([a2()]),
            # up.plans.SequentialPlan([a1(), a2()]),
        ],
    )

    # basic numeric with timed effect
    problem = Problem("basic_undef_numeric")
    object_type = UserType("Obj")
    o1 = problem.add_object("o1", object_type)
    o2 = problem.add_object("o2", object_type)
    value = problem.add_fluent("value", IntType(), o=object_type)
    problem.set_initial_value(value(o1), 1)  # only value(o1) is defined
    increase_one = InstantaneousAction("increase_one", o=object_type)
    increase_one.add_increase_effect(value(increase_one.o), 1)
    problem.add_action(increase_one)

    increase_both = InstantaneousAction("increase_both")
    increase_both.add_increase_effect(value(o1), 1)
    increase_both.add_increase_effect(value(o2), 1)
    problem.add_action(increase_both)

    problem.add_goal(Equals(value(o1), 1))
    problems["basic_undef_numeric"] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=[up.plans.SequentialPlan([increase_one(o1)])],
        invalid_plans=[  # invalid plans contain actions that rely on undefined values
            up.plans.SequentialPlan([increase_one(o2)]),
            up.plans.SequentialPlan([increase_both()]),
            up.plans.SequentialPlan([increase_one(o1), increase_one(o2)]),
        ],
    )

    # continuous effect in durative
    continous_changing_fluent = Fluent("continous_changing_fluent", RealType())

    continuous_change = DurativeAction("continuous_change")
    interval = TimeInterval(StartTiming(), EndTiming())
    continuous_change.add_increase_continuous_effect(
        interval, continous_changing_fluent, 1
    )
    continuous_change.add_condition(StartTiming(), LE(continous_changing_fluent, 30))

    problem = Problem("durative_continuous_example")
    problem.add_fluent(continous_changing_fluent)
    problem.add_action(continuous_change)
    problem.set_initial_value(continous_changing_fluent, 5)
    problem.add_goal(GE(continous_changing_fluent, 20))

    problems["durative_continuous_example"] = TestCase(
        problem=problem,
        solvable=False,
        valid_plans=[],
        invalid_plans=[],
    )

    # interpreted functions ----------
    # interpreted functions in instaneous action precondition
    problem = Problem("interpreted_functions_in_conditions")

    def i_f_simple_bool(inputone, inputtwo):
        return (inputone * inputtwo) == 60

    signatureConditionF = OrderedDict()
    signatureConditionF["inputone"] = IntType()
    signatureConditionF["inputtwo"] = IntType()
    funx = InterpretedFunction("funx", BoolType(), signatureConditionF, i_f_simple_bool)
    end_goal = Fluent("end_goal")
    ione = Fluent("ione", IntType(0, 20))
    itwo = Fluent("itwo", IntType(0, 20))
    instant_action_i_f_condition = InstantaneousAction("instant_action_i_f_condition")
    instant_action_i_f_condition.add_precondition(
        And(
            GE(ione, 10), Not(funx(itwo, itwo))
        )  # note that (!funx (i2, i2)) is always true
    )
    instant_action_i_f_condition.add_precondition((funx(ione, itwo)))
    instant_action_i_f_condition.add_effect(end_goal, True)
    problem.add_fluent(end_goal)
    problem.add_fluent(ione)
    problem.add_fluent(itwo)
    problem.add_action(instant_action_i_f_condition)
    problem.set_initial_value(end_goal, False)
    problem.set_initial_value(ione, 12)
    problem.set_initial_value(itwo, 5)
    problem.add_goal(end_goal)
    ifproblem = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=[
            up.plans.SequentialPlan([instant_action_i_f_condition()]),
        ],
        invalid_plans=[
            up.plans.SequentialPlan([]),
        ],
    )
    problems["interpreted_functions_in_conditions"] = ifproblem

    # interpreted functions in durative action condition - could be changed
    funx = InterpretedFunction("funx", BoolType(), signatureConditionF, i_f_simple_bool)

    end_goal = Fluent("end_goal")
    ione = Fluent("ione", IntType(0, 20))
    itwo = Fluent("itwo", IntType(0, 20))

    durative_action_i_f_condition = DurativeAction("durative_action_i_f_condition")

    durative_action_i_f_condition.add_condition(
        EndTiming(), And(GE(ione, 10), Not(funx(itwo, itwo)))
    )
    durative_action_i_f_condition.add_condition(StartTiming(), (funx(ione, itwo)))
    durative_action_i_f_condition.add_condition(
        StartTiming(), Not(And(GE(ione, 15), LE(itwo, 5)))
    )
    durative_action_i_f_condition.add_effect(EndTiming(), end_goal, True)
    durative_action_i_f_condition.set_fixed_duration(5)

    problem = Problem("interpreted_functions_in_durative_conditions")
    problem.add_fluent(end_goal)
    problem.add_fluent(ione)
    problem.add_fluent(itwo)
    problem.add_action(durative_action_i_f_condition)
    problem.set_initial_value(end_goal, False)
    problem.set_initial_value(ione, 12)
    problem.set_initial_value(itwo, 5)
    problem.add_goal(end_goal)

    ifproblem = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=[
            up.plans.SequentialPlan([durative_action_i_f_condition()]),
        ],
        invalid_plans=[
            up.plans.SequentialPlan([]),
        ],
    )
    problems["interpreted_functions_in_durative_conditions"] = ifproblem

    # interpreted functions in duration
    def i_f_go_home_duration(
        israining, basetime
    ):  # if it rains you will take longer to walk home
        r = basetime
        if israining:
            r = basetime * 1.4
        return r

    gohomedurationsignature = OrderedDict()
    gohomedurationsignature["israining"] = BoolType()
    gohomedurationsignature["basetime"] = IntType()
    gohomeduration = InterpretedFunction(
        "gohomeduration", RealType(), gohomedurationsignature, i_f_go_home_duration
    )

    athome = Fluent("athome")
    rain = Fluent("rain")
    normaltime = Fluent("normaltime", IntType(0, 20))

    gohome = DurativeAction("gohome")
    gohome.add_condition(StartTiming(), Not(athome))
    gohome.add_effect(EndTiming(), athome, True)
    gohome.set_fixed_duration(gohomeduration(rain, normaltime))

    problem = Problem("interpreted_functions_in_durations")
    problem.add_fluent(athome)
    problem.add_fluent(rain)
    problem.add_fluent(normaltime)
    problem.add_action(gohome)
    problem.set_initial_value(athome, False)
    problem.set_initial_value(rain, True)
    problem.set_initial_value(normaltime, 10)
    problem.add_goal(athome)
    ifproblem = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=[
            up.plans.SequentialPlan([gohome()]),
        ],
        invalid_plans=[
            up.plans.SequentialPlan([]),
        ],
    )
    problems["interpreted_functions_in_durations"] = ifproblem

    # interpreted functions in bool assignment - could be changed

    funx = InterpretedFunction("funx", BoolType(), signatureConditionF, i_f_simple_bool)

    ione = Fluent("ione", IntType(0, 20))
    itwo = Fluent("itwo", IntType(0, 20))
    end_goal = Fluent("end_goal")

    apply_i_f_assignment = InstantaneousAction("apply_i_f_assignment")
    apply_i_f_assignment.add_effect(end_goal, funx(ione, itwo))

    increase_val = InstantaneousAction("increase_val")
    increase_val.add_effect(ione, Plus(ione, 2))

    problem = Problem("interpreted_functions_in_boolean_assignment")
    problem.add_fluent(ione)
    problem.add_fluent(itwo)
    problem.add_fluent(end_goal)

    problem.add_action(apply_i_f_assignment)
    problem.add_action(increase_val)
    problem.set_initial_value(ione, 3)
    problem.set_initial_value(itwo, 12)
    problem.set_initial_value(end_goal, False)
    problem.add_goal(end_goal)

    ifproblem = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=[
            up.plans.SequentialPlan([increase_val(), apply_i_f_assignment()]),
        ],
        invalid_plans=[
            up.plans.SequentialPlan([apply_i_f_assignment(), increase_val()]),
        ],
    )
    problems["interpreted_functions_in_boolean_assignment"] = ifproblem

    return problems
