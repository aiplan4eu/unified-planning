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
package org.agreement_technologies.common.map_communication;

import java.io.Serializable;
import java.util.ArrayList;

/**
 * AgentCommunication interface provides methods for the agents to communicate
 * among them.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface AgentCommunication {

    // Base TCP/IP port. This port will be assigned to the first agent.
    // The second ageng will listen in the next port number, and so on.
    public static final int BASE_PORT = 38000;
    // Predefined messages
    public static final String ACK_MESSAGE = "<ACK>";
    public static final String END_STAGE_MESSAGE = "<END>";
    public static final String SYNC_MESSAGE = "<SYNC>";
    public static final String PASS_BATON_MESSSAGE = "<PASSBATON>";
    public static final String NO_SOLUTION_MESSAGE = "<NOPLAN>";
    public static final String YES_REPLY = "<YES>";
    public static final String NO_REPLY = "<NO>";
    public static final String NO_AGENT = "<NOAGENT>";

    /**
     * Returns the index of this agent.
     *
     * @return This agent index
     * @since 1.0
     */
    int getThisAgentIndex();

    /**
     * Returns the name of this agent.
     *
     * @return This agent name
     * @since 1.0
     */
    String getThisAgentName();

    /**
     * Retrieves the list of names of all agents in the task.
     *
     * @return Agent list
     * @since 1.0
     */
    ArrayList<String> getAgentList();

    /**
     * Returns the number of agents in the task.
     *
     * @return Number of agents
     * @since 1.0
     */
    int numAgents();

    /**
     * Returns the name of the agent which sent the last received message.
     *
     * @return Agent name
     * @since 1.0
     */
    String getSenderAgent();

    /**
     * Checks if the current agent has the baton.
     *
     * @return <code>true</code> if this agent has the baton;
     * <code>false</code>, otherwise.
     * @since 1.0
     */
    boolean batonAgent();

    /**
     * Returns the name of the baton agent.
     *
     * @return Name of the baton agent
     * @since 1.0
     */
    String getBatonAgent();

    /**
     * Returns the list of agents, excluding itself.
     *
     * @return List of the other agents in the task
     * @since 1.0
     */
    ArrayList<String> getOtherAgents();

    /**
     * Returns the index of the given agent.
     *
     * @param agName Agent name
     * @return Agent index
     * @since 1.0
     */
    int getAgentIndex(String agName);

    /**
     * Gets the total number of set messages.
     *
     * @return the number of sent messages
     * @since 1.0
     */
    int getNumMessages();

    /**
     * Sends a message to all other agents and waits an acknowledgement.
     *
     * @param obj	Message content
     * @param waitACK	Wait for a receipt confirmation
     * @since 1.0
     */
    void sendMessage(Serializable obj, boolean waitACK);

    /**
     * Sends an acknowledgement message to other agent.
     *
     * @param toAgent Destination agent
     * @since 1.0
     */
    void sendAck(String toAgent);

    /**
     * Sends a message to other agent and waits an acknowledgement.
     *
     * @param toAgent	Receiver
     * @param obj	Message content
     * @param waitACK	Wait for a receipt confirmation
     * @since 1.0
     */
    void sendMessage(String toAgent, Serializable obj, boolean waitACK);

    /**
     * Receives a message from other agent.
     *
     * @param fromAgent Message sender
     * @param sendACK Send a confirmation when the message is received
     * @return Content of the message
     * @since 1.0
     */
    Serializable receiveMessage(String fromAgent, boolean sendACK);

    /**
     * Receives a message from other agent.
     *
     * @param sendACK Send a confirmation when the message is received
     * @return Content of the message
     * @since 1.0
     */
    Serializable receiveMessage(boolean sendACK);

    /**
     * Receives a message from other agent that fits the given filter.
     *
     * @param filter Message filter
     * @param sendACK Send a confirmation when the message is received
     * @return Content of the message
     * @since 1.0
     */
    Serializable receiveMessage(MessageFilter filter, boolean sendACK);

    /**
     * Passes the baton to the following agent.
     *
     * @since 1.0
     */
    void passBaton();

    /**
     * Checks if an agent is already accessible.
     *
     * @param ag Agent name
     * @return <code>true</code> if the agent is ready to receive messages;
     * <code>false</code>, otherwise.
     * @since 1.0
     */
    public boolean registeredAgent(String ag);

    /**
     * Enqueues a message.
     *
     * @param message Message to enqueue.
     * @since 1.0
     */
    public void enqueueMsg(Message message);

    /**
     * Finishes the communications.
     *
     * @since 1.0
     */
    public void close();
}
