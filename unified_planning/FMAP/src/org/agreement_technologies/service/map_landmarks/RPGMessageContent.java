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

import java.util.ArrayList;

/**
 * RPGMessageContent class implements a message used to transmit data about the
 * levels in the RPG of several fluents.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class RPGMessageContent implements java.io.Serializable {

    // Serial number for serialization
    private static final long serialVersionUID = 6010531211010261701L;
    private final boolean RPGChanged;                   // Indicates if there are changes in the RPG
    private final ArrayList<MessageContentRPG> data;    // List of fluent levels

    /**
     * Creates a new message.
     *
     * @param dataToSend List of fluent levels
     * @param changed <code>true</code>, if there are changes in the RPG;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    RPGMessageContent(ArrayList<MessageContentRPG> dataToSend, boolean changed) {
        RPGChanged = changed;
        data = dataToSend;
    }

    /**
     * Adds new fluent levels to the message.
     *
     * @param d Fluent levels to add
     * @since 1.0
     */
    public void addRPGData(MessageContentRPG d) {
        data.add(d);
    }

    /**
     * Gets the list of luent levels.
     *
     * @return List of fluent levels
     * @since 1.0
     */
    public ArrayList<MessageContentRPG> getData() {
        return data;
    }

    /**
     * Checks if the RPG has changed.
     *
     * @return <code>true</code>, if there are changes in the RPG;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean isRPGChanged() {
        return RPGChanged;
    }
}
