Examples
========

.. warning::
   TODO: Fix Notebook links once merged to master

We present here a list of notebooks recommended to start with unified-planning.

Basic Example
-------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: 01-basic-example.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Unified_Planning_Basics.ipynb
   :alt: Open In Colab


In this notebook we show the basic usage of the unified planning library.

In particular we will go through the following steps:


* create a classical planning problem;
* call a planner to solve the problem;
* go beyond plan generation showing how to validate a plan and how to ground a planning problem;
* call multiple planners in parallel;
* read and write PDDL problems.

PDDL I/O
--------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: io/01-pddl-usage-example.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/PDDL_IO_Example.ipynb
   :alt: Open In Colab


In this notebook we show how to parse a problem from PDDL in the unified_planning and how to write
a unified_planning problem in PDDL.

Temporal Planning
-----------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: 03-temporal-planning.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Unified_Planning_Temporal.ipynb
   :alt: Open In Colab


In this notebook we show how to use the unified planning library to model temporal problems.

In particular we model the well-known MatchCellar problem and we call a planner to solve it.

Simulated Effects
-----------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: 04-simulated-effects.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Simulated_effects.ipynb
   :alt: Open In Colab


In this notebook we show the simulated effects usage in the unified planning library.

In particular, we exploit the use of a simulated effects to model the battery consumption of a robot during a movement defining a function in Python code.

Oversubscription Planning and MetaEngine Usage
----------------------------------------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: ./06-oversubscription-with-metaengine.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Oversubscription_with_MetaEngine.ipynb
   :alt: Open In Colab


In this notebook we define an oversubscription planning problem and we solve it using a ``MetaEngine``.

Planning Engine Integration
---------------------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: ./planner-integration.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Planning_engine_demo.ipynb
   :alt: Open In Colab


In this notebook we create a new planning engine for the "Oneshot" operation mode, we register the new planner in the UP library and we test it on a simple problem.

Compilers
---------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: ./05-compilers.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Compilers_example.ipynb
   :alt: Open In Colab


In this notebook we show the usage of the operation mode "Compiler", explaining how to use a compiler and how to take a plan written for the compiled problem and create the equivalent plan for the original problem.

Optimal Planning
----------------


.. image:: https://img.shields.io/badge/see-Github-579aca?logo=github
   :target: Optimal_Planning.ipynb
   :alt: Open In GitHub


.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Optimal_Planning.ipynb
   :alt: Open In Colab


In this notebook we show how to define a problem with an Optimality metric and how to get a solver that
gives the optimal solution regarding the given metric.

.. toctree::
   :maxdepth: 2
   :numbered:
   :glob:
   :titlesonly:
   :caption: Examples
   :hidden:

   ./notebooks/*
   ./notebooks/io/*