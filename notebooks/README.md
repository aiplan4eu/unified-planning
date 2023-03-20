# Notebooks

We present here a list of notebooks recommended to start with unified-planning, available in the `notebooks/` folder of the repository.


## Basic Usage

[![Open In GitHub](https://img.shields.io/badge/see-Github-579aca?logo=github)](Unified_Planning_Basics.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Unified_Planning_Basics.ipynb)

In this notebook we show the basic usage of the unified planning library.

In particular we will go through the following steps:
* create a classical planning problem;
* call a planner to solve the problem;
* go beyond plan generation showing how to validate a plan and how to ground a planning problem;
* call multiple planners in parallel.

## PDDL I/O

[![Open In GitHub](https://img.shields.io/badge/see-Github-579aca?logo=github)](PDDL_IO_Example.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/PDDL_IO_Example.ipynb)

In this notebook we show how to parse a problem from PDDL in the unified_planning and how to write
a unified_planning problem in PDDL.


## Temporal Planning

[![Open In GitHub](https://img.shields.io/badge/see-Github-579aca?logo=github)](Unified_Planning_Temporal.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Unified_Planning_Temporal.ipynb)

In this notebook we show how to use the unified planning library to model temporal problems.

In particular we model the well-known MatchCellar problem and we call a planner to solve it.


## Hierarchical Planning

[![Open In GitHub](https://img.shields.io/badge/see-Github-579aca?logo=github)](Hierarchical_Planning.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Hierarchical_Planning.ipynb)

In this notebook we show how to use the unified planning library to model **hierarchical planning problems**.

In particular, we build a task hierarchy on top of the `logistics` problem.


## Simulated Effects

[![Open In GitHub](https://img.shields.io/badge/see-Github-579aca?logo=github)](Simulated_effects.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Simulated_effects.ipynb)

In this notebook we show the simulated effects usage in the unified planning library.

In particular, we exploit the use of a simulated effects to model the battery consumption of a robot during a movement defining a function in Python code.


## Oversubscription Planning and MetaEngine Usage

[![Open In GitHub](https://img.shields.io/badge/see-Github-579aca?logo=github)](Oversubscription_with_MetaEngine.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Oversubscription_with_MetaEngine.ipynb)

In this notebook we define an oversubscription planning problem and we solve it using a `MetaEngine`.


## Planning Engine Integration

[![Open In GitHub](https://img.shields.io/badge/see-Github-579aca?logo=github)](Planning_engine_demo.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Planning_engine_demo.ipynb)

In this notebook we create a new planning engine for the "Oneshot" operation mode, we register the new planner in the UP library and we test it on a simple problem.

## Compilers

[![Open In GitHub](https://img.shields.io/badge/see-Github-579aca?logo=github)](Compilers_example.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Compilers_example.ipynb)

In this notebook we show the usage of the operation mode "Compiler", explaining how to use a compiler and how to take a plan written for the compiled problem and create the equivalent plan for the original problem.

## Optimal Planning

[![Open In GitHub](https://img.shields.io/badge/see-Github-579aca?logo=github)](Optimal_Planning.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Optimal_Planning.ipynb)

In this notebook we show how to define a problem with an Optimality metric and how to get a solver that
gives the optimal solution regarding the given metric.
