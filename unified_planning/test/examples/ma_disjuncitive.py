from unified_planning.shortcuts import *
from unified_planning.model.multi_agent import *
from collections import namedtuple
from unified_planning.io.ma_pddl_writer import MAPDDLWriter

#TYPEs
Location = UserType("Location")
PouchObj = UserType("PouchObj")
Door = UserType("Door")
StateG = UserType("StateG")
#FLUENTS
stateDoor = Fluent("stateDoor", Door=Door)
at = Fluent("at", loc=Location)
pouchAt = Fluent("pouchAt", BoolType(), pouch=PouchObj, loc=Location)
inStateG = Fluent("inStateG", stateGrip=StateG)
#OBJECTS
home = Object("home", Location)
office = Object("office", Location)
vision2 = Object("vision2", Location)
open20 = Object("open20", Door)
close20 = Object("close20", Door)
startState = Object("startState", StateG)
active = Object("active", StateG)
pouch1 = Object("pouch1", PouchObj)

problem = MultiAgentProblem("P&G")

#AGENTs
robot_a = Agent("robot_a", problem)
scale_a = Agent("scale_a", problem)

robot_a.add_public_fluent(at, default_initial_value=False)
robot_a.add_private_fluent(inStateG, default_initial_value=False)
scale_a.add_public_fluent(stateDoor, default_initial_value=False)
problem.ma_environment.add_fluent(pouchAt, default_initial_value=False)

#ACTIONS

movegripper_activate = InstantaneousAction("movegripper_activate")
movegripper_activate.add_precondition(inStateG(startState))
movegripper_activate.add_effect(inStateG(active), True)
movegripper_activate.add_effect(inStateG(startState), False)

movegripper_move = InstantaneousAction("movegripper_move")
movegripper_move.add_precondition(
    inStateG(active))
movegripper_move.add_precondition(at(office))
movegripper_move.add_effect(at(home), True)
movegripper_move.add_effect(at(office), False)

open_door = InstantaneousAction("open_door")
open_door.add_precondition(stateDoor(close20))
open_door.add_precondition(Or( Dot(robot_a, at(office)), Dot(robot_a, at(home))))
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

#INITIAL VALUEs
problem.set_initial_value(Dot(robot_a, at(office)), True)
problem.set_initial_value(Dot(robot_a, inStateG(startState)), True)
problem.set_initial_value(Dot(scale_a, stateDoor(close20)), True)

#GOALs
#problem.add_goal(Dot(robot_a, at(home)))
#problem.add_goal(Dot(robot_a, at(home)))
problem.add_goal(Dot(scale_a, stateDoor(open20)))
problem.add_goal(Dot(robot_a, at(home)))
#problem.add_goal(Dot(scale_a, stateDoor(open20)))
#problem.add_goal(pouchAt(pouch1, home) or pouchAt(pouch1, office))
#problem.add_goal(Or(pouchAt(pouch1, home), pouchAt(pouch1, office)))


#problem.add_goal(Or(Dot(scale_a, stateDoor(open20)), Dot(scale_a, stateDoor(close20))))


print(problem.goals, "ooooooooooooooooooooooooo")

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
    #assert original_problem_kind.has_conditional_effects()
    #assert qr_kind.has_conditional_effects()
    #assert cer_kind.has_disjunctive_conditions()
    assert not cer_kind.has_disjunctive_conditions()




#print(cer_problem.agent("scale_a"))
#print(cer_problem.goals)
print(cer_problem)


w = MAPDDLWriter(cer_problem)
w.write_ma_domain("ma_disjuncitive")
w.write_ma_problem("ma_disjuncitive")


with OneshotPlanner(name='fmap') as planner:
    result = planner.solve(cer_problem, None, "2")
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