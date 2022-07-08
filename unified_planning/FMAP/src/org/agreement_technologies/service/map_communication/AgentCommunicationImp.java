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
package org.agreement_technologies.service.map_communication;

import java.io.IOException;
import java.io.ObjectOutputStream;
import java.io.Serializable;
import java.net.Socket;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Vector;
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_communication.Message;
import org.agreement_technologies.common.map_communication.MessageFilter;
import org.agreement_technologies.common.map_parser.AgentList;
import org.agreement_technologies.common.map_parser.Task;

/**
 * AgentCommunicationImp class implements the interface AgentCommunication to
 * provide methods for the agents to communicate among them through sockets.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class AgentCommunicationImp implements AgentCommunication {

    // Sleeping time while waiting to reveive a message (1 millisecond)
    private static final int WAIT_TIME_MESSAGE = 1;
    // Maximum wait time for a message (30 seg.)
    private static final int WAIT_TIMEOUT_MESSAGE = 30000;

    private final String agentName;                 // Name of this agent (without suffix)
    private final ArrayList<AgentIP> otherAgents;   // Other agents in the task
    private final ArrayList<AgentIP> allAgents;     // All agents in the task
    private int batonAgent;                         // Baton agent index
    private int thisAgentIndex;                     // Index of this agent
    private Vector<Message> msgQueue;               // Message queue
    private int numMessages;                        // Number of sent messages
    private String senderAgent;                     // Agent that sent the last received message

    private CommunicationServer server;             // Communication server (thead to listen for new messages)
    private HashMap<String, String> ipAddress;      // Table that contains the IP address of each agent
    private HashMap<String, Integer> portIndex;     // Table that contains the IP port of each agent
    private HashMap<String, Integer> agentIndex;    // Table that contains the index of each agent
    private ArrayList<String> agentNames;           // Names of the agents in the task      
    private ArrayList<String> otherAgentNames;      // Names of the other agents in the task (excluding this one)
    private Socket clientSockets[];                 // Array of sockets to communicate with the other agents 

    /**
     * Constructor. Creates an agent communication utility for this agent.
     *
     * @param agentName Name of this agent
     * @since 1.0
     */
    private AgentCommunicationImp(String agentName) {
        this.agentName = agentName.toLowerCase();
        otherAgents = new ArrayList<>();
        allAgents = new ArrayList<>();
        msgQueue = new Vector<>();
        ipAddress = new HashMap<>();
        portIndex = new HashMap<>();
        agentIndex = new HashMap<>();
        agentNames = new ArrayList<>();
        otherAgentNames = new ArrayList<>();
        numMessages = 0;
        batonAgent = 0;
    }

    /**
     * Constructor. Creates an agent communication utility for this agent,
     * getting the information about the other agents from the planning task.
     *
     * @param agentName Name of this agent
     * @param task Planning task
     * @throws IOException If an error creating the CommunicationServer occurs
     * @since 1.0
     */
    public AgentCommunicationImp(String agentName, Task task) throws IOException {
        this(agentName);
        // Search for agents
        String[] objs = task.getObjects();
        for (String obj : objs) {
            if (isAgent(obj, task)) {
                if (!obj.equalsIgnoreCase(agentName)) {
                    otherAgents.add(new AgentIP(obj.toLowerCase(), "127.0.0.1"));
                }
                allAgents.add(new AgentIP(obj.toLowerCase(), "127.0.0.1"));
            }
        }
        // Sorting agents by name and setting the baton agent as the first one
        Collections.sort(allAgents);
        Collections.sort(otherAgents);
        if (allAgents.isEmpty()) {
            allAgents.add(new AgentIP(this.agentName, "127.0.0.1"));
        }
        thisAgentIndex = allAgents.indexOf(new AgentIP(this.agentName));
        for (int i = 0; i < allAgents.size(); i++) {
            ipAddress.put(allAgents.get(i).name, allAgents.get(i).ip);
            portIndex.put(allAgents.get(i).name, BASE_PORT + i);
            agentIndex.put(allAgents.get(i).name, i);
            agentNames.add(allAgents.get(i).name);
        }
        for (int i = 0; i < otherAgents.size(); i++) {
            otherAgentNames.add(otherAgents.get(i).name);
        }
        clientSockets = new Socket[allAgents.size()];
        server = new CommunicationServer(this, thisAgentIndex, otherAgentNames.size());
        server.start();
    }

    /**
     * Constructor. Creates an agent communication utility for this agent,
     * getting the information about the other agents from the AgentList.
     *
     * @param agentName Name of this agent
     * @param agList List of agents
     * @throws IOException If an error creating the CommunicationServer occurs
     * @since 1.0
     */
    public AgentCommunicationImp(String agentName, AgentList agList) throws IOException {
        this(agentName);
        // Search for agents
        for (int i = 0; i < agList.numAgents(); i++) {
            String agName = agList.getName(i).toLowerCase();
            if (!agName.equalsIgnoreCase(agentName)) {
                otherAgents.add(new AgentIP(agName, agList.getIP(i)));
            }
            allAgents.add(new AgentIP(agName, agList.getIP(i)));
        }
        // Sorting agents by name and setting the baton agent as the first one
        Collections.sort(allAgents);
        Collections.sort(otherAgents);
        if (allAgents.isEmpty()) {
            allAgents.add(new AgentIP(this.agentName, "127.0.0.1"));
        }
        thisAgentIndex = allAgents.indexOf(new AgentIP(this.agentName));
        for (int i = 0; i < allAgents.size(); i++) {
            ipAddress.put(allAgents.get(i).name, allAgents.get(i).ip);
            portIndex.put(allAgents.get(i).name, BASE_PORT + i);
            agentIndex.put(allAgents.get(i).name, i);
            agentNames.add(allAgents.get(i).name);
        }
        for (int i = 0; i < otherAgents.size(); i++) {
            otherAgentNames.add(otherAgents.get(i).name);
        }
        clientSockets = new Socket[allAgents.size()];
        server = new CommunicationServer(this, thisAgentIndex, otherAgentNames.size());
        server.start();
    }

    /**
     * Enqueues a message.
     *
     * @param message Message to enqueue.
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public void enqueueMsg(Message message) {
        msgQueue.add(message);
    }

    /**
     * Checks if an agent is already accessible.
     *
     * @param ag Agent name
     * @return <code>true</code> if the agent is ready to receive messages;
     * <code>false</code>, otherwise.
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public boolean registeredAgent(String ag) {
        int socketIndex = agentIndex.get(ag);
        try {
            if (clientSockets[socketIndex] == null) {
                clientSockets[socketIndex] = new Socket(ipAddress.get(ag), portIndex.get(ag));
            }
            return true;
        } catch (IOException ex) {
            return false;
        }
    }

    /**
     * Checks if a given object is an agent.
     *
     * @param obj Object
     * @param task Planning task
     * @return <code>true</code> if the object is an agent; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    private boolean isAgent(String obj, Task task) {
        String types[] = task.getObjectTypes(obj);
        for (String t : types) {
            if (t.equalsIgnoreCase("agent")) {
                return true;
            }
        }
        for (String t : types) {
            if (isAgentType(t, task)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Checks if a given type is a sub-type of agent.
     *
     * @param type Type
     * @param task Planning task
     * @return <code>true</code> if type if a sub-type of agent;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    private boolean isAgentType(String type, Task task) {
        String ptypes[] = task.getParentTypes(type);
        for (String t : ptypes) {
            if (t.equalsIgnoreCase("agent")) {
                return true;
            }
        }
        for (String t : ptypes) {
            if (isAgentType(t, task)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Returns the index of this agent.
     *
     * @return This agent index
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public int getThisAgentIndex() {
        return thisAgentIndex;
    }

    /**
     * Returns the name of this agent.
     *
     * @return This agent name
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public String getThisAgentName() {
        return agentName;
    }

    /**
     * Retrieves the list of names of all agents in the task.
     *
     * @return Agent list
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public ArrayList<String> getAgentList() {
        return agentNames;
    }

    /**
     * Returns the number of agents in the task.
     *
     * @return Number of agents
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public int numAgents() {
        return allAgents.size();
    }

    /**
     * Returns the name of the agent which sent the last received message.
     *
     * @return Agent name
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public String getSenderAgent() {
        return senderAgent;
    }

    /**
     * Checks if the current agent has the baton.
     *
     * @return <code>true</code> if this agent has the baton;
     * <code>false</code>, otherwise.
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public boolean batonAgent() {
        return batonAgent == thisAgentIndex;
    }

    /**
     * Returns the name of the baton agent.
     *
     * @return Name of the baton agent
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public String getBatonAgent() {
        return agentNames.get(batonAgent);
    }

    /**
     * Returns the list of agents, excluding itself.
     *
     * @return List of the other agents in the task
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public ArrayList<String> getOtherAgents() {
        return otherAgentNames;
    }

    /**
     * Returns the index of the given agent.
     *
     * @param agName Agent name
     * @return Agent index
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public int getAgentIndex(String agName) {
        return agentNames.indexOf(agName);
    }

    /**
     * Gets the total number of set messages.
     *
     * @return the number of sent messages
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public int getNumMessages() {
        return numMessages;
    }

    /**
     * Sends a message to all other agents and waits an acknowledgement.
     *
     * @param obj	Message content
     * @param waitACK	Wait for a receipt confirmation
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public void sendMessage(java.io.Serializable obj, boolean waitACK) {
        for (String toAgent : otherAgentNames) {
            sendMessage(toAgent, obj, waitACK);
        }
    }

    /**
     * Sends a message to other agent and waits an acknowledgement.
     *
     * @param toAgent	Receiver
     * @param obj	Message content
     * @param waitACK	Wait for a receipt confirmation
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public void sendMessage(String toAgent, java.io.Serializable obj, boolean waitACK) {
        int socketIndex = agentIndex.get(toAgent);
        try {
            if (clientSockets[socketIndex] == null) {
                clientSockets[socketIndex] = new Socket(ipAddress.get(toAgent), portIndex.get(toAgent));
            }
            Socket socket = clientSockets[socketIndex];
            ObjectOutputStream out = new ObjectOutputStream(socket.getOutputStream());
            out.writeObject(new MessageImp(obj, agentName));
            out.flush();
        } catch (IOException ex) {
            throw new CommunicationException(ex.toString());
        }
        if (waitACK) {
            Message resp;
            int time = 0;
            do {
                resp = checkQueue(toAgent, ACK_MESSAGE);
                wait(WAIT_TIME_MESSAGE);
                time += WAIT_TIME_MESSAGE;
                if (time >= WAIT_TIMEOUT_MESSAGE) {
                    throw new RuntimeException("Message timeout while waiting an ACK from agent " + toAgent);
                }
            } while (resp == null);
        }
        numMessages++;
    }

    /**
     * Searches a message in the queue with the given sender and content
     *
     * @param fromAgent	Sender
     * @param cont	Message content
     * @return The message if it is found, otherwise <code>null</code>
     * @since 1.0
     */
    private Message checkQueue(String fromAgent, java.io.Serializable cont) {
        int index = -1;
        Message res = null;
        for (int i = 0; i < msgQueue.size(); i++) {
            Message msg = msgQueue.get(i);
            if (msg.sender().equalsIgnoreCase(fromAgent) && cont.equals(msg.content())) {
                index = i;
                break;
            }
        }
        if (index != -1) {
            res = msgQueue.get(index);
            msgQueue.remove(index);
        }
        return res;
    }

    /**
     * Searches a message in the queue with the given sender
     *
     * @param fromAgent	Sender
     * @return The message if it is found, otherwise <code>null</code>
     * @since 1.0
     */
    private Message checkQueue(String fromAgent) {
        int index = -1;
        Message res = null;
        for (int i = 0; i < msgQueue.size(); i++) {
            Message msg = msgQueue.get(i);
            if (msg.sender().equalsIgnoreCase(fromAgent) && !ACK_MESSAGE.equals(msg.content())) {
                index = i;
                break;
            }
        }
        if (index != -1) {
            res = msgQueue.get(index);
            msgQueue.remove(index);
        }
        return res;
    }

    /**
     * Searches a message in the queue that meets the given filter
     *
     * @param filter Message filter
     * @return The message if it is found, otherwise <code>null</code>
     * @see MessageFilter
     * @since 1.0
     */
    private Message checkQueue(MessageFilter filter) {
        int index = -1;
        Message res = null;
        for (int i = 0; i < msgQueue.size(); i++) {
            Message m = msgQueue.get(i);
            if (filter.validMessage(m)) {
                index = i;
                break;
            }
        }
        if (index != -1) {
            res = msgQueue.get(index);
            msgQueue.remove(index);
        }
        return res;
    }

    /**
     * Receives a message from other agent.
     *
     * @param fromAgent Message sender
     * @param sendACK Send a confirmation when the message is received
     * @return Content of the message
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public java.io.Serializable receiveMessage(String fromAgent, boolean sendACK) {
        Message msg;
        int time = 0;
        do {
            msg = checkQueue(fromAgent);
            if (msg == null) {
                wait(WAIT_TIME_MESSAGE);
                time += WAIT_TIME_MESSAGE;
                if (time >= WAIT_TIMEOUT_MESSAGE) {
                    throw new RuntimeException("Message timeout while waiting a message from agent " + fromAgent);
                }
            }
        } while (msg == null);
        senderAgent = fromAgent.toLowerCase();
        java.io.Serializable obj = msg.content();
        if (sendACK) {
            sendMessage(msg.sender(), ACK_MESSAGE, false);
        }
        return obj;
    }

    /**
     * Receives a message from other agent that fits the given filter.
     *
     * @param filter Message filter
     * @param sendACK Send a confirmation when the message is received
     * @return Content of the message
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public Serializable receiveMessage(MessageFilter filter, boolean sendACK) {
        Message msg;
        int time = 0;
        do {
            msg = checkQueue(filter);
            if (msg == null) {
                wait(WAIT_TIME_MESSAGE);
                time += WAIT_TIME_MESSAGE;
                if (time >= WAIT_TIMEOUT_MESSAGE) {
                    throw new RuntimeException("Message timeout while waiting a filtered message");
                }
            }
        } while (msg == null);
        senderAgent = msg.sender();
        java.io.Serializable obj = msg.content();
        if (sendACK) {
            sendMessage(msg.sender(), ACK_MESSAGE, false);
        }
        return obj;
    }

    /**
     * Receives a message from other agent.
     *
     * @param sendACK Send a confirmation when the message is received
     * @return Content of the message
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public Serializable receiveMessage(boolean sendACK) {
        Message msg;
        int time = 0;
        while (msgQueue.isEmpty()) {
            wait(WAIT_TIME_MESSAGE);
            time += WAIT_TIME_MESSAGE;
            if (time >= WAIT_TIMEOUT_MESSAGE) {
                throw new RuntimeException("Message timeout while waiting a message");
            }
        }
        msg = msgQueue.get(0);
        msgQueue.remove(0);
        senderAgent = msg.sender();
        java.io.Serializable obj = msg.content();
        if (sendACK) {
            sendMessage(msg.sender(), ACK_MESSAGE, false);
        }
        return obj;
    }

    /**
     * Passes the baton to the following agent.
     *
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public void passBaton() {
        batonAgent++;
        if (batonAgent >= numAgents()) {
            batonAgent = 0;
        }
    }

    /**
     * Waits a given time in milliseconds.
     *
     * @param time Milliseconds to wait
     * @since 1.0
     */
    private void wait(int time) {
        try {
            Thread.sleep(time);
        } catch (InterruptedException e) {
        }
    }

    /**
     * Sends an acknowledgement message to other agent.
     *
     * @param toAgent Destination agent
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public void sendAck(String toAgent) {
        sendMessage(toAgent, ACK_MESSAGE, false);
    }

    /**
     * Finishes the communications.
     *
     * @see AgentCommunication
     * @since 1.0
     */
    @Override
    public void close() {
        for (Socket s : clientSockets) {
            if (s != null) {
                try {
                    s.close();
                } catch (IOException ex) {
                }
            }
        }
    }

    /**
     * CommunicationException class defines an exception that occurs during
     * communication.
     *
     * @since 1.0
     */
    public static class CommunicationException extends RuntimeException {

        // Serial number for serialization
        private static final long serialVersionUID = -7439092128849900745L;

        /**
         * Constructor of a communicatione exception.
         *
         * @param msg Error message
         * @since 1.0
         */
        public CommunicationException(String msg) {
            super(msg);
        }
    }

    /**
     * AgentIP class stores the name of an agent together with its IP address.
     *
     * @since 1.0
     */
    private static class AgentIP implements Comparable<AgentIP> {

        String name;    // Name of the agent
        String ip;      // IP address of the agent

        /**
         * Constructor.
         *
         * @param name Agent name
         * @param ip IP address
         * @since 1.0
         */
        private AgentIP(String name, String ip) {
            this.name = name;
            this.ip = ip;
        }

        /**
         * Constructor without specifying the IP address.
         *
         * @param agentName Name of the agent
         * @since 1.0
         */
        private AgentIP(String agentName) {
            this.name = agentName;
        }

        /**
         * Compares two AgentIP objects by their names.
         *
         * @param a The other AgentIP object
         * @return 0 if both agents have the same name, a value less than 0 if
         * the name of the other agent is a string lexicographically greater
         * than the name of this agent; and a value greater than 0, otherwise
         * @since 1.0
         */
        @Override
        public int compareTo(AgentIP a) {
            return name.compareTo(a.name);
        }

        /**
         * Checks if two AgentIP objects have the same name.
         *
         * @param x The other AgentIP object
         * @return <code>true</code> if both agents have the same name;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            return ((AgentIP) x).name.equals(name);
        }

        /**
         * Returns a hash code based on the name of this agentIP.
         *
         * @return Hash code of this object
         * @since 1.0
         */
        @Override
        public int hashCode() {
            return name.hashCode();
        }

        /**
         * Returns the name of this agentIP.
         *
         * @return Name of this agentIP
         * @since 1.0
         */
        @Override
        public String toString() {
            return name;
        }
    }
}
