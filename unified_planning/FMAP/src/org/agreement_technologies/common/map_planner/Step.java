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
package org.agreement_technologies.common.map_planner;

/**
 * Common interface for plan steps (actions inserted in a plan).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Step {

    /**
     * Gets the name of the action associated to the step.
     *
     * @return Action name
     * @since 1.0
     */
    String getActionName();

    /**
     * Returns preconditions of an action.
     *
     * @return Preconditions array
     * @since 1.0
     */
    Condition[] getPrecs();

    /**
     * Returns effects of an action.
     *
     * @return Effects array
     * @since 1.0
     */
    Condition[] getEffs();

    /**
     * Gets index of the step in the plan.
     *
     * @return Step index
     * @since 1.0
     */
    int getIndex();

    /**
     * Returns the agent that introduced the step in the plan.
     *
     * @return Agent identifier
     * @since 1.0
     */
    String getAgent();

    /**
     * Returns the time step in which the step is scheduled.
     *
     * @return Time step
     * @since 1.0
     */
    int getTimeStep();

    /**
     * Schedules the plan step in a given time step.
     *
     * @param st Time step
     * @since 1.0
     */
    void setTimeStep(int st);

}
