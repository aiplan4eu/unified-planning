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
from unified_planning.shortcuts import *
from unified_planning.model.multi_agent import *
from collections import namedtuple
from unified_planning.io.ma_pddl_writer import MAPDDLWriter

Example = namedtuple("Example", ["problem", "plan"])


def get_example_problems():
    problems = {}

    problem = MultiAgentProblem("ma-logistic")
    truck1 = Agent("truck1", problem)
    truck2 = Agent("truck2", problem)
    airplane = Agent("airplane", problem)

    object = UserType("object")
    location = UserType("location", object)
    vehicle = UserType("vehicle", object)
    package = UserType("package", object)
    city = UserType("city", object)
    airport = UserType("airport", location)
    #obj = UserType("obj")
    truck_ = UserType("truck_", vehicle) #agente
    airplane_ = UserType("airplane_", vehicle) #agente


    pos = Fluent("pos", location=location)
    at = Fluent("at", BoolType(), object=object, location=location)
    In = Fluent("in", BoolType(), package=package, vehicle=vehicle)
    on = Fluent("on", BoolType(), object=object)
    # Da mettere nell'agente (PRIVATI)
    in_city = Fluent("in_city", BoolType(), location=location, city=city)
    #driving = Fluent("driving", truck=truck)
    #driving_p = Fluent("driving_p", airplane=airplane)

    truck1.add_public_fluent(pos, default_initial_value=False)
    truck1.add_private_fluent(in_city, default_initial_value=False)
    truck1.add_public_fluent(on, default_initial_value=False)
    #truck1.add_fluent(driving, default_initial_value=False)
    truck2.add_public_fluent(pos, default_initial_value=False)
    truck2.add_private_fluent(in_city, default_initial_value=False)
    truck2.add_public_fluent(on, default_initial_value=False)
    #truck2.add_fluent(driving, default_initial_value=False)
    airplane.add_public_fluent(pos, default_initial_value=False)
    airplane.add_public_fluent(on, default_initial_value=False)
    #airplane.add_fluent(driving_p, default_initial_value=False)
    problem.ma_environment.add_fluent(at, default_initial_value=False)
    #problem.ma_environment.add_fluent(on, default_initial_value=False)
    problem.ma_environment.add_fluent(In, default_initial_value=False)

    #city_ = Object("city_", city)
    #truck_ = Object("truck_", truck)
    #obj = Object("obj", package)
    #loc = Object("loc", location)
    #loc_from = Object("loc_from", location)
    #loc_to = Object("loc_to", location)
    #airplane_ = Object("airplane_", airplane)

    load_truck = InstantaneousAction("load_truck", loc=location, obj=package)
    #truck = load_truck.parameter("truck")
    obj = load_truck.parameter("obj")
    loc = load_truck.parameter("loc")

    #load_truck.add_precondition(pos(y))
    #load_truck.add_precondition(Dot(truck1, pos(loc))) #se avessi potuto mettere il dot negli effect
    #load_truck.add_precondition(at(truck_, loc))
    load_truck.add_precondition(at(obj, loc))
    load_truck.add_precondition(pos(loc))
    load_truck.add_effect(at(obj, loc), False)
    load_truck.add_effect(on(obj), True)
    #load_truck.add_effect(on(obj), False)
    #non posso fare:
    #load_truck.add_effect(Dot(truck1, on(obj)), True)
    #Perchè non è possibile inserire il dot negli effetti.

    #Cosa strana dopo aver definito i parametri per una azione non posso definire gli stessi parametri per un altra
    unload_truck = InstantaneousAction("unload_truck", obj=package, loc=location)
    #truck = unload_truck.parameter("truck")
    obj = unload_truck.parameter("obj")
    loc = unload_truck.parameter("loc")

    #load_truck.add_precondition(pos(y))
    #load_truck.add_precondition(Dot(truck1, pos(loc))) #se avessi potuto mettere il dot negli effect
    unload_truck.add_precondition(pos(loc))
    unload_truck.add_precondition(on(obj))
    unload_truck.add_effect(on(obj), False)
    unload_truck.add_effect(at(obj, loc), True)


    drive_truck = InstantaneousAction("drive_truck", loc_from=location, loc_to=location, city_=city)
    loc_from = drive_truck.parameter("loc_from")
    loc_to = drive_truck.parameter("loc_to")
    city_ = drive_truck.parameter("city_")
    # load_truck.add_precondition(pos(y))
    # load_truck.add_precondition(Dot(truck1, pos(loc))) #se avessi potuto mettere il dot negli effect
    drive_truck.add_precondition(pos(loc_from))
    drive_truck.add_precondition(in_city(loc_from, city_))
    drive_truck.add_precondition(in_city(loc_to, city_))
    #drive_truck.add_precondition(in_city(truck, loc_to, city))
    drive_truck.add_effect(pos(loc_from), False)
    drive_truck.add_effect(pos(loc_to), True)
    #drive_truck.add_effect(Dot(truck1, in_city(loc_to, city)), True)

    load_airplane = InstantaneousAction("load_airplane", loc = airport, obj=package)
    loc = load_airplane.parameter("loc")
    obj = load_airplane.parameter("obj")
    load_airplane.add_precondition(at(obj, loc))
    load_airplane.add_precondition(pos(loc))
    load_airplane.add_effect(at(obj, loc), False)
    load_airplane.add_effect(on(obj), True)

    unload_airplane = InstantaneousAction("unload_airplane", loc = airport, obj=package)
    loc = load_airplane.parameter("loc")
    obj = load_airplane.parameter("obj")
    unload_airplane.add_precondition(on(obj))
    unload_airplane.add_precondition(pos(loc))
    unload_airplane.add_effect(on(obj), False)
    unload_airplane.add_effect(at(obj, loc), True)

    fly_airplane = InstantaneousAction("fly_airplane", loc_from=airport, loc_to=airport)
    loc_from = fly_airplane.parameter("loc_from")
    loc_to = fly_airplane.parameter("loc_to")
    fly_airplane.add_precondition(pos(loc_from))
    fly_airplane.add_effect(pos(loc_from), False)
    fly_airplane.add_effect(pos(loc_to), True)

    truck1.add_action(drive_truck)
    truck1.add_action(unload_truck)
    truck1.add_action(load_truck)
    truck2.add_action(drive_truck)
    truck2.add_action(unload_truck)
    truck2.add_action(load_truck)
    airplane.add_action(load_airplane)
    airplane.add_action(unload_airplane)
    airplane.add_action(fly_airplane)
    problem.add_agent(truck1)
    problem.add_agent(truck2)
    problem.add_agent(airplane)


    #problem-ma_pddl_driver1
    obj21 = Object("obj21", package)
    obj22 = Object("obj22", package)
    obj23 = Object("obj23", package)
    obj11 = Object("obj11", package)
    obj13 = Object("obj13", package)
    obj12 = Object("obj12", package)
    apt2 = Object("apt2", airport)
    apt1 = Object("apt1", airport)
    pos1 = Object("pos1", location)
    #tru1 = Object("tru1", truck_)
    cit1 = Object("cit1", city)
    #private tru2
    pos2 = Object("pos2", location)
    #tru2 = Object("tru2", truck_)
    cit2 = Object("cit2", city)

    #private apn1
    #apn1 = Object("apn1", airplane_)

    problem.add_object(obj21)
    problem.add_object(obj22)
    problem.add_object(obj23)
    problem.add_object(obj11)
    problem.add_object(obj13)
    problem.add_object(obj12)
    problem.add_object(apt2)
    problem.add_object(apt1)
    problem.add_object(pos1)
    #problem.add_object(tru1)
    problem.add_object(cit1)
    problem.add_object(pos2)
    #problem.add_object(tru2)
    problem.add_object(cit2)
    #problem.add_object(apn1)

    #problem.set_initial_value(at(tru1, pos1), True)
    problem.set_initial_value(Dot(truck1, pos(pos1)), True)
    #problem.set_initial_value(pos(tru1, pos1), True)
    problem.set_initial_value(at(obj11, pos1), True)
    problem.set_initial_value(at(obj12, pos1), True)
    problem.set_initial_value(at(obj13, pos1), True)
    problem.set_initial_value(Dot(truck1, in_city(pos1, cit1)), True)
    problem.set_initial_value(Dot(truck1, in_city(apt1, cit1)), True)
    problem.set_initial_value(Dot(truck1, pos(pos1)), True)

    #driver2_problem
    #problem.set_initial_value(at(tru2, pos2), True)
    problem.set_initial_value(Dot(truck2, pos(pos2)), True)
    problem.set_initial_value(at(obj21, pos2), True)
    problem.set_initial_value(at(obj22, pos2), True)
    problem.set_initial_value(at(obj23, pos2), True)
    problem.set_initial_value(Dot(truck2, in_city(pos2, cit2)), True)
    problem.set_initial_value(Dot(truck2, in_city(apt2, cit2)), True)
    problem.set_initial_value(Dot(truck2, pos(pos2)), True)
    #airplane_problem
    #problem.set_initial_value(at(apn1, apt2), True)
    problem.set_initial_value(Dot(airplane, pos(apt2)), True)
    problem.set_initial_value(at(obj11, pos1), True)
    problem.set_initial_value(at(obj12, pos1), True)
    problem.set_initial_value(at(obj13, pos1), True)
    problem.set_initial_value(Dot(airplane, pos(apt2)), True)

    problem.add_goal(at(obj11, apt1))
    problem.add_goal(at(obj23, pos1))
    problem.add_goal(at(obj13, apt1))
    problem.add_goal(at(obj21, pos1))


    w = MAPDDLWriter(problem)
    w.write_ma_domain('logistic')
    w.write_ma_problem('logistic')



    plan = None
    logistic = Example(problem=problem, plan=plan)
    problems["ma_logistic"] = logistic
    return problems


problems = get_example_problems()
problem = problems["ma_logistic"].problem

with OneshotPlanner(name='fmap') as planner:
    result = planner.solve(problem, None, "2")
    all_sequential_plans =  result.plan.all_sequential_plans()
    count = 0
    for i in all_sequential_plans:
        print(i)
        count += 1
    print("countcountcountcountcountcountcountcountcount", count)
    if result.status == up.engines.PlanGenerationResultStatus.SOLVED_SATISFICING:
        print("FMAP returned: %s" % result.plan, result.plan.all_sequential_plans())
        #print("FMAP returned: %s" % result.plan, result.plan.get_neighbors())
        print("Adjacency list:", result.plan.get_adjacency_list)
        print("result:", result)
        print("Genero grafo", result.plan.get_graph_file('ma_logistic'))
    else:
        print("Log Error:", result)
