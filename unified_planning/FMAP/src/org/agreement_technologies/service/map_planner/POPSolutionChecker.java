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

/**
 * Abstract class, partial SolutionChecker implementation.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public abstract class POPSolutionChecker implements SolutionChecker {

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
    @Override
    public Boolean keepsConstraints(POPInternalPlan incrementalCandidate, POPStep step) {
        if (incrementalCandidate.getThreats() == null) {
            return true;
        }
        if (incrementalCandidate.getThreats().size() > 0) {
            return false;
        }
        if (incrementalCandidate.getFather() == null) {
            return false;
        }
        int v = step.getAction().getPrecs().size() - (incrementalCandidate.getTotalCausalLinks().size() - incrementalCandidate.getPlanner().getNumCausalLinks());
        return v <= 0;
    }
}
