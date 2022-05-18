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


import unified_planning as up
from unified_planning.shortcuts import *
from collections import namedtuple

Example = namedtuple('Example', ['problem', 'plan'])

def get_example_problems():
    problems = {}

    # basic
    x = Fluent('x')
    a = InstantaneousAction('a')
    a.add_precondition(Not(x))
    a.add_effect(x, True)
    problem = Problem('basic')
    problem.add_fluent(x)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.add_goal(x)
    plan = up.plan.SequentialPlan([up.plan.ActionInstance(a)])
    basic = Example(problem=problem, plan=plan)
    problems['basic'] = basic

    # basic conditional
    x = Fluent('x')
    y = Fluent('y')
    a_x = InstantaneousAction('a_x')
    a_y = InstantaneousAction('a_y')
    a_x.add_precondition(Not(x))
    a_x.add_effect(x, True, y)
    a_y.add_precondition(Not(y))
    a_y.add_effect(y, True)
    problem = Problem('basic_conditional')
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(a_x)
    problem.add_action(a_y)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, False)
    problem.add_goal(x)
    plan = up.plan.SequentialPlan([up.plan.ActionInstance(a_y), up.plan.ActionInstance(a_x)])
    basic_conditional = Example(problem=problem, plan=plan)
    problems['basic_conditional'] = basic_conditional

    # complex conditional
    a = Fluent('a')
    b = Fluent('b')
    c = Fluent('c')
    d = Fluent('d')
    k = Fluent('k')
    x = Fluent('x')
    y = Fluent('y')
    z = Fluent('z')
    a_act = InstantaneousAction('A')
    a_0_act = InstantaneousAction('A_0')
    a_1_act = InstantaneousAction('A_1')
    a_2_act = InstantaneousAction('A_2')
    a_act.add_precondition(Not(a))
    a_act.add_effect(a, TRUE())
    a_act.add_effect(k, TRUE(), b)
    a_act.add_effect(x, TRUE(), Not(c))
    a_act.add_effect(y, FALSE(), d)
    a_0_act.add_precondition(Not(a))
    a_0_act.add_precondition(d)
    a_0_act.add_effect(b, TRUE())
    a_1_act.add_precondition(Not(a))
    a_1_act.add_precondition(d)
    a_1_act.add_precondition(b)
    a_1_act.add_effect(c, FALSE(), c)
    a_1_act.add_effect(c, TRUE(), Not(c))
    a_2_act.add_effect(a, FALSE())
    a_2_act.add_effect(d, TRUE())
    a_2_act.add_effect(z, FALSE(), z)
    a_2_act.add_effect(z, TRUE(), Not(z))
    problem = Problem('complex_conditional')
    problem.add_fluent(a)
    problem.add_fluent(b)
    problem.add_fluent(c)
    problem.add_fluent(d)
    problem.add_fluent(k)
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_fluent(z)
    problem.add_action(a_act)
    problem.add_action(a_0_act)
    problem.add_action(a_1_act)
    problem.add_action(a_2_act)
    problem.set_initial_value(a, True)
    problem.set_initial_value(b, False)
    problem.set_initial_value(c, True)
    problem.set_initial_value(d, False)
    problem.set_initial_value(k, False)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, True)
    problem.set_initial_value(z, False)
    problem.add_goal(a)
    problem.add_goal(b)
    problem.add_goal(Not(c))
    problem.add_goal(d)
    problem.add_goal(k)
    problem.add_goal(x)
    problem.add_goal(Not(y))
    problem.add_goal(z)
    plan = up.plan.SequentialPlan([up.plan.ActionInstance(a_2_act),
                                   up.plan.ActionInstance(a_0_act),
                                   up.plan.ActionInstance(a_1_act),
                                   up.plan.ActionInstance(a_act)])
    complex_conditional = Example(problem=problem, plan=plan)
    problems['complex_conditional'] = complex_conditional

    # basic without negative preconditions
    x = Fluent('x')
    y = Fluent('y')
    a = InstantaneousAction('a')
    a.add_precondition(y)
    a.add_effect(x, True)
    problem = Problem('basic_without_negative_preconditions')
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, True)
    problem.add_goal(x)
    plan = up.plan.SequentialPlan([up.plan.ActionInstance(a)])
    basic_without_negative_preconditions = Example(problem=problem, plan=plan)
    problems['basic_without_negative_preconditions'] = basic_without_negative_preconditions

    # basic nested conjunctions
    problem = Problem('basic_nested_conjunctions')
    x = problem.add_fluent('x')
    y = problem.add_fluent('y')
    z = problem.add_fluent('z')
    j = problem.add_fluent('j')
    k = problem.add_fluent('k')

    a = InstantaneousAction('a')
    a.add_precondition(And(y, And(z, j, k)))
    a.add_effect(x, True)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, True)
    problem.set_initial_value(z, True)
    problem.set_initial_value(j, True)
    problem.set_initial_value(k, True)
    problem.add_goal(And(x, And(y, z, And(j, k))))
    plan = up.plan.SequentialPlan([up.plan.ActionInstance(a)])
    basic_nested_conjunctions = Example(problem=problem, plan=plan)
    problems['basic_nested_conjunctions'] = basic_nested_conjunctions

    # basic exists
    sem = UserType("Semaphore")
    x = Fluent('x')
    y = Fluent('y', BoolType(), semaphore=sem)
    o1 = Object('o1', sem)
    o2 = Object('o2', sem)
    s_var = Variable("s", sem)
    a = InstantaneousAction('a')
    a.add_precondition(Exists(FluentExp(y, [s_var]), s_var))
    a.add_effect(x, True)
    problem = Problem('basic_exists')
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_object(o1)
    problem.add_object(o2)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y(o1), True)
    problem.set_initial_value(y(o2), False)
    problem.add_goal(x)
    plan = up.plan.SequentialPlan([up.plan.ActionInstance(a)])
    basic_exists = Example(problem=problem, plan=plan)
    problems['basic_exists'] = basic_exists


    # basic forall
    sem = UserType("Semaphore")
    x = Fluent('x')
    y = Fluent('y', BoolType(), semaphore=sem)
    s_var = Variable("s", sem)
    a = InstantaneousAction('a')
    a.add_precondition(Forall(Not(y(s_var)), s_var))
    a.add_effect(x, True)
    problem = Problem('basic_forall')
    problem.add_fluent(x)
    problem.add_fluent(y)
    o1 = problem.add_object('o1', sem)
    o2 = problem.add_object('o2', sem)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y(o1), False)
    problem.set_initial_value(y(o2), False)
    problem.add_goal(x)
    plan = up.plan.SequentialPlan([up.plan.ActionInstance(a)])
    basic_forall = Example(problem=problem, plan=plan)
    problems['basic_forall'] = basic_forall

    # temporal conditional
    Obj = UserType('Obj')
    is_same_obj = Fluent('is_same_obj', BoolType(), object_1=Obj, object_2=Obj)
    is_ok = Fluent('is_ok', BoolType(), test=Obj)
    is_ok_giver = Fluent('is_ok_giver', BoolType(), test=Obj)
    ok_given = Fluent('ok_given')
    set_giver = DurativeAction('set_giver', y=Obj)
    y = set_giver.parameter('y')
    set_giver.set_fixed_duration(2)
    set_giver.add_condition(StartTiming(), Not(is_ok_giver(y)))
    set_giver.add_effect(StartTiming(), is_ok_giver(y), True)
    set_giver.add_effect(EndTiming(), is_ok_giver(y), False)
    take_ok = DurativeAction('take_ok', x=Obj, y=Obj)
    x = take_ok.parameter('x')
    y = take_ok.parameter('y')
    take_ok.set_fixed_duration(3)
    take_ok.add_condition(StartTiming(), Not(is_ok(x)))
    take_ok.add_condition(StartTiming(), Not(is_ok_giver(y)))
    take_ok.add_condition(StartTiming(), Not(is_same_obj(x, y)))
    take_ok.add_effect(EndTiming(), is_ok(x), True, is_ok_giver(y))
    take_ok.add_effect(EndTiming(), ok_given, True)
    o1 = Object('o1', Obj)
    o2 = Object('o2', Obj)
    problem = Problem('temporal_conditional')
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
    plan = up.plan.TimeTriggeredPlan([(Fraction(0, 1), up.plan.ActionInstance(take_ok, (ObjectExp(o1), ObjectExp(o2))), Fraction(3, 1)),
                                      (Fraction(1, 1), up.plan.ActionInstance(set_giver, (ObjectExp(o2), )), Fraction(2, 1))])
    temporal_conditional = Example(problem=problem, plan=plan)
    problems['temporal_conditional'] = temporal_conditional

    # basic with actions cost
    x = Fluent('x')
    y = Fluent('y')
    a = InstantaneousAction('a')
    a.add_precondition(Not(x))
    a.add_effect(x, True)
    b = InstantaneousAction('b')
    b.add_precondition(Not(y))
    b.add_effect(y, True)
    c = InstantaneousAction('c')
    c.add_precondition(y)
    c.add_effect(x, True)
    problem = Problem('basic_with_costs')
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(a)
    problem.add_action(b)
    problem.add_action(c)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, False)
    problem.add_goal(x)
    problem.add_quality_metric(up.model.metrics.MinimizeActionCosts({a: Int(10), b: Int(1), c: Int(1)}))
    plan = up.plan.SequentialPlan([up.plan.ActionInstance(b),
                                   up.plan.ActionInstance(c)])
    basic_with_costs = Example(problem=problem, plan=plan)
    problems['basic_with_costs'] = basic_with_costs

    # counter
    counter_1 = Fluent('counter_1', IntType(0, 10))
    counter_2 = Fluent('counter_2', IntType(0, 10))
    fake_counter = Fluent('fake_counter', IntType(0, 10))
    increase = InstantaneousAction('increase')
    increase.add_increase_effect(counter_1, 1)
    increase.add_effect(counter_2, Plus(counter_2, 1))
    increase.add_effect(fake_counter, Div(Times(fake_counter, 2), 2))
    problem = Problem('counter')
    problem.add_fluent(counter_1)
    problem.add_fluent(counter_2)
    problem.add_fluent(fake_counter)
    problem.add_action(increase)
    problem.set_initial_value(counter_1, 0)
    problem.set_initial_value(counter_2, 0)
    problem.set_initial_value(fake_counter, 1)
    problem.add_goal(Iff(LT(fake_counter, counter_1), LT(counter_2, 3)))
    plan = up.plan.SequentialPlan([up.plan.ActionInstance(increase), up.plan.ActionInstance(increase)])
    counter = Example(problem=problem, plan=plan)
    problems['counter'] = counter

    return problems
