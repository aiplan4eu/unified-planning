import unified_planning
from unified_planning.shortcuts import *
from collections import namedtuple


from unified_planning.io.pddl_writer import PDDLWriter
from unified_planning.io.pddl_reader import PDDLReader
Example = namedtuple('Example', ['problem', 'plan'])

def prova():
    problems = {}

    # robot locations connected
    Location = UserType('Location')
    Robot = UserType('Robot')
    is_at = Fluent('is_at', BoolType(), [Location, Robot])
    battery_charge = Fluent('battery_charge', RealType(0, 100), [Robot])
    is_connected = Fluent('is_connected', BoolType(), [Location, Location])
    move = InstantaneousAction('move', robot=Robot, l_from=Location, l_to=Location)
    robot = move.parameter('robot')
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(GE(battery_charge(robot), 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(is_at(l_from, robot))
    move.add_precondition(Not(is_at(l_to, robot)))
    move.add_precondition(Or(is_connected(l_from, l_to), is_connected(l_to, l_from)))
    move.add_effect(is_at(l_from, robot), False)
    move.add_effect(is_at(l_to, robot), True)
    move.add_decrease_effect(battery_charge(robot), 10)
    move_2 = InstantaneousAction('move_2', robot=Robot, l_from=Location, l_to=Location)
    robot = move_2.parameter('robot')
    l_from = move_2.parameter('l_from')
    l_to = move_2.parameter('l_to')
    move_2.add_precondition(GE(battery_charge(robot), 15))
    move_2.add_precondition(Not(Equals(l_from, l_to)))
    move_2.add_precondition(is_at(l_from, robot))
    move_2.add_precondition(Not(is_at(l_to, robot)))
    mid_location = Variable('mid_loc', Location)
    # (E (location mid_location)
    # !((mid_location == l_from) || (mid_location == l_to)) && (is_connected(l_from, mid_location) || is_connected(mid_location, l_from)) &&
    # && (is_connected(l_to, mid_location) || is_connected(mid_location, l_to)))
    move_2.add_precondition(Exists(And(Not(Or(Equals(mid_location, l_from), Equals(mid_location, l_to))),
                                       Or(is_connected(l_from, mid_location), is_connected(mid_location, l_from)),
                                       Or(is_connected(l_to, mid_location), is_connected(mid_location, l_to))),
                                   mid_location))
    move_2.add_effect(is_at(l_from, robot), False)
    move_2.add_effect(is_at(l_to, robot), True)
    move_2.add_decrease_effect(battery_charge(robot), 15)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    l3 = Object('l3', Location)
    l4 = Object('l4', Location)
    l5 = Object('l5', Location)
    r1 = Object('r1', Robot)
    problem = Problem('robot_locations_connected')
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(battery_charge)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_action(move)
    problem.add_action(move_2)
    problem.add_object(r1)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(l4)
    problem.add_object(l5)
    problem.set_initial_value(is_at(l1, r1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.set_initial_value(battery_charge(r1), 100)
    problem.add_goal(is_at(l5, r1))
    plan = unified_planning.plan.SequentialPlan(
        [unified_planning.plan.ActionInstance(move_2, (ObjectExp(r1), ObjectExp(l1), ObjectExp(l3))),
         unified_planning.plan.ActionInstance(move_2, (ObjectExp(r1), ObjectExp(l3), ObjectExp(l5)))])
    robot_locations_connected = Example(problem=problem, plan=plan)
    problems['robot_locations_connected'] = robot_locations_connected

    print(problem)
    w = PDDLWriter(problem)
    print(w.get_domain())
    print(w.get_problem())

prova()