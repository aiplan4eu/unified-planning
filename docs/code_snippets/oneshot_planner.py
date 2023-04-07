from unified_planning.shortcuts import *

problem = Problem()

Location = UserType("Location")

l1 = problem.add_object("l1", Location)
l2 = problem.add_object("l2", Location)
loader_plate = problem.add_object("loader_plate", Location)

loader_at = problem.add_fluent("loader_at", default_initial_value=False, pos=Location)
package_at = problem.add_fluent("package_at", default_initial_value=False, pos=Location)

move = InstantaneousAction("move", l_from=Location, l_to=Location)
move.add_precondition(loader_at(move.l_from))
move.add_effect(loader_at(move.l_from), False)
move.add_effect(loader_at(move.l_to), True)

load = InstantaneousAction("load", pos=Location)
load.add_precondition(loader_at(load.pos))
load.add_precondition(package_at(load.pos))
load.add_effect(package_at(loader_plate), True)
load.add_effect(package_at(load.pos), False)

unload = InstantaneousAction("unload", pos=Location)
unload.add_precondition(package_at(loader_plate))
unload.add_precondition(loader_at(unload.pos))
unload.add_effect(package_at(unload.pos), True)
unload.add_effect(package_at(loader_plate), True)

problem.add_actions([move, load, unload])

problem.set_initial_value(package_at(l2), True)
problem.set_initial_value(loader_at(l1), True)
problem.add_goal(package_at(l1))

with OneshotPlanner(problem_kind=problem.kind) as planner:
    result = planner.solve(problem)
    print(result)
# PlanGenerationResult(
#    status=<PlanGenerationResultStatus.SOLVED_SATISFICING: 1>,
#    plan=[move(l1, l2), load(l2), move(l2, l1), unload(l1)],
#    engine_name='Fast Downward',
#    metrics=None
#    log_messages=[]
# )

assert str(result.plan) == "[move(l1, l2), load(l2), move(l2, l1), unload(l1)]"

with OneshotPlanner(
    names=["tamer", "pyperplan"],
    params=[{"heuristic": "hadd", "weight": 0.8}, {}],
) as planner:
    result = planner.solve(problem)
    print(result)
# PlanGenerationResult(
#    status=<PlanGenerationResultStatus.SOLVED_SATISFICING: 1>,
#    plan=[move(l1, l2), load(l2), move(l2, l1), unload(l1)],
#    engine_name='Fast Downward',
#    metrics=None
#    log_messages=[]
# )

assert str(result.plan) == "[move(l1, l2), load(l2), move(l2, l1), unload(l1)]"

plan = result.plan
with PlanValidator(name="tamer") as validator:
    result = validator.validate(problem, plan)
    print(result)
# ValidationResult(
#    status=<ValidationResultStatus.VALID: 1>,
#    engine_name='tamer',
#    log_messages=[]
# )
