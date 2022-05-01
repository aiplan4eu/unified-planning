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

/**
 * LandmarkOrdering interface provides the necessary methods to work with
 * orderings between landmark nodes in the landmarks graph (LG).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface LandmarkOrdering {

    int NECESSARY = 1;      // Necessary ordering
    int REASONABLE = 2;     // Reasonable ordering

    /**
     * Gets landmark 1 of the landmark ordering 1 -> 2.
     *
     * @return Exit landmark node of the ordering
     * @since 1.0
     */
    LandmarkNode getNode1();

    /**
     * Gets landmark 2 of the landmark ordering 1 -> 2.
     *
     * @return Destination landmark node of the ordering
     * @since 1.0
     */
    LandmarkNode getNode2();

    /**
     * Retrieves type of landmark ordering, either NECESSARY or REASONABLE.
     *
     * @return Ordering type
     * @since 1.0
     */
    int getType();
    
}
