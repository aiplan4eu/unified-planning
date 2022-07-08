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

import org.agreement_technologies.common.map_planner.Condition;
import org.agreement_technologies.common.map_planner.OpenCondition;

/**
 * Open condition definition.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPOpenCondition implements OpenCondition {

    // Condition type
    static final int EQUAL = 1;
    static final int DISTINCT = 2;

    private final POPPrecEff precEff;   // Precondition
    private POPStep step;               // Associated step
    private Boolean isGoal;             // Indicates if the precondition is a goal

    /**
     * Constructor.
     *
     * @param cond Reference to the original precondition
     * @param s Associated step
     * @param g Flag that indicates if the open condition is a goal
     * @since 1.0
     */
    public POPOpenCondition(POPPrecEff cond, POPStep s, Boolean g) {
        this.step = s;
        this.isGoal = g;
        this.precEff = cond;
    }

    /**
     * Gets the open precondition.
     *
     * @return Preondition
     * @since 1.0
     */
    @Override
    public Condition getCondition() {
        return precEff.getCondition();
    }

    /**
     * Gets the original precondition.
     *
     * @return Original precondition
     * @since 1.0
     */
    public POPPrecEff getPrecEff() {
        return precEff;
    }

    /**
     * Gets the plan step associated to the open precondition.
     *
     * @return Affected plan step
     * @since 1.0
     */
    @Override
    public POPStep getStep() {
        return step;
    }

    /**
     * Sets the plan step associated to the open precondition.
     *
     * @param step Affected plan step
     * @since 1.0
     */
    public void setStep(POPStep step) {
        this.step = step;
    }

    /**
     * Checks if the open condition is a goal.
     *
     * @return <code>true</code>, if the condition is a goal;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public Boolean isGoal() {
        return this.isGoal;
    }

    /**
     * States that the precondition is a goal.
     * 
     * @since 1.0
     */
    public void setGoal() {
        this.isGoal = true;
    }
    
    /**
     * States that the precondition is not a goal.
     * 
     * @since 1.0
     */
    public void setNotGoal() {
        this.isGoal = false;
    }

    /**
     * Gets a description of this condition.
     * 
     * @return Condition description
     * @since 1.0
     */
    @Override
    public String toString() {
        return this.precEff.toString();
    }

}
