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

import java.io.Serializable;
import java.util.ArrayList;
import java.util.BitSet;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_planner.CausalLink;
import org.agreement_technologies.common.map_planner.Condition;
import org.agreement_technologies.common.map_planner.OpenCondition;
import org.agreement_technologies.common.map_planner.Ordering;
import org.agreement_technologies.common.map_planner.PlannerFactory;
import org.agreement_technologies.common.map_planner.Step;

/**
 * Serializable class to send/receive plan proposals to/from other agents.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class ProposalToSend implements Serializable {

    // Serial number for serialization
    private static final long serialVersionUID = 6509357846584167L;
    private ArrayList<PCausalLink> causalLinks; // New causal links
    private ArrayList<POrdering> orderings;     // New orderings
    private PStep step;                         // New step
    private boolean isSolution;         // Indicates if this plan is a solution
    private boolean repeatedState;      // Indicates if this plan leads to a repeated state
    private int h, hLand;               // Heuristic values (DTG and LAND) for this plan
    private BitSet achievedLandmarks;   // Set of achieved landmarks

    /**
     * Builds a plan proposal to sent to the given agent.
     *
     * @param prop	Plan to send
     * @param ag	Destination agent
     * @param repeated Indicates if this plan leads to a repeated state
     * @since 1.0
     */
    public ProposalToSend(InternalProposal prop, String ag, boolean repeated) {
        repeatedState = repeated;
        causalLinks = new ArrayList<>();
        orderings = new ArrayList<>();
        POPIncrementalPlan plan = (POPIncrementalPlan) prop.plan;
        for (CausalLink c : plan.getCausalLinks()) {
            causalLinks.add(new PCausalLink(c));
        }
        for (Ordering o : plan.getOrderings()) {
            orderings.add(new POrdering(o));
        }
        step = new PStep(plan.getStep());
        isSolution = plan.isSolution();
        h = plan.getH();
        hLand = plan.getHLan();
        achievedLandmarks = prop.achievedLandmarks;
    }

    /**
     * Gets the set of achieved landmarks.
     *
     * @return Set of achieved landmarks
     * @since 1.0
     */
    public BitSet getAchievedLandmarks() {
        return achievedLandmarks;
    }

    /**
     * Indicates if this plan leads to a repeated state.
     *
     * @return <code>true</code>, if the plan leads to a repeated state;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean isRepeated() {
        return repeatedState;
    }

    /**
     * Translates the new (serializable) step of this plan into a step.
     *
     * @param configuration Planner factory
     * @return Step
     * @since 1.0
     */
    public Step getStep(PlannerFactoryImp configuration) {
        return step.toStep(configuration);
    }

    /**
     * Gets the list of orderings in this proposal.
     *
     * @param configuration Planner factory
     * @return List of orderings
     * @since 1.0
     */
    public ArrayList<Ordering> getOrderings(PlannerFactoryImp configuration) {
        ArrayList<Ordering> o = new ArrayList<>(orderings.size());
        for (POrdering po : orderings) {
            o.add(po.toOrdering(configuration));
        }
        return o;
    }

    /**
     * Gets the list of causal links in this proposal.
     *
     * @param configuration Planner factory
     * @param basePlan Base plan
     * @param newStep New added step
     * @param orderings List of orderings
     * @return Array of causal links
     */
    public CausalLink[] getCausalLinks(PlannerFactoryImp configuration,
            POPIncrementalPlan basePlan, Step newStep, ArrayList<Ordering> orderings) {
        ArrayList<CausalLink> acl = new ArrayList<>();
        CausalLink cl;
        for (PCausalLink pcl : causalLinks) {
            if (pcl != null) {
                cl = pcl.toCausalLink(configuration, basePlan, newStep);
                if (cl != null) {
                    acl.add(cl);
                } else {	// Add as ordering
                    orderings.add(configuration.createOrdering(pcl.step1, pcl.step2));
                }
            }
        }
        return acl.toArray(new CausalLink[acl.size()]);
    }

    /**
     * Indicates if this proposal is a solution plan.
     *
     * @return <code>true</code>, if this proposal is a solution plan;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean isSolution() {
        return isSolution;
    }

    /**
     * Gets the DTG heuristic value of this proposal.
     *
     * @return DTG heuristic value
     * @since 1.0
     */
    public int getH() {
        return h;
    }

    /**
     * Gets the landmarks heuristic value of this proposal.
     *
     * @return Landmarks heuristic value
     * @since 1.0
     */
    public int getHLand() {
        return hLand;
    }

    /**
     * Serializable class to send/receive grounded conditions.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class PGroundedCond implements Serializable {

        // Serial number for serialization
        private static final long serialVersionUID = -425234291857601218L;
        private int var;        // Variable index
        private int value;      // Value index
        private int condition;  // Condition type (EQUAL or DISTINCT)

        /**
         * Creates a new serializable condition.
         *
         * @param cond Condition
         * @since 1.0
         */
        public PGroundedCond(Condition cond) {
            var = cond.getVarCode();
            value = cond.getValueCode();
            condition = cond.getType();
        }

        /**
         * Translates this serializable condition into a condition.
         *
         * @return Condition
         * @since 1.0
         */
        public Condition toCondition() {
            return new POPCondition(condition, var, value);
        }

        /**
         * Gets a description of this condition.
         *
         * @return Condition description
         */
        @Override
        public String toString() {
            String res = condition == GroundedCond.EQUAL ? "=" : "<>";
            return var + res + value;
        }
    }

    /**
     * Serializable class to send/receive open conditions.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class POpenCondition implements Serializable {

        // Serial number for serialization
        private static final long serialVersionUID = 7396924233555014626L;
        private int stepIndex;          // Index of the step with this precondition
        private PGroundedCond cond;     // Open condition

        /**
         * Creates a new serializable open condition.
         *
         * @param oc Open condition
         * @since 1.0
         */
        public POpenCondition(OpenCondition oc) {
            stepIndex = oc.getStep().getIndex();
            cond = new PGroundedCond(oc.getCondition());
        }

        /**
         * Gets a description of this open condition.
         *
         * @return Open condition description
         */
        @Override
        public String toString() {
            return "[" + stepIndex + "] " + cond;
        }
    }

    /**
     * Serializable class to send/receive causal links.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class PCausalLink implements Serializable {

        // Serial number for serialization
        private static final long serialVersionUID = -7424617979375788553L;
        private int step1, step2;       // First and second step
        private PGroundedCond cond;     // Condition of the causal link

        /**
         * Creates a new serializable causal link.
         *
         * @param c Causal link
         * @since 1.0
         */
        public PCausalLink(CausalLink c) {
            step1 = c.getIndex1();
            step2 = c.getIndex2();
            cond = new PGroundedCond(c.getCondition());
        }

        /**
         * Translates this serializable open condition into an ordering.
         *
         * @param pf Planner factory
         * @return Ordering
         * @since 1.0
         */
        public Ordering toOrdering(PlannerFactory pf) {
            return pf.createOrdering(step1, step2);
        }

        /**
         * Translates this serializable open condition into a causal link.
         *
         * @param pf Planner factory
         * @param basePlan Base plan
         * @param newStep New step added to the base plan
         * @return Causal link
         * @since 1.0
         */
        public CausalLink toCausalLink(PlannerFactoryImp pf, POPIncrementalPlan basePlan,
                Step newStep) {
            Condition gc = cond.toCondition();
            Step s1 = step1 == 0 ? basePlan.getInitialStep() : findStep(step1, basePlan);
            Step s2 = newStep != null ? newStep : basePlan.getFinalStep();
            return pf.createCausalLink(gc, s1, s2);
        }

        /**
         * Finds a step in a given plan.
         *
         * @param s Index of the step to find
         * @param basePlan Plan to search in
         * @return Step found
         * @since 1.0
         */
        private static Step findStep(int s, POPIncrementalPlan basePlan) {
            if (basePlan.getStep().getIndex() == s) {
                return basePlan.getStep();
            }
            return findStep(s, basePlan.getFather());
        }
    }

    /**
     * Serializable class to send/receive orderings.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class POrdering implements Serializable {

        // Serial number for serialization
        private static final long serialVersionUID = 4213546490197217271L;
        private final int step1, step2;     // First and second steps of the ordering

        /**
         * Creates a new serializable ordering from a causal link.
         *
         * @param c Causal link
         * @since 1.0
         */
        public POrdering(CausalLink c) {
            step1 = c.getIndex1();
            step2 = c.getIndex2();
        }

        /**
         * Translates this serializable ordering into an ordering.
         *
         * @param pf Planner factory
         * @return Translated ordering
         * @since 1.0
         */
        public Ordering toOrdering(PlannerFactory pf) {
            return pf.createOrdering(step1, step2);
        }

        /**
         * Creates a new serializable ordering from an ordering.
         *
         * @param o Ordering
         * @since 1.0
         */
        public POrdering(Ordering o) {
            step1 = o.getIndex1();
            step2 = o.getIndex2();
        }

        /**
         * Checks if two orderings are equal.
         *
         * @param x Another ordering to compare with
         * @return <code>true</code>, if both orderings are equal;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            POrdering po = (POrdering) x;
            return step1 == po.step1 && step2 == po.step2;
        }
    }

    /**
     * Serializable class to send/receive plan steps.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class PStep implements Serializable {

        // Serializable number for serialization
        private static final long serialVersionUID = 2695531841107912873L;
        private final int index;        // Step index
        private String agent;           // Executor agent
        private String actionName;      // Action name
        PGroundedCond prec[], eff[];    // Action preconditions and effecs

        /**
         * Creates a new serializable step.
         *
         * @param step Step
         * @since 1.0
         */
        public PStep(Step step) {
            if (step != null) {
                index = step.getIndex();
                agent = step.getAgent();
                actionName = step.getActionName();
                ArrayList<PGroundedCond> aPrecs = new ArrayList<>();
                for (Condition cond : step.getPrecs()) {
                    aPrecs.add(new PGroundedCond(cond));
                }
                ArrayList<PGroundedCond> aEffs = new ArrayList<>();
                for (Condition eff : step.getEffs()) {
                    aEffs.add(new PGroundedCond(eff));
                }
                prec = aPrecs.toArray(new PGroundedCond[aPrecs.size()]);
                eff = aEffs.toArray(new PGroundedCond[aEffs.size()]);
            } else {
                index = -1;
            }
        }

        /**
         * Translates this serializable step into a step.
         *
         * @param pf Planner factory
         * @return Translated step
         * @since 1.0
         */
        public Step toStep(PlannerFactoryImp pf) {
            if (index == -1) {
                return null;
            }
            ArrayList<Condition> sPrec = new ArrayList<>(prec.length);
            ArrayList<Condition> sEff = new ArrayList<>(eff.length);
            for (int i = 0; i < prec.length; i++) {
                sPrec.add(prec[i].toCondition());
            }
            for (int i = 0; i < eff.length; i++) {
                sEff.add(eff[i].toCondition());
            }
            return pf.createStep(index, agent, actionName,
                    sPrec.toArray(new Condition[sPrec.size()]),
                    sEff.toArray(new Condition[sEff.size()]));
        }
    }

}
