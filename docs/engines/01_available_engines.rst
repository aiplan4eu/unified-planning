
Available Engines
=================



The tables below give a high-level overview of the planning engines integrated with the UP.

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
    - 🗸
    - 
    - 
    - plan length, action costs
  * - `ENHSP`_
    - OneShot, Anytime
    - 🗸
    - 🗸
    -
    - action costs, final value
  * - `Tamer`_
    - OneShot
    - 🗸
    - 🗸
    - 🗸
    - 
  * - `Aries`_ [#aries-actions]_
    - OneShot, Anytime
    - 🗸
    - 🗸 (integers)
    - 🗸
    - plan length, makespan, action costs
  * - `Pyperplan`_ [#pyperplan-note]_
    - OneShot
    - 🗸
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
  * - `UP (builtin)`
    - 🗸
    - 
    - 
    - 
    - 
  * - `Tamer`_
    - 🗸
    - 🗸
    - 🗸
    - 
    - 
  * - `Aries`_
    - 🗸
    - 🗸
    - 🗸
    - 🗸
    - 🗸


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
    - 🗸
    - 🗸 (integers)
    - 🗸
    - 🗸
    - plan length, makespan, action costs

A WIP integration is known for `SIADEX <https://github.com/UGR-IntelligentSystemsGroup/up-siadex/>`_.

Scheduling
^^^^^^^^^^

The only planner with full support for scheduling is `Aries`_. Integration work is known for the `discrete-optimization suite <https://github.com/aiplan4eu/up-discreteoptimization>`_ and for `PPS <https://github.com/aiplan4eu/up-pps>`_.





.. _`aries`: https://github.com/plaans/aries/blob/master/planning/unified/plugin/README.md
.. _`fast-downward`: https://github.com/aiplan4eu/up-fast-downward/blob/main/README.md
.. _`tamer`: https://github.com/aiplan4eu/up-tamer/blob/master/README.md
.. _`enhsp`: https://github.com/aiplan4eu/up-enhsp/blob/master/README.md
.. _`spiderplan`: https://github.com/aiplan4eu/up-spiderplan/blob/master/README.md
.. _`fmap`: https://github.com/aiplan4eu/up-fmap/blob/master/README.md
.. _`lpg`: https://github.com/aiplan4eu/up-lpg/blob/master/README.md
.. _`pyperplan`: https://github.com/aiplan4eu/up-pyperplan/blob/master/README.md