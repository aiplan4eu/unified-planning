.. _engines:

==========
Optimality
==========

.. contents::
   :local:


Quality Metrics
===============

The UP library defines a set of "Quality Metrics" to express the objective functions to be optimized. Such metrics are defined in the `unified_planning.model.metrics` package and are described below.

- **MinimizeSequentialPlanLength** is used to optimize the number of steps in the resulting plans.

- **MinimizeActionCosts** assigns a numeric cost to each action in the problem and asks the planner to find a plan of minimal cost.

- **MinimizeExpressionOnFinalState** asks the planner to find a plan that minimizes the value of a given expression in the final state of the plan.

- **MaximizeExpressionOnFinalState** asks the planner to find a plan that maximizes the value of a given expression in the final state of the plan.

- **Oversubscription** Defines a set of optional goals, each with an associated cost that is payed if the goal is not achieved by the plan. The job of the planner is to find a plan that achieves a subset of the optional goals paying the minimal cost.

- **MinimizeMakespan** (Temporal planning only) Asks to find a plan taking the shortest possible time until the ending of the last action in the plan.

Creating quality metrics amounts to instantiate the corresponding object and adding it to one or more `Problem` instances. See the `Optimal Planning Notebook <https://github.com/aiplan4eu/unified-planning/blob/master/notebooks/Optimal_Planning.ipynb>`_ for an example.


Optimal and Satisficing Planning
================================

Some planning engines can guarantee to find the optimal solution for some kinds of quality metrics, others can only apply a best-effort approach to find good-quality solutions without optimality guarantees. The UP allows the user to explicitly define the desired optimality guarantees as parameters of the operative modes.

If a planning engine is able to generate a solution result it could be either marked as `SOLVED_OPTIMALLY` or `SOLVED_SATISFICING` to indicate whether the produced solution is guaranteed to be optimal or not.


Notes
-----

If a planning problem without optimality metrics is required to be solved optimally, an exception is thrown.

If a planning problem without optimality metrics is solved by a planning engine capable of guaranteeing some optimality, it is anyway marked as `SOLVED_SATISFICING`.






