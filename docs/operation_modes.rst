Operation Modes
===============

Operation Modes (OMs) represent and standardize the possible interactions with a planning engine. Each OM defines an API that an engine willing to support the OM shall implement: in this way, engines declaring to support the same OM can be used interchangeably.
Each OM defines an interface by means of a “mixin”, which in Python lingo means an abstract class to be inherited together with other classes to construct an emerging behavior. In our case, a planning engine can inherit multiple such mixins to signal the support of multiple operation modes. Each OM defines a set of methods (we carefully designed such methods to be non-interfering with one another) which are documented to clarify the expected assumptions and guarantees. Moreover, as we will discuss below, each engine will inherit from the `Engine` abstract class which provides the basic machinery for the plug-in mechanism and for declaring the supported kinds of problems.
All the operation modes can be invoked by using the `Factory` class, which implements the engine-selection mechanism based on our plug-in system. Each environment contains a private `Factory`, allowing different subsets of engines and selection priorities to co-exist in the same process, and each OM is also exposed as a top-level function for the global environment in the unified_planning.shortcuts module. When calling the OM constructor (either from the factory or from the shortcuts) it is always possible to specify the name of the engine to be used (i.e. to force to select a specific engine, if available) or to let the UP to select an engine automatically, by specifying only the `ProblemKind` (which can be retrieved automatically from a problem `p` using the ``p.kind`` property).

We currently support the following operation modes:

OneshotPlanner
--------
The simplest and more obvious operation mode is called `OneshotPlanner`. The semantics of this OM is very simple: given a problem, return a solution plan for it or declare it unsolvable. This is the usual planning query which is the object of the International Planning Competition and is arguably the expected basic functionality of any “planner”.
The example below shows a basic usage of the OM: the `OneshotPlanner` constructor selects a planning engine suitable for the given kind of problem and the OM defines a single ``solve(p: AbstractProblem)`` method to be implemented by the engine. This method returns a `PlanGenerationResult` object containing information about the the generated plan (if any), the metrics being optimized, log messages (if any) and a status flag indicating if the problem has been solved, under which optimality guarantee or if the planner encountered errors or proved the problem unsatisfiable.

.. code-block::
    :caption: OneshotPlanner with automatic Engine selection

        with OneshotPlanner(problem_kind=problem.kind) as planner:
            result = planner.solve(problem)
            print(result)
        # PlanGenerationResult(
        #    status=<PlanGenerationResultStatus.SOLVED_SATISFICING: 1>,
        #    plan=[move(l1, l2), load(l2), move(l2, l1), unload(l1)],
        #    engine_name='Fast Downward',
        #    metrics=None
        #    log_messages=[]
        # )

The possible values for the status flag are defined in the ``PlanGenerationResultStatus`` enumeration listed below.

+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Value               | Meaning                                                                                                                                                                   |
+=====================+===========================================================================================================================================================================+
|  SOLVED_SATISFICING | Valid plan found.                                                                                                                                                         |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| SOLVED_OPTIMALLY    | Optimal plan found                                                                                                                                                        |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|  UNSOLVABLE_PROVEN  | The problem admits no plan, no valid plan exists                                                                                                                          |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| TIMEOUT             | The planner ran out of time                                                                                                                                               |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MEMOUT              | The planner ran out of memory                                                                                                                                             |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| INTERNAL_ERROR      | The planner encountered an internal error                                                                                                                                 |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| INTERMEDIATE        | The report is not a final one but an intermediate one. This is used only by the AnytimePlanner OM (described below) to report plans found during the iterative procedure. |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

At construction time, it is possible to specify an `OptimalityGuarantee`, which requires the engine to find an optimal solution (`SOLVED_OPTIMALLY`) for the problem or allows it to return sub-optimal plans (`SATISFICING`).
In the example above, it suffices to invoke the OM as ``OneshotPlanner(problem_kind=problem.kind, optimality_guarantee=OptimalityGuarantee.SOLVED_OPTIMALLY)`` to require an engine capable of finding the optimal solution for the problem (which should have at least one optimality metric to optimize).

Note that in the example above, we used the automated engine selection  offered by the `UP`, because we did not indicate the name of the engine we wanted to use. We could specify an exact engine to be used by invoking the OM as ``OneshotPlanner(name=”tamer”)``. When specifying an engine to be used, it is also possible to pass engine-specific parameters to control the engine behaviors, for example:
``OneshotPlanner(name=”tamer”, param={“heuristic”: “hadd”, “weight”: 0.8})``

Finally, it is possible to execute more than one `OneshotPlanner` in parallel by simply specifying the list of names and the specific parameters of every parallel execution as shown in the example below.

.. code-block::
    :caption: OneshotPlanner with parallel Engines execution

        with OneshotPlanner(
            names=["tamer", "fast-downward", "enhsp"],
            params=[{“heuristic”: “hadd”, “weight”: 0.8}, {}, {}],
        ) as planner:
            result = planner.solve(problem)
            print(result)
        # PlanGenerationResult(
        #    status=<PlanGenerationResultStatus.SOLVED_SATISFICING: 1>,
        #    plan=[move(l1, l2), load(l2), move(l2, l1), unload(l1)],
        #    engine_name='Fast Downward',
        #    metrics=None
        #    log_messages=[]
        # )


PlanValidator
--------
Plan validation is the problem of deciding, given a planning problem and a plan, if the plan is a valid solution for the problem. Also, this OM specifies only one method to be implemented by the engines: ``validate(problem : AbstractProblem, plan: Plan)``.

.. code-block::
    :caption: Getting PlanValidator with Engine name

        with PlanValidator(name="tamer") as validator:
            result = validator.validate(problem, plan)
            print(result)
        # ValidationResult(
        #    status=<ValidationResultStatus.VALID: 1>,
        #    engine_name='sequential_plan_validator',
        #    log_messages=[]
        #    metric_evaluations={minimize actions-cost:
        #        {'move': distance(l_from, l_to), 'default': None}: 10}
        #
        # )

The result of the `validate` method is a `ValidationResult`, containing a status flag which can be either ``ValidationResultStatus.VALID`` or ``ValidationResultStatus.INVALID``, the name of the engine used and possibly log messages produced by the engine and a map from quality metrics defined in the problem and their evaluations in the plan (`metric_evaluations` map).

SequentialSimulator
--------

This OM defines an interactive simulator for exploring the planning space of a given problem. Given a problem at construction time, it is possible to check if an action is applicable in a state, and to compute successor states. States contain the value of all the fluents in the problem, hence it is possible to easily construct visualizations and plots. Moreover, using this OM it is easy to cast the planning problem into Model-Free Reinforcement Learning (by using the simulator for constructing the rollouts) and to construct prototypes of planners and validators (because the simulator essentially encapsulates the operational semantics of the planning problems).

.. code-block::
    :caption: Simulate a SequentialPlan and inspect the value of a fluent during plan execution

        battery = FluentExp(problem.fluent("battery"))
        with SequentialSimulator(problem) as simulator:
            print(f"Initial battery = {state.get_value(battery)}")
            state = simulator.get_initial_state()
            for ai in plan.actions:
                state = simulator.apply(state, ai)
                print(f"Applied action: {ai}. ", end="")
                print(f"Remaining battery: {state.get_value(battery)}")
            if simulator.is_goal(state):
                print("Goal reached!")
        # Initial battery = 100
        # Applied action: move(l1, l2). Remaining battery: 80
        # Applied action: load(l2). Remaining battery: 75
        # Applied action: move(l2, l1). Remaining battery: 50
        # Applied action: unload(l1). Remaining battery: 45
        # Goal reached!

Each method of the `SequentialSimulator` is stateless, meaning that it is not required to simulate a sequence of states in order, but it is possible to “jump” among different states of the same problem.

* Compiling: is an operation mode that transforms a given problem into an equivalent one that doesn't make use of action parameters or first order predicates. The library implements several simplifications and compilations that can transform one problem into an equivalent one getting rid of some of the planning constructs. For example, we offer a functionality to remove conditional effects from the planning problem specification by compiling the input problem into an equivalent one that does not make use of conditional effects. Our architecture is very general and offers functionalities to transform a plan for the target problem of the compilation into a plan for the input problem. This allows the creation of pipelines of compilers that can map an input planning problem into an equivalent one supported by a target planning engine and then transform back the plan generated by the engine into a valid plan for the overall input problem.


The solving interface also features a powerful automatic filtering of planning engines. In fact, the input planning problem is automatically analysed in order to determine the features needed to tackle the problem itself. The planning engines available on the system where the library is executed are then filtered, and only the ones that are capable of tackling the problem are left for the user to select from. This mechanism simplifies the job of the user in the selection of the right planning engine to be used.
All the functionalities of the solving interface are collected under the ``unified_planning.engines`` package.

Compiler Example
-------
The following example shows how to create a compiler to remove negative conditions from a problem and to retrieve the plan for the original problem from a plan of the transformed problem. If the planner does not support negative conditions, the original problem could not be solved, while the compiler allows us to solve the problem anyway.

.. literalinclude:: ./code_snippets/robot_battery.py
    :lines: 42-76

OneshotPlanner Example
-------

The following example shows how to get a planner and solve a problem.

.. literalinclude:: ./code_snippets/robot_battery.py
    :lines: 80-86
