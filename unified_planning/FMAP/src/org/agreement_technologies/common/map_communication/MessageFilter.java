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

/**
 * MessageFilter interface is a filter that agents can define to retrieve a
 * specific message from the queue of received messages.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface MessageFilter {

    /**
     * Check if a given message meets the conditions of the filter.
     *
     * @param m Message to check
     * @return <code>true</code> if the message meets the conditions of the
     * filter; <code>false</code>, otherwise
     * @since 1.0
     */
    boolean validMessage(Message m);

}
