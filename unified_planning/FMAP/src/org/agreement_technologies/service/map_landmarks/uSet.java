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

import java.util.ArrayList;
import org.agreement_technologies.common.map_landmarks.LandmarkFluent;
import org.agreement_technologies.common.map_landmarks.LandmarkNode;
import org.agreement_technologies.common.map_landmarks.LandmarkSet;

/**
 * uSet class implements a disjuctive set of fluents inside a landmark node.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class uSet implements LandmarkSet {

    private final String id;                      // Set identifier
    private final ArrayList<LandmarkFluent> set;  // Disjunction of landmark fluents
    private LandmarkNode node;                    // Owner landmark node

    /**
     * Create a new disjunction.
     *
     * @param l First landmark fluent in the disjuctions
     * @since 1.0
     */
    public uSet(LandmarkFluent l) {
        id = l.getVar().getFuctionName();
        set = new ArrayList<>();
        set.add(l);
    }

    /**
     * Gets fluent set metadata.
     *
     * @return String of fluents set data
     * @since 1.0
     */
    @Override
    public String identify() {
        return id;
    }

    /**
     * Add a landmark fluent to this set.
     *
     * @param l Fluent to add
     * @since 1.0
     */
    @Override
    public void addElement(LandmarkFluent l) {
        if (!set.contains(l)) {
            set.add(l);
        }
    }

    /**
     * Gets the list of fluents in the set.
     *
     * @return List of fluents
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkFluent> getElements() {
        return set;
    }

    /**
     * Set the node this set of fluents belong to.
     *
     * @param n Owner landmark node
     * @since 1.0
     */
    @Override
    public void setLGNode(LandmarkNode n) {
        node = n;
    }

    /**
     * Returns the node owner of this set.
     *
     * @return Owner node
     * @since 1.0
     */
    @Override
    public LandmarkNode getLTNode() {
        return node;
    }

    /**
     * Compares two setsof fluents.
     *
     * @param o Another set of fluent to compare with this one.
     * @return Zero if both sets are equal; 1, otherwise
     * @since 1.0
     */
    @Override
    public int compareTo(LandmarkSet o) {
        uSet u = (uSet) o;
        if (this.id.equals(u.id)) {
            if (this.set.size() == u.set.size()) {
                for (int i = 0; i < this.set.size(); i++) {
                    if (this.set.get(i).getVar() != u.set.get(i).getVar() || !this.set.get(i).getValue().equals(u.set.get(i).getValue())) {
                        return 1;
                    }
                }
                return 0;
            }
        }
        return 1;
    }

    /**
     * Checks if a given fluent is inside this set.
     *
     * @param p Fluent to check
     * @return <code>true</code>, if the given fluent is in this set;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean match(LandmarkFluent p) {
        for (LandmarkFluent l : set) {
            if (l.equals(p)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Gets a description of this set of fluent landmarks.
     * 
     * @return Description of this set of fluent landmarks 
     * @since 1.0
     */
    @Override
    public String toString() {
        String res = new String();
        res += "{";

        for (LandmarkFluent d : this.set) {
            res += d.toString() + ", ";
        }
        res += "}";

        return res;
    }
}
