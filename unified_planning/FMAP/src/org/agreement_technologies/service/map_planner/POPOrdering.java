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

import org.agreement_technologies.common.map_planner.Ordering;

/**
 * Models the ordering constraints on a partial order plan; implements the
 * Ordering interface.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPOrdering implements Ordering {

    // Serial number for serialization
    private static final long serialVersionUID = 4827398571308475818L;
    private final int step1;    // First step of the ordering
    private final int step2;    // Second step of the ordering

    /**
     * Builds the ordering data structure.
     *
     * @param s1 Index of the step s1
     * @param s2 Index of the step s2
     * @since 1.0
     */
    public POPOrdering(int s1, int s2) {
        this.step1 = s1;
        this.step2 = s2;
    }

/**
     * Returns step 1 of the ordering 1 -> 2.
     *
     * @return Step 1 of the ordering
     * @since 1.0
     */
    @Override
    public int getIndex1() {
        return this.step1;
    }

    /**
     * Returns step 2 of the ordering 1 -> 2.
     *
     * @return Step 2 of the ordering
     * @since 1.0
     */
    @Override
    public int getIndex2() {
        return this.step2;
    }

    /**
     * Gets a description of this ordering.
     * 
     * @return Ordering description
     * @since 1.0
     */
    @Override
    public String toString() {
        String res = new String();
        res += this.step1 + " -> " + this.step2;
        return res;
    }
    
}
