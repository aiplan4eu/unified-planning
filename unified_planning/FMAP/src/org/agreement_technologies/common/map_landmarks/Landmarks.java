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
package org.agreement_technologies.common.map_landmarks;

import java.util.ArrayList;

/**
 * Landmarks is the main interface to calculate and work with landmarks.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Landmarks {

    int NECESSARY_ORDERINGS = 1;    // Necessary orderings
    int REASONABLE_ORDERINGS = 2;   // Reasonable orderings
    int ALL_ORDERINGS = 3;          // All types of orderings

    /**
     * Retrieves all the orderings between landmarks in the LG.
     *
     * @param type Type of orderings to return (NECESSARY_ORDERINGS,
     * REASONABLE_ORDERINGS or ALL_ORDERINGS)
     * @param onlyGoals If true, return only orderings that affect the task
     * goals; otherwise, return all the orederings
     * @return List of orderings between landmarks
     * @since 1.0
     */
    ArrayList<LandmarkOrdering> getOrderings(int type, boolean onlyGoals);

    /**
     * Removes transitive orderings between landmarks.
     * 
     * @since 1.0
     */
    void filterTransitiveOrders();

    /**
     * Removes cycles in the LG.
     * 
     * @since 1.0
     */
    void removeCycles();

    /**
     * Retrieves nodes of the LG.
     *
     * @return List of landmark nodes (single and disjunctive landmarks)
     * @since 1.0
     */
    ArrayList<LandmarkNode> getNodes();

    /**
     * Gets the total number of single and disjunctive landmarks.
     *
     * @return Number of landmarks of the LG
     * @since 1.0
     */
    int numGlobalNodes();

    /**
     * Returns current number of landmarks (during plan construction).
     *
     * @return Number of landmarks of the LG
     * @since 1.0
     */
    int numTotalNodes();
    
}
