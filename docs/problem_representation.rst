Problem Representation
======================

The main functionality offered by the library concerns the specification of a planning problem. The API provides classes and functions to populate a Problem object with the fluents, actions, initial states and goal specifications constituting the planning problem specification.
The functionalities for creating model objects and to manipulate them are collected in the unified_planning.model package of the library.
In all the examples below all the shortcuts must be imported, with the command:

`from unified_planning.shortcuts import *`

Classical and Numeric Example
-------------------------------
The following example shows a simple robotic planning problem modeling a robot moving between locations while consuming battery. The example shows the basic functionalities and objects needed to declare the problem specification. A more detailed presentation of the different objects is available on the `Google Colab <https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Unified_Planning_Basics.ipynb>`_ Python notebook where we document and explain all the different classes and their semantics.

.. literalinclude:: ./code_snippets/robot_battery.py
    :lines: 3-38


In the current version, the Unified-Planning library allows the specification of classical, numerical and temporal planning problems. In order to support the latitude expressiveness levels we have operators for arithmetic such as plus minus times and division and specific temporal operators to attach conditions and effects to specific timings within the duration of an action. The library :ref:`documentation <api-ref>` provides examples and describes the use of these functionalities.


Temporal Example
-----------------
Temporal planning is the problem of finding a plan for a planning problem involving durative actions and/or temporal constraints.
This means that it is possible to model actions having:
* duration constrained by a (possibly state-based) lower and and upper bound
* conditions or effects expressed at specific instant of the action, in particular at times start+delay or end+delay, where start refers to the starting time of the action, end to the ending time and delay is a real constant (positive or negative).
* durative conditions to be maintained within sub-intervals, delimited by the same time-point used for instantaneous conditions.

.. literalinclude:: ./code_snippets/temporal_and_scheduling.py
    :lines: 3-44


Scheduling Example
-------------------
Scheduling is a restricted form of temporal planning where the set of actions (usually called activities) are known in advance and the problem consists in deciding the timing of the activities.
Generally, scheduled problems involve resources and constraints that define the feasible space of solutions.
Since scheduling problems are very common and scheduling as a computer science problem belongs to a simpler complexity class (NP) with respect to temporal planning (PSPACE, under suitable assumptions) we created a dedicated representation for scheduling problems.
We can represent a generic scheduling problem using the SchedulingProblem class as shown in the example below.

.. literalinclude:: ./code_snippets/temporal_and_scheduling.py
    :lines: 47-78


MultiAgent Example
-------------------
Multi-agent Planning lifts planning to a context where many agents operate in a common environment, each with its own view of the domain. The objective is to produce a set of plans, one for each agent, which allows the agents to achieve their goals.
The problem comes in several variants, depending on various features. Specifically, multi-agent planning can be competitive, meaning that the agents compete against each other in order to achieve their goal, or cooperative, which refers to the case where the agents collaborate towards a common goal. Another distinction is based on whether planning is performed in a centralized or distributed manner. In the former case, the planning responsibility is assigned to a single entity, which produces a plan consisting of actions, each to be delegated to some agent, while in the latter, the responsibility is distributed to the participating agents, each of which plans at a local level, by possibly exchanging information with the others; in this variant, each agent comes up with a local plan, and the execution of all plans must be appropriately coordinated at runtime. Finally, the setting may or may not require privacy-preservation, which refers to the requirement that every agent might decide not to disclose some information (consequently affecting the space of admissible solutions).

.. literalinclude:: ./code_snippets/multi_agent_and_contingent.py
    :lines: 3-41


Contingent Example
--------------------
A contingent planning problem represents an action-based problem in which the exact initial state is not entirely known and some of the actions produce “observations” upon execution. More specifically, some actions can be SensingActions, which indicate which fluents they observe and after the successful execution of such actions, the observed fluents become known to the executor. The inherent non-determinism in the initial state can therefore be “shrinked” by performing suitable SensingActions and a plan is then a strategy that prescribes what to execute based on the past observations.

.. literalinclude:: ./code_snippets/multi_agent_and_contingent.py
    :lines: 44-94


Hierarchical Example
---------------------
A hierarchical planning problem is a problem formulation which extends the Problem object described so far adding support for tasks, methods and decompositions. The general idea is that the planning problem is augmented with high-level tasks that represent abstract operations (e.g. processing an order, going to some distant location) that may require a combination of actions to be achieved. Each high-level task is associated with one or several methods that describe how the task can be decomposed into a set of lower-level tasks and actions.The presence of several methods for a single task represent alternative possibilities of achieving the same operation, among which the planner shall decide. The most important difference between hierarchical and non-hierarchical planning is that in hierarchical planning all actions of the plan must derive from a set of (partially ordered) high-level objective tasks, called the initial task network.

.. literalinclude:: ./code_snippets/hierarchical_problem.py
    :lines: 3-58
