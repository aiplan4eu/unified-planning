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
 * MessageContentGlobalId class implements a message used to calculate global
 * identifiers for the landmarks.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class MessageContentGlobalId implements Serializable {

    // Serial version for serializarion
    private static final long serialVersionUID = 6012531211040121809L;
    // List of goblal identifiers
    private final ArrayList<GlobalIdInfo> literals;
    // Current value for global indexes
    private int currentGlobalIndex;

    /**
     * Creates a new message.
     *
     * @param l List of goblal identifiers
     * @since 1.0
     */
    public MessageContentGlobalId(ArrayList<GlobalIdInfo> l) {
        literals = l;
    }

    /**
     * Gets the list of goblal identifiers.
     *
     * @return List of goblal identifiers
     * @since 1.0
     */
    public ArrayList<GlobalIdInfo> getLiterals() {
        return literals;
    }

    /**
     * Gets the current value for global indexes.
     *
     * @return Current value for global indexes
     * @since 1.0
     */
    public int getCurrentGlobalIndex() {
        return currentGlobalIndex;
    }

    /**
     * Sets the current value for global indexes.
     *
     * @param id Current value for global indexes
     * @since 1.0
     */
    public void setCurrentGlobalIndex(int id) {
        currentGlobalIndex = id;
    }
}
