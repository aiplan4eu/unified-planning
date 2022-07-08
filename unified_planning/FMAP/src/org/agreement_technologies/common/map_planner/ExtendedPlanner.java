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

import org.agreement_technologies.service.map_planner.POPIncrementalPlan;
import org.agreement_technologies.service.map_planner.POPInternalPlan;
import org.agreement_technologies.service.tools.CustomArrayList;

/**
 * Extended planner interface.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface ExtendedPlanner extends Planner {

    /**
     * Gets the full list of causal links in the base plan.
     *
     * @return List of causal links in the base plan
     * @since 1.0
     */
    CustomArrayList<CausalLink> getTotalCausalLinks();

    /**
     * Gets the initial step of the base plan.
     *
     * @return Initial step
     * @since 1.0
     */
    Step getInitialStep();

    /**
     * Gets the final step of the base plan.
     *
     * @return Final step
     * @since 1.0
     */
    Step getFinalStep();

    /**
     * Gets the full list of orderings in the base plan.
     *
     * @return List of orderings in the base plan
     * @since 1.0
     */
    CustomArrayList<Ordering> getTotalOrderings();

    /**
     * Gets the list of predecessor plans of the current base plan in the search
     * tree.
     *
     * @return Array of predecessor plans of the current base plan
     * @since 1.0
     */
    POPIncrementalPlan[] getAntecessors();

    /**
     * Checks if new causal links have been added to build the successor plan.
     *
     * @return <code>true</code>, if new causal links have been added to build
     * the successor plan. <code>false</code>, otherwise
     * @since 1.0
     */
    boolean getModifiedCausalLinks();

    /**
     * Checks if new orderings have been added to build the successor plan.
     *
     * @return <code>true</code>, if new orderings have been added to build the
     * successor plan. <code>false</code>, otherwise
     * @since 1.0
     */
    boolean getModifiedOrderings();

    /**
     * Solves the last threat of the plan by promoting or demoting the
     * threatening step.
     *
     * @param father Base plan
     * @param isFinalStep Indicates if the final step is supported in the plan
     * @since 1.0
     */
    public void solveThreat(POPInternalPlan father, boolean isFinalStep);

    /**
     * Sets the number of causal links in the current plan.
     *
     * @param n Number of causal links
     * @since 1.0
     */
    void setNumCausalLinks(int n);

    /**
     * Sets if new causal links have been added to build the successor plan.
     *
     * @param m <code>true</code>, if new causal links have been added to build
     * the successor plan. <code>false</code>, otherwise
     * @since 1.0
     */
    void setModifiedCausalLinks(boolean m);

    /**
     * Sets the number of orderings in the current plan.
     *
     * @param n Number of orderings
     * @since 1.0
     */
    void setNumOrderings(int n);

    /**
     * Sets if new orderings have been added to build the successor plan.
     *
     * @param m <code>true</code>, if new orderings have been added to build the
     * successor plan. <code>false</code>, otherwise
     * @since 1.0
     */
    void setModifiedOrderings(boolean m);

    /**
     * Adds a new causal link to the current plan.
     *
     * @param cl New causal link
     * @since 1.0
     */
    void addCausalLink(CausalLink cl);

    /**
     * Adds a new ordering link to the current plan.
     *
     * @param o New ordering
     * @since 1.0
     */
    void addOrdering(Ordering o);

    /**
     * Gets the number of causal links in the current plan.
     *
     * @return Number of causal links
     * @since 1.0
     */
    int getNumCausalLinks();

}
