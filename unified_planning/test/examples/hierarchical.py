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
from unified_planning.shortcuts import *
from unified_planning.model.htn import *
from collections import namedtuple

Example = namedtuple("Example", ["problem", "plan"])


def get_example_problems():
    problems = {}

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
    t1 = go_recursive.add_subtask(move, source, inter)
    t2 = go_recursive.add_subtask(go, target)
    go_recursive.set_ordered(t1, t2)
    htn.add_method(go_recursive)

    go1 = htn.task_network.add_subtask(go, l4)
    final_loc = htn.task_network.add_variable("final_loc", Location)
    go2 = htn.task_network.add_subtask(go, final_loc)
    htn.task_network.add_constraint(Or(Equals(final_loc, l1), Equals(final_loc, l2)))
    htn.task_network.set_strictly_before(go1, go2)

    htn.set_initial_value(loc, l1)
    plan = up.plans.SequentialPlan(
        [
            up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2))),
            up.plans.ActionInstance(move, (ObjectExp(l2), ObjectExp(l3))),
            up.plans.ActionInstance(move, (ObjectExp(l3), ObjectExp(l4))),
            up.plans.ActionInstance(move, (ObjectExp(l4), ObjectExp(l3))),
            up.plans.ActionInstance(move, (ObjectExp(l3), ObjectExp(l2))),
        ]
    )
    htn_go = Example(problem=htn, plan=plan)

    problems["htn-go"] = htn_go

    return problems


if __name__ == "__main__":
    for name, problem in get_example_problems().items():
        print(f"======= {name} ======")
        print(str(problem))
