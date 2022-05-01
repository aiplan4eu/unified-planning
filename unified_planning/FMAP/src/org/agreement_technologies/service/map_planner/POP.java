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

import org.agreement_technologies.common.map_planner.IPlan;
import java.util.ArrayList;
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_communication.PlanningAgentListener;
import org.agreement_technologies.common.map_heuristic.Heuristic;
import org.agreement_technologies.common.map_planner.OpenCondition;
import org.agreement_technologies.service.tools.CustomArrayList;

/**
 * Partial-Order Planner main class. Parameters: configuration object, search
 * tree, timeout, solution checking method, auxiliar array, base plan,
 * incremental version of the base plan
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POP extends Planner {

    /**
     * Builds a POP from scratch.
     *
     * @param conf Configuration object
     * @param initial Initial step
     * @param last Final step
     * @param goals List of task goals
     * @param h Heuristic function
     * @param comm Communication utility
     * @param agentListener Agent listener (GUI for feedback)
     * @param searchType Search type
     * @since 1.0
     */
    public POP(PlannerFactoryImp conf, POPStep initial, POPStep last,
            ArrayList<OpenCondition> goals, Heuristic h, AgentCommunication comm,
            PlanningAgentListener agentListener, int searchType) {
        super(comm);
        this.configuration = conf;
        this.solutionChecker = configuration.getSolutionChecker();
        this.agentListener = agentListener;
        this.heuristic = h;
        this.comm = comm;
        this.myAgent = conf.getAgent();
        this.parent = this;
        setInitialStep(initial);
        setFinalStep(last);
        initialInternalPlan = new POPInternalPlan(null, null, null, null, goals, null, null, false, this);
        this.initialIncrementalPlan = new POPIncrementalPlan(initialInternalPlan, null, this);
        if (agentListener != null) {
            agentListener.newPlan(initialIncrementalPlan, configuration);
        }
        this.successors = new ArrayList<>();
        initialIncrementalPlan.setName(0, null);
        this.searchTree = new POPSearchMethodTwoQueues(initialIncrementalPlan);
        //Create plan selection method
        planSelection = configuration.getNegotiationFactory().getNegotiationMethod(comm, searchTree);
        totalCausalLinks = new CustomArrayList<>(50);
        totalOrderings = new CustomArrayList<>(50);
        this.matrix = new POPMatrix(20);
        memoization = new StateMemoization(configuration.getNumGlobalVariables());
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
        ArrayList<IPlan> succ, refinements = new ArrayList<>();
        this.hashEffects = null;

        //The first plan to be processed is a copy of the planner's initial plan
        POPInternalPlan auxInternal = currentInternal;
        POPStep step;

        //Pre-calculate the applicable actions for the current plan
        ArrayList<POPAction> applicableActions = super.calculateApplicableActions();

        //Search loop; add an applicable action to the plan
        for (POPAction act : applicableActions) {
            currentInternal = auxInternal;

            if (!this.internalSearchTree.isEmpty()) {
                this.internalSearchTree.getNextPlan();
            }
            this.internalSearchTree.addPlan(currentInternal);
            //Check if the current action is applicable
            //Create a step associated to the action
            step = new POPStep(act, currentInternal.numSteps(), this.myAgent);
            succ = this.solveAction(step);
            if (succ.size() > 0) {
                for (IPlan s : succ) {
                    refinements.add(s);
                }
                succ.clear();
            }
        }

        //Clean causal link and ordering arrays from last usage
        restoreCausalLinks();
        restoreOrderings();

        //Return refinement plans
        return refinements;
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
    public IPlan sendProposalsMonoagent(ArrayList<IPlan> proposals, IPlan basePlan) {
        IPlan solution = null;
        for (int i = 0; i < proposals.size(); i++) {
            IPlan plan = proposals.get(i);
            if (plan.isSolution() || memoization.search((POPIncrementalPlan) plan) == null) {
                plan.setName(i, basePlan);
                if (plan.isSolution()) {
                    plan.setH(0, 0);
                } else {
                    heuristic.evaluatePlan(plan, 0);
                }
                searchTree.addPlan(plan);
                if (!plan.isSolution()) {
                    memoization.add((POPIncrementalPlan) plan);
                } else {
                    solution = plan;
                }
                if (agentListener != null) {
                    agentListener.newPlan(plan, configuration);
                }
            }
        }
        return solution;
    }

    /**
     * Plan evaluation. To be overriden in descendant classes.
     *
     * @param plan Plan to be evaluated
     * @param evThreads List of evaluation threads
     * @since 1.0
     */
    @Override
    public void evaluatePlan(IPlan plan, ArrayList<Planner.EvaluationThread> evThreads) {
    }

}
