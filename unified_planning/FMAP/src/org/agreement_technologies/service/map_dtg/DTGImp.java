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
package org.agreement_technologies.service.map_dtg;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.PriorityQueue;
import java.util.Vector;
import org.agreement_technologies.common.map_dtg.DTG;
import org.agreement_technologies.common.map_dtg.DTGRequest;
import org.agreement_technologies.common.map_dtg.DTGSet;
import org.agreement_technologies.common.map_dtg.DTGTransition;
import org.agreement_technologies.common.map_grounding.Action;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedEff;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.GroundedVar;

/**
 * DTGImp class represents a Domain Transition Graph of a variable.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class DTGImp implements DTG {

    // Maximum number of search nodes to calculate the shortest paths
    private static final int MAX_SEARCH_NODES = 9999;
    private DTGSet dtgSet;          // Set of Domain Transition Graphs
    private GroundedTask task;      // Grounded task
    private GroundedVar var;        // Variable of this DTG
    private String values[];        // Set of possible values of the variable 
    // Table with the numeric index for each possible value
    private Hashtable<String, Integer> valueIndex;
    // Matrix of transitions; Columns and rows are the start and end values of the transitions 
    private ArrayList<ArrayList<Transition>> transitions;
    // Array of tables which allow to store already computed paths to avoid repetitions of calculations.
    // It is a vector as there is a table per thread, allowing this way a multi-thread evaluation
    private Vector<Hashtable<TransitionMemo, Path>> shortestPaths;
    // Array of tables which allow to store already computed path distances to avoid repetitions of calculations.
    // It is a vector as there is a table per thread, allowing this way a multi-thread evaluation
    private Vector<Hashtable<TransitionMemo, Integer>> distances;
    // For multi-agent evaluation. This table stores all shortest paths from an initial
    // value to the rest of possible values of the variable
    private Hashtable<String, Dijkstra> shortestPathsMulti;
    // Counter for expanded nodes in the search for shortest paths
    private int searchNodes;

    /**
     * Constructor of a new Domain Transition Graph
     *
     * @param dtgSet Reference to the collection of DTGs
     * @param v Variable for this DTG
     * @param task Grounded task
     * @since 1.0
     */
    public DTGImp(DTGSet dtgSet, GroundedVar v, GroundedTask task) {
        this.dtgSet = dtgSet;
        this.task = task;
        var = v;
        values = v.getReachableValues();
        if (v.isBoolean() && values.length < 2) {
            values = new String[2];
            values[0] = "true";
            values[1] = "false";
        }
        valueIndex = new Hashtable<String, Integer>(values.length);
        transitions = new ArrayList<ArrayList<Transition>>(values.length);
        for (int i = 0; i < values.length; i++) {
            valueIndex.put(values[i], i);
            transitions.add(new ArrayList<DTGImp.Transition>());
        }
        for (Action a : task.getActions()) {
            GroundedEff eff = changes(a, var);
            if (eff != null) {
                addTransition(a, eff, task.getAgentName().toLowerCase());
            }
        }
        shortestPaths = new Vector<Hashtable<TransitionMemo, DTGImp.Path>>();
        distances = new Vector<Hashtable<TransitionMemo, Integer>>();
        shortestPathsMulti = new Hashtable<String, DTGImp.Dijkstra>();
    }

    /**
     * Returns the path cost (in number of actions) for the currect variable to
     * change from a given initial value to the given end value. Unlike the
     * pathCost method, this one is designed for multi-agent evaluation.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @return Path cost
     * @since 1.0
     */
    @Override
    public int pathCostMulti(String initValue, String endValue) {
        Dijkstra sp = shortestPathsMulti.get(initValue);
        if (sp == null) {
            Integer vIndex = valueIndex.get(initValue);
            sp = new Dijkstra(vIndex);
        }
        return sp.getPathCost(endValue);
    }

    /**
     * Returns the path (list of values) for the currect variable to change from
     * a given initial value to the given end value. This method is designed for
     * multi-agent evaluation.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @return Array of values
     * @since 1.0
     */
    @Override
    public String[] getPathMulti(String initValue, String endValue) {
        Dijkstra sp = shortestPathsMulti.get(initValue);
        if (sp == null) {
            Integer vIndex = valueIndex.get(initValue);
            sp = new Dijkstra(vIndex);
        }
        return sp.getPath(endValue);
    }

    /**
     * Adds a new transition to the DTG.
     *
     * @param a Action that causes the transition
     * @param eff Effect of the action that causes the transition
     * @param fromAgent Agent that causes the transition
     * @since 1.0
     */
    private void addTransition(Action a, GroundedEff eff, String fromAgent) {
        GroundedCond prec = requires(a, var);
        int toValue = valueIndex.get(eff.getValue());
        if (prec == null || prec.getCondition() == GroundedCond.DISTINCT) {
            for (int fromValue = 0; fromValue < values.length; fromValue++) {
                if (toValue != fromValue) {
                    Transition t = getTransition(fromValue, toValue);
                    if (t == null) {
                        t = new Transition(fromValue, toValue, a, fromAgent);
                        transitions.get(fromValue).add(t);
                    } else {
                        t.addAction(a, fromAgent);
                    }
                }
            }
        } else {
            int fromValue = valueIndex.get(prec.getValue());
            Transition t = getTransition(fromValue, toValue);
            if (t == null) {
                t = new Transition(fromValue, toValue, a, fromAgent);
                transitions.get(fromValue).add(t);
            } else {
                t.addAction(a, fromAgent);
            }
        }
    }

    /**
     * Gets a transition from one value to another one.
     *
     * @param fromValue Initial value
     * @param toValue End value
     * @return The transition, if it is found; <code>null</code>, otherwise
     * @since 1.0
     */
    private Transition getTransition(int fromValue, int toValue) {
        for (Transition t : transitions.get(fromValue)) {
            if (t.toValue == toValue) {
                return t;
            }
        }
        return null;
    }

    /**
     * Returns the set of transitions for this variable that start from a given
     * initial value.
     *
     * @param fromValue Initial value
     * @return Array of transitions
     * @since 1.0
     */
    @Override
    public DTGTransition[] getTransitionsFrom(String fromValue) {
        Integer index = valueIndex.get(fromValue);
        if (index == null) {
            return null;
        }
        ArrayList<Transition> trans = transitions.get(index);
        DTGTransition[] res = new DTGTransition[trans.size()];
        for (int i = 0; i < res.length; i++) {
            res[i] = trans.get(i);
        }
        return res;
    }

    /**
     * Returns the set of transitions for this variable that finish in a given
     * end value.
     *
     * @param toValue End value
     * @return Array of transitions
     * @since 1.0
     */
    @Override
    public DTGTransition[] getTransitionsTo(String toValue) {
        Integer index = valueIndex.get(toValue);
        if (index == null) {
            return null;
        }
        ArrayList<DTGTransition> res = new ArrayList<>();
        for (ArrayList<Transition> trans : transitions) {
            for (Transition t : trans) {
                if (t.toValue == index) {
                    res.add(t);
                }
            }
        }
        return res.toArray(new DTGTransition[res.size()]);
    }

    /**
     * Checks if a given action modifies the value of a given variable.
     *
     * @param a Action
     * @param v Variable
     * @return The action effect that modifies the variable; <code>null</code>,
     * if the action does not update the variable
     * @since 1.0
     */
    private GroundedEff changes(Action a, GroundedVar v) {
        for (GroundedEff eff : a.getEffs()) {
            if (eff.getVar().equals(v)) {
                return eff;
            }
        }
        return null;
    }

    /**
     * Checks if a given action requires a given variable to have a certain
     * value as a precondition.
     *
     * @param a Action
     * @param v Variable
     * @return The action precondition that involves the variable;
     * <code>null</code>, if the action has not that variable in its
     * preconditions
     * @since 1.0
     */
    private GroundedCond requires(Action a, GroundedVar v) {
        for (GroundedCond pre : a.getPrecs()) {
            if (pre.getVar().equals(v)) {
                return pre;
            }
        }
        return null;
    }

    /**
     * Returns an array with the last transitions computed.
     *
     * @return Array with the last transitions computed
     * @since 1.0
     */
    public DTGTransition[] getNewTransitions() {
        ArrayList<DTGTransition> tList = new ArrayList<>();
        for (int i = 0; i < values.length; i++) {
            ArrayList<Transition> tv = transitions.get(i);
            for (Transition t : tv) {
                if (t.newTransition) {
                    t.newTransition = false;
                    tList.add(t);
                }
            }
        }
        return tList.toArray(new DTGTransition[tList.size()]);
    }

    /**
     * Adds a new transition to this DTG.
     *
     * @param startValue Initial value
     * @param finalValue End value
     * @param commonPrecs Common preconditions to all the actions that produce
     * this transition
     * @param commonEffs Common effects to all the actions that produce this
     * transition
     * @param fromAgent Agent that produces this transition
     */
    public void addTransition(String startValue, String finalValue,
            GroundedCond[] commonPrecs, GroundedEff[] commonEffs, String fromAgent) {
        boolean newFinalValue = valueIndex.containsKey(finalValue);
        int fvIndex = newFinalValue ? valueIndex.get(finalValue) : addNewValue(finalValue);
        if (!valueIndex.containsKey(startValue)) {	// New value for this variable
            int svIndex = addNewValue(startValue);
            transitions.get(svIndex).add(new Transition(svIndex, fvIndex, commonPrecs,
                    commonEffs, fromAgent));
        } else {                                        // Existing value
            int svIndex = valueIndex.get(startValue);
            ArrayList<Transition> tList = transitions.get(svIndex);
            Transition t = null;
            for (Transition aux : tList) {
                if (aux.toValue == fvIndex) {
                    t = aux;
                    break;
                }
            }
            if (t == null) {            // New transition
                tList.add(new Transition(svIndex, fvIndex, commonPrecs, commonEffs,
                        fromAgent));
            } else {			// Existing transition
                t.boundCommonPrecs(commonPrecs, fromAgent);
            }
        }
        if (newFinalValue) {	// Generate new possible transitions
            for (Action a : task.getActions()) {
                GroundedCond prec = requires(a, var);
                if (prec != null && prec.getValue().equals(finalValue)) {
                    GroundedEff eff = changes(a, var);
                    if (eff != null) {
                        addTransition(a, eff, task.getAgentName().toLowerCase());
                    }
                }
            }
        }
    }

    /**
     * Adds a new possible value for this variable
     *
     * @param newValue New value
     * @return Index of this new value
     * @since 1.0
     */
    private int addNewValue(String newValue) {
        String auxValues[] = new String[values.length + 1];
        System.arraycopy(values, 0, auxValues, 0, values.length);
        int reachedValueIndex = values.length;
        auxValues[reachedValueIndex] = newValue;
        values = auxValues;
        valueIndex.put(newValue, reachedValueIndex);
        transitions.add(new ArrayList<Transition>());
        return reachedValueIndex;
    }

    /**
     * Returns a description of this DTG.
     *
     * @return Description of this DTG
     * @since 1.0
     */
    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("DTG (").append(var.toString()).append("):\n");
        for (ArrayList<Transition> tList : transitions) {
            for (Transition t : tList) {
                sb.append(t.toString()).append("\n");
            }
        }
        return sb.toString();
    }

    /**
     * Computes the shortest path for the value transition.
     *
     * @param initialValue Initial value of the variable
     * @param endValue End value of the variable
     * @param state Current state
     * @param newValues Already achieved values for all the variables
     * @param threadIndex Thread index (for multi-thread purposes)
     * @return Shortest path
     * @since 1.0
     */
    private Path computePath(String initialValue, String endValue, HashMap<String, String> state,
            HashMap<String, ArrayList<String>> newValues, int threadIndex) {
        Hashtable<TransitionMemo, Path> spTable = getShortestPathTable(threadIndex);
        TransitionMemo tm = new TransitionMemo(initialValue, endValue);
        Path p = spTable.get(tm);
        if (p == null) {
            p = new Path(initialValue, endValue, state, newValues, threadIndex);
            spTable.put(tm, p);
        }
        return p;
    }

    /**
     * Gets the table of shortest path of a given thread
     *
     * @param threadIndex Thread index
     * @return Table of shortest path of the given thread
     * @since 1.0
     */
    private Hashtable<TransitionMemo, Path> getShortestPathTable(int threadIndex) {
        if (threadIndex < shortestPaths.size()) {
            return shortestPaths.get(threadIndex);
        }
        Hashtable<TransitionMemo, Path> table = new Hashtable<>();
        shortestPaths.add(table);
        return table;
    }

    /**
     * Returns the path (list of values) for the currect variable to change from
     * a given initial value to the given end value. This method is not designed
     * for multi-agent evaluation.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @param state Current state
     * @param newValues Already achieved values for all the variables
     * @param threadIndex Thread index (for multi-thread purposes)
     * @return Array of values
     * @since 1.0
     */
    @Override
    public String[] getPath(String initValue, String endValue, HashMap<String, String> state,
            HashMap<String, ArrayList<String>> newValues, int threadIndex) {
        Path p = computePath(initValue, endValue, state, newValues, threadIndex);
        return p.getPath();
    }

    /**
     * Checks if a given value for this variable is not known by this agent.
     *
     * @param value Value to check
     * @return <code>true</code> if this agent does not know this value;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean unknownValue(String value) {
        return value.equals("?") || !valueIndex.containsKey(value);
    }

    /**
     * Returns the path cost (in number of actions) for the currect variable to
     * change from a given initial value to the given end value. This method is
     * not designed for multi-agent evaluation.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @param state Current state
     * @param newValues Already achieved values for all the variables
     * @param threadIndex Thread index (for multi-thread purposes)
     * @return Path cost
     * @since 1.0
     */
    @Override
    public int pathCost(String initValue, String endValue, HashMap<String, String> state,
            HashMap<String, ArrayList<String>> newValues, int threadIndex) {
        Path p = computePath(initValue, endValue, state, newValues, threadIndex);
        return p.getCost();
    }

    /**
     * Gets information about the transition for the current variable from an
     * intial value to an end value.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @return Transition information
     * @see DTGTransition
     * @since 1.0
     */
    @Override
    public DTGTransition getTransition(String initValue, String endValue) {
        Integer v1 = valueIndex.get(initValue),
                v2 = valueIndex.get(endValue);
        if (v1 == null) {
            v1 = valueIndex.get("?");
        }
        if (v2 == null) {
            v2 = valueIndex.get("?");
        }
        return getTransition(v1, v2);
    }

    /**
     * Gets the name of the current variable.
     *
     * @return Name of the variable
     * @since 1.0
     */
    @Override
    public String getVarName() {
        return var.toString();
    }

    /**
     * Returns the distance (in number of actions) for the currect variable to
     * change from a given initial value to the given end value. This method is
     * not designed for multi-agent evaluation.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @param threadIndex Thread index (for multi-thread purposes)
     * @return Distance in number of actions
     * @since 1.0
     */
    @Override
    public int getDistance(String initValue, String endValue, int threadIndex) {
        Hashtable<TransitionMemo, Integer> distTable = getDistanceTable(threadIndex);
        TransitionMemo tm = new TransitionMemo(initValue, endValue);
        Integer dst = distTable.get(tm);
        if (dst == null) {
            dst = computeDijkstraDistance(initValue, endValue);
            distTable.put(tm, dst);
        }
        return dst;
    }

    /**
     * Gets the table of path distances of a given thread
     *
     * @param threadIndex Thread index
     * @return Table of path distances of the given thread
     * @since 1.0
     */
    private Hashtable<TransitionMemo, Integer> getDistanceTable(int threadIndex) {
        if (threadIndex < distances.size()) {
            return distances.get(threadIndex);
        }
        Hashtable<TransitionMemo, Integer> dt = new Hashtable<>();
        distances.add(dt);
        return dt;
    }

    /**
     * Computes the shortest path in the DTG for the current variable to change
     * its value from a given initial value to a given final value.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @return Array of values of the path
     * @since 1.0
     */
    public String[] computeDijkstraPath(String initValue, String endValue) {
        Integer init = valueIndex.get(initValue), dst = valueIndex.get(endValue);
        if (init == null || dst == null) {
            return null;
        }
        int minCost[] = new int[values.length], minPath[] = new int[values.length];
        boolean visited[] = new boolean[values.length];
        for (int i = 0; i < values.length; i++) {
            minCost[i] = INFINITE;
            minPath[i] = -1;
        }
        minCost[init] = 0;
        PriorityQueue<DistanceToV> qPrior = new PriorityQueue<>();
        qPrior.add(new DistanceToV(init, 0));
        while (!qPrior.isEmpty()) {
            int v = qPrior.poll().index;
            if (!visited[v]) {
                visited[v] = true;
                for (Transition t : transitions.get(v)) {
                    if (minCost[t.toValue] > minCost[v] + t.getCost()) {
                        minCost[t.toValue] = minCost[v] + t.getCost();
                        minPath[t.toValue] = v;
                        qPrior.add(new DistanceToV(t.toValue, minCost[t.toValue]));
                    }
                }
            }
        }
        if (minCost[dst] == INFINITE) {
            return null;
        }
        ArrayList<String> res = new ArrayList<>();
        res.add(values[dst]);
        for (int vAux = minPath[dst]; vAux != -1; vAux = minPath[vAux]) {
            res.add(0, values[vAux]);
        }
        return res.toArray(new String[res.size()]);
    }

    /**
     * Computes the distance (number of value changes) for the current variable
     * to change its value from a given initial value to a given final value.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @return Path distance
     * @since 1.0
     */
    private int computeDijkstraDistance(String initValue, String endValue) {
        Integer init = valueIndex.get(initValue), dst = valueIndex.get(endValue);
        if (init == null || dst == null) {
            return INFINITE;
        }
        int minCost[] = new int[values.length];
        boolean visited[] = new boolean[values.length];
        for (int i = 0; i < values.length; i++) {
            minCost[i] = INFINITE;
        }
        minCost[init] = 0;
        PriorityQueue<DistanceToV> qPrior = new PriorityQueue<>();
        qPrior.add(new DistanceToV(init, 0));
        while (!qPrior.isEmpty()) {
            int v = qPrior.poll().index;
            if (!visited[v]) {
                visited[v] = true;
                for (Transition t : transitions.get(v)) {
                    if (minCost[t.toValue] > minCost[v] + t.getCost()) {
                        minCost[t.toValue] = minCost[v] + t.getCost();
                        qPrior.add(new DistanceToV(t.toValue, minCost[t.toValue]));
                    }
                }
            }
        }
        return minCost[dst];
    }

    /**
     * Clears the cache, which stores already computed paths for value
     * transitions.
     *
     * @param threadIndex Thread index (for multi-thread purposes)
     * @since 1.0
     */
    @Override
    public void clearCache(int threadIndex) {
        getShortestPathTable(threadIndex).clear();
        getDistanceTable(threadIndex).clear();
    }

    /**
     * DistanceToV class is used in the priority queue of the Dijkstra
     * algorithm.
     *
     * @since 1.0
     */
    private static class DistanceToV implements Comparable<DistanceToV> {

        int index;      // Value index
        int cost;       // Path cost until this value

        /**
         * Constructor.
         *
         * @param index Value index
         * @param cost Path cost until this value
         * @since 1.0
         */
        public DistanceToV(int index, int cost) {
            this.index = index;
            this.cost = cost;
        }

        /**
         * Compares this object with a given one.
         *
         * @param dv Another object to compare
         * @return A negative number if this object has higher priority (smaller
         * cost); Zero if both objects have the same cost; A positive number,
         * otherwise
         * @since 1.0
         */
        @Override
        public int compareTo(DistanceToV dv) {
            if (cost < dv.cost) {
                return -1;
            } else if (cost > dv.cost) {
                return 1;
            } else {
                return 0;
            }
        }
    }

    /**
     * TransitionMemo class identifies a transition (start and final value) to
     * be used in the hash tables.
     *
     * @since 1.0
     */
    private static class TransitionMemo {

        String fromValue;   // Initial value
        String toValue;     // Final value

        /**
         * Constructor for a TransitionMemo object.
         *
         * @param initialValue Initial value
         * @param endValue End value
         * @since 1.0
         */
        public TransitionMemo(String initialValue, String endValue) {
            this.fromValue = initialValue;
            this.toValue = endValue;
        }

        /**
         * Checks if this transition and another given one are equal.
         *
         * @param x The other transition
         * @return <code>true</code>, if both objects are equal;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            TransitionMemo tm = (TransitionMemo) x;
            return tm.fromValue.equals(fromValue) && tm.toValue.equals(toValue);
        }

        /**
         * Gets a description of this transition.
         *
         * @return Description of this transition
         * @since 1.0
         */
        @Override
        public String toString() {
            return fromValue + " " + toValue;
        }

        /**
         * Gets a hash code for this transition.
         *
         * @return Hash code of this transition
         * @since 1.0
         */
        @Override
        public int hashCode() {
            return (fromValue + " " + toValue).hashCode();
        }
    }

    /**
     * Transition class represents a transition between values of a variable.
     *
     * @since 1.0
     */
    public class Transition implements DTGTransition {

        int fromValue;                          // Start value 
        int toValue;                            // End value
        // Set of actions that can cause this transition
        ArrayList<Action> actions;
        // Common preconditions to all the actions that produce this transition
        ArrayList<GroundedCond> commonPrecs;
        // Common effects to all the actions that produce this transition
        ArrayList<GroundedEff> commonEffs;
        // Flag to indicate if this is a new transition
        boolean newTransition;
        // List of agents that can produce this transition
        ArrayList<String> agents;

        /**
         * Constructor of a new transition.
         *
         * @param fromValue Start value
         * @param toValue End value
         * @param a Action that causes this transition
         * @param agent Name of the agent that causes this transition
         * @since 1.0
         */
        public Transition(int fromValue, int toValue, Action a, String agent) {
            agents = new ArrayList<>();
            agents.add(agent);
            this.fromValue = fromValue;
            this.toValue = toValue;
            newTransition = true;
            actions = new ArrayList<>();
            actions.add(a);
            commonPrecs = new ArrayList<>();
            for (GroundedCond prec : a.getPrecs()) {
                commonPrecs.add(prec);
            }
            commonEffs = new ArrayList<>();
            for (GroundedEff eff : a.getEffs()) {
                commonEffs.add(eff);
            }
        }

        /**
         * Constructor of a new transition.
         *
         * @param svIndex Index of the start value
         * @param fvIndex Index of the end value
         * @param precs Array of common preconditions
         * @param effs Array of common effects
         * @param agent Name of the agent that causes this transition
         * @since 1.0
         */
        public Transition(int svIndex, int fvIndex, GroundedCond[] precs,
                GroundedEff[] effs, String agent) {
            agents = new ArrayList<>();
            agents.add(agent);
            this.fromValue = svIndex;
            this.toValue = fvIndex;
            newTransition = !values[svIndex].equals("?") && !values[fvIndex].equals("?");
            actions = new ArrayList<>();
            commonPrecs = new ArrayList<>();
            for (GroundedCond prec : precs) {
                commonPrecs.add(prec);
            }
            commonEffs = new ArrayList<>();
            for (GroundedEff eff : effs) {
                commonEffs.add(eff);
            }
        }

        /**
         * Returns the cost of this transition.
         *
         * @return Always 1, as one transition is caused by only one action
         * @since 1.0
         */
        public int getCost() {
            return 1;
        }

        /**
         * Removes the preconditions which are not common to all the actions.
         *
         * @param precs Array of preconditions to check
         * @param fromAgent Agent that can execute the actions where the
         * preconditions come from
         * @since 1.0
         */
        public void boundCommonPrecs(GroundedCond[] precs, String fromAgent) {
            int i = 0;
            while (i < commonPrecs.size()) {
                boolean exists = false;
                GroundedCond cPrec = commonPrecs.get(i);
                for (GroundedCond p : precs) {
                    if (p.getCondition() == cPrec.getCondition()
                            && p.getVar().equals(cPrec.getVar())
                            && p.getValue().equals(cPrec.getValue())) {
                        exists = true;
                        break;
                    }
                }
                if (exists) {
                    i++;
                } else {
                    commonPrecs.remove(i);
                }
            }
            if (!agents.contains(fromAgent)) {
                agents.add(fromAgent);
            }
        }

        /**
         * Adds another action that can also cause this transition.
         *
         * @param a New action
         * @param agent Agent that can execute the action
         * @since 1.0
         */
        public void addAction(Action a, String agent) {
            boolean newAction = true;
            if (!agents.contains(agent)) {
                agents.add(agent);
            }
            for (Action aux : actions) {
                if (aux == a) {
                    newAction = false;
                    break;
                }
            }
            if (newAction) {
                actions.add(a);
                int i = 0;
                while (i < commonPrecs.size()) {
                    if (requires(a, commonPrecs.get(i))) {
                        i++;
                    } else {
                        commonPrecs.remove(i);
                    }
                }
                i = 0;
                while (i < commonEffs.size()) {
                    if (changes(a, commonEffs.get(i))) {
                        i++;
                    } else {
                        commonEffs.remove(i);
                    }
                }
            }
        }

        /**
         * Check if a given action has a given effect.
         *
         * @param a Action
         * @param eff Effect
         * @return <code>true</code>, if the action has that effect;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        private boolean changes(Action a, GroundedEff eff) {
            for (GroundedEff e : a.getEffs()) {
                if (e.getVar().equals(eff.getVar())
                        && e.getValue().equals(eff.getValue())) {
                    return true;
                }
            }
            return false;
        }

        /**
         * Check if a given action has a given precondition.
         *
         * @param a Action
         * @param prec Precondition
         * @return <code>true</code>, if the action has that precondition;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        private boolean requires(Action a, GroundedCond prec) {
            for (GroundedCond p : a.getPrecs()) {
                if (p.getCondition() == prec.getCondition()
                        && p.getVar().equals(prec.getVar())
                        && p.getValue().equals(prec.getValue())) {
                    return true;
                }
            }
            return false;
        }

        /**
         * Gets a description of this transition.
         *
         * @return Description of this transition
         * @since 1.0
         */
        @Override
        public String toString() {
            String s1 = "";
            for (GroundedCond c : commonPrecs) {
                if (s1.equals("")) {
                    s1 = c.toString();
                } else {
                    s1 = s1 + "," + c.toString();
                }
            }
            String s2 = "";
            for (Action a : actions) {
                if (s2.equals("")) {
                    s2 = a.toString();
                } else {
                    s2 = s2 + "," + a.toString();
                }
            }
            String s3 = "";
            for (GroundedEff c : commonEffs) {
                if (s3.equals("")) {
                    s3 = c.toString();
                } else {
                    s3 = s3 + "," + c.toString();
                }
            }
            return "[" + agents + "] " + values[fromValue] + "->" + values[toValue]
                    + " [" + s1 + "]" + " {" + s2 + "}" + " [" + s3 + "]";
        }

        /**
         * Gets the variable of this transition.
         *
         * @return Variable of the transition
         * @since 1.0
         */
        @Override
        public GroundedVar getVar() {
            return var;
        }

        /**
         * Gets the initial value for the variable in this transition.
         *
         * @return Initial value
         * @since 1.0
         */
        @Override
        public String getStartValue() {
            return values[fromValue];
        }

        /**
         * Gets the fnial value for the variable in this transition.
         *
         * @return Final value
         * @since 1.0
         */
        @Override
        public String getFinalValue() {
            return values[toValue];
        }

        /**
         * Gets a list of the common preconditions to all the actions that
         * produce this transition.
         *
         * @return List of common preconditions
         * @since 1.0
         */
        @Override
        public ArrayList<GroundedCond> getCommonPreconditions() {
            return commonPrecs;
        }

        /**
         * Gets a list of the common effects to all the actions that produce
         * this transition.
         *
         * @return List of common effects
         * @since 1.0
         */
        @Override
        public ArrayList<GroundedEff> getCommonEffects() {
            return commonEffs;
        }

        /**
         * Gets a list of the agents that can cause this transition.
         *
         * @return List of agents that can cause this transition
         * @since 1.0
         */
        @Override
        public ArrayList<String> getAgents() {
            return agents;
        }
    }

    /**
     * Path class represents a path (set of value transitions) in the DTG.
     *
     * @since 1.0
     */
    public class Path {

        private String path[];      // Array of values of the path
        private int cost;           // Path cost

        /**
         * Constructs a new path.
         *
         * @param initialValue Initial value
         * @param endValue End value
         * @param state Current state
         * @param newValues Already achieved values for all the variables
         * @param threadIndex Thread index (for multi-thread purposes)
         * @since 1.0
         */
        public Path(String initialValue, String endValue, HashMap<String, String> state,
                HashMap<String, ArrayList<String>> newValues, int threadIndex) {
            path = null;
            cost = INFINITE;
            Integer index = valueIndex.get(initialValue);
            if (index == null) {
                return;
            }
            int init = index;
            index = valueIndex.get(endValue);
            if (index == null) {
                return;
            }
            int end = index;
            if (init == end) {
                path = new String[1];
                path[0] = initialValue;
                cost = 0;
            } else {
                path = computeDijkstraPath(initialValue, endValue);
                if (path == null) {
                    return;
                }
                cost = evaluateCost(path, state, newValues, threadIndex);
                computeShortestPath(init, end, state, newValues, threadIndex);
            }
        }

        /**
         * Computes and returns the cost of a path.
         *
         * @param p Path (array of values)
         * @param state Current state
         * @param newValues Already achieved values for all the variables
         * @param threadIndex Thread index (for multi-thread purposes)
         * @return Path cost
         * @since 1.0
         */
        private int evaluateCost(String[] p, HashMap<String, String> state,
                HashMap<String, ArrayList<String>> newValues, int threadIndex) {
            Hashtable<String, String> s = new Hashtable<>();
            if (state != null) {
                s.putAll(state);
            }
            int c = 0;
            for (int i = 1; i < p.length; i++) {
                DTGTransition t = getTransition(p[i - 1], p[i]);
                if (t == null) {
                    return INFINITE;
                }
                c += computeCost(t, s, newValues, threadIndex) + 1;
                updateState(t, s, null);
            }
            return c;
        }

        /**
         * Updates the state through the common effect of the given transition.
         *
         * @param t Value transition
         * @param state Current state
         * @param valuesBackup Backup of the state before the update. The backup
         * is done only if it is not <code>null</code>
         * @since 1.0
         */
        private void updateState(DTGTransition t, Hashtable<String, String> state,
                ArrayList<String> valuesBackup) {
            for (GroundedEff eff : t.getCommonEffects()) {
                String value = state.put(eff.getVar().toString(), eff.getValue());
                if (valuesBackup != null) {
                    valuesBackup.add(value);
                }
            }
        }

        /**
         * Computes and returns the cost of a transition. It also check the cost
         * of achieving the common preconditions of the transition.
         *
         * @param t Transition to evaluate
         * @param state Current state
         * @param newValues Already achieved values for all the variables
         * @param threadIndex Thread index (for multi-thread purposes)
         * @return Transition cost
         * @since 1.0
         */
        private int computeCost(DTGTransition t, Hashtable<String, String> state,
                HashMap<String, ArrayList<String>> newValues, int threadIndex) {
            int res = 0;
            for (GroundedCond c : t.getCommonPreconditions()) {
                int bestCost;
                String varName = c.getVar().toString();
                String stateValue = state.get(varName);
                DTG dtg = dtgSet.getDTG(varName);
                if (stateValue != null && !stateValue.equals(c.getValue())) {
                    bestCost = dtg.getDistance(stateValue, c.getValue(), threadIndex);
                } else {
                    bestCost = 0;
                }
                if (newValues != null) {
                    ArrayList<String> valueList = newValues.get(varName);
                    if (valueList != null) {
                        for (String value : valueList) {
                            int auxCost;
                            if (value.equals(c.getValue())) {
                                auxCost = 0;
                            } else {
                                auxCost = dtg.getDistance(value, c.getValue(), threadIndex);
                            }
                            if (auxCost < bestCost) {
                                bestCost = auxCost;
                            }
                        }
                    }
                }
                res += bestCost;
            }
            return res;
        }

        /**
         * Starts a search to find the shortest path from an initial to an end
         * value. This is the launcher of a recursive method with the same name.
         *
         * @param initValue Initial value
         * @param endValue End value
         * @param state Current state
         * @param newValues Already achieved values for all the variables
         * @param threadIndex Thread index (for multi-thread purposes)
         * @since 1.0
         */
        private void computeShortestPath(int initValue, int endValue, HashMap<String, String> state,
                HashMap<String, ArrayList<String>> newValues, int threadIndex) {
            searchNodes = 0;
            Hashtable<String, String> s = new Hashtable<>();
            boolean visited[] = new boolean[values.length];
            ArrayList<String> p = new ArrayList<>();
            visited[initValue] = true;
            for (Transition t : transitions.get(initValue)) {
                s.clear();
                if (state != null) {
                    s.putAll(state);
                }
                p.clear();
                p.add(values[initValue]);
                computeShortestPath(t, endValue, s, newValues, p, visited, 0, threadIndex);
            }
        }

        /**
         * Recursive method call to find the shortest path from an initial to an
         * end value.
         *
         * @param t Transition
         * @param endValue End value
         * @param state Current state
         * @param newValues Already achieved values for all the variables
         * @param p Array to store the values in the path
         * @param visited Array to mark the already visited values
         * @param currentCost Cost of the current (partially built) path
         * @param threadIndex Thread index (for multi-thread purposes)
         * @since 1.0
         */
        private void computeShortestPath(Transition t, int endValue, Hashtable<String, String> state,
                HashMap<String, ArrayList<String>> newValues, ArrayList<String> p, boolean[] visited,
                int currentCost, int threadIndex) {
            currentCost++;
            if (currentCost >= cost) {
                return;
            }
            currentCost += computeCost(t, state, newValues, threadIndex); // Compute the cost of the transition preconditions
            if (currentCost >= cost) {
                return;
            }
            p.add(values[t.toValue]);
            if (t.toValue == endValue) { // End value reached: check if the cost is better
                if (currentCost < cost) {
                    cost = currentCost;
                    path = p.toArray(new String[p.size()]);
                    p.remove(p.size() - 1);
                    //System.out.println("OK");
                }
                return;
            }
            ArrayList<String> valuesBackup = new ArrayList<String>(); // Apply transition effects
            updateState(t, state, valuesBackup);
            visited[t.toValue] = true;				      // Continue the path building
            if (++searchNodes < MAX_SEARCH_NODES) {
                for (Transition next : transitions.get(t.toValue)) {
                    if (!visited[next.toValue]) {
                        computeShortestPath(next, endValue, state, newValues, p, visited,
                                currentCost, threadIndex);
                    }
                }
            }
            visited[t.toValue] = false;	// Restore previous values
            p.remove(p.size() - 1);
            int i = 0;
            for (GroundedEff eff : t.commonEffs) {
                String value = valuesBackup.get(i++);
                if (value != null) {
                    state.put(eff.getVar().toString(), value);
                } else {
                    state.remove(eff.getVar().toString());
                }
            }
        }

        /**
         * Gets the path cost.
         *
         * @return Path cost
         * @since 1.0
         */
        public int getCost() {
            return cost;
        }

        /**
         * Returns the array of values of the path.
         *
         * @return Array of values
         * @since 1.0
         */
        public String[] getPath() {
            return path;
        }
    }

    /**
     * Dijkstra class implements the Dijkstra algorithm for computing shortest
     * paths.
     *
     * @since 1.0
     */
    private class Dijkstra {

        private static final int INFINITE = (Integer.MAX_VALUE) / 3; // Infinite
        private int initialValue;   // Initial value
        int minCost[];              // Array with the minimum cost to reach the rest of values
        int minPath[];              // Array with the previous values in the path to reach a given one
        String agent[];             // Array with the agents to reach each value

        /**
         * Constructor and calculation of the Dijkstra algorithm
         *
         * @param vIndex Initial value
         * @since 1.0
         */
        public Dijkstra(Integer vIndex) {
            minCost = new int[values.length];
            minPath = new int[values.length];
            agent = new String[values.length];
            boolean visited[] = new boolean[values.length];
            for (int i = 0; i < values.length; i++) {
                minCost[i] = INFINITE;
                minPath[i] = -1;
            }
            if (vIndex == null) {
                return;
            }
            initialValue = vIndex;
            minCost[initialValue] = 0;
            PriorityQueue<DistanceToV> qPrior = new PriorityQueue<>();
            qPrior.add(new DistanceToV(initialValue, 0));
            while (!qPrior.isEmpty()) {
                int v = qPrior.poll().index;
                if (!visited[v]) {
                    visited[v] = true;
                    for (Transition t : transitions.get(v)) {
                        if (minCost[t.toValue] > minCost[v] + t.getCost()) {
                            minCost[t.toValue] = minCost[v] + t.getCost();
                            minPath[t.toValue] = v;
                            qPrior.add(new DistanceToV(t.toValue, minCost[t.toValue]));
                        }
                    }
                }
            }
        }

        /**
         * Decodes and returns the shortest path after the Dijkstra algorithm.
         *
         * @param value End value
         * @return Array of values
         * @since 1.0
         */
        public String[] getPath(String value) {
            Integer vIndex = valueIndex.get(value);
            if (vIndex == null) {
                vIndex = valueIndex.get("?");
            }
            int length = 0, index = vIndex;
            while (minPath[index] != -1) {
                length++;
                index = minPath[index];
            }
            String path[] = new String[length + 1];
            path[length--] = value;
            while (minPath[vIndex] != -1) {
                path[length--] = values[minPath[vIndex]];
                vIndex = minPath[vIndex];
            }
            return path;
        }

        /**
         * Gets the previous value in the path to reach a given one.
         *
         * @param value Value to reach
         * @return Previous value
         * @since 1.0
         */
        public String previousValue(String value) {
            Integer vIndex = valueIndex.get(value);
            if (vIndex == null) {
                return null;
            }
            int prev = minPath[vIndex];
            if (prev < 0) {
                return null;
            }
            return values[prev];
        }

        /**
         * Updates the shortest path with the information received from other
         * agent.
         *
         * @param request Received message.
         * @since 1.0
         */
        public void update(DTGRequest request) {
            int reachedValueIndex = valueIndex.get(request.reachedValue());
            if (minCost[reachedValueIndex] > request.reachedValueCost()) {	// Update
                minCost[reachedValueIndex] = request.reachedValueCost();
                minPath[reachedValueIndex] = -2;
                agent[reachedValueIndex] = request.fromAgent();
                boolean visited[] = new boolean[values.length];
                int unkIndex = valueIndex.containsKey("?") ? valueIndex.get("?") : -1;
                if (unkIndex >= 0) {
                    visited[unkIndex] = true;
                }
                PriorityQueue<DistanceToV> qPrior = new PriorityQueue<>();
                qPrior.add(new DistanceToV(reachedValueIndex, request.reachedValueCost()));
                while (!qPrior.isEmpty()) {
                    int v = qPrior.poll().index;
                    if (!visited[v]) {
                        visited[v] = true;
                        for (Transition t : transitions.get(v)) {
                            if (minCost[t.toValue] > minCost[v] + t.getCost() || t.toValue == unkIndex) {
                                if (minCost[t.toValue] > minCost[v] + t.getCost()) {
                                    minCost[t.toValue] = minCost[v] + t.getCost();
                                    minPath[t.toValue] = v;
                                    agent[t.toValue] = null;
                                    qPrior.add(new DistanceToV(t.toValue, minCost[t.toValue]));
                                }
                            }
                        }
                    }
                }
            }
        }

        /**
         * Gets the minimum cost to reach a value
         *
         * @param value Value to reach
         * @return Minimum cost to reach the value
         */
        public int getPathCost(String value) {
            Integer index = valueIndex.get(value);
            if (index == null) {
                return -1;
            }
            return minCost[index];
        }
    }
}
