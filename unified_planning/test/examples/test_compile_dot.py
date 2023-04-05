# MULTI-AGENT PROBLEM and AGENTS DEFINITION
from unified_planning.shortcuts import *
from unified_planning.model.multi_agent import *
from collections import namedtuple
from unified_planning.io.ma_pddl_writer import MAPDDLWriter


# TYPEs
location = UserType("location")
postureG = UserType("postureG")
stateG = UserType("stateG")
modeG = UserType("modeG")
pouchObj = UserType("pouchObj")

#---------------------------------------------------------------------------

# FLUENTs
at = Fluent("at", BoolType(), loc=location)
pouchAt = Fluent("pouchAt", BoolType(), pouch=pouchObj, loc=location)
pouchIn = Fluent("pouchIn", BoolType(), pouch=pouchObj, deviceOrBin=location)

inPosG = Fluent("inPosG", BoolType(), posture=postureG)
inStateG = Fluent("inStateG", BoolType(), state=stateG)

restLoc = Fluent("restLoc", BoolType(), x=location, device=location)
dropPos = Fluent("dropPos", BoolType(), x=location, device=location)
graspPos = Fluent("graspPos", BoolType(), x=location, device=location)
exitPos = Fluent("exitPos", BoolType(), x=location, device=location)

measuredAt = Fluent("measuredAt", BoolType(), pouch=pouchObj, loc=location)

detected = Fluent("detected", BoolType(), pouch=pouchObj )
grasped = Fluent("grasped", BoolType(), pouch=pouchObj )

graspMode = Fluent("graspMode", BoolType(), pouch=pouchObj, mode=modeG)

reset = Fluent("reset", BoolType(), device=location)

#---------------------------------------------------------------------------

# OBJECTs
home = Object("home", location)
vision2 = Object("vision2", location)
pickup = Object("pickup", location)
pouchpose = Object("pouchpose", location)
bin = Object("bin", location)
scale = Object("scale", location)
scaledown = Object("scaledown", location)
scaleout = Object("scaleout", location)
scalein = Object("scalein", location)
scaleup = Object("scaleup", location)
mark10 = Object("mark10", location)
mark10out = Object("mark10out", location)
mark10out2 = Object("mark10out2", location)
mark10in = Object("mark10in", location)
mark10in2 = Object("mark10in2", location)

default = Object("default", postureG)
grasping = Object("grasping", postureG)
open20 = Object("open20", postureG)
open0 = Object("open0", postureG)

startState = Object("startState", stateG)
active = Object("active", stateG)

horizontal = Object("horizontal", modeG)
vertical = Object("vertical", modeG)

pouch1 = Object("pouch1", pouchObj)
pouch2 = Object("pouch2", pouchObj)
pouch3 = Object("pouch3", pouchObj)

#---------------------------------------------------------------------------
# ACTIONs

movegripper_activate = InstantaneousAction("movegripper_activate")
movegripper_activate.add_precondition(inStateG(startState))
movegripper_activate.add_precondition(Not(inStateG(active)))
movegripper_activate.add_effect(inStateG(active), True)
movegripper_activate.add_effect(inStateG(startState), False)
movegripper_activate.add_effect(inPosG(default), True)
movegripper_activate.add_effect(at(home), True)

movegripper_open20 = InstantaneousAction("movegripper_open20", postFrom=postureG, x=location, y=location, m=modeG, pouch=pouchObj)
postFrom = movegripper_open20.parameter("postFrom")
x = movegripper_open20.parameter("x")
y=  movegripper_open20.parameter("y")
m = movegripper_open20.parameter("m")
pouch = movegripper_open20.parameter("pouch")
movegripper_open20.add_precondition(inStateG(active))
movegripper_open20.add_precondition(inPosG(postFrom))
movegripper_open20.add_precondition(Not(inPosG(open20)))
movegripper_open20.add_precondition(at(x))
movegripper_open20.add_precondition(dropPos(x, y))
p_var = Variable("p_var", pouchObj)   ##########PROVATO pouch AL POSTO DI pouchObj
movegripper_open20.add_effect(inPosG(open20), True)
movegripper_open20.add_effect(inPosG(postFrom), False)
movegripper_open20.add_effect(pouchIn(pouch, y), True, (And (grasped(pouch), graspMode(pouch, m)) ) )   # WHEN CON DOPPIA PRECONDIZIONE (AND)
movegripper_open20.add_effect(pouchAt(pouch, x), False, (And (grasped(pouch), graspMode(pouch, m)) ) )   # WHEN
movegripper_open20.add_effect(graspMode(pouch, m), False, (And (grasped(pouch), graspMode(pouch, m)) ) )   # WHEN
movegripper_open20.add_effect(grasped(pouch), False, (And (grasped(pouch), graspMode(pouch, m)) ) )   # WHEN

movegripper_grasp = InstantaneousAction("movegripper_grasp", postFrom=postureG, x=location, y=location, pouch=pouchObj)
postFrom = movegripper_grasp.parameter("postFrom")
x = movegripper_grasp.parameter("x")
y=  movegripper_grasp.parameter("y")
pouch = movegripper_open20.parameter("pouch")
movegripper_grasp.add_precondition(inStateG(active))
movegripper_grasp.add_precondition(Not(pouchIn(pouch, bin)))
movegripper_grasp.add_precondition(inPosG(postFrom))
movegripper_grasp.add_precondition(Not(inPosG(grasping)))
movegripper_grasp.add_precondition(at(x))
movegripper_grasp.add_precondition(graspPos(x, y))
movegripper_grasp.add_precondition(pouchIn(pouch, y))
movegripper_grasp.add_precondition(Not(grasped(pouch)))
movegripper_grasp.add_effect(inPosG(grasping), True)
movegripper_grasp.add_effect(inPosG(postFrom), False)
movegripper_grasp.add_effect(grasped(pouch), True)
movegripper_grasp.add_effect(pouchAt(pouch, x), True)
movegripper_grasp.add_effect(pouchIn(pouch, y), False)

goto = InstantaneousAction("goto", fromLoc=location, toLoc=location, pouch=pouchObj)
fromLoc = goto.parameter("fromLoc")
toLoc = goto.parameter("toLoc")
pouch = goto.parameter("pouch")
goto.add_precondition(inStateG(active))
goto.add_precondition(at(fromLoc))
y_var = Variable("y_var", location)
goto.add_precondition(Or (Not(inPosG(grasping)), grasped(pouch)) )
goto.add_effect(at(toLoc), True)
goto.add_effect(at(fromLoc), False)
goto.add_effect(pouchAt(pouch, toLoc), True, grasped(pouch))
goto.add_effect(pouchAt(pouch, fromLoc), False, grasped(pouch))

goto_grasp = InstantaneousAction("goto_grasp", fromLoc=location, toLoc=location, pouchWhere=location, m=modeG, pouch=pouchObj)
fromLoc = goto_grasp.parameter("fromLoc")
toLoc = goto_grasp.parameter("toLoc")
pouchWhere = goto_grasp.parameter("pouchWhere")
pouch = goto_grasp.parameter("pouch")
m = goto_grasp.parameter("m")
#goto_grasp.add_precondition(inStateG(active))
goto_grasp.add_precondition(Not(pouchIn(pouch, bin)))
goto_grasp.add_precondition(at(fromLoc))
goto_grasp.add_precondition(pouchIn(pouch, pouchWhere))
goto_grasp.add_precondition(detected(pouch))
goto_grasp.add_precondition(graspPos(toLoc, pouchWhere))
goto_grasp.add_precondition(inPosG(open20))
goto_grasp.add_effect(at(toLoc), True)
goto_grasp.add_effect(at(fromLoc), False)
goto_grasp.add_effect(graspMode(pouch, m), True)

perceptPouch = InstantaneousAction("perceptPouch", pouch=pouchObj)
pouch = perceptPouch.parameter("pouch")
perceptPouch.add_precondition(at(vision2))
perceptPouch.add_effect(detected(pouch), True)
perceptPouch.add_effect(pouchIn(pouch, pouchpose), True)

measure = InstantaneousAction("measure", device=location, rest=location, pouch=pouchObj)
device = measure.parameter("device")
rest = measure.parameter("rest")
pouch = measure.parameter("pouch")

problemMA = MultiAgentProblem("P&G")
scale_a = Agent("scale_a", problemMA)
scale_a.add_fluent(at)
measure.add_precondition(Not((Dot(scale_a, at(rest)))))

measure.add_precondition(pouchIn(pouch, device))
measure.add_precondition(at(rest))
measure.add_precondition(restLoc(rest, device))
measure.add_precondition(reset(device))
measure.add_effect(measuredAt(pouch, device), True)

'''
scale_reset = InstantaneousAction("scale_reset", pouch=pouchObj)
pouch = scale_reset.parameter("pouch")
scale_reset.add_precondition(Not(reset(scale)))
scale_reset.add_precondition(Not(pouchIn(pouch, scale)))
scale_reset.add_effect(reset(scale), True)
'''

# (TAMER) Usando questa azione, più generica anche se inutile nel caso P&G,
# al posto di 'scale_reset', ci impiega 23 minuti per il goal 'measuredAt(pouch1, scale)'
# Invece, usando scale_reset, impiega 1/2 minuti
# (FAST-DOWNWARD) Stessi tempi che usando scale_reset --> lascio azione più generica
resetDev = InstantaneousAction("resetDev", device=location, pouch=pouchObj)
device = resetDev.parameter("device")
pouch = resetDev.parameter("pouch")
resetDev.add_precondition(Not(reset(device)))
resetDev.add_precondition(Not(pouchIn(pouch, device)))
resetDev.add_effect(reset(device), True)


#-------------------------------------------------------------------------------


problem = Problem("P&G")
problem.add_action(movegripper_activate)
problem.add_action(movegripper_open20)
problem.add_action(movegripper_grasp)
problem.add_action(goto)
problem.add_action(goto_grasp)
problem.add_action(perceptPouch)
problem.add_action(measure)
problem.add_action(resetDev)

problem.add_fluent(at, default_initial_value=False)
problem.add_fluent(pouchAt, default_initial_value=False)
problem.add_fluent(pouchIn, default_initial_value=False)
problem.add_fluent(inPosG, default_initial_value=False)
problem.add_fluent(inStateG, default_initial_value=False)
problem.add_fluent(restLoc, default_initial_value=False)
problem.add_fluent(dropPos, default_initial_value=False)
problem.add_fluent(graspPos, default_initial_value=False)
problem.add_fluent(exitPos, default_initial_value=False)
problem.add_fluent(measuredAt, default_initial_value=False)
problem.add_fluent(detected, default_initial_value=False)
problem.add_fluent(grasped, default_initial_value=False)
problem.add_fluent(graspMode, default_initial_value=False)
problem.add_fluent(reset, default_initial_value=False)

#problem.add_objects([home, vision2, pickup, pouchpose])
problem.add_object(home)
problem.add_object(vision2)
problem.add_object(pickup)
problem.add_object(pouchpose)
problem.add_object(bin)
problem.add_object(scale)
problem.add_object(scaledown)
problem.add_object(scaleout)
problem.add_object(scalein)
problem.add_object(scaleup)
problem.add_object(mark10)
problem.add_object(mark10out)
problem.add_object(mark10out2)
problem.add_object(mark10in)
problem.add_object(mark10in2)
problem.add_object(default)
problem.add_object(grasping)
problem.add_object(open20)
problem.add_object(open0)
problem.add_object(startState)
problem.add_object(active)
problem.add_object(horizontal)
problem.add_object(vertical)
problem.add_object(pouch1)
problem.add_object(pouch2)
problem.add_object(pouch3)
#problem.add_objects([pouch1, pouch2, pouch3])

problem.set_initial_value(inStateG(startState), True)
problem.set_initial_value(reset(mark10), True)
problem.set_initial_value(restLoc(scaledown, scale), True)
problem.set_initial_value(restLoc(mark10out, mark10), True)
problem.set_initial_value(dropPos(vision2, pouchpose), True)
problem.set_initial_value(dropPos(scaleup, scale), True)
problem.set_initial_value(dropPos(mark10in, mark10), True)
problem.set_initial_value(dropPos(bin, bin), True)
problem.set_initial_value(graspPos(pouchpose, pouchpose), True)
problem.set_initial_value(graspPos(scalein, scale), True)
problem.set_initial_value(graspPos(mark10in2, mark10), True)
problem.set_initial_value(exitPos(pickup, pouchpose), True)
problem.set_initial_value(exitPos(scaleout, scale), True)
problem.set_initial_value(exitPos(mark10out2, mark10), True)



# USARE FAST-DOWNWARD COME PLANNING ENGINE!!!!!!!!!
# TEMPISTICHE CON TAMER:
# GOAL PER CUI CI METTE 20 SECONDI
#problem.add_goal(measuredAt(pouch1, scale))
#problem.add_goal(grasped(pouch1))
#problem.add_goal(at(vision2))
#problem.add_goal(inStateG(active))
# con goal: measuredAt(pouch1, scale) and measuredAt(pouch1, mark10) CI METTE 7 MINUTI CIRCA
# con goal: measuredAt(pouch1, scale) and pouchIn(pouch1, bin) CI METTE 7 MINUTI CIRCA
# con goal: measuredAt(pouch1, scale) and measuredAt(pouch1, mark10) and pouchIn(pouch1, bin) DOPO PIù DI UN'ORA NON TROVA ANCORA LA SOLUZIONE
problem.add_goal(measuredAt(pouch1, scale))
problem.add_goal(measuredAt(pouch1, mark10))
problem.add_goal(pouchIn(pouch1, bin))

# NEANCHE MAI PROVATI, VISTO CHE NON RISOLVEVA GLI ALTRI
problem.add_goal(measuredAt(pouch2, scale))
problem.add_goal(measuredAt(pouch2, mark10))
problem.add_goal(pouchIn(pouch2, bin))

qr_kind = problem.kind
qr_problem = problem

# Get the compiler from the factory
from unified_planning.engines import CompilationKind

# Get the compiler from the factory
with Compiler(
        problem_kind=qr_kind,
        compilation_kind=CompilationKind.CONDITIONAL_EFFECTS_REMOVING
) as conditional_effects_remover:
    # After we have the compiler, we get the compilation result
    cer_result = conditional_effects_remover.compile(
        qr_problem,
        CompilationKind.CONDITIONAL_EFFECTS_REMOVING
    )
    cer_problem = cer_result.problem
    cer_kind = cer_problem.kind

    # Check the result of the compilation
    assert qr_kind.has_conditional_effects()
    assert not cer_kind.has_conditional_effects()

# The CompilationKind class is defined in the unified_planning/engines/mixins/compiler.py file
# Get the compiler from the factory
with Compiler(
        problem_kind=cer_kind,
        compilation_kind=CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING
) as disjunctive_conditions_remover:
    # After we have the compiler, we get the compilation result
    dcr_result = disjunctive_conditions_remover.compile(
        cer_problem,
        CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING
    )
    dcr_problem = dcr_result.problem
    dcr_kind = dcr_problem.kind

    # Check the result of the compilation
    assert qr_kind.has_disjunctive_conditions()
    assert cer_kind.has_disjunctive_conditions()
    assert not dcr_kind.has_disjunctive_conditions()
# To get the Compiler from the factory we can use the Compiler operation mode.
# It takes a problem_kind and a compilation_kind, and returns a compiler with the capabilities we need
# Get the compiler from the factory
with Compiler(
        problem_kind=dcr_kind,
        compilation_kind=CompilationKind.NEGATIVE_CONDITIONS_REMOVING
) as negative_conditions_remover:
    # After we have the compiler, we get the compilation result
    ncr_result = negative_conditions_remover.compile(
        dcr_problem,
        CompilationKind.NEGATIVE_CONDITIONS_REMOVING
    )
    ncr_problem = ncr_result.problem
    ncr_kind = ncr_problem.kind

    # Check the result of the compilation
    assert dcr_kind.has_negative_conditions()
    assert not ncr_kind.has_negative_conditions()

print(ncr_problem)