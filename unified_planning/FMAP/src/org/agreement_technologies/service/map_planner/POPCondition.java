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

import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedEff;
import org.agreement_technologies.common.map_planner.Condition;
import org.agreement_technologies.common.map_planner.PlannerFactory;

/**
 * POPCondition class represents a condition between a variable and a value.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPCondition implements Condition {

    private final int type;     // Condition type (Condition.EQUAL or Condition.DISTINCT)
    private final int var;      // Variable index
    private final int value;    // Value index

    /**
     * Creates a new condition.
     *
     * @param c Grounded condition
     * @param pf Planner factory
     * @since 1.0
     */
    public POPCondition(GroundedCond c, PlannerFactory pf) {
        type = c.getCondition();
        var = pf.getCodeFromVar(c.getVar());
        value = pf.getCodeFromValue(c.getValue());
    }

    /**
     * Creates a new condition.
     *
     * @param type Condition type
     * @param var Variable index
     * @param value Value index
     * @since 1.0
     */
    public POPCondition(int type, int var, int value) {
        this.type = type;
        this.var = var;
        this.value = value;
    }

    /**
     * Creates a new condition.
     *
     * @param e Grounded effect
     * @param pf Planner factory
     * @since 1.0
     */
    public POPCondition(GroundedEff e, PlannerFactoryImp pf) {
        this.type = EQUAL;
        this.var = pf.getCodeFromVar(e.getVar());
        this.value = pf.getCodeFromValue(e.getValue());
    }

    /**
     * Returns the condition type.
     *
     * @return Condition type (EQUAL or DISTINCT)
     * @since 1.0
     */
    @Override
    public int getType() {
        return type;
    }

    /**
     * Returns the code of the variable.
     *
     * @return Variable code
     * @since 1.0
     */
    @Override
    public int getVarCode() {
        return var;
    }

    /**
     * Returns the code of the value.
     *
     * @return Value code
     * @since 1.0
     */
    @Override
    public int getValueCode() {
        return value;
    }

    /**
     * Returns identifier of the condition.
     *
     * @return Univoque condition identifier
     * @since 1.0
     */
    @Override
    public String toKey() {
        if (type == Condition.EQUAL) {
            return var + "=" + value;
        } else {
            return var + "<>" + value;
        }
    }

    /**
     * Gets a description of this condition.
     *
     * @return Condition description
     * @since 1.0
     */
    @Override
    public String toString() {
        return toKey();
    }

    /**
     * Gets information of the condition to be shown in the GUI.
     *
     * @param pf Planner factory
     * @return Printable information of the condition
     * @since 1.0
     */
    @Override
    public String labeled(PlannerFactory pf) {
        if (pf == null) {
            return toKey();
        }
        String varName = pf.getVarNameFromCode(var);
        String valueName = pf.getValueFromCode(value);
        if (varName == null) {
            varName = "" + var;
        }
        if (valueName == null) {
            valueName = "" + value;
        }
        if (type == Condition.EQUAL) {
            return varName + "=" + valueName;
        } else {
            return varName + "<>" + valueName;
        }
    }

}
