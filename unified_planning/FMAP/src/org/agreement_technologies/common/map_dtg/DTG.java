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
package org.agreement_technologies.common.map_dtg;

import java.util.ArrayList;
import java.util.HashMap;

/**
 * DTG is the interface that represents a Domain Transition Graph of a variable.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface DTG {

    static final int INFINITE = (Integer.MAX_VALUE) / 3;    // Infinite

    /**
     * Returns the path cost (in number of actions) for the currect variable to
     * change from a given initial value to the given end value. This method is
     * not designed for multi-agent evaluation.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @param state Current state
     * @param newValues Already achieved values for all the variables
     * @param threadIndex Thread index (for multi-thread purposes)
     * @return Path cost
     * @since 1.0
     */
    int pathCost(String initValue, String endValue, HashMap<String, String> state,
            HashMap<String, ArrayList<String>> newValues, int threadIndex);

    /**
     * Returns the path cost (in number of actions) for the currect variable to
     * change from a given initial value to the given end value. Unlike the
     * pathCost method, this one is designed for multi-agent evaluation.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @return Path cost
     * @since 1.0
     */
    int pathCostMulti(String initValue, String endValue);

    /**
     * Returns the path (list of values) for the currect variable to change from
     * a given initial value to the given end value. This method is designed for
     * multi-agent evaluation.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @return Array of values
     * @since 1.0
     */
    String[] getPathMulti(String initValue, String endValue);

    /**
     * Gets information about the transition for the current variable from an
     * intial value to an end value.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @return Transition information
     * @see DTGTransition
     * @since 1.0
     */
    DTGTransition getTransition(String initValue, String endValue);

    /**
     * Gets the name of the current variable.
     *
     * @return Name of the variable
     * @since 1.0
     */
    String getVarName();

    /**
     * Returns the path (list of values) for the currect variable to change from
     * a given initial value to the given end value. This method is not designed
     * for multi-agent evaluation.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @param state Current state
     * @param newValues Already achieved values for all the variables
     * @param threadIndex Thread index (for multi-thread purposes)
     * @return Array of values
     * @since 1.0
     */
    String[] getPath(String initValue, String endValue, HashMap<String, String> state,
            HashMap<String, ArrayList<String>> newValues, int threadIndex);

    /**
     * Returns the set of transitions for this variable that start from a given
     * initial value.
     *
     * @param fromValue Initial value
     * @return Array of transitions
     * @since 1.0
     */
    DTGTransition[] getTransitionsFrom(String fromValue);

    /**
     * Returns the set of transitions for this variable that finish in a given
     * end value.
     *
     * @param endValue End value
     * @return Array of transitions
     * @since 1.0
     */
    DTGTransition[] getTransitionsTo(String endValue);

    /**
     * Checks if a given value for this variable is not known by this agent.
     *
     * @param value Value to check
     * @return <code>true</code> if this agent does not know this value;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    boolean unknownValue(String value);

    /**
     * Returns the distance (in number of actions) for the currect variable to
     * change from a given initial value to the given end value. This method is
     * not designed for multi-agent evaluation.
     *
     * @param initValue Initial value
     * @param endValue End value
     * @param threadIndex Thread index (for multi-thread purposes)
     * @return Distance in number of actions
     * @since 1.0
     */
    int getDistance(String initValue, String endValue, int threadIndex);

    /**
     * Clears the cache, which stores already computed paths for value
     * transitions.
     *
     * @param threadIndex Thread index (for multi-thread purposes)
     * @since 1.0
     */
    void clearCache(int threadIndex);
}
