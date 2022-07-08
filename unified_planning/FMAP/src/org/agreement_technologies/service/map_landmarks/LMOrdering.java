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
package org.agreement_technologies.service.map_landmarks;

import org.agreement_technologies.common.map_landmarks.LandmarkNode;
import org.agreement_technologies.common.map_landmarks.LandmarkOrdering;

/**
 * LMOrdering class implements orderings between landmark nodes in the landmarks
 * graph (LG).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class LMOrdering implements LandmarkOrdering {

    private final LandmarkNode node1;   // Initial node of the ordering
    private final LandmarkNode node2;   // Final node of the ordering
    private final int type;             // Ordering type (NECESSARY or REASONABLE)

    /**
     * Creates a new ordering.
     *
     * @param i1 Initial node
     * @param i2 Final node
     * @param type Ordering type (NECESSARY or REASONABLE)
     * @since 1.0
     */
    public LMOrdering(LandmarkNode i1, LandmarkNode i2, int type) {
        node1 = i1;
        node2 = i2;
        this.type = type;
    }

    /**
     * Gets a description of this ordering.
     *
     * @return Description of this ordering
     * @since 1.0
     */
    @Override
    public String toString() {
        return node1.toString() + " -> " + node2.toString();
    }

    /**
     * Gets the initial node.
     *
     * @return Initial node of this ordering
     * @since 1.0
     */
    @Override
    public LandmarkNode getNode1() {
        return node1;
    }

    /**
     * Gets the final node.
     *
     * @return Final node of this ordering
     * @since 1.0
     */
    @Override
    public LandmarkNode getNode2() {
        return node2;
    }

    /**
     * Gets the type of this ordering.
     *
     * @return Ordering type (NECESSARY or REASONABLE)
     * @since 1.0
     */
    @Override
    public int getType() {
        return type;
    }

    /**
     * Check if two orderings are equal.
     *
     * @param x Another ordering to compare with this one
     * @return <code>true</code>, if both orderings have the same initial and
     * final node; <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean equals(Object x) {
        LandmarkOrdering o = (LandmarkOrdering) x;
        return node1.getIndex() == o.getNode1().getIndex()
                && node2.getIndex() == o.getNode2().getIndex();
    }
}
