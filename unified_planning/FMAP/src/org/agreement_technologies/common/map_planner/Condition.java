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
package org.agreement_technologies.common.map_planner;

/**
 * Common interface for conditions (variable-value pairs that define
 * preconditions and effects).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Condition {

    // Condition types
    static final int EQUAL = 1;
    static final int DISTINCT = 2;

    /**
     * Returns the condition type.
     *
     * @return Condition type (EQUAL or DISTINCT)
     * @since 1.0
     */
    int getType();

    /**
     * Returns the code of the variable.
     *
     * @return Variable code
     * @since 1.0
     */
    int getVarCode();

    /**
     * Returns the code of the value.
     *
     * @return Value code
     * @since 1.0
     */
    int getValueCode();

    /**
     * Returns identifier of the condition.
     *
     * @return Univoque condition identifier
     * @since 1.0
     */
    String toKey();

    /**
     * Gets information of the condition to be shown in the GUI.
     *
     * @param pf Planner factory
     * @return Printable information of the condition
     * @since 1.0
     */
    String labeled(PlannerFactory pf);
    
}
