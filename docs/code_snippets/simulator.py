from unified_planning.shortcuts import *
from unified_planning.plans import SequentialPlan, ActionInstance

problem = Problem()

Location = UserType("Location")

l1 = problem.add_object("l1", Location)
l2 = problem.add_object("l2", Location)
loader_plate = problem.add_object("loader_plate", Location)

battery = problem.add_fluent("battery", IntType(), default_initial_value=100)
loader_at = problem.add_fluent("loader_at", default_initial_value=False, pos=Location)
package_at = problem.add_fluent("package_at", default_initial_value=False, pos=Location)

move = InstantaneousAction("move", l_from=Location, l_to=Location)
move.add_precondition(loader_at(move.l_from))
move.add_effect(loader_at(move.l_from), False)
move.add_effect(loader_at(move.l_to), True)
move.add_decrease_effect(battery, 20, Not(package_at(loader_plate)))
move.add_decrease_effect(battery, 25, package_at(loader_plate))

load = InstantaneousAction("load", pos=Location)
load.add_precondition(loader_at(load.pos))
load.add_precondition(package_at(load.pos))
load.add_effect(package_at(loader_plate), True)
load.add_effect(package_at(load.pos), False)
move.add_decrease_effect(battery, 5)

unload = InstantaneousAction("unload", pos=Location)
unload.add_precondition(package_at(loader_plate))
unload.add_precondition(loader_at(unload.pos))
unload.add_effect(package_at(unload.pos), True)
unload.add_effect(package_at(loader_plate), True)
move.add_decrease_effect(battery, 5)

problem.add_actions([move, load, unload])

problem.set_initial_value(package_at(l2), True)
problem.set_initial_value(loader_at(l1), True)
problem.add_goal(package_at(l1))

plan = SequentialPlan(
    [
        ActionInstance(move, (l1, l2)),
        ActionInstance(load, (l2,)),
        ActionInstance(move, (l2, l1)),
        ActionInstance(unload, (l1,)),
    ]
)
battery = FluentExp(problem.fluent("battery"))
with SequentialSimulator(problem) as simulator:
    state = simulator.get_initial_state()
    print(f"Initial battery = {state.get_value(battery)}")
    for ai in plan.actions:
        state = simulator.apply(state, ai)
        print(f"Applied action: {ai}. ", end="")
        print(f"Remaining battery: {state.get_value(battery)}")
    if simulator.is_goal(state):
        print("Goal reached!")
# Initial battery = 100
# Applied action: move(l1, l2). Remaining battery: 80
# Applied action: load(l2). Remaining battery: 75
# Applied action: move(l2, l1). Remaining battery: 50
# Applied action: unload(l1). Remaining battery: 45
# Goal reached!
