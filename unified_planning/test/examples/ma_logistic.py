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
    driver1 = Agent("driver1", problem)
    driver2 = Agent("driver2", problem)
    driver3 = Agent("driver3", problem)

    object = UserType("object")
    location = UserType("location", object)
    vehicle = UserType("vehicle", object)
    package = UserType("package", object)
    city = UserType("city", object)
    airport = UserType("airport", location)
    #obj = UserType("obj")
    truck = UserType("truck", vehicle) #agente
    airplane = UserType("airplane", vehicle) #agente


    pos = Fluent("pos", location=location)
    at = Fluent("at", BoolType(), object=object, location=location)
    In = Fluent("in", BoolType(), package=package, vehicle=vehicle)
    on = Fluent("on", BoolType(), object=object)
    # Da mettere nell'agente (PRIVATI)
    in_city = Fluent("in_city", BoolType(), location=location, city=city)
    driving = Fluent("driving", truck=truck)
    driving_p = Fluent("driving_p", airplane=airplane)

    driver1.add_fluent(pos, default_initial_value=False)
    driver1.add_fluent(in_city, default_initial_value=False)
    driver1.add_fluent(driving, default_initial_value=False)
    driver2.add_fluent(pos, default_initial_value=False)
    driver2.add_fluent(in_city, default_initial_value=False)
    driver2.add_fluent(driving, default_initial_value=False)
    driver3.add_fluent(pos, default_initial_value=False)
    driver3.add_fluent(driving_p, default_initial_value=False)
    problem.ma_environment.add_fluent(at, default_initial_value=False)
    problem.ma_environment.add_fluent(on, default_initial_value=False)
    problem.ma_environment.add_fluent(In, default_initial_value=False)

    city_ = Object("city_", city)
    truck_ = Object("truck_", truck)
    obj = Object("obj", package)
    loc = Object("loc", location)
    loc_from = Object("loc_from", location)
    loc_to = Object("loc_to", location)
    airplane_ = Object("airplane_", airplane)

    load_truck = InstantaneousAction("load_truck")
    #truck = load_truck.parameter("truck")
    #obj = load_truck.parameter("obj")
    #loc = load_truck.parameter("loc")

    #load_truck.add_precondition(pos(y))
    #load_truck.add_precondition(Dot(truck1, pos(loc))) #se avessi potuto mettere il dot negli effect
    load_truck.add_precondition(at(truck_, loc))
    load_truck.add_precondition(at(obj, loc))
    load_truck.add_precondition(pos(loc))
    load_truck.add_effect(at(obj, loc), False)
    load_truck.add_effect(In(obj, truck_), True)
    #load_truck.add_effect(On(obj), False)
    #non posso fare:
    #load_truck.add_effect(Dot(truck1, On(obj)), True)
    #Perchè non è possibile inserire il dot negli effetti.

    #Cosa strana dopo aver definito i parametri per una azione non posso definire gli stessi parametri per un altra
    unload_truck = InstantaneousAction("unload_truck")
    #truck = unload_truck.parameter("truck")
    #obj = unload_truck.parameter("obj")
    #loc = unload_truck.parameter("loc")

    #load_truck.add_precondition(pos(y))
    #load_truck.add_precondition(Dot(truck1, pos(loc))) #se avessi potuto mettere il dot negli effect
    unload_truck.add_precondition(at(truck_, loc))
    unload_truck.add_precondition(In(obj, truck_))
    unload_truck.add_precondition(pos(loc))
    unload_truck.add_effect(In(obj, truck_), False)
    unload_truck.add_effect(at(obj, loc), True)


    drive_truck = InstantaneousAction("drive_truck")
    #loc_from = drive_truck.parameter("loc_from")
    #loc_to = drive_truck.parameter("loc_to")
    # load_truck.add_precondition(pos(y))
    # load_truck.add_precondition(Dot(truck1, pos(loc))) #se avessi potuto mettere il dot negli effect
    drive_truck.add_precondition(at(truck_, loc_from))
    drive_truck.add_precondition(in_city(loc_from, city_))
    drive_truck.add_precondition(in_city(loc_to, city_))
    drive_truck.add_precondition(driving(truck_))
    drive_truck.add_precondition(pos(loc_from))
    #drive_truck.add_precondition(in_city(truck, loc_to, city))
    drive_truck.add_effect(pos(loc_from), False)
    drive_truck.add_effect(at(truck_, loc_from), False)
    drive_truck.add_effect(at(truck_, loc_to), True)
    drive_truck.add_effect(pos(loc_to), True)
    #drive_truck.add_effect(Dot(driver1, in_city(loc_to, city)), True)

    load_airplane = InstantaneousAction("load_airplane", loc = airport)
    loc = load_airplane.parameter("loc")
    load_airplane.add_precondition(at(obj, loc))
    load_airplane.add_precondition(at(airplane_, loc))
    load_airplane.add_precondition(pos(loc))
    load_airplane.add_effect(at(obj, loc), False)
    load_airplane.add_effect(In(obj, airplane_), True)

    unload_airplane = InstantaneousAction("unload_airplane", loc = airport)
    loc = unload_airplane.parameter("loc")
    unload_airplane.add_precondition(In(obj, airplane_))
    unload_airplane.add_precondition(at(airplane_, loc))
    unload_airplane.add_precondition(pos(loc))
    unload_airplane.add_effect(In(obj, airplane_), False)
    unload_airplane.add_effect(at(obj, loc), True)

    fly_airplane = InstantaneousAction("fly_airplane")
    fly_airplane.add_precondition(at(airplane_, loc_from))
    fly_airplane.add_precondition(pos(loc_from))
    fly_airplane.add_precondition(driving_p(airplane_))
    fly_airplane.add_effect(at(airplane_, loc_from), False)
    fly_airplane.add_effect(at(airplane_, loc_to), True)
    fly_airplane.add_effect(pos(loc_to), True)

    driver1.add_action(drive_truck)
    driver1.add_action(unload_truck)
    driver1.add_action(load_truck)
    driver2.add_action(drive_truck)
    driver2.add_action(unload_truck)
    driver2.add_action(load_truck)
    driver3.add_action(load_airplane)
    driver3.add_action(unload_airplane)
    driver3.add_action(fly_airplane)
    problem.add_agent(driver1)
    problem.add_agent(driver2)
    problem.add_agent(driver3)

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
    tru1 = Object("tru1", truck)
    cit1 = Object("cit1", city)
    #private tru2
    pos2 = Object("pos2", location)
    tru2 = Object("tru2", truck)
    cit2 = Object("cit2", city)

    #private apn1
    apn1 = Object("apn1", airplane)

    problem.add_object(obj21)
    problem.add_object(obj22)
    problem.add_object(obj23)
    problem.add_object(obj11)
    problem.add_object(obj13)
    problem.add_object(obj12)
    problem.add_object(apt2)
    problem.add_object(apt1)
    problem.add_object(pos1)
    problem.add_object(tru1)
    problem.add_object(cit1)
    problem.add_object(pos2)
    problem.add_object(tru2)
    problem.add_object(cit2)
    problem.add_object(apn1)

    problem.set_initial_value(at(tru1, pos1), True)
    problem.set_initial_value(at(obj11, pos1), True)
    problem.set_initial_value(at(obj12, pos1), True)
    problem.set_initial_value(at(obj13, pos1), True)
    problem.set_initial_value(Dot(driver1, in_city(pos1, cit1)), True)
    problem.set_initial_value(Dot(driver1, in_city(apt1, cit1)), True)
    problem.set_initial_value(Dot(driver1, driving(tru1)), True)
    problem.set_initial_value(Dot(driver1, pos(pos1)), True)

    #driver2_problem
    problem.set_initial_value(at(tru2, pos2), True)
    problem.set_initial_value(at(obj21, pos2), True)
    problem.set_initial_value(at(obj22, pos2), True)
    problem.set_initial_value(at(obj23, pos2), True)
    problem.set_initial_value(Dot(driver2, in_city(pos2, cit2)), True)
    problem.set_initial_value(Dot(driver2, in_city(apt2, cit2)), True)
    problem.set_initial_value(Dot(driver2, driving(tru2)), True)
    problem.set_initial_value(Dot(driver2, pos(pos2)), True)
    #airplane_problem
    problem.set_initial_value(at(apn1, apt2), True)
    problem.set_initial_value(at(obj11, pos1), True)
    problem.set_initial_value(at(obj12, pos1), True)
    problem.set_initial_value(at(obj13, pos1), True)
    problem.set_initial_value(Dot(driver3, driving_p(apn1)), True)
    problem.set_initial_value(Dot(driver3, pos(apt2)), True)

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
    result = planner.solve(problem, None, "1")
    if result.status == up.engines.PlanGenerationResultStatus.SOLVED_SATISFICING:
        print("FMAP returned: %s" % result.plan, result.plan.to_sequential_plan())
        print("Adjacency list:", result.plan.get_adjacency_list)
        print("result:", result)
    else:
        print("Log Error:", result)
