.. _engines:

======================
Metrics & Plan Quality
======================

.. contents::
   :local:


Quality Metrics
===============

The UP library defines a set of "Quality Metrics" to express the objective functions to be optimized. Such metrics are defined in the `unified_planning.model.metrics` file and are described below.

- **MinimizeSequentialPlanLength** is used to optimize the number of steps in the resulting plans.

- **MinimizeActionCosts** assigns a numeric cost to each action in the problem and asks the planner to find a plan of minimal cost.

- **MinimizeExpressionOnFinalState** asks the planner to find a plan that minimizes the value of a given expression in the final state of the plan.

- **MaximizeExpressionOnFinalState** asks the planner to find a plan that maximizes the value of a given expression in the final state of the plan.

- **Oversubscription** Defines a set of optional goals, each with an associated cost that is payed if the goal is not achieved by the plan. The job of the planner is to find a plan that achieves a subset of the optional goals paying the minimal cost.

- **MinimizeMakespan** (Temporal planning only) Asks to find a plan taking the shortest possible time until the ending of the last action in the plan.

Creating quality metrics amounts to instantiate the corresponding object and adding it to one or more `Problem` instances. See the `Optimal Planning Notebook <https://github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/02-optimal-planning.ipynb>`_ for an example.


Optimal, Anytime and Satisficing Planning
=========================================

When dealing with quality metrics, it is useful to keep the following in mind:

- A **satisficing** planner will return the first plan found, regardless of its quality.
- An **optimal** planner will only return a provably optimal plan.
- An **anytime** planner will return a series of plan of increasing quality until it runs out of time or is no longer able to improve its last solution.

.. code-block::

    # By default, Oneshot planner will return the first available solver (typically a satisficing one)
    with OneshotPlanner(problem_kind=problem.kind) as planner:
      res = planner.solve(utr_problem)

    # An optimal solver can be explicitly required with the optimality_guarantee parameter
    with OneshotPlanner(problem_kind=problem.kind,
                        optimality_guarantee=PlanGenerationResultStatus.SOLVED_OPTIMALLY) as optimal_planner:
      res = optimal_planner.solve(utr_problem)

    # An anytime planner can be requested with the AnytimePlanning operation mode
    with AnytimePlanner(problem_kind=problem.kind) as planner:
      for res in planner.get_solutions(problem):
        print(res)

Proving the optimality of plan can be very time-consuming and orders of magnitude longer than finding it.
Indeed, it requires the planner to prove that all potential alternative plans are of lower quality.
As a rule of thumb, if you are interested in finding high quality solutions but do not care about optimality you should use an anytime planner.
Its runtime can be capped with the ``timeout`` parameter of ``get_solutions()`` or may just break out of the loop when your happy with the returned solution.

Notes
-----

- If a planning problem without optimality metrics is required to be solved optimally, an exception is thrown.
- If a planning problem without optimality metrics is solved by a planning engine capable of guaranteeing some optimality, it is anyway marked as `SOLVED_SATISFICING`.
- The UP currently supports only 1 metric in each problem, therefore multi-objective optimization is not possible.
