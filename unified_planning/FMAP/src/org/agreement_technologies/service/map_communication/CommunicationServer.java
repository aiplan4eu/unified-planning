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
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketTimeoutException;
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_communication.Message;

/**
 * CommunicationServer class implements a thread that listens for incoming IP
 * messages.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class CommunicationServer extends Thread {

    private final ServerSocket server;          // Server socket
    private final AgentCommunication comm;      // Agent communication utility
    private final int numConnections;           // Number of connections

    /**
     * Constructor of a new communication server.
     * 
     * @param comm Agent communication utility
     * @param agentIndex Index of the owner agent
     * @param numConnections Number of needed connections
     * @throws IOException If a communication error is detected
     * @since 1.0
     */
    public CommunicationServer(AgentCommunication comm, int agentIndex, 
            int numConnections) throws IOException {
        server = new ServerSocket(AgentCommunication.BASE_PORT + agentIndex);
        this.comm = comm;
        this.numConnections = numConnections;
    }

    /**
     * Start the thread execution.
     * 
     * @since 1.0
     */
    @Override
    public void run() {
        try {
            for (int i = 0; i < numConnections; i++) {
                try {
                    Socket client = server.accept();
                    Connection newConnection = new Connection(client);
                    newConnection.start();
                } catch (SocketTimeoutException timeout) {
                }
            }
        } catch (Exception e) {
            System.out.println("SERVER ERROR: " + e);
        }
    }

    /**
     * Connection class implements a single connection with an agent.
     * 
     * @since 1.0
     */
    private class Connection extends Thread {

        private final Socket client;    // Client socket

        /**
         * Creates a new connection.
         * 
         * @param client Client socket 
         * @since 1.0
         */
        private Connection(Socket client) {
            this.client = client;
        }

        /**
         * Starts the thread execution.
         * 
         * @since 1.0
         */
        @Override
        public void run() {
            try {
                while (true) {
                    ObjectInputStream in = new ObjectInputStream(client.getInputStream());
                    Object obj = in.readObject();
                    if (obj instanceof MessageImp) {
                        comm.enqueueMsg((Message) obj);
                    } else {
                        ObjectOutputStream out = new ObjectOutputStream(client.getOutputStream());
                        out.writeObject(obj);
                        out.flush();
                    }
                }
            } catch (IOException | ClassNotFoundException ex) {
            }
        }
    }
}
