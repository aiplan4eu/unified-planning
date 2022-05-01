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

import java.io.Serializable;
import org.agreement_technologies.common.map_communication.Message;

/**
 * MessageImp class implements the Message interface. This class represents a
 * message, with a sender agent and a content.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class MessageImp implements Message {

    final Serializable content;     // Content of the message
    final String sender;            // Sender agent

    /**
     * Creates a new message.
     *
     * @param obj Content of the message
     * @param agentName Name of the sender agent
     * @since 1.0
     */
    MessageImp(Serializable obj, String agentName) {
        content = obj;
        sender = agentName;
    }

    /**
     * Gets the content of the message.
     *
     * @return Content of the message.
     * @since 1.0
     */
    @Override
    public Serializable content() {
        return content;
    }

    /**
     * Gets the sender of the message.
     *
     * @return Name of the sender agent
     * @since 1.0
     */
    @Override
    public String sender() {
        return sender;
    }
}
