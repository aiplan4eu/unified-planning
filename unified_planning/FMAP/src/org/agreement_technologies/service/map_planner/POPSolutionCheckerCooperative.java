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

import org.agreement_technologies.common.map_planner.PlannerFactory;

/**
 * POPSolutionCheckerCooperative class checks whether a single-agent 
 * partial-order plan is a solution. If the plan does not have open conditions 
 * nor threats, it is a solution.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
class POPSolutionCheckerCooperative extends POPSolutionChecker {

    /**
     * Checks if a given plan is a solution.
     *
     * @param candidate Plan to check
     * @param pf Planner factory
     * @return <code>true</code>, if the plan is a solution; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    @Override
    public Boolean isSolution(POPIncrementalPlan candidate, PlannerFactory pf) {
         return candidate.isSolution();
    }
    
}
