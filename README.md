# The AIPlan4EU Unified Planning Library

[![Actions Status](https://github.com/aiplan4eu/unified-planning/actions/workflows/release.yml/badge.svg)](https://github.com/aiplan4eu/unified-planning/actions)
[![Coverage Status](https://codecov.io/gh/aiplan4eu/unified-planning/branch/master/graph/badge.svg?token=GBM7HYNDRB)](https://codecov.io/gh/aiplan4eu/unified-planning)
[![Documentation Status](https://readthedocs.org/projects/unified-planning/badge/?version=latest)](https://unified-planning.readthedocs.io/en/latest/)
[![PyPI version](https://badge.fury.io/py/unified-planning.svg)](https://pypi.python.org/pypi/unified-planning)

The unified_planning library makes it easy to formulate planning problems and to invoke automated planners.

* Define problems in a *simple*, *intuitive*, and *planner independent* way
* Solve your planning problems using one of the native solvers, or by using any PDDL planner
* Dump your problems in PDDL (or  ANML) format
* Parse PDDL problem formulations
* Simplification, grounding, removal of conditional effects and many other transformations are available
* and more...

## Usage
```python
from unified_planning.shortcuts import *

x = Fluent("x")

a = InstantaneousAction("a")
a.add_precondition(Not(x))
a.add_effect(x, True)

problem = Problem("basic")
problem.add_fluent(x)
problem.add_action(a)
problem.set_initial_value(x, False)
problem.add_goal(x)

with OneshotPlanner(problem_kind=problem.kind) as planner:
    result = planner.solve(problem)
    if result.status in unified_planning.engines.results.POSITIVE_OUTCOMES:
        print(f"{planner.name} found this plan: {result.plan}")
    else:
        print("No plan found.")
```

## Documentation

The documentation is available [here](https://unified-planning.readthedocs.io/en/latest/)

## Examples

More complex examples are available as notebooks [here](https://unified-planning.readthedocs.io/en/latest/examples.html).

## Staying Updated

To stay informed about project updates, announcements, and general discussions, we encourage you to join our public mailing list: (https://groups.google.com/g/unified-planning).

You can subscribe to this list to receive notifications and engage in community discussions.

## Acknowledgments

<img src="https://www.aiplan4eu-project.eu/wp-content/uploads/2021/07/euflag.png" width="60" height="40">

This library is being developed for the AIPlan4EU H2020 project (https://aiplan4eu-project.eu) that is funded by the European Commission under grant agreement number 101016442.
