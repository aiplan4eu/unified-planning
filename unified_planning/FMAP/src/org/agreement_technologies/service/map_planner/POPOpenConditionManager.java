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

import java.util.Iterator;
import java.util.ArrayList;
import org.agreement_technologies.common.map_planner.OpenCondition;

/**
 * Precondition manager interface; stores and managaes the open conditions of a
 * plan.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface POPOpenConditionManager {

    /**
     * Extracts the next open condition.
     *
     * @return Open condition
     * @since 1.0
     */
    POPOpenCondition getNextOpenCondition();

    /**
     * Consults, without removing, the next open condition.
     *
     * @return Open condition
     * @since 1.0
     */
    POPOpenCondition checkNextOpenCondition();

    /**
     * Adds the preconditions of the initial plan to the manager.
     *
     * @param precs List of open conditions to add
     * @since 1.0
     */
    void addInitialOpenConditions(ArrayList<OpenCondition> precs);

    /**
     * Adds the new open conditions to the successor plan.
     *
     * @param precs List of open conditions to add
     * @since 1.0
     */
    void addOpenConditions(ArrayList<OpenCondition> precs);

    /**
     * Cleans all the open conditions of the plan.
     *
     * @since 1.0
     */
    void clearOpenConditions();

    /**
     * Cleans the open condition and restores the corresponding ones to the base
     * plan.
     *
     * @since 1.0
     */
    void restoreOpenConditions();

    /**
     * Gets an iteraton on the open conditions.
     *
     * @return Iterator
     * @since 1.0
     */
    Iterator<OpenCondition> getIterator();

    /**
     * Returns the number of open conditions in the plan.
     *
     * @return Number of open conditions
     * @since 1.0
     */
    int size();

    /**
     * Gets the list of open conditions in the plan.
     *
     * @return List of open conditions
     * @since 1.0
     */
    ArrayList<OpenCondition> getList();

    /**
     * Sorts the open conditions by safety.
     *
     * @since 1.0
     */
    void update();

    /**
     * Gets the list of open conditions in the plan.
     *
     * @return Array of open conditions
     * @since 1.0
     */
    OpenCondition[] getOpenConditions();

}
