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
package org.agreement_technologies.common.map_parser;

/**
 * NumericEffect interface provides methods to deal with action numeric effects.
 * Only "increase" effects are implemented in this version.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface NumericEffect {

    // Effect type
    static final int INCREASE = 0;

    /**
     * Gets the effect type.
     * 
     * @return Effect type
     * @since 1.0
     */
    public int getType();

    /**
     * Gets the numeric function that will be updated.
     * 
     * @return Numeric function
     * @since 1.0
     */
    public Function getNumericVariable();

    /**
     * Gets the numeric expression that will be used to update the function.
     * 
     * @return Numeric expression
     * @since 1.0
     */
    public NumericExpression getNumericExpression();

}
