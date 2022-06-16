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

Example = namedtuple('Example', ['problem', 'plan'])

def get_example_problems():
    problems = {}

    htn = HierarchicalProblem()

    Location = UserType("Location")
    l1 = Object("l1", Location)
    htn.add_object(l1)
    l2 = Object("l2", Location)
    htn.add_object(l2)
    l3 = Object("l3", Location)
    htn.add_object(l3)

    loc = Fluent("loc", Location)
    htn.add_fluent(loc)

    connected = Fluent("connected", l1=Location, l2=Location)
    htn.add_fluent(connected, default_initial_value=False)

    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(Equals(loc, l_from))
    move.add_precondition(connected(l_from, l_to))
    move.add_effect(loc, l_to)
    htn.add_action(move)
    go = htn.add_task("go", target=Location)

    go_direct = Method("go-direct", source=Location, target=Location)
    go_direct.set_task(go)
    source = go_direct.parameter("source")
    target = go_direct.parameter("target")
    go_direct.add_precondition(Equals(loc, source))
    go_direct.add_precondition(connected(source, target))
    go_direct.add_subtask(move, source, target)
    htn.add_method(go_direct)

    go_indirect = Method("go-indirect", source=Location, inter=Location, target=Location)
    go_indirect.set_task(go, go_indirect.parameter("target"))
    source = go_indirect.parameter("source")
    inter = go_indirect.parameter("inter")
    target = go_indirect.parameter("target")
    go_indirect.add_precondition(Equals(loc, source))
    go_indirect.add_precondition(connected(source, inter))
    t1 = go_indirect.add_subtask(move, source, inter)
    t2 = go_indirect.add_subtask(go, target)
    go_indirect.set_ordered(t1, t2)
    htn.add_method(go_indirect)

    go1 = htn.task_network.add_subtask(go, l1)
    final_loc = htn.task_network.add_variable("final_loc", Location)
    go2 = htn.task_network.add_subtask(go, final_loc)
    htn.task_network.set_strictly_before(go1, go2)
    htn.task_network.add_constraint(Or(Equals(final_loc, l2),
                                       Equals(final_loc, l3)))
    htn.set_initial_value(loc, l1)
    plan = up.plans.SequentialPlan([up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2))), up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)))])
    htn_go = Example(problem=htn, plan=plan)

    problems['htn-go'] = htn_go

    return problems


if __name__ == "__main__":
    for name, problem in get_example_problems().items():
        print(f"======= {name} ======")
        print(str(problem))
