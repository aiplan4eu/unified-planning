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
 * LandmarkGraph interface provides the necessary methods to work with the
 * landmarks graph (LG).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface LandmarkGraph {

    /**
     * Retrieves reasonable orderings of the LG.
     *
     * @return Arraylist of reasonable landmark orderings
     * @since 1.0
     */
    ArrayList<LandmarkOrdering> getReasonableOrderingList();

    /**
     * Retrieves necessary orderings of the LG.
     *
     * @return Arraylist of necessary landmark orderings
     * @since 1.0
     */
    ArrayList<LandmarkOrdering> getNeccessaryOrderingList();

    /**
     * Gets nodes of the LG.
     *
     * @return Arraylist of nodes of the LG
     * @since 1.0
     */
    ArrayList<LandmarkNode> getNodes();

    /**
     * Gets number of landmark nodes in the LG.
     *
     * @return Number of landmark nodes in the LG
     * @since 1.0
     */
    int numGlobalNodes();

    /**
     * Gets current number of nodes in the LG (during LG construction).
     *
     * @return Current number of landmark nodes in the LG
     * @since 1.0
     */
    int numTotalNodes();

}
