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


"""problem = MultiAgentProblem("simple_MA")

robot_a = Agent("robot_a", problem)
scale_a = Agent("scale_a", problem)
Location = UserType("Location")
door = UserType("door")

home = Object("home", Location)
office = Object("office", Location)
open20 = Object("open20", door)
close20 = Object("close20", door)

# FLUENTs
at = Fluent("at", loc=Location)
open = Fluent("open", door=door)
on = Fluent("on", BoolType())
pos = Fluent("pos", loc=Location)

#robot_a.add_fluent(at, default_initial_value=False)
robot_a.add_fluent(pos, default_initial_value=False)
scale_a.add_fluent(open, default_initial_value=False)

#ACTIONs
movegripper = InstantaneousAction("movegripper")
#y_var = Variable("y_var", Location)
#movegripper.add_precondition(Iff(Or(Exists(Not(pos(office)), y_var), Not(pos(home))), pos(home)))
#movegripper.add_precondition(And(Or(Not(pos(office)), pos(home)), pos(office)))
#movegripper.add_precondition(Dot(scale_a, open(close20)))
movegripper.add_precondition(pos(office))
movegripper.add_effect(pos(home), True)

open_door = InstantaneousAction("open_door")
open_door.add_precondition(open(close20))
#open_door.add_precondition(Dot(robot_a, pos(home)))
open_door.add_effect(open(open20), True)

robot_a.add_action(movegripper)
scale_a.add_action(open_door)

problem.add_object(home)
problem.add_object(office)
problem.add_object(open20)
problem.add_object(close20)

problem.add_agent(robot_a)
problem.add_agent(scale_a)

problem.set_initial_value(Dot(robot_a, pos(office)), True)
problem.set_initial_value(Dot(scale_a, open(close20)), True)

problem.add_goal(Dot(robot_a, pos(home)))
problem.add_goal(Dot(scale_a, open(open20)))

w = MAPDDLWriter(problem)
w.write_ma_domain("simple_ma")
w.write_ma_problem("simple_ma")

with OneshotPlanner(name='fmap') as planner:
    result = planner.solve(problem, None, "1")
    if result.status == up.engines.PlanGenerationResultStatus.SOLVED_SATISFICING:
        print("FMAP returned: %s" % result.plan, result.plan.all_sequential_plans())
        #print("FMAP returned: %s" % result.plan, result.plan.get_neighbors())
        print("Adjacency list:", result.plan.get_adjacency_list)
        print("result:", result)
    else:
        print("Log Error:", result)


#whit Usertype in action
def simple_ex_ma_with_ut():
    problem = MultiAgentProblem("simple_MA")

    robot_a = Agent("robot_a", problem)
    scale_a = Agent("scale_a", problem)
    Location = UserType("Location")
    door = UserType("door")

    home = UserType("home", Location)
    office = UserType("office", Location)
    open20 = UserType("open20", door)
    close20 = UserType("close20", door)

    # FLUENTs
    open = Fluent("open", door=door)
    pos = Fluent("pos", loc=Location)

    # robot_a.add_fluent(at, default_initial_value=False)
    robot_a.add_fluent(pos, default_initial_value=False)
    scale_a.add_fluent(open, default_initial_value=False)

    # ACTIONs
    movegripper = InstantaneousAction("movegripper", x=office, y=home)
    x = movegripper.parameter("x")
    y = movegripper.parameter("y")
    # y_var = Variable("y_var", Location)
    # movegripper.add_precondition(Iff(Or(Exists(Not(pos(office)), y_var), Not(pos(home))), pos(home)))
    # movegripper.add_precondition(And(Or(Not(pos(office)), pos(home)), pos(office)))
    # movegripper.add_precondition(Dot(scale_a, open(close20)))
    movegripper.add_precondition(pos(x))
    movegripper.add_effect(pos(y), True)

    open_door = InstantaneousAction("open_door", z=close20, w=open20)
    z = open_door.parameter("z")
    w = open_door.parameter("w")
    open_door.add_precondition(open(z))
    # open_door.add_precondition(Dot(robot_a, pos(home)))
    open_door.add_effect(open(w), True)

    robot_a.add_action(movegripper)
    scale_a.add_action(open_door)

    home1 = Object("home1", home)
    office1 = Object("office1", office)
    open20_ = Object("open20_", open20)
    close20_ = Object("close20_", close20)

    problem.add_object(home1)
    problem.add_object(office1)
    problem.add_object(open20_)
    problem.add_object(close20_)

    problem.add_agent(robot_a)
    problem.add_agent(scale_a)

    problem.set_initial_value(Dot(robot_a, pos(office1)), True)
    problem.set_initial_value(Dot(scale_a, open(close20_)), True)

    problem.add_goal(Dot(robot_a, pos(home1)))
    problem.add_goal(Dot(scale_a, open(open20_)))

    w = MAPDDLWriter(problem)
    w.write_ma_domain("simple_ma")
    w.write_ma_problem("simple_ma")

    with OneshotPlanner(name='fmap') as planner:
        result = planner.solve(problem, None, "1")
        if result.status == up.engines.PlanGenerationResultStatus.SOLVED_SATISFICING:
            print("FMAP returned: %s" % result.plan, result.plan.all_sequential_plans())
            # print("FMAP returned: %s" % result.plan, result.plan.get_neighbors())
            print("Adjacency list:", result.plan.get_adjacency_list)
            print("result:", result)
        else:
            print("Log Error:", result)"""

def new_simple_example():
    # TYPEs
    Location = UserType("Location")
    PouchObj = UserType("PouchObj")
    Door = UserType("Door")
    StateG = UserType("StateG")
    # FLUENTS
    stateDoor = Fluent("stateDoor", Door=Door)
    at = Fluent("at", loc=Location)
    pouchAt = Fluent("pouchAt", BoolType(), pouch=PouchObj, loc=Location)
    inStateG = Fluent("inStateG", stateGrip=StateG)
    home = Object("home", Location)
    office = Object("office", Location)
    vision2 = Object("vision2", Location)
    open20 = Object("open20", Door)
    close20 = Object("close20", Door)
    startState = Object("startState", StateG)
    active = Object("active", StateG)
    pouch1 = Object("pouch1", PouchObj)

    problem = MultiAgentProblem("P&G")

    # AGENTs
    robot_a = Agent("robot_a", problem)
    scale_a = Agent("scale_a", problem)

    robot_a.add_public_fluent(at, default_initial_value=False)
    robot_a.add_private_fluent(inStateG, default_initial_value=False)
    scale_a.add_public_fluent(stateDoor, default_initial_value=False)
    problem.ma_environment.add_fluent(pouchAt, default_initial_value=False)
    # ACTIONS

    movegripper_activate = InstantaneousAction("movegripper_activate")
    movegripper_activate.add_precondition(inStateG(startState))
    movegripper_activate.add_effect(inStateG(active), True)
    movegripper_activate.add_effect(inStateG(startState), False)

    movegripper_move = InstantaneousAction("movegripper_move")
    movegripper_move.add_precondition(
        inStateG(active))  ### precondizione che rende necessaria azione 'movegripper_activate'
    movegripper_move.add_precondition(at(office))
    movegripper_move.add_effect(at(home), True)
    movegripper_move.add_effect(at(office), False)

    open_door = InstantaneousAction("open_door")
    open_door.add_precondition(stateDoor(close20))
    open_door.add_precondition(Dot(robot_a, at(home)))  ### precondizione che rende necessaria azione 'movegripper_move'
    #open_door.add_precondition(at(home))
    #open_door.add_precondition(pouchAt(pouch1, vision2))
    open_door.add_effect(stateDoor(open20), True)
    open_door.add_effect(stateDoor(close20), False)

    robot_a.add_action(movegripper_activate)
    robot_a.add_action(movegripper_move)
    scale_a.add_action(open_door)

    problem.add_agent(robot_a)
    problem.add_agent(scale_a)

    problem.add_object(home)
    problem.add_object(office)
    problem.add_object(vision2)
    problem.add_object(open20)
    problem.add_object(close20)
    problem.add_object(startState)
    problem.add_object(active)
    problem.add_object(pouch1)

    # INITIAL VALUEs
    problem.set_initial_value(Dot(robot_a, at(office)), True)
    problem.set_initial_value(Dot(robot_a, inStateG(startState)), True)
    problem.set_initial_value(Dot(scale_a, stateDoor(close20)), True)

    # GOALs
    problem.add_goal(Dot(robot_a, at(home)))
    problem.add_goal(Dot(scale_a, stateDoor(open20)))

    w = MAPDDLWriter(problem)
    w.write_ma_domain("simple_ma")
    w.write_ma_problem("simple_ma")

    with OneshotPlanner(name='fmap') as planner:
        result = planner.solve(problem, None, "1")
        if result.status == up.engines.PlanGenerationResultStatus.SOLVED_SATISFICING:
            print("FMAP returned: %s" % result.plan)
            print("result:", result)
            print("\n")
            print("%s Returned Sequential Plans object: %s" % (planner.name, result.plan.all_sequential_plans()))
            [print(f"{idx} Sequential Plans: {seq_plan}") for idx, seq_plan in
             enumerate(result.plan.all_sequential_plans())]
            print("\n")
            print("Adjacency list:", result.plan.get_adjacency_list)
        else:
            print("Log Error:", result)

#simple_ex_ma_with_ut()
new_simple_example()