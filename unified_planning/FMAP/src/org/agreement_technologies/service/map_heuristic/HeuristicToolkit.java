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
package org.agreement_technologies.service.map_heuristic;

import java.util.ArrayList;
import java.util.HashMap;
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_planner.Condition;
import org.agreement_technologies.common.map_planner.Plan;
import org.agreement_technologies.common.map_planner.Step;

/**
 * HeuristicToolkit class provides some useful methods to evaluate plans.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class HeuristicToolkit {

    /**
     * Returns a list with the goals of the planning task.
     *
     * @param comm Communication utility
     * @param gTask Grounded task
     * @return List of goals
     * @since 1.0
     */
    @SuppressWarnings("unchecked")
    public static ArrayList<GoalCondition> computeTaskGoals(AgentCommunication comm,
            GroundedTask gTask) {
        ArrayList<GoalCondition> ocs = new ArrayList<>();
        for (GroundedCond cond : gTask.getGlobalGoals()) {
            ocs.add(new GoalCondition(cond.getVar().toString(), cond.getValue()));
        }
        if (comm.numAgents() > 1) {
            if (comm.batonAgent()) {
                for (String ag : comm.getOtherAgents()) {
                    ArrayList<GoalCondition> data = (ArrayList<GoalCondition>) comm.receiveMessage(ag, true);
                    updateConditions(ocs, data);
                }
                comm.sendMessage(ocs, true);
            } else {
                comm.sendMessage(comm.getBatonAgent(), ocs, true);
                ocs = (ArrayList<GoalCondition>) comm.receiveMessage(
                        comm.getBatonAgent(), true);
            }
        }
        return ocs;
    }

    /**
     * Computes the frontier state for a given plan.
     *
     * @param p Plan
     * @param stepsOrder Indexes of the plan steps sorted in a topological order
     * @return Frontier state: for each variable index, the index of its value
     * @since 1.0
     */
    public static HashMap<Integer, Integer> computeState(Plan p, int[] stepsOrder) {
        HashMap<Integer, Integer> varValue = new HashMap<>();
        ArrayList<Step> stepList = p.getStepsArray();
        for (int step : stepsOrder) {
            Step a = stepList.get(step);
            for (Condition eff : a.getEffs()) {
                varValue.put(eff.getVarCode(), eff.getValueCode());
            }
        }
        return varValue;
    }

    /**
     * Updates the list of conditions with the data received from other agents.
     *
     * @param ocs List of goal conditions
     * @param data Goals received from other agent
     * @since 1.0
     */
    private static void updateConditions(ArrayList<GoalCondition> ocs,
            ArrayList<GoalCondition> data) {
        for (GoalCondition cond : data) {
            boolean found = false;
            for (GoalCondition oc : ocs) {
                if (cond.equals(oc)) {
                    found = true;
                    break;
                }
            }
            if (!found) {
                ocs.add(cond);
            }
        }
    }

}
