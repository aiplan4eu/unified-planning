import unified_planning
from unified_planning.plans import SequentialPlan, ActionInstance
from unified_planning.shortcuts import *
from unified_planning.model.htn import Task, Method, HierarchicalProblem
from unified_planning.test import TestCase

Location = UserType("Location")
objects = [Object(f"l{i}", Location) for i in range(5)]
t1 = Task("t1")
t2 = Task("t2")
t3 = Task("t3")

actions = [InstantaneousAction(f"a{i}") for i in range(10)]


def base():
    pb = HierarchicalProblem()
    pb.add_objects(objects)
    for action in actions:
        pb.add_action(action)
    for task in [t1, t2, t3]:
        pb.add_task(task)
    pb.task_network.add_subtask(t1)
    return pb


def add_method(pb, name, task, *subtasks):
    m = Method(name)
    m.set_task(task)
    s_tasks = [m.add_subtask(st) for st in subtasks]
    m.set_ordered(*s_tasks)
    pb.add_method(m)


def set_costs(pb, *costs):
    cost_map: Dict[Action, Expression] = {}
    for action, cost in zip(actions, costs):
        cost_map[action] = Int(cost)
    pb.add_quality_metric(up.model.metrics.MinimizeActionCosts(cost_map))


def get_test_cases():
    """Generates deterministically a set of non-recursive HTN problems with known optimum."""
    res: Dict[str, TestCase] = {}

    def export(pb, optimum, *costs):
        clone = pb.clone()
        set_costs(clone, *costs)
        clone.name = f"htn:opti-action-costs-{len(res)}"
        test_case = TestCase(clone, solvable=True, optimum=optimum)
        res[clone.name] = test_case

    pb = base()
    add_method(pb, "m11", t1, actions[0], actions[1])
    add_method(pb, "m12", t1, actions[2])

    export(pb, 3, 2, 2, 3)
    export(pb, 4, 2, 2, 4)
    export(pb, 4, 2, 2, 5)

    pb = base()
    add_method(pb, "m11", t1, t2, t3)
    add_method(pb, "m21", t2, actions[0], actions[1])
    add_method(pb, "m31", t3, actions[2], actions[3])
    add_method(pb, "m32", t3, actions[4], actions[5], actions[6])
    export(pb, 4, 1, 1, 1, 1, 1, 1, 1)
    export(pb, 3, 1, 1, 1, 1, 0, 0, 1)
    export(pb, 5, 1, 1, 1, 10, 1, 1, 1)
    export(pb, 13, 1, 1, 1, 10, 1, 10, 1)
    export(pb, 202, 1, 1, 100, 100, 100, 100, 100)

    return res
