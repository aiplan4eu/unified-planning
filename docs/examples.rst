Examples
========

We present here a list of notebooks recommended to start with unified-planning.

Basic Example
-------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/01-basic-example.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/01-basic-example.ipynb
   :alt: Open In Colab


In this notebook we show the basic usage of the unified planning library.

In particular we will go through the following steps:


* create a classical planning problem;
* call a planner to solve the problem;
* go beyond plan generation showing how to validate a plan and how to ground a planning problem;
* call multiple planners in parallel.



Numeric Planning
----------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/01-numeric-planning.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/01-numeric-planning.ipynb
   :alt: Open In Colab


In this notebook we show how to model a numeric problem.

We will define a simple problem with counters that must be incremented.


Optimal Planning
----------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/02-optimal-planning.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/02-optimal-planning.ipynb
   :alt: Open In Colab


In this notebook we show how to define a problem with an Optimality metric and how to get a solver that gives the optimal solution regarding the given metric.


Temporal Planning
-----------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/03-temporal-planning.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/03-temporal-planning.ipynb
   :alt: Open In Colab


In this notebook we show how to use the unified planning library to model temporal problems.

In particular we model the well-known MatchCellar problem and we call a planner to solve it.


Simple Multi-Agent Planning Problem
-----------------------------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/09-multiagent-planning-simple.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/09-multiagent-planning-simple.ipynb
   :alt: Open In Colab


In this notebook shows how to use the unified planning library to model simple multi-agent problems and what heuristics the planner supports.


Depot Multi-Agent Planning Problem
----------------------------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/10-multiagent-planning.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/10-multiagent-planning.ipynb
   :alt: Open In Colab

In this notebook we show how to use the unified planning library to model multi-agent problems. In particular we model the well-known Depot problem and we call a planner to solve it.


Simulated Effects
-----------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/04-simulated-effects.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/04-simulated-effects.ipynb
   :alt: Open In Colab


In this notebook we show the simulated effects usage in the unified planning library.

In particular, we exploit the use of a simulated effects to model the battery consumption of a robot during a movement defining a function in Python code.


Compilers
---------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/05-compilers.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/05-compilers.ipynb
   :alt: Open In Colab


In this notebook we show the usage of the operation mode "Compiler", explaining how to use a compiler and how to take a plan written for the compiled problem and create the equivalent plan for the original problem.


Oversubscription Planning and MetaEngine Usage
----------------------------------------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/06-oversubscription-with-metaengine.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/06-oversubscription-with-metaengine.ipynb
   :alt: Open In Colab


In this notebook we define an oversubscription planning problem and we solve it using a ``MetaEngine``.


Hierarchical Planning
---------------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/07-hierarchical-planning.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/07-hierarchical-planning.ipynb
   :alt: Open In Colab


In this notebook, we show how to use unified planning library to define hierarchical planning problem.


Sequential Simulator
--------------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/08-sequential-simulator.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/08-sequential-simulator.ipynb
   :alt: Open In Colab


In this notebook, we show how to use the ``SequentialSimulator``.

The simulator is used to:

* check action applicability in a state
* see the state created by an action application
* inspect fluents values during a plan execution
* evaluate quality metrics during plan execution

Planning Engine Integration
---------------------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/planner-integration.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/planner-integration.ipynb
   :alt: Open In Colab


In this notebook we create a new planning engine for the "OneshotPlanner" operation mode, we register the new planner in the UP library and we test it on a simple problem.


PDDL I/O
--------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/io/01-pddl-usage-example.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/io/01-pddl-usage-example.ipynb
   :alt: Open In Colab


In this notebook we show how to parse a problem from PDDL in the unified_planning and how to write
a unified_planning problem in PDDL.


Plan Parsing and Conversion
---------------------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/12-plan-parsing-conversion.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/12-plan-parsing-conversion.ipynb
   :alt: Open In Colab


In this notebook we show how to parse a plan from a file (or a string) and how to convert a plan from a format to another.


MA-PDDL Writer
--------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/io/02-mapddl-writer-example.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/io/02-mapddl-writer-example.ipynb
   :alt: Open In Colab


In this notebook we show how to write a unified_planning problem in MA-PDDL.

Task and Motion Planning
------------------------

In this notebook we show how to create a Task and Motion Planning (TAMP) problem
that includes a map, configurations, and movable objects that are used to impose
motion constraints in TAMP operators. (Note: this example does not work in Colab
because the engine uses Docker itself.)

.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: https:///github.com/aiplan4eu/unified-planning/blob/master/docs/notebooks/io/14-task-and-motion-planning.ipynb
   :alt: Open In GitHub


.. toctree::
   :maxdepth: 2
   :numbered:
   :glob:
   :titlesonly:
   :caption: Examples
   :hidden:

   ./notebooks/*
   ./notebooks/io/*
