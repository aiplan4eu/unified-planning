import unified_planning
from unified_planning.shortcuts import *
from unified_planning.model.multi_agent import *
from unified_planning.test import TestCase


def get_test_cases():

    res = {}

    problem = MultiAgentProblem("P&G")
    # AGENTs
    robot_a = Agent("robot_a", problem)
    scale1_a = Agent("scale1_a", problem)
    marks1_a = Agent("marks1_a", problem)
    markt1_a = Agent("markt1_a", problem)

    # TYPES
    LocationG = UserType("LocationG")
    LocationP = UserType("LocationP")
    StateG = UserType("StateG")
    PouchObj = UserType("PouchObj")
    pos = Fluent("pos", place=LocationP)

    # DEFINE FLUENTS
    at = Fluent("at", BoolType(), loc=LocationG)
    inStateG = Fluent("inStateG", BoolType(), state=StateG)
    relativeLoc = Fluent("relativeLoc", BoolType(), locP=LocationP, locG=LocationG)
    adj = Fluent("adj", BoolType(), fromL=LocationG, to=LocationG)
    opened = Fluent("opened", BoolType(), device=LocationP)
    isDraw = Fluent("isDraw", BoolType(), loc=LocationP)
    isBin = Fluent("isBin", BoolType(), loc=LocationP)
    isBinLoc = Fluent("isBinLoc", BoolType(), loc=LocationG)
    isMarkStrength = Fluent("isMarkStrength", BoolType(), loc=LocationP)
    isMarkSloc = Fluent("isMarkSloc", BoolType(), loc=LocationG)
    isScale = Fluent("isScale", BoolType(), loc=LocationP)
    reset = Fluent("reset", BoolType(), device=LocationP)
    free = Fluent("free", BoolType(), device=LocationP)
    pouchAt = Fluent("pouchAt", BoolType(), pouch=PouchObj, loc=LocationP)
    detected = Fluent("detected", BoolType(), pouch=PouchObj)
    grasped = Fluent("grasped", BoolType(), pouch=PouchObj)
    measuredAt = Fluent("measuredAt", BoolType(), pouch=PouchObj, device=LocationP)
    isP1 = Fluent("isP1", BoolType(), pouch=PouchObj)
    isP2 = Fluent("isP2", BoolType(), pouch=PouchObj)
    isP3 = Fluent("isP3", BoolType(), pouch=PouchObj)

    # ADD FLUENTS
    robot_a.add_public_fluent(at, default_initial_value=False)
    robot_a.add_public_fluent(inStateG, default_initial_value=False)

    scale1_a.add_private_fluent(pos, default_initial_value=False)
    scale1_a.add_public_fluent(reset, default_initial_value=False)

    marks1_a.add_private_fluent(pos, default_initial_value=False)
    marks1_a.add_public_fluent(reset, default_initial_value=False)

    markt1_a.add_private_fluent(pos, default_initial_value=False)
    markt1_a.add_public_fluent(reset, default_initial_value=False)

    problem.ma_environment.add_fluent(free, default_initial_value=False)
    problem.ma_environment.add_fluent(pouchAt, default_initial_value=False)
    problem.ma_environment.add_fluent(detected, default_initial_value=False)
    problem.ma_environment.add_fluent(grasped, default_initial_value=False)
    problem.ma_environment.add_fluent(measuredAt, default_initial_value=False)
    problem.ma_environment.add_fluent(isP1, default_initial_value=False)
    problem.ma_environment.add_fluent(isP2, default_initial_value=False)
    problem.ma_environment.add_fluent(isP3, default_initial_value=False)

    problem.ma_environment.add_fluent(adj, default_initial_value=False)
    problem.ma_environment.add_fluent(relativeLoc, default_initial_value=False)
    problem.ma_environment.add_fluent(isDraw, default_initial_value=False)
    problem.ma_environment.add_fluent(opened, default_initial_value=False)
    problem.ma_environment.add_fluent(isBin, default_initial_value=False)
    problem.ma_environment.add_fluent(isMarkStrength, default_initial_value=False)
    problem.ma_environment.add_fluent(isScale, default_initial_value=False)
    problem.ma_environment.add_fluent(isMarkSloc, default_initial_value=False)
    problem.ma_environment.add_fluent(isBinLoc, default_initial_value=False)

    # OBJECTS
    vision2 = Object("vision2", LocationG)
    drawersLoc = Object("drawersLoc", LocationG)
    scaleLoc = Object("scaleLoc", LocationG)
    mark10SLoc = Object("mark10SLoc", LocationG)
    mark10TLoc = Object("mark10TLoc", LocationG)
    binLoc = Object("binLoc", LocationG)

    drawer = Object("drawer", LocationP)
    scale1 = Object("scale1", LocationP)
    markS1 = Object("markS1", LocationP)
    markT1 = Object("markT1", LocationP)
    bin = Object("bin", LocationP)

    available = Object("available", StateG)

    pouch1 = Object("pouch1", PouchObj)
    pouch2 = Object("pouch2", PouchObj)
    pouch3 = Object("pouch3", PouchObj)
    d4_r2_c5 = Object("d4_r2_c5", PouchObj)
    d4_r5_c5 = Object("d4_r5_c5", PouchObj)

    # ADD OBJECTS
    problem.add_object(vision2)
    problem.add_object(drawersLoc)
    problem.add_object(scaleLoc)
    problem.add_object(mark10SLoc)
    problem.add_object(mark10TLoc)
    problem.add_object(binLoc)

    problem.add_object(drawer)
    problem.add_object(scale1)
    problem.add_object(markS1)
    problem.add_object(markT1)
    problem.add_object(bin)

    problem.add_object(available)

    problem.add_object(d4_r2_c5)
    problem.add_object(d4_r5_c5)

    problem.add_object(pouch1)
    problem.add_object(pouch2)
    problem.add_object(pouch3)

    # ACTIONS
    goto = InstantaneousAction("goto", fromL=LocationG, to=LocationG)
    fromL = goto.parameter("fromL")
    to = goto.parameter("to")
    goto.add_precondition(at(fromL))
    goto.add_precondition(adj(fromL, to))
    goto.add_effect(at(to), True)
    goto.add_effect(at(fromL), False)

    sense_imaging = InstantaneousAction("sense_imaging", pouch=PouchObj)
    pouch = sense_imaging.parameter("pouch")
    sense_imaging.add_precondition(at(vision2))
    sense_imaging.add_precondition(opened(drawer))
    sense_imaging.add_precondition(Not(detected(pouch)))
    sense_imaging.add_precondition(inStateG(available))
    sense_imaging.add_precondition(
        Or(isP1(pouch), Or(Not(detected(d4_r2_c5)), Not(pouchAt(d4_r2_c5, drawer))))
    )
    sense_imaging.add_precondition(
        Or(isP2(pouch), Or(Not(detected(d4_r5_c5)), Not(pouchAt(d4_r5_c5, drawer))))
    )
    sense_imaging.add_effect(detected(pouch), True)
    sense_imaging.add_effect(pouchAt(pouch, drawer), True)

    pick_pouch = InstantaneousAction(
        "pick_pouch", pouch=PouchObj, whereP=LocationP, gripPos=LocationG
    )
    pouch = pick_pouch.parameter("pouch")
    whereP = pick_pouch.parameter("whereP")
    gripPos = pick_pouch.parameter("gripPos")
    pick_pouch.add_precondition(inStateG(available))
    pick_pouch.add_precondition(detected(pouch))
    pick_pouch.add_precondition(pouchAt(pouch, whereP))
    pick_pouch.add_precondition(Not(free(whereP)))
    pick_pouch.add_precondition(at(gripPos))
    pick_pouch.add_precondition(relativeLoc(whereP, gripPos))
    pick_pouch.add_precondition(Not(isBin(whereP)))
    pick_pouch.add_precondition(Not(isMarkStrength(whereP)))
    pick_pouch.add_precondition(Or(Not(isDraw(whereP)), opened(whereP)))
    pick_pouch.add_effect(grasped(pouch), True)
    pick_pouch.add_effect(inStateG(available), False)
    pick_pouch.add_effect(pouchAt(pouch, whereP), False)
    pick_pouch.add_effect(free(whereP), True, Not(isDraw(whereP)))

    put_pouch_on = InstantaneousAction(
        "put_pouch_on", pouch=PouchObj, whereP=LocationP, gripPos=LocationG
    )
    pouch = put_pouch_on.parameter("pouch")
    whereP = put_pouch_on.parameter("whereP")
    gripPos = put_pouch_on.parameter("gripPos")
    put_pouch_on.add_precondition(grasped(pouch))
    put_pouch_on.add_precondition(Not(inStateG(available)))
    put_pouch_on.add_precondition(Not(isDraw(whereP)))
    put_pouch_on.add_precondition(Not(isBin(whereP)))
    put_pouch_on.add_precondition(relativeLoc(whereP, gripPos))
    put_pouch_on.add_precondition(at(gripPos))
    put_pouch_on.add_precondition(free(whereP))
    put_pouch_on.add_effect(pouchAt(pouch, whereP), True)
    put_pouch_on.add_effect(grasped(pouch), False)
    put_pouch_on.add_effect(inStateG(available), True)
    put_pouch_on.add_effect(free(whereP), False)

    drop_pouch = InstantaneousAction("drop_pouch", pouch=PouchObj, gripPos=LocationG)
    pouch = drop_pouch.parameter("pouch")
    gripPos = drop_pouch.parameter("gripPos")
    drop_pouch.add_precondition(at(gripPos))
    drop_pouch.add_precondition(
        Or(
            And(grasped(pouch), Not(inStateG(available)), isBinLoc(gripPos)),
            And(measuredAt(pouch, markS1), pouchAt(pouch, markS1), isMarkSloc(gripPos)),
        )
    )  # Equals(gripPos, binLoc) #Equals(gripPos, mark10SLoc)
    drop_pouch.add_effect(pouchAt(pouch, bin), True)
    drop_pouch.add_effect(inStateG(available), True)
    drop_pouch.add_effect(grasped(pouch), False)
    drop_pouch.add_effect(free(markS1), True, isMarkSloc(gripPos))
    drop_pouch.add_effect(pouchAt(pouch, markS1), False, isMarkSloc(gripPos))

    # resetDev
    device_reset = InstantaneousAction("device_reset", dev=LocationP)
    dev = device_reset.parameter("dev")
    device_reset.add_precondition(pos(dev))
    device_reset.add_precondition(Not(reset(dev)))
    device_reset.add_precondition(Not(isDraw(dev)))
    device_reset.add_precondition(Not(isBin(dev)))
    device_reset.add_precondition(free(dev))
    device_reset.add_effect(reset(dev), True)

    measure = InstantaneousAction("measure", pouch=PouchObj, dev=LocationP)  #
    pouch = measure.parameter("pouch")
    dev = measure.parameter("dev")
    measure.add_precondition(pos(dev))
    measure.add_precondition(reset(dev))
    measure.add_precondition(pouchAt(pouch, dev))
    measure.add_precondition(Not(isDraw(dev)))
    measure.add_precondition(Not(isBin(dev)))
    measure.add_effect(measuredAt(pouch, dev), True)
    measure.add_effect(reset(dev), False)

    # ADD ACTIONS
    robot_a.add_action(goto)
    robot_a.add_action(sense_imaging)
    robot_a.add_action(pick_pouch)
    robot_a.add_action(put_pouch_on)
    robot_a.add_action(drop_pouch)

    scale1_a.add_action(measure)
    scale1_a.add_action(device_reset)

    marks1_a.add_action(measure)
    marks1_a.add_action(device_reset)

    markt1_a.add_action(measure)
    markt1_a.add_action(device_reset)

    # ADD AGENTS
    problem.add_agent(robot_a)
    problem.add_agent(scale1_a)
    problem.add_agent(marks1_a)
    problem.add_agent(markt1_a)

    # INITIAL VALUES
    problem.set_initial_value(Dot(robot_a, inStateG(available)), True)
    problem.set_initial_value(Dot(robot_a, at(drawersLoc)), True)

    problem.set_initial_value(Dot(scale1_a, pos(scale1)), True)
    problem.set_initial_value(Dot(marks1_a, pos(markS1)), True)
    problem.set_initial_value(Dot(markt1_a, pos(markT1)), True)

    problem.set_initial_value(isP1(d4_r2_c5), True)
    problem.set_initial_value(isP2(d4_r5_c5), True)

    problem.set_initial_value(free(scale1), True)
    problem.set_initial_value(free(markS1), True)
    problem.set_initial_value(free(markT1), True)

    problem.set_initial_value(isDraw(drawer), True)
    problem.set_initial_value(opened(drawer), True)
    problem.set_initial_value(isBin(bin), True)

    problem.set_initial_value(isMarkStrength(markS1), True)
    problem.set_initial_value(isScale(scale1), True)
    problem.set_initial_value(isMarkSloc(mark10SLoc), True)
    problem.set_initial_value(isBinLoc(binLoc), True)

    problem.set_initial_value(adj(binLoc, mark10SLoc), True)
    problem.set_initial_value(adj(mark10SLoc, binLoc), True)
    problem.set_initial_value(adj(mark10SLoc, scaleLoc), True)
    problem.set_initial_value(adj(scaleLoc, mark10SLoc), True)
    problem.set_initial_value(adj(mark10SLoc, drawersLoc), True)
    problem.set_initial_value(adj(drawersLoc, mark10SLoc), True)
    problem.set_initial_value(adj(mark10TLoc, drawersLoc), True)
    problem.set_initial_value(adj(drawersLoc, mark10TLoc), True)
    problem.set_initial_value(adj(scaleLoc, drawersLoc), True)
    problem.set_initial_value(adj(drawersLoc, scaleLoc), True)
    problem.set_initial_value(adj(drawersLoc, vision2), True)
    problem.set_initial_value(adj(vision2, drawersLoc), True)
    problem.set_initial_value(adj(mark10TLoc, vision2), True)
    problem.set_initial_value(adj(vision2, mark10TLoc), True)

    problem.set_initial_value(relativeLoc(drawer, vision2), True)
    problem.set_initial_value(relativeLoc(scale1, scaleLoc), True)
    problem.set_initial_value(relativeLoc(markS1, mark10SLoc), True)
    problem.set_initial_value(relativeLoc(markT1, mark10TLoc), True)
    problem.set_initial_value(relativeLoc(bin, binLoc), True)

    # GOALS
    # problem.add_goal(measuredAt(pouch1, scale1))
    # problem.add_goal(measuredAt(pouch1, markS1))
    # problem.add_goal(measuredAt(pouch1, markT1))
    # problem.add_goal(pouchAt(pouch1, bin))
    # problem.add_goal(measuredAt(pouch2, scale1))
    # problem.add_goal(measuredAt(pouch2, markS1))
    # problem.add_goal(measuredAt(pouch2, markT1))
    # problem.add_goal(pouchAt(pouch2, bin))
    problem.add_goal(measuredAt(d4_r2_c5, scale1))
    problem.add_goal(measuredAt(d4_r2_c5, markT1))
    problem.add_goal(pouchAt(d4_r2_c5, bin))
    problem.add_goal(measuredAt(d4_r5_c5, scale1))
    problem.add_goal(measuredAt(d4_r5_c5, markS1))
    problem.add_goal(measuredAt(d4_r5_c5, markT1))
    problem.add_goal(pouchAt(d4_r5_c5, bin))

    res["procter_and_gamble"] = TestCase(problem=problem, solvable=True)

    return res
