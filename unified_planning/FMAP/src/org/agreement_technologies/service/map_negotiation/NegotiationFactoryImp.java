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
package org.agreement_technologies.service.map_negotiation;

import org.agreement_technologies.common.map_negotiation.NegotiationFactory;
import org.agreement_technologies.common.map_negotiation.PlanSelection;
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_planner.POPSearchMethod;

/**
 * NegotiationFactoryImp class initializes negotiation methods for
 * preference-based planning.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class NegotiationFactoryImp implements NegotiationFactory {

    private final int negotiationType;              // Negotiation type

    /**
     * Creates a new negotiation factory.
     *
     * @param neg Negotiation type
     * @since 1.0
     */
    public NegotiationFactoryImp(int neg) {
        this.negotiationType = neg;
    }

    /**
     * Initializes negotiation method.
     *
     * @param c Commnication infrastructure
     * @param st Search tree
     * @return Negotiation method for plan selection
     * @since 1.0
     */
    @Override
    public PlanSelection getNegotiationMethod(AgentCommunication c, POPSearchMethod st) {
        PlanSelection ps;
        switch (negotiationType) {
            case COOPERATIVE:
                ps = new CooperativePlanSelection(c, st);
                break;
            case BORDA:
                ps = new CustomBordaNegotiation(c, st, BORDA_PROPOSALS);
                break;
            default:
                ps = null;
        }
        return ps;
    }

    /**
     * Returns negotiation method type.
     *
     * @return Negotiation method identifier
     * @since 1.0
     */
    @Override
    public int getNegotiationType() {
        return this.negotiationType;
    }
}
