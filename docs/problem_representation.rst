Problem Representation
======================

The main functionality offered by the library concerns the specification of a planning problem. In particular, the UP library supports the following classes of planning problems: Classical, Numeric, Temporal, Scheduling, Multi-Agent, Hierarchical, Task and Motion Planning (TAMP) and Conformant. For each of these, we provide a short description, a syntax overview and a link to a detailed discussion.

One of the key element of the problem specifications is the ProblemKind class (automatically computed by all the planning problems classes via the kind property), which  is a collection of flags, documented in the table below, that identifies the modeling features used in any problem specification, so that the library can determine the applicability of each engine for a certain query.


Problem Kinds
-------------

.. list-table::
   :header-rows: 1

   * - Features
     - ProblemKind flag
     - Description
   * - PROBLEM_CLASS
     - ACTION_BASED
     - The problem is an action-based classical, numeric or temporal planning problem.
   * -
     - HIERARCHICAL
     - The problem is an action-based problem with hierarchical features.
   * -
     - CONTINGENT
     - The problem is an action-based problem with non-deterministic initial state and observation (called sensing) actions.
   * -
     - ACTION_BASED_MULTI_AGENT
     - The problem is an action-based problem where action and fluents can be divided in more than one agent.
   * -
     - SCHEDULING
     - The problem is a scheduling problem where a known set of activities need to be scheduled in time.
   * -
     - TAMP
     - The problem is a *Task and Motion Planning* problem.
   * - PROBLEM_TYPE
     - SIMPLE_NUMERIC_PLANNING
     - The numeric part of the problem exhibits only linear numeric conditions of the form f(X) {>=,>,=} 0 where f(X) is a linear expression constructed over numeric variables X. Moreover, effects are restricted to increase and decrease operations by a constant. For instance x+=k with k constant is allowed, while x+=y with y variable is not.
   * -
     - GENERAL_NUMERIC_PLANNING
     - The problem uses numeric planning using unrestricted arithmetic.
   * - TIME
     - CONTINUOUS_TIME
     - The temporal planning problem is defined over a continuous time model.
   * -
     - DISCRETE_TIME
     - The temporal planning problem is defined over a discrete time model.
   * -
     - INTERMEDIATE_CONDITIONS_AND_EFFECTS
     - The temporal planning problem uses either conditions or effects happening during an action (not just at the beginning or end of the interval).
   * -
     - EXTERNAL_CONDITIONS_AND_EFFECTS
     - The temporal planning problem uses either conditions or effects happening outside the interval of an action (e.g. 10 seconds after the end of the action).
   * -
     - TIMED_EFFECTS
     - The temporal planning problem has effects scheduled at absolute times (e.g., Timed Initial Literals in PDDL).
   * -
     - TIMED_GOALS
     - The temporal planning problem uses goals required to be true at times different from the end of the plan.
   * -
     - DURATION_INEQUALITIES
     - The temporal planning problem has at least one action with non-constant duration (and instead uses a lower bound different than upper bound).
   * -
     - SELF_OVERLAPPING
     - The temporal planning problem allows actions self overlapping.
   * - EXPRESSION_DURATION
     - STATIC_FLUENTS_IN_DURATION
     - The duration of at least one action uses static fluents (that may never change).
   * -
     - FLUENTS_IN_DURATION
     - The duration of at least one action is specified using non-static fluents (that might change over the course of a plan).
   * -
     - INT_TYPE_DURATIONS
     - The duration of at least one action is of int type; added in ProblemKind's version 2.
   * -
     - REAL_TYPE_DURATIONS
     - The duration of at least one action is of real type; added in ProblemKind's version 2.
   * - NUMBERS
     - CONTINUOUS_NUMBERS
     - The problem uses numbers ranging over continuous domains (e.g. reals); deprecated in ProblemKind's version 2.
   * -
     - DISCRETE_NUMBERS
     - The problem uses numbers ranging over discrete domains (e.g. integers); deprecated in ProblemKind's version 2.
   * -
     - BOUNDED_TYPES
     - The problem uses bounded-domain numbers.
   * - CONDITIONS_KIND
     - NEGATIVE_CONDITIONS
     - The problem has at least one condition using the negation Boolean operator.
   * -
     - DISJUNCTIVE_CONDITIONS
     - The problem has at least one condition using the Boolean “or” operator.
   * -
     - EQUALITIES
     - The problem has at least one condition using the equality predicate (usually over two finite-domain variables or object fluents).
   * -
     - EXISTENTIAL_CONDITIONS
     - The problem has at least a condition using the “exists” quantifier over problem objects.
   * -
     - UNIVERSAL_CONDITIONS
     - The problem has at least a condition using the “forall” quantifier over problem objects.
   * - EFFECTS_KIND
     - CONDITIONAL_EFFECTS
     - At least one effect has a condition.
   * -
     - FORALL_EFFECTS
     - At least one effect uses the “forall” quantifier over problem objects.
   * -
     - INCREASE_EFFECTS
     - At least one effect uses the numeric increment operator.
   * -
     - DECREASE_EFFECTS
     - At least one effect uses the numeric decrement operator.
   * -
     - STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS
     - At least one effect uses a static fluent in the expression of a boolean assignment.
   * -
     - STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS
     - At least one effect uses a static fluent in the expression of a numeric assignment.
   * -
     - STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS
     - At least one effect uses a static fluent in the expression of a object assignment.
   * -
     - FLUENTS_IN_BOOLEAN_ASSIGNMENTS
     - At least one effect uses a fluent in the expression of a boolean assignment.
   * -
     - FLUENTS_IN_NUMERIC_ASSIGNMENTS
     - At least one effect uses a fluent in the expression of a numeric assignment.
   * -
     - FLUENTS_IN_OBJECT_ASSIGNMENTS
     - At least one effect uses a fluent in the expression of a object assignment.
   * - TYPING
     - FLAT_TYPING
     - The problem uses user-defined types, but no type inherits from another.
   * -
     - HIERARCHICAL_TYPING
     - At least one user-defined type in the problem inherits from another type.
   * - PARAMETERS
     - BOOL_FLUENT_PARAMETERS
     - At least one fluent has a parameter of boolean type.
   * -
     - BOUNDED_INT_FLUENT_PARAMETERS
     - At least one fluent has a parameter of bounded integer type. Note that unbounded ints are not allowed in fluent parameters).
   * -
     - BOOL_ACTION_PARAMETERS
     - At least one action has a parameter of boolean type.
   * -
     - BOUNDED_INT_ACTION_PARAMETERS
     - At least one action has a parameter of bounded integer type.
   * -
     - UNBOUNDED_INT_ACTION_PARAMETERS
     - At least one action has a parameter of unbounded integer type.
   * -
     - REAL_ACTION_PARAMETERS
     - At least one action has a parameter of real type.
   * - FLUENTS_TYPE
     - NUMERIC_FLUENTS
     - The problem has at least one fluent of numeric type; deprecated in ProblemKind's version 2.
   * -
     - INT_FLUENTS
     - The problem has at least one fluent of integer type; added in ProblemKind's version 2.
   * -
     - REAL_FLUENTS
     - The problem has at least one fluent of real type; added in ProblemKind's version 2.
   * -
     - OBJECT_FLUENTS
     - The problem has at least one finite-domain fluent (fluent of user-defined type).
   * - QUALITY_METRICS
     - ACTIONS_COST
     - The problem has a quality metric associating a cost to each action and requiring to minimize the total cost of actions used in a plan.
   * -
     - FINAL_VALUE
     - The problem has a quality metric requiring to optimize the value of a numeric expression in the final state of a plan.
   * -
     - MAKESPAN
     - The problem has a quality metric requiring to minimize the time at which the last action in the plan is terminated.
   * -
     - PLAN_LENGTH
     - The problem has a quality metric requiring to minimize the number of actions used in a plan.
   * -
     - OVERSUBSCRIPTION
     - The problem has a quality metric associating a positive value to some optional goal and the objective is to find the plan of maximal value.
   * -
     - TEMPORAL_OVERSUBSCRIPTION
     - The problem has a quality metric associating a positive value to some optional timed goal and the objective is to find the plan of maximal value.
   * - ACTIONS_COST_KIND
     - STATIC_FLUENTS_IN_ACTIONS_COST
     - There is at least a static fluent in the Action's cost (that may never change).
   * -
     - FLUENTS_IN_ACTIONS_COST
     - There is at least a non-static fluent in the Action's cost (that might change over the course of a plan).
   * -
     - INT_NUMBERS_IN_ACTIONS_COST
     - There is at least one Action's cost in the ACTIONS_COST that is of int type; added in ProblemKind's version 2.
   * -
     - REAL_NUMBERS_IN_ACTIONS_COST
     - There is at least one Action's cost in the ACTIONS_COST that is of real type; added in ProblemKind's version 2.
   * - OVERSUBSCRIPTION_KIND
     - INT_NUMBERS_IN_OVERSUBSCRIPTION
     - There is at least one gain in the Oversubscription (or Temporal Oversubscription) metric that is of int type; added in ProblemKind's version 2.
   * -
     - REAL_NUMBERS_IN_OVERSUBSCRIPTION
     - There is at least one gain in the Oversubscription (or Temporal Oversubscription) metric that is of real type; added in ProblemKind's version 2.
   * - SIMULATED_ENTITIES
     - SIMULATED_EFFECTS
     - The problem uses at least one simulated effect.
   * - CONSTRAINTS_KIND
     - TRAJECTORY_CONSTRAINTS
     - The problem uses at least one LTL trajectory constraint.
   * -
     - STATE_INVARIANTS
     - The problem uses at least one state invariants.
   * - HIERARCHICAL
     - METHOD_PRECONDITIONS
     - At least one method of the problem contains preconditions (i.e. statement that must hold at the start of the method.
   * -
     - TASK_NETWORK_CONSTRAINTS
     - At least one task network (initial task network or method) contains a constraint: statement over static functions that is required to hold for the task network to appear in the solution.
   * -
     - INITIAL_TASK_NETWORK_VARIABLES
     - The initial task network contains at least one existentially qualified variable.
   * -
     - TASK_ORDER_TOTAL
     - In all task networks, all temporal constraints are simple precedence constraints and induce a total order over all subtasks.
   * -
     - TASK_ORDER_PARTIAL
     - In all task networks, all temporal constraints are simple precedence constraints. At least one task network is not totally ordered.
   * -
     - TASK_ORDER_TEMPORAL
     - Task networks may be subject to arbitrary temporal constraints (e.g. simple temporal constraints or disjunctive temporal constraints).
   * - MULTI_AGENT
     - AGENT_SPECIFIC_PRIVATE_GOAL
     - At least one agent has at least one private specific goal. Private-specific goals are; individual agent goals (not coalition goals) unknown to other agents.
   * -
     - AGENT_SPECIFIC_PUBLIC_GOAL
     - At least one agent has at least one public-specific goal. Public-specific goals are; individual agent goals (not coalition goals) known to other agents.

The API provides classes and functions to populate a Problem object with the fluents, actions, initial states and goal specifications constituting the planning problem specification.
The functionalities for creating model objects and to manipulate them are collected in the unified_planning.model package of the library.
In all the examples below all the shortcuts must be imported, with the command:

``from unified_planning.shortcuts import *``





Classical and Numeric Planning
------------------------------
The following example shows a simple robotic planning problem modeling a robot moving between locations while consuming battery. The example shows the basic functionalities and objects needed to declare the problem specification. A more detailed presentation of the different objects is available on the `Google Colab <https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/docs/notebooks/01-basic-example.ipynb>`_ Python notebook where we document and explain all the different classes and their semantics.

.. literalinclude:: ./code_snippets/robot_battery.py
    :lines: 3-38


In the current version, the Unified-Planning library allows the specification of classical, numerical and temporal planning problems. In order to support the latitude expressiveness levels we have operators for arithmetic such as plus minus times and division and specific temporal operators to attach conditions and effects to specific timings within the duration of an action. The library :ref:`documentation <api-reference>` provides examples and describes the use of these functionalities.


Temporal Planning
-----------------

Temporal planning is the problem of finding a plan for a planning problem involving durative actions and/or temporal constraints.
This means that it is possible to model actions having:

* duration constrained by a (possibly state-based) lower and and upper bound
* conditions or effects expressed at specific instant of the action, in particular at times start+delay or end+delay, where start refers to the starting time of the action, end to the ending time and delay is a real constant (positive or negative).
* durative conditions to be maintained within sub-intervals, delimited by the same time-point used for instantaneous conditions.

.. literalinclude:: ./code_snippets/temporal_and_scheduling.py
    :lines: 3-44


Hierarchical Planning
---------------------

A *hierarchical planning* problem is a problem formulation which extends the Problem object described so far adding support for tasks, methods and decompositions. The general idea is that the planning problem is augmented with high-level tasks that represent abstract operations (e.g. processing an order, going to some distant location) that may require a combination of actions to be achieved. Each high-level task is associated with one or several methods that describe how the task can be decomposed into a set of lower-level tasks and actions.The presence of several methods for a single task represent alternative possibilities of achieving the same operation, among which the planner shall decide. The most important difference between hierarchical and non-hierarchical planning is that in hierarchical planning all actions of the plan must derive from a set of (partially ordered) high-level objective tasks, called the initial task network.
`[Detailed presentation 🔗] <notebooks/07-hierarchical-planning.html>`__

.. literalinclude:: ./code_snippets/hierarchical_problem.py
    :lines: 3-58
    :caption: Syntax Overview


Multi-Agent Planning
--------------------

Multi-agent Planning lifts planning to a context where many agents operate in a common environment, each with its own view of the domain. The objective is to produce a set of plans, one for each agent, which allows the agents to achieve their goals.
The problem comes in several variants, depending on various features. Specifically, multi-agent planning can be competitive, meaning that the agents compete against each other in order to achieve their goal, or cooperative, which refers to the case where the agents collaborate towards a common goal. Another distinction is based on whether planning is performed in a centralized or distributed manner. In the former case, the planning responsibility is assigned to a single entity, which produces a plan consisting of actions, each to be delegated to some agent, while in the latter, the responsibility is distributed to the participating agents, each of which plans at a local level, by possibly exchanging information with the others; in this variant, each agent comes up with a local plan, and the execution of all plans must be appropriately coordinated at runtime. Finally, the setting may or may not require privacy-preservation, which refers to the requirement that every agent might decide not to disclose some information (consequently affecting the space of admissible solutions).
`[Detailed presentation 🔗] <notebooks/10-multiagent-planning.html>`__

.. literalinclude:: ./code_snippets/multi_agent_and_contingent.py
    :lines: 3-41


Contingent Planning
-------------------
A contingent planning problem represents an action-based problem in which the exact initial state is not entirely known and some of the actions produce “observations” upon execution. More specifically, some actions can be SensingActions, which indicate which fluents they observe and after the successful execution of such actions, the observed fluents become known to the executor. The inherent non-determinism in the initial state can therefore be “shrinked” by performing suitable SensingActions and a plan is then a strategy that prescribes what to execute based on the past observations.

.. literalinclude:: ./code_snippets/multi_agent_and_contingent.py
    :lines: 44-95


Scheduling
----------

Scheduling is a restricted form of temporal planning where the set of actions (usually called activities) are known in advance and the problem consists in deciding the timing and parameters of the activities.
Generally, scheduled problems involve resources and constraints that define the feasible space of solutions.
Since scheduling problems are very common and scheduling as a computer science problem belongs to a simpler complexity class (NP) with respect to temporal planning (PSPACE, under suitable assumptions) we created a dedicated representation for scheduling problems.
We can represent a generic scheduling problem using the SchedulingProblem class as shown in the example below.
`[Detailed presentation 🔗]  <notebooks/13-scheduling.html>`__

.. literalinclude:: ./code_snippets/temporal_and_scheduling.py
    :lines: 47-67
    :caption: Syntax Overview

