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
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_planner.PlannerFactory;

/**
 * POPSolutionCheckerPrivateGoals class checks for solutions in problems with
 * private goals.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPSolutionCheckerPrivateGoals extends POPSolutionChecker {

    private final AgentCommunication comm;    // Communication utility
    private final GroundedTask task;          // Grounded task
    private final double threshold;           // Metric threshold

    /**
     * Creates a new solution checker.
     *
     * @param c Communication utility
     * @param t Grodunded task
     */
    public POPSolutionCheckerPrivateGoals(AgentCommunication c, GroundedTask t) {
        comm = c;
        task = t;
        threshold = task.getMetricThreshold();
    }

    /**
     * Checks if a given plan is a solution.
     *
     * @param candidate Plan to check
     * @param pf Planner factory
     * @return <code>true</code>, if the plan is a solution; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    @Override
    public Boolean isSolution(POPIncrementalPlan candidate, PlannerFactory pf) {
        //Single agent
        if (comm.numAgents() == 1) {
            if (candidate.isSolution()) {
                return (task.evaluateMetric(candidate.computeState(
                        candidate.getFather().linearization(), pf), 0) - threshold) <= 0.0f;
            } else {
                return false;
            }
        }
        //Multi-agent
        //If all the global goals are fulfilled, check if the agents' preferences are met
        if (candidate.isSolution()) {
            int approvals = 0, totalAgents = comm.getAgentList().size();
            //Baton agent: receives other agents' results
            if (comm.batonAgent()) {
                //Receive results from other agents
                for (int i = 0; i < comm.getOtherAgents().size(); i++) {
                    if ((Boolean) comm.receiveMessage(true) == true) {
                        approvals++;
                    }
                }
                //Calculate own result
                double metric = task.evaluateMetric(
                        candidate.computeState(candidate.getFather().linearization(), pf), 0);
                candidate.setMetric(metric);

                if (metric - threshold <= 0.0f) {
                    approvals++;
                }
                //Check if more than the 50% of the agents satisfy their metrics
                Boolean finalRes = (float) approvals / totalAgents > 0.5f;
                //Send final result to the rest of agents
                comm.sendMessage(finalRes, false);

                return finalRes;
            } //Participant agent
            else {
                //The participant checks if its metric value reaches the threshold,
                //and communicates the result to the baton agent
                double metric = task.evaluateMetric(
                        candidate.computeState(candidate.getFather().linearization(), pf), 0);
                candidate.setMetric(metric);

                Boolean res = metric - threshold <= 0.0f;
                comm.sendMessage(comm.getBatonAgent(), res, true);

                //The participant waits for the average result computed by the baton agent result and returns it
                res = (Boolean) comm.receiveMessage(false);

                return res;
            }
        } else {
            return false;
        }
    }

}
