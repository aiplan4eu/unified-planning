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
import org.agreement_technologies.common.map_planner.Ordering;
import org.agreement_technologies.common.map_planner.Step;

/**
 * Memoization class stores the generated plans to avoid expand repeated plans
 * during the search.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class Memoization {

    // Initial size of the map to store plans
    private static final int MAP_SIZE = 65537;
    // Hash table to store plans
    private final HashEntry<Integer, POPIncrementalPlan> entrySet[];

    /**
     * Creates an empty memoization table.
     *
     * @since 1.0
     */
    @SuppressWarnings("unchecked")
    public Memoization() {
        entrySet = new HashEntry[MAP_SIZE];
    }

    /**
     * Adds a new plan to the table.
     *
     * @param p Plan to add
     * @since 1.0
     */
    public void add(POPIncrementalPlan p) {
        int code = getPlanCode(p);
        int pos = position(code);
        entrySet[pos] = new HashEntry<>(code, p, entrySet[pos]);
    }

    /**
     * Searches for a given plan in the table.
     *
     * @param p Plan to search for
     * @return Plan in the table equal to the given one. <code>null</code>, if
     * it is not found
     * @since 1.0
     */
    public IPlan search(POPIncrementalPlan p) {
        int code = getPlanCode(p);
        int pos = position(code);
        HashEntry<Integer, POPIncrementalPlan> e = entrySet[pos];
        while (e != null) {
            if (e.key == code) {
                if (equalPlans(p, e.value)) {
                    return e.value;
                }
            }
            e = e.next;
        }
        return null;	// Not found
    }

    /**
     * Checks if two plans are equal.
     *
     * @param p1 First plan
     * @param p2 Second plan
     * @return <code>true</code>, if both plans are equal; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    @SuppressWarnings("unchecked")
    private static boolean equalPlans(POPIncrementalPlan p1, POPIncrementalPlan p2) {
        int numSteps = p1.numSteps();
        if (numSteps != p2.numSteps()) {
            return false;
        }
        ArrayList<Integer> nextSteps1[] = new ArrayList[numSteps];
        ArrayList<Integer> nextSteps2[] = new ArrayList[numSteps];
        for (int i = 0; i < numSteps; i++) {
            nextSteps1[i] = new ArrayList<>();
            nextSteps2[i] = new ArrayList<>();
        }
        String stepNames1[] = new String[numSteps];
        String stepNames2[] = new String[numSteps];
        int n = numSteps;
        while (p2.getFather() != null) {
            stepNames2[--n] = p2.getStep().toString();
            for (CausalLink c : p2.getCausalLinks()) {
                if (!nextSteps2[c.getIndex1()].contains(c.getIndex2())) {
                    nextSteps2[c.getIndex1()].add(c.getIndex2());
                }
            }
            for (Ordering o : p2.getOrderings()) {
                if (!nextSteps2[o.getIndex1()].contains(o.getIndex2())) {
                    nextSteps2[o.getIndex1()].add(o.getIndex2());
                }
            }
            p2 = p2.getFather();
        }
        n = numSteps;
        while (p1.getFather() != null) {
            stepNames1[--n] = p1.getStep().toString();
            for (CausalLink c : p1.getCausalLinks()) {
                if (!nextSteps1[c.getIndex1()].contains(c.getIndex2())) {
                    nextSteps1[c.getIndex1()].add(c.getIndex2());
                }
            }
            for (Ordering o : p1.getOrderings()) {
                if (!nextSteps1[o.getIndex1()].contains(o.getIndex2())) {
                    nextSteps1[o.getIndex1()].add(o.getIndex2());
                }
            }
            p1 = p1.getFather();
        }
        boolean checked[] = new boolean[numSteps];
        return checkStep(0, 0, stepNames1, stepNames2, nextSteps1, nextSteps2, checked);
    }

    /**
     * Checks if the sequence of steps are equal in both plans.
     *
     * @param s1 Current step to check in the first plan
     * @param s2 Current step to check in the second plan
     * @param stepNames1 Array with the step names in the first plan
     * @param stepNames2 Array with the step names in the second plan
     * @param nextSteps1 For each step in the first plan, list of the steps
     * which go after it
     * @param nextSteps2 For each step in the second plan, list of the steps
     * which go after it
     * @param checked List of already checked steps to avoid repetitions
     * @return <code>true</code>, if the sequence of steps are equal in both
     * plans; <code>false</code>, otherwise
     * @since 1.0
     */
    private static boolean checkStep(int s1, int s2, String[] stepNames1, String[] stepNames2,
            ArrayList<Integer>[] nextSteps1, ArrayList<Integer>[] nextSteps2, boolean checked[]) {
        if (checked[s1]) {
            return true;
        }
        checked[s1] = true;
        for (int next1 : nextSteps1[s1]) {
            int next2 = -1;
            for (int aux : nextSteps2[s2]) {
                if (stepNames1[next1].equals(stepNames2[aux])) {
                    next2 = aux;
                    break;
                }
            }
            if (next2 == -1 || !checkStep(next1, next2, stepNames1, stepNames2, nextSteps1,
                    nextSteps2, checked)) {
                return false;
            }
        }
        return true;
    }

    /**
     * Gets the position of a plan in the table.
     *
     * @param code Plan code
     * @return Position of a plan in the table
     * @since 1.0
     */
    private int position(int code) {
        int index = code % entrySet.length;
        if (index < 0) {
            index += entrySet.length;
        }
        return index;
    }

    /**
     * Calculates a (hash) code for the given plan.
     *
     * @param p Plan
     * @return (Hash) code for the plan
     * @since 1.0
     */
    private int getPlanCode(POPIncrementalPlan p) {
        int code = 0;
        Step s;
        while (p.getFather() != null) {
            s = p.getStep();
            code += s.getActionName().hashCode();
            if (s.getAgent() != null) {
                code += s.getAgent().hashCode();
            }
            p = p.getFather();
        }
        return code;
    }

    /**
     * Entry for the memoization hash table.
     * 
     * @param <K> Type for keys
     * @param <V> Type for values
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    private static class HashEntry<K, V> {

        K key;                  // Key element
        V value;                // Value element
        HashEntry<K, V> next;   // Next entry in the list

        /**
         * Creates a new entry.
         * 
         * @param key Key
         * @param value Value
         * @param next Next entry in the list
         * @since 1.0
         */
        public HashEntry(K key, V value, HashEntry<K, V> next) {
            this.key = key;
            this.value = value;
            this.next = next;
        }
    }
    
}
