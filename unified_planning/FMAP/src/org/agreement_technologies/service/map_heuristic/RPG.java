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
package org.agreement_technologies.service.map_heuristic;

import java.util.ArrayList;
import java.util.HashMap;
import org.agreement_technologies.common.map_grounding.Action;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedEff;

/**
 * RPG class implements a relaxed planning graph for the FF heuristic.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class RPG {

    private HashMap<VarValue, Integer> literalLevels;   // Levels of literals
    private HashMap<String, Integer> actionLevels;      // Action levels
    private int numLevels;                              // Number of levels

    /**
     * Build a RPG.
     *
     * @param state Current state
     * @param goals Set of top-level goals
     * @param pgoals Set of private goals
     * @param requirers For each condition, set of actions that requires that
     * condition
     * @since 1.0
     */
    public RPG(HashMap<String, ArrayList<String>> state, ArrayList<GroundedCond> goals,
            ArrayList<GroundedCond> pgoals, HashMap<String, ArrayList<Action>> requirers) {
        ArrayList<VarValue> lastLevel = new ArrayList<>(2 * state.size()),
                newLevel = new ArrayList<>(2 * state.size());
        literalLevels = new HashMap<>();
        actionLevels = new HashMap<>();
        ArrayList<VarValue> remainingGoals = new ArrayList<>(goals.size());
        for (String var : state.keySet()) {
            VarValue v = new VarValue(var, state.get(var).get(0), 0);
            lastLevel.add(v);
            literalLevels.put(v, 0);
        }
        for (GroundedCond g : goals) {
            VarValue gv = new VarValue(g.getVar().toString(), g.getValue(), 0);
            if (!literalLevels.containsKey(gv)) {
                remainingGoals.add(gv);
            }
        }
        for (GroundedCond g : pgoals) {
            VarValue gv = new VarValue(g.getVar().toString(), g.getValue(), 0);
            if (!literalLevels.containsKey(gv)) {
                remainingGoals.add(gv);
            }
        }
        numLevels = 0;
        while (!remainingGoals.isEmpty() && !lastLevel.isEmpty()) {
            newLevel.clear();
            for (VarValue v : lastLevel) {
                ArrayList<Action> aList = requirers.get(v.getId());
                if (aList != null) {
                    for (Action a : aList) {
                        if (!actionLevels.containsKey(a.toString())) {
                            boolean executable = true;
                            for (GroundedCond prec : a.getPrecs()) {
                                if (!holds(prec)) {
                                    executable = false;
                                    break;
                                }
                            }
                            if (executable) {
                                actionLevels.put(a.toString(), numLevels);
                                for (GroundedEff eff : a.getEffs()) {
                                    VarValue ev = new VarValue(eff.getVar().toString(),
                                            eff.getValue(), numLevels + 1);
                                    if (!literalLevels.containsKey(ev) && !newLevel.contains(ev)) {
                                        newLevel.add(ev);
                                    }
                                }
                            }
                        }	// End for action
                    }
                }
            }	// End for varValues
            numLevels++;
            for (VarValue v : newLevel) {
                literalLevels.put(v, v.level);
                remainingGoals.remove(v);
            }
            ArrayList<VarValue> aux = lastLevel;
            lastLevel = newLevel;
            newLevel = aux;
        }	// End RPG loop
    }

    /**
     * Checks if a given condition is already in the RPG.
     *
     * @param prec Condition to check
     * @return <code>true</code>, if the condition is already in the RPG;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    private boolean holds(GroundedCond prec) {
        return literalLevels.containsKey(new VarValue(prec.getVar().toString(),
                prec.getValue(), 0));
    }

    /**
     * Gets the number of levels in the RPG.
     *
     * @return Number of levels in the RPG
     * @since 1.0
     */
    public int numLevels() {
        return numLevels;
    }

    /**
     * Given a condition, gets the corresponding pair of (variable,value) in the
     * RPG.
     *
     * @param g Condition
     * @return Corresponding pair of (variable,value) in the RPG, or
     * <code>null</code> if it is not found
     * @since 1.0
     */
    public VarValue getVarValue(GroundedCond g) {
        VarValue v = new VarValue(g.getVar().toString(), g.getValue(), 0);
        Integer level = literalLevels.get(v);
        if (level == null) {
            return null;
        }
        v.level = level;
        return v;
    }

    /**
     * Gets the level of an action in the RPG.
     *
     * @param a Action
     * @return Level of the action in the RPG, or -1 if it is not found
     * @since 1.0
     */
    public int getLevel(Action a) {
        Integer level = actionLevels.get(a.toString());
        return level != null ? level : -1;
    }

    /**
     * Calculates the difficulty of an action, adding the level of its
     * preconditions.
     *
     * @param a Action
     * @return Difficulty of the action
     * @since 1.0
     */
    public int getDifficulty(Action a) {
        int d = 0;
        for (GroundedCond prec : a.getPrecs()) {
            VarValue v = new VarValue(prec.getVar().toString(), prec.getValue(), 0);
            d += literalLevels.get(v);
        }
        return d;
    }

    /**
     * VarValue class stores a pair (variable, value), together with its level
     * in the RPG.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    public static class VarValue implements Comparable<VarValue> {

        String var;         // Name of the variable
        String value;       // Variable value
        int level;          // Level in the RPG

        /**
         * Creates a new pair (variable, value).
         *
         * @param var Name of the variable
         * @param value Variable value
         * @param level Level in the RPG
         * @since 1.0
         */
        public VarValue(String var, String value, int level) {
            this.var = var;
            this.value = value;
            this.level = level;
        }

        /**
         * Gets a description of this pair (variable, value).
         *
         * @return Description of this pair (variable, value)
         * @since 1.0
         */
        @Override
        public String toString() {
            return var + "=" + value + "(" + level + ")";
        }

        /**
         * Gets a unique string identifier for this pair (variable, value).
         *
         * @return Unique string identifier for this pair (variable, value)
         * @since 1.0
         */
        public String getId() {
            return var + "=" + value;
        }

        /**
         * Checks if two pairs are equal, without taking into account the RPG
         * level
         *
         * @param x Another pair (variable, value)
         * @return <code>true</code>, if both pairs have the same variable and
         * value; <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            VarValue v = (VarValue) x;
            return var.equals(v.var) && value.equals(v.value);
        }

        /**
         * Gets a hash code for this pair (variable, value).
         *
         * @return Hash code
         * @since 1.0
         */
        @Override
        public int hashCode() {
            return (var + value).hashCode();
        }

        /**
         * Compares two pairs.
         *
         * @param v Another pair (variable, value) to compare with this one
         * @return Value less than zero if the level of this pair is smaller;
         * Value greater than zero if the level of the other goal is smaller;
         * Zero, otherwise
         * @since 1.0
         */
        @Override
        public int compareTo(VarValue v) {
            return v.level - level;
        }
    }

}
