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

/**
 * GlobalIndexVarValueInfo class implements a global index for pairs (variable,
 * value).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class GlobalIndexVarValueInfo implements Serializable {

    // Serial number for serialization
    private static final long serialVersionUID = -24058733714951171L;
    private final String varValue;  // Pair (variable, value) name
    private final int globalIndex;  // Associated global index

    /**
     * Creates a global index.
     * 
     * @param iv Global index
     * @param v Pair (variable, value) name
     * @since 1.0
     */
    public GlobalIndexVarValueInfo(int iv, String v) {
        varValue = v;
        globalIndex = iv;
    }

    /**
     * Gets the pair (variable, value) name.
     * 
     * @return Pair (variable, value) name
     * @since 1.0
     */
    public String getItem() {
        return varValue;
    }

    /**
     * Gets the associated global index.
     * 
     * @return Global index
     * @since 1.0
     */
    public Integer getGlobalIndex() {
        return globalIndex;
    }

}
