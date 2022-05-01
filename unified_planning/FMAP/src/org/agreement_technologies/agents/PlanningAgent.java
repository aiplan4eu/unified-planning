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
package org.agreement_technologies.agents;

import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_communication.PlanningAgentListener;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_landmarks.Landmarks;
import org.agreement_technologies.common.map_parser.AgentList;

/**
 * PlanningAgent represents a planning agent.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class PlanningAgent extends Thread implements AgentListener {

    protected PlanningAlgorithm alg;			// Plannning algorithm
    protected String name;                              // Agent name

    /**
     * Constructor of a planning agent 
     *
     * @param name	Agent name
     * @param domainFile	Domain filename
     * @param problemFile	Problem filename
     * @param agList List of agents in the task
     * @param waitSynch Wait for synchronized start
     * @param sameObjects Same object enabled
     * @param traceOn Activate trace
     * @param h Heuristic function
     * @param searchPerformance Search type
     * @throws Exception Platform error
     * @since 1.0
     */
    public PlanningAgent(String name, String domainFile, String problemFile, AgentList agList,
            boolean waitSynch, int sameObjects, boolean traceOn, int h, int searchPerformance)
            throws Exception {
        this.name = name.toLowerCase();
        alg = new PlanningAlgorithm(name, domainFile, problemFile, agList, waitSynch,
                sameObjects, traceOn, h, searchPerformance);
    }

    /**
     * Execution code for the planning agent.
     *
     * @since 1.0
     */
    @Override
    public void run() {
        alg.execute();
    }

    /**
     * Retrieves the agent name (without the suffix).
     *
     * @return Agent name
     * @see AgentListener
     * @since 1.0
     */
    @Override
    public String getShortName() {
        return this.name;
    }

    /**
     * Sets the agent status listener.
     *
     * @param paListener Planning agent listener
     * @see PlanningAgentListener
     * @see AgentListener
     * @since 1.0
     */
    @Override
    public void setAgentListener(PlanningAgentListener paListener) {
        alg.paListener = paListener;
    }

    /**
     * Select a plan by its name.
     *
     * @param planName Name of the plan.
     * @see AgentListener
     * @since 1.0
     */
    @Override
    public void selectPlan(String planName) {
        if (alg.paListener != null) {
            alg.paListener.selectPlan(planName);
        }
    }

    /**
     * Returns the grounded planning task.
     *
     * @return Grounded planning task
     * @see GroundedTask
     * @see AgentListener
     * @since 1.0
     */
    @Override
    public GroundedTask getGroundedTask() {
        return alg.groundedTask;
    }

    /**
     * Returns the agent communication utility.
     *
     * @return Agent communication utility.
     * @see AgentCommunication
     * @see AgentListener
     * @since 1.0
     */
    @Override
    public AgentCommunication getCommunication() {
        return alg.comm;
    }

    /**
     * Check if the planning process is finished.
     *
     * @return <code>true</code> if this agent has finished; <code>false</code>,
     * otherwise.
     * @since 1.0
     */
    public boolean isFinished() {
        return alg.status == PlanningAlgorithm.STATUS_IDLE
                || alg.status == PlanningAlgorithm.STATUS_ERROR;
    }

    /**
     * Check if an error has occurred during the planning process.
     *
     * @return <code>true</code> if this agent has finished because of an error;
     * <code>false</code>, otherwise.
     * @since 1.0
     */
    public boolean isError() {
        return alg.status == PlanningAlgorithm.STATUS_ERROR;
    }

    /**
     * Returns the gaph of landmarks.
     *
     * @return Landmarks graph.
     * @see Landmarks
     * @see AgentListener
     * @since 1.0
     */
    @Override
    public Landmarks getLandmarks() {
        return alg.landmarks;
    }

    /**
     * Stops the planning process.
     *
     * @since 1.0
     */
    void shutdown() {
        try {
            if (alg.comm != null) {
                alg.comm.close();
            }
        } catch (Exception e) {
        }
    }
}
