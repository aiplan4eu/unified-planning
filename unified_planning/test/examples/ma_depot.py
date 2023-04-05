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

    # basic multi agent
    place = UserType("place")
    locatable = UserType("locatable")
    # driver = UserType("driver")
    # depot = UserType("depot", place)
    # distributor = UserType("distributor", place)
    truck = UserType("truck", locatable)
    hoist = UserType("hoist", locatable)
    surface = UserType("surface", locatable)

    pallet = UserType("pallet", surface)
    crate = UserType("crate", surface)

    pos = Fluent("pos", place=place)

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

    problem = MultiAgentProblem("depot")

    depot0_a = Agent("depot0_agent", problem)
    distributor0_a = Agent("distributor0_agent", problem)
    distributor1_a = Agent("distributor1_agent", problem)
    driver0_a = Agent("driver0_agent", problem)
    driver1_a = Agent("driver1_agent", problem)

    problem.ma_environment.add_fluent(at, default_initial_value=False)
    problem.ma_environment.add_fluent(on, default_initial_value=False)
    problem.ma_environment.add_fluent(In, default_initial_value=False)
    problem.ma_environment.add_fluent(clear, default_initial_value=False)
    depot0_a.add_private_fluent(lifting, default_initial_value=False)
    # depot0_a.add_fluent(available, default_initial_value=False)
    depot0_a.add_private_fluent(available, default_initial_value=False)

    distributor0_a.add_private_fluent(lifting, default_initial_value=False)
    # distributor0_a.add_fluent(available, default_initial_value=False)
    distributor0_a.add_private_fluent(available, default_initial_value=False)

    distributor1_a.add_private_fluent(lifting, default_initial_value=False)
    # distributor1_a.add_fluent(available, default_initial_value=False)
    distributor1_a.add_private_fluent(available, default_initial_value=False)

    driver0_a.add_private_fluent(driving, default_initial_value=False)
    driver1_a.add_private_fluent(driving, default_initial_value=False)

    depot0_a.add_public_fluent(pos, default_initial_value=False)
    distributor0_a.add_public_fluent(pos, default_initial_value=False)
    distributor1_a.add_public_fluent(pos, default_initial_value=False)
    driver0_a.add_public_fluent(pos, default_initial_value=False)
    driver1_a.add_public_fluent(pos, default_initial_value=False)


    drive = InstantaneousAction("drive", x=truck, y=place, z=place)
    x = drive.parameter("x")
    y = drive.parameter("y")
    z = drive.parameter("z")

    drive.add_precondition(pos(y))
    drive.add_precondition(at(x, y))
    drive.add_precondition(driving(x))
    drive.add_effect(pos(z), True)
    drive.add_effect(pos(y), False)
    drive.add_effect(at(x, z), True)
    drive.add_effect(at(x, y), False)

    lift = InstantaneousAction("lift", p=place, x=hoist, y=crate, z=surface)
    p = lift.parameter("p")
    x = lift.parameter("x")
    y = lift.parameter("y")
    z = lift.parameter("z")

    lift.add_precondition(pos(p))
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

    drop.add_precondition(pos(p))
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

    load.add_precondition(pos(p))
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

    unload.add_precondition(pos(p))
    unload.add_precondition(at(x, p))
    unload.add_precondition(at(z, p))
    unload.add_precondition(available(x))
    unload.add_precondition(In(y, z))

    unload.add_effect(lifting(x, y), True)
    unload.add_effect(In(y, z), False)
    unload.add_effect(available(x), False)


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

    problem.add_agent(depot0_a)
    problem.add_agent(distributor0_a)
    problem.add_agent(distributor1_a)
    problem.add_agent(driver0_a)
    problem.add_agent(driver1_a)

    truck0 = Object("truck0", truck)
    truck1 = Object("truck1", truck)
    depot0_place = Object("depot0_place", place)
    distributor0_place = Object("distributor0_place", place)
    distributor1_place = Object("distributor1_place", place)
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

    problem.set_initial_value(
        Dot(driver0_a, pos(distributor1_place)), True
    )  # controllare se è distrib_0 o _1
    problem.set_initial_value(Dot(driver1_a, pos(depot0_place)), True)
    problem.set_initial_value(Dot(depot0_a, pos(depot0_place)), True)
    problem.set_initial_value(Dot(depot0_a, available(hoist0)), True)
    problem.set_initial_value(Dot(distributor0_a, available(hoist1)), True)
    problem.set_initial_value(Dot(distributor1_a, available(hoist2)), True)

    problem.set_initial_value(Dot(distributor0_a, pos(distributor0_place)), True)
    problem.set_initial_value(Dot(distributor1_a, pos(distributor1_place)), True)

    problem.set_initial_value(Dot(driver0_a, driving(truck0)), True)
    problem.set_initial_value(Dot(driver1_a, driving(truck1)), True)

    problem.add_goal(on(crate0, pallet2))
    problem.add_goal(on(crate1, pallet1))
    #problem.add_goal(Dot(depot0_a, pos(distributor0_place)))

    plan = None
    depot = Example(problem=problem, plan=plan)
    problems["depot_mix"] = depot
    return problems


problems = get_example_problems()
problem = problems["depot_mix"].problem
"""from unified_planning.model.walkers import Dnf
from unified_planning.engines.compilers.disjunctive_conditions_remover import *
env = problem.environment
dnf = Dnf(env)
new_problem = MultiAgentProblem("ok")
ag1 = Agent("ag1", new_problem)
new_problem.add_agent(ag1)
remover = DisjunctiveConditionsRemover()
new_to_old: Dict[Action, Optional[Action]] = {}
for a in problem.agent("driver0_agent").actions:
    print(a)
    if isinstance(a, InstantaneousAction):
        new_precond = dnf.get_dnf_expression(
            env.expression_manager.And(a.preconditions)
        )
        print(new_precond)

        if new_precond.is_or():
            for and_exp in new_precond.args:
                na = remover._create_new_action_with_given_precond(
                    new_problem, and_exp, a, dnf
                )
                if na is not None:
                    new_to_old[na] = a
                    ag1.add_action(na)
        else:
            na = remover._create_new_action_with_given_precond(
                new_problem, new_precond, a, dnf
            )
            if na is not None:
                new_to_old[na] = a
                ag1.add_action(na)

    if isinstance(a, InstantaneousAction):
        new_precond = dnf.get_dnf_expression(
            env.expression_manager.And(a.preconditions)
        )
        if new_precond.is_or():
            for and_exp in new_precond.args:
                na = remover._create_new_action_with_given_precond(
                    new_problem, and_exp, a, dnf
                )
                if na is not None:
                    new_to_old[na] = a
                    new_problem.add_action(na)
        else:
            na = remover._create_new_action_with_given_precond(
                new_problem, new_precond, a, dnf
            )
            if na is not None:
                new_to_old[na] = a
                ag1.add_action(na)
print("oooooooooooooooooo", ag1)
from unified_planning.engines.compilers.ma_disjunctive_conditions_remover import *
ok = MA_DisjunctiveConditionsRemover()"""
with Compiler(
        problem_kind=problem.kind,
        compilation_kind=CompilationKind.MA_DISJUNCTIVE_CONDITIONS_REMOVING
) as DISJUNCTIVE:
    # After we have the compiler, we get the compilation result
    cer_result = DISJUNCTIVE.compile(
        problem,
        CompilationKind.MA_DISJUNCTIVE_CONDITIONS_REMOVING
    )
    cer_problem = cer_result.problem
    cer_kind = cer_problem.kind

    # Check the result of the compilation
    # assert original_problem_kind.has_conditional_effects()
    # assert qr_kind.has_conditional_effects()
    #assert not cer_kind.has_conditional_effects()

print(cer_kind, cer_problem,"\n\n\n\n")
breakpoint()
w = MAPDDLWriter(problem)
print("\n\n\n --------------------DOMAIN-------------------------------------------")
# ok = w.get_ma_problem_agent('depot0_agent')
w.print_ma_domain_agent("depot0_agent")
w.print_ma_problem_agent("depot0_agent")
# print("oooooooo", ok)
w.write_ma_domain("depot2")
print("\n\n\n -------------------PROBLEM-------------------------------------------")
w.write_ma_problem("depot2")

print("problemproblem", problem)
with OneshotPlanner(name='fmap') as planner:
    result = planner.solve(problem)
    if result.status == up.engines.PlanGenerationResultStatus.SOLVED_SATISFICING:
        for seq_plan in result.plan.all_sequential_plans():
            print("\n seq_planseq_plan:",seq_plan)
        #print("FMAP returned: %s" % result.plan.to_sequential_plan())
        print("\n\n FMAP returned: %s" % result.plan.get_adjacency_list)
        print("oooooooooooooooooo", result.plan.get_graph_file('ciaooooo'))


        #print("\n\n FMAP returned: %s" % result.plan.get_neighbors())
    else:
        print("No plan found.", result)


with OneshotPlanner(problem_kind=problem.kind) as planner:
    if planner.supports(problem.kind):
        result = planner.solve(problem)
        print(result.plan, "Ooooooooooooooooooooooooo", problem.kind)
        with PlanValidator(problem_kind=problem.kind,plan_kind=result.plan.kind) as validator:
            print("Okkkkkkkkkkkk")
            #ok = validator.supports_plan(plan_kind)
            #print(ok, "aaaaaaaaaaaaaaaaaaaaa")
            #check = validator.validate(problem, result.plan)
            #self.assertTrue(check)
# ok = Equals(Dot(agent1, location), Dot(agent2, location))
#plan = result.plan
#with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as validator:
#    if validator.validate(problem, plan):
#        print('The plan is valid')
#    else:
#        print('The plan is invalid')

def get_example_problems2():
    problems = {}

    # basic multi agent
    problem = MultiAgentProblem("ma-basic")

    Location = UserType("Location")

    is_connected = Fluent("is_connected", BoolType(), l1=Location, l2=Location)
    problem.ma_environment.add_fluent(is_connected, default_initial_value=False)

    r = Agent("robot", problem)
    pos = Fluent("pos", Location)
    r.add_fluent(pos)
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Equals(pos, l_from))
    move.add_precondition(is_connected(l_from, l_to))
    move.add_effect(pos, l_to)
    r.add_action(move)
    problem.add_agent(r)

    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem.add_objects([l1, l2])

    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(Dot(r, pos), l1)
    problem.add_goal(Equals(Dot(r, pos), l2))

    plan = up.plans.SequentialPlan(
        [up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)), r)]
    )

    basic = Example(problem=problem, plan=plan)
    problems["ma-basic"] = basic
    return problems


"""problems = get_example_problems2()
problem = problems["ma-basic"].problem
#print(problem.agents)

w = PDDLWriter(problem)
print("\n\n\n --------------------DOMAIN-------------------------------------------")
w.print_domain()
print("\n\n\n -------------------PROBLEM-------------------------------------------")
w.print_problem()"""


"""def ciao():
    problems = {}

    # robot
    Location = UserType("Location")
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    battery_charge = Fluent("battery_charge", RealType(0, 100))
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(GE(battery_charge, 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(
    robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_effect(battery_charge, Minus(battery_charge, 10))
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot")
    problem.add_fluent(robot_at)
    problem.add_fluent(battery_charge)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(battery_charge, 100)
    problem.add_goal(robot_at(l2))
    plan = up.plans.SequentialPlan(
        [up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)))]
    )
    robot = Example(problem=problem, plan=plan)
    problems["robot"] = robot

    with OneshotPlanner(name='enhsp') as planner:
        result = planner.solve(problem)
        if result.status == up.engines.PlanGenerationResultStatus.SOLVED_SATISFICING:
            print("Pyperplan returned: %s" % result)
        else:
            print("No plan found.")

ciao()"""
