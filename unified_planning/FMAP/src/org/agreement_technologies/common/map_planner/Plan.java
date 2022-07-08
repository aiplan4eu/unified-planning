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

import java.util.ArrayList;

/**
 * Basic interface of partial-order plans: extended by IPlan and HPlan and
 * implemented by service.map_Planner.POPIncrementalPlan.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Plan {

    // Output types for plan printing
    static final int REGULAR = 0;
    static final int CoDMAP_CENTRALIZED = 1;
    static final int CoDMAP_DISTRIBUTED = 2;

    // Constants required for plan linearization
    static final int UNASSIGNED = -2;
    static final int INITIAL = -1;

    /**
     * Generates an array that contains all the causal links of the plan.
     *
     * @return Causal links array
     * @since 1.0
     */
    ArrayList<CausalLink> getCausalLinksArray();

    /**
     * Generates an array that contains all the steps of the plan.
     *
     * @return Steps array
     * @since 1.0
     */
    ArrayList<Step> getStepsArray();

    /**
     * Generates an array that contains all the orderings of the plan.
     *
     * @return Orderings array
     * @since 1.0
     */
    ArrayList<Ordering> getOrderingsArray();

    /**
     * Retrieves the initial step of the plan.
     *
     * @return Initial step
     * @since 1.0
     */
    Step getInitialStep();

    /**
     * Retrieves the final step of the plan.
     *
     * @return Final step
     * @since 1.0
     */
    Step getFinalStep();

    /**
     * Checks if the plan is a solution.
     *
     * @return <code>true</code>, if the plan is a solution for the task;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    boolean isSolution();

    /**
     * Returns the number of steps of the plan, excluding the initial and final
     * actions.
     *
     * @return Number of steps
     * @since 1.0
     */
    int numSteps();

    /**
     * Counts the number of steps of the plan, except for the initial and final
     * actions.
     *
     * @return Number of steps
     * @since 1.0
     */
    int countSteps();

    /**
     * Gets the name of the plan.
     *
     * @return Plan name
     * @since 1.0
     */
    String getName();

    /**
     * Verifies if the plan is at the root of the search tree.
     *
     * @return <code>true</code>, if the plan has no antecessors;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    boolean isRoot();

    /**
     * Gets g value (number of steps of the plan).
     *
     * @return g value
     * @since 1.0
     */
    int getG();

    /**
     * Gets h value (obtained through heuristic calculations).
     *
     * @return h value
     * @since 1.0
     */
    int getH();

    /**
     * If a metric is defined, returns the metric value.
     *
     * @return Metric value of the plan
     * @since 1.0
     */
    double getMetric();

    /**
     * In preference-based planning, returns the private h value of a
     * preference.
     *
     * @param prefIndex Index of the preference
     * @return h Value of the preference
     * @since 1.0
     */
    int getHpriv(int prefIndex);

    /**
     * In multi-heuristic mode, returns the secondary heuristic value calculated
     * through h_land heuristic in MH-FMAP.
     *
     * @return Secondary heuristic value
     * @since 1.0
     */
    int getHLan();

    /**
     * Assigns an h value to the plan In multi-heuristic search, it sets primary
     * and secondary heuristic values.
     *
     * @param h Primary heuristic value
     * @param hLan Secondary heuristic value
     * @since 1.0
     */
    void setH(int h, int hLan);

    /**
     * In preference-based planning, assigns an h value to a given preference.
     *
     * @param h h value
     * @param prefIndex Index of a preference
     * @since 1.0
     */
    void setHPriv(int h, int prefIndex);

    /**
     * Sets g value of the plan.
     *
     * @param g g value
     * @since 1.0
     */
    void setG(int g);

    /**
     * Gets the antecessor or parent of the plan.
     *
     * @return Parent plan, or <code>null</code> if this.isRoot()
     * @since 1.0
     */
    Plan getParentPlan();

    /**
     * Prints plan information and statistics.
     *
     * @param output Output format (REGULAR, CoDMAP_CENTRALIZED or
     * CoDMAP_DISTRIBUTED)
     * @param myagent Agent identifier
     * @param agents List of identifiers of the participating agents
     * @since 1.0
     */
    void printPlan(int output, String myagent, ArrayList<String> agents);

}
