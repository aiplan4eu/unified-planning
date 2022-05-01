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

import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_negotiation.PlanSelection;
import org.agreement_technologies.common.map_planner.Plan;
import org.agreement_technologies.service.map_planner.POPIncrementalPlan;
import org.agreement_technologies.common.map_planner.POPSearchMethod;

/**
 * Cooperative plan selection: Standard plan selection for cooperative agents
 * without negotiation.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class CooperativePlanSelection implements PlanSelection {

    private final AgentCommunication comm;      // Communication utility
    private final POPSearchMethod searchTree;   // Search tree

    /**
     * Creates a new cooperative plan selector.
     *
     * @param c Communication utility
     * @param st Search tree
     * @since 1.0
     */
    public CooperativePlanSelection(AgentCommunication c, POPSearchMethod st) {
        this.comm = c;
        this.searchTree = st;
    }

    /**
     * Selects next base plan to expand according to the cooperative criterion.
     *
     * @return Base plan to expand
     * @since 1.0
     */
    @Override
    public Plan selectNextPlan() {
        //Single agent
        if (comm.numAgents() == 1) {
            return (POPIncrementalPlan) searchTree.getNextPlan();
        }
        //Multi-agent
        POPIncrementalPlan plan;
        //Baton agent
        if (comm.batonAgent()) {
            plan = (POPIncrementalPlan) searchTree.getNextPlan();
            if (plan != null) //The baton agent sends only the name of the plan
            {
                comm.sendMessage(plan.getName(), true);
            } else {
                comm.sendMessage(AgentCommunication.NO_SOLUTION_MESSAGE, true);
            }
        } //Non-baton agent
        else {
            String planName = (String) comm.receiveMessage(comm.getBatonAgent(), true);
            if (planName.equals(AgentCommunication.NO_SOLUTION_MESSAGE)) {
                plan = null;
            } else //The agent selects and extracts a plan that matches the plan name it received
            {
                plan = (POPIncrementalPlan) searchTree.removePlan(planName);
            }
        }
        return plan;
    }

}
