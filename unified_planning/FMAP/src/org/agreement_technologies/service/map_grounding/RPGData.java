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
package org.agreement_technologies.service.map_grounding;

import java.io.Serializable;
import java.util.ArrayList;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.ReachedValue;

/**
 * Class for RPG data communication.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class RPGData implements Serializable {

    // Serial number for serialization
    private static final long serialVersionUID = -1957180289257722567L;
    String varName;         // Variable name
    String params[];        // Name of the parameters
    String paramTypes[][];  // Types of the parameters
    String value;           // Value name
    String valueTypes[];    // Types of the value
    int minTime[];          // Minimum time required for each agent to make the variable to take this value

    /**
     * Initializes the data from the grounded task value.
     *
     * @param v Value to communicate
     * @param gTask Grounded task
     * @param agents List of agents
     * @since 1.0
     */
    public RPGData(ReachedValue v, GroundedTask gTask, ArrayList<String> agents) {
        varName = v.getVar().getFuctionName();
        params = v.getVar().getParams();
        paramTypes = new String[params.length][];
        for (int i = 0; i < params.length; i++) {
            paramTypes[i] = v.getVar().getParamTypes(i);
        }
        value = v.getValue();
        valueTypes = gTask.getObjectTypes(value);
        minTime = new int[agents.size()];
        for (int i = 0; i < minTime.length; i++) {
            minTime[i] = v.getVar().getMinTime(value, agents.get(i));
        }
    }

    /**
     * Returns a description of this data.
     *
     * @return Data description
     * @since 1.0
     */
    @Override
    public String toString() {
        String res = "(= (" + varName;
        for (String p : params) {
            res += " " + p;
        }
        res += ") " + value + ")[" + (minTime[0] == -1 ? "-" : minTime[0]);
        for (int i = 1; i < minTime.length; i++) {
            res += "," + (minTime[i] == -1 ? "-" : minTime[i]);
        }
        return res + "]";
    }
}
