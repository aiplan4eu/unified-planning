# Notebooks

We present here a list of notebooks recommended to start with unified-planning, available in the `notebooks/` folder of the repository.


## Basic Usage

[![Open In GitHub](https://img.shields.io/badge/see-Github-579aca?logo=github)](notebooks/Unified_Planning_Basics.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Unified_Planning_Basics.ipynb)

In this notebook we show the basic usage of the unified planning library.

In particular we will go through the following steps:
* create a classical planning problem;
* call a planner to solve the problem;
* go beyond plan generation showing how to validate a plan and how to ground a planning problem;
* call multiple planners in parallel;
* read and write PDDL problems.


## Temporal Planning

[![Open In GitHub](https://img.shields.io/badge/see-Github-579aca?logo=github)](notebooks/Unified_Planning_Temporal.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Unified_Planning_Temporal.ipynb)

In this notebook we show how to use the unified planning library to model temporal problems.

In particular we model the well-known MatchCellar problem and we call a planner to solve it.


## Simulated Effects

[![Open In GitHub](https://img.shields.io/badge/see-Github-579aca?logo=github)](notebooks/Simulated_effects.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Simulated_effects.ipynb)

In this notebook we show the simulated effects usage in the unified planning library.

In particular, we exploit the use of a simulated effects to model the battery consumption of a robot during a movement defining a function in Python code.


## Planning Engine Integration

[![Open In GitHub](https://img.shields.io/badge/see-Github-579aca?logo=github)](notebooks/Planning_engine_demo.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Planning_engine_demo.ipynb)

In this notebook we create a new planning engine for the "Oneshot" operation mode, we register the new planner in the UP library and we test it on a simple problem.
