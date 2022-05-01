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
package org.agreement_technologies.service.map_landmarks;

import java.io.Serializable;
import java.util.ArrayList;

/**
 * MessageContentLandmarkGraph class implements a message used to exchange data
 * from the landmarks graph.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class MessageContentLandmarkGraph implements Serializable {

    // Constants for message types
    public static final int COMMON_PRECS_STAGE = 0;
    public static final int VERIFICATION_STAGE = 1;
    public static final int IS_LANDMARK = 2;
    public static final int IS_NOT_LANDMARK = 3;
    public static final int RPG_UNCHANGED = 4;
    public static final int NO_PRODUCER_ACTIONS = 5;
    public static final int CHANGE_LEVEL = 6;
    public static final int PASS_BATON = 7;
    public static final int END_PROCEDURE = 8;

    private final int type;                             // Message type
    private final Integer nextLevel;                    // Number of the next level
    private final String literal;                       // Fluent
    private final ArrayList<LMLiteralInfo> literals;    // List of information about fluent landmarks
    private final ArrayList<String> reachedGoals;       // List of achieved top-level goals
    private final String sender;                        // Sender agent
    private final ArrayList<LMLiteralInfo> uSets;       // List of disjunctive landmarks
    private final ArrayList<String> RPGLiterals;        // List of fluents from the RPG
    private final Integer globalIndex;                  // Global index

    /**
     * Creates a new message.
     *
     * @param gi Global index
     * @param l Fluent
     * @param c List of information about fluent landmarks
     * @param u List of disjunctive landmarks
     * @param r List of fluents from the RPG
     * @param g List of achieved top-level goals
     * @param a Sender agent
     * @param ll Number of the next level
     * @param t Message type
     * @since 1.0
     */
    public MessageContentLandmarkGraph(Integer gi, String l, ArrayList<LMLiteralInfo> c,
            ArrayList<LMLiteralInfo> u, ArrayList<String> r, ArrayList<String> g,
            String a, Integer ll, int t) {
        globalIndex = gi;
        nextLevel = ll;
        type = t;
        literal = l;
        literals = c;
        uSets = u;
        sender = a;
        reachedGoals = g;
        RPGLiterals = r;
    }

    /**
     * Gets the global index.
     *
     * @return Global index
     * @since 1.0
     */
    public int getGlobalIndex() {
        return globalIndex;
    }

    /**
     * Gets the list of information about fluent landmarks.
     *
     * @return List of information about fluent landmarks
     * @since 1.0
     */
    public ArrayList<LMLiteralInfo> getLiterals() {
        return literals;
    }

    /**
     * Gets the list of disjunctive landmarks.
     *
     * @return List of disjunctive landmarks
     * @since 1.0
     */
    public ArrayList<LMLiteralInfo> getDisjunctions() {
        return uSets;
    }

    /**
     * Gets the list of fluents from the RPG.
     *
     * @return List of fluents from the RPG
     * @since 1.0
     */
    public ArrayList<String> getRPGLiterals() {
        return RPGLiterals;
    }

    /**
     * Gets the list of achieved top-level goals.
     *
     * @return List of achieved top-level goals
     * @since 1.0
     */
    public ArrayList<String> getReachedGoals() {
        return reachedGoals;
    }

    /**
     * Gets the sender agent.
     *
     * @return Name of the sender agent
     * @since 1.0
     */
    public String getAgent() {
        return sender;
    }

    /**
     * Gets the fluent.
     *
     * @return Fluent description
     * @since 1.0
     */
    public String getLiteral() {
        return literal;
    }

    /**
     * Gets the number of the next level.
     *
     * @return Number of the next level
     * @since 1.0
     */
    public int getNextLevelSize() {
        return nextLevel;
    }

    /**
     * Gets the message type.
     *
     * @return Message type
     * @since 1.0
     */
    public int getMessageType() {
        return type;
    }
}
