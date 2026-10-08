from unified_planning.shortcuts import *

# [heuristic-start]
Location = UserType("Location")
robot_at = Fluent("robot_at", BoolType(), l=Location)
visited = Fluent("visited", BoolType(), l=Location)

move = InstantaneousAction("move", l_from=Location, l_to=Location)
move.add_precondition(robot_at(move.l_from))
move.add_effect(robot_at(move.l_from), False)
move.add_effect(robot_at(move.l_to), True)
move.add_effect(visited(move.l_to), True)

problem = Problem("visit_all")
problem.add_fluent(robot_at, default_initial_value=False)
problem.add_fluent(visited, default_initial_value=False)
problem.add_action(move)
l1, l2, l3 = (problem.add_object(f"l{i}", Location) for i in (1, 2, 3))
problem.set_initial_value(robot_at(l1), True)
problem.set_initial_value(visited(l1), True)
problem.add_goal(And(visited(l2), visited(l3)))

with SequentialSimulator(problem) as simulator, Heuristic(problem) as h:
    state = simulator.get_initial_state()
    print(f"h(initial state) = {h.value(state)}")
    for action, params in simulator.get_applicable_actions(state):
        successor = simulator.apply(state, action, params)
        print(f"h after {action.name}{params} = {h.value(successor)}")
# h(initial state) = 2
# h after move(l1, l1) = 2
# h after move(l1, l2) = 1
# h after move(l1, l3) = 1
# [heuristic-end]
