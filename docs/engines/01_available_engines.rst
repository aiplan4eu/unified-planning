
Available Engines
=================



The tables below give a high-level overview of the planning engines integrated with the UP.

The characterization of the planning systems is deliberately kept very broad and is mainly intended to help identify which planners are relevant for a given class of problem. We redirect you to the specific documentation of each planner for a more in depth characterization of their features and limitations.

In this page only appear solvers that are *officially integrated* in the unified planning library, for which we have reasonable confidence that they will not give you incorrect results (i.e. they successfully pass all :ref:`engine tests <testing_engines>`), now and in the future (i.e. they have a clearly identified maintainer).
We do mention some solvers whose integration is partial, but that may be nevertheless of interest in some special cases.

Action-Based Planning
^^^^^^^^^^^^^^^^^^^^^

.. list-table:: 

  * - Engine
    - Operation modes
    - Classical
    - Numeric
    - Temporal
    - Metrics
  * - `Fast-Downward`_
    - OneShot, Anytime
    - Y
    - 
    - 
    - plan length, action costs
  * - `ENHSP`_
    - OneShot, Anytime
    - Y
    - Y
    -
    - action costs, final value
  * - `Tamer`_
    - OneShot
    - Y
    - Y
    - Y
    - 
  * - `LPG`_
    - OneShot, Repair, Anytime
    - Y
    - Y
    - Y
    - plan length, makespan, action costs
  * - `Aries`_ [#aries-actions]_
    - OneShot, Anytime
    - Y
    - Y (integers)
    - Y
    - plan length, makespan, action costs
  * - `Pyperplan`_ [#pyperplan-note]_
    - OneShot
    - Y
    - 
    - 
    - 

.. [#aries-actions] Aries' focus is on hierarchical planning and scheduling and is likely not competitive with other planners in action-based planning.
.. [#pyperplan-note] Pyperplan is mostly intended for education purposes and cannot be expected to scale to non-trivial problems.


Plan Validation
^^^^^^^^^^^^^^^

.. list-table::

  * - Engine
    - Action-Based planning
    - Numeric
    - Temporal
    - Hierarchical
    - Scheduling
    - Multi-Agent
  * - `UP (builtin)`
    - Y
    - Y
    - 
    - 
    - 
    - 
  * - `Tamer`_
    - Y
    - Y
    - Y
    - 
    - 
    - 
  * - `Aries`_
    - Y
    - Y
    - Y
    - Y
    - Y
    - 
  * - `MA-Plan-Validator`_
    - Y
    -
    -
    -
    -
    - Y

Hierarchical Planning
^^^^^^^^^^^^^^^^^^^^^

.. list-table:: 

  * - Engine
    - Operation modes
    - Total-Order
    - Partial-Order
    - Numeric
    - Temporal
    - Metrics
  * - `Aries`_
    - OneShot, Anytime
    - Y
    - Y (integers)
    - Y
    - Y
    - plan length, makespan, action costs

A WIP integration is known for `SIADEX <https://github.com/UGR-IntelligentSystemsGroup/up-siadex/>`_.

Scheduling
^^^^^^^^^^

The only planner with full support for scheduling is `Aries`_. Integration work is known for the `discrete-optimization suite <https://github.com/aiplan4eu/up-discreteoptimization>`_ and for `PPS <https://github.com/aiplan4eu/up-pps>`_.

Multi-Agent Planning
^^^^^^^^^^^^^^^^^^^^^
Task and Motion Planning
^^^^^^^^^^

.. list-table::

  * - Engine
    - Operation modes
    - Classical
    - Partial-Order
  * - `fmap`_
    - OneShot
    - Y
    - Y
The only planner with support for task and motion planning is `Spiderplan`_.


.. _`aries`: https://github.com/plaans/aries/blob/master/planning/unified/plugin/README.md
.. _`fast-downward`: https://github.com/aiplan4eu/up-fast-downward/blob/main/README.md
.. _`tamer`: https://github.com/aiplan4eu/up-tamer/blob/master/README.md
.. _`enhsp`: https://github.com/aiplan4eu/up-enhsp/blob/master/README.md
.. _`spiderplan`: https://github.com/aiplan4eu/up-spiderplan/blob/master/README.md
.. _`fmap`: https://github.com/aiplan4eu/up-fmap/blob/master/README.md
.. _`lpg`: https://github.com/aiplan4eu/up-lpg/blob/master/README.md
.. _`pyperplan`: https://github.com/aiplan4eu/up-pyperplan/blob/master/README.md
.. _`ma-plan-validator`: https://github.com/aiplan4eu/ma-plan-validator/blob/master/README.md
