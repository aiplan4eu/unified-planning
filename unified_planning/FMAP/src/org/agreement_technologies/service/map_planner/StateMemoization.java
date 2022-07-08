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
import java.util.HashMap;

/**
 * StateMemoization class stores the generated plans to avoid expand repeated
 * plans during the search. Compare frontier states is much faster than compare
 * partial-order plans, but no so accurate (see Memoization class).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class StateMemoization {

    // Initial map size
    private static final int MAP_SIZE = 65537;
    // Hash map
    private final HashEntry<Integer, POPIncrementalPlan> entrySet[];
    // Number of variables (equal to the state size)
    private final int numVars;

    /**
     * Creates an empty map.
     *
     * @param numVars Number of variables
     * @since 1.0
     */
    @SuppressWarnings("unchecked")
    public StateMemoization(int numVars) {
        entrySet = new HashEntry[MAP_SIZE];
        this.numVars = numVars;
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
     * Checks if the frontier states of two plans are equal.
     *
     * @param p1 First plan
     * @param p2 Second plan
     * @return <code>true</code>, if both plans lead to the same frontier state;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    private boolean equalPlans(POPIncrementalPlan p1, POPIncrementalPlan p2) {
        int[] order1 = p1.linearization(), order2 = p2.linearization();
        int[] s1 = p1.computeCodeState(order1, numVars),
                s2 = p2.computeCodeState(order2, numVars);
        for (int v = 0; v < numVars; v++) {
            if (s2[v] != s1[v]) {
                return false;
            }
        }
        return true;
    }

    /**
     * Checks if a plan leads to the given frontier state.
     *
     * @param s1 Fontier state
     * @param p2 Plan to check
     * @return <code>true</code>, if the plan leads to the given frontier state;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    private boolean equalPlans(int s1[], POPIncrementalPlan p2) {
        int[] order2 = p2.linearization();
        int[] s2 = p2.computeCodeState(order2, numVars);
        for (int v = 0; v < numVars; v++) {
            if (s1[v] != s2[v]) {
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
        if (p.isSolution()) {
            return 0;
        }
        int[] order = p.linearization();
        int[] state = p.computeCodeState(order, numVars);
        StringBuilder s = new StringBuilder(numVars << 2);
        for (int v = 0; v < numVars; v++) {
            s.append(state[v]);
        }
        return s.toString().hashCode();
    }

    /**
     * Checks if the addition of an action a to a base plan p leads to a
     * repeated state.
     *
     * @param p Plan
     * @param a Action to add
     * @return Plan in the map that leads to the same state as the given plan
     * after adding the given action; <code>null</code>, if the addition of the
     * action to the plan leads to a new state
     * @since 1.0
     */
    public IPlan search(POPIncrementalPlan p, POPAction a) {
        int code;
        int[] order = p.linearization();
        int[] s = p.computeCodeState(order, numVars);
        if (p.isSolution()) {
            code = 0;
        } else {
            //Update state with the new action a
            for (POPPrecEff eff : a.getEffects()) {
                s[eff.getVarCode()] = eff.getValueCode();
            }
            //Obtain plan code from the frontier state calculated
            code = getPlanCode(s);
        }
        int pos = position(code);
        HashEntry<Integer, POPIncrementalPlan> e = entrySet[pos];
        while (e != null) {
            if (e.key == code) {
                if (equalPlans(s, e.value)) {
                    return e.value;
                }
            }
            e = e.next;
        }
        return null;	// Not found
    }

    /**
     * Compute the plan code for the given frontier state.
     *
     * @param state Frontier state
     * @return Plan code
     */
    private int getPlanCode(int[] state) {
        StringBuilder s = new StringBuilder(numVars << 2);
        for (int v = 0; v < numVars; v++) {
            s.append(state[v]);
        }
        return s.toString().hashCode();
    }

    /**
     * Prints the histogram for the map.
     *
     * @since 1.0
     */
    public void histogram() {
        int max = 0;
        HashMap<Integer, Integer> h = new HashMap<>();
        for (int i = 0; i < entrySet.length; i++) {
            int length = listLength(entrySet[i]);
            int value = h.containsKey(length) ? h.get(length) : 0;
            value++;
            h.put(length, value);
            if (length > max) {
                max = length;
            }
        }
        System.out.println("HISTOGRAM:");
        for (int i = 0; i <= max; i++) {
            if (h.containsKey(i)) {
                System.out.println(i + "\t" + h.get(i));
            }
        }
    }

    /**
     * Computes the length of a given cell in the map.
     *
     * @param hashEntry Map entry
     * @return Length of the cell in the map that starts with the given entry
     * @since 1.0
     */
    private int listLength(HashEntry<Integer, POPIncrementalPlan> hashEntry) {
        int n = 0;
        while (hashEntry != null) {
            n++;
            hashEntry = hashEntry.next;
        }
        return n;
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
