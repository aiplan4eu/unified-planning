This page presents a taxonomy of planning-related concepts that will be considered for the development of the Unified Planning Framework and to classify techniques and resources produced by the project.

(Comment from A. Saffiotti: It may be useful to discuss the link of our work with the many emerging taxonomies and ontologies produced by the EC or by the member states in their attempts to define AI strategies.  For example:
https://publications.jrc.ec.europa.eu/repository/handle/JRC118163 (from the EC JRC, very simple taxonomy on p.11 and link with many keywords on p.16)
https://www.din.de/en/innovation-and-research/artificial-intelligence (from the German government, taxonomy on p.42))

The first item in our taxonomy concerns the characterization of the planning problem characteristics, these define the features used in the description of the planning task.
* **Planning Problem Characterization**
  * **Pure Scheduling** (i.e. no actions to be decided, just sequencing/time assignment)
    * **No**
    * **Yes**
  * **Presence of Time**
    * **No**
    * **Discrete**
    * **Continuous**
  * **Presence of numerical quantities**
    * **No**
    * **Discrete**
    * **Continuous**
  * **Presence of conditional effects**
    * **No**
    * **Yes**
  * **Hierarchical structure**
    * **No**
    * **Yes**
    * **Recursive**
  * **Motion planning**
    * **No**
    * **Topological** (i.e. maps)
    * **Continuous**
  * **Simulated entities**
    * **None**
    * **Entire actions** (i.e. Semantic Attachments)
    * **Simulated resources**
  * **Agents**
    * **Single**
    * **Multiple**
      * **Configuration**
        * **Centralized**
        * **Distributed**
      * **Agent relationship**
        * **Cooperative**
        * **Competitive**
      * **Privacy Preserving**
        * **Yes**
        * **No**
  * **Discrete non-determinism**
    * **No**
    * **Initial-state only**
      * **Qualitative** (e.g. FOND)
      * **Quantitative** (e.g. MDP)
    * **Effects**
      * **Qualitative** (i.e. FOND)
      * **Quantitative** (i.e. MDP)
  * **Continuous non-determinism**
    * **No**
    * **Temporal uncertainty**
      * **Qualitative** (i.e. controllability)
      * **Quantitative** (i.e. probabilities)
    * **Resource uncertainty**
      * **Qualitative** (i.e. controllability)
      * **Quantitative** (i.e. probabilities)
  * **Observability**
    This only makes sens when some kind of non-determinism is considered in the problem
    * **None**
    * **Full**
    * **Partial**
  * **Optimization objectives**
    * **None**
    * **Action Costs**
      * **Positive-only**
        * **Constant**
        * **State-dependent**
      * **General**
        * **Constant**
        * **State-dependent**
    * **Continuous Resource Optimization**
    * **Makespan Optimization**
  * **Optimization Kind**
    * **None**
    * **Satisficing**
    * **Optimal**
    * **Pareto-optimal**

The second item concerns solutions, i.e what the planner/solver generates as output
* **Solutions**
  * **Action Sequence**
  * **Partial-Order Plan**
  * **Simple Temporal Network**
  * **Policy**
  * **Validation error trace**
    If the validation of a plan is failed, the validator returns an execution allowed by the plan that violates some constraint or never reaches the goals
  * **Generalized Plan**

Third item are operations modes, that are ways in which the user can interact with the planner/solver
* **Operation Modes**
  * **One-shot**
    Given a planning problem, find a solution and return it
  * **Single action decision** (e.g. MCTS)
    Only predict the next action to execute
  * **Online/Incremental**
    Resume search after some feedback from execution (i.e. re-plan given some changes in the initial state and/or in the problem formulation)
  * **Mixed initiative**
    Solve the planning problem in interaction with a human
  * **Plan Repair**
    Given a plan that was generated under some assumption, try to repair it when some assumption is broken
  * **Plan Validation**
    Given a problem and a plan, check if the plan is valid for the given problem (for a certain notion of validity e.g. strong validity)
  * **Plan Recognition**
    Given some observations, understand which is the plan followed by an agent
  * **Generalized Planning**
    Given a set of planning problems find a policy/strategy that works for all of them

Methods are algorithms/frameworks used to implement the planner/solver
* **Methods**
  * **Heuristic search**
  * **Reduction to Satisfiability**
  * **MCTS**
  * **Local search**
  * **Symbolic search**
  * **Reinforcement Learning** (This has a [taxonomy](https://spinningup.openai.com/en/latest/spinningup/rl_intro2.html#a-taxonomy-of-rl-algorithms) of its own)
  * **Plan-space planning**
  * **Analytical**
  * **Case-based planning**
  * **Reductions**
  * **Width-based planning**

Use-cases in which the planner solver has been employed
* **Use-Cases**
  * **Underwater Vehicles**
  * **Planning agricultural operations**
  * **Planning for consumer-goods experiments**
  * **Planning for Space**
  * **Autonomous Vehicles Fleet Management**
  * **Indoor Robotics**
  * **Flexible Manufacturing**

Actual tools that implement planning algorithms and operation modes
* **Tools**
  * **Fast Downward**
  * **TFD**
  * **LPG**
  * **ARIES**
  * **Tamer**
  * **FF**
  * **ENHSP**
  * **FMAP**
  * **Scikit-decide**

Several relations are possible!
E.g.:
A Planning Problem emerges from a Use-Case and is solved by a Tool configured with a certain Operation Mode that implements a Method that generates a certain Solution
