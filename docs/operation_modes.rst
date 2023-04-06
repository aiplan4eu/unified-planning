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

.. literalinclude:: ./code_snippets/oneshot_planner.py
    :caption: OneshotPlanner with automatic Engine selection
    :lines: 37-46

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

.. literalinclude:: ./code_snippets/oneshot_planner.py
    :caption: OneshotPlanner with parallel Engines execution
    :lines: 50-62


PlanValidator
--------
Plan validation is the problem of deciding, given a planning problem and a plan, if the plan is a valid solution for the problem. Also, this OM specifies only one method to be implemented by the engines: ``validate(problem : AbstractProblem, plan: Plan)``.

.. literalinclude:: ./code_snippets/oneshot_planner.py
    :caption: Getting PlanValidator with Engine name
    :lines: 67-74

The result of the `validate` method is a `ValidationResult`, containing a status flag which can be either ``ValidationResultStatus.VALID`` or ``ValidationResultStatus.INVALID``, the name of the engine used and possibly log messages produced by the engine and a map from quality metrics defined in the problem and their evaluations in the plan (`metric_evaluations` map).

SequentialSimulator
--------

This OM defines an interactive simulator for exploring the planning space of a given problem. Given a problem at construction time, it is possible to check if an action is applicable in a state, and to compute successor states. States contain the value of all the fluents in the problem, hence it is possible to easily construct visualizations and plots. Moreover, using this OM it is easy to cast the planning problem into Model-Free Reinforcement Learning (by using the simulator for constructing the rollouts) and to construct prototypes of planners and validators (because the simulator essentially encapsulates the operational semantics of the planning problems).

.. literalinclude:: ./code_snippets/simulator.py
    :caption: Simulate a SequentialPlan and inspect the value of a fluent during plan execution
    :lines: 51-66

Each method of the `SequentialSimulator` is stateless, meaning that it is not required to simulate a sequence of states in order, but it is possible to “jump” among different states of the same problem.

Compiler
--------

The “Compiler” OM defines a transformation of an `AbstractProblem` into another one. This model-to-model transformation can serve different purposes depending on the type of compilation being implemented. At the time of writing, the UP implements the following `CompilationKinds`.

+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| CompilationKind                 | Description                                                                                                                                                           |
+=================================+=======================================================================================================================================================================+
| GROUNDING                       | Transforms a Problem into an equivalent one where every action does not have any finite-domain parameter.                                                             |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| CONDITIONAL_EFFECTS_REMOVING    | Rewrites a problem into an equivalent one where all effects of all actions are non-conditional.                                                                       |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| DISJUNCTIVE_CONDITIONS_REMOVING | Rewrites a problem into an equivalent one where all actions (pre)conditions and effects conditions are pure conjunctions of literals.                                 |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| NEGATIVE_CONDITIONS_REMOVING    | Rewrites a problem into an equivalent one where all actions (pre)conditions and effects conditions do not use the negation operator.                                  |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| QUANTIFIERS_REMOVING            | Rewrites a problem into an equivalent one where all actions (pre)conditions and effects conditions do not use universal nor existential quantification over objects.  |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| TRAJECTORY_CONSTRAINTS_REMOVING | Rewrites a problem into an equivalent one with no trajectory constraints.                                                                                             |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| USERTYPE_FLUENTS_REMOVING       | Rewrites a problem into an equivalent one where no fluent has user-defined type.                                                                                      |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| BOUNDED_TYPES_REMOVING          | Rewrites a problem into an equivalent one where all numeric types are unbounded and the bounds constraints are preserved only by actions and effects (pre)conditions. |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Also the ``Compiler`` OM can be used either by specifying a certain engine by name or by letting the UP to pick a suitable implementation; in addition, the user has to specify the ``compilation_kind`` to indicate which kind of transformation is needed.

.. literalinclude:: ./code_snippets/compiler.py
    :caption: Remove Quantifiers from a Problem and solve it
    :lines: 25-43

Instead of just returning the transformed problem, the OM (which defines a single compile method) returns an object containing also a ``map_back_action_instance`` field, which is a function taking an ``ActionInstance`` for the transformed problem and returning the corresponding ``ActionInstance`` in the original problem (if any). In this way, it is possible to transform back plans generated for the target problems into plans generated for the original one. To simplify this process, all UP ``Plans`` offer a ``replace_action_instances`` method (shown in the example above) which applies this reverse transformation to all the actions in the plan.


AnytimePlanner
--------
Similarly to ``OneshotPlanner``, the ``AnytimePlanner`` OM aims at generating valid plans given a problem specification. Differently from `OneshotPlanning`, however,  the `AnytimePlanner` OM generates a stream of solutions instead of a single one, and this is represented in Python by using a `generator`. The `AnytimePlanner` OM defines a single method, called ``get_solutions(Problem: AbstractProblem)``, returning an `iterator` of ``PlanGenerationResults``. The OM does not specify by default which relation should incur among the generated solutions, but it is possible to ask for a specific guarantee by setting the ``anytime_guarantee`` parameter. Values of this enumeration are listed below.

+--------------------+--------------------------------------------------------------------------------------------------------------------------------------+
| AnytimeGuarantee   | Description                                                                                                                          |
+====================+======================================================================================================================================+
| INCREASING_QUALITY | Each generated plan will have at least one metric specified in the problem with a better value than all previously generated plans.  |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------+
| OPTIMAL_PLANS      | Each generated plan is optimal with respect to the metric specified in the problem.                                                  |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------+

The generator returned by the OM can be simply iterated as any sequence object and will yield a sequence of ``PlanGenerationResult``.

.. code-block::
    :caption: Decreasing plan length

        problem.add_quality_metric(MinimizeSequentialPlanLength())
        with AnytimePlanner(
            problem_kind=problem.kind, anytime_guarantee="INCREASING_QUALITY"
        ) as planner:
            for i, p in enumerate(planner.get_solutions(problem)):
                plan = p.plan
                print(f"{i+1}) {p.plan.actions}")
                if len(p.plan.actions) <= 4:
                    print("Done!")
                    break
        # 1) [move(l1, l2), load(o1, l2), move(l2, l1), unload(o1, l1), move(l1, l2), load(o2, l2), move(l2, l1), unload(o2, l1)]
        # 2) [move(l1, l2), load(o1, l2), load(o2, l2), move(l2, l1), unload(o1, l1), unload(o2, l1)]
        # 3) [move(l1, l2), load_all(l2), move(l2, l1), unload_all(l1)]
        # Done!

Replanner
--------

In order to support a re-planning schema, the UP provides a dedicated OM called `Replanner`. The idea of this OM is to work as a `OneshotPlanner` where the problem being solved can change from one call to another. The engines implementing this OM are informed of the single changes to the problem, consisting in adding or removing actions or goals or changing the initial state.
In this way, an engine can possibly re-use computations done for solving previous calls in order to speed-up subsequent calls. The interface of the OM consists of a ``resolve()`` method devoted to solving the current problem formulation and the following problem modification primitives:
* ``remove_action``: removes an action of the problem, specified by name;
* ``add_action``: adds a new action to the problem;
* ``update_initial_value``: changes the initial value of a specified fluent
* ``remove_goal``: removes a goal from the problem
* ``add_goal``: adds a new goal to the problem.

Importantly, the replanner object needs to be kept in memory from one resolve call to another to possibly exploit the incrementality of the engine.

.. code-block::
    :caption: Replanner example removing and adding actions

        with Replanner(problem) as replanner:
            print(f"1) {replanner.resolve().plan.actions}")
            replanner.remove_action("move_l1_l3")
            print(f"2) {replanner.resolve().plan.actions}")
            replanner.remove_action("move_l3_l4")
            print(f"3) {replanner.resolve().plan}")
            replanner.add_action(move_l2_l4)
            print(f"4) {replanner.resolve().plan.actions}")
            replanner.remove_action("move_l1_l2")
            replanner.update_initial_value(occupied_location, l2)
            print(f"5) {replanner.resolve().plan.actions}")
            replanner.remove_goal(occupied_location.Equals(l4))
            replanner.add_goal(occupied_location.Equals(l3))
            print(f"6) {replanner.resolve().plan.actions}")
        # 1) [move_l1_l3, move_l3_l4]
        # 2) [move_l1_l2, move_l2_l3, move_l3_l4]
        # 3) None
        # 4) [move_l1_l2, move_l2_l4]
        # 5) [move_l2_l4]
        # 6) [move_l2_l3]

PlanRepairer
--------
Another OM devoted to supporting online (re)planning is ``PlanRepairer``. The idea of this OM is to generate a valid (and possibly optimal) plan for a given problem. However, differently from `OneshotPlanner`, the engine can use a given plan as a seed for its search. The specified plan might or not be valid and can be ignored; however, the spirit of the OM would be to find a valid/optimal plan close enough to the given seed plan. Ideally, this is useful in situations where a plan has been automatically or manually generated, but the execution of the plan failed and we are looking for a recovery from this failure without regenerating the whole plan from scratch, but instead we seek to fix the plan for the new contingencies.
The interface of the OM consists of a single method called ``repair(problem: AbstractProblem, plan: Plan)`` returning a ``PlanGenerationResult`` object just like `OneshotPlanner`. Moreover, it is possible to specify an ``optimality_guarantee`` as described in the `OneshotPlanner` section.

.. code-block::
    :caption: PlanRepairer example

        broken_plan = ... # a plan that might or not be valid for the problem
        with PlanRepairer(problem_kind=problem.kind, plan_kind=broken_plan.kind) as repairer:
            new_plan = repairer.repair(problem, broken_plan).plan

PortfolioSelector
--------
This OM provides a service for selecting a promising ``OneshotPlanner`` for a given problem. The UP library filters the available engines selecting those which can, in principle, solve a given problem (this mechanism is applied in all OMs when only the problem kind is specified in the query); however, the UP does not implement sophisticated mechanisms to select among the applicable engines (if more than one engine is available for solving a certain problem). Instead, a simple precedence list is specified (and can be updated by the user either via code or via a configuration file). The ``PortfolioSelector`` OM, instead, allows the user to invoke more sophisticated selection mechanisms, usually derived automatically by means of Machine Learning algorithms.
The OM defines a single method called ``get_best_oneshot_planners(problem: AbstractProblem)`` which returns an ordered list of engine names and an ordered list of parameters, where a pair engine name and parameters appearing at index ``i`` is considered by the engine to be better than any engine at index ``j > i``. The output is designed to be immediately usable by a ``OneshotPlanner`` call (possibly using parallel execution, as described above.)

.. code-block::
    :caption: PortfolioSelector example

        # 3 different problems, all solvable by tamer, enhsp and fast-downward
        problem_1 = ...
        problem_2 = ...
        problem_3 = ...
        with PortfolioSelector(problem_kind=problem.kind) as selector:
            planners, params = selector.get_best_oneshot_planners(problem_1)
            print(f"1) {planners}, {params}")
            planners, params = selector.get_best_oneshot_planners(problem_2)
            print(f"2) {planners}, {params}")
            planners, params = selector.get_best_oneshot_planners(problem_3)
            print(f"3) {planners}, {params}")
            planners, params = selector.get_best_oneshot_planners(problem_1, max_engines=2)
            print(f"4) {planners}, {params}")

        # 1) [tamer, enshp, fast-downward], [{}, {}, {}]
        # 2) [enhsp, fast-downward, tamer], [{}, {}, {}]
        # 3) [fast-downward, tamer, enhsp], [{}, {}, {}]
        # 4) [tamer, enshp], [{}, {}]
