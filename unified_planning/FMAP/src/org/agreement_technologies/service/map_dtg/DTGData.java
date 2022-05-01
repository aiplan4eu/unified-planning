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
import org.agreement_technologies.common.map_dtg.DTGTransition;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedEff;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.GroundedVar;

/**
 * DTGData class represents the data that agents can exchange, i.e. value
 * transitions for a variable, during the Domain Transitions Graph building.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class DTGData implements java.io.Serializable {

    // Serial number for serialization
    private static final long serialVersionUID = 6011631219080464901L;
    private final String varName;                   // Name of the variable
    private final String fromValue;                 // Initial value of the variable
    private final String toValue;                   // End value of the variable
    // List of the common preconditions to all the actions that produce this transition
    private final ArrayList<DTGCondition> commonPrecs;
    // List of the common effects to all the actions that produce this transition
    private final ArrayList<DTGEffect> commonEffs;

    /**
     * Static method to check if a given value transition can be shared, i.e. it
     * is not private, with a given agent.
     *
     * @param t Value transition
     * @param ag Destination agent
     * @return <code>true</code> if the data can be shared with the destination
     * agent; <code>false</code>, otherwise
     * @since 1.0
     */
    public static boolean shareable(DTGTransition t, String ag) {
        GroundedVar v = t.getVar();
        if (!v.shareable(ag)) {
            return false;
        }
        return !(!v.shareable(t.getStartValue(), ag) && !v.shareable(t.getFinalValue(), ag));
    }

    /**
     * Constructor of the message
     *
     * @param t Value transition
     * @param ag Destination agent
     * @since 1.0
     */
    public DTGData(DTGTransition t, String ag) {
        GroundedVar v = t.getVar();
        this.varName = v.shareable(ag) ? v.toString() : "?";
        this.fromValue = v.shareable(t.getStartValue(), ag) ? t.getStartValue() : "?";
        this.toValue = v.shareable(t.getFinalValue(), ag) ? t.getFinalValue() : "?";
        commonPrecs = new ArrayList<>();
        for (GroundedCond prec : t.getCommonPreconditions()) {
            if (prec.getVar().shareable(prec.getValue(), ag)) {
                commonPrecs.add(new DTGCondition(prec));
            }
        }
        commonEffs = new ArrayList<>();
        for (GroundedEff eff : t.getCommonEffects()) {
            if (eff.getVar().shareable(eff.getValue(), ag)) {
                commonEffs.add(new DTGEffect(eff));
            }
        }
    }

    /**
     * Returns a description of this message.
     *
     * @return Description of this message.
     * @since 1.0
     */
    @Override
    public String toString() {
        String s = "";
        for (DTGCondition prec : commonPrecs) {
            if (s.equals("")) {
                s = prec.toString();
            } else {
                s = s + "," + prec.toString();
            }
        }
        return varName + ": " + fromValue + "->" + toValue + " [" + s + "]";
    }

    /**
     * Gets the variable of the value transition.
     *
     * @return Name of the variable
     * @since 1.0
     */
    public String getVarName() {
        return varName;
    }

    /**
     * Gets the start value of the variable.
     *
     * @return Start value
     * @since 1.0
     */
    public String getStartValue() {
        return fromValue;
    }

    /**
     * Gets the end value of the variable.
     *
     * @return End value
     * @since 1.0
     */
    public String getFinalValue() {
        return toValue;
    }

    /**
     * Gets the common preconditions of all the actions that can cause the
     * transition.
     *
     * @param task Grounded task
     * @return Array of common preconditions of all the actions that can cause
     * the transition
     * @since 1.0
     */
    public GroundedCond[] getCommonPrecs(GroundedTask task) {
        GroundedVar[] vars = task.getVars();
        GroundedCond[] precs = new GroundedCond[commonPrecs.size()];
        for (int i = 0; i < commonPrecs.size(); i++) {
            DTGCondition c = commonPrecs.get(i);
            GroundedVar v = null;
            for (GroundedVar aux : vars) {
                if (c.varName.equals(aux.toString())) {
                    v = aux;
                    break;
                }
            }
            if (v == null) {
                throw new RuntimeException("Unknown variable '" + c.varName
                        + "' received during the DTG construction");
            }
            precs[i] = task.createGroundedCondition(c.condition, v, c.value);
        }
        return precs;
    }

    /**
     * Gets the common effects of all the actions that can cause the transition.
     *
     * @param task Grounded task
     * @return Array of common effects of all the actions that can cause the
     * transition
     * @since 1.0
     */
    public GroundedEff[] getCommonEffs(GroundedTask task) {
        GroundedVar[] vars = task.getVars();
        GroundedEff[] effs = new GroundedEff[commonEffs.size()];
        for (int i = 0; i < commonEffs.size(); i++) {
            DTGEffect c = commonEffs.get(i);
            GroundedVar v = null;
            for (GroundedVar aux : vars) {
                if (c.varName.equals(aux.toString())) {
                    v = aux;
                    break;
                }
            }
            if (v == null) {
                throw new RuntimeException("Unknown variable '" + c.varName
                        + "' received during the DTG construction");
            }
            effs[i] = task.createGroundedEffect(v, c.value);
        }
        return effs;
    }

    /**
     * DTGCondition represents an action precondition, ready to be transmitted
     * to other agents.
     *
     * @since 1.0
     */
    private static class DTGCondition implements java.io.Serializable {

        // Serial number for serialization
        private static final long serialVersionUID = -8411329280671918342L;
        private int condition;  // Condition, see the constants defined in GroundedCond class
        private String varName; // Name of the variable 
        private String value;   // Value that the variable must take

        /**
         * Constructor of the condition.
         *
         * @param prec Action precondition
         * @since 1.0
         */
        public DTGCondition(GroundedCond prec) {
            this.condition = prec.getCondition();
            this.varName = prec.getVar().toString();
            this.value = prec.getValue();
        }

        /**
         * Gets a description for this condition.
         *
         * @return Description of this condition
         * @since 1.0
         */
        @Override
        public String toString() {
            return "(" + varName + (condition == GroundedCond.EQUAL ? "=" : "<>")
                    + value + ")";
        }
    }

    /**
     * DTGEffect represents an action effect, ready to be transmitted to other
     * agents.
     *
     * @since 1.0
     */
    private static class DTGEffect implements java.io.Serializable {

        // Serial number for serialization
        private static final long serialVersionUID = -8967487407479184565L;
        private String varName;     // Name of the variable 
        private String value;       // Value that the variable must take

        /**
         * Constructor of the effect.
         *
         * @param eff Action effect
         * @since 1.0
         */
        public DTGEffect(GroundedEff eff) {
            this.varName = eff.getVar().toString();
            this.value = eff.getValue();
        }

        /**
         * Gets a description for this effect.
         *
         * @return Description of this effect
         * @since 1.0
         */
        @Override
        public String toString() {
            return "(" + varName + "=" + value + ")";
        }
    }
}
