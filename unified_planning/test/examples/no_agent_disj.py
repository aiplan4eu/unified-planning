from unified_planning.shortcuts import *
from unified_planning.io.pddl_writer import PDDLWriter

Location = UserType('Location')
robot_at = unified_planning.model.Fluent('robot_at', BoolType(), l=Location)
connected = unified_planning.model.Fluent('connected', BoolType(), l_from=Location, l_to=Location)

move = unified_planning.model.InstantaneousAction('move', l_from=Location, l_to=Location)
l_from = move.parameter('l_from')
l_to = move.parameter('l_to')
move.add_precondition(connected(l_from, l_to))
move.add_precondition(robot_at(l_from))
move.add_effect(robot_at(l_from), False)
move.add_effect(robot_at(l_to), True)

problem = unified_planning.model.Problem('robot')
problem.add_fluent(robot_at, default_initial_value=False)
problem.add_fluent(connected, default_initial_value=False)
problem.add_action(move)

NLOC = 10
locations = [unified_planning.model.Object('l%s' % i, Location) for i in range(NLOC)]
problem.add_objects(locations)

problem.set_initial_value(robot_at(locations[0]), True)
for i in range(NLOC - 1):
    problem.set_initial_value(connected(locations[i], locations[i+1]), True)

problem.add_goal(robot_at(locations[-1]))
problem.add_goal(Or(robot_at(locations[-3]), robot_at(locations[-2])))
print(problem)




original_problem = problem
original_problem_kind = problem.kind

w = PDDLWriter(problem)
#w.print_domain()
w.print_problem()







from unified_planning.engines import CompilationKind


# Get the compiler from the factory
with Compiler(
        problem_kind=problem.kind,
        compilation_kind=CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING
) as disjunctive_conditions_remover:
    # After we have the compiler, we get the compilation result
    dcr_result = disjunctive_conditions_remover.compile(
        problem,
        CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING
    )
    dcr_problem = dcr_result.problem
    dcr_kind = dcr_problem.kind

    # Check the result of the compilation
    #assert qr_kind.has_disjunctive_conditions()
    #assert cer_kind.has_disjunctive_conditions()
    assert not dcr_kind.has_disjunctive_conditions()

print(dcr_problem, "Ooooooooooooooooooooooo")
w = PDDLWriter(dcr_problem)
#w.print_domain()
w.print_problem()