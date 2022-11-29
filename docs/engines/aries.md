# Aries

[Aries](https://github.com/plaans/aries) is an automated planner targeting hierarchical and temporal problems. The objective of Aries is to model and solve hierarchical problems with advanced temporal features and optimization metrics. It relies on the proximity of these with scheduling problems to propose a compilation into a constraint satisfaction formalism. Solving exploits a custom combinatorial solver that leverages the concept of optional variables in scheduling solvers as well as the clause learning mechanisms of SAT solvers.

## Status

Integration into the AIPlan4EU project is ongoing, synchronized with the effort for augmenting the modeling capabilities of the unified-planning library to model hierarchical problems.

## Planning approaches of UP supported

- *Problem kind*: Hierarchical planning
- *Operative mode*: One shot planning


## Installation

After cloning this repository run `pip install up-aries`.
Note that the integration is still incomplete and is in particular missing the full support of hierarchical problems in protobuf from the unified-planning library.

