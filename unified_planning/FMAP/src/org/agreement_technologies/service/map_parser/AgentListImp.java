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
package org.agreement_technologies.service.map_parser;

import java.util.ArrayList;
import org.agreement_technologies.common.map_parser.AgentList;

/**
 * AgentListImp class manages a list of agents.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class AgentListImp implements AgentList {

    /**
     * Agent class stores information about an agent: name and IP address.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    private static class Agent {

        String name;    // Agent name
        String ip;      // IP address

        /**
         * Creates a new agent.
         *
         * @param name Agent name
         * @param ip IP address
         * @since 1.0
         */
        private Agent(String name, String ip) {
            this.name = name;
            this.ip = ip;
        }

        /**
         * Gets a description of this agent.
         *
         * @return Description of this agent
         * @since 1.0
         */
        @Override
        public String toString() {
            return name + ":" + ip;
        }
    }

    private final ArrayList<Agent> list;    // List of agents

    /**
     * Creates a new empty list of agents.
     *
     * @since 1.0
     */
    public AgentListImp() {
        list = new ArrayList<>();
    }

    /**
     * Adds a new agent to the list.
     *
     * @param name Agent name
     * @param ip IP address of the agent
     * @since 1.0
     */
    @Override
    public void addAgent(String name, String ip) {
        list.add(new Agent(name, ip));
    }

    /**
     * Checks if the list is empty.
     *
     * @return <code>true</code>, if the list is empty; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    @Override
    public boolean isEmpty() {
        return list.isEmpty();
    }

    /**
     * Gets a description of this agent list.
     *
     * @return Description of this agent list
     * @since 1.0
     */
    @Override
    public String toString() {
        String s = "";
        for (Agent a : list) {
            s += "[" + a + "]";
        }
        return s;
    }

    /**
     * Get the IP address of an agent.
     *
     * @param index Agent index (from 0 numAgents()-1)
     * @return IP address of the agent
     * @since 1.0
     */
    @Override
    public String getIP(int index) {
        return list.get(index).ip;
    }

    /**
     * Gets the number of agents.
     *
     * @return Number of agents in the list
     * @since 1.0
     */
    @Override
    public int numAgents() {
        return list.size();
    }

    /**
     * Gets the name of an agent.
     *
     * @param index Agent index (from 0 numAgents()-1)
     * @return Name of the agent
     * @since 1.0
     */
    @Override
    public String getName(int index) {
        return list.get(index).name;
    }
}
