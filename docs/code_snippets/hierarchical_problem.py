from unified_planning.shortcuts import *

from unified_planning.model.htn import HierarchicalProblem, Method

htn = HierarchicalProblem()

Location = UserType("Location")
l1 = htn.add_object("l1", Location)
l2 = htn.add_object("l2", Location)
l3 = htn.add_object("l3", Location)
l4 = htn.add_object("l4", Location)
l5 = htn.add_object("l5", Location)

loc = htn.add_fluent("loc", Location)

connected = Fluent("connected", l1=Location, l2=Location)
htn.add_fluent(connected, default_initial_value=False)
for li, lj in [(l1, l2), (l2, l3), (l3, l4), (l4, l3), (l3, l2), (l2, l1)]:
    htn.set_initial_value(connected(li, lj), True)

# define low level action, as in non-hierarchical planning
move = InstantaneousAction("move", l_from=Location, l_to=Location)
move.add_precondition(Equals(loc, move.l_from))
move.add_precondition(connected(move.l_from, move.l_to))
move.add_effect(loc, move.l_to)
htn.add_action(move)

# define high-level task: going to some location
go = htn.add_task("go", target=Location)

# first method: nothing to do if already at target
go_noop = Method("go-noop", target=Location)
go_noop.set_task(go)
target = go_noop.parameter("target")
go_noop.add_precondition(Equals(loc, target))
htn.add_method(go_noop)

# second method (tail recursive): first make an allowed move an action
# and recursively decompose go(target) again
go_recursive = Method("go-recursive", source=Location, inter=Location, target=Location)
go_recursive.set_task(go, go_recursive.parameter("target"))
go_recursive.add_precondition(Equals(loc, go_recursive.source))
go_recursive.add_precondition(connected(go_recursive.source, go_recursive.inter))
t1 = go_recursive.add_subtask(
    move, go_recursive.source, go_recursive.inter, ident="move"
)
t2 = go_recursive.add_subtask(go, go_recursive.target, ident="go-rec")
go_recursive.set_ordered(t1, t2)
htn.add_method(go_recursive)

# set objectives tasks in initial task network
go1 = htn.task_network.add_subtask(go, l4, ident="go_l4")
final_loc = htn.task_network.add_variable("final_loc", Location)
go2 = htn.task_network.add_subtask(go, final_loc, ident="go_final")
htn.task_network.add_constraint(Or(Equals(final_loc, l1), Equals(final_loc, l2)))
htn.task_network.set_strictly_before(go1, go2)

htn.set_initial_value(loc, l1)
