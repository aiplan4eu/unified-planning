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
 * GlobalIdInfo class allows to define global identifiers for fluents, common to
 * all agents in the task.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class GlobalIdInfo implements Serializable {

    // Serial number for serialization
    private static final long serialVersionUID = 9212531211040121809L;
    private final String literal;   // Fluent
    private final int globalId;     // Global identifier for the fluent

    GlobalIdInfo(String l, int id) {
        literal = l;
        globalId = id;
    }

    String getLiteral() {
        return literal;
    }

    public int getGlobalId() {
        return globalId;
    }
}
