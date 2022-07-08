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
package org.agreement_technologies.common.map_heuristic;

import java.util.ArrayList;
import java.util.BitSet;

/**
 * Heuristic interface provides the necessary methods to compute heuristic
 * values.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Heuristic {

    // Infinite value for shortest path calculations
    static final int INFINITE = (Integer.MAX_VALUE) / 3;
    // Code for requests related to landmarks
    static final int INFO_LANDMARKS = 1;

    /**
     * Heuristic evaluation of a plan. The resulting value is stored inside the
     * plan (see setH method in Plan interface).
     *
     * @param p Plan to evaluate
     * @param threadIndex Thread index, for multi-threading purposes
     * @since 1.0
     */
    void evaluatePlan(HPlan p, int threadIndex);

    /**
     * Multi-heuristic evaluation of a plan, also evaluates the remaining
     * landmarks to achieve. The resulting value is stored inside the plan (see
     * setH method in Plan interface).
     *
     * @param p Plan to evaluate
     * @param threadIndex Thread index, for multi-threading purposes
     * @param achievedLandmarks List of already achieved landmarks
     * @since 1.0
     */
    void evaluatePlan(HPlan p, int threadIndex, ArrayList<Integer> achievedLandmarks);

    /**
     * Heuristically evaluates the cost of reaching the agent's private goals.
     *
     * @param p Plan to evaluate
     * @param threadIndex Thread index, for multi-threading purposes
     * @since 1.0
     */
    void evaluatePlanPrivacy(HPlan p, int threadIndex);

    /**
     * Synchronization step after the distributed heuristic evaluation.
     *
     * @since 1.0
     */
    void waitEndEvaluation();

    /**
     * Begining of the heuristic evaluation stage.
     *
     * @param basePlan Base plan, whose successors will be evaluated
     * @since 1.0
     */
    void startEvaluation(HPlan basePlan);

    /**
     * Gets information about a given topic.
     *
     * @param infoFlag Topic to get information about. In this version, only
     * landmarks information (see INFO_LANDMARKS constant) is available
     * @return Object with the requested information
     * @since 1.0
     */
    Object getInformation(int infoFlag);

    /**
     * Checks if the current heuristic evaluator supports multi-threading.
     *
     * @return <code>true</code>, if multi-therading evaluation is available.
     * <code>false</code>, otherwise
     * @since 1.0
     */
    boolean supportsMultiThreading();

    /**
     * Checks if the current heuristic evaluator requieres an additional stage
     * for landmarks evaluation.
     *
     * @return <code>true</code>, if a landmarks evaluation stage is required.
     * <code>false</code>, otherwise
     * @since 1.0
     */
    boolean requiresHLandStage();

    /**
     * Returns the total number of global (public) landmarks.
     * 
     * @return Total number of global (public) landmarks
     * @since 1.0
     */
    int numGlobalLandmarks();

    /**
     * Returns the new landmarks achieved in this plan.
     * 
     * @param plan Plan to check
     * @param achievedLandmarks Already achieved landmarks
     * @return List of indexes of the new achieved landmarks
     * @since 1.0
     */
    ArrayList<Integer> checkNewLandmarks(HPlan plan, BitSet achievedLandmarks);

}
