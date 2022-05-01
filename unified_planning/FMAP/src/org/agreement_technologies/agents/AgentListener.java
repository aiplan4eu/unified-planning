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

/**
 * AgentListener is the interface that all planning agents must implement. These
 * methods allow the graphical interface to get information about the planning
 * progress.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface AgentListener {

    /**
     * Returns the name of the agent (without any sufix or prefix).
     *
     * @return The name of the agent.
     * @see PlanningAgent
     * @since 1.0
     */
    String getShortName();

    /**
     * Sets the listener for state changes of the agent. Usually, the listener
     * is the main graphical interface.
     *
     * @param paListener Listener for changes of state.
     * @see PlanningAgentListener
     * @see GUIPlanningAgent
     * @see PlanningAgent
     * @since 1.0
     */
    void setAgentListener(PlanningAgentListener paListener);

    /**
     * Notifies the state-change listener about the selection of a plan by the
     * user.
     *
     * @param planName Name of the selected plan.
     * @see GUITrace
     * @see PlanningAgent
     * @since 1.0
     */
    void selectPlan(String planName);

    /**
     * Returns the grounded planning task.
     *
     * @return The grounded task.
     * @see PlanningAgent
     * @see GroundedTask
     * @see GUIdisRPG
     * @since 1.0
     */
    GroundedTask getGroundedTask();

    /**
     * Returns the agent communication interface.
     *
     * @return The agent communication interface.
     * @see PlanningAgent
     * @see AgentCommunication
     * @see GUIdisRPG
     * @since 1.0
     */
    AgentCommunication getCommunication();

    /**
     * Returns the landmarks graph.
     *
     * @return The landmarks graph.
     * @see PlanningAgent
     * @see Landmarks
     * @see GUILandmarks
     * @since 1.0
     */
    Landmarks getLandmarks();
}
