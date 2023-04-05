# MULTI-AGENT PROBLEM and AGENTS DEFINITION
from unified_planning.shortcuts import *
from unified_planning.model.multi_agent import *
from collections import namedtuple
from unified_planning.io.ma_pddl_writer import MAPDDLWriter


problemMA = MultiAgentProblem("P&G")

robot_a = Agent("robot_a", problemMA)
scale_a = Agent("scale_a", problemMA)
mark10_a = Agent("mark10_a", problemMA)

#---------------------------------------------------------------------------
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
#pouchIn = Fluent("pouchIn", BoolType(), pouch=pouchObj, deviceOrBin=location)

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

# agent's  PRIVATE fluents: necessary to be done here, since some private
#                           fluents may be needed, through Dot() in the
#                           preconditions of some actions




#problemMA.ma_environment.add_fluent(robotAtRest, default_initial_value=False)
#problemMA.add_fluent(reset, default_initial_value=False)

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


#problemMA.add_goal(grasped(pouch1))
#problemMA.add_goal( Dot(robot_a, at(vision2)) )
#problemMA.add_goal( Dot(robot_a, inStateG(active)) )

problemMA.add_goal(measuredAt(pouch1, scale))
problemMA.add_goal(measuredAt(pouch1, mark10))
problemMA.add_goal(pouchAt(pouch1, bin))

problemMA.add_goal(measuredAt(pouch2, scale))
problemMA.add_goal(measuredAt(pouch2, mark10))
problemMA.add_goal(pouchAt(pouch2, bin))

measure_scale_scaleRest_pouch1_0 = InstantaneousAction("measure_scale_scaleRest_pouch1_0")  #
measure_scale_scaleRest_pouch1_0.add_precondition(pouchAt(pouch1, scale))
measure_scale_scaleRest_pouch1_0.add_precondition(reset(scale))
measure_scale_scaleRest_pouch1_0.add_effect(measuredAt(pouch1, scale), True)
measure_scale_scaleRest_pouch1_0.add_effect(reset(scale), False)

# 2
measure_scale_scaleRest_pouch2_0 = InstantaneousAction("measure_scale_scaleRest_pouch2_0")  #
measure_scale_scaleRest_pouch2_0.add_precondition(pouchAt(pouch2, scale))
measure_scale_scaleRest_pouch2_0.add_precondition(reset(scale))
measure_scale_scaleRest_pouch2_0.add_effect(measuredAt(pouch2, scale), True)
measure_scale_scaleRest_pouch2_0.add_effect(reset(scale), False)

# 3



scale_a.add_action(measure_scale_scaleRest_pouch1_0)
scale_a.add_action(measure_scale_scaleRest_pouch2_0)
scale_a.add_fluent(restLoc)

# AGGIUNTA DELLE AZIONI AGLI AGENTI
n_tot_actions = 0
n_device_scale_actions = 0
n_device_mark10_actions = 0
n_other_actions = 0

problemMA.add_agent(scale_a)
problemMA.add_agent(mark10_a)
problemMA.add_agent(robot_a)



w = MAPDDLWriter(problemMA)
w.write_ma_domain('pach_nuovo')
w.write_ma_problem('pach_nuovo')