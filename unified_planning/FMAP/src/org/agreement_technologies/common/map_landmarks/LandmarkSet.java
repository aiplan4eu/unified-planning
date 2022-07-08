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
 * LandmarkSet interface groups a set of fluents inside a landmark node.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface LandmarkSet extends Comparable<LandmarkSet> {

    /**
     * Gets the list of fluents in the set.
     *
     * @return List of fluents
     * @since 1.0
     */
    ArrayList<LandmarkFluent> getElements();

    /**
     * Gets fluent set metadata.
     *
     * @return String of fluents set data
     * @since 1.0
     */
    String identify();

    /**
     * Set the node this set of fluents belong to.
     *
     * @param newNode Owner landmark node
     * @since 1.0
     */
    void setLGNode(LandmarkNode newNode);

    /**
     * Add a landmark fluent to this set.
     *
     * @param fluent Fluent to add
     * @since 1.0
     */
    void addElement(LandmarkFluent fluent);

    /**
     * Returns the node owner of this set.
     *
     * @return Owner node
     * @since 1.0
     */
    LandmarkNode getLTNode();

    /**
     * Checks if a given fluent is inside this set.
     *
     * @param p Fluent to check
     * @return <code>true</code>, if the given fluent is in this set;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    boolean match(LandmarkFluent p);

}
