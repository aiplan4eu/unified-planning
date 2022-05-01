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
package org.agreement_technologies.common.map_parser;

/**
 * Ungrounded planning task. Stores the problem and domain information of a
 * parsed planning task.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Task {

    /**
     * Returns the domain name.
     *
     * @return Domain name
     * @since 1.0
     */
    String getDomainName();

    /**
     * Return the problem name.
     *
     * @return Problem name
     * @since 1.0
     */
    String getProblemName();

    /**
     * Returns the requirements list.
     *
     * @return Array of strings, each string representing a requirement
     * specified in the domain file. Supported requirements are: strips, typing,
     * negative-preconditions and object-fluents
     * @since 1.0
     */
    String[] getRequirements();

    /**
     * Returns the list of types.
     *
     * @return Array of strings, each string is a type defined in the domain
     * file
     * @since 1.0
     */
    String[] getTypes();

    /**
     * Returns the base types of a given type.
     *
     * @param type Name of the type
     * @return Array of strings which contains the super-types for the given
     * type
     * @since 1.0
     */
    String[] getParentTypes(String type);

    /**
     * Returns the list of objects.
     *
     * @return Array of string containing the names of the objects declared in
     * the domain (constants section) and problem (objects section) files
     * @since 1.0
     */
    String[] getObjects();

    /**
     * Returns the type list of a given object.
     *
     * @param objName Object name
     * @return Array of string containing the set of types of the given object
     * @since 1.0
     */
    String[] getObjectTypes(String objName);

    /**
     * Returns the list of functions (predicates are also included as they are
     * considered boolean functions).
     *
     * @return Array of functions defined in the domain file
     * @since 1.0
     */
    Function[] getFunctions();

    /**
     * Returns the list of operators.
     *
     * @return Array of operators defined in the domain file
     * @since 1.0
     */
    Operator[] getOperators();

    /**
     * Returns the shared data, which defines the information the current agent
     * can share with the other ones.
     *
     * @return Array of shared data defined in the problem file
     * @since 1.0
     */
    SharedData[] getSharedData();

    /**
     * Returns the initial state information.
     *
     * @return Array of facts
     * @since 1.0
     */
    Fact[] getInit();

    /**
     * Returns the list of belief rules.
     *
     * @return Array of belief rules
     * @since 1.0
     */
    Operator[] getBeliefs();

    /**
     * Returns the list of goals.
     *
     * @return Array of goals (facts)
     * @since 1.0
     */
    Fact[] getGoals();

    /**
     * Returns the level of self-interest of the agent. The self-interest is a
     * number from 0 to 1, where 0 means fully coopertive and 1 means fully
     * self-interested.
     *
     * @return Self-interest level
     * @since 1.0
     */
    double getSelfInterest();

    /**
     * Gets the metric threshold. This threshold indicates the minimum metric
     * value for the agent to accept a plan as a solution.
     *
     * @return Metric threshold
     * @since 1.0
     */
    double getMetricThreshold();

    /**
     * Gets the lst of preferences.
     *
     * @return List of preferences (facts)
     * @since 1.0
     */
    Fact[] getPreferences();

    /**
     * Gets the name of a given preference by its index.
     * 
     * @param index Preference index
     * @return Preference name
     * @since 1.0
     */
    String getPreferenceName(int index);

    /**
     * Gets the metric function.
     * 
     * @return Metric function
     * @since 1.0
     */
    Metric getMetric();

    /**
     * Gets the congestion operators.
     * 
     * @return Array of congestion operators
     * @since 1.0
     */
    Congestion[] getCongestion();

    /**
     * Get the initial-state numeric facts.
     * 
     * @return Array of initial-state numeric facts
     * @since 1.0
     */
    NumericFact[] getInitialNumericFacts();

}
