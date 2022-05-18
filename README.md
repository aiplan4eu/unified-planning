# The AIPlan4EU Unified Planning Library

[![Actions Status](https://github.com/aiplan4eu/unified-planning/actions/workflows/main.yml/badge.svg)](https://github.com/aiplan4eu/unified-planning/actions)
[![Coverage Status](https://codecov.io/gh/aiplan4eu/unified-planning/branch/master/graph/badge.svg?token=GBM7HYNDRB)](https://codecov.io/gh/aiplan4eu/unified-planning)
[![Documentation Status](https://readthedocs.org/projects/unified-planning/badge/?version=latest)](https://unified-planning.readthedocs.io/en/latest/)

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

x = Fluent('x')

a = InstantaneousAction('a')
a.add_precondition(Not(x))
a.add_effect(x, True)

problem = Problem('basic')
problem.add_fluent(x)
problem.add_action(a)
problem.set_initial_value(x, False)
problem.add_goal(x)

with OneshotPlanner(problem_kind=problem.kind) as planner:
    plan = planner.solve(problem)
    print(plan)
```


## Notebooks

More complex live demos are available as notebooks:

* [Basic usage](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Unified_Planning_Basics.ipynb)
* [Temporal Planning](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Unified_Planning_Temporal.ipynb)
* [Simulated Effects](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Simulated_effects.ipynb)
* [Planning Engine Integration](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Planning_engine_demo.ipynb)


## Acknowledgments

<img src="https://www.aiplan4eu-project.eu/wp-content/uploads/2021/07/euflag.png" width="60" height="40">

This library is being developed for the AIPlan4EU H2020 project (https://aiplan4eu-project.eu) that is funded by the European Commission under grant agreement number 101016442.
