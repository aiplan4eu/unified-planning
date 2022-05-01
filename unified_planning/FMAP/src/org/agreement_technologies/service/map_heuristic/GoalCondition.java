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

/**
 * GoalCondition class represents a (sub)goal, i.e. a condition that must be
 * achieved.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class GoalCondition implements java.io.Serializable {

    // Serial number for serialization
    private static final long serialVersionUID = -5772521153532509020L;
    public String varName;      // Name of the variable
    public String value;        // Value for the variable

    /**
     * Creates a new goal condition.
     *
     * @param varName Name of the variable
     * @param value Value for the variable
     * @since 1.0
     */
    public GoalCondition(String varName, String value) {
        this.varName = varName;
        this.value = value;
    }

    /**
     * Check if two goals are equal.
     *
     * @param x Another goal to compare with this one.
     * @return <code>true</code>, if both goals have the same variable name and
     * value; <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean equals(Object x) {
        return varName.equals(((GoalCondition) x).varName)
                && value.equals(((GoalCondition) x).value);
    }

    /**
     * Returns a description of this goal.
     *
     * @return Description of this goal
     * @since 1.0
     */
    @Override
    public String toString() {
        return varName + "=" + value;
    }
    
}
