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

Example = namedtuple("Example", ["problem", "plan"])


def get_example_problems():
    problems = {}

    # basic multi agent

    place = UserType("place")
    locatable = UserType("locatable")
    # driver = UserType("driver")

    depot = UserType("depot", place)
    distributor = UserType("distributor", place)

    truck = UserType("truck", locatable)
    hoist = UserType("hoist", locatable)
    surface = UserType("surface", locatable)

    pallet = UserType("pallet", surface)
    crate = UserType("crate", surface)

    pos = Fluent("pos", BoolType(), place=place)

    at = Fluent("at", BoolType(), locatable=locatable, place=place)
    on = Fluent("on", BoolType(), crate=crate, surface=surface)
    In = Fluent("in", BoolType(), crate=crate, truck=truck)
    clear = Fluent("clear", BoolType(), surface=surface)

    # Da mettere nell'agente (PRIVATI)
    # lifting = Fluent("lifting", a=place, hoist=hoist, crate=crate)
    # available = Fluent("available", a=place, hoist=hoist)
    # driving = Fluent("driving", a=driver, truck=truck)

    # Avaiable e lifting sostituiti con Avaiable_ e lifting
    available = Fluent("available", hoist=hoist)
    lifting = Fluent("lifting", hoist=hoist, crate=crate)
    driving = Fluent("driving", truck=truck)

    drive = InstantaneousAction("drive", x=truck, y=place, z=place)
    x = drive.parameter("x")
    y = drive.parameter("y")
    z = drive.parameter("z")

    drive.add_precondition(at(x, y))
    drive.add_precondition(driving(x))
    drive.add_effect(at(x, z), True)
    drive.add_effect(at(x, y), False)

    lift = InstantaneousAction("lift", p=place, x=hoist, y=crate, z=surface)
    p = lift.parameter("p")
    x = lift.parameter("x")
    y = lift.parameter("y")
    z = lift.parameter("z")

    lift.add_precondition(at(x, p))
    lift.add_precondition(available(x))
    lift.add_precondition(at(y, p))
    lift.add_precondition(on(y, z))
    lift.add_precondition(clear(y))

    lift.add_effect(lifting(x, y), True)
    lift.add_effect(clear(z), True)
    lift.add_effect(at(y, p), False)
    lift.add_effect(clear(y), False)
    lift.add_effect(available(x), False)
    lift.add_effect(on(y, z), False)

    drop = InstantaneousAction("drop", p=place, x=hoist, y=crate, z=surface)
    p = drop.parameter("p")
    x = drop.parameter("x")
    y = drop.parameter("y")
    z = drop.parameter("z")

    drop.add_precondition(at(x, p))
    drop.add_precondition(at(z, p))
    drop.add_precondition(clear(z))
    drop.add_precondition(lifting(x, y))

    drop.add_effect(available(x), True)
    drop.add_effect(at(y, p), True)
    drop.add_effect(clear(y), True)
    drop.add_effect(on(y, z), True)
    drop.add_effect(lifting(x, y), False)
    drop.add_effect(clear(z), False)

    load = InstantaneousAction("load", p=place, x=hoist, y=crate, z=truck)
    p = load.parameter("p")
    x = load.parameter("x")
    y = load.parameter("y")
    z = load.parameter("z")

    load.add_precondition(at(x, p))
    load.add_precondition(at(z, p))
    load.add_precondition(lifting(x, y))

    load.add_effect(In(y, z), True)
    load.add_effect(available(x), True)
    load.add_effect(lifting(x, y), False)

    unload = InstantaneousAction("unload", p=place, x=hoist, y=crate, z=truck)
    p = unload.parameter("p")
    x = unload.parameter("x")
    y = unload.parameter("y")
    z = unload.parameter("z")

    unload.add_precondition(at(x, p))
    unload.add_precondition(at(z, p))
    unload.add_precondition(available(x))
    unload.add_precondition(In(y, z))

    unload.add_effect(lifting(x, y), True)
    unload.add_effect(In(y, z), False)
    unload.add_effect(available(x), False)

    problem = MultiAgentProblem("depot")

    depot0_a = Agent("depot0_a", problem)
    distributor0_a = Agent("distributor0_a", problem)
    distributor1_a = Agent("distributor1_a", problem)
    driver0_a = Agent("driver0_a", problem)
    driver1_a = Agent("driver1_a", problem)
    env = MAEnvironment(problem)

    driver0_a.add_action(drive)
    driver1_a.add_action(drive)

    depot0_a.add_action(lift)
    depot0_a.add_action(drop)
    depot0_a.add_action(load)
    depot0_a.add_action(unload)

    distributor0_a.add_action(lift)
    distributor0_a.add_action(drop)
    distributor0_a.add_action(load)
    distributor0_a.add_action(unload)

    distributor1_a.add_action(lift)
    distributor1_a.add_action(drop)
    distributor1_a.add_action(load)
    distributor1_a.add_action(unload)

    env.add_fluent(at, default_initial_value=False)
    env.add_fluent(on, default_initial_value=False)
    env.add_fluent(In, default_initial_value=False)
    env.add_fluent(clear, default_initial_value=False)
    depot0_a.add_fluent(lifting, default_initial_value=False)
    # depot0_a.add_fluent(available, default_initial_value=False)
    depot0_a.add_fluent(available, default_initial_value=False)

    distributor0_a.add_fluent(lifting, default_initial_value=False)
    # distributor0_a.add_fluent(available, default_initial_value=False)
    distributor0_a.add_fluent(available, default_initial_value=False)

    distributor1_a.add_fluent(lifting, default_initial_value=False)
    # distributor1_a.add_fluent(available, default_initial_value=False)
    distributor1_a.add_fluent(available, default_initial_value=False)

    driver0_a.add_fluent(driving, default_initial_value=False)
    driver1_a.add_fluent(driving, default_initial_value=False)

    depot0_a.add_fluent(pos)
    distributor0_a.add_fluent(pos)
    distributor1_a.add_fluent(pos)
    driver0_a.add_fluent(pos)
    driver1_a.add_fluent(pos)

    problem.add_agent(depot0_a)
    problem.add_agent(distributor0_a)
    problem.add_agent(distributor1_a)
    problem.add_agent(driver0_a)
    problem.add_agent(driver1_a)

    truck0 = Object("truck0", truck)
    truck1 = Object("truck1", truck)
    depot0_place = Object("depot0_place", depot)
    distributor0_place = Object("distributor0_place", distributor)
    distributor1_place = Object("distributor1_place", distributor)
    crate0 = Object("crate0", crate)
    crate1 = Object("crate1", crate)
    pallet0 = Object("pallet0", pallet)
    pallet1 = Object("pallet1", pallet)
    pallet2 = Object("pallet2", pallet)

    # oggetti privati
    hoist0 = Object("hoist0", hoist)
    hoist1 = Object("hoist1", hoist)
    hoist2 = Object("hoist2", hoist)
    # driver0 = Object("driver0", driver)
    # driver1 = Object("driver1", driver)

    problem.add_object(crate0)
    problem.add_object(crate1)
    problem.add_object(truck0)  # agente
    problem.add_object(truck1)  # agente
    problem.add_object(depot0_place)  # agente
    problem.add_object(distributor0_place)  # agente
    problem.add_object(distributor1_place)  # agente
    problem.add_object(pallet0)
    problem.add_object(pallet1)
    problem.add_object(pallet2)
    problem.add_object(hoist0)
    problem.add_object(hoist1)
    problem.add_object(hoist2)
    # problem.add_object(driver0) #agente
    # problem.add_object(driver1) #agente

    problem.set_initial_value(at(pallet0, depot0_place), True)
    problem.set_initial_value(clear(crate1), True)
    problem.set_initial_value(at(pallet1, distributor0_place), True)
    problem.set_initial_value(clear(crate0), True)
    problem.set_initial_value(at(pallet2, distributor1_place), True)
    problem.set_initial_value(clear(pallet2), True)

    problem.set_initial_value(at(truck0, distributor1_place), True)
    problem.set_initial_value(at(truck1, depot0_place), True)
    problem.set_initial_value(at(hoist0, depot0_place), True)
    # problem.set_initial_value(available(depot0_place, hoist0), True)
    problem.set_initial_value(at(hoist1, distributor0_place), True)
    # problem.set_initial_value(available(distributor0_place, hoist1), True)
    problem.set_initial_value(at(hoist2, distributor1_place), True)
    # problem.set_initial_value(available(distributor1_place, hoist2), True)
    problem.set_initial_value(at(crate0, distributor0_place), True)
    problem.set_initial_value(on(crate0, pallet1), True)
    problem.set_initial_value(at(crate1, depot0_place), True)
    problem.set_initial_value(on(crate1, pallet0), True)

    # problem.set_initial_value(Dot(driver0_a, pos(distributor0_place)), True)
    # problem.set_initial_value(Dot(driver1_a, pos(depot0_place)), True)
    problem.set_initial_value(Dot(depot0_a, pos(depot0_place)), True)
    problem.set_initial_value(Dot(depot0_a, available(hoist0)), True)
    problem.set_initial_value(Dot(distributor0_a, available(hoist1)), True)
    problem.set_initial_value(Dot(distributor1_a, available(hoist2)), True)

    problem.set_initial_value(Dot(distributor0_a, pos(distributor0_place)), True)
    problem.set_initial_value(Dot(distributor1_a, pos(distributor1_place)), True)

    problem.add_goal(on(crate0, pallet2))
    problem.add_goal(on(crate1, pallet1))

    plan = None
    depot = Example(problem=problem, plan=plan)
    problems["depot_mix"] = depot
    return problems


problems = get_example_problems()
problem = problems["depot_mix"].problem
from unified_planning.io.pddl_writer import PDDLWriter

print(problem)
breakpoint()
w = PDDLWriter(problem)
print("\n\n\n --------------------DOMAIN-------------------------------------------")
w.print_domain()
print("\n\n\n -------------------PROBLEM-------------------------------------------")
w.print_problem()

# ok = Equals(Dot(agent1, location), Dot(agent2, location))
