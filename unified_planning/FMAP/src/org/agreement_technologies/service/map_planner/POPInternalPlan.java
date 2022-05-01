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

import org.agreement_technologies.common.map_planner.ExtendedPlanner;
import java.util.ArrayList;
import java.util.Iterator;
import org.agreement_technologies.common.map_planner.CausalLink;
import org.agreement_technologies.common.map_planner.OpenCondition;
import org.agreement_technologies.common.map_planner.Ordering;
import org.agreement_technologies.common.map_planner.Step;
import org.agreement_technologies.service.tools.CustomArrayList;

/**
 * Internal incremental plan to calculate a refinement over a parent plan.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPInternalPlan implements Cloneable {

    private final ExtendedPlanner POP;                  // Reference to the planner
    private final POPInternalPlan father;               // Parent plan
    private final POPStep step;                         // Added step
    private final POPCausalLink causalLink;             // Added causal link
    private ArrayList<OpenCondition> openConditions;    // List of open conditions
    private ArrayList<POPThreat> threats;               // List of threats
    private POPOrdering ordering;                       // Added ordering
    private int steps;                                  // Number of steps in the plan

    /**
     * Generic constructor for solving preconditions, with a new step or with an
     * existing one, and threats.
     *
     * @param basePlan Parent plan
     * @param newStep Added step
     * @param newLink Added causal link
     * @param newOrdering Added ordering
     * @param precs List of open conditions
     * @param thre List of threats
     * @param solvedPrec Solved open condition
     * @param supportFinalStep Indicates if the final step is supported in the
     * plan
     * @param planner Reference to the planner
     * @since 1.0
     */
    POPInternalPlan(POPInternalPlan basePlan, POPStep newStep, POPCausalLink newLink,
            POPOrdering newOrdering, ArrayList<OpenCondition> precs,
            ArrayList<POPThreat> thre, OpenCondition solvedPrec,
            boolean supportFinalStep, ExtendedPlanner planner) {
        POP = planner;

        if (POP.getAntecessors() != null) {
            steps = POP.getAntecessors().length + 2;
            if (supportFinalStep) {
                steps--;
            }
        } else {
            steps = -1;
        }

        this.father = basePlan;
        this.step = newStep;
        this.causalLink = newLink;
        if (causalLink == null) {
            this.ordering = newOrdering;
        }
        this.threats = new ArrayList<>();

        if (precs != null) {
            this.openConditions = new ArrayList<>(precs.size());
        }

        // Add all the preconditions except for the solved one (if any)
        Iterator<OpenCondition> it = null;
        if (basePlan != null) {
            if (basePlan.getPreconditions() != null) {
                it = basePlan.getPreconditions().iterator();
            }
        }
        if (it == null) {
            if (precs != null) {
                for (OpenCondition o : precs) {
                    this.openConditions.add(o);
                }
            }
        } else {
            POPOpenCondition prec;
            while (it.hasNext()) {
                prec = (POPOpenCondition) it.next();
                // If the current precondition is not the solved one, store it in the child plan
                // If the current precondition is the solved one but the steps are different, store it in the child plan
                if ((solvedPrec != null && prec.getCondition() != ((POPOpenCondition) solvedPrec).getCondition())
                        || (solvedPrec != null && prec.getCondition() == ((POPOpenCondition) solvedPrec).getCondition() && prec.getStep().getIndex() != solvedPrec.getStep().getIndex())
                        || solvedPrec == null) {
                    this.openConditions.add(prec);
                }
            }
        }

        // Add all the preconditions corresponding to the new step (if any)
        if (newStep != null) {
            for (POPPrecEff pe : newStep.getAction().getPrecs()) {
                if (!pe.getCondition().toString().equals(solvedPrec.getCondition().toString())) // Mark the new preconditions as subgoals (in MAP is necessary, but not in single-agent)
                {
                    this.openConditions.add(new POPOpenCondition(pe, newStep, true));
                }
            }
        }

        // Add all the threats that we have not solved
        if (thre != null) {
            for (int i = 0; i < thre.size(); i++) {
                this.threats.add(thre.get(i));
            }
        }
    }

    /**
     * Makes a copy of this plan.
     *
     * @return Copy of this plan
     * @since 1.0
     */
    @Override
    public Object clone() {
        POPInternalPlan c = new POPInternalPlan(null, null, null, null, null, null, null, false, this.POP);

        ArrayList<OpenCondition> precs = new ArrayList<>(this.getPreconditions().size());
        for (OpenCondition p : this.getPreconditions()) {
            precs.add((POPOpenCondition) p);
        }
        c.setPreconditions(precs);

        return c;
    }

    /**
     * Gets a reference to the planner.
     *
     * @return Planner reference
     * @since 1.0
     */
    public ExtendedPlanner getPlanner() {
        return POP;
    }

    /**
     * Sets the list of open conditions.
     *
     * @param p List of open conditions
     * @since 1.0
     */
    public void setPreconditions(ArrayList<OpenCondition> p) {
        this.openConditions = p;
    }

    /**
     * Gets the list of open conditions.
     *
     * @return List of open conditions
     * @since 1.0
     */
    public ArrayList<OpenCondition> getPreconditions() {
        return this.openConditions;
    }

    /**
     * Gets the list of threats.
     *
     * @return List of threats
     * @since 1.0
     */
    public ArrayList<POPThreat> getThreats() {
        return this.threats;
    }

    /**
     * Gets the parent plan.
     *
     * @return Parent plan
     * @since 1.0
     */
    public POPInternalPlan getFather() {
        return this.father;
    }

    /**
     * Gets the added ordering.
     *
     * @return Added ordering
     * @since 1.0
     */
    public POPOrdering getOrdering() {
        return this.ordering;
    }

    /**
     * Gets the added step.
     *
     * @return Added step
     * @since 1.0
     */
    public POPStep getStep() {
        return this.step;
    }

    /**
     * Gets the added causal link.
     *
     * @return Added causal link
     * @since 1.0
     */
    public POPCausalLink getCausalLink() {
        return this.causalLink;
    }

    /**
     * Sets the added ordering.
     *
     * @param v1 Index of the first step
     * @param v2 Index of the second step
     * @since 1.0
     */
    public void setOrdering(int v1, int v2) {
        this.ordering = new POPOrdering(v1, v2);
    }

    /**
     * Sets the total number of steps in the plan.
     *
     * @param n Total number of steps in the plan
     * @since 1.0
     */
    public void setNumSteps(int n) {
        steps = n;
    }

    /**
     * Gets the final step.
     *
     * @return Final step
     * @since 1.0
     */
    public Step getFinalStep() {
        return POP.getFinalStep();
    }

    /**
     * Adds a new threat.
     *
     * @param v New threat
     * @since 1.0
     */
    public void addThreats(ArrayList<POPThreat> v) {
        for (POPThreat t : v) {
            this.threats.add(t);
        }
    }

    /**
     * Removes the threats and initializes the list of open conditions.
     *
     * @param oc List of open conditions
     * @since 1.0
     */
    public void restorePlan(ArrayList<OpenCondition> oc) {
        threats = new ArrayList<>();
        openConditions = new ArrayList<>();
        for (OpenCondition o : oc) {
            openConditions.add(o);
        }
    }

    /**
     * Removes the threats and the open conditions.
     *
     * @since 1.0
     */
    public void cleanPlan() {
        this.openConditions = null;
        this.threats = null;
    }

    /**
     * Gets a description of this plan.
     *
     * @return Plan description
     * @since 1.0
     */
    @Override
    public String toString() {
        String res = "";
        res += "Precs: " + this.openConditions.size() + "\n";
        res += "Threats: " + this.threats.size();

        return res;
    }

    /**
     * Gets a step in the plan by its index.
     *
     * @param index Step index
     * @return Plan step
     * @since 1.0
     */
    public Step getStep(int index) {
        if (index == 0) {
            return POP.getInitialStep();
        }
        if (index == 1) {
            return POP.getFinalStep();
        }

        if (this.isRoot() || index <= numSteps() - 2) {
            return POP.getAntecessors()[index - 1].getStep();
        }

        POPInternalPlan aux = this;
        while (!aux.isRoot()) {
            if (aux.step != null) {
                return aux.step;
            }
            aux = aux.father;
        }

        if (POP.getAntecessors()[POP.getAntecessors().length - 1].getStep().getIndex() == index) {
            return POP.getAntecessors()[POP.getAntecessors().length - 1].getStep();
        }

        return null;
    }

    /**
     * Gets the list of open conditions.
     *
     * @return List of open conditions
     * @since 1.0
     */
    public ArrayList<OpenCondition> getTotalOpenConditions() {
        return this.openConditions;
    }

    /**
     * Gets the full list of internal causal links in the plan.
     *
     * @param cl Array to store the causal links in
     * @since 1.0
     */
    public void getInternalCausalLinks(CausalLink[] cl) {
        POPInternalPlan p = this;
        int i = cl.length - 1;

        if (this.causalLink != null) {
            cl[i] = causalLink;
            i--;
        }
        while (p.father != null) {
            p = p.father;
            if (p.causalLink != null) {
                cl[i] = p.causalLink;
                i--;
            }
        }
    }

    /**
     * Adds the modified causal links to the current plan.
     *
     * @since 1.0
     */
    public void addCausalLinks() {
        if (!POP.getModifiedCausalLinks()) {
            POPInternalPlan p = this;

            if (this.causalLink != null) {
                POP.addCausalLink(causalLink);
            }
            while (p.father != null) {
                p = p.father;
                if (p.causalLink != null) {
                    POP.addCausalLink(p.causalLink);
                }
            }
            POP.setModifiedCausalLinks(true);
        }
    }

    /**
     * Gets the full list of internal orderings in the plan.
     *
     * @return List of orderings
     * @since 1.0
     */
    public ArrayList<Ordering> getInternalOrderings() {
        ArrayList<Ordering> or = new ArrayList<>(3);
        POPInternalPlan p = this;

        if (this.ordering != null) {
            or.add(ordering);
        }
        while (p.father != null) {
            p = p.father;
            if (p.ordering != null) {
                or.add(p.ordering);
            }
        }
        return or;
    }

    /**
     * Adds the modified orderings to the current plan.
     *
     * @since 1.0
     */
    public void addOrderings() {
        if (!POP.getModifiedOrderings()) {
            POPInternalPlan p = this;

            if (this.ordering != null) {
                POP.addOrdering(ordering);
            }
            while (p.father != null) {
                p = p.father;
                if (p.ordering != null) {
                    POP.addOrdering(p.ordering);
                }
            }
            POP.setModifiedOrderings(true);
        }
    }

    /**
     * Gets the full list of causal links in the plan.
     *
     * @return List of causal links
     * @since 1.0
     */
    public CustomArrayList<CausalLink> getTotalCausalLinks() {
        return POP.getTotalCausalLinks();
    }

    /**
     * Gets the full list of orderings in the plan.
     *
     * @return List of causal links
     * @since 1.0
     */
    public CustomArrayList<Ordering> getTotalOrderings() {
        return POP.getTotalOrderings();
    }

    /**
     * Returns the number of steps of the plan.
     *
     * @return Number of steps
     * @since 1.0
     */
    public int numSteps() {
        if (steps == -1) {
            steps = POP.getAntecessors().length + 1;
        }

        return steps;
    }

    /**
     * Verifies if the plan is at the root of the search tree.
     *
     * @return <code>true</code>, if the plan has no ancestors;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean isRoot() {
        return father == null;
    }

    /**
     * Checks if the plan is a solution.
     *
     * @return <code>true</code>, if the plan is a solution for the task;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean isSolution() {
        if (step != null && step.getIndex() == 1) {
            return true;
        }
        if (isRoot()) {
            return false;
        }
        return father.isSolution();
    }

    /**
     * Gets the last added step.
     *
     * @return Last added step
     * @since 1.0
     */
    Step getLatestStep() {
        POPInternalPlan aux = this;
        while (aux != null && aux.step == null) {
            aux = aux.father;
        }
        if (aux == null && this.isRoot()) {
            return POP.getAntecessors()[POP.getAntecessors().length - 1].getStep();
        }
        if (aux == null) {
            return this.step;
        }

        return aux.step;
    }

    /**
     * Creates a new internal plan from another one.
     *
     * @param original Original internal plan
     * @param thread Planner reference
     * @since 1.0
     */
    POPInternalPlan(POPInternalPlan original, ExtendedPlanner thread) {
        POP = thread;
        father = original.father;
        step = original.step;
        causalLink = original.causalLink;
        openConditions = original.openConditions;
        threats = original.threats;
        ordering = original.ordering;
        steps = original.steps;
    }

}
