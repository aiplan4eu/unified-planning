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
package org.agreement_technologies.common.map_planner;

import java.util.ArrayList;
import org.agreement_technologies.common.map_heuristic.HPlan;
import org.agreement_technologies.service.tools.CustomArrayList;

/**
 * IPlan interface provides methods to work with incremental plans.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface IPlan extends HPlan {

    /**
     * Gets the full list of causal links in the plan.
     *
     * @return List of causal links in the plan
     * @since 1.0
     */
    CustomArrayList<CausalLink> getTotalCausalLinks();

    /**
     * Gets the full list of steps in the plan.
     *
     * @return List of steps in the plan
     * @since 1.0
     */
    ArrayList<Step> getTotalSteps();

    /**
     * Gets the full list of orderings in the plan.
     *
     * @return List of orderings in the plan
     * @since 1.0
     */
    CustomArrayList<Ordering> getTotalOrderings();

    /**
     * Sets the name for this plan.
     * 
     * @param n Child index (children plans are numbered from zero)
     * @param father Parent plan
     * @since 1.0
     */
    void setName(int n, Plan father);

    /**
     * Gets the parent plan.
     * 
     * @return Parent plan
     * @since 1.0
     */
    Plan getFather();
    
}
