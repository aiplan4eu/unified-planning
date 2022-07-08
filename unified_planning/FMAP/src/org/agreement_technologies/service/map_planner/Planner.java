/* 
 * Copyright (C) 2017 Universitat Politècnica de València
 *
 * This file is part of FMAP.
 *
 * FMAP is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * FMAP is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with FMAP. If not, see <http://www.gnu.org/licenses/>.
 */
package org.agreement_technologies.service.map_planner;

import java.util.ArrayList;
import java.util.Hashtable;
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_communication.Message;
import org.agreement_technologies.common.map_communication.MessageFilter;
import org.agreement_technologies.common.map_communication.PlanningAgentListener;
import org.agreement_technologies.common.map_heuristic.Heuristic;
import org.agreement_technologies.common.map_negotiation.NegotiationFactory;
import org.agreement_technologies.common.map_negotiation.PlanSelection;
import org.agreement_technologies.common.map_planner.CausalLink;
import org.agreement_technologies.common.map_planner.Condition;
import org.agreement_technologies.common.map_planner.ExtendedPlanner;
import org.agreement_technologies.common.map_planner.IPlan;
import org.agreement_technologies.common.map_planner.OpenCondition;
import org.agreement_technologies.common.map_planner.Ordering;
import org.agreement_technologies.common.map_planner.POPSearchMethod;
import org.agreement_technologies.common.map_planner.Plan;
import org.agreement_technologies.common.map_planner.Step;
import org.agreement_technologies.service.tools.CustomArrayList;

/**
 * Planner abstract class: includes the basic planning methods used in POP and
 * POPMultiThread.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public abstract class Planner implements ExtendedPlanner {

    static final int EQUAL = 1;         // Equal condition
    static final int DISTINCT = 2;      // Distinct condition
    static final int NO_TIMEOUT = -1;   // Planning without timeout
    static final int IDA_SEARCH = 1;    // Code for IDA Search
    static final int A_SEARCH = 2;      // Code for A* Search

    protected POPIncrementalPlan basePlan;              // Base plan
    protected PlannerFactoryImp configuration;          // Planner setup
    protected Heuristic heuristic;                      // Heuristic function
    protected AgentCommunication comm;                  // Communication utility
    protected StateMemoization memoization;             // Memoization to avoid plan repetitions
    protected POPInternalSearchTree internalSearchTree; // Internal search tree to build successor plans
    protected POPSearchMethod searchTree;               // Search tree for solving the planning task
    protected SolutionChecker solutionChecker;          // Solution checker
    protected PlanSelection planSelection;              // Plan selector for choosing the next base plan
    protected ArrayList<POPInternalPlan> successors;    // List of successor plans for the base plan
    protected String myAgent;                           // Name of this agent
    protected POPInternalPlan currentInternal;          // Current internal plan
    protected POPIncrementalPlan initialIncrementalPlan;// Initial plan
    protected POPInternalPlan initialInternalPlan;      // Initial internal plan
    protected int expandedNodes;                        // Number of expanded nodes
    protected PlanningAgentListener agentListener;      // Agent listener (GUI for feedback)
    protected OrderingManager matrix;                   // Orderings matrix
    protected Hashtable<Integer, Integer> lastValues;   // For each variable, last value achieved in the base plan
    protected Hashtable<String, Boolean> hashEffects;   // Stores the effects of the steps (as strings) of the base plan
    protected Step initialStep;                         // Initial step
    protected Step finalStep;                           // Final step
    protected POPIncrementalPlan[] antecessors;         // Ancestor plans of the base plan
    protected ArrayList<OpenCondition> openConditions;  // List of open conditions in the base plan
    protected CustomArrayList<CausalLink> totalCausalLinks; // Full list of causal links in the base plan
    protected int numCausalLinks;                           // Number of causal links
    protected boolean modifiedCausalLinks;                  // Indicates if the list of causal links has been modified
    protected CustomArrayList<Ordering> totalOrderings;     // Full list of orderings in the base plan
    protected int numOrderings;                             // Number of orderings
    protected boolean modifiedOrderings;                    // Indicates if the list of orderings has been modified
    protected int planningStep;                             // Number of search iterations (expanded plans)
    protected long planTime = 0;                            // Planning time in milliseconds
    protected long evaluationTime = 0;                      // Plan evaluation time in milliseconds
    protected long communicationTime = 0;                   // Communication time in milliseconds
    protected ExtendedPlanner parent;                       // Internal planner, for computing successors
    protected ArrayList<ArrayList<ProposalToSend>> proposalsToSend; // For each agent, list of plan proposals to send
    protected MessageFilterProposals proposalsFilter;       // Filter to receive plan proposals from other agents
    protected MessageFilterAdjustment adjustmentFilter;     // Filter to receive heuristic value adjustments from other agents
    private int discarded;                              // Number of rejected plans
    private Hashtable<Integer, Boolean> hazardousVars;  // Variables which are updated in the actions but not required in their preconditions
    private HeuristicAdjustment hAdjustment;            // Message for heuristic adjustments
    private NewBasePlanMessage newBasePlanMsg;          // Message to communicate the selection of a nes base plan
    private final ArrayList<InternalProposal> allProposals; // List of all plan proposals from all the agents

    /**
     * Creates a new planner.
     *
     * @param comm Communication utility
     * @since 1.0
     */
    public Planner(AgentCommunication comm) {
        this.comm = comm;
        proposalsToSend = new ArrayList<>(comm
                .getOtherAgents().size());
        for (int i = 0; i < comm.getOtherAgents().size(); i++) {
            proposalsToSend.add(new ArrayList<ProposalToSend>());
        }
        proposalsFilter = new MessageFilterProposals();
        adjustmentFilter = new MessageFilterAdjustment();
        newBasePlanMsg = new NewBasePlanMessage();
        allProposals = new ArrayList<>();
    }

    /**
     * Gets the list of predecessor plans of the current base plan in the search
     * tree.
     *
     * @return Array of predecessor plans of the current base plan
     * @since 1.0
     */
    @Override
    public POPIncrementalPlan[] getAntecessors() {
        return antecessors;
    }

    /**
     * Gets the full list of causal links in the base plan.
     *
     * @return List of causal links in the base plan
     * @since 1.0
     */
    @Override
    public CustomArrayList<CausalLink> getTotalCausalLinks() {
        return totalCausalLinks;
    }

    /**
     * Gets the full list of orderings in the base plan.
     *
     * @return List of orderings in the base plan
     * @since 1.0
     */
    @Override
    public CustomArrayList<Ordering> getTotalOrderings() {
        return totalOrderings;
    }

    /**
     * Gets the initial step of the base plan.
     *
     * @return Initial step
     * @since 1.0
     */
    @Override
    public Step getInitialStep() {
        return initialStep;
    }

    /**
     * Gets the final step of the base plan.
     *
     * @return Final step
     * @since 1.0
     */
    @Override
    public Step getFinalStep() {
        return finalStep;
    }

    /**
     * Sets the number of causal links in the current plan.
     *
     * @param n Number of causal links
     * @since 1.0
     */
    @Override
    public void setNumCausalLinks(int n) {
        numCausalLinks = n;
    }

    /**
     * Sets if new causal links have been added to build the successor plan.
     *
     * @param m <code>true</code>, if new causal links have been added to build
     * the successor plan. <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public void setModifiedCausalLinks(boolean m) {
        modifiedCausalLinks = m;
    }

    /**
     * Gets the number of causal links in the current plan.
     *
     * @return Number of causal links
     * @since 1.0
     */
    @Override
    public int getNumCausalLinks() {
        return numCausalLinks;
    }

    /**
     * Checks if new causal links have been added to build the successor plan.
     *
     * @return <code>true</code>, if new causal links have been added to build
     * the successor plan. <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean getModifiedCausalLinks() {
        return modifiedCausalLinks;
    }

    /**
     * Sets the number of orderings in the current plan.
     *
     * @param n Number of orderings
     * @since 1.0
     */
    @Override
    public void setNumOrderings(int n) {
        numOrderings = n;
    }

    /**
     * Sets if new orderings have been added to build the successor plan.
     *
     * @param m <code>true</code>, if new orderings have been added to build the
     * successor plan. <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public void setModifiedOrderings(boolean m) {
        modifiedOrderings = m;
    }

    /**
     * Checks if new orderings have been added to build the successor plan.
     *
     * @return <code>true</code>, if new orderings have been added to build the
     * successor plan. <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean getModifiedOrderings() {
        return modifiedOrderings;
    }

    /**
     * Adds a new causal link to the current plan.
     *
     * @param cl New causal link
     * @since 1.0
     */
    @Override
    public void addCausalLink(CausalLink cl) {
        getTotalCausalLinks().add(cl);
        if (!getModifiedCausalLinks()) {
            setModifiedCausalLinks(true);
        }
    }

    /**
     * Adds a new ordering link to the current plan.
     *
     * @param o New ordering
     * @since 1.0
     */
    @Override
    public void addOrdering(Ordering cl) {
        totalOrderings.add(cl);
        if (!modifiedOrderings) {
            modifiedOrderings = true;
        }
    }

    /**
     * Retrieves the number of planning iterations executed to find a solution
     * plan.
     *
     * @return Planning iterations
     * @since 1.0
     */
    @Override
    public int getIterations() {
        return this.planningStep;
    }

    /**
     * Computes a solution plan.
     *
     * @param start System time at start
     * @return Solution plan
     * @since 1.0
     */
    @Override
    public Plan computePlan(long start) {
        long t1;
        planningStep = 1;
        Plan solution = null;
        ArrayList<IPlan> proposals;
        int solutions = 0;
        MetricChecker metricChecker = new MetricChecker(comm);

        if (this.planningStep == 1) {
            discarded = 0;
        }

        openConditions = new ArrayList<>();

        for (OpenCondition oc : this.initialInternalPlan.getPreconditions()) {
            openConditions.add(oc);
        }
        basePlan = (POPIncrementalPlan) searchTree.checkNextPlan();

        if (solutionChecker.isSolution(basePlan, configuration)) {
            if (agentListener != null) {
                this.agentListener.trace(1, "Solution found");
            }
            return basePlan;
        }
        if (agentListener != null) {
            agentListener.newPlan(searchTree.checkNextPlan(), configuration);
        }
        boolean adjustHLandStage = heuristic.requiresHLandStage();

        while (solution == null) {
            if (agentListener != null) {
                this.agentListener.trace(0, "Planning step: " + planningStep);
            }

            // Plan selection stage
            t1 = System.currentTimeMillis();
            basePlan = selectNextPlan(adjustHLandStage);
            this.communicationTime = this.communicationTime
                    + (System.currentTimeMillis() - t1);

            if (basePlan == null) {
                break; // No solution
            }
            if (agentListener != null) {
                this.agentListener.trace(1,
                        "Plan " + basePlan.getName() + " (h=" + basePlan.getH()
                        + ", hL=" + basePlan.getHLan() + ") selected");
            } else if (comm.batonAgent()) {
                System.out.println("; Hdtg = " + basePlan.getH() + ", Hlan = " + basePlan.getHLan());
            }

            this.setAntecessors(basePlan);
            initialInternalPlan.setNumSteps(antecessors.length);
            basePlan.calculateCausalLinks();
            basePlan.calculateOrderings();

            t1 = System.currentTimeMillis();
            proposals = computeSuccessors(initialInternalPlan);

            this.planTime = this.planTime + (System.currentTimeMillis() - t1);

            solution = sendProposals(proposals, basePlan, adjustHLandStage);
            planningStep++;

            // Check if the solution plan found meets the preference thresholds
            if (solution != null) {
                if (!this.solutionChecker
                        .isSolution((POPIncrementalPlan) solution, configuration)) {
                    solution = null;
                }
            }
            if (agentListener != null && solution != null) {
                if (metricChecker.isBestSolution(solution, configuration
                        .getNegotiationFactory().getNegotiationType())) {
                    // Print the plan only if it improves the average metric
                    printStatistics(solution, metricChecker);
                }
                solutions++;
            }
        }

        if (this.comm.getAgentIndex(myAgent) == 1) {
            //System.out.println("\nCoDMAP Distributed format");
            //System.out.println("-------------------------");
            System.out.println("\n; Solution plan - CoDMAP Distributed format");
            System.out.println("; -----------------------------------------");
            for (int i = 0; i < comm.getAgentList().size(); i++) {
                //System.out.println("; Agent " + comm.getAgentList().get(i));
                solution.printPlan(Plan.CoDMAP_DISTRIBUTED, comm.getAgentList().get(i), comm.getAgentList());
            }
            /*System.out.println("\nCoDMAP Centralized format");
            System.out.println("-------------------------");
            solution.printPlan(Plan.CoDMAP_CENTRALIZED, myAgent, comm.getAgentList());
            System.out.println("\nRegular format");
            System.out.println("--------------");
            solution.printPlan(Plan.REGULAR, myAgent, comm.getAgentList());
            System.out.println("\n");*/
        }

        return solution;
    }

    /**
     * Gets the next base plan.
     *
     * @param adjustHLandStage Indicates if a stage to adjust the landmarks
     * heuristic values of the successor plans is needed
     * @return Next base plan
     * @since 1.0
     */
    private POPIncrementalPlan selectNextPlan(boolean adjustHLandStage) {
        if (comm.numAgents() == 1) {
            return (POPIncrementalPlan) searchTree.getNextPlan();
        }
        POPIncrementalPlan plan;
        if (comm.batonAgent()) { // Baton agent
            if (!adjustHLandStage) {
                for (InternalProposal p : allProposals) {
                    if (!p.plan.isSolution()) {
                        searchTree.addPlan(p.plan);
                    }
                }
            }
            plan = (POPIncrementalPlan) searchTree.getNextPlan();
            if (plan != null) {
                newBasePlanMsg.setName(plan.getName());
            } else {
                newBasePlanMsg.setName(AgentCommunication.NO_SOLUTION_MESSAGE);
            }
            //System.out.println("Send base plan: " + newBasePlanMsg);
            comm.sendMessage(newBasePlanMsg, true);
        } else { // Non-baton agent
            newBasePlanMsg = (NewBasePlanMessage) comm.receiveMessage(comm.getBatonAgent(), true);
            //System.out.println(comm.getThisAgentName() + " receives base plan: " + newBasePlanMsg);
            storeAndAdjustProposals();
            String planName = newBasePlanMsg.getPlanName();
            if (planName.equals(AgentCommunication.NO_SOLUTION_MESSAGE)) {
                plan = null;
            } else {
                plan = (POPIncrementalPlan) searchTree.removePlan(planName);
            }
        }
        newBasePlanMsg.Clear();
        allProposals.clear();
        return plan;
    }

    /**
     * Stores the received plan proposals, adjusting their landmarks heuristc
     * values if necessary
     *
     * @since 1.0
     */
    private void storeAndAdjustProposals() {
        for (NewBasePlanMessage.HeuristicChange change : newBasePlanMsg.getChanges()) {
            String planName = change.getName();
            for (InternalProposal p : allProposals) {
                if (p.plan.getName().equals(planName)) {
                    //System.out.println("Adjusted heuristic of " + planName + " with " + change.getIncH());
                    p.plan.setH(p.plan.getH(), p.plan.getHLan() - change.getIncH());
                    break;
                }
            }
        }
        for (InternalProposal p : allProposals) {
            if (!p.plan.isSolution()) {
                searchTree.addPlan(p.plan);
            }
        }
    }

    /**
     * Prints a solution plan and some data about computing time and plan
     * quality.
     *
     * @param solution Solution plan
     * @param mc Object to check the average metric value of the plan
     * @since 1.0
     */
    private void printStatistics(Plan solution, MetricChecker mc) {
        agentListener.trace(1, "Solution found: " + solution.getName());
        agentListener
                .trace(0, String.format("Planning (expansion) time: %.3f sec.",
                        this.planTime / 1000.0));
        agentListener.trace(0, String.format("Evaluation time: %.3f sec.",
                this.evaluationTime / 1000.0));
        agentListener.trace(0, String.format("Communication time: %.3f sec.",
                this.communicationTime / 1000.0));
        agentListener.trace(0, String.format("Average branching factor: %.3f",
                (double) (searchTree.size() + planningStep)
                / (double) planningStep));
        if (this.configuration.getNegotiationFactory().getNegotiationType() != NegotiationFactory.COOPERATIVE) {
            agentListener.trace(0, String.format("Metric value: %.1f",
                    evaluateMetric((POPIncrementalPlan) solution)));
            agentListener.trace(
                    0,
                    String.format("Average metric value: %.1f",
                            mc.getBestMetric()));
        }
        agentListener.trace(0,
                String.format("Discarded plans: %d", this.discarded));
        calculateTimeSteps(solution);
    }

    /**
     * Gets the metric value of a given plan.
     *
     * @param plan Plan to check
     * @return Metric value of the plan
     */
    public double evaluateMetric(POPIncrementalPlan plan) {
        double makespan;
        if (configuration.getGroundedTask().metricRequiresMakespan()) {
            makespan = plan.computeMakespan();
        } else {
            makespan = 0;
        }
        if (plan.isSolution()) {
            return configuration.getGroundedTask().evaluateMetric(
                    plan.computeState(plan.getFather().linearization(), configuration),
                    makespan);
        }
        return configuration.getGroundedTask().evaluateMetric(
                plan.computeState(plan.linearization(), configuration), makespan);
    }

    /**
     * Sets the ancestor plans for a given plan.
     *
     * @param nextPlan Plan
     * @since 1.0
     */
    public void setAntecessors(POPIncrementalPlan nextPlan) {
        int offset = 1;

        if (nextPlan.isRoot()) {
            antecessors = new POPIncrementalPlan[1];
        } else {
            if (nextPlan.isSolution()) {
                offset--;
                if (nextPlan.getStep().getIndex() == 1) {
                    antecessors = new POPIncrementalPlan[nextPlan.getFather()
                            .getStep().getIndex() + 1];
                } else {
                    antecessors = new POPIncrementalPlan[nextPlan.getStep()
                            .getIndex() + 1];
                }
            } else {
                antecessors = new POPIncrementalPlan[nextPlan.getStep()
                        .getIndex()];
            }
        }

        POPIncrementalPlan aux = nextPlan;
        int pos = antecessors.length - 1;
        while (!aux.isRoot()) {
            if (aux.getStep().getIndex() == 1) {
                antecessors[pos] = aux;
                offset++;
                aux = aux.getFather();
            } else {
                antecessors[aux.getStep().getIndex() - offset] = aux;
                pos = aux.getStep().getIndex() - 1;
                aux = aux.getFather();
            }
        }
        antecessors[0] = aux;
    }

    /**
     * Proposals sending simulation for single-agent tasks.
     *
     * @param proposals List of plan proposals to send
     * @param basePlan Current base plan
     * @return Solution plan if found; <code>null</code>, otherwise
     * @since 1.0
     */
    public abstract IPlan sendProposalsMonoagent(ArrayList<IPlan> proposals,
            IPlan basePlan);

    /**
     * Main loop of the planner: selects and solves plans' flaws and manages the
     * search tree.
     *
     * @return Solution plan or valid refinement; <code>null</code>, if the
     * complete search tree has been explored without finding further solutions
     * @since 1.0
     */
    public abstract ArrayList<IPlan> POPForwardLoop();

    /**
     * Plan evaluation. To be overriden in descendant classes.
     *
     * @param plan Plan to be evaluated
     * @param evThreads List of evaluation threads
     * @since 1.0
     */
    public abstract void evaluatePlan(IPlan plan,
            ArrayList<Planner.EvaluationThread> evThreads);

    /**
     * Computes the successor plans of the given base plan.
     *
     * @param basePlan Base plan
     * @return List of successor plans
     * @since 1.0
     */
    protected ArrayList<IPlan> computeSuccessors(POPInternalPlan basePlan) {
        this.currentInternal = basePlan;

        this.internalSearchTree = new POPInternalSearchTree(
                this.initialInternalPlan);

        ArrayList<IPlan> solutions = addFinalStep();
        ArrayList<IPlan> plans = null;
        // Add successors if:
        // 1 - There are not solutions. In case there are solutions, add
        // successors if:
        // 2 - FMAP is in anytime mode or it is using non-cooperative
        // negotiation strategy
        if (solutions == null) {
            plans = POPForwardLoop();
        }
        if (solutions != null) {
            if (plans != null) {
                for (IPlan p : solutions) {
                    plans.add(p);
                }
            } else {
                plans = solutions;
            }
        }
        for (IPlan p : plans) {
            p.setG(p.numSteps());
        }
        return plans;
    }

    /**
     * Sens plan proposals to the other agents.
     *
     * @param prop List of plan proposals
     * @param basePlan Base plan
     * @param adjustHLandStage Indicates if a stage to adjust the landmarks
     * heuristic values of the plans is needed
     * @return Solution plan if it is found among the proposals;
     * <code>null</code>, otherwise
     * @since 1.0
     */
    protected IPlan sendProposals(ArrayList<IPlan> prop, IPlan basePlan, boolean adjustHLandStage) {
        if (comm.numAgents() == 1) {
            return sendProposalsMonoagent(prop, basePlan);
        }
        // Check if there are repeated proposals before evaluating them
        ArrayList<InternalProposal> ownProposals = new ArrayList<>();
        for (IPlan p : prop) {
            if (memoization.search((POPIncrementalPlan) p) == null) {
                if (!p.isSolution()) {
                    memoization.add((POPIncrementalPlan) p);
                }
                ownProposals.add(new InternalProposal(p));
            } else {
                discarded++;
            }
        }
        long t2 = System.currentTimeMillis();
        evaluateProposals(ownProposals, basePlan, adjustHLandStage);
        this.evaluationTime = this.evaluationTime
                + (System.currentTimeMillis() - t2);

        long t3 = System.currentTimeMillis();
        IPlan solution = communicateProposals(ownProposals, adjustHLandStage);
        this.communicationTime = this.communicationTime
                + (System.currentTimeMillis() - t3);

        return solution;
    }

    /**
     * Evaluates the private goals of the plan proposals.
     *
     * @param allProposals List of plan proposals
     * @param basePlan Base plan
     * @since 1.0
     */
    protected void evaluatePrivateGoals(ArrayList<IPlan> allProposals,
            IPlan basePlan) {
        heuristic.startEvaluation(basePlan);
        for (IPlan p : allProposals) {
            heuristic.evaluatePlanPrivacy(p, 0);
        }
        heuristic.waitEndEvaluation();
    }

    /**
     * Calculates the heursistic values of a list of plan proposals.
     *
     * @param proposals List of plan proposals
     * @param basePlan Base plan
     * @param adjustHLandStage Indicates if a stage to adjust the landmarks
     * heuristic values of the plans is needed
     * @since 1.0
     */
    protected void evaluateProposals(ArrayList<InternalProposal> proposals, IPlan basePlan,
            boolean adjustHLandStage) {
        heuristic.startEvaluation(basePlan);
        if (adjustHLandStage) {
            ArrayList<Integer> achievedLandmarks = new ArrayList<>();
            for (InternalProposal p : proposals) {
                heuristic.evaluatePlan(p.plan, 0, achievedLandmarks);
                p.setAchievedLandmarks(achievedLandmarks, heuristic.numGlobalLandmarks());
                achievedLandmarks.clear();
            }
        } else {
            for (InternalProposal p : proposals) {
                heuristic.evaluatePlan(p.plan, 0);
            }
        }
        heuristic.waitEndEvaluation();
    }

    /**
     * Sens the own plan proposals to the other agents.
     *
     * @param ownProposals List of own plan proposals
     * @param adjustHLandStage Indicates if a stage to adjust the landmarks
     * heuristic values of the plans is needed
     * @return Solution plan if it is found among the proposals;
     * <code>null</code>, otherwise
     * @since 1.0
     */
    protected IPlan communicateProposals(ArrayList<InternalProposal> ownProposals,
            boolean adjustHLandStage) {

        prepareProposalsToSend(ownProposals);
        // Communicate and receive proposals
        IPlan solution;
        if (!adjustHLandStage) {
            int propCount = 0;
            for (String ag : comm.getOtherAgents()) {
                comm.sendMessage(ag, proposalsToSend.get(propCount++), false);
            }
            solution = receiveProposals(ownProposals);
        } else {
            int propCount = 0, batonAgentIndex = 0;
            for (String ag : comm.getOtherAgents()) {	// Do not send to baton agent
                if (!ag.equals(comm.getBatonAgent())) {
                    comm.sendMessage(ag, proposalsToSend.get(propCount), false);
                } else {
                    batonAgentIndex = propCount;
                }
                propCount++;
            }
            solution = adjustAndReceiveProposals(ownProposals, batonAgentIndex);
        }
        return solution;
    }

    /**
     * Receives the plan proposals from other agents and adjusts their heuristic
     * values if needed.
     *
     * @param ownProposals List of own plan proposals
     * @param batonAgentIndex Index of the current baton agent
     * @return Solution plan if it is found among the proposals;
     * <code>null</code>, otherwise
     * @since 1.0
     */
    private IPlan adjustAndReceiveProposals(ArrayList<InternalProposal> ownProposals,
            int batonAgentIndex) {
        IPlan solution;
        if (!comm.batonAgent()) {
            solution = receiveProposals(ownProposals);
            adjustHeuristic(allProposals);
            hAdjustment.addOwnProposals(proposalsToSend.get(batonAgentIndex));
            comm.sendMessage(comm.getBatonAgent(), hAdjustment, false);
        } else {
            solution = receiveHeuristicAdjustments(ownProposals);
        }
        return solution;
    }

    /**
     * Receives heuristic value adjustments from other agents.
     *
     * @param ownProposals List of own plan proposals
     * @return Solution plan if it is found among the proposals;
     * <code>null</code>, otherwise
     * @since 1.0
     */
    private IPlan receiveHeuristicAdjustments(ArrayList<InternalProposal> ownProposals) {
        IPlan solution = null;
        hAdjustment = new HeuristicAdjustment(1 + ownProposals.size() * comm.numAgents());
        int index = 0;
        for (String ag : comm.getAgentList()) {
            if (ag.equals(comm.getThisAgentName())) {	// This agent
                for (InternalProposal p : ownProposals) {
                    p.plan.setName(index++, basePlan);
                    allProposals.add(p);
                    if (p.plan.isSolution()) {
                        solution = p.plan;
                    } else {
                        memoization.add((POPIncrementalPlan) p.plan);
                    }
                    if (agentListener != null) {
                        agentListener.trace(2, "Sending plan " + p.plan.getName()
                                + "[" + p.plan.getH() + "]");
                        agentListener.newPlan(p.plan, configuration);
                    }
                }
            } else {						// Other agent
                adjustmentFilter.fromAgent = ag;
                HeuristicAdjustment h = (HeuristicAdjustment) comm
                        .receiveMessage(adjustmentFilter, false);
                for (ProposalToSend prop : h.getProposals()) {
                    POPIncrementalPlan p = new POPIncrementalPlan(prop, basePlan,
                            configuration, this);
                    p.setName(index++, basePlan);
                    String planName = p.getName();
                    InternalProposal proposal = new InternalProposal(p, prop.getAchievedLandmarks());
                    ArrayList<Integer> newLand = heuristic.checkNewLandmarks(proposal.plan, proposal.achievedLandmarks);
                    hAdjustment.merge(planName, newLand);
                    allProposals.add(proposal);
                    if (p.isSolution()) {
                        solution = p;
                    } else {
                        memoization.add(p);
                    }
                    if (agentListener != null) {
                        agentListener.trace(2, "Received plan " + planName + " from " + ag + "[" + p.getH() + "]");
                        agentListener.newPlan(p, configuration);
                    }
                }
                ArrayList<String> planNames = h.proposalsWithAdjustments();
                for (String planName : planNames) {
                    hAdjustment.merge(planName, h.getNewLandmarks(planName));
                }
            }
        }
        updateHLandValues();
        return solution;
    }

    /**
     * Updates the landmarks heuristic values of all the proposals.
     *
     * @since 1.0
     */
    private void updateHLandValues() {
        for (InternalProposal p : allProposals) {
            IPlan plan = p.plan;
            String planName = plan.getName();
            int incH = hAdjustment.getNumNewLandmarks(planName);
            if (incH > 0) {
                newBasePlanMsg.addAdjustment(planName, incH);
                plan.setH(plan.getH(), plan.getHLan() - incH);
            }
            if (!plan.isSolution()) {
                searchTree.addPlan(plan);
            }
        }
    }

    /**
     * Adjust the heuristic values of the plan proposals.
     *
     * @param proposals List of plan proposals
     * @since 1.0
     */
    private void adjustHeuristic(ArrayList<InternalProposal> proposals) {
        hAdjustment = new HeuristicAdjustment(proposals.size());
        String fromAgent;

        for (InternalProposal prop : proposals) {
            IPlan plan = prop.plan;
            fromAgent = plan.lastAddedStep().getAgent();
            if (fromAgent != null && !comm.getThisAgentName().equals(fromAgent)) {
                // Proposal from other agent and the new step is not at the end of the plan
                ArrayList<Integer> newLandmarks = heuristic.checkNewLandmarks(plan,
                        prop.achievedLandmarks);
                hAdjustment.add(plan.getName(), newLandmarks);
            }
        }
    }

    /**
     * Receives a list of plan proposals from other agents.
     *
     * @param ownProposals List of own proposals
     * @return Solution plan if it is found among the proposals;
     * <code>null</code>, otherwise
     * @since 1.0
     */
    private IPlan receiveProposals(ArrayList<InternalProposal> ownProposals) {
        IPlan solution = null;
        int index = 0;
        for (String ag : comm.getAgentList()) {
            if (ag.equals(comm.getThisAgentName())) {	// This agent
                for (InternalProposal p : ownProposals) {
                    p.plan.setName(index++, basePlan);
                    allProposals.add(p);
                    if (p.plan.isSolution()) {
                        solution = p.plan;
                    } else {
                        memoization.add((POPIncrementalPlan) p.plan);
                    }
                    if (agentListener != null) {
                        agentListener.trace(2, "Sending plan " + p.plan.getName()
                                + "[" + p.plan.getH() + "]");
                        agentListener.newPlan(p.plan, configuration);
                    }
                }
            } else { // Other agent
                proposalsFilter.fromAgent = ag;
                @SuppressWarnings("unchecked")
                ArrayList<ProposalToSend> pp = (ArrayList<ProposalToSend>) comm
                        .receiveMessage(proposalsFilter, false);
                for (ProposalToSend prop : pp) {
                    POPIncrementalPlan p = new POPIncrementalPlan(prop, basePlan, configuration, this);
                    p.setName(index++, basePlan);
                    allProposals.add(new InternalProposal(p, prop.getAchievedLandmarks()));
                    if (p.isSolution()) {
                        solution = p;
                    } else {
                        memoization.add(p);
                    }
                    if (agentListener != null) {
                        agentListener.trace(2, "Received plan " + p.getName()
                                + " from " + ag + "[" + p.getH() + "]");
                        agentListener.newPlan(p, configuration);
                    }
                }
            }
        }
        return solution;
    }

    /**
     * Prepares the list of plan proposals to be sent to other agents.
     *
     * @param proposals List of plan proposals
     * @since 1.0
     */
    private void prepareProposalsToSend(ArrayList<InternalProposal> proposals) {
        for (int i = 0; i < comm.getOtherAgents().size(); i++) {
            proposalsToSend.get(i).clear();
        }
        int propCount;
        for (InternalProposal prop : proposals) {
            propCount = 0;
            for (String ag : comm.getOtherAgents()) {
                ProposalToSend pp = new ProposalToSend(prop, ag, false);
                proposalsToSend.get(propCount).add(pp);
                propCount++;
            }
        }
    }

    /**
     * Calculates the time steps for a solution plan.
     *
     * @param solution Solution plan
     * @since 1.0
     */
    protected void calculateTimeSteps(Plan solution) {
        ArrayList<Ordering> ord = solution.getOrderingsArray();
        ArrayList<CausalLink> cl = solution.getCausalLinksArray();
        Hashtable<Integer, Integer> stepsFound = new Hashtable<>();
        boolean found, moreFound = true;
        int timeStep = 0;

        while (moreFound) {
            moreFound = false;

            for (int i = 2; i < solution.getStepsArray().size(); i++) {
                if (solution.getStepsArray().get(i).getTimeStep() == -1) {
                    found = true;
                    for (Ordering o : ord) {
                        if (o.getIndex2() == i
                                && (stepsFound.get(o.getIndex1()) == null || stepsFound
                                .get(o.getIndex1()) == timeStep)) {
                            found = false;
                            break;
                        }
                    }
                    if (found) {
                        for (CausalLink c : cl) {
                            if (c.getIndex1() != 0 && c.getIndex2() != 1) {
                                if (c.getIndex2() == i
                                        && (stepsFound.get(c.getIndex1()) == null || stepsFound
                                        .get(c.getIndex1()) == timeStep)) {
                                    found = false;
                                    break;
                                }
                            }
                        }
                    }
                    if (found) {
                        moreFound = true;
                        stepsFound.put(i, timeStep);
                        solution.getStepsArray().get(i).setTimeStep(timeStep);
                    }
                }
            }

            timeStep++;
        }
    }

    /**
     * Estimates the actions of the domain that are potentially supportable in
     * the current base plan.
     *
     * @return List of potentially supportable actions
     * @since 1.0
     */
    protected ArrayList<POPAction> calculateApplicableActions_old() {
        ArrayList<POPAction> applicableActions = new ArrayList<>();
        // Analyze all the actions in the agent's domain
        for (POPAction pa : this.configuration.getActions()) {
            if (this.isApplicable(currentInternal, pa)) {
                if (isHazardous(pa)) {
                    applicableActions.add(pa);
                } else if (this.memoization.search(basePlan, pa) == null) {
                    applicableActions.add(pa);
                }
            }
        }
        this.agentListener.trace(1, "Agent " + comm.getThisAgentName()
                + " found " + applicableActions.size() + " applicable actions");
        return applicableActions;
    }

    /**
     * Estimates the actions of the domain that are potentially supportable in
     * the current base plan.
     *
     * @return List of potentially supportable actions
     * @since 1.0
     */
    protected ArrayList<POPAction> calculateApplicableActions() {
        ArrayList<POPAction> applicableActions = new ArrayList<>();
        this.calculateEffectsLastValues(currentInternal);
        // Analyze all the actions in the agent's domain
        for (POPAction pa : this.configuration.getActions()) {
            if (this.isActionSupportable(currentInternal, pa)) {
                if (this.memoization.search(basePlan, pa) == null) {
                    applicableActions.add(pa);
                }
            }

        }
        if (agentListener != null) {
            agentListener.trace(1, "Agent " + comm.getThisAgentName() + " found " + applicableActions.size() + " applicable actions");
        }
        return applicableActions;
    }

    /**
     * Checks if the preconditions of an action can be supported in the given
     * plan.
     *
     * @param p Plan
     * @param a Action to check
     * @return <code>true</code>, if the action preconditions can be supported;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public Boolean isActionSupportable(POPInternalPlan p, POPAction a) {
        POPPrecEff prec;
        for (int i = 0; i < a.getPrecs().size(); i++) {
            prec = a.getPrecs().get(i);
            if (a.hasEffectInVariable(i)) {
                Integer value = lastValues.get(prec.getVarCode());
                if (value != null && value != prec.getValueCode()) {
                    return false;
                }
            } else {
                if (this.hashEffects.get(prec.toKey()) == null) {
                    return false;
                }
            }
        }
        return true;
    }

    /**
     * Fills the hashEffects structure.
     *
     * @param p Base plan
     * @since 1.0
     */
    public void calculateEffectsLastValues(POPInternalPlan p) {
        POPStep ps;
        int[] linearization = this.basePlan.linearization();
        int index;
        this.hashEffects = new Hashtable<>();
        this.lastValues = new Hashtable<>();
        // Check the steps of the linearized base plan in reverse order
        for (int i = linearization.length - 1; i >= 0; i--) {
            index = linearization[i];
            if (index != 1) {
                ps = (POPStep) p.getStep(index);

                for (POPPrecEff eff : ps.getEffects()) {
                    hashEffects.put(eff.toKey(), true);
                    if (lastValues.get(eff.getVarCode()) == null) {
                        lastValues.put(eff.getVarCode(), eff.getValueCode());
                    }
                }
            }
        }
    }

    /**
     * Checks if an action modifies variables which are not in its
     * preconditions.
     *
     * @param a Action to check
     * @return <code>true</code>, if the action modifies variables which are not
     * in its preconditions; <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean isHazardous(POPAction a) {
        for (POPPrecEff eff : a.getEffects()) {
            if (this.hazardousVars.get(eff.getVarCode()) != null) {
                return true;
            }
        }
        return false;
    }

    /**
     * Checks if an action is applicable in a plan.
     *
     * @param p Plan
     * @param a Action to check
     * @return <code>true</code>, if the action is applicable;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public Boolean isApplicable(POPInternalPlan p, POPAction a) {
        POPStep ps;
        int i;
        Boolean found;
        if (this.hashEffects == null) {
            // hashEffects stores the effects of the steps of the base plan
            this.hashEffects = new Hashtable<>();
            this.hazardousVars = new Hashtable<>();
            // Analyze the steps of the base plan
            for (i = 0; i < p.numSteps(); i++) {
                ps = (POPStep) p.getStep(i);
                if (ps.getIndex() != 1) {
                    for (POPPrecEff eff : ps.getEffects()) {
                        // Fill hashEffects structure
                        this.hashEffects.put(eff.toKey(), Boolean.TRUE);

                        if (ps.getIndex() != 0) {
                            found = false;
                            for (POPPrecEff pre : ps.getPreconditions()) {
                                if (pre.getVarCode() == eff.getVarCode()) {
                                    found = true;
                                    break;
                                }
                            }
                            if (!found) {
                                this.hazardousVars.put(eff.getVarCode(), Boolean.TRUE);
                            }
                        }
                    }
                }
            }
        }

        for (POPPrecEff prec : a.getPrecs()) {
            if (this.hashEffects.get(prec.toKey()) == null) {
                return false;
            }
        }

        return true;
    }

    /**
     * Restore the causal links array when a new POPInternalPlan is expanded.
     *
     * @since 1.0
     */
    public void restoreCausalLinks() {
        getTotalCausalLinks().trimToSize(getNumCausalLinks());
        setModifiedCausalLinks(false);
    }

    /**
     * Restore the causal links array when a new POPInternalPlan is expanded.
     *
     * @since 1.0
     */
    public void restoreOrderings() {
        totalOrderings.trimToSize(numOrderings);
        modifiedOrderings = false;
    }

    /**
     * Secondary loop, integrates a new action in the plan and solves all its
     * flaws.
     *
     * @param step Step to integrate
     * @return Plan refinements obtained after the integration
     * @since 1.0
     */
    protected ArrayList<IPlan> solveAction(POPStep step) {
        ArrayList<IPlan> refinements = new ArrayList<>();
        successors.clear();
        POPIncrementalPlan refinement;

        while (!this.internalSearchTree.isEmpty()) {
            this.expandedNodes++;
            // Clean causal link and ordering arrays from previous usage
            restoreCausalLinks();
            restoreOrderings();
            currentInternal = (POPInternalPlan) this.internalSearchTree
                    .getNextPlan();
            // Store causal links and orderings of the next plan in the array
            currentInternal.addCausalLinks();
            currentInternal.addOrderings();

            matrix.rebuild(currentInternal);

            // If the plan supports completely the action, store it as a solution
            if (this.solutionChecker.keepsConstraints(currentInternal, step)) {
                refinement = new POPIncrementalPlan(
                        (POPInternalPlan) currentInternal,
                        antecessors[antecessors.length - 1], parent);
                refinements.add(refinement);
            } else {
                // If the plan has threats, solve the first of them
                if (currentInternal.getThreats().size() > 0) {
                    solveThreat(currentInternal, step.getIndex() == 1);
                } // If the plan is threat-free, the next open condition of the
                // new action is solved
                else {
                    if (currentInternal.getPreconditions().size() > 0) {
                        this.solveOpenCondition(currentInternal, step);
                    }
                }
            }
        }

        return refinements;
    }

    /**
     * Selects and solves an open condition of the plan.
     *
     * @param father Base plan
     * @param newStep New step to add
     * @since 1.0
     */
    public void solveOpenCondition(POPInternalPlan father, POPStep newStep) {
        POPInternalPlan successor;
        POPAction act;
        POPStep step;
        POPOpenCondition prec;
        ArrayList<POPInternalPlan> suc = new ArrayList<>();
        int i;
        boolean isFinalStep = newStep.getIndex() == 1;

        // If the new step is not yet stored into the plan, we add it by solving
        // one of its preconditions through a causal link
        if (father.numSteps() <= newStep.getIndex()) {
            // Select the first precondition of the new step
            prec = new POPOpenCondition(newStep.getPreconditions()[0], newStep,
                    true);
            // Solve the selected open condition with the existent steps of the plan
            for (i = 0; i < father.numSteps(); i++) {// Step s:
                step = (POPStep) father.getStep(i);
                act = step.getAction();
                if (step.getIndex() != 1) {
                    for (POPPrecEff eff : act.getEffects()) {
                        if (eff.getVarCode() == prec.getCondition().getVarCode()) {
                            if ((prec.getCondition().getType() == EQUAL
                                    && eff.getValueCode() == prec.getCondition().getValueCode()
                                    && eff.getType() == EQUAL)
                                    || (prec.getCondition().getType() == DISTINCT
                                    && eff.getValueCode() != prec.getCondition().getValueCode())) {
                                successor = new POPInternalPlan(father, newStep,
                                        new POPCausalLink(step, prec.getPrecEff(), newStep),
                                        new POPOrdering(step.getIndex(), prec.getStep().getIndex()),
                                        father.getPreconditions(), null, prec,
                                        isFinalStep, this);

                                this.detectThreatsNewStep(newStep,
                                        step.getIndex(), father, successor);
                                this.detectThreatsLink(
                                        successor.getCausalLink(), father,
                                        successor);
                                suc.add(successor);
                            }
                        }
                    }
                }
            }
        } else {
            // Retrieve the next open condition to be solved and erase it from
            // the plan
            prec = (POPOpenCondition) father.getPreconditions().get(
                    father.getPreconditions().size() - 1);
            father.getPreconditions().remove(
                    father.getPreconditions().size() - 1);

            // Search among the plan's steps
            for (i = 0; i < father.numSteps(); i++) {
                step = (POPStep) father.getStep(i);
                act = step.getAction();

                if (step.getIndex() != prec.getStep().getIndex()) {
                    if (step.getIndex() != 1) { // Skip final step, cannot solve any condition
                        for (POPPrecEff eff : act.getEffects()) {
                            if (eff.getVarCode() == prec.getCondition().getVarCode()) {
                                if ((prec.getCondition().getType() == EQUAL
                                        && eff.getValueCode() == prec.getCondition().getValueCode()
                                        && eff.getType() == EQUAL)
                                        || (prec.getCondition().getType() == DISTINCT
                                        && eff.getValueCode() != prec.getCondition().getValueCode())) {
                                    if (!matrix.checkOrdering(prec.getStep()
                                            .getIndex(), step.getIndex())) {
                                        POPStep st = (POPStep) father
                                                .getStep(prec.getStep()
                                                        .getIndex());
                                        // Generate the new incremental plan, 
                                        // storing the list of open conditions 
                                        // and the parent plan
                                        successor = new POPInternalPlan(father,
                                                null,
                                                new POPCausalLink(step, prec
                                                        .getPrecEff(), st),
                                                new POPOrdering(
                                                        step.getIndex(), prec
                                                        .getStep()
                                                        .getIndex()),
                                                father.getPreconditions(),
                                                null, prec, isFinalStep, this);

                                        if (!matrix.checkOrdering(step
                                                .getIndex(), prec.getStep()
                                                        .getIndex())) {
                                            successor.setOrdering(step
                                                    .getIndex(), prec.getStep()
                                                            .getIndex());
                                        }

                                        this.detectThreatsLink(
                                                successor.getCausalLink(),
                                                father, successor); // Search for
                                        // threats that the existing steps in the
                                        // plan can cause to the new causal link
                                        suc.add(successor);
                                    }
                                }
                            }
                        }
                    }
                }
            }
            father.cleanPlan();
        }

        // Store the successors in the search tree
        this.internalSearchTree.addSuccessors(suc);
    }

    /**
     * Solves the last threat of the plan by promoting or demoting the
     * threatening step.
     *
     * @param father Base plan
     * @param isFinalStep Indicates if we are supporting the final step
     */
    @Override
    public void solveThreat(POPInternalPlan father, boolean isFinalStep) {
        POPInternalPlan successor1 = null, successor2 = null;

        // Extract the last threat of the list to solve it (LIFO criteria)
        POPThreat threat = father.getThreats().remove(
                father.getThreats().size() - 1);

        // Locate the indexes of the involved steps
        int index1 = threat.getCausalLink().getIndex1(); // Store the index of
        // step Pi
        int index2 = threat.getCausalLink().getIndex2(); // Store the index of
        // step Pj
        int indexThreat = threat.getThreateningStep(); // Store the index of the
        // threatening step P

        // Check if the threat exists already; if not, we erase it, exit the
        // method and restart the search process with the current plan
        // The threat may have been removed by the deletion of a previous threat
        if (matrix.checkOrdering(indexThreat, index1)
                || matrix.checkOrdering(index2, indexThreat)) {
            internalSearchTree.addPlan(father);
        }

        // Promotion process (performed only if Pj is NOT the final step)
        if (index2 != 1) {
            // Try to promote P (add ordering Pj -> P). To do so, check if there
            // is not an ordering (direct or transitive) P -> Pj
            // If the ordering P -> Pj is not found, an ordering Pj -> P is
            // added
            if (!matrix.checkOrdering(indexThreat, index2)
                    && !matrix.checkOrdering(index2, indexThreat)) {
                successor1 = new POPInternalPlan(father, null, null, null,
                        father.getPreconditions(), father.getThreats(), null,
                        isFinalStep, father.getPlanner());
                successor1.setOrdering(index2, indexThreat);
                internalSearchTree.addPlan(successor1);
            }
        }

        // Demotion process (performed only if Pi is NOT the initial step)
        if (index1 != 0) {
            // Try to demote P (add ordering P -> Pi).
            if (!matrix.checkOrdering(index1, indexThreat)
                    && !matrix.checkOrdering(indexThreat, index1)) {
                successor2 = new POPInternalPlan(father, null, null, null,
                        father.getPreconditions(), father.getThreats(), null,
                        isFinalStep, father.getPlanner());
                successor2.setOrdering(indexThreat, index1);
                internalSearchTree.addPlan(successor2);
            }
        }
        // Store the successors in the search tree
        if (successor1 != null || successor2 != null) {
            father.cleanPlan();
        }
    }

    /**
     * Detects all the threats caused by the inclusion of a new causal link si
     * -p-> sj, where si may be an existing or a new step.
     *
     * @param link New causal link
     * @param father Parent plan
     * @param successor Successor plan that stores the new causal link
     * @since 1.0
     */
    public void detectThreatsLink(POPCausalLink link, POPInternalPlan father,
            POPInternalPlan successor) {
        int i, j, index1, index2;

        Boolean order;
        POPStep step;
        ArrayList<POPThreat> threats = new ArrayList<>();
        int type = link.getCondition().getType();

        // Buscamos los indices de los dos pasos del causal link
        index1 = link.getIndex1();
        index2 = link.getIndex2();

        // Check the plan step, skipping the initial anf final ones which cannot cause threats
        for (i = 2; i < father.numSteps(); i++) {
            step = (POPStep) father.getStep(i);
            if (step == null) {
                father.setNumSteps(-1);
                father.numSteps();
                step = (POPStep) father.getStep(i);
            }
            // Check that the current step is not part of the causal link
            if (index1 != i && index2 != i) {
                for (j = 0; j < step.getAction().getEffects().size(); j++) {
                    if (type == EQUAL) {
                        if (step.getAction().getEffects().get(j).getVarCode() == link.getCondition().getVarCode()
                                && step.getAction().getEffects().get(j).getValueCode() != link.getCondition().getValueCode()) {
                            // If P is the initial step, there is an ordering P > Pi
                            if (i == 0) {
                                order = true;
                            } // We search for an ordering P > Pi
                            else {
                                order = matrix.checkOrdering(i, index1);
                            }
                            // Otherwise, we search an ordering Pj > P
                            if (!order) {
                                order = matrix.checkOrdering(index2, i);
                            }
                            // If we did not found the orderings, we add the new
                            // threat (as P can be placed between Pi and Pj)
                            if (!order) {
                                threats.add(new POPThreat(step, link));
                            }
                        }
                    }
                    if (type == DISTINCT) {
                        if (step.getAction().getEffects().get(j).getVarCode() == link.getCondition().getVarCode()
                                && step.getAction().getEffects().get(j).getValueCode() == link.getCondition().getValueCode()) {
                            if (i == 0) {
                                order = true;
                            } else {
                                order = matrix.checkOrdering(i, index1);
                            }
                            if (!order) {
                                order = matrix.checkOrdering(index2, i);
                            }
                            if (!order) {
                                threats.add(new POPThreat(step, link));
                            }
                        }
                    }
                }
            }
        }
        successor.addThreats(threats);
    }

    /**
     * Detects all the threats caused by the inclusion of a new step.
     *
     * @param step New step introduced
     * @param index Index of the step s2 of the ordering ns -> s2, where ns is
     * the new step introduced
     * @param father Parent plan
     * @param successor Successor plan that stores the new step
     * @since 1.0
     */
    public void detectThreatsNewStep(POPStep step, int index,
            POPInternalPlan father, POPInternalPlan successor) {
        int i, j, index1, index2, indexStep;
        Boolean order;
        POPCausalLink link;
        Condition precondition;
        ArrayList<POPThreat> threats = new ArrayList<>();

        indexStep = step.getIndex();

        for (i = 0; i < step.getAction().getEffects().size(); i++) {
            for (j = father.getTotalCausalLinks().size() - 1; j >= 0; j--) {
                link = (POPCausalLink) father.getTotalCausalLinks().get(j);
                precondition = link.getCondition();
                index1 = link.getIndex1();
                index2 = link.getIndex2();

                // If the new step is not part of the causal link, check the threats
                if (indexStep != index1 && indexStep != index2) {
                    if (link.getCondition().getType() == EQUAL) {
                        if (step.getAction().getEffects().get(i).getVarCode()
                                == precondition.getVarCode()
                                && step.getAction().getEffects().get(i).getValueCode()
                                != precondition.getValueCode()) {
                            order = matrix.checkOrdering(index2, index);
                            // If there is no ordering P > Pi or Pj > P, create the new threat
                            if (!order) {
                                threats.add(new POPThreat(step, link));
                            }
                        }
                    } else if (link.getCondition().getType() == DISTINCT) {
                        if (step.getAction().getEffects().get(i).getVarCode() == precondition.getVarCode()
                                && step.getAction().getEffects().get(i).getValueCode() == precondition.getValueCode()) {
                            if (index1 == index) {
                                order = true;
                            } else {
                                order = matrix.checkOrdering(index, index1);
                            }
                            if (!order) {
                                threats.add(new POPThreat(step, link));
                            }
                        }
                    }
                }
            }
        }
        // Add the threats found to the successor plan
        successor.addThreats(threats);
    }

    /**
     * Sets the initial step.
     *
     * @param s Initial step
     * @since 1.0
     */
    public void setInitialStep(Step s) {
        initialStep = s;
    }

    /**
     * Sets the final step.
     *
     * @param s Final step
     * @since 1.0
     */
    public void setFinalStep(Step s) {
        finalStep = s;
    }

    /**
     * Gets the solution checker.
     *
     * @return Solution checker
     * @since 1.0
     */
    public SolutionChecker getSolutionChecker() {
        return this.solutionChecker;
    }

    /**
     * Gets the base plan.
     *
     * @return Base plan
     * @since 1.0
     */
    public POPIncrementalPlan getBasePlan() {
        return basePlan;
    }

    /**
     * Gets the number of orderings in the base plan.
     *
     * @return Number of orderings
     * @since 1.0
     */
    public int getNumOrderings() {
        return numOrderings;
    }

    /**
     * Add the final step to the base plan.
     *
     * @return List of generated successors (solution plans)
     * @since 1.0
     */
    private ArrayList<IPlan> addFinalStep() {
        this.hashEffects = null;

        // The first plan to be processed is a copy of the planner's initial plan
        POPInternalPlan auxInternal = currentInternal;
        initialInternalPlan.setNumSteps(-1);

        if (this.basePlan.getH() == 0) {
            // Check if the final step is applicable
            POPStep st = (POPStep) currentInternal.getFinalStep();
            if (this.isApplicable(currentInternal, st.getAction())) {
                ArrayList<IPlan> succ = this.solveAction(st);

                currentInternal = auxInternal;
                restoreCausalLinks();
                restoreOrderings();
                currentInternal.restorePlan(openConditions);

                // Return successors (solution plans), if any
                if (succ.size() > 0) {
                    return succ;
                }
            }
        }
        // Return null if there is no solution
        return null;
    }

    /**
     * EvaluationThread class: thread for plan evaluation.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class EvaluationThread extends Thread {

        IPlan plan;         // Plan to evaluate
        int threadIndex;    // Thread index

        /**
         * Creates a new evaluation thread.
         *
         * @param plan Plan to evaluate
         * @param threadIndex Thread index
         * @since 1.0
         */
        EvaluationThread(IPlan plan, int threadIndex) {
            this.plan = plan;
            this.threadIndex = threadIndex;
        }

        /**
         * Starts the thread.
         *
         * @since 1.0
         */
        @Override
        public void run() {
            heuristic.evaluatePlan(plan, threadIndex);
        }
    }

    /**
     * MessageFilterProposals class: filter to receive messages with plan
     * proposals from other agents.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class MessageFilterProposals implements MessageFilter {

        protected String fromAgent; // Sender agent

        /**
         * Check if a given message meets the conditions of the filter.
         *
         * @param m Message to check
         * @return <code>true</code> if the message meets the conditions of the
         * filter; <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean validMessage(Message m) {
            return m.sender().equals(fromAgent)
                    && (m.content() instanceof ArrayList<?>);
        }
    }

    /**
     * MessageFilterAdjustment class: filter to receive heuristic valuea
     * djustments from other agents.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class MessageFilterAdjustment implements MessageFilter {

        protected String fromAgent; // Sender agent

        /**
         * Check if a given message meets the conditions of the filter.
         *
         * @param m Message to check
         * @return <code>true</code> if the message meets the conditions of the
         * filter; <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean validMessage(Message m) {
            return m.sender().equals(fromAgent)
                    && (m.content() instanceof HeuristicAdjustment);
        }
    }
    
}
