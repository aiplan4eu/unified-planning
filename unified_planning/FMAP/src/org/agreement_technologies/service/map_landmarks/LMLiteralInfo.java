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
import org.agreement_technologies.common.map_landmarks.LandmarkFluent;

/**
 * LMLiteralInfo class allows to exchange information about landmark fluents
 * between agents.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class LMLiteralInfo implements Serializable {

    // Serial number for serialization
    private static final long serialVersionUID = 5010121211010241301L;
    private final String literal;               // Fluent description
    private final String var;                   // Variable name
    private final String value;                 // Value
    private final String function;              // Fluent function
    private final String agent;                 // Sender agent
    private final ArrayList<String> agents;     // Agents that can share this fluent
    private int level;                          // Level of this landmark in the RPG
    private boolean isGoal;                     // Indicates if this fluent is a top-level goal

    /**
     * Creates new information about a landmark fluent.
     *
     * @param l Landmark fluent
     * @param ag Sender agent
     * @param ags Agents that can share this fluent
     * @since 1.0
     */
    public LMLiteralInfo(LandmarkFluent l, String ag, ArrayList<String> ags) {
        literal = l.toString();
        var = l.getVarName();
        value = l.getValue();
        function = l.getVar().getFuctionName();
        agent = ag;
        agents = ags;
        level = l.getLevel();
        isGoal = l.isGoal();
    }

    /**
     * Creates new information about a landmark fluent.
     *
     * @param f Function of the variable
     * @param ag Agents that can share this fluent
     * @since 1.0
     */
    public LMLiteralInfo(String f, ArrayList<String> ag) {
        literal = null;
        var = null;
        value = null;
        function = f;
        agent = null;
        agents = ag;
    }

    /**
     * Gets the description of this fluent.
     *
     * @return Description of this fluent
     * @since 1.0
     */
    public String getLiteral() {
        return literal;
    }

    /**
     * Gets the level of this landmark in the RPG.
     *
     * @return Level of this landmark in the RPG
     * @since 1.0
     */
    public int getLevel() {
        return level;
    }

    /**
     * Indicates if this fluent is a top-level goal.
     *
     * @return <code>true</code>, if this fluent is a top-level goal;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean isGoal() {
        return isGoal;
    }

    /**
     * Gets the variable of this fluent.
     *
     * @return Variable of this fluent
     * @since 1.0
     */
    public String getVariable() {
        return var;
    }

    /**
     * Gets the value of this fluent.
     *
     * @return value of this fluent
     * @since 1.0
     */
    public String getValue() {
        return value;
    }

    /**
     * Gets the function of this variable.
     *
     * @return Function of this variable
     * @since 1.0
     */
    public String getFunction() {
        return function;
    }

    /**
     * Gets the sender agent.
     *
     * @return Name of the sender agent
     * @since 1.0
     */
    public String getAgent() {
        return agent;
    }

    /**
     * Gets the list of agents that can share this fluent.
     *
     * @return List of agents that can share this fluent
     * @since 1.0
     */
    public ArrayList<String> getAgents() {
        return agents;
    }

    /**
     * Gets a description of this fluent.
     *
     * @return Description of this fluent
     * @since 1.0
     */
    @Override
    public String toString() {
        return literal;
    }
}
