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
package org.agreement_technologies.common.map_communication;

import org.agreement_technologies.common.map_planner.Plan;
import org.agreement_technologies.common.map_planner.PlannerFactory;

/**
 * PlanningAgentListener interface receives status changes from a planning
 * agent.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface PlanningAgentListener {

    /**
     * Agent status change notification.
     *
     * @param status New status. See constants defined in PlanningAlgorithm
     * class
     * @see PlanningAlgorithm
     * @see GUIPlanningAgent
     * @since 1.0
     */
    void statusChanged(int status);

    /**
     * Notifies an error message.
     *
     * @param msg Error message
     * @see GUIPlanningAgent
     * @since 1.0
     */
    void notyfyError(String msg);

    /**
     * Shows a trace message.
     *
     * @param indentLevel Indentation level to show the message
     * @param msg Message to show
     * @see GUIPlanningAgent
     * @since 1.0
     */
    void trace(int indentLevel, String msg);

    /**
     * Shows a new plan in the tree.
     *
     * @param plan Plan to show
     * @param pf Planner factory
     * @see PlannerFactory
     * @see GUIPlanningAgent
     * @since 1.0
     */
    void newPlan(Plan plan, PlannerFactory pf);

    /**
     * Clears the tree and shows a single plan.
     *
     * @param plan Plan to show
     * @param pf Planner factory
     * @see PlannerFactory
     * @see GUIPlanningAgent
     * @since 1.0
     */
    void showPlan(Plan plan, PlannerFactory pf);

    /**
     * Selects a plan by its name
     *
     * @param planName Plan name
     * @see GUIPlanningAgent
     * @since 1.0
     */
    void selectPlan(String planName);
}
