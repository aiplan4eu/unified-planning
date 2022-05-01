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

import java.io.Serializable;

/**
 * DTGRequest interface is a request for information needed to build the Domain
 * Transition Graphs in a distributed way.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface DTGRequest extends Serializable {

    /**
     * Gets the destination agent of the request.
     *
     * @return Name of the destination agent
     * @since 1.0
     */
    String toAgent();

    /**
     * Gets the sender agent of the request.
     *
     * @return Name of the sender agent
     * @since 1.0
     */
    String fromAgent();

    /**
     * Gets the name of the variable involved in the request.
     *
     * @return Name of the variable
     * @since 1.0
     */
    String varName();

    /**
     * Gets the name of the value reached by the variable.
     *
     * @return Reached value
     * @since 1.0
     */
    String reachedValue();

    /**
     * Gest the cost for the variable to reach the value from the intial value.
     *
     * @return Cost of reaching the value
     * @since 1.0
     */
    int reachedValueCost();

    /**
     * Gets the name of the intial value of the variable.
     *
     * @return Intial value
     * @since 1.0
     */
    String initialValue();
}
