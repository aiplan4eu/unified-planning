from unified_planning.shortcuts import *
from unified_planning.model.multi_agent import *
from collections import namedtuple

# TYPEs
location = UserType("location")
postureG = UserType("postureG")
stateG = UserType("stateG")
modeG = UserType("modeG")
pouchObj = UserType("pouchObj")

# ---------------------------------------------------------------------------
Example = namedtuple("Example", ["problem", "plan"])


def get_example_problems():
    # FLUENTs
    problems = {}
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

    detected = Fluent("detected", BoolType(), pouch=pouchObj)
    grasped = Fluent("grasped", BoolType(), pouch=pouchObj)

    graspMode = Fluent("graspMode", BoolType(), pouch=pouchObj, mode=modeG)

    reset = Fluent("reset", BoolType(), device=location)

    # ---------------------------------------------------------------------------

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

    # ---------------------------------------------------------------------------
    # ACTIONs

    movegripper_activate = InstantaneousAction("movegripper_activate")
    movegripper_activate.add_precondition(inStateG(startState))
    movegripper_activate.add_precondition(Not(inStateG(active)))
    movegripper_activate.add_effect(inStateG(active), True)
    movegripper_activate.add_effect(inStateG(startState), False)
    movegripper_activate.add_effect(inPosG(default), True)
    movegripper_activate.add_effect(at(home), True)

    movegripper_open20 = InstantaneousAction(
        "movegripper_open20",
        postFrom=postureG,
        x=location,
        y=location,
        m=modeG,
        pouch=pouchObj,
    )
    postFrom = movegripper_open20.parameter("postFrom")
    x = movegripper_open20.parameter("x")
    y = movegripper_open20.parameter("y")
    m = movegripper_open20.parameter("m")
    pouch = movegripper_open20.parameter("pouch")
    movegripper_open20.add_precondition(inStateG(active))
    movegripper_open20.add_precondition(inPosG(postFrom))
    movegripper_open20.add_precondition(Not(inPosG(open20)))
    movegripper_open20.add_precondition(at(x))
    movegripper_open20.add_precondition(dropPos(x, y))
    p_var = Variable("p_var", pouchObj)
    movegripper_open20.add_precondition(
        Or(Equals(y, pouchpose), Not(Exists(pouchIn(p_var, y), p_var)))
    )  ########
    movegripper_open20.add_effect(inPosG(open20), True)
    movegripper_open20.add_effect(inPosG(postFrom), False)
    movegripper_open20.add_effect(
        pouchIn(pouch, y), True, (And(grasped(pouch), graspMode(pouch, m)))
    )  # WHEN CON DOPPIA PRECONDIZIONE (AND)
    movegripper_open20.add_effect(
        pouchAt(pouch, x), False, (And(grasped(pouch), graspMode(pouch, m)))
    )  # WHEN
    movegripper_open20.add_effect(
        graspMode(pouch, m), False, (And(grasped(pouch), graspMode(pouch, m)))
    )  # WHEN
    movegripper_open20.add_effect(
        grasped(pouch), False, (And(grasped(pouch), graspMode(pouch, m)))
    )  # WHEN

    movegripper_grasp = InstantaneousAction(
        "movegripper_grasp", postFrom=postureG, x=location, y=location, pouch=pouchObj
    )
    postFrom = movegripper_grasp.parameter("postFrom")
    x = movegripper_grasp.parameter("x")
    y = movegripper_grasp.parameter("y")
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
    goto.add_precondition(
        Not(Exists(graspPos(toLoc, y_var), y_var))
    )  # EXISTENTIAL CONDITION (DEFINIZIONE DI UNA VARIABILE)
    goto.add_precondition(
        Or(Not(Equals(toLoc, mark10in)), graspMode(pouch, horizontal))
    )  # OR e EQUALS(=)        #ORRRRRRRRRRRRRRRRRRRRRRRRRR
    goto.add_precondition(Or(Not(inPosG(grasping)), grasped(pouch)))
    goto.add_effect(at(toLoc), True)
    goto.add_effect(at(fromLoc), False)
    goto.add_effect(pouchAt(pouch, toLoc), True, grasped(pouch))
    goto.add_effect(pouchAt(pouch, fromLoc), False, grasped(pouch))

    goto_grasp = InstantaneousAction(
        "goto_grasp",
        fromLoc=location,
        toLoc=location,
        pouchWhere=location,
        m=modeG,
        pouch=pouchObj,
    )
    fromLoc = goto_grasp.parameter("fromLoc")
    toLoc = goto_grasp.parameter("toLoc")
    pouchWhere = goto_grasp.parameter("pouchWhere")
    pouch = goto_grasp.parameter("pouch")
    m = goto_grasp.parameter("m")
    # goto_grasp.add_precondition(inStateG(active))
    goto_grasp.add_precondition(Not(pouchIn(pouch, bin)))
    goto_grasp.add_precondition(at(fromLoc))
    goto_grasp.add_precondition(pouchIn(pouch, pouchWhere))
    goto_grasp.add_precondition(detected(pouch))
    goto_grasp.add_precondition(graspPos(toLoc, pouchWhere))
    goto_grasp.add_precondition(inPosG(open20))
    goto_grasp.add_precondition(Not(Equals(fromLoc, toLoc)))
    goto_grasp.add_precondition(
        Or(Not(Equals(toLoc, mark10in2)), Equals(m, horizontal))
    )  # ORRRRRRRRRRRRRRRRRRRRRRRRRR
    goto_grasp.add_precondition(
        Or(Not(Equals(toLoc, pouchpose)), Equals(m, vertical))
    )  # ORRRRRRRRRRRRRRRRRRRRRRRRRR
    goto_grasp.add_effect(at(toLoc), True)
    goto_grasp.add_effect(at(fromLoc), False)
    goto_grasp.add_effect(graspMode(pouch, m), True)

    perceptPouch = InstantaneousAction("perceptPouch", pouch=pouchObj)
    pouch = perceptPouch.parameter("pouch")
    perceptPouch.add_precondition(at(vision2))
    perceptPouch.add_effect(detected(pouch), True)
    perceptPouch.add_effect(pouchIn(pouch, pouchpose), True)

    measure = InstantaneousAction(
        "measure", device=location, rest=location, pouch=pouchObj
    )
    device = measure.parameter("device")
    rest = measure.parameter("rest")
    pouch = measure.parameter("pouch")
    measure.add_precondition(pouchIn(pouch, device))
    measure.add_precondition(at(rest))
    measure.add_precondition(restLoc(rest, device))
    measure.add_precondition(reset(device))
    measure.add_precondition(
        Or(Equals(device, scale), measuredAt(pouch, scale))
    )  # ORRRRRRRRRRRRRRRRRRRRRRRRRR
    measure.add_effect(measuredAt(pouch, device), True)
    measure.add_effect(reset(device), False, Equals(device, scale))

    resetDev = InstantaneousAction("reset_dev", device=location, pouch=pouchObj)
    device = resetDev.parameter("device")
    pouch = resetDev.parameter("pouch")
    resetDev.add_precondition(Not(reset(device)))
    resetDev.add_precondition(Not(pouchIn(pouch, device)))
    resetDev.add_effect(reset(device), True)

    # -------------------------------------------------------------------------------

    problem = MultiAgentProblem("P&G")

    robot_a = Agent("robot_a", problem)
    scale_a = Agent("scale_a", problem)
    mark10_a = Agent("mark10_a", problem)

    # Agent robotic arm
    robot_a.add_action(movegripper_activate)
    robot_a.add_action(movegripper_open20)
    robot_a.add_action(movegripper_grasp)
    robot_a.add_action(goto)
    robot_a.add_action(goto_grasp)
    robot_a.add_action(perceptPouch)
    robot_a.add_fluent(at, default_initial_value=False)
    robot_a.add_fluent(inPosG, default_initial_value=False)
    robot_a.add_fluent(inStateG, default_initial_value=False)

    # Agent scale device
    scale_a.add_action(measure)
    scale_a.add_action(resetDev)
    scale_a.add_fluent(at, default_initial_value=False)
    scale_a.add_fluent(reset, default_initial_value=False)

    # Agent mark10 device
    mark10_a.add_action(measure)
    mark10_a.add_action(resetDev)
    mark10_a.add_fluent(at, default_initial_value=False)
    mark10_a.add_fluent(reset, default_initial_value=False)

    # FLUENTI D'AMBIENTE
    # problem.add_fluent(at, default_initial_value=False)
    problem.ma_environment.add_fluent(pouchAt, default_initial_value=False)
    problem.ma_environment.add_fluent(pouchIn, default_initial_value=False)
    # problem.add_fluent(inPosG, default_initial_value=False)
    # problem.add_fluent(inStateG, default_initial_value=False)
    problem.ma_environment.add_fluent(restLoc, default_initial_value=False)
    problem.ma_environment.add_fluent(dropPos, default_initial_value=False)
    problem.ma_environment.add_fluent(graspPos, default_initial_value=False)
    problem.ma_environment.add_fluent(exitPos, default_initial_value=False)
    problem.ma_environment.add_fluent(measuredAt, default_initial_value=False)
    problem.ma_environment.add_fluent(detected, default_initial_value=False)
    problem.ma_environment.add_fluent(grasped, default_initial_value=False)
    problem.ma_environment.add_fluent(graspMode, default_initial_value=False)
    # problem.add_fluent(reset, default_initial_value=False)

    # AGGIUNTA DEGLI AGENTI sopra definiti AL PROBLEMA
    problem.add_agent(robot_a)
    problem.add_agent(scale_a)
    problem.add_agent(mark10_a)

    # AGGIUNTA DEGLI OGGETTI AL PROBLEMA
    # problem.add_objects([home, vision2, pickup, pouchpose])
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
    problem.add_objects([pouch1, pouch2, pouch3])

    # SETTING INITIAL VALUES OF THE PROBLEM
    problem.set_initial_value(Dot(robot_a, inStateG(startState)), True)
    problem.set_initial_value(
        Dot(mark10_a, reset(mark10)), True
    )  # VERIFICA SE POSSO SEMPLICEMENTE TOGLIERE IL PARAMETRO DA RESET
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

    # problem.add_goal(grasped(pouch1))
    # problem.add_goal( Dot(robot_a, at(vision2)) )
    # problem.add_goal( Dot(robot_a, inStateG(active)) )

    problem.add_goal(measuredAt(pouch1, scale))
    problem.add_goal(measuredAt(pouch1, mark10))
    problem.add_goal(pouchIn(pouch1, bin))
    """
    problem.add_goal(measuredAt(pouch2, scale))
    problem.add_goal(measuredAt(pouch2, mark10))
    problem.add_goal(pouchIn(pouch2, bin))
    """
    plan = None
    pauch = Example(problem=problem, plan=plan)
    problems["pauch"] = pauch
    return problems


'''problems = get_example_problems()
problem = problems["pauch"].problem
from unified_planning.io.ma_pddl_writer import MAPDDLWriter



breakpoint()
w = MAPDDLWriter(problem)
print("\n\n\n --------------------DOMAIN-------------------------------------------")
# ok = w.get_ma_problem_agent('depot0_agent')
# w.print_ma_domain_agent("depot0_agent")
# w.print_ma_problem_agent("depot0_agent")
# print("oooooooo", ok)
w.write_ma_domain("pauch")
print("\n\n\n -------------------PROBLEM-------------------------------------------")
w.write_ma_problem("pauch")'''

