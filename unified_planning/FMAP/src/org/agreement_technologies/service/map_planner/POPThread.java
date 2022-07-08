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
import org.agreement_technologies.common.map_planner.CausalLink;
import org.agreement_technologies.common.map_planner.IPlan;
import org.agreement_technologies.common.map_planner.OpenCondition;
import org.agreement_technologies.common.map_planner.Ordering;
import org.agreement_technologies.common.map_planner.Step;
import org.agreement_technologies.service.tools.CustomArrayList;

/**
 * POPThread class implements a thread for partial-order planning.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPThread extends Planner implements Runnable {

    private final ArrayList<POPAction> threadActions;   // Actions to add to the base plan
    private ArrayList<IPlan> threadRefinements;         // List of generated refinement plans

    /**
     * Creates a new POP thread.
     *
     * @param actions Applicable action to add to the base plan to generate
     * successors
     * @param conf Planner factory
     * @param goals List of task goals
     * @param initial Initial step
     * @param last Final step
     * @param planner Reference to the planner
     * @since 1.0
     */
    public POPThread(ArrayList<POPAction> actions, PlannerFactoryImp conf, ArrayList<OpenCondition> goals,
            Step initial, Step last, POPMultiThread planner) {
        super(planner.comm);
        this.parent = planner;
        this.solutionChecker = ((POPMultiThread) parent).getSolutionChecker();
        threadActions = actions;

        this.myAgent = conf.getAgent();

        initialStep = initial;
        finalStep = last;

        initialInternalPlan = new POPInternalPlan(null, null, null, null, goals, null, null, false, this);
        this.initialIncrementalPlan = new POPIncrementalPlan(initialInternalPlan, null, this);

        this.successors = new ArrayList<>();

        initialIncrementalPlan.setName(0, null);
        initializeArrays();

        this.matrix = new POPMatrix(20);
    }

    /**
     * Starts the thread.
     *
     * @since 1.0
     */
    @Override
    public void run() {
        threadRefinements = POPForwardLoop();
    }

    /**
     * Sets the current internal plan.
     *
     * @param p Current internal plan
     * @since 1.0
     */
    public void setCurrentInternalPlan(POPInternalPlan p) {
        currentInternal = p;
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
        POPInternalPlan auxInternal;
        POPStep step;
        currentInternal = new POPInternalPlan(currentInternal, this);
        auxInternal = currentInternal;
        initialInternalPlan.setNumSteps(-1);

        //Synchronize class information
        initialInternalPlan.setNumSteps(antecessors.length);
        calculateCausalLinks(((POPMultiThread) parent).getBasePlan(), antecessors);
        calculateOrderings(((POPMultiThread) parent).getBasePlan(), antecessors);

        //Search loop; add an applicable action to the plan
        for (POPAction act : threadActions) {
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
     * Initializes the search.
     *
     * @param p Current internal plan
     * @since 1.0
     */
    public void initializeSearchTree(POPInternalPlan p) {
        this.internalSearchTree = new POPInternalSearchTree(p);
    }

    /**
     * Sets the ancestor plans of the current one.
     *
     * @param ant Array of ancestor plans
     * @since 1.0
     */
    public void setAntecessors(POPIncrementalPlan[] ant) {
        antecessors = new POPIncrementalPlan[ant.length];
        for (int i = 0; i < ant.length; i++) {
            antecessors[i] = ant[i];
        }
    }

    /**
     * Returns the computes plan refinements.
     *
     * @return List of refinements
     * @since 1.0
     */
    public ArrayList<IPlan> getRefinements() {
        return this.threadRefinements;
    }

    /**
     * Clears the arrays to store orderings and causal links.
     *
     * @since 1.0
     */
    public final void initializeArrays() {
        totalCausalLinks = new CustomArrayList<>(50);
        totalOrderings = new CustomArrayList<>(50);
    }

    /**
     * Adds all the causal links when expanding a plan.
     *
     * @param base Base plan
     * @param antecessors Array of the base plan ancestors
     * @since 1.0
     */
    public void calculateCausalLinks(POPIncrementalPlan base, POPIncrementalPlan[] antecessors) {
        //The base plan does not include any causal links
        this.getTotalCausalLinks().clear();
        if (!base.isRoot()) {
            POPIncrementalPlan aux = base;
            while (!aux.isRoot()) {
                for (CausalLink c : aux.getCausalLinks()) {
                    this.getTotalCausalLinks().add(c);
                }
                aux = aux.getFather();
            }
        }
        this.setNumCausalLinks(this.getTotalCausalLinks().size());
        this.setModifiedCausalLinks(false);
    }

    /**
     * Adds all the orderings when expanding a plan.
     *
     * @param base Base plan
     * @param antecessors Array of the base plan ancestors
     * @since 1.0
     */
    public void calculateOrderings(POPIncrementalPlan base, POPIncrementalPlan[] antecessors) {
        //The base plan does not include any orderings
        this.getTotalOrderings().clear();
        if (!base.isRoot()) {
            POPIncrementalPlan aux = base;
            while (!aux.isRoot()) {
                for (Ordering o : aux.getOrderings()) {
                    this.getTotalOrderings().add(o);
                }
                aux = aux.getFather();
            }
        }
        this.setNumOrderings(this.getTotalOrderings().size());
        this.setModifiedOrderings(false);
    }

    /**
     * Clears the list of actions.
     *
     * @since 1.0
     */
    void clearThreadActions() {
        this.threadActions.clear();
    }

    /**
     * Adds an applicable action to the list.
     *
     * @param pa Action
     * @since 1.0
     */
    void addApplicableAction(POPAction pa) {
        this.threadActions.add(pa);
    }

    /**
     * Proposals sending simulation for single-agent tasks. Not used.
     *
     * @param proposals List of plan proposals to send
     * @param basePlan Current base plan
     * @return Solution plan if found; <code>null</code>, otherwise
     * @since 1.0
     */
    @Override
    public IPlan sendProposalsMonoagent(ArrayList<IPlan> proposals, IPlan basePlan) {
        return null;
    }

    /**
     * Plan evaluation. Not used.
     *
     * @param plan Plan to be evaluated
     * @param evThreads List of evaluation threads
     * @since 1.0
     */
    @Override
    public void evaluatePlan(IPlan plan, ArrayList<EvaluationThread> evThreads) {
    }

    /**
     * Sets the ancestor plans for a given plan. Not used.
     *
     * @param nextPlan Plan
     * @since 1.0
     */
    @Override
    public void setAntecessors(POPIncrementalPlan nextPlan) {
    }

}
