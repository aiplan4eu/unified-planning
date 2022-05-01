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

import java.io.Serializable;
import java.util.ArrayList;

/**
 * NewBasePlanMessage class implements a message to set the next base plan to
 * expand.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class NewBasePlanMessage implements Serializable {

    // Serial number for serialization
    private static final long serialVersionUID = 8929938148396574560L;
    // Name of the next base plan
    private String basePlanName;
    // List of changes to adjust the heuristic value of the plan proposals
    private final ArrayList<HeuristicChange> hChanges;

    /**
     * Creates a new message.
     *
     * @since 1.0
     */
    public NewBasePlanMessage() {
        hChanges = new ArrayList<>();
    }

    /**
     * Clears the list of heuristic adjustments.
     *
     * @since 1.0
     */
    public void Clear() {
        hChanges.clear();
    }

    /**
     * Sets the name of the next base plan.
     *
     * @param name Plan name
     * @since 1.0
     */
    public void setName(String name) {
        basePlanName = name;
    }

    /**
     * Gets the name of the next base plan.
     *
     * @return Plan name
     * @since 1.0
     */
    public String getPlanName() {
        return basePlanName;
    }

    /**
     * Adds an heuristic value adjustment for a given plan.
     *
     * @param name Plan name
     * @param incH Increase of its heuristic value
     * @since 1.0
     */
    public void addAdjustment(String name, int incH) {
        hChanges.add(new HeuristicChange(name, incH));
    }

    /**
     * Gets the list of changes to adjust the heuristic value of the plan
     * proposals.
     *
     * @return List of changes to adjust the heuristic value of the plan
     * proposals
     * @since 1.0
     */
    public ArrayList<HeuristicChange> getChanges() {
        return hChanges;
    }

    /**
     * Gets a description of this message.
     *
     * @return Message description
     * @since 1.0
     */
    @Override
    public String toString() {
        return basePlanName + " - " + hChanges.toString();
    }

    /**
     * HeuristicChange class represents a heuristic value adjustment for a plan.
     * 
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class HeuristicChange implements Serializable {

        // Serial number for serialization
        private static final long serialVersionUID = 5546547894487479208L;
        private final String planName;  // Plan name
        private final int incH;         // Increase in its heuristic value

        /**
         * Creates a new heuristic value adjustment.
         * 
         * @param name Plan name
         * @param h Increase in its heuristic value
         * @since 1.0
         */
        public HeuristicChange(String name, int h) {
            planName = name;
            incH = h;
        }

        /**
         * Gets the plan name.
         * 
         * @return Plan name
         * @since 1.0
         */
        public String getName() {
            return planName;
        }

        /**
         * Gets the increase in the plan's heuristic value.
         * 
         * @return Increase in the heuristic value
         * @since 1.0
         */
        public int getIncH() {
            return incH;
        }

        /**
         * Gets a description of this adjustment.
         * 
         * @return Adjsutment description
         * @since 1.0
         */
        @Override
        public String toString() {
            return "(" + planName + "," + incH + ")";
        }
    }

}
