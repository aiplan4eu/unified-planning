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

import org.agreement_technologies.common.map_planner.CausalLink;
import org.agreement_technologies.common.map_planner.Condition;
import org.agreement_technologies.common.map_planner.Step;

/**
 * Causal link between two steps of a partial-order plan; implements the
 * CausalLink interface.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPCausalLink implements CausalLink {

    // Serial number for serialization
    private static final long serialVersionUID = -328831501262615523L;
    private final Step step1;       // Initial step of the link
    private POPPrecEff condition;   // Causal-link condition
    private final Step step2;       // Final step of the link

    /**
     * Creates a new causal link.
     * 
     * @param s1 Initial step of the link
     * @param c Causal-link condition
     * @param s2 Final step of the link
     * @since 1.0
     */
    public POPCausalLink(POPStep s1, POPPrecEff c, POPStep s2) {
        this.step1 = s1;
        this.condition = c;
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
        return this.step1.getIndex();
    }

    /**
     * Returns the precondition supported in the causal link.
     *
     * @return Precondition
     * @since 1.0
     */
    @Override
    public Condition getCondition() {
        return this.condition.getCondition();
    }

    /**
     * Returns step 2 of the ordering 1 -> 2.
     *
     * @return Step 2 of the ordering
     * @since 1.0
     */
    @Override
    public int getIndex2() {
        return this.step2.getIndex();
    }

    /**
     * Sets the causal-link condition.
     * 
     * @param v Causal-link condition
     */
    public void setCondition(POPPrecEff v) {
        this.condition = v;
    }

    /**
     * Gets a description of this casual link.
     * 
     * @return Description of this casual link
     */
    @Override
    public String toString() {
        String res = "(" + this.getIndex1() + ") -";
        res += this.condition.toString() + "-> (";
        res += this.getIndex2() + ")";

        return res;
    }

    /**
     * Returns step 1 of the causal link 1 --cond--> 2.
     *
     * @return Step 1 of the causal link
     * @since 1.0
     */
    @Override
    public Step getStep1() {
        return this.step1;
    }

    /**
     * Returns step 2 of the causal link 1 --cond--> 2.
     *
     * @return Step 2 of the causal link
     * @since 1.0
     */
    @Override
    public Step getStep2() {
        return this.step2;
    }

    /**
     * Gets the supported function (wrapper of Condition).
     *
     * @return Supported function
     * @since 1.0
     */
    @Override
    public POPFunction getFunction() {
        return condition.getFunction();
    }

    /**
     * Sets the supported function (wrapper of Condition).
     *
     * @param popFunction Supported function
     * @since 1.0
     */
    public void setFunction(POPFunction popFunction) {
        condition.setFunction(popFunction);
    }
    
}
