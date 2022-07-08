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
import org.agreement_technologies.common.map_planner.Step;

/**
 * Models the steps of a partial-order plan; implements the Step interface.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPStep implements Step {

    private final POPAction action; // Action
    private final String agent;     // Executor agent
    private final int index;        // Step index

    private int timeStep;

    /**
     * Creates a new step.
     *
     * @param act Action
     * @param i Step index
     * @param ag Executor agent
     * @since 1.0
     */
    POPStep(POPAction act, int i, String ag) {
        this.action = act;
        this.agent = ag;
        this.index = i;
        this.timeStep = -1;
    }

    /**
     * Gets the associated action.
     *
     * @return Associated action
     * @since 1.0
     */
    public POPAction getAction() {
        return this.action;
    }

    /**
     * Returns the agent that introduced the step in the plan.
     *
     * @return Agent identifier
     * @since 1.0
     */
    @Override
    public String getAgent() {
        return this.agent;
    }

    /**
     * Gets index of the step in the plan.
     *
     * @return Step index
     * @since 1.0
     */
    @Override
    public int getIndex() {
        return this.index;
    }

    /**
     * Gets the name of the associated action.
     *
     * @return Name of the associated action
     * @since 1.0
     */
    public String getName() {
        return this.action.getName();
    }

    /**
     * Gets the action preconditions.
     *
     * @return Array of action preconditions
     * @since 1.0
     */
    public POPPrecEff[] getPreconditions() {
        int i;
        POPPrecEff[] precs = new POPPrecEff[this.getAction().getPrecs().size()];

        for (i = 0; i < this.getAction().getPrecs().size(); i++) {
            precs[i] = this.getAction().getPrecs().get(i);
        }

        return precs;
    }

    /**
     * Gets the action effects.
     *
     * @return Array of action effects
     * @sine 1.0
     */
    public POPPrecEff[] getEffects() {
        int i;
        POPPrecEff[] effs = new POPPrecEff[this.getAction().getEffects().size()];

        for (i = 0; i < this.getAction().getEffects().size(); i++) {
            effs[i] = this.getAction().getEffects().get(i);
        }

        return effs;
    }

    /**
     * Gets a description of this step.
     *
     * @return Step description
     * @since 1.0
     */
    @Override
    public String toString() {
        String res;

        if (this.index == 0) {
            res = "Initial";
        } else if (this.index == 1) {
            res = "Last";
        } else {
            res = this.action.toString();
        }

        return res;
    }

    /**
     * Returns the time step in which the step is scheduled.
     *
     * @return Time step
     * @since 1.0
     */
    @Override
    public int getTimeStep() {
        return this.timeStep;
    }

    /**
     * Schedules the plan step in a given time step.
     *
     * @param ts Time step
     * @since 1.0
     */
    @Override
    public void setTimeStep(int ts) {
        this.timeStep = ts;
    }

    /**
     * Gets the name of the action associated to the step.
     *
     * @return Action name
     * @since 1.0
     */
    @Override
    public String getActionName() {
        return action.getName();
    }

    /**
     * Returns preconditions of an action.
     *
     * @return Preconditions array
     * @since 1.0
     */
    @Override
    public Condition[] getPrecs() {
        return action.getPrecConditions();
    }

    /**
     * Returns effects of an action.
     *
     * @return Effects array
     * @since 1.0
     */
    @Override
    public Condition[] getEffs() {
        return action.getEffConditions();
    }

}
