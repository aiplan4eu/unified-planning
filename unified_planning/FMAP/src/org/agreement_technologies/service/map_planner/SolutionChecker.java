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
 * SolutionChecker interface allows to check if a plan is a solution.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface SolutionChecker {

    /**
     * Checks if a given plan is a solution.
     *
     * @param candidate Plan to check
     * @param pf Planner factory
     * @return <code>true</code>, if the plan is a solution; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    Boolean isSolution(POPIncrementalPlan candidate, PlannerFactory pf);

    /**
     * Checks if the plan meets the additional constraints (as not to exceed a
     * given limit on the number of steps fixed in advance).
     *
     * @param incrementalCandidate Plan to check
     * @param step Added step
     * @return <code>true</code>, if the plan meets all the fixed constraints;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    Boolean keepsConstraints(POPInternalPlan incrementalCandidate, POPStep step);
}
