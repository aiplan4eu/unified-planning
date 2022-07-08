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
 * Grounded variable.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface GroundedVar extends java.io.Serializable {

    /**
     * Returns the function name.
     *
     * @return Function name
     * @since 1.0
     */
    String getFuctionName();

    /**
     * Returns the function parameters (list of object names).
     *
     * @return Function parameters
     * @since 1.0
     */
    String[] getParams();

    /**
     * Returns the list of types for a given parameter.
     *
     * @param paramNumber Number of parameter (0 .. getParams().length - 1)
     * @return Array of types
     * @since 1.0
     */
    String[] getParamTypes(int paramNumber);

    /**
     * Returns the function domain types.
     *
     * @return Array of types for the values of the function
     * @since 1.0
     */
    String[] getDomainTypes();

    /**
     * Returns the initial true value (object name) or null if it has none.
     *
     * @return Variable value in the initial state
     * @since 1.0
     */
    String initialTrueValue();

    /**
     * Returns the initial false values for this variable (list of objects).
     *
     * @return Array of false values (values of the variables that does not hold
     * in the initial state)
     * @since 1.0
     */
    String[] initialFalseValues();

    /**
     * Gets the Minimum time, according to the disRPG, in which the variable can
     * get the given value (objName). Returns -1 if the given value is not
     * reachable.
     *
     * @param objName Value name
     * @return Minimum time needed to reach that value; -1 if it is not
     * reachable
     * @since 1.0
     */
    int getMinTime(String objName);

    /**
     * Minimal time, according to the disRPG, in which a given agent can get
     * this variable to have a given value (objName). Returns -1 if the given
     * agent cannot assign the given value to this variable.
     *
     * @param objName Value name
     * @param agent Agent to generate the value
     * @return Minimum time needed to reach that value by that agent; -1 if it
     * is not reachable
     * @since 1.0
     */
    int getMinTime(String objName, String agent);

    /**
     * Checks whether the given value for this variable can be shared with the
     * given agent.
     *
     * @param objName Value name
     * @param agent Destination agent
     * @return <code>true</code>, if that value for this variable can be shared
     * with the destination agent; <code>false</code>, otherwise
     * @since 1.0
     */
    boolean shareable(String objName, String agent);

    /**
     * Checks whether the given variable can be shared with the given agent.
     *
     * @param agent Destination agent
     * @return <code>true</code>, if the values of this variable can be shared
     * with the destination agent; <code>false</code>, otherwise
     * @since 1.0
     */
    boolean shareable(String agent);

    /**
     * List of reachable values for this variable.
     *
     * @return Array of reachable values for this variable
     * @since 1.0
     */
    String[] getReachableValues();

    /**
     * Checks if this variable is boolean, i.e. that its values can be only
     * <code>true</code> or <code>false</code>.
     *
     * @return <code>true</code>, it this variable is boolean;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    boolean isBoolean();

}
