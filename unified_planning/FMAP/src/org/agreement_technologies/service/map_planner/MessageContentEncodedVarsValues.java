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
package org.agreement_technologies.service.map_planner;

import java.io.Serializable;
import java.util.ArrayList;

/**
 * MessageContentEncodedVarsValues class implements a message to encode pairs of
 * (variable, value) with indexes, in order to keep privacy.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class MessageContentEncodedVarsValues implements Serializable {

    // Indexes for pairs of (variable, value)
    ArrayList<ArrayList<GlobalIndexVarValueInfo>> globalIndexes;
    // Current value of the counter for global indexes of variables
    private final int currentGlobalIndexVars;
    // Current value of the counter for global indexes of values
    private final int currentGlobalIndexValues;

    /**
     * Creates a new message.
     * 
     * @param ids Indexes for pairs of (variable, value)
     * @param iv Current value of the counter for global indexes of variables
     * @param ival Current value of the counter for global indexes of values
     * @since 1.0
     */
    public MessageContentEncodedVarsValues(ArrayList<ArrayList<GlobalIndexVarValueInfo>> ids, 
            int iv, int ival) {
        globalIndexes = ids;
        currentGlobalIndexVars = iv;
        currentGlobalIndexValues = ival;
    }

    /**
     * Gets the list of indexes for pairs of (variable, value).
     * 
     * @return List of indexes for pairs of (variable, value)
     * @since 1.0
     */
    public ArrayList<ArrayList<GlobalIndexVarValueInfo>> getGlobalIndexes() {
        return globalIndexes;
    }

    /**
     * Gets the current value of the counter for global indexes of variables.
     * 
     * @return Current value of the counter for global indexes of variables
     * @since 1.0
     */
    public int getCurrentGlobalIndexVars() {
        return currentGlobalIndexVars;
    }

    /**
     * Gets the current value of the counter for global indexes of values.
     * 
     * @return Current value of the counter for global indexes of values
     * @since 1.0
     */
    public int getCurrentGlobalIndexValues() {
        return currentGlobalIndexValues;
    }
    
}
