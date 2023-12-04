# Planning for Logistics Automation: Behavior Tree Testing

## Context

Robots behavior at Magazino is designed using behavior trees which give an
intuitive idea of how a system will behave depending on action success or
failure. However, actions in behavior trees often have hidden dependencies that
are difficult to track. Attempting to execute an action when its data
requirements are not satisfied usually leads to system down time. It is
therefore essential to catch these dependency issues before the system is
deployed.

In this use case, we employ planning to find execution traces in behavior trees
that violate data assumptions. If a plan is found, it indicates a way to execute
the behavior tree that would crash the system.

- For details see our conference paper [1] 
- This use case is also documents on the AI on Demand platform [2]
- A video overview can be found on YouTube [3]

## Planning Problem Description

Given a behavior tree with data dependencies, we convert it to a state that
describes the structure of the tree (node types, children) and its initial
execution state (no node has been visited). Then, for each data dependency we
create a goal to reach the corresponding action without satisfying the data
dependency. This can be modeled as a classical planning problem.

## Modeling in UP

The main challenge was to find a good representation of the behavior tree and
its state as the state of a planning problem.

The state includes:
- The state of each node (success, failure, running, pending)
- The currently active child of control flow nodes
- Indexed children of control flow nodes
- Number of children to allow checking when we are done

Operators represent the advancement of the tree during execution:

- Control node operators are initialized and select the next child, succeed, or
  fail based on the outcome of their child trees.
- Task (actions) node can succeed or fail and make data available.

## Operation Modes and Integration Aspects

- Operation mode: One-shot planning

### Domain encoder 

The domain is defined as the set of operators needed to specify the possible
executions of each node type.

### Problem encoder 

Our behavior trees are defined in a proprietary JSON format, that specifies both
the structure of the tree (parent / children), the type of the nodes and the
inputs / outputs of each node.

### Solution decoder 

For visualisation purposes, the planner result is parsed and a human-friendly
message is produced (showing the execution sequence and the return values of the
nodes being executed that lead to the violation of the constraints).

## Lessons Learned

- Represent numbers with symbols (e.g., `n0`, `n1`) to avoid issues with
  planning engines that use PDDL. In this case, the state also must include any
  required relations between these number-symbols (e.g., successor-of).
  
- Pruning: for large trees, the state becomes very large. However, for a given
  data dependency we can prune the tree by removing all sub-trees that do not
  contain relevant nodes (i.e., nodes that produce or consume the required
  data). This significantly improved performance of the approach (see [1] for
  details).

## Resources

[1] Köckemann, U., Calisi, D., Gemignani, G., Renoux, J., & Saffiotti,
    A. (2023). Planning for Automated Testing of Implicit Constraints in
    Behavior Trees. Proceedings of the International Conference on Automated
    Planning and Scheduling, 33(1),
    649-658. https://doi.org/10.1609/icaps.v33i1.27247
[2] AI on Demand use case: https://www.ai4europe.eu/business-and-industry/case-studies/planning-logistics-automation
[3] Overview video: https://www.youtube.com/watch?v=2wfQFq5DrtQ

