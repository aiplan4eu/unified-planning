Execution Environment
====================================

The contingent module exposes execution-environment abstractions for closed-loop interaction with a planning problem.

``ExecutionEnvironment`` defines the minimal contract:

* ``apply(action)`` executes one action and returns an observation map.
* ``is_goal_reached()`` checks whether the current execution state satisfies the goals.

``SimulatedExecutionEnvironment`` provides a concrete implementation for
``ContingentProblem``. It:

* clones the contingent problem into a deterministic ``Problem`` for simulation;
* samples hidden initial fluents consistently with ``oneof`` and ``or`` constraints;
* executes actions through the sequential simulator;
* returns observed fluent values when executing ``SensingAction`` instances.

.. note::

   ``SimulatedExecutionEnvironment`` uses ``pysmt`` to sample hidden initial assignments and requires at least one available SMT solver backend (for example ``z3``).

API Reference
-------------

For complete class APIs, see:

* :doc:`ExecutionEnvironment <model/contingent/ExecutionEnvironment>`
* :doc:`SimulatedExecutionEnvironment <model/contingent/SimulatedExecutionEnvironment>`

Usage Example
-------------

This end-to-end example follows the workflow of the :doc:`ActionSelector and Contingent Execution Environment notebook <../notebooks/15-action-selector-and-execution-environment>`, combining a custom selector with ``SimulatedExecutionEnvironment`` in a contingent closed loop.

.. literalinclude:: ../code_snippets/action_selector_and_execution_environment.py
    :caption: End-to-end contingent closed loop with SimulatedExecutionEnvironment
    :start-after: # [execution-environment-flow-start]
    :end-before: # [execution-environment-flow-end]
