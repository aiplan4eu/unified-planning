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

/**
 * Interface for the search method; manages the storage and extraction of
 * partial order plans.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface POPSearchMethod {

    /**
     * Gets the next base plan.
     *
     * @return Next plan; <code>null</code>, if the queue is empty
     * @since 1.0
     */
    IPlan getNextPlan();

    /**
     * Gets the next plan to resume the search after finding a solution
     *
     * @return Next plan in the queue
     * @since 1.0
     */
    IPlan getNextPlanResume();

    /**
     * Checks the following plan to be processed without extracting it.
     *
     * @return Next plan
     * @since 1.0
     */
    IPlan checkNextPlan();

    /**
     * Adds to the queue the new plans generated when solving a flaw.
     *
     * @param successors Array of successors generated when a flaw of the parent
     * plan is solved
     * @since 1.0
     */
    void addSuccessors(ArrayList<IPlan> successors);

    /**
     * Adds a new plan to the queue.
     *
     * @param plan New plan
     * @since 1.0
     */
    void addPlan(IPlan plan);

    /**
     * Checks if the queue of plans is empty.
     *
     * @return <code>true</code>, if the queue is empty; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    boolean isEmpty();

    /**
     * Gets the number of plans in the queue.
     *
     * @return Number of plans
     * @since 1.0
     */
    int size();

    /**
     * Store a solution plan.
     *
     * @param solution Solution plan
     * @since 1.0
     */
    void addSolution(IPlan solution);

    /**
     * Removes a plan from the queue.
     *
     * @param planName Plan name
     * @return Deleted plan
     * @since 1.0
     */
    IPlan removePlan(String planName);

    /**
     * Returns the n first plans in the queue.
     *
     * @param n Number of plans to return
     * @return Array with the n first plans
     * @since 1.0
     */
    IPlan[] getFirstPlans(int n);

    /**
     * Gets a plan in the queue by its name.
     *
     * @param planName Plan name
     * @return Plan with the given name
     * @since 1.0
     */
    IPlan getPlanByName(String planName);

    /**
     * Gets the public evaluation function value for the given plan.
     *
     * @param p Plan
     * @return Evaluation function value for the plan
     * @since 1.0
     */
    int getPublicValue(IPlan p);

}
