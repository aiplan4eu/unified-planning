from unified_planning.shortcuts import *
from unified_planning.model.multi_agent import *
from collections import namedtuple
from unified_planning.io.ma_pddl_writer import MAPDDLWriter

import os
import unified_planning as up
import unified_planning.engines
from unified_planning.model.problem_kind import ProblemKind
from unified_planning.environment import get_env
from typing import List, Optional, Union
import pkg_resources

# TYPEs
Location = UserType("Location")
PostureG = UserType("PostureG")
StateG = UserType("StateG")
ModeG = UserType("ModeG")
PouchObj = UserType("PouchObj")

#---------------------------------------------------------------------------

# FLUENTs
at = Fluent("at", BoolType(), loc=Location)
pouchAt = Fluent("pouchAt", BoolType(), pouch=PouchObj, loc=Location)
#pouchIn = Fluent("pouchIn", BoolType(), pouch=PouchObj, deviceOrBin=Location)

inPosG = Fluent("inPosG", BoolType(), posture=PostureG)
inStateG = Fluent("inStateG", BoolType(), state=StateG)

restLoc = Fluent("restLoc", BoolType(), x=Location, device=Location)
dropPos = Fluent("dropPos", BoolType(), x=Location, device=Location)
graspPos = Fluent("graspPos", BoolType(), x=Location, device=Location)
exitPos = Fluent("exitPos", BoolType(), x=Location, device=Location)

measuredAt = Fluent("measuredAt", BoolType(), pouch=PouchObj, loc=Location)

detected = Fluent("detected", BoolType(), pouch=PouchObj )
grasped = Fluent("grasped", BoolType(), pouch=PouchObj )

graspMode = Fluent("graspMode", BoolType(), pouch=PouchObj, mode=ModeG)

reset = Fluent("reset", BoolType(), device=Location)

#robotAtRest = Fluent("robotAtRest", BoolType(), rest=Location)

# FLUENT DA USARE CON DOT mark10_a, mark10
pos = Fluent("pos", place=Location)


#---------------------------------------------------------------------------

# OBJECTs
home = Object("home", Location)
drawer = Object("drawer", Location)
pouchposeDrawer = Object("pouchposeDrawer", Location)
vision2 = Object("vision2", Location)
pickup = Object("pickup", Location)
bin = Object("bin", Location)
binUp = Object("binUp", Location)
scale = Object("scale", Location)
scaleRest = Object("scaleRest", Location)
scaleOut = Object("scaleOut", Location)
pouchposeScale = Object("pouchposeScale", Location)
scaleUp = Object("scaleUp", Location)
mark10 = Object("mark10", Location)
mark10Rest = Object("mark10Rest", Location)
mark10Out = Object("mark10Out", Location)
mark10Up = Object("mark10Up", Location)
pouchposeMark10 = Object("pouchposeMark10", Location)

default = Object("default", PostureG)
grasping = Object("grasping", PostureG)
open20 = Object("open20", PostureG)
open0 = Object("open0", PostureG)

startState = Object("startState", StateG)
active = Object("active", StateG)

horizontal = Object("horizontal", ModeG)
vertical = Object("vertical", ModeG)

pouch1 = Object("pouch1", PouchObj)
pouch2 = Object("pouch2", PouchObj)
pouch3 = Object("pouch3", PouchObj)


#---------------------------------------------------------------------------
# ACTIONs

movegripper_activate = InstantaneousAction("movegripper_activate")
movegripper_activate.add_precondition(inStateG(startState))
movegripper_activate.add_precondition(Not(inStateG(active)))
movegripper_activate.add_effect(inStateG(active), True)
movegripper_activate.add_effect(inStateG(startState), False)
movegripper_activate.add_effect(inPosG(default), True)
movegripper_activate.add_effect(at(home), True)
'''
movegripper_open20 = InstantaneousAction("movegripper_open20", postFrom=PostureG, x=Location, y=Location, m=ModeG, pouch=PouchObj)
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
movegripper_open20.add_precondition(Or( Not(inPosG(grasping)), (And( grasped(pouch) , graspMode(pouch, m) )) ) )   #UPDATE 16-17 NOVEMBRE
#p_var = Variable("p_var", PouchObj)   ##########PROVATO pouch AL POSTO DI pouchObj
#movegripper_open20.add_precondition(Or( Equals(y, bin), Equals(y, pouchpose), Not(Exists(pouchIn(p_var, y), p_var)) ) )
# EXISTENTIAL CONDITION manually compiled:
movegripper_open20.add_precondition(Or( Equals(y, bin) , Equals(y, drawer) , Not(Or ( pouchAt(pouch1, y), pouchAt(pouch2, y), pouchAt(pouch3, y) )) ) )     #(Or( Equals(y, pouchpose), Not(Exists(pouchIn(p_var, y), p_var)) ) )  ########
movegripper_open20.add_effect(inPosG(open20), True)
movegripper_open20.add_effect(inPosG(postFrom), False)
movegripper_open20.add_effect(pouchAt(pouch, y), True, (And (grasped(pouch), graspMode(pouch, m)) ) )   # WHEN CON DOPPIA PRECONDIZIONE (AND)
movegripper_open20.add_effect(pouchAt(pouch, x), False, (And (grasped(pouch), graspMode(pouch, m)) ) )   # WHEN
movegripper_open20.add_effect(graspMode(pouch, m), False, (And (grasped(pouch), graspMode(pouch, m)) ) )   # WHEN
movegripper_open20.add_effect(grasped(pouch), False, (And (grasped(pouch), graspMode(pouch, m)) ) )   # WHEN
#movegripper_open20.add_effect([graspMode(pouch, m),grasped(pouch)], [False, False], (And (grasped(pouch), graspMode(pouch, m)) ) )   # WHEN # NON FUNZIONA SCRITTO COSì
'''
'''
movegripper_grasp = InstantaneousAction("movegripper_grasp", postFrom=PostureG, x=Location, y=Location, pouch=PouchObj, m=ModeG)
postFrom = movegripper_grasp.parameter("postFrom")
x = movegripper_grasp.parameter("x")
y =  movegripper_grasp.parameter("y")
pouch = movegripper_grasp.parameter("pouch")
m =  movegripper_grasp.parameter("m")
movegripper_grasp.add_precondition(inStateG(active))
movegripper_grasp.add_precondition(Not(pouchAt(pouch, bin)))
movegripper_grasp.add_precondition(inPosG(postFrom))
movegripper_grasp.add_precondition(Not(inPosG(grasping)))
movegripper_grasp.add_precondition(at(x))
movegripper_grasp.add_precondition(graspPos(x, y))
movegripper_grasp.add_precondition(pouchAt(pouch, y))
movegripper_grasp.add_precondition(Not(grasped(pouch)))
movegripper_grasp.add_precondition(graspMode(pouch, m))
movegripper_grasp.add_effect(inPosG(grasping), True)
movegripper_grasp.add_effect(inPosG(postFrom), False)
movegripper_grasp.add_effect(grasped(pouch), True)
movegripper_grasp.add_effect(pouchAt(pouch, x), True)
movegripper_grasp.add_effect(pouchAt(pouch, y), False)

goto = InstantaneousAction("goto", fromLoc=Location, toLoc=Location, pouch=PouchObj)
fromLoc = goto.parameter("fromLoc")
toLoc = goto.parameter("toLoc")
pouch = goto.parameter("pouch")
goto.add_precondition(inStateG(active))
goto.add_precondition(at(fromLoc))
goto.add_precondition(Not(Equals(toLoc, bin)))
#y_var = Variable("y_var", Location)
#goto.add_precondition(Not(Exists(graspPos(toLoc, y_var), y_var) ) ) 
# EXISTENTIAL CONDITION manually compiled:
goto.add_precondition(Not(Or(graspPos(toLoc, home) ,graspPos(toLoc, drawer) , graspPos(toLoc, scale) , graspPos(toLoc, mark10) , graspPos(toLoc, bin) , graspPos(toLoc, pouchposeDrawer) , graspPos(toLoc, pouchposeScale) , graspPos(toLoc, pouchposeMark10) , graspPos(toLoc, scaleRest) , graspPos(toLoc, mark10Rest) , graspPos(toLoc, pickup) , graspPos(toLoc, scaleOut) , graspPos(toLoc, mark10Out) , graspPos(toLoc, vision2) , graspPos(toLoc, scaleUp) , graspPos(toLoc, mark10Up) , graspPos(toLoc, binUp) ) ))       # EXISTENTIAL CONDITION (DEFINIZIONE DI UNA VARIABILE)
goto.add_precondition(Or( Not(Equals(toLoc, mark10Up)), graspMode(pouch, horizontal) ) )    # OR e EQUALS(=)        #ORRRRRRRRRRRRRRRRRRRRRRRRRR
goto.add_precondition(Or (Not(inPosG(grasping)), grasped(pouch)) )
goto.add_effect(at(toLoc), True)
goto.add_effect(at(fromLoc), False)
goto.add_effect(pouchAt(pouch, toLoc), True, grasped(pouch))
goto.add_effect(pouchAt(pouch, fromLoc), False, grasped(pouch))
#goto.add_effect(robotAtRest(toLoc), True, Equals(toLoc, scaleRest) )
#goto.add_effect(robotAtRest(toLoc), True, Equals(toLoc, mark10Rest) )
#goto.add_effect(robotAtRest(scaleRest), False, Not(Equals(toLoc, scaleRest) ) )
#goto.add_effect(robotAtRest(mark10Rest), False,  Not(Equals(toLoc, mark10Rest))  )

# not (graspPos(toLoc, home) or graspPos(toLoc, vision2) or graspPos(toLoc, pickup) or graspPos(toLoc, pouchpose) or graspPos(toLoc, bin) or graspPos(toLoc, scale) or graspPos(toLoc, scaledown) or graspPos(toLoc, scaleout) or graspPos(toLoc, scalein) or graspPos(toLoc, scaleup) or graspPos(toLoc, mark10) or graspPos(toLoc, mark10out) or graspPos(toLoc, mark10out2) or graspPos(toLoc, mark10in) or graspPos(toLoc, mark10in2))

goto_grasp = InstantaneousAction("goto_grasp", fromLoc=Location, toLoc=Location, pouchWhere=Location, m=ModeG, pouch=PouchObj)
fromLoc = goto_grasp.parameter("fromLoc")
toLoc = goto_grasp.parameter("toLoc")
pouchWhere = goto_grasp.parameter("pouchWhere")
pouch = goto_grasp.parameter("pouch")
m = goto_grasp.parameter("m")
#goto_grasp.add_precondition(inStateG(active))
goto_grasp.add_precondition(Not(pouchAt(pouch, bin)))
goto_grasp.add_precondition(at(fromLoc))
goto_grasp.add_precondition(pouchAt(pouch, pouchWhere))
goto_grasp.add_precondition(detected(pouch))
goto_grasp.add_precondition(graspPos(toLoc, pouchWhere))
goto_grasp.add_precondition(inPosG(open20))
goto_grasp.add_precondition(Not(Equals(fromLoc, toLoc)))
goto_grasp.add_precondition(Or( Not(Equals(toLoc, pouchposeMark10)), Equals(m, horizontal) ) )   #ORRRRRRRRRRRRRRRRRRRRRRRRRR
goto_grasp.add_precondition(Or( Not(Equals(toLoc, pouchposeDrawer)), Equals(m, vertical) ) )     #ORRRRRRRRRRRRRRRRRRRRRRRRRR   
goto_grasp.add_precondition(Not(graspMode(pouch1, horizontal)))
goto_grasp.add_precondition(Not(graspMode(pouch1, vertical)))
goto_grasp.add_precondition(Not(graspMode(pouch2, horizontal)))
goto_grasp.add_precondition(Not(graspMode(pouch2, vertical)))
goto_grasp.add_precondition(Not(graspMode(pouch3, horizontal)))
goto_grasp.add_precondition(Not(graspMode(pouch3, vertical)))
goto_grasp.add_effect(at(toLoc), True)
goto_grasp.add_effect(at(fromLoc), False)
goto_grasp.add_effect(graspMode(pouch, m), True)
#goto_grasp.add_effect(robotAtRest(scaleRest), False, Not(Equals(toLoc, scaleRest) ) )
#goto_grasp.add_effect(robotAtRest(mark10Rest), False,  Not(Equals(toLoc, mark10Rest))  )

perceptPouch = InstantaneousAction("perceptPouch", pouch=PouchObj)
pouch = perceptPouch.parameter("pouch")
perceptPouch.add_precondition(at(vision2))
perceptPouch.add_precondition(Not(detected(pouch)))
perceptPouch.add_effect(detected(pouch), True)
perceptPouch.add_effect(pouchAt(pouch, drawer), True)

measure = InstantaneousAction("measure", device=Location, rest=Location, pouch=PouchObj)  #
device = measure.parameter("device")
rest = measure.parameter("rest")
pouch = measure.parameter("pouch")
measure.add_precondition(pouchAt(pouch, device))
measure.add_precondition(at(rest))
measure.add_precondition(restLoc(rest, device))
#measure.add_precondition(robotAtRest(rest))
#measure.add_precondition(restLoc(rest, device))
measure.add_precondition(reset(device))
measure.add_precondition(Not(inPosG(grasping)))
measure.add_precondition(Or( Equals(device, scale), measuredAt(pouch, scale) ) )      #ORRRRRRRRRRRRRRRRRRRRRRRRRR   
measure.add_effect(measuredAt(pouch, device), True)
measure.add_effect(reset(device), False, Equals(device, scale))  #when


scale_reset = InstantaneousAction("scale_reset") #, pouch=PouchObj)
#pouch = scale_reset.parameter("pouch")
scale_reset.add_precondition(Not(reset(scale)))
scale_reset.add_precondition(And( Not(pouchAt(pouch1, scale)) , Not(pouchAt(pouch2, scale)) , Not(pouchAt(pouch3, scale)) ) )
scale_reset.add_effect(reset(scale), True)
'''

#-------------------------------------------------------------------------------


problem = Problem("P&G")
problem.add_action(movegripper_activate)
'''
problem.add_action(movegripper_open20)
problem.add_action(movegripper_grasp)
problem.add_action(goto)
problem.add_action(goto_grasp)
problem.add_action(perceptPouch)
problem.add_action(measure)
problem.add_action(scale_reset) #(resetDev)
'''

problem.add_fluent(at, default_initial_value=False)
problem.add_fluent(pouchAt, default_initial_value=False)
#problem.add_fluent(pouchIn, default_initial_value=False)
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
#problem.add_fluent(robotAtRest, default_initial_value=False)

#problem.add_objects([home, vision2, pickup, pouchpose])
problem.add_object(home)
problem.add_object(vision2)
problem.add_object(pickup)
problem.add_object(pouchposeDrawer)
problem.add_object(drawer)
problem.add_object(bin)
problem.add_object(binUp)
problem.add_object(scale)
problem.add_object(scaleRest)
problem.add_object(scaleOut)
problem.add_object(pouchposeScale)
problem.add_object(scaleUp)
problem.add_object(mark10)
problem.add_object(mark10Rest)
problem.add_object(mark10Out)
problem.add_object(mark10Up)
problem.add_object(pouchposeMark10)
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
problem.set_initial_value(restLoc(scaleRest, scale), True)
problem.set_initial_value(restLoc(mark10Rest, mark10), True)
problem.set_initial_value(dropPos(vision2, drawer), True)
problem.set_initial_value(dropPos(scaleUp, scale), True)
problem.set_initial_value(dropPos(mark10Up, mark10), True)
problem.set_initial_value(dropPos(binUp, bin), True)
problem.set_initial_value(graspPos(pouchposeDrawer, drawer), True)
problem.set_initial_value(graspPos(pouchposeScale, scale), True)
problem.set_initial_value(graspPos(pouchposeMark10, mark10), True)
problem.set_initial_value(exitPos(pickup, drawer), True)
problem.set_initial_value(exitPos(scaleOut, scale), True)
problem.set_initial_value(exitPos(mark10Out, mark10), True)

'''
problem.add_goal(measuredAt(pouch1, scale))
problem.add_goal(measuredAt(pouch1, mark10))
problem.add_goal(pouchAt(pouch1, bin))
'''
problem.add_goal(at(home))
from unified_planning.engines import CompilationKind
problem_kind = problem.kind
print(problem_kind)

with Compiler(
        problem_kind = problem_kind,
        compilation_kind = CompilationKind.GROUNDING
    ) as equality_remover:
    eq_result = equality_remover.compile(
        problem,
        CompilationKind.GROUNDING
    )
    eq_problem = eq_result.problem
    eq_kind = eq_problem.kind

from unified_planning.engines import CompilationKind

# The CompilationKind class is defined in the unified_planning/engines/mixins/compiler.py file

# To get the Compiler from the factory we can use the Compiler operation mode.
# It takes a problem_kind and a compilation_kind, and returns a compiler with the capabilities we need
with Compiler(
        problem_kind=eq_kind,  # eq_kind
        compilation_kind=CompilationKind.QUANTIFIERS_REMOVING
) as quantifiers_remover:
    # After we have the compiler, we get the compilation result
    qr_result = quantifiers_remover.compile(
        eq_problem,  # eq_problem
        CompilationKind.QUANTIFIERS_REMOVING
    )
    qr_problem = qr_result.problem
    qr_kind = qr_problem.kind

    # Check the result of the compilation
    # assert problem_kind.has_existential_conditions() #and problem_kind.has_universal_conditions()
    assert not qr_kind.has_existential_conditions() and not qr_kind.has_universal_conditions()

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
    # assert original_problem_kind.has_conditional_effects()
    # assert qr_kind.has_conditional_effects()
    assert not cer_kind.has_conditional_effects()

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
    # assert qr_kind.has_disjunctive_conditions()
    # assert cer_kind.has_disjunctive_conditions()
    assert not dcr_kind.has_disjunctive_conditions()

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
    assert not ncr_kind.has_negative_conditions()
#-----------------------------------------------------------------------------------------------------------------------

problemMA = MultiAgentProblem("PGMulti")

robot_a = Agent("robot_a", problemMA)
'''
scale_a = Agent("scale_a", problemMA)
mark10_a = Agent("mark10_a", problemMA)
'''

# TYPEs
Location = UserType("Location")
PostureG = UserType("PostureG")
StateG = UserType("StateG")
ModeG = UserType("ModeG")
PouchObj = UserType("PouchObj")



# FLUENTs
at = Fluent("at", BoolType(), loc=Location)

inPosG = Fluent("inPosG", BoolType(), posture=PostureG)
inStateG = Fluent("inStateG", BoolType(), state=StateG)
'''
pouchAt = Fluent("pouchAt", BoolType(), pouch=PouchObj, loc=Location)

restLoc = Fluent("restLoc", BoolType(), x=Location, device=Location)
dropPos = Fluent("dropPos", BoolType(), x=Location, device=Location)
graspPos = Fluent("graspPos", BoolType(), x=Location, device=Location)
exitPos = Fluent("exitPos", BoolType(), x=Location, device=Location)

measuredAt = Fluent("measuredAt", BoolType(), pouch=PouchObj, loc=Location)

detected = Fluent("detected", BoolType(), pouch=PouchObj )
grasped = Fluent("grasped", BoolType(), pouch=PouchObj )

graspMode = Fluent("graspMode", BoolType(), pouch=PouchObj, mode=ModeG)

reset = Fluent("reset", BoolType(), device=Location)

#robotAtRest = Fluent("robotAtRest", BoolType(), rest=Location)

# FLUENT DA USARE CON DOT mark10_a, mark10
pos = Fluent("pos", place=Location)

'''


# agent's  PRIVATE fluents: necessary to be done here, since some private
#                           fluents may be needed, through Dot() in the
#                           preconditions of some actions
robot_a.add_fluent(at, default_initial_value=False)
robot_a.add_fluent(inPosG, default_initial_value=False)
robot_a.add_fluent(inStateG, default_initial_value=False)
'''
scale_a.add_fluent(reset, default_initial_value=False)
mark10_a.add_fluent(reset, default_initial_value=False)
'''

# ENVIRONMENT FLUENTS
'''
#problemMA.add_fluent(at, default_initial_value=False)
problemMA.ma_environment.add_fluent(pouchAt, default_initial_value=False)
#problemMA.ma_environment.add_fluent(pouchIn, default_initial_value=False)
#problemMA.add_fluent(inPosG, default_initial_value=False)
#problemMA.add_fluent(inStateG, default_initial_value=False)
problemMA.ma_environment.add_fluent(restLoc, default_initial_value=False)
problemMA.ma_environment.add_fluent(dropPos, default_initial_value=False)
problemMA.ma_environment.add_fluent(graspPos, default_initial_value=False)
problemMA.ma_environment.add_fluent(exitPos, default_initial_value=False)
problemMA.ma_environment.add_fluent(measuredAt, default_initial_value=False)
problemMA.ma_environment.add_fluent(detected, default_initial_value=False)
problemMA.ma_environment.add_fluent(grasped, default_initial_value=False)
problemMA.ma_environment.add_fluent(graspMode, default_initial_value=False)
'''
#problemMA.ma_environment.add_fluent(robotAtRest, default_initial_value=False)
#problemMA.add_fluent(reset, default_initial_value=False)


# OBJECTs
home = Object("home", Location)
drawer = Object("drawer", Location)
pouchposeDrawer = Object("pouchposeDrawer", Location)
vision2 = Object("vision2", Location)
pickup = Object("pickup", Location)
bin = Object("bin", Location)
binUp = Object("binUp", Location)
scale = Object("scale", Location)
scaleRest = Object("scaleRest", Location)
scaleOut = Object("scaleOut", Location)
pouchposeScale = Object("pouchposeScale", Location)
scaleUp = Object("scaleUp", Location)
mark10 = Object("mark10", Location)
mark10Rest = Object("mark10Rest", Location)
mark10Out = Object("mark10Out", Location)
mark10Up = Object("mark10Up", Location)
pouchposeMark10 = Object("pouchposeMark10", Location)

default = Object("default", PostureG)
grasping = Object("grasping", PostureG)
open20 = Object("open20", PostureG)
open0 = Object("open0", PostureG)

startState = Object("startState", StateG)
active = Object("active", StateG)

horizontal = Object("horizontal", ModeG)
vertical = Object("vertical", ModeG)

pouch1 = Object("pouch1", PouchObj)
pouch2 = Object("pouch2", PouchObj)
pouch3 = Object("pouch3", PouchObj)


# AGGIUNTA DEGLI OGGETTI AL PROBLEMA
#problemMA.add_objects([home, vision2, pickup, pouchpose])
problemMA.add_object(home)
problemMA.add_object(drawer)
problemMA.add_object(pouchposeDrawer)
problemMA.add_object(vision2)
problemMA.add_object(pickup)
problemMA.add_object(bin)
problemMA.add_object(binUp)
problemMA.add_object(scale)
problemMA.add_object(scaleRest)
problemMA.add_object(scaleOut)
problemMA.add_object(pouchposeScale)
problemMA.add_object(scaleUp)
problemMA.add_object(mark10)
problemMA.add_object(mark10Rest)
problemMA.add_object(mark10Out)
problemMA.add_object(mark10Up)
problemMA.add_object(pouchposeMark10)
problemMA.add_object(default)
problemMA.add_object(grasping)
problemMA.add_object(open20)
problemMA.add_object(open0)
problemMA.add_object(startState)
problemMA.add_object(active)
problemMA.add_object(horizontal)
problemMA.add_object(vertical)
problemMA.add_objects([pouch1, pouch2, pouch3])

# SETTING INITIAL VALUES OF THE PROBLEM

problemMA.set_initial_value(Dot(robot_a, inStateG(startState)), True)
#problemMA.set_initial_value(Dot(mark10_a, reset(mark10)), True)  #VERIFICA SE POSSO SEMPLICEMENTE TOGLIERE IL PARAMETRO DA RESET
'''
problemMA.set_initial_value(restLoc(scaleRest, scale), True)
problemMA.set_initial_value(restLoc(mark10Rest, mark10), True)
problemMA.set_initial_value(dropPos(vision2, drawer), True)
problemMA.set_initial_value(dropPos(scaleUp, scale), True)
problemMA.set_initial_value(dropPos(mark10Up, mark10), True)
problemMA.set_initial_value(dropPos(binUp, bin), True)
problemMA.set_initial_value(graspPos(pouchposeDrawer, drawer), True)
problemMA.set_initial_value(graspPos(pouchposeScale, scale), True)
problemMA.set_initial_value(graspPos(pouchposeMark10, mark10), True)
problemMA.set_initial_value(exitPos(pickup, drawer), True)
problemMA.set_initial_value(exitPos(scaleOut, scale), True)
problemMA.set_initial_value(exitPos(mark10Out, mark10), True)
'''
problemMA.add_goal(Dot(robot_a, at(home)))

#problemMA.add_goal(at(home))

'''
problemMA.add_goal(measuredAt(pouch1, scale))
problemMA.add_goal(measuredAt(pouch1, mark10))
problemMA.add_goal(pouchAt(pouch1, bin))

problemMA.add_goal(measuredAt(pouch2, scale))
problemMA.add_goal(measuredAt(pouch2, mark10))
problemMA.add_goal(pouchAt(pouch2, bin))
'''

# AGGIUNTA DEGLI AGENTI sopra definiti AL PROBLEMA
#problemMA.add_agent(scale_a)
#problemMA.add_agent(mark10_a)
problemMA.add_agent(robot_a)
print(problemMA.agent("robot_a").actions)

# AGGIUNTA DELLE AZIONI AGLI AGENTI
n_tot_actions = 0
n_device_scale_actions = 0
n_device_mark10_actions = 0
n_other_actions = 0

for i in dcr_problem.actions:  #
    # print(i.name)
    n_tot_actions += 1
    if "measure_scale" in i.name:
        n_device_scale_actions += 1

    elif "scale_reset" in i.name:
        # problemMA.agent("scale_a").add_action(i)
        n_device_scale_actions += 1

    elif "measure_mark10" in i.name:
        # problemMA.agent("mark10_a").add_action(i)
        n_device_mark10_actions += 1

    else:
        problemMA.agent("robot_a").add_action(i)
        n_other_actions += 1

print(n_tot_actions)
print(n_device_scale_actions)
print(n_device_mark10_actions)
print(n_other_actions)

print(problemMA.agent("robot_a").actions)



print(problemMA)

from unified_planning.io.ma_pddl_writer import MAPDDLWriter
w = MAPDDLWriter(problemMA)
w.write_ma_domain("ok")
w.write_ma_problem("ok")

with OneshotPlanner(name='fmap') as planner:
    result = planner.solve(problemMA)
    if result.status == up.engines.PlanGenerationResultStatus.SOLVED_SATISFICING:
        print("FMAP returned: %s" % result.plan)
        print("FMAP returned: %s" % result.plan.to_sequential_plan(), result.plan.get_adjacency_list)
        print(result)
    else:
        print(result)
        print("No plan found.")