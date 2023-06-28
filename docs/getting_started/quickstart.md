# Quickstart

This guide shows the basic usage of the unified planning library.

In particular we will go through the following steps:

-   create a classical planning problem;
-   call a planner to solve the problem;
-   go beyond plan generation showing how to validate a plan and how to ground a planning problem;
-   call multiple planners in parallel.

### Imports

The basic imports we need for this demo are abstracted in the `shortcuts` package.

```python
from unified_planning.shortcuts import *
```

### Problem representation

In this example, we will model a very simple robot navigation problem.

#### Types

The first thing to do is to introduce a `UserType` to model the concept of a location. It is possible to introduce as many types as needed; then, for each type we will define a set of objects of that type.

In addition to `UserType`s we have three built-in types: `Bool`, `Real` and `Integer`.

```python
Location = UserType('Location')
```

#### Fluents and constants

The basic variables of a planning problem are called "fluents" and are quantities that can change over time. Fluents can have differen types, in this first example we will stick to classical "predicates" that are fluents of boolean type. Moreover, fluents can have parameters: effectively describing multiple variables.

For example, a boolean fluent `connected` with two parameters of type `Location` (that can be interpreted as `from` and `to`) can be used to model a graph of locations: there exists an edge between two locations `a` and `b` if `connected(a, b)` is true.

In this example, `connected` will be a constant (i.e. it will never change in any execution), but another fluent `robot_at` will be used to model where the robot is: the robot is in locatiopn `l` if and only if `robot_at(l)` is true (we will ensure that exactly one such `l` exists, so that the robot is always in one single location).

```python
robot_at = unified_planning.model.Fluent('robot_at', BoolType(), l=Location)
connected = unified_planning.model.Fluent('connected', BoolType(), l_from=Location, l_to=Location)
```

#### Actions

Now we have the problem variables, but in order to describe the possible evolutions of a systems we need to describe how these variables can be changed and how they can evolve. We model this problem using classical, action-based planning, where a set of actions is used to characterize the possible transitions of the system from a state to another.

An action is a transition that can be applied if a specified set of preconditions is satisfied and that prescribes a set of effects that change the value of some fluents. All the fluents that are subjected to the action effects are unchanged.

We allow _lifted_ actions, that are action with parameters: the parameters can be used to specify preconditions or effects and the planner will select among the possible values of each parameters the ones to be used to characterize a specific action.

In our example, we introduce an action called `move` that has two parameters of type `Location` indicating the current position of the robot `l_from` and the intended destination of the movement `l_to`. The `move(a, b)` action is applicable only when the robot is in position `a` (i.e. `robot_at(a)`) and if `a` and `b` are connected locations (i.e. `connected(a, b)`). As a result of applying the action `move(a, b)`, the robot is no longer in `a` and is instead in location `b`.

In the unified_planning, we can create actions by instantiating the `InstantaneousAction` class; parameters are specified as keyword arguments to the constructor as shown below. Preconditions and effects are added by means of the `add_precondition` and `add_effect` methods.

```python
move = InstantaneousAction('move', l_from=Location, l_to=Location)
l_from = move.parameter('l_from')
l_to = move.parameter('l_to')
move.add_precondition(connected(l_from, l_to))
move.add_precondition(robot_at(l_from))
move.add_effect(robot_at(l_from), False)
move.add_effect(robot_at(l_to), True)
```

#### Creating the problem

The class that represents a planning problem is `Problem`, it contains the set of fluents, the actions, the objects, an intial value for all the fluents and a goal to be reached by the planner. We start by adding the entities we created so far. Note that entities are not bound to one problem, we can create the actions and fluents one and create multiple problems with them.

```python
problem = Problem('robot')
problem.add_fluent(robot_at, default_initial_value=False)
problem.add_fluent(connected, default_initial_value=False)
problem.add_action(move)
```

The set of objects is a set of `Object` instances, each represnting an element of the domain. In this example, we create `NLOC` (set to 10) locations named `l0` to `l9`. We can create the set of objects and add it to the problem as follows.

```python
NLOC = 10
locations = [Object('l%s' % i, Location) for i in range(NLOC)]
problem.add_objects(locations)
```

Then, we need to specify the initial state. We used the `default_initial_value` specification when adding the fluents, so it suffices to indicate the fluents that are initially true (this is called "closed-world assumption". Without this specification, we would need to initialize all the possible instantiation of all the fluents).

In this example, we connect location `li` with location `li+1`, creating a simple "linear" graph lof locations and we set the initial position of the robot in location `l0`.

```python
problem.set_initial_value(robot_at(locations[0]), True)
for i in range(NLOC - 1):
    problem.set_initial_value(connected(locations[i], locations[i+1]), True)
```

Finally, we set the goal of the problem. In this example, we set ourselves to reach location `l9`.

```python
problem.add_goal(robot_at(locations[-1]))
```

### Solving Planning Problems

The most direct way to solve a planning problem is to select an available planning engine by name and use it to solve the problem. In the following we use `pyperplan` to solve the problem and print the plan.

```python
with OneshotPlanner(name='pyperplan') as planner:
    result = planner.solve(problem)
    if result.status == up.engines.PlanGenerationResultStatus.SOLVED_SATISFICING:
        print("Pyperplan returned: %s" % result.plan)
    else:
        print("No plan found.")
```

The unified_planning can also automatically select, among the available planners installed on the system, one that is expressive enough for the problem at hand.

```python
with OneshotPlanner(problem_kind=problem.kind) as planner:
    result = planner.solve(problem)
    print("%s returned: %s" % (planner.name, result.plan))
```

#### Beyond plan generation

`OneshotPlanner` is not the only operation mode we can invoke from the unified_planning, it is just one way to interact with a planning engine. Another useful functionality is `PlanValidation` that checks if a plan is valid for a problem.

```python
plan = result.plan
with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as validator:
    if validator.validate(problem, plan):
        print('The plan is valid')
    else:
        print('The plan is invalid')
```

It is also possible to use the `Compiler` operation mode with `compilation_kind=CompilationKind.GROUNDING` to create an equivalent formulation of a problem that does not use parameters for the actions.

For an in-depth tutorial about the `Compiler` operation mode check the [Notebook on Compilers](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Compilers_example.ipynb).

```python
with Compiler(problem_kind=problem.kind, compilation_kind=CompilationKind.GROUNDING) as grounder:
    grounding_result = grounder.compile(problem, CompilationKind.GROUNDING)
    ground_problem = grounding_result.problem

    # The grounding_result can be used to "lift" a ground plan back to the level of the original problem
    with OneshotPlanner(problem_kind=ground_problem.kind) as planner:
        ground_plan = planner.solve(ground_problem).plan
        print('Ground plan: %s' % ground_plan)
        # Replace the action instances of the grounded plan with their correspoding lifted version
        lifted_plan = ground_plan.replace_action_instances(grounding_result.map_back_action_instance)
        print('Lifted plan: %s' % lifted_plan)
        # Test the problem and plan validity
        with PlanValidator(problem_kind=problem.kind, plan_kind=ground_plan.kind) as validator:
            ground_validation = validator.validate(ground_problem, ground_plan)
            lift_validation = validator.validate(problem, lifted_plan)
            Valid = up.engines.ValidationResultStatus.VALID
            assert ground_validation.status == Valid
            assert lift_validation.status == Valid
```

#### Parallel planning

We can invoke different instances of a planner in parallel or different planners and return the first plan that is generated effortlessly.

```python
with OneshotPlanner(names=['tamer', 'tamer', 'pyperplan'],
                    params=[{'heuristic': 'hadd'}, {'heuristic': 'hmax'}, {}]) as planner:
    plan = planner.solve(problem).plan
    print("%s returned: %s" % (planner.name, plan))
```
