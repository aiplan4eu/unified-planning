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
package org.agreement_technologies.common.map_grounding;

/**
 * Grounded condition: (= variable value) or (<> variable value).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface GroundedCond extends java.io.Serializable {

    static final int EQUAL = 1;     // Equal condition
    static final int DISTINCT = 2;  // Distinct condition

    /**
     * Returns the condition type (EQUAL or DISTINCT).
     *
     * @return Condition type
     * @since 1.0
     */
    int getCondition();

    /**
     * Returns the grounded variable.
     *
     * @return Grounded variable
     * @since 1.0
     */
    GroundedVar getVar();

    /**
     * Returns the value (object name, 'undefined' is not allowed).
     *
     * @return Value
     * @since 1.0
     */
    String getValue();

}
