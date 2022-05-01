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

import org.agreement_technologies.common.map_planner.IPlan;
import java.util.ArrayList;
import java.util.BitSet;

/**
 * InternalProposal class represents an agent's plan proposal. This proposal can
 * contain private data, which must be filtered before sending to the other
 * agents.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class InternalProposal {

    public IPlan plan;                  // Plan proposal
    public BitSet achievedLandmarks;    // Set of achieved landmarks in this plan

    /**
     * Creates a new plan proposal without landmark information.
     * 
     * @param p Plan proposal 
     * @since 1.0
     */
    public InternalProposal(IPlan p) {
        this.plan = p;
        this.achievedLandmarks = null;
    }

    /**
     * Creates a new plan proposal.
     * 
     * @param p Plan proposal
     * @param achievedLandmarks Set of achieved landmarks in this plan
     * @since 1.0
     */
    public InternalProposal(IPlan p, BitSet achievedLandmarks) {
        this.plan = p;
        this.achievedLandmarks = achievedLandmarks;
    }

    /**
     * Sets the list of achieved landmarks in this plan.
     * 
     * @param list List of indexes of the achieved landmarks
     * @param numlLandmarks Total number of existing landmarks in the task
     * @since 1.0
     */
    public void setAchievedLandmarks(ArrayList<Integer> list, int numlLandmarks) {
        achievedLandmarks = new BitSet(numlLandmarks);
        for (Integer index : list) {
            achievedLandmarks.set(index);
        }
    }
    
}
