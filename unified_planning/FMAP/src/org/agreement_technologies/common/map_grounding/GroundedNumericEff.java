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
 * Grounded numeric effect: only to increase the value of a numeric variable is
 * supported.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface GroundedNumericEff {

    static final int INCREASE = 0;  // Operator type: only increase is supported

    /**
     * Returns the operator type (INCREASE).
     *
     * @return Operator type
     * @since 1.0
     */
    int getType();

    /**
     * Returns the grounded numeric variable.
     *
     * @return Grounded numeric variable
     * @since 1.0
     */
    GroundedVar getVariable();

    /**
     * Gets the numeric expression defined to update the value of the variable.
     * 
     * @return Numeric expression
     * @since 1.0
     */
    GroundedNumericExpression getExpression();
}
