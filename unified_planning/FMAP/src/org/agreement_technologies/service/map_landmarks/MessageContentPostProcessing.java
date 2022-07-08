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

/**
 * MessageContentLandmarkSharing class implements a message used to transmit
 * orderings transmitted during the landmark graph postprocessing.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class MessageContentPostProcessing implements Serializable {

    // Serial number for serialization
    private static final long serialVersionUID = 4010531211080423701L;
    private final String literal1;  // First literal in the ordering
    private final String literal2;  // Second literal in the ordering

    /**
     * Creates a new message.
     *
     * @param l1 First literal
     * @param l2 Second literal
     * @since 1.0
     */
    public MessageContentPostProcessing(String l1, String l2) {
        literal1 = l1;
        literal2 = l2;
    }

    /**
     * Gets the first literal of the ordering.
     *
     * @return First literal of the ordering
     * @since 1.0
     */
    public String getLiteral1() {
        return literal1;
    }

    /**
     * Gets the secondliteral of the ordering.
     *
     * @return second literal of the ordering
     * @since 1.0
     */
    public String getLiteral2() {
        return literal2;
    }
}
