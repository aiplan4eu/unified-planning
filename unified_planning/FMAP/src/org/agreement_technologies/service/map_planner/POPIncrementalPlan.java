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
import java.util.HashMap;
import java.util.Hashtable;
import org.agreement_technologies.common.map_planner.CausalLink;
import org.agreement_technologies.common.map_planner.Condition;
import org.agreement_technologies.common.map_planner.ExtendedPlanner;
import org.agreement_technologies.common.map_planner.IPlan;
import org.agreement_technologies.common.map_planner.Ordering;
import org.agreement_technologies.common.map_planner.Plan;
import org.agreement_technologies.common.map_planner.PlannerFactory;
import org.agreement_technologies.common.map_planner.Step;
import org.agreement_technologies.service.tools.CustomArrayList;

/**
 * Incremental plans for the external search tree; each plan stores a new action
 * w.r.t. its father.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPIncrementalPlan implements IPlan {

    private String name;                    // Plan name
    private POPIncrementalPlan father;      // Parent plan
    private Step step;                      // Step that this plan adds w.r.t. its parent plan
    private ArrayList<Ordering> orderings;  // Orderings that this plan adds w.r.t. its parent plan
    private CausalLink[] causalLinks;       // Causal links that this plan adds w.r.t. its parent plan
    private int g;                  // Plan depth in the search tree
    private int h;                  // Plan heuristic value
    private int hPriv[];            // Private heuristic values of this plan
    private int hLan;               // Landmarks heuristic value of this plan
    private int numSteps;           // Total number of steps in this plan
    private double metric;          // Metric value of this plan
    private int[] totalOrder;       // Step indexes sorted in a topological order
    private ExtendedPlanner POP;    // Reference to the planner
    private boolean isSolution;     // Indicates if this plan is a solution plan

    /**
     * Creates a new incremental plan from an internal plan.
     *
     * @param p Internal plan
     * @param prev Parent plan
     * @param planner Reference to the planner
     * @since 1.0
     */
    public POPIncrementalPlan(POPInternalPlan p, POPIncrementalPlan prev,
            ExtendedPlanner planner) {
        POP = planner;
        father = prev;
        if (prev != null) {
            step = p.getLatestStep();
            numSteps = father.numSteps + 1;
        } // Root
        else {
            step = POP.getInitialStep();
            numSteps = 2;
        }
        isSolution = false;
        orderings = p.getInternalOrderings();
        if (step == null && prev != null) {
            step = POP.getFinalStep();
            numSteps--;
            isSolution = true;
        }
        if (step != null) {
            causalLinks = new CausalLink[step.getPrecs().length];
            p.getInternalCausalLinks(causalLinks);
        }
        totalOrder = null;
        hPriv = null;
    }

    /**
     * Build a plan with the information included in the proposal.
     *
     * @param pp PlanProposal
     * @param basePlan Base plan
     * @param configuration Planner factory
     * @param planner Reference to the planner
     * @since 1.0
     */
    public POPIncrementalPlan(ProposalToSend pp, IPlan basePlan,
            PlannerFactoryImp configuration, ExtendedPlanner planner) {
        POP = planner;
        father = (POPIncrementalPlan) basePlan;
        h = pp.getH();
        hLan = pp.getHLand();
        g = father.g + 1;
        step = pp.getStep(configuration);
        numSteps = father.numSteps + (step != null ? 1 : 0);
        orderings = pp.getOrderings(configuration);
        causalLinks = pp.getCausalLinks(configuration, father, step, orderings);
        isSolution = pp.isSolution();
        totalOrder = null;
        metric = -1;
        hPriv = null;
    }

    /**
     * Constructor for plan searching.
     *
     * @param planName Plan name
     * @since 1.0
     */
    public POPIncrementalPlan(String planName) {
        name = planName;
        totalOrder = null;
    }

    /**
     * Adds all the causal links when expanding a plan.
     * 
     * @since 1.0
     */
    public void calculateCausalLinks() {
        // The base plan does not include any causal links
        POP.getTotalCausalLinks().clear();
        if (!this.isRoot()) {
            POPIncrementalPlan aux = this;
            while (!aux.isRoot()) {
                for (CausalLink c : aux.getCausalLinks()) {
                    POP.getTotalCausalLinks().add(c);
                }
                aux = aux.father;
            }
        }
        POP.setNumCausalLinks(POP.getTotalCausalLinks().size());
        POP.setModifiedCausalLinks(false);
    }

    /**
     * Adds all the causal links when expanding a plan.
     * 
     * @since 1.0
     */
    public void calculateOrderings() {
        // The base plan does not include any causal links
        POP.getTotalOrderings().clear();
        if (!this.isRoot()) {
            POPIncrementalPlan aux = this;
            while (!aux.isRoot()) {
                for (Ordering o : aux.getOrderings()) {
                    POP.getTotalOrderings().add(o);
                }
                aux = aux.father;
            }
        }
        POP.setNumOrderings(POP.getTotalOrderings().size());
        POP.setModifiedOrderings(false);
    }

    /**
     * Gets the list of causal links that this plan adds w.r.t. its parent plan.
     *
     * @return Array of causal links that this plan adds w.r.t. its parent plan
     * @since 1.0
     */
    public CausalLink[] getCausalLinks() {
        return this.causalLinks;
    }

    /**
     * Gets the list of orerings that this plan adds w.r.t. its parent plan.
     *
     * @return Array of orerings that this plan adds w.r.t. its parent plan
     * @since 1.0
     */
    public ArrayList<Ordering> getOrderings() {
        return this.orderings;
    }

    /**
     * Gets the step added in this plan.
     *
     * @return Added step
     * @since 1.0
     */
    public Step getStep() {
        return this.step;
    }

    /**
     * Gets the parent plan.
     *
     * @return Parent plan
     * @since 1.0
     */
    @Override
    public POPIncrementalPlan getFather() {
        return this.father;
    }

    /**
     * Gets the full list of causal links in the plan.
     *
     * @return List of causal links in the plan
     * @since 1.0
     */
    @Override
    public CustomArrayList<CausalLink> getTotalCausalLinks() {
        return POP.getTotalCausalLinks();
    }

    /**
     * Gets the full list of steps in the plan.
     *
     * @return List of steps in the plan
     * @since 1.0
     */
    @Override
    public ArrayList<Step> getTotalSteps() {
        ArrayList<Step> st = new ArrayList<>();
        POPIncrementalPlan aux = this;
        int bound;

        // st.add(aux.step);
        while (!aux.isRoot()) {
            if (aux.step != null) {
                st.add(aux.step);
            }
            aux = aux.father;
        }

        ArrayList<Step> sti = new ArrayList<>(st.size() + 2);
        sti.add(POP.getInitialStep());
        sti.add(POP.getFinalStep());
        if (st.get(0).getIndex() == 1) {
            bound = 1;
        } else {
            bound = 0;
        }
        for (int i = st.size() - 1; i >= bound; i--) {
            sti.add(st.get(i));
        }

        return sti;
    }

    /**
     * If a metric is defined, returns the metric value.
     *
     * @return Metric value of the plan
     * @since 1.0
     */
    @Override
    public double getMetric() {
        if (metric == -1) {
            metric = ((Planner) POP).evaluateMetric(this);
        }

        return metric;
    }

    /**
     * Gets the full list of orderings in the plan.
     *
     * @return List of orderings in the plan
     * @since 1.0
     */
    @Override
    public CustomArrayList<Ordering> getTotalOrderings() {
        return POP.getTotalOrderings();
    }

    /**
     * Retrieves the initial step of the plan.
     *
     * @return Initial step
     * @since 1.0
     */
    @Override
    public Step getInitialStep() {
        return POP.getInitialStep();
    }

    /**
     * Retrieves the final step of the plan.
     *
     * @return Final step
     * @since 1.0
     */
    @Override
    public Step getFinalStep() {
        return POP.getFinalStep();
    }

    /**
     * Checks if the plan is a solution.
     *
     * @return <code>true</code>, if the plan is a solution for the task;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean isSolution() {
        return isSolution;
    }

    /**
     * Returns the number of steps of the plan, excluding the initial and final
     * actions.
     *
     * @return Number of steps
     * @since 1.0
     */
    @Override
    public int numSteps() {
        return numSteps;
    }

    /**
     * Gets the name of the plan.
     *
     * @return Plan name
     * @since 1.0
     */
    @Override
    public String getName() {
        return this.name;
    }

    /**
     * Sets the name for this plan.
     *
     * @param n Child index (children plans are numbered from zero)
     * @param father Parent plan
     * @since 1.0
     */
    @Override
    public void setName(int n, Plan father) {
        if (isRoot()) {
            this.name = "\u03A0" + "0";
        } else {
            this.name = this.father.getName() + "-" + n;
        }
    }

    /**
     * Sets g value of the plan.
     *
     * @param g g value
     * @since 1.0
     */
    @Override
    public void setG(int g) {
        this.g = g;
    }

    /**
     * Verifies if the plan is at the root of the search tree.
     *
     * @return <code>true</code>, if the plan has no ancestors;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean isRoot() {
        return father == null;
    }

    /**
     * Gets g value (number of steps of the plan).
     *
     * @return g value
     * @since 1.0
     */
    @Override
    public int getG() {
        return g;
    }

    /**
     * Gets h value (obtained through heuristic calculations).
     *
     * @return h value
     * @since 1.0
     */
    @Override
    public int getH() {
        return h;
    }

    /**
     * Gets a description of this plan.
     *
     * @return Plan description
     */
    @Override
    public String toString() {
        String res = this.name + " (H=" + this.h + ",Hl=" + this.hLan + ",Hp=";
        if (hPriv == null || hPriv.length == 0) {
            res += "none";
        } else {
            res += hPriv[0];
            for (int i = 1; i < hPriv.length; i++) {
                res += "," + hPriv[i];
            }
        }
        return res + ")";
    }

    /**
     * Generates an array that contains all the causal links of the plan.
     *
     * @return Causal links array
     * @since 1.0
     */
    @Override
    public ArrayList<CausalLink> getCausalLinksArray() {
        POPIncrementalPlan aux = this;
        ArrayList<CausalLink> cl = new ArrayList<>();

        while (!aux.isRoot()) {
            if (aux.getCausalLinks() != null) {
                for (CausalLink l : aux.getCausalLinks()) {
                    cl.add(l);
                }
            }
            aux = aux.father;
        }

        return cl;
    }

    /**
     * Generates an array that contains all the steps of the plan.
     *
     * @return Steps array
     * @since 1.0
     */
    @Override
    public ArrayList<Step> getStepsArray() {
        POPIncrementalPlan aux = this;
        ArrayList<Step> s = new ArrayList<>();
        ArrayList<POPIncrementalPlan> p = new ArrayList<>();
        while (!aux.isRoot()) {
            p.add(aux);
            aux = aux.father;
        }
        s.add(POP.getInitialStep());
        s.add(POP.getFinalStep());
        for (int i = p.size() - 1; i >= 0; i--) {
            if (!p.get(i).isSolution) {
                s.add(p.get(i).getStep());
            }
        }
        return s;
    }

    /**
     * Generates an array that contains all the orderings of the plan.
     *
     * @return Orderings array
     * @since 1.0
     */
    @Override
    public ArrayList<Ordering> getOrderingsArray() {
        POPIncrementalPlan aux = this;
        ArrayList<Ordering> or = new ArrayList<>();

        while (!aux.isRoot()) {
            if (aux.getOrderings() != null) {
                for (Ordering o : aux.getOrderings()) {
                    or.add(o);
                }
            }
            aux = aux.father;
        }

        return or;
    }

    /**
     * Compares two plans by their names.
     *
     * @param x Another plan to compare with
     * @return <code>true</code>, if both plans have the same name;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean equals(Object x) {
        return ((POPIncrementalPlan) x).name.equals(name);
    }

    /**
     * Gets a hash code for this plan.
     *
     * @return Hash code
     * @since 1.0
     */
    @Override
    public int hashCode() {
        return name.hashCode();
    }

    /**
     * Gets the steps of the plan sorted in a topological order.
     *
     * @return Array of step indexes
     * @since 1.0
     */
    @Override
    public int[] linearization() {
        if (totalOrder != null) {
            return totalOrder;
        }
        int index = 0;
        totalOrder = new int[numSteps - 1];
        boolean visited[] = new boolean[numSteps];
        HashMap<Integer, ArrayList<Integer>> orderings = new HashMap<>(numSteps);
        HashMap<Integer, POPIncrementalPlan> incPlans = new HashMap<>(numSteps);
        for (POPIncrementalPlan p = this; p != null; p = p.father) {
            // Store orderings in variable "orderings" (adjacency list)
            for (Ordering o : p.orderings) {
                ArrayList<Integer> prev = orderings.get(o.getIndex2());
                if (prev == null) {
                    prev = new ArrayList<>();
                    prev.add(o.getIndex1());
                    orderings.put(o.getIndex2(), prev);
                } else if (!prev.contains(o.getIndex1())) {
                    prev.add(o.getIndex1());
                }
            }
            // incPlans stores the incremental plans that add a step to the plan
            incPlans.put(p.step.getIndex(), p);
        }
        // For each incremental plan in incPlans, call linearization (recursive method)
        for (POPIncrementalPlan p = this; p.father != null; p = p.father) {
            if (!visited[p.step.getIndex()]) {
                index = linearization(p, totalOrder, index, visited, orderings,
                        incPlans);
            }
        }
        return totalOrder;
    }

    /**
     * Calculates a linearization for a given plan.
     *
     * @param p Plan to linearize
     * @param toPlan Array to fill with the step indexes in a topological order
     * @param index Current position in the "toPlan" array
     * @param visited Indicates which steps have already been visited
     * @param orderings List of plan orderings
     * @param incPlans Mapping of generation index -> ancestor plan
     * @return Current position in the "toPlan" array
     * @since 1.0
     */
    private static int linearization(POPIncrementalPlan p, int[] toPlan,
            int index, boolean[] visited,
            HashMap<Integer, ArrayList<Integer>> orderings,
            HashMap<Integer, POPIncrementalPlan> incPlans) {
        int s = p.getStep().getIndex();
        visited[s] = true;
        // Analyze causal links s1 -<v,d>-> s2 in p by recursively calling
        // linearization over s1
        // p adds an action and supports all its preconditions through
        // previously existing actions in the plan
        for (CausalLink cl : p.causalLinks) {
            if (!visited[cl.getIndex1()]) {
                index = linearization(incPlans.get(cl.getIndex1()), toPlan,
                        index, visited, orderings, incPlans);
            }
        }
        ArrayList<Integer> prev = orderings.get(s);
        if (prev != null) {
            for (Integer s1 : prev) {
                if (!visited[s1]) {
                    index = linearization(incPlans.get(s1), toPlan, index,
                            visited, orderings, incPlans);
                }
            }
        }
        if (s != 1) {
            toPlan[index++] = s;
        }
        return index;
    }

    /**
     * Computes the resulting frontier state after the plan execution. This
     * method is used in centralized problems.
     *
     * @param totalOrder Indexes of the plan steps sorted in a topological order
     * @param pf Planner factory
     * @return Frontier state. In this structure only one value is stored for
     * each variable
     * @since 1.0
     */
    @Override
    public HashMap<String, String> computeState(int[] totalOrder,
            PlannerFactory pf) {
        HashMap<String, String> varValue = new HashMap<>();
        ArrayList<Step> stepList = getStepsArray();
        Step a;
        for (int step : totalOrder) {
            a = stepList.get(step);
            for (Condition eff : a.getEffs()) {
                String var = pf.getVarNameFromCode(eff.getVarCode());
                if (var != null) {
                    String value = pf.getValueFromCode(eff.getValueCode());
                    if (value != null) {
                        varValue.put(var, value);
                    }
                }
            }
        }
        return varValue;
    }

    /**
     * Computes the resulting frontier state after the plan execution. This
     * method is used in distributed problems.
     *
     * @param totalOrder Indexes of the plan steps sorted in a topological order
     * @param pf Planner factory
     * @return Frontier multi-state. It is a multi-state as this structure
     * allows to store several values for each variable
     * @since 1.0
     */
    @Override
    public HashMap<String, ArrayList<String>> computeMultiState(
            int[] totalOrder, PlannerFactory pf) {
        HashMap<String, ArrayList<String>> varValue = new HashMap<>();
        ArrayList<Step> stepList = getStepsArray();
        String v, value;
        Step a;
        ArrayList<String> list;
        for (int step : totalOrder) {
            a = stepList.get(step);
            for (Condition eff : a.getEffs()) {
                v = pf.getVarNameFromCode(eff.getVarCode());
                if (v != null) {
                    value = pf.getValueFromCode(eff.getValueCode());
                    if (value != null) {
                        if (varValue.containsKey(v)) {
                            list = varValue.get(v);
                            list.set(0, value);
                        } else {
                            list = new ArrayList<>();
                            list.add(value);
                            varValue.put(v, list);
                        }
                    }
                }
            }
        }
        return varValue;
    }

    /**
     * Gets the last step added to the plan.
     *
     * @return Last added step
     * @since 1.0
     */
    @Override
    public Step lastAddedStep() {
        return step;
    }

    /**
     * Counts the number of steps of the plan, except for the initial and final
     * actions.
     *
     * @return Number of steps
     * @since 1.0
     */
    @Override
    public int countSteps() {
        int n = 0;
        POPIncrementalPlan father = this;

        while (!father.isRoot()) {
            if (father.getStep() != null) {
                n++;
            }
            father = father.getFather();
        }
        // Do not count the initial step
        return n - 1;
    }

    /**
     * In preference-based planning, returns the private h value of a
     * preference.
     *
     * @param prefIndex Index of the preference
     * @return h Value of the preference
     * @since 1.0
     */
    @Override
    public int getHpriv(int prefIndex) {
        if (hPriv == null) {
            return 0;
        }
        return hPriv[prefIndex];
    }

    /**
     * In multi-heuristic mode, returns the secondary heuristic value calculated
     * through h_land heuristic in MH-FMAP.
     *
     * @return Secondary heuristic value
     * @since 1.0
     */
    @Override
    public int getHLan() {
        return hLan;
    }

    /**
     * Assigns an h value to the plan In multi-heuristic search, it sets primary
     * and secondary heuristic values.
     *
     * @param h Primary heuristic value
     * @param hLan Secondary heuristic value
     * @since 1.0
     */
    @Override
    public void setH(int h, int hLan) {
        this.h = h;
        this.hLan = hLan;
    }

    /**
     * In preference-based planning, assigns an h value to a given preference.
     *
     * @param h h value
     * @param prefIndex Index of a preference
     * @since 1.0
     */
    @Override
    public void setHPriv(int h, int prefIndex) {
        if (hPriv == null) {
            hPriv = new int[prefIndex + 1];
        } else if (hPriv.length <= prefIndex) {
            int tmp[] = new int[prefIndex + 1];
            System.arraycopy(hPriv, 0, tmp, 0, hPriv.length);
            hPriv = tmp;
        }
        hPriv[prefIndex] = h;
    }

    /**
     * Sets the metric value of this plan.
     *
     * @param metric metric value
     * @since 1.0
     */
    void setMetric(double metric) {
        this.metric = metric;
    }

    /**
     * Calculates the total number of steps in this plan.
     *
     * @return Total number of steps
     * @since 1.0
     */
    private int calculateSteps() {
        int steps = 0;
        POPIncrementalPlan father = this;
        while (father != null) {
            steps++;
            father = father.getFather();
        }

        return steps;
    }

    /**
     * Calculates the makespan of this plan.
     *
     * @return Plan makespan
     * @since 1.0
     */
    @SuppressWarnings("unchecked")
    public double computeMakespan() {
        if (this.g == 0) {
            g = this.calculateSteps();
        }

        ArrayList<Integer> adjacents[] = new ArrayList[g];
        for (int i = 0; i < adjacents.length; i++) {
            adjacents[i] = new ArrayList<>();
        }
        ArrayList<Ordering> orderings = getOrderingsArray();
        ArrayList<CausalLink> causalLinks = getCausalLinksArray();
        for (Ordering po : orderings) {
            if (!adjacents[po.getIndex1()].contains(po.getIndex2())) {
                adjacents[po.getIndex1()].add(po.getIndex2());
            }
        }
        for (CausalLink cl : causalLinks) {
            if (!adjacents[cl.getIndex1()].contains(cl.getIndex2())) {
                adjacents[cl.getIndex1()].add(cl.getIndex2());
            }
        }
        int distance[] = new int[adjacents.length];
        computeMaxDistance(0, distance, adjacents);
        if (step.getIndex() == 1) { // Final step in the plan
            return distance[1] - 1;
        } else {
            int max = 1;
            for (int i = 2; i < distance.length; i++) {
                if (distance[max] < distance[i]) {
                    max = i;
                }
            }
            return distance[max];
        }
    }

    /**
     * Calculates de maximum distance of a given step to the final step.
     *
     * @param v Current step index
     * @param distance Array to store the distances from all the steps to the
     * final step
     * @param adjacents List of adjacents to each step
     * @since 1.0
     */
    private void computeMaxDistance(int v, int distance[],
            ArrayList<Integer> adjacents[]) {
        for (Integer w : adjacents[v]) {
            if (distance[w] <= distance[v]) {
                distance[w] = distance[v] + 1;
                computeMaxDistance(w, distance, adjacents);
            }
        }
    }

    /**
     * Gets the antecessor or parent of the plan.
     *
     * @return Parent plan, or <code>null</code> if this.isRoot()
     * @since 1.0
     */
    @Override
    public Plan getParentPlan() {
        return father;
    }

    /**
     * Computes the resulting frontier state after the plan execution. This
     * method is used in centralized problems, and works with indexes instead of
     * variables and values names.
     *
     * @param totalOrder Indexes of the plan steps sorted in a topological order
     * @param numVars Number of (non-numeric) variables in the state
     * @return State. For each variable, this array stores the index of its
     * value
     * @since 1.0
     */
    @Override
    public int[] computeCodeState(int[] totalOrder, int numVars) {
        int state[] = new int[numVars];
        ArrayList<Step> stepList = getStepsArray();
        Step a;
        for (int step : totalOrder) {
            a = stepList.get(step);
            for (Condition eff : a.getEffs()) {
                state[eff.getVarCode()] = eff.getValueCode();
            }
        }
        return state;
    }

    /**
     * Prints plan information and statistics.
     *
     * @param output Output format (REGULAR, CoDMAP_CENTRALIZED or
     * CoDMAP_DISTRIBUTED)
     * @param myAgent Agent identifier
     * @param agents List of identifiers of the participating agents
     * @since 1.0
     */
    @Override
    public void printPlan(int output, String myAgent, ArrayList<String> agents) {
        int i, j, makespan = 0;
        //boolean found;
        int[] actions;
        ArrayList<Step> steps = getTotalSteps();

        //Calculate plan linearization
        switch (output) {
            case Plan.CoDMAP_CENTRALIZED:
                actions = linearizePlan(Plan.CoDMAP_CENTRALIZED, agents);
                break;
            case Plan.CoDMAP_DISTRIBUTED:
                actions = linearizePlan(Plan.CoDMAP_DISTRIBUTED, agents);
                break;
            default:
                actions = linearizePlan(Plan.REGULAR, agents);
                break;
        }

        for (i = 0; i < actions.length; i++) {
            if (actions[i] > makespan) {
                makespan = actions[i];
            }
        }

        //Print the plan
        //CoDMAP distributed format
        //Print only the sequence of actions of the current agent; print no-ops when necessary
        if (output == Plan.CoDMAP_DISTRIBUTED) {
            for (i = 0; i <= makespan; i++) {
                //found = false;
                for (j = 2; j < actions.length; j++) {
                    if (actions[j] == i && steps.get(j).getAgent().equals(myAgent)) {
                        System.out.println(i + ": (" + steps.get(j).getActionName() + ")");
                        //found = true;
                    }
                }
            }
        } //Regular and CoDMAP Centralized format
        //Print actions of the plan ordered by time step
        else {
            //Only the first agent in the list shall print the plan
            if (myAgent.equals(agents.get(0))) {
                for (i = 0; i <= makespan; i++) {
                    for (j = 2; j < actions.length; j++) {
                        if (actions[j] == i) {
                            if (output == Plan.CoDMAP_CENTRALIZED) {
                                System.out.println("(" + steps.get(j).getActionName() + ")");
                            } else {
                                System.out.println(i + ": (" + steps.get(j).getActionName() + ")");
                            }
                        }
                    }
                }
            }
        }
    }

    /**
     * Calculates a topological order of the steps in the plan.
     *
     * @param mode Output format (REGULAR, CoDMAP_CENTRALIZED or
     * CoDMAP_DISTRIBUTED)
     * @param agents List of agent names
     * @return Array with the step indexes sorted in a topological order
     * @since 1.0
     */
    private int[] linearizePlan(int mode, ArrayList<String> agents) {
        int[] actions = new int[this.getTotalSteps().size()];
        int i, level, assigned;
        boolean assign;
        ArrayList<Integer> pre;
        ArrayList<Step> steps = getTotalSteps();
        //Predecessors hash table: given a step, all its predecessors are stored
        Hashtable<Integer, ArrayList<Integer>> predecessors = new Hashtable<>();
        for (i = 0; i < steps.size(); i++) {
            predecessors.put(i, new ArrayList<Integer>());
            //Initialize actions structure (stores the level of each action)
            actions[i] = Plan.UNASSIGNED;
        }
        actions[0] = Plan.INITIAL;
        //Add predecessors by analyzing orderings
        for (Ordering o : this.getTotalOrderings()) {
            predecessors.get(o.getIndex2()).add(o.getIndex1());
        }
        for (CausalLink l : this.getTotalCausalLinks()) {
            predecessors.get(l.getStep2().getIndex()).add(l.getStep1().getIndex());
        }

        switch (mode) {
            //CoDMAP competition - centralized track format (linear plan)
            case Plan.CoDMAP_CENTRALIZED:
                for (level = 0; level <= actions.length - 2; level++) {
                    for (i = 2; i < actions.length; i++) {
                        //If the action does not have an assigned level, check the maximum level of its predecessors
                        if (actions[i] == Plan.UNASSIGNED) {
                            assign = true;
                            pre = predecessors.get(i);
                            for (int p : pre) {
                                //If a predecessor does not have an assigned level, action i cannot be scheduled yet
                                if (actions[p] == Plan.UNASSIGNED) {
                                    assign = false;
                                    break;
                                }
                            }
                            //Schedule action i and break to the next iteration
                            if (assign) {
                                actions[i] = level;
                                break;
                            }
                        }
                    }
                }
                break;
            //CoDMAP competition - distributed track format (a sequence of actions per agent)
            case Plan.CoDMAP_DISTRIBUTED:
                int[] succSequenceSizes = new int[actions.length];
                for (i = 0; i < succSequenceSizes.length; i++) {
                    succSequenceSizes[i] = -1;
                }
                Hashtable<Integer, ArrayList<Integer>> successors = new Hashtable<>();
                for (i = 0; i < steps.size(); i++) {
                    successors.put(i, new ArrayList<Integer>());
                }
                //Add successors by analyzing orderings
                for (Ordering o : this.getTotalOrderings()) {
                    successors.get(o.getIndex1()).add(o.getIndex2());
                }
                for (CausalLink l : this.getTotalCausalLinks()) {
                    successors.get(l.getStep1().getIndex()).add(l.getStep2().getIndex());
                }
                //Base case
                for (i = 2; i < succSequenceSizes.length; i++) {
                    if (successors.get(i).isEmpty()) {
                        succSequenceSizes[i] = 0;
                    }
                }

                ArrayList<Integer> sequence;
                int j,
                 max;
                boolean exit,
                 completed = false,
                 notCalculated;
                while (!completed) {
                    for (i = 2; i < succSequenceSizes.length; i++) {
                        if (succSequenceSizes[i] == -1) {
                            sequence = successors.get(i);

                            exit = false;
                            for (j = 0; j < sequence.size(); j++) {
                                if (succSequenceSizes[sequence.get(j)] == -1) {
                                    exit = true;
                                    break;
                                }
                            }
                            if (!exit) {
                                max = Integer.MIN_VALUE;
                                for (j = 0; j < sequence.size(); j++) {
                                    if (succSequenceSizes[sequence.get(j)] > max) {
                                        max = succSequenceSizes[sequence.get(j)];
                                    }
                                }
                                succSequenceSizes[i] = max + 1;
                            }
                        }
                    }
                    //Verify if all the successor sequences are calculated
                    notCalculated = false;
                    for (i = 2; i < succSequenceSizes.length; i++) {
                        if (succSequenceSizes[i] == -1) {
                            notCalculated = true;
                            break;
                        }
                    }
                    if (!notCalculated) {
                        completed = true;
                    }
                }

                int scheduled = 0;
                int bestAction,
                 longestSuccessorSequence;
                level = 0;
                while (scheduled < actions.length - 2) {
                    for (String ag : agents) {
                        bestAction = -1;
                        longestSuccessorSequence = Integer.MIN_VALUE;
                        for (i = 2; i < actions.length; i++) {
                            //If an action introduced by agent ag does not have an assigned level, 
                            //check the maximum level of its predecessors
                            if (actions[i] == Plan.UNASSIGNED && steps.get(i).getAgent().equals(ag)) {
                                assign = true;
                                pre = predecessors.get(i);
                                for (int p : pre) {
                                    //If a predecessor does not have an assigned level,
                                    //or if it is scheduled at the current level,
                                    //action i cannot be scheduled yet
                                    if (actions[p] == Plan.UNASSIGNED || actions[p] == level) {
                                        assign = false;
                                        break;
                                    }
                                }
                                //Schedule action i and break to the next iteration
                                if (assign) {
                                    if (succSequenceSizes[i] > longestSuccessorSequence) {
                                        bestAction = i;
                                        longestSuccessorSequence = succSequenceSizes[i];
                                    }
                                }
                            }
                        }
                        if (bestAction != -1) {
                            actions[bestAction] = level;
                            scheduled++;
                        }
                    }
                    level++;
                }
                break;
            //POP format - actions scheduled as early as possible
            default:
                level = 0;
                assigned = 0;
                while (assigned < actions.length - 2) {
                    for (i = 2; i < actions.length; i++) {
                        //If the action does not have an assigned level, check the maximum level of its predecessors
                        if (actions[i] == Plan.UNASSIGNED) {
                            assign = true;
                            pre = predecessors.get(i);
                            for (int p : pre) {
                                //If a predecessor does not have an assigned level,
                                //or if it is assigned to the current level, action i cannot be scheduled yet
                                if (actions[p] == Plan.UNASSIGNED || actions[p] == level) {
                                    assign = false;
                                    break;
                                }
                            }
                            //Schedule action i and increase assigned variable
                            if (assign) {
                                actions[i] = level;
                                assigned++;
                            }
                        }
                    }
                    //Increase the level after an iteration
                    level++;
                }
                break;
        }

        return actions;
    }

}
