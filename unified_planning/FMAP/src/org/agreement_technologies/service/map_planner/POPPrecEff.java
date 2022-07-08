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

import org.agreement_technologies.common.map_planner.Condition;

/**
 * Function-value tuple that defines preconditions and effects in a POP.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPPrecEff {

    static final int EQUAL = 1;             // Equal condition
    static final int DISTINCT = 2;          // Distinct condition
    static final boolean IS_PREC = true;    // Indicates that this is an action precondition    
    static final boolean IS_EFF = false;    // Indcates that this is an action effect

    private Condition condition;            // Original grounded condition
    private POPFunction function;           // Variable
    private final String value;             // Value
    private final int conditionType;        // Condition type (EQUAL or DISTINCT)
    private String key;                     // String identifier for this condition
    private int index;                      // Index for this condition

    /**
     * Creates a new condition.
     *
     * @param cond Original grounded condition
     * @param var Variable
     * @param val Value
     * @param co Condition type (EQUAL or DISTINCT)
     * @since 1.0
     */
    public POPPrecEff(Condition cond, POPFunction var, String val, int co) {
        this.condition = cond;
        this.conditionType = co;
        this.function = var;
        this.value = val;
        this.key = null;
        this.key = this.toKey();
    }

    /**
     * Gets the variable code.
     *
     * @return Variable code
     * @since 1.0
     */
    public int getVarCode() {
        return condition.getVarCode();
    }

    /**
     * Gets the value code.
     *
     * @return Value code
     * @since 1.0
     */
    public int getValueCode() {
        return condition.getValueCode();
    }

    /**
     * Sets the index for this condition.
     *
     * @param i Condition index
     * @since 1.0
     */
    public void setIndex(int i) {
        this.index = i;
    }

    /**
     * Gets the index for this condition.
     *
     * @return Condition index
     * @since 1.0
     */
    public int getIndex() {
        return this.index;
    }

    /**
     * Sets the variable.
     *
     * @param v Variable
     * @since 1.0
     */
    public void setFunction(POPFunction v) {
        this.function = v;
    }

    /**
     * Sets the value.
     *
     * @return Value
     * @since 1.0
     */
    public String getValue() {
        return this.value;
    }

    /**
     * Gets the condition type.
     *
     * @return Condition type
     * @since 1.0
     */
    public int getType() {
        return this.conditionType;
    }

    /**
     * Gets the original grounded condition.
     *
     * @return Grounded condition
     * @since 1.0
     */
    public Condition getCondition() {
        return this.condition;
    }

    /**
     * Sets the original grounded condition.
     *
     * @param gc Grounded condition
     * @since 1.0
     */
    public void setGroundedCondition(Condition gc) {
        this.condition = gc;
    }

    /**
     * Gets a string identifier for this condition.
     *
     * @return String identifier
     * @since 1.0
     */
    public final String toKey() {
        if (this.key == null) {
            String res;
            if (this.conditionType == EQUAL) {
                res = "=";
            } else if (this.conditionType == DISTINCT) {
                res = "<>";
            } else {
                res = "?";
            }
            key = condition.getVarCode() + res + condition.getValueCode();
            return key;
        } else {
            return this.key;
        }
    }

    /**
     * Gets a description of this condition.
     *
     * @return Description of this condition
     * @since 1.0
     */
    @Override
    public String toString() {
        String res;
        int n = 0;
        res = function.getName() + "(";
        for (String s : function.getParams()) {
            if (n == 0) {
                n++;
            } else {
                res += ", ";
            }
            res += s;
        }
        if (this.conditionType == EQUAL) {
            res += ") = ";
        }
        if (this.conditionType == DISTINCT) {
            res += ") <> ";
        }
        res += this.getValue();
        return res;
    }

    /**
     * Gets the variable in this condition.
     *
     * @return Variable
     * @since 1.0
     */
    public POPFunction getFunction() {
        return function;
    }

}
