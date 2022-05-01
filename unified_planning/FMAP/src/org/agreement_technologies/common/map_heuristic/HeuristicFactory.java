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
package org.agreement_technologies.common.map_heuristic;

import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_planner.PlannerFactory;

/**
 * HeuristicFactory base class allows to create heuristic evaluators.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public abstract class HeuristicFactory {
    
    // Heuristic functions
    public static final String[] HEURISTICS = {"FF", "DTG", "DTG + Landmarks", 
        "Inc. DTG + Landmarks"};
    public static final int FF = 0;             // FF heuristic function (only for centralized problems)
    public static final int DTG = 1;            // DTG (Domain Transition Graph) heuristic
    public static final int LAND_DTG_NORM = 2;  // DTGs + Landmarks evaluation
    public static final int LAND_DTG_INC = 3;   // DTGs integrated with landmarks

    // Heuristic information: this item checks if landmark information is used in the heuristic
    public static final int INFO_USES_LANDMARKS = 1;
    public static final int INFO_DISTRIBUTED = 2;

    /**
     * Gets an heuristic evaluator.
     * 
     * @param heuristic Heuristic function (see constants in this interface)
     * @param comm Communication utility
     * @param groundedTask Grounded task
     * @param pf Planner factory
     * @return Heuristic evaluator
     * @since 1.0
     */
    public abstract Heuristic getHeuristic(int heuristic, AgentCommunication comm, GroundedTask groundedTask,
            PlannerFactory pf);

    /**
     * Retrieves information about a given heuristic function.
     * 
     * @param heuristic Heuristic function (see constants in this interface)
     * @param infoFlag Topic to ask about. In this version, only INFO_USES_LANDMARKS
     * and INFO_DISTRIBUTED are available
     * @return Object with the equested information
     * @since 1.0
     */
    public static Object getHeuristicInfo(int heuristic, int infoFlag) {
        Object res = null;
        if (infoFlag == INFO_USES_LANDMARKS) {
            switch (heuristic) {
                case FF:
                    res = "no";
                    break;
                case DTG:
                    res = "no";
                    break;
                case LAND_DTG_NORM:
                    res = "yes";
                    break;
                case LAND_DTG_INC:
                    res = "yes";
                    break;
            }
        } else if (infoFlag == INFO_DISTRIBUTED) {
            switch (heuristic) {
                case FF:
                    res = "no";
                    break;
                case DTG:
                    res = "yes";
                    break;
                case LAND_DTG_NORM:
                    res = "yes";
                    break;
                case LAND_DTG_INC:
                    res = "yes";
                    break;
            }
        }
        return res;
    }   
 
}
