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
package org.agreement_technologies.service.map_landmarks;

import java.io.Serializable;
import java.util.ArrayList;

/**
 * MessageContentLandmarkSharing class implements a message used to transmit
 * single landmarks to agents that are not in the label of the associated
 * literal.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class MessageContentLandmarkSharing implements Serializable {

    // Serial number for serialization
    private static final long serialVersionUID = 4010531211040421300L;
    private final int literalId;            // Literal identifier
    private final ArrayList<String> agents; // List of agent names

    /**
     * Creates a new message.
     * 
     * @param l Literal identifier
     * @param ag List of agents
     * @since 1.0
     */
    public MessageContentLandmarkSharing(int l, ArrayList<String> ag) {
        literalId = l;
        agents = ag;
    }

    /**
     * Gets the literal indentifier.
     * 
     * @return Literal identifier
     * @since 1.0
     */
    public int getLiteralId() {
        return literalId;
    }

    /**
     * Gets the list of agents.
     * 
     * @return List of agent names
     * @since 1.0
     */
    public ArrayList<String> getAgents() {
        return agents;
    }
}
