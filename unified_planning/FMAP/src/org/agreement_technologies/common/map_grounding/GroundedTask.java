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
package org.agreement_technologies.common.map_grounding;

import java.util.ArrayList;
import java.util.HashMap;

/**
 * Grounded planning task.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface GroundedTask extends java.io.Serializable {

    // Types of same-objects filtering
    public static final int SAME_OBJECTS_DISABLED = 0;      // Disabled
    public static final int SAME_OBJECTS_REP_PARAMS = 1;    // Repeated parameters in the action
    public static final int SAME_OBJECTS_PREC_EQ_EFF = 2;   // Action with one precondition equals to one effect

    /**
     * Gets the domain name.
     *
     * @return Name of the domain
     * @since 1.0
     */
    String getDomainName();

    /**
     * Gets the problem name
     *
     * @return Name of the problem
     * @since 1.0
     */
    String getProblemName();

    /**
     * Gets the name of this agent.
     *
     * @return Name of this agent
     * @since 1.0
     */
    String getAgentName();

    /**
     * Returns the list of agents in the MAP task.
     *
     * @return Array of string (agent names)
     * @since 1.0
     */
    String[] getAgentNames();

    /**
     * Gets the requirement list.
     *
     * @return List of requirements
     * @since 1.0
     */
    String[] getRequirements();

    /**
     * Gets the list of types.
     *
     * @return Array of types
     * @since 1.0
     */
    String[] getTypes();

    /**
     * Gets the parent types of a given type.
     *
     * @param type Name of the type
     * @return Array of parent types
     * @since 1.0
     */
    String[] getParentTypes(String type);

    /**
     * Gets the object list (including 'undefined').
     *
     * @return Array of object names
     * @since 1.0
     */
    String[] getObjects();

    /**
     * Gets the list of types for a given object.
     *
     * @param objName Name of the object
     * @return Array of types of the object
     * @since 1.0
     */
    String[] getObjectTypes(String objName);

    /**
     * Gets the list of variables.
     *
     * @return Array of grounded variables
     * @since 1.0
     */
    GroundedVar[] getVars();

    /**
     * Gets a grounded variable through its name
     *
     * @param varName Name of the variable
     * @return Grounded variable
     * @since 1.0
     */
    GroundedVar getVarByName(String varName);

    /**
     * Gets the list of grounded actions.
     *
     * @return List of grounded actions
     * @since 1.0
     */
    ArrayList<Action> getActions();

    /**
     * Returns the list of grounded belief rules.
     *
     * @return List of grounded belief rules
     * @since 1.0
     */
    GroundedRule[] getBeliefs();

    /**
     * Returns the global goals (public goals).
     *
     * @return List of global goals
     * @since 1.0
     */
    ArrayList<GroundedCond> getGlobalGoals();

    /**
     * Creates a new grounded condition.
     *
     * @param condition Condition type (EQUAL or DISTINCT)
     * @param var Grounded variable
     * @param value Value
     * @return New grounded condition
     * @since 1.0
     */
    GroundedCond createGroundedCondition(int condition, GroundedVar var, String value);

    /**
     * Creates a new grounded effect.
     *
     * @param var Grounded variable
     * @param value Value
     * @return New grounded effect
     * @since 1.0
     */
    GroundedEff createGroundedEffect(GroundedVar var, String value);

    /**
     * Creates a new action.
     *
     * @param opName Operator name
     * @param params Action parameters
     * @param prec Action preconditions
     * @param eff Action effects
     * @return New action
     * @since 1.0
     */
    Action createAction(String opName, String params[], GroundedCond prec[],
            GroundedEff eff[]);

    /**
     * Optimize structures after grounding.
     *
     * @since 1.0
     */
    void optimize();

    /**
     * Returns the level of self-interest of the agent. The self-interest is a
     * number from 0 to 1, where 0 means fully coopertive and 1 means fully
     * self-interested.
     *
     * @return Self-interest level
     * @since 1.0
     */
    double getSelfInterestLevel();

    /**
     * Gets the metric threshold. This threshold indicates the minimum metric
     * value for the agent to accept a plan as a solution.
     *
     * @return Metric threshold
     * @since 1.0
     */
    double getMetricThreshold();

    /**
     * Indicates if the metric function contains the total-time keyword, i.e.
     * that tries to optimize the makespan.
     *
     * @return <code>true</code>, if the metric includes the total-time as a
     * parameter; <code>false</code>, otherwise
     * @since 1.0
     */
    boolean metricRequiresMakespan();

    /**
     * Evaluates the metric function in a given state.
     *
     * @param state State
     * @param makespan Makespan of the plan
     * @return Metric function value
     * @since 1.0
     */
    double evaluateMetric(HashMap<String, String> state, double makespan);

    /**
     * Evaluates the metric function in a given state.
     *
     * @param state Multi-state (it is a state where a variable can have several
     * values)
     * @param makespan Makespan of the plan
     * @return Metric function value
     * @since 1.0
     */
    double evaluateMetricMulti(HashMap<String, ArrayList<String>> state, double makespan);

    /**
     * Gets the lst of preferences.
     *
     * @return List of preferences (grounded conditions)
     * @since 1.0
     */
    ArrayList<GroundedCond> getPreferences();

    /**
     * Returns the number of preferences.
     *
     * @return Number of preferences
     * @since 1.0
     */
    int getNumPreferences();

    /**
     * Gets the cost of violating a given preference.
     *
     * @param prefIndex Preference index (in [0,getNumPreferences()-1])
     * @return Violation cost
     * @since 1.0
     */
    double getViolatedCost(int prefIndex);

    /**
     * Checks if the used model is negation by failure.
     *
     * @return <code>true</code>, if the model type is negation by failure;
     * <code>false</code> is the model is unknown by failure
     * @since 1.0
     */
    boolean negationByFailure();

}
