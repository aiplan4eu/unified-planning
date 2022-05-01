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
package org.agreement_technologies.common.map_negotiation;

import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_planner.POPSearchMethod;

/**
 * Negotiation factory interface: initializes negotiation methods for
 * preference-based planning.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface NegotiationFactory {

    // Negotiation methods
    public static final int COOPERATIVE = 0;
    public static final int BORDA = 1;
    
    // Number of proposals for Borda voting
    public static final int BORDA_PROPOSALS = 10;

    /**
     * Initializes negotiation method.
     *
     * @param c Commnication infrastructure
     * @param st Search tree
     * @return Negotiation method for plan selection
     * @since 1.0
     */
    PlanSelection getNegotiationMethod(AgentCommunication c, POPSearchMethod st);

    /**
     * Returns negotiation method type.
     *
     * @return Negotiation method identifier
     * @since 1.0
     */
    int getNegotiationType();
}
