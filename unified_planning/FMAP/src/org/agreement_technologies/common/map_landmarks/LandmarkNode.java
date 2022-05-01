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
package org.agreement_technologies.common.map_landmarks;

import java.util.ArrayList;

/**
 * LandmarkNode interface provides the necessary methods to work with nodes in
 * the landmarks graph (LG).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface LandmarkNode {

    // Single-literal node
    public static final boolean SINGLE_LITERAL = true;
    // Node with a disjunctive set of literals
    public static final boolean DISJUNCTION = false;

    /**
     * Gets the list of literals associated to the disjunctive landmark node.
     *
     * @return List of literals, null if the landmark is SINGLE_LITERAL
     * @since 1.0
     */
    LandmarkFluent[] getLiterals();

    /**
     * Checks if the landmark node is a goal.
     *
     * @return <code>true</code>, if the landmark is a goal; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    boolean isGoal();

    /**
     * Checks if the landmark node is single or disjunctive.
     *
     * @return SINGLE_LITERAL if the landmark is single, DISJUNCTION if the
     * landmark is disjunctive
     * @since 1.0
     */
    boolean isSingleLiteral();

    /**
     * Gets the literal associated to the single landmark node.
     *
     * @return Literal of the node, <code>null</code> if the landmark is DISJUNCTION
     * @since 1.0
     */
    LandmarkFluent getLiteral();

    /**
     * Gets local index of the landmark node.
     *
     * @return Landmark index
     * @since 1.0
     */
    int getIndex();

    /**
     * Establishes local index of the landmark node.
     *
     * @param index Landmark index
     * @since 1.0
     */
    void setIndex(int index);

    /**
     * Gets agents that share the landmark node.
     *
     * @return Arraylist of agent identifiers
     * @since 1.0
     */
    ArrayList<String> getAgents();

    /**
     * Gets landmark node metadata.
     *
     * @return String of landmark node data
     * @since 1.0
     */
    String identify();

    /**
     * Assigns list of agents that share the landmark node.
     *
     * @param agents List of agent names
     * @since 1.0
     */
    void setAgents(ArrayList<String> agents);

    /**
     * Establishes predecessor landmark nodes in the LG.
     *
     * @param antecessors Local indexes of landmark nodes that precede this
     * landmark node
     * @since 1.0
     */
    void setAntecessors(ArrayList<Integer> antecessors);

    /**
     * Returns the disjunction of a disjunctive landmark node.
     *
     * @return Disjunction of the landmark node, <code>null</code> if SINGLE_LITERAL
     * @since 1.0
     */
    LandmarkSet getDisjunction();

    /**
     * Gets list of actions that produce the literal or literals of the landmark
     * node as effects.
     *
     * @return Arraylist of producer landmark actions
     * @since 1.0
     */
    ArrayList<LandmarkAction> getProducers();

    /**
     * Sets a unique global (multi-agent) identifier for the landmark node.
     *
     * @param globalIndex Global identifier
     * @return Next global identifier
     * @since 1.0
     */
    int setGlobalId(int globalIndex);

    /**
     * Gets the unique global (multi-agent) identifier of the landmark node.
     *
     * @return Global identifier
     * @since 1.0
     */
    int getGlobalId();

}
