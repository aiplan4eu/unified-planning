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
import java.util.logging.Level;
import java.util.logging.Logger;
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_communication.PlanningAgentListener;
import org.agreement_technologies.common.map_heuristic.Heuristic;
import org.agreement_technologies.common.map_planner.IPlan;
import org.agreement_technologies.common.map_planner.OpenCondition;
import org.agreement_technologies.service.tools.CustomArrayList;

/**
 * Multi-thread Partial-Order Planner class.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPMultiThread extends Planner {

    private final int totalThreads;                 // Number of threads
    private final ArrayList<POPThread> runnables;   // List of POP threads
    private final ArrayList<Thread> threads;        // List of threads, which contain the POP threads
    private final boolean multithreadHeuristic;     // Indicates if the heuristic evaluator supports multithreading

    /**
     * Builds a POP from scratch.
     *
     * @param conf Configuration object
     * @param initial Initial step
     * @param last Final step
     * @param goals List of task goals
     * @param h Heuristic function evaluator
     * @param comm Communication utility
     * @param agentListener Agent listener (GUI for feedback)
     * @param searchType Search type
     * @since 1.0
     */
    public POPMultiThread(PlannerFactoryImp conf, POPStep initial,
            POPStep last, ArrayList<OpenCondition> goals, Heuristic h,
            AgentCommunication comm, PlanningAgentListener agentListener,
            int searchType) {
        super(comm);
        this.parent = this;

        this.configuration = conf;
        this.solutionChecker = configuration.getSolutionChecker();
        this.agentListener = agentListener;
        this.heuristic = h;
        this.comm = comm;

        this.myAgent = conf.getAgent();

        setInitialStep(initial);
        setFinalStep(last);

        initialInternalPlan = new POPInternalPlan(null, null, null, null,
                goals, null, null, false, this);
        this.initialIncrementalPlan = new POPIncrementalPlan(
                initialInternalPlan, null, this);

        if (agentListener != null) {
            agentListener.newPlan(initialIncrementalPlan, configuration);
        }

        this.successors = new ArrayList<>();

        initialIncrementalPlan.setName(0, null);
        this.searchTree = new POPSearchMethodTwoQueues(initialIncrementalPlan);
        // Create plan selection method
        planSelection = configuration.getNegotiationFactory()
                .getNegotiationMethod(comm, searchTree);

        totalCausalLinks = new CustomArrayList<>(50);
        totalOrderings = new CustomArrayList<>(50);

        this.matrix = new POPMatrix(20);// new
        // POPOrderingManagerNoMemorization();
        memoization = new StateMemoization(configuration.getNumGlobalVariables());

        this.totalThreads = conf.getTotalThreads();
        runnables = new ArrayList<>(this.totalThreads);
        threads = new ArrayList<>(this.totalThreads);

        for (int i = 0; i < this.totalThreads; i++) {
            ArrayList<POPAction> threadActions = new ArrayList<>();
            runnables.add(new POPThread(threadActions, conf, goals, initial,
                    last, this));
        }

        this.multithreadHeuristic = h.supportsMultiThreading();
    }

    /**
     * Main loop of the planner: selects and solves plans' flaws and manages the
     * search tree.
     *
     * @return Solution plan or valid refinement; <code>null</code>, if the
     * complete search tree has been explored without finding further solutions
     * @since 1.0
     */
    @Override
    public ArrayList<IPlan> POPForwardLoop() {
        ArrayList<IPlan> refinements = new ArrayList<>();
        this.hashEffects = null;

        initialInternalPlan.setNumSteps(-1);

        int i, j;

        // Initialize thread variables
        for (POPThread t : this.runnables) {
            t.setCurrentInternalPlan(currentInternal);
            t.initializeSearchTree(initialInternalPlan);
        }

        // Calculate applicable actions, distribute them among threads
        int actionsPerThread, remainder, index = 0;
        for (POPThread r : runnables) {
            r.clearThreadActions();
        }

        ArrayList<POPAction> applicableActions = super
                .calculateApplicableActions();

        actionsPerThread = applicableActions.size() / totalThreads;
        remainder = applicableActions.size() % totalThreads;

        // Add actions to each of the threads
        for (i = 0; i < totalThreads; i++) {
            for (j = actionsPerThread * index; j < actionsPerThread
                    * (index + 1); j++) {
                runnables.get(i).addApplicableAction(applicableActions.get(j));
            }
            index++;
        }
        // Add the remainding actions to the last thread
        for (i = actionsPerThread * index; i < actionsPerThread * index
                + remainder; i++) {
            runnables.get(runnables.size() - 1).addApplicableAction(
                    applicableActions.get(i));
        }

        // Launch threads to add applicable actions to the plan
        threads.clear();
        for (i = 0; i < this.totalThreads; i++) {
            threads.add(new Thread(this.runnables.get(i)));
            threads.get(i).start();
        }

        // Wait for each thread to conclude its execution
        for (i = 0; i < this.totalThreads; i++) {
            try {
                this.threads.get(i).join();
            } catch (InterruptedException ex) {
                Logger.getLogger(POPMultiThread.class.getName()).log(
                        Level.SEVERE, null, ex);
            }
        }

        // Add the refinement plans obtained by each thread to the main
        // refinement plan list
        for (int t = 0; t < totalThreads; t++) {
            refinements.addAll(runnables.get(t).getRefinements());
        }

        // Return refinement plans
        return refinements;
    }

    /**
     * Sets the ancestor plans for a given plan.
     *
     * @param nextPlan Plan
     * @since 1.0
     */
    @Override
    public void setAntecessors(POPIncrementalPlan nextPlan) {
        super.setAntecessors(nextPlan);

        for (POPThread t : this.runnables) {
            t.setAntecessors(antecessors);
        }
    }

    /**
     * Proposals sending simulation for single-agent tasks.
     *
     * @param proposals List of plan proposals to send
     * @param basePlan Current base plan
     * @return Solution plan if found; <code>null</code>, otherwise
     * @since 1.0
     */
    @Override
    public IPlan sendProposalsMonoagent(ArrayList<IPlan> proposals,
            IPlan basePlan) {
        IPlan solution = null;
        ArrayList<EvaluationThread> evThreads = new ArrayList<>();
        int i = 0;
        while (i < proposals.size()) {
            IPlan plan = proposals.get(i);
            if (plan.isSolution()
                    || memoization.search((POPIncrementalPlan) plan) == null) {
                plan.setName(i, basePlan);
                evaluatePlan(plan, evThreads);
                if (!plan.isSolution()) {
                    memoization.add((POPIncrementalPlan) plan);
                } else {
                    solution = plan;
                }
                i++;
            } else {
                proposals.remove(i);
            }
        }
        for (EvaluationThread ev : evThreads) {
            try {
                ev.join();
            } catch (InterruptedException e) {
            }
        }
        for (IPlan plan : proposals) {
            searchTree.addPlan(plan);
            if (agentListener != null) {
                agentListener.newPlan(plan, configuration);
            }
        }
        return solution;
    }

    /**
     * Plan evaluation.
     *
     * @param plan Plan to be evaluated
     * @param evThreads List of evaluation threads
     * @since 1.0
     */
    @Override
    public void evaluatePlan(IPlan plan, ArrayList<EvaluationThread> evThreads) {
        if (plan.isSolution()) {
            plan.setH(0, 0);
        } else if (multithreadHeuristic) {
            EvaluationThread t = new EvaluationThread(plan, evThreads.size());
            t.start();
            evThreads.add(t);
        } else {
            heuristic.evaluatePlan(plan, 0);
        }
    }

}
