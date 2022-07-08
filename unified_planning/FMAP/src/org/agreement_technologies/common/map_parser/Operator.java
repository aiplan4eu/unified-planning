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
 * Operator interface provides methods to deal with operators (ungrounded
 * actions).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Operator {
    
    /**
     * Returns the operator name.
     * 
     * @return Operator name
     * @since 1.0
     */
    String getName();

    /**
     * Returns the operator parameters.
     * 
     * @return Array with the operator parameters
     * @since 1.0
     */
    Parameter[] getParameters();

    /**
     * Get the operator precondition (list of conditions).
     *
     * @return Array of operator conditions 
     * @since 1.0
     */
    Condition[] getPrecondition();

    /**
     * Get the operator effect (list of effects)
     *
     * @return Array with the operator effects
     * @since 1.0
     */
    Condition[] getEffect();

    /**
     * Returns the preference value. Returns -1 if it is not set.
     *
     * @return Preference value; -1 if it is not set
     * @since 1.0
     */
    int getPreferenceValue();

    /**
     * Get the numeric effects (list of effects) of the operator.
     * 
     * @return Array of numeric effects
     * @since 1.0
     */
    NumericEffect[] getNumericEffects();
    
}
