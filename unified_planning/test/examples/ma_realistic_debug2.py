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
# limitations under the License.


import unified_planning
from unified_planning.shortcuts import *
from collections import namedtuple
from unified_planning.model.agent import Agent
from unified_planning.model.ma_problem import MultiAgentProblem
from realistic import get_example_problems
from unified_planning.model.environment_ma import Environment_ma

from unified_planning.io.pddl_writer import PDDLWriter
from unified_planning.io.pddl_reader import PDDLReader
from unified_planning.transformers import NegativeConditionsRemover
from unified_planning.transformers import DisjunctiveConditionsRemover

Example = namedtuple('Example', ['problem', 'plan'])
problems = {}
#examples = get_example_problems()

def prova():
    Location = UserType('Location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    robot_at_2 = Fluent('robot_at_2', BoolType(), [Location])
    move = InstantaneousAction('move', l_from=Location, l_to=Location)
    move_2 = InstantaneousAction('move_2', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(robot_at(l_from))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)

    move_2.add_precondition(robot_at_2(l_from))
    move_2.add_effect(robot_at_2(l_from), False)
    move_2.add_effect(robot_at_2(l_to), True)

    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    '''l3 = Object('l3', Location)
    l4 = Object('l4', Location)'''


    problem = Problem('robotto')
    problem.add_fluent(robot_at)
    problem.add_fluent(robot_at_2)
    problem.add_action(move)
    problem.add_action(move_2)

    problem.add_object(l1)
    problem.add_object(l2)

    '''problem.add_object(l3)
    problem.add_object(l4)'''

    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    '''problem.set_initial_value(robot_at(l3), False)
    problem.set_initial_value(robot_at(l4), False)'''

    problem.set_initial_value(robot_at_2(l1), True)
    problem.set_initial_value(robot_at_2(l2), False)
    '''problem.set_initial_value(robot_at_2(l1), False)
    problem.set_initial_value(robot_at_2(l2), False)'''

    problem.add_goal(robot_at(l2))
    problem.add_goal(robot_at_2(l2))



    '''w = PDDLWriter(problem)
    print(w.get_domain())
    print(w.get_problem())'''
    print(problem.user_types())
    with OneshotPlanner(name='pyperplan') as planner:
        solve_plan = planner.solve(problem)
        print("Pyperplan returned: %s" % solve_plan)


def prova2():
    # robot_loader_adv
    Robot = UserType('Robot')
    Container = UserType('Container')
    Location = UserType('Location')
    robot_at = Fluent('robot_at', BoolType(), [Robot, Location])
    cargo_at = Fluent('cargo_at', BoolType(), [Container, Location])
    cargo_mounted = Fluent('cargo_mounted', BoolType(), [Container, Robot])
    move = InstantaneousAction('move', l_from=Location, l_to=Location, r=Robot)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    r = move.parameter('r')
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(r, l_from))
    move.add_precondition(Not(robot_at(r, l_to)))
    move.add_effect(robot_at(r, l_from), False)
    move.add_effect(robot_at(r, l_to), True)
    load = InstantaneousAction('load', loc=Location, r=Robot, c=Container)
    loc = load.parameter('loc')
    r = load.parameter('r')
    c = load.parameter('c')
    load.add_precondition(cargo_at(c, loc))
    load.add_precondition(robot_at(r, loc))
    load.add_precondition(Not(cargo_mounted(c, r)))
    load.add_effect(cargo_at(c, loc), False)
    load.add_effect(cargo_mounted(c,r), True)
    unload = InstantaneousAction('unload', loc=Location, r=Robot, c=Container)
    loc = unload.parameter('loc')
    r = unload.parameter('r')
    c = unload.parameter('c')
    unload.add_precondition(Not(cargo_at(c, loc)))
    unload.add_precondition(robot_at(r, loc))
    unload.add_precondition(cargo_mounted(c,r))
    unload.add_effect(cargo_at(c, loc), True)
    unload.add_effect(cargo_mounted(c,r), False)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    l3 = Object('l3', Location)
    r1 = Object('r1', Robot)
    c1 = Object('c1', Container)
    problem = Problem('robot_loader_adv')
    problem.add_fluent(robot_at)
    problem.add_fluent(cargo_at)
    problem.add_fluent(cargo_mounted)
    problem.add_action(move)
    problem.add_action(load)
    problem.add_action(unload)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(r1)
    problem.add_object(c1)
    problem.set_initial_value(robot_at(r1,l1), True)
    problem.set_initial_value(robot_at(r1,l2), False)
    problem.set_initial_value(robot_at(r1,l3), False)
    problem.set_initial_value(cargo_at(c1,l1), False)
    problem.set_initial_value(cargo_at(c1,l2), True)
    problem.set_initial_value(cargo_at(c1,l3), False)
    problem.set_initial_value(cargo_mounted(c1,r1), False)
    problem.add_goal(cargo_at(c1,l3))
    problem.add_goal(robot_at(r1,l1))
    plan = unified_planning.plan.SequentialPlan([unified_planning.plan.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2), ObjectExp(r1))),
                               unified_planning.plan.ActionInstance(load, (ObjectExp(l2), ObjectExp(r1), ObjectExp(c1))),
                               unified_planning.plan.ActionInstance(move, (ObjectExp(l2), ObjectExp(l3), ObjectExp(r1))),
                               unified_planning.plan.ActionInstance(unload, (ObjectExp(l3), ObjectExp(r1), ObjectExp(c1))),
                               unified_planning.plan.ActionInstance(move, (ObjectExp(l3), ObjectExp(l1), ObjectExp(r1)))])
    robot_loader_adv = Example(problem=problem, plan=plan)
    problems['robot_loader_adv'] = robot_loader_adv
    #npr = NegativeConditionsRemover(problem)

    #positive_problem = npr.get_rewritten_problem()
    #print("positive_problem", positive_problem)

    '''with OneshotPlanner(name='tamer') as planner:
        solve_plan = planner.solve(problem)
        print("Pyperplan returned: %s" % solve_plan)'''

    w = PDDLWriter(problem)
    print(w.get_domain())
    print(w.get_problem())


def prova3():
    # robot no negative preconditions
    Location = UserType('location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    move = InstantaneousAction('move', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(robot_at(l_from))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    problem = Problem('robot')
    problem.add_fluent(robot_at)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.add_goal(robot_at(l2))


    w = PDDLWriter(problem)
    print(w.get_domain())
    print(w.get_problem())

    npr = NegativeConditionsRemover(problem)

    positive_problem = npr.get_rewritten_problem()
    print("positive_problem", positive_problem)


    with OneshotPlanner(name='tamer') as planner:
        solve_plan = planner.solve(problem)
        print("Pyperplan returned: %s" % solve_plan)



def prova4_single():
    Location = UserType('Location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    cargo_at = Fluent('cargo_at', BoolType(), [Location])
    is_same_location = Fluent('is_same_location', BoolType(), [Location, Location])
    cargo_mounted = Fluent('cargo_mounted')
    move = InstantaneousAction('move', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_precondition(Not(is_same_location(l_from, l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    load = InstantaneousAction('load', loc=Location)
    loc = load.parameter('loc')
    load.add_precondition(cargo_at(loc))
    load.add_precondition(robot_at(loc))
    load.add_precondition(Not(cargo_mounted))
    load.add_effect(cargo_at(loc), False)
    load.add_effect(cargo_mounted, True)
    unload = InstantaneousAction('unload', loc=Location)
    loc = unload.parameter('loc')
    unload.add_precondition(Not(cargo_at(loc)))
    unload.add_precondition(robot_at(loc))
    unload.add_precondition(cargo_mounted)
    unload.add_effect(cargo_at(loc), True)
    unload.add_effect(cargo_mounted, False)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    problem = Problem('robot_loader_mod')
    problem.add_fluent(robot_at, default_initial_value=False)
    problem.add_fluent(cargo_at, default_initial_value=False)
    problem.add_fluent(cargo_mounted, default_initial_value=False)
    problem.add_fluent(is_same_location, default_initial_value=False)
    problem.add_action(move)
    problem.add_action(load)
    problem.add_action(unload)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(cargo_at(l2), True)
    for o in problem.objects(Location):
        problem.set_initial_value(is_same_location(o, o), True)
    problem.add_goal(cargo_at(l1))

    with OneshotPlanner(name='tamer') as planner:
        solve_plan = planner.solve(problem)
        print("Pyperplan returned: %s" % solve_plan)

    npr = NegativeConditionsRemover(problem)
    positive_problem = npr.get_rewritten_problem()
    print("positive_problem", positive_problem)

    dnfr = DisjunctiveConditionsRemover(problem)
    dnf_problem = dnfr.get_rewritten_problem()

def prova_robot():
    Location = UserType('location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    move = InstantaneousAction('move', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(robot_at(l_from))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    problem = Problem('robot')
    problem.add_fluent(robot_at)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.add_goal(robot_at(l2))
    plan = unified_planning.plan.SequentialPlan([unified_planning.plan.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)))])
    robot_no_negative_preconditions = Example(problem=problem, plan=plan)
    problems['robot_no_negative_preconditions'] = robot_no_negative_preconditions

    w = PDDLWriter(problem)
    print(w.get_domain())
    print(w.get_problem())


    #npr = NegativeConditionsRemover(problem)
    #positive_problem = npr.get_rewritten_problem()
    #print(positive_problem)

def prove_varie():
    Entity = UserType('Entity', None)  # None can be avoided
    Agent = UserType('Agent', None)  # None can be avoided
    Location = UserType('Location', Entity)
    Location1 = UserType('Location1', Agent)
    Unmovable = UserType('Unmovable', Location)
    Unmovable1 = UserType('Unmovable1', Location1)
    TableSpace = UserType('TableSpace', Unmovable)
    TableSpace1 = UserType('TableSpace1', Unmovable1)
    Movable = UserType('Movable', Location)
    Block = UserType('Block', Movable)
    clear = Fluent('clear', BoolType(), [Location])
    on = Fluent('on', BoolType(), [Movable, Location])

    located = Fluent("located", BoolType(), [Movable, Location])


    move = InstantaneousAction('move', item=Movable, l_from=Location, l_to=Location)
    item = move.parameter('item')
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')

    move.add_precondition(clear(item))
    move.add_precondition(clear(l_to))
    move.add_precondition(on(item, l_from))
    move.add_effect(clear(l_from), True)
    move.add_effect(on(item, l_from), False)
    move.add_effect(clear(l_to), False)


    problem = Problem('hierarchical_blocks_world')
    problem.add_fluent(clear, default_initial_value=False)
    problem.add_fluent(on, default_initial_value=False)
    problem.add_action(move)
    ts_1 = Object('ts_1', TableSpace)
    ts_2 = Object('ts_2', TableSpace)
    ts_3 = Object('ts_3', TableSpace)
    ts_4 = Object('ts_4', TableSpace1)
    problem.add_objects([ts_1, ts_2, ts_3, ts_4])
    block_1 = Object('block_1', Block)
    block_2 = Object('block_2', Block)
    block_3 = Object('block_3', Block)
    block_4 = Object('block_4', Block)
    problem.add_objects([block_1, block_2, block_3, block_4])

    # The blocks are all on ts_1, in order block_3 under block_1 under block_2
    problem.set_initial_value(clear(ts_2), True)
    problem.set_initial_value(clear(ts_3), True)
    problem.set_initial_value(clear(block_2), True)
    problem.set_initial_value(on(block_3, ts_1), True)
    problem.set_initial_value(on(block_1, block_3), True)
    problem.set_initial_value(on(block_2, block_1), True)
    #problem.set_initial_value(not(ts_4), True)

    # We want them on ts_3 in order block_3 on block_2 on block_1
    problem.add_goal(on(block_1, ts_3))
    #problem.add_goal(on(block_4, ts_4))
    problem.add_goal(on(block_2, block_1))
    problem.add_goal(on(block_3, block_2))
    problem.add_goal(on(block_3, block_4))

    plan = unified_planning.plan.SequentialPlan([
        unified_planning.plan.ActionInstance(move, (ObjectExp(block_2), ObjectExp(block_1), ObjectExp(ts_2))),
        unified_planning.plan.ActionInstance(move, (ObjectExp(block_1), ObjectExp(block_3), ObjectExp(ts_3))),
        unified_planning.plan.ActionInstance(move, (ObjectExp(block_2), ObjectExp(ts_2), ObjectExp(block_1))),
        unified_planning.plan.ActionInstance(move, (ObjectExp(block_3), ObjectExp(ts_1), ObjectExp(block_2)))])
    hierarchical_blocks_world = Example(problem=problem, plan=plan)
    problems['hierarchical_blocks_world'] = hierarchical_blocks_world
    print(problem)
    w = PDDLWriter(problem)
    print(w.get_domain())
    print(w.get_problem())

#prove_varie()


def depot():
    place = UserType('place', None)
    hoist = UserType('hoist', None)
    surface = UserType('surface', None)
    #agent = UserType('agent', None)                 #questo in depot è sottointeso, per ora lo specifichaimo
    depot = UserType('depot', place)                #ma anche ad agent
    distributor = UserType('distributor', place)    #ma anche ad agent
    #truck = UserType('truck', agent)
    truck = UserType('truck', None)
    crate = UserType('crate', hoist)
    pallet = UserType('pallet', surface)


    myAgent = Fluent('myAgent', BoolType(), [truck])
    clear = Fluent('clear', None, [hoist])
    clear_s = Fluent('clear', None, [surface])

    located = Fluent('located', None, [hoist, place])
    at = Fluent('at', None, [truck, place])
    placed = Fluent('placed', None, [pallet, place])
    pos = Fluent('pos', None, [crate, place]) #Non posso utilizzare (place or truck)?
    pos_u = Fluent('pos_u', None, [crate, truck]) #Si può fare in un modo migliore?
    on = Fluent('on', None, [crate, hoist])
    on_u = Fluent('on_u', None, [crate, truck])
    on_s = Fluent('on_s', None, [crate, surface])

    truck0 = Object('truck0', truck)
    truck1 = Object('truck1', truck)


    drive = InstantaneousAction('drive', truck=truck, x=place, y=place)
    truck = drive.parameter('truck')
    x = drive.parameter('x')
    y = drive.parameter('y')






    drive.add_precondition(myAgent(truck))
    #Drive.add_precondition(Equals(myAgent(truck), x)) Non supportato
    #Equality operator is not supported for Boolean terms.Use Iff instead.

    drive.add_precondition(at(truck, x))
    drive.add_effect(at(truck, y), True)


    #Load.add_precondition(pos(crate))
    #Load.add_precondition(Not(clear(crate)))
    load = InstantaneousAction('load', x=place, c=crate, h=hoist)
    c = load.parameter('c')
    #t = load.parameter('t')
    x = load.parameter('x')
    h = load.parameter('h')

    load.add_precondition(myAgent(truck))
    load.add_precondition(at(truck, x))
    #load.add_precondition(clear(truck, h))
    load.add_precondition(pos(c, x))
    load.add_precondition(Not(clear(h)))
    load.add_precondition(Not(clear(c)))
    load.add_precondition(on(c, h))
    load.add_precondition(located(h, x))

    load.add_effect(pos(c, x), True)
    load.add_effect(on(c, h), True)
    load.add_effect(clear(c), False)
    load.add_effect(clear(h), False)
    #load.add_effect(Not(clear(h)))

    unload = InstantaneousAction('unload', x=place, c=crate, h=hoist)
    c = unload.parameter('c')
    #t = load.parameter('t')
    x = unload.parameter('x')
    h = unload.parameter('h')

    unload.add_precondition(myAgent(truck))
    unload.add_precondition(located(h, x))
    load.add_precondition(at(truck, x))
    #load.add_precondition(clear(truck, h))
    unload.add_precondition(pos_u(c, truck))
    unload.add_precondition(on_u(c, truck))
    unload.add_precondition(clear(h))
    unload.add_precondition(clear(c))

    unload.add_effect(pos(c, x), True)
    unload.add_effect(on(c, h), True)
    unload.add_effect(clear(c), False)
    unload.add_effect(clear(h), False)

    #Drive.add_precondition(myAgent(truck))
    #Drive.add_precondition(at(x), True)
    #Drive.add_precondition(at(y))
    #Drive.add_precondition(Equals(at, truck))
    #Drive.add_effect(at(truck), True)





    problem = Problem('depot')
    depot0 = Object('depot0', depot)
    distributor0 = Object('distributor0', distributor)
    distributor1 = Object('distributor1', distributor)

    crate0 = Object('crate0', crate)
    crate1 = Object('crate1', crate)
    pallet0 = Object('pallet0', pallet)
    pallet1 = Object('pallet1', pallet)
    pallet2 = Object('pallet2', pallet)
    hoist0 = Object('hoist0', hoist)
    hoist1 = Object('hoist1', hoist)
    hoist2 = Object('hoist2', hoist)

    problem.add_object(truck0)
    problem.add_object(truck1)
    problem.add_object(depot0)
    problem.add_object(distributor0)
    problem.add_object(distributor1)
    problem.add_object(pallet0)
    problem.add_object(pallet1)
    problem.add_object(pallet2)
    problem.add_object(hoist0)
    problem.add_object(hoist1)
    problem.add_object(hoist2)


    problem.add_fluent(myAgent, default_initial_value=False)
    problem.add_fluent(clear, default_initial_value=False)
    #problem.add_fluent(located, default_initial_value=False)

    '''problem.add_shared_data(clear)
    problem.add_shared_data(at)
    problem.add_shared_data(pos)
    problem.add_shared_data(pos_u)
    problem.add_shared_data(on)
    problem.add_shared_data(on_u)
    problem.add_shared_data(on_s)'''


    problem.add_action(drive)
    problem.add_action(load)
    problem.add_action(unload)
    '''problem.add_fluent(myAgent, default_initial_value=False)
    #problem.add_fluent(clear, default_initial_value=False)
    problem.add_fluent(located, default_initial_value=False)
    problem.add_fluent(at, default_initial_value=False)
    problem.add_fluent(placed, default_initial_value=False)
    problem.add_fluent(pos, default_initial_value=False)
    problem.add_fluent(pos_u, default_initial_value=False)
    problem.add_fluent(on_u, default_initial_value=False)
    problem.add_fluent(on, default_initial_value=False)'''

    problem.set_initial_value(myAgent(truck0), True)
    problem.set_initial_value(pos(crate0, distributor0), True)
    problem.set_initial_value(clear(crate0), True)
    problem.set_initial_value(on_s(crate0, pallet1), True)
    problem.set_initial_value(pos(crate1, depot0), True)
    problem.set_initial_value(clear(crate1), True)
    problem.set_initial_value(on_s(crate1, pallet0), True)
    problem.set_initial_value(at(truck0, distributor1), True)
    problem.set_initial_value(at(truck1, depot0), True)
    problem.set_initial_value(located(hoist0, depot0), True)
    problem.set_initial_value(clear(hoist0), True)
    problem.set_initial_value(located(hoist1, distributor0), True)
    problem.set_initial_value(clear(hoist1), True)
    problem.set_initial_value(located(hoist2, distributor1), True)
    problem.set_initial_value(clear(hoist2), True)
    problem.set_initial_value(placed(pallet0, depot0), True)
    problem.set_initial_value(Not(clear_s(pallet0)), True)
    problem.set_initial_value(placed(pallet1, distributor0), True)
    problem.set_initial_value(Not(clear_s(pallet1)), True)
    problem.set_initial_value(placed(pallet2, distributor1), True)
    problem.set_initial_value(clear_s(pallet2), True)
    #problem.set_initial_value(at(truck0, distributor1), True)

    problem.add_goal(on_s(crate0, pallet2))
    problem.add_goal(on_s(crate1, pallet1))
    problems['depot'] = depot

    print("problem.user_types()", problem.user_types())

    '''problem.add_fluent(place, default_initial_value=True)
    problem.add_fluent(hoist, default_initial_value=True)
    problem.add_fluent(surface, default_initial_value=True)
    problem.add_fluent(agent, default_initial_value=True)
    problem.add_fluent(truck, default_initial_value=True)
    problem.add_fluent(crate, default_initial_value=True)
    problem.add_fluent(pallet, default_initial_value=True)
    problem.add_fluent(myAgent, default_initial_value=True)'''
    #print(problem)

    w = PDDLWriter(problem)
    print(w.get_domain())
    print(w.get_problem())

def reader():
    reader = PDDLReader()
    pddl_problem = reader.parse_problem('../pddl/depot/domain.pddl',
                                        '../pddl/depot/problem.pddl')

    print(pddl_problem)

depot()