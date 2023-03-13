# Copyright 2021 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unified_planning.plans import ActionInstance
from unified_planning.plans.hierarchical_plan import (
    MethodInstance,
    Decomposition,
    HierarchicalPlan,
)
from unified_planning.shortcuts import *
from unified_planning.model.htn import *
from collections import namedtuple

Example = namedtuple("Example", ["problem", "plan"])


def get_example_problems():
    problems = {}

    # basic
    htn = HierarchicalProblem()

    Location = UserType("Location")
    l1 = htn.add_object("l1", Location)
    l2 = htn.add_object("l2", Location)
    l3 = htn.add_object("l3", Location)
    l4 = htn.add_object("l4", Location)

    loc = htn.add_fluent("loc", Location)

    connected = Fluent("connected", l1=Location, l2=Location)
    htn.add_fluent(connected, default_initial_value=False)
    htn.set_initial_value(connected(l1, l2), True)
    htn.set_initial_value(connected(l2, l3), True)
    htn.set_initial_value(connected(l3, l4), True)
    htn.set_initial_value(connected(l4, l3), True)
    htn.set_initial_value(connected(l3, l2), True)
    htn.set_initial_value(connected(l2, l1), True)

    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Equals(loc, l_from))
    move.add_precondition(connected(l_from, l_to))
    move.add_effect(loc, l_to)
    htn.add_action(move)
    go = htn.add_task("go", target=Location)

    go_noop = Method("go-noop", target=Location)
    go_noop.set_task(go)
    target = go_noop.parameter("target")
    go_noop.add_precondition(Equals(loc, target))
    htn.add_method(go_noop)

    go_recursive = Method(
        "go-recursive", source=Location, inter=Location, target=Location
    )
    go_recursive.set_task(go, go_recursive.parameter("target"))
    source = go_recursive.parameter("source")
    inter = go_recursive.parameter("inter")
    target = go_recursive.parameter("target")
    go_recursive.add_precondition(Equals(loc, source))
    go_recursive.add_precondition(connected(source, inter))
    t1 = go_recursive.add_subtask(move, source, inter, ident="move")
    t2 = go_recursive.add_subtask(go, target, ident="go-rec")
    go_recursive.set_ordered(t1, t2)
    htn.add_method(go_recursive)

    go1 = htn.task_network.add_subtask(go, l4, ident="go_l4")
    final_loc = htn.task_network.add_variable("final_loc", Location)
    go2 = htn.task_network.add_subtask(go, final_loc, ident="go_final")
    htn.task_network.add_constraint(Or(Equals(final_loc, l1), Equals(final_loc, l2)))
    htn.task_network.set_strictly_before(go1, go2)

    htn.set_initial_value(loc, l1)
    flat_plan = up.plans.SequentialPlan(
        [
            up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2))),
            up.plans.ActionInstance(move, (ObjectExp(l2), ObjectExp(l3))),
            up.plans.ActionInstance(move, (ObjectExp(l3), ObjectExp(l4))),
            up.plans.ActionInstance(move, (ObjectExp(l4), ObjectExp(l3))),
            up.plans.ActionInstance(move, (ObjectExp(l3), ObjectExp(l2))),
        ]
    )
    acts = flat_plan.actions

    # Rebuilds the hierarchy that leads to the sequence of move actions.
    # Several elements are captured from the environment. Their redefinition allows the function
    # to be also usable for the temporal variant as well
    def goto_hier(
        acts: List[ActionInstance], target: Union[Object, FNode]
    ) -> MethodInstance:
        (target,) = get_environment().expression_manager.auto_promote(target)
        if len(acts) == 0:
            return MethodInstance(go_noop, parameters=(target,))
        else:
            a = acts[0]
            return MethodInstance(
                go_recursive,
                parameters=(a.actual_parameters[0], a.actual_parameters[1], target),
                decomposition=Decomposition(
                    {t1.identifier: acts[0], t2.identifier: goto_hier(acts[1:], target)}
                ),
            )

    plan = HierarchicalPlan(
        flat_plan,
        Decomposition(
            {
                go1.identifier: goto_hier(acts[0:3], l4),
                go2.identifier: goto_hier(acts[3:], acts[-1].actual_parameters[-1]),
            }
        ),
    )

    htn_go = Example(problem=htn, plan=plan)
    problems["htn-go"] = htn_go

    # basic temporal
    htn_temporal = HierarchicalProblem()
    overall = ClosedTimeInterval(StartTiming(), EndTiming())

    Location = UserType("Location")
    l1 = htn_temporal.add_object("l1", Location)
    l2 = htn_temporal.add_object("l2", Location)
    l3 = htn_temporal.add_object("l3", Location)
    l4 = htn_temporal.add_object("l4", Location)

    loc = htn_temporal.add_fluent("loc", Location)

    connected = Fluent("connected", l1=Location, l2=Location)
    htn_temporal.add_fluent(connected, default_initial_value=False)
    htn_temporal.set_initial_value(connected(l1, l2), True)
    htn_temporal.set_initial_value(connected(l2, l3), True)
    htn_temporal.set_initial_value(connected(l3, l4), True)
    htn_temporal.set_initial_value(connected(l4, l3), True)
    htn_temporal.set_initial_value(connected(l3, l2), True)
    htn_temporal.set_initial_value(connected(l2, l1), True)

    durative_move = DurativeAction("durative_move", l_from=Location, l_to=Location)
    l_from = durative_move.parameter("l_from")
    l_to = durative_move.parameter("l_to")
    durative_move.add_condition(StartTiming(), Equals(loc, l_from))
    durative_move.add_condition(overall, connected(l_from, l_to))
    durative_move.add_effect(EndTiming(), loc, l_to)
    durative_move.set_fixed_duration(10)
    htn_temporal.add_action(durative_move)
    go = htn_temporal.add_task("go", target=Location)

    go_noop = Method("go-noop_t", target=Location)
    go_noop.set_task(go)
    target = go_noop.parameter("target")
    go_noop.add_precondition(Equals(loc, target))
    htn_temporal.add_method(go_noop)

    go_recursive = Method(
        "go-recursive_t", source=Location, inter=Location, target=Location
    )
    go_recursive.set_task(go, go_recursive.parameter("target"))
    source = go_recursive.parameter("source")
    inter = go_recursive.parameter("inter")
    target = go_recursive.parameter("target")
    go_recursive.add_precondition(Equals(loc, source))
    go_recursive.add_precondition(connected(source, inter))
    t1 = go_recursive.add_subtask(durative_move, source, inter)
    t2 = go_recursive.add_subtask(go, target)
    go_recursive.set_ordered(t1, t2)
    htn_temporal.add_method(go_recursive)

    go1 = htn_temporal.task_network.add_subtask(go, l4)
    final_loc = htn_temporal.task_network.add_variable("final_loc", Location)
    go2 = htn_temporal.task_network.add_subtask(go, final_loc)
    htn_temporal.task_network.add_constraint(
        Or(Equals(final_loc, l1), Equals(final_loc, l2))
    )
    htn_temporal.task_network.set_strictly_before(go1, go2)
    htn_temporal.task_network.add_constraint(
        LT(Timing(0, go2.end), GlobalStartTiming(100))
    )

    htn_temporal.set_initial_value(loc, l1)
    flat_plan = up.plans.TimeTriggeredPlan(  # type: ignore
        [
            (
                Fraction(0, 100),
                up.plans.ActionInstance(durative_move, (ObjectExp(l1), ObjectExp(l2))),
                Fraction(1, 1),
            ),
            (
                Fraction(101, 100),
                up.plans.ActionInstance(durative_move, (ObjectExp(l2), ObjectExp(l3))),
                Fraction(1, 1),
            ),
            (
                Fraction(202, 100),
                up.plans.ActionInstance(durative_move, (ObjectExp(l3), ObjectExp(l4))),
                Fraction(1, 1),
            ),
            (
                Fraction(303, 100),
                up.plans.ActionInstance(durative_move, (ObjectExp(l4), ObjectExp(l3))),
                Fraction(1, 1),
            ),
            (
                Fraction(404, 100),
                up.plans.ActionInstance(durative_move, (ObjectExp(l3), ObjectExp(l2))),
                Fraction(1, 1),
            ),
            (
                Fraction(505, 100),
                up.plans.ActionInstance(durative_move, (ObjectExp(l2), ObjectExp(l1))),
                Fraction(1, 1),
            ),
        ]
    )

    acts = [a[1] for a in flat_plan.timed_actions]  # type: ignore
    plan = HierarchicalPlan(
        flat_plan,
        Decomposition(
            {
                go1.identifier: goto_hier(acts[0:3], l4),
                go2.identifier: goto_hier(acts[3:], acts[-1].actual_parameters[-1]),
            }
        ),
    )

    htn_go_temporal = Example(problem=htn_temporal, plan=plan)
    problems["htn-go-temporal"] = htn_go_temporal

    return problems


if __name__ == "__main__":
    for name, problem in get_example_problems().items():
        print(f"======= {name} ======")
        print(str(problem))
