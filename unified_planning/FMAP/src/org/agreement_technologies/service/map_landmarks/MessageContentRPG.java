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

/**
 * MessageContentRPG class implements a message used to transmit data about the
 * level in the RPG of a fluent.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class MessageContentRPG implements java.io.Serializable {

    // Serial number for serialization
    private static final long serialVersionUID = 6010531211080464901L;
    private final String fluent;    // Fluent name
    private Integer level;          // Level in the RPG

    /**
     * Creates a new message.
     * 
     * @param var Variable name
     * @param val Value
     * @param lv Fluent level in the RPG
     * @since 1.0
     */
    MessageContentRPG(String var, String val, Integer lv) {
        fluent = var + " " + val;
        level = lv;
    }

    /**
     * Gets the fluent name.
     * 
     * @return Fluent name
     * @since 1.0
     */
    public String getFluent() {
        return fluent;
    }

    /**
     * Gets the fluent level in the RPG.
     * 
     * @return Fluent level in the RPG
     * @since 1.0
     */
    public Integer getLevel() {
        return level;
    }

    /**
     * Sets the fluent level in the RPG.
     * 
     * @param level Fluent level in the RPG
     * @since 1.0
     */
    public void setLevel(Integer level) {
        this.level = level;
    }

    /**
     * Gets a description of this message.
     * 
     * @return Message description
     * @since 1.0
     */
    @Override
    public String toString() {
        return fluent + " -> " + level;
    }
}
