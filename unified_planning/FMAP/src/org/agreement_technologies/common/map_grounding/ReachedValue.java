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
 * Reached values in the grounding process.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface ReachedValue extends java.io.Serializable {

    /**
     * Gets the involved variable.
     *
     * @return Grounded variable
     * @since 1.0
     */
    GroundedVar getVar();

    /**
     * Gets the value for this variable.
     *
     * @return Value name
     * @since 1.0
     */
    String getValue();

    /**
     * Gets the minimum time for the variable to get this value.
     *
     * @return Minimum time for the variable to get this value
     * @since 1.0
     */
    int getMinTime();

    /**
     * Checks if this value can be shared to another agent.
     *
     * @param agName Name of the destination agent
     * @return <code>true</code>, if this value for this variable can be shared
     * with the destination agent; <code>false</code>, otherwise
     * @since 1.0
     */
    boolean shareable(String agName);

}
