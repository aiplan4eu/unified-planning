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
package org.agreement_technologies.common.map_parser;

/**
 * AgentList interface manages a list of agents.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface AgentList {

    /**
     * Adds a new agent to the list.
     *
     * @param name Agent name
     * @param ip IP address of the agent
     * @since 1.0
     */
    void addAgent(String name, String ip);

    /**
     * Checks if the list is empty.
     *
     * @return <code>true</code>, if the list is empty; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    boolean isEmpty();

    /**
     * Get the IP address of an agent.
     * 
     * @param index Agent index (from 0 numAgents()-1)
     * @return IP address of the agent
     * @since 1.0
     */
    String getIP(int index);

    /**
     * Gets the number of agents.
     * 
     * @return Number of agents in the list
     * @since 1.0
     */
    int numAgents();

    /**
     * Gets the name of an agent.
     * 
     * @param index Agent index (from 0 numAgents()-1)
     * @return Name of the agent
     * @since 1.0
     */
    String getName(int index);

}
