# Surveillance and Inspection Drones

## Context

This use case centers on the deployment of a decision-making system for the purpose of conducting drone surveys and inspections. It encompasses two distinct scenarios in which one or more drones, each equipped with cameras, are employed to survey an area, identify objects of interest, and closely inspect said objects, all within an energy-constrained context. Comprehensive information pertaining to this use case is available on the [AIOnDemand](https://www.ai4europe.eu/business-and-industry/case-studies/drones-surveillance-and-inspection) platform.


## Planning Problem Description

The primary objective of this use case is to establish a system that facilitates the following functionalities:

1. Surveying a specified area to pinpoint objects of interest.
2. Elaborating plans for conducting in-depth inspections of these objects of interest, including coordination among multiple available drones.
3. Facilitating the return of drones to the base for battery replacement in instances of low power, enabling the continuation of operations.

To accomplish this, the use case factors in various metrics such as drone battery consumption, the distance between target objects to be inspected, the time required for inspecting a single target, and the number of drones employed for inspection. These metrics serve as the foundation for the model used in this use case.


## Modeling in UP

The success of this use case depends on temporal planning for optimization, intertwined with numerical constraints. To address this complex scenario, numerical fluents are configured to internally assess constraints during both the planning and execution phases.

For example, the critical consideration of drone battery consumption necessitates an emergent response. If the fluent pertaining to battery levels fails during execution, the drone initiates an emergency protocol involving a safe landing and subsequent battery replacement before recommencing its mission. Another instance involves the optimization of the distance between target objects following the initial survey. The problem is structured such that, after localizing the expected number of target objects, a specific rule is applied to establish the optimal order for inspecting these objects, thereby enhancing efficiency in terms of time consumption.

The experiments conducted encompass two scenarios: one with a single drone and another involving two drones. The chosen planner for these experiments is Aries. These experiments take place in both simulated and real-world environments within a controlled setting. Incremental variations are incorporated to explore diverse approaches used to this use case, as outlined in the table below.


| Variation | Description |
|-----------|-------------|
| Sequential Planning |	The problem is modeled with known locations for n targets requiring inspection. |
| Sequential Planning with replanning |	The problem is modeled with known locations for n targets and executed in a simulation, with battery consumption interruptions prompting replanning based on the current state of the experiment. |
| Temporal Planning | The initial problem version is modeled with known target locations (n) and is executed with time constraints. Subsequently, a second version localizes the plates through survey actions, redefines the problem, extends the plan for the localized targets, and executes them. |
| Parallel Plan Generation | Building upon the previous variation, this experiment extends to parallel plan generation for scenarios involving multiple drones, each independently inspecting target objects. |
	

## Operation Modes and Integration Aspects


The model definition enables the system to generate plans that encompass surveying the area of interest, searching for specific objects (colored plates in this instance), object localization, and conducting detailed inspections of individual objects. The operation mode employed for this use case is One Shot Planning, and the Aries Planning Engine is used to devise optimal plans for the various experiments.

The drones feature a Python interface that interfaces with the GenoM3 framework and its functional components, thereby gaining access to plan execution services. The Python interface, known as "py-genomix," and the plans generated using UP are directly mapped using a bridge functionality. This bridge facilitates the conversion of plans into executable services by means of dependency graphs. The integration of the bridge is achieved through the Embedded Systems Bridge (ESB), a TSB functionality that permits the integration of UP Services into framework-agnostic applications.

## Lessons Learned

Through the exploration of the various experimental stages and variations outlined above, we have learned many key lessons in the context of modeling and planning. A few of them are:

1. **Efficient Model Definition for Expedited Planning**: Expressing a straightforward and simplified model definition can significantly speedup the planning process. By reducing the complexity of the model, planners can generate plans more swiftly. This allows for real-time or near-real-time decision-making. It has been essential to strike a balance between including essential details and minimizing unnecessary intricacies in the model.
2. **Critical Assessment of Model Definition**: Choices related to the implementation of instantaneous or durative actions can have a substantial impact on the time required to devise a solution. The tradeoff has been to balance the need for temporal accuracy of the problem with the computational cost when modeling the use case.
3. **Importance of Planning Engine Selection**: The selection of an appropriate planning engine has played an important role in addressing the complexity of the problem. The choice have been made based on the evaluation of the specific requirements, constraints, and other relevant factors.

## Resources

- [Experiment Landing Page](https://www.ai4europe.eu/business-and-industry/case-studies/drones-surveillance-and-inspection)
- A Closed-Loop Framework-Independent Bridge: from AIPlan4EU’s Unified Planning Platform to Embedded Systems. [Paper](https://icaps23.icaps-conference.org/program/workshops/planrob/PlanRob-23_paper_8.pdf)
- GenoM3 Templates: from Middleware Independence to Formal Models Synthesis. [Paper](https://arxiv.org/abs/1807.10154)
- Drone Experiment. [Github](https://github.com/lerema/genom3-experiment)
- Embedded Systems Bridge. [Github](https://github.com/aiplan4eu/embedded-systems-bridge)