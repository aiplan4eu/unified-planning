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
package org.agreement_technologies.service.map_heuristic;

import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_heuristic.Heuristic;
import org.agreement_technologies.common.map_heuristic.HeuristicFactory;
import org.agreement_technologies.common.map_planner.PlannerFactory;

/**
 * HeuristicFactoryImp class allows to create heuristic evaluators.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class HeuristicFactoryImp extends HeuristicFactory {

    /**
     * Gets an heuristic evaluator.
     *
     * @param heuristic Heuristic function (see constants in HeuristicFactory)
     * @param comm Communication utility
     * @param gTask Grounded task
     * @param pf Planner factory
     * @return Heuristic evaluator
     * @since 1.0
     */
    @Override
    public Heuristic getHeuristic(int heuristic, AgentCommunication comm, GroundedTask gTask,
            PlannerFactory pf) {
        Heuristic h;
        switch (heuristic) {
            case FF:
                h = new FFHeuristic(comm, gTask, pf);
                break;
            case DTG:
                h = new DTGHeuristic(comm, gTask, pf);
                break;
            case LAND_DTG_NORM:
                h = new LandmarksHeuristic(comm, gTask, false, pf);
                break;
            case LAND_DTG_INC:
                h = new LandmarksHeuristic(comm, gTask, true, pf);
                break;
            default:
                h = null;
        }
        return h;
    }
    
}
