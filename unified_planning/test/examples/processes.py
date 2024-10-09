from unified_planning.shortcuts import *
from unified_planning.model.action import Process
from unified_planning.io import PDDLReader, PDDLWriter


on = Fluent("on")
d = Fluent("d", RealType())

a = InstantaneousAction("turn_on")
a.add_precondition(Not(on))
a.add_effect(on, True)

evt = Event("turn_off_automatically")
evt.add_precondition(GE(d, 200))
evt.add_effect(on, False)

b = Process("moving")
b.add_precondition(on)
b.add_derivative(d, 1)

problem = Problem("1D Movement")
problem.add_fluent(on)
problem.add_fluent(d)
problem.add_action(a)
problem.add_action(b)
problem.add_action(evt)
problem.set_initial_value(on, False)
problem.set_initial_value(d, 0)
problem.add_goal(GE(d, 10))

z = Fluent("z", BoolType())
pr = Process("Name")
pr.add_precondition(z)

with OneshotPlanner(problem_kind=problem.kind) as planner:
    result = planner.solve(problem)
    if result.status in unified_planning.engines.results.POSITIVE_OUTCOMES:
        print(f"{planner.name} found this plan: {result.plan}")
    else:
        print("No plan found.")
