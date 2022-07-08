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
 * Generic methods to be implemented by the ordering manager classes.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface OrderingManager {

    /**
     * Checks if there is an ordering between two steps.
     * 
     * @param i First step index
     * @param j Second step index
     * @return <code>true</code>, if there is an ordering between both steps;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean checkOrdering(int i, int j);

    /**
     * Updates the manager with a new plan.
     * 
     * @param p Plan
     * @since 1.0
     */
    public void update(POPInternalPlan p);

    /**
     * Sets the number of steps in the current plan.
     * 
     * @param size Number of steps
     * @since 1.0
     */
    public void setSize(int size);

    /**
     * Gets the number of steps in the current plan.
     * 
     * @return Number of steps
     * @since 1.0
     */
    public int getSize();

    /**
     * Prepares the manager to store a new plan's orderings.
     * 
     * @since 1.0
     */
    public void newPlan();

    /**
     * Adds a new ordering between two steps.
     * 
     * @param o1 First step
     * @param o2 Second step
     * @since 1.0
     */
    public void addOrdering(int o1, int o2);

    /**
     * Removes an ordering between two steps.
     * 
     * @param o1 First step
     * @param o2 Second step
     * @since 1.0
     */
    public void removeOrdering(int o1, int o2);

    /**
     * Computes the accessibility matrix.
     * 
     * @since 1.0
     */
    public void computeAccessibilityMatrix();

    /**
     * Prepares and updates the manager with a new plan.
     * 
     * @param plan Plan
     * @since 1.0
     */
    public void rebuild(POPInternalPlan plan);

}
