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

import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_communication.PlanningAgentListener;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.GroundedVar;
import org.agreement_technologies.common.map_heuristic.Heuristic;

/**
 * Common base class for the planner factory: manages and creates planners
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public abstract class PlannerFactory {

    // Search types
    public static final String[] SEARCH_METHODS = {"A Search"};
    public static final int A_SEARCH = 0;
    
    /**
     * Creates a new planner.
     *
     * @param gTask Grounded task
     * @param h Heuristic function
     * @param comm Communications object
     * @param agentListener Agent listener
     * @param searchType Search method
     * @return New planner
     * @since 1.0
     */
    public abstract Planner createPlanner(GroundedTask gTask, Heuristic h, AgentCommunication comm,
            PlanningAgentListener agentListener, int searchType);

    /**
     * Returns the default search method.
     * @return Default search method
     * @since 1.0
     */
    public static int getDefaultSearchMethod() {
        return A_SEARCH;
    }
    
    /**
     * Creates a new plan ordering.
     *
     * @param stepIndex1 Index of the first plan step
     * @param stepIndex2 Index of the second plan step
     * @return New ordering
     * @since 1.0
     */
    public abstract Ordering createOrdering(int stepIndex1, int stepIndex2);

    /**
     * Builds a new causal link.
     *
     * @param condition Grounded condition
     * @param step1 First plan step
     * @param step2 Second plan step
     * @return New causal link
     * @since 1.0
     */
    public abstract CausalLink createCausalLink(Condition condition, Step step1, Step step2);

    /**
     * Creates a new step
     *
     * @param stepIndex	Step index in the plan
     * @param agent	Executor agent
     * @param actionName Action name
     * @param prec	Array of preconditions
     * @param eff	Array of effects
     * @return New plan step
     * @since 1.0
     */
    public abstract Step createStep(int stepIndex, String agent, String actionName,
            Condition[] prec, Condition[] eff);

    /**
     * Gets the string key of a variable from its global identifier.
     *
     * @param code Global identifier of a variable
     * @return String key of the variable; null if the variable is not in the
     * agent's domain
     * @since 1.0
     */
    public abstract String getVarNameFromCode(int code);

    /**
     * Gets a value from its global identifier.
     *
     * @param code Global identifier of a value
     * @return Value; <code>null</code>, if the value is not in the agent's
     * domain
     * @since 1.0
     */
    public abstract String getValueFromCode(int code);

    /**
     * Gets the global identifier of a variable from its string key.
     *
     * @param var String key of a variable
     * @return Global identifier of the variable; -1 if the variable is not in
     * the agent's domain
     * @since 1.0
     */
    public abstract int getCodeFromVarName(String var);

    /**
     * Gets the global identifier of a variable.
     *
     * @param var variable
     * @return Global identifier of the variable; -1 if the variable is not in
     * the agent's domain
     * @since 1.0
     */
    public abstract int getCodeFromVar(GroundedVar var);

    /**
     * Gets the global identifier of a value.
     *
     * @param val Value
     * @return Global identifier of the value; -1 if the value is not in the
     * agent's domain
     * @since 1.0
     */
    public abstract int getCodeFromValue(String val);

    /**
     * Checks constraints between the search method and the heuristic function
     * @param search Search method
     * @param heuristic Heuristic function
     * @return <code>true</code>, if both parameters are compatible; 
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public static boolean checkSearchConstraints(int search, int heuristic) {
        return true;
    }
}
