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
 * Planning action (grounded operator).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Action {

    /**
     * Returns the operator name.
     *
     * @return Operator name
     * @since 1.0
     */
    String getOperatorName();

    /**
     * Returns the list of parameters (list of objects).
     *
     * @return Array of parameters
     * @since 1.0
     */
    String[] getParams();

    /**
     * Gets the action preconditions.
     *
     * @return Array of preconditions
     * @since 1.0
     */
    GroundedCond[] getPrecs();

    /**
     * Gets the action effects.
     *
     * @return Array of effects
     * @since 1.0
     */
    GroundedEff[] getEffs();

    /**
     * Minimum time, according to the disRPG, in which the action can be
     * executed.
     *
     * @return Minimum time needed to execute this action
     * @since 1.0
     */
    int getMinTime();

    /**
     * Optimize structures after grounding.
     *
     * @since 1.0
     */
    void optimize();

    /**
     * Gets the action numeric effects.
     *
     * @return Array of numeric effects
     * @since 1.0
     */
    GroundedNumericEff[] getNumEffs();

    /**
     * Check if this action and a given one are mutex.
     *
     * @param a Another action
     * @return <code>true</code>, if both actions are mutex; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    boolean isMutex(Action a);
}
