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
package org.agreement_technologies.service.map_planner;

import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_negotiation.NegotiationFactory;
import org.agreement_technologies.common.map_planner.Plan;

/**
 * MetricChecker class checks if a plan has the best average metric value.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class MetricChecker {

    double bestMetric;                        // Best average metric value
    private final AgentCommunication comm;    // Communication utility

    /**
     * Creates a new metric checker.
     *
     * @param c Communication utility
     * @since 1.0
     */
    public MetricChecker(AgentCommunication c) {
        bestMetric = Double.MAX_VALUE;
        comm = c;
    }

    /**
     * Checks if the given plan if the best solution found.
     *
     * @param solution Solution plan
     * @param type Negotiation type
     * @return <code>true</code>, if the plan is the best solution found until
     * now according to the task metric function; <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean isBestSolution(Plan solution, int type) {
        if (type == NegotiationFactory.COOPERATIVE) {
            return true;   // Without negotiation, plans found are always better
        }
        double avgMetric = solution.getMetric();
        String agentMetric;
        if (comm.batonAgent()) {
            for (int i = 0; i < comm.getOtherAgents().size(); i++) {
                agentMetric = (String) comm.receiveMessage(true);
                avgMetric += Double.parseDouble(agentMetric);
            }
            avgMetric = avgMetric / comm.getAgentList().size();
            avgMetric += ((POPIncrementalPlan) solution).computeMakespan();
            //The baton agent sends the average metric data to the rest of agents
            comm.sendMessage(Double.toString(avgMetric), true);
        } //Non-baton agent
        else {
            agentMetric = Double.toString(avgMetric);
            //Send this agent's metric to the baton agent
            comm.sendMessage(comm.getBatonAgent(), agentMetric, true);
            //Receive the average metric data from the baton agent
            agentMetric = (String) comm.receiveMessage(comm.getBatonAgent(), true);
            avgMetric = Double.parseDouble(agentMetric);
        }
        boolean isBest = avgMetric < bestMetric;
        if (isBest) {
            bestMetric = avgMetric;
        }
        return isBest;
    }

    /**
     * Gets the best achieved average metric value.
     * 
     * @return Best average metric value
     * @since 1.0
     */
    public double getBestMetric() {
        return bestMetric;
    }
    
}
