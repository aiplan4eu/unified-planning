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

/**
 * POPThreat class implements a threat in the plan (a step that threatens the
 * condition of a causal link).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPThreat {

    private final int threatStep;           // Index of the threatening step
    private final POPCausalLink causalLink; // Threatened causal link

    /**
     * Creates a new threat.
     * 
     * @param ts Threatening step
     * @param cl Causal link
     * @since 1.0
     */
    public POPThreat(POPStep ts, POPCausalLink cl) {
        this.threatStep = ts.getIndex();
        this.causalLink = cl;
    }

    /**
     * Returns the index of the threatening step.
     * 
     * @return Index of the threatening step
     * @since 1.0
     */
    public int getThreateningStep() {
        return this.threatStep;
    }

    /**
     * Returns the threatened causal link.
     * 
     * @return Causal link
     * @since 1.0
     */
    public POPCausalLink getCausalLink() {
        return this.causalLink;
    }
    
}
