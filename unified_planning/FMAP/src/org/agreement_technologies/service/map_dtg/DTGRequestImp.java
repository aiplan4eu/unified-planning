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
package org.agreement_technologies.service.map_dtg;

import org.agreement_technologies.common.map_dtg.DTGRequest;

/**
 * DTGRequest interface is a request for information needed to build the Domain
 * Transition Graphs in a distributed way.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class DTGRequestImp implements DTGRequest {

    // Serial number for serialization
    private static final long serialVersionUID = 4766115568690770517L;
    private final String fromAgent;     // Sender agent
    private final String toAgent;       // Destination agent
    private final String varName;       // Name of the variable
    private final String initialValue;  // Initial value
    private final String reachedValue;  // Reached value
    private final int reachedValueCost; // Cost of reaching the value

    /**
     * Constructor of a new request.
     *
     * @param fromAgent Sender agent
     * @param toAgent Destination agent
     * @param varName Variable name
     * @param initialValue Initial value
     * @param reachedValue Reached value
     * @param reachedValueCost Cost of reaching the value
     * @since 1.0
     */
    public DTGRequestImp(String fromAgent, String toAgent, String varName,
            String initialValue, String reachedValue, int reachedValueCost) {
        this.fromAgent = fromAgent;
        this.toAgent = toAgent;
        this.varName = varName;
        this.reachedValue = reachedValue;
        this.reachedValueCost = reachedValueCost;
        this.initialValue = initialValue;
    }

    /**
     * Gets a description of this request.
     *
     * @return Description of this request
     * @since 1.0
     */
    @Override
    public String toString() {
        return fromAgent + ":" + varName + " -> "
                + toAgent + ":" + reachedValue + ":" + reachedValueCost;
    }

    /**
     * Gets the destination agent of the request.
     *
     * @return Name of the destination agent
     * @since 1.0
     */
    @Override
    public String toAgent() {
        return toAgent;
    }

    /**
     * Gets the sender agent of the request.
     *
     * @return Name of the sender agent
     * @since 1.0
     */
    @Override
    public String fromAgent() {
        return fromAgent;
    }

    /**
     * Gets the name of the variable involved in the request.
     *
     * @return Name of the variable
     * @since 1.0
     */
    @Override
    public String varName() {
        return varName;
    }

    /**
     * Gets the name of the value reached by the variable.
     *
     * @return Reached value
     * @since 1.0
     */
    @Override
    public String reachedValue() {
        return reachedValue;
    }

    /**
     * Gest the cost for the variable to reach the value from the intial value.
     *
     * @return Cost of reaching the value
     * @since 1.0
     */
    @Override
    public int reachedValueCost() {
        return reachedValueCost;
    }

    /**
     * Gets the name of the intial value of the variable.
     *
     * @return Intial value
     * @since 1.0
     */
    @Override
    public String initialValue() {
        return initialValue;
    }
}
