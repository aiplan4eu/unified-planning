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

import java.util.ArrayList;
import org.agreement_technologies.common.map_grounding.GroundedVar;
import org.agreement_technologies.common.map_landmarks.LandmarkAction;
import org.agreement_technologies.common.map_landmarks.LandmarkFluent;

/**
 * LMLiteral class implements a fluent, i.e. (variable, value), in the landmarks
 * graph.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class LMLiteral implements LandmarkFluent {

    private final GroundedVar var;                      // Variable
    private final String value;                         // Value for the variable
    private int level;                                  // Level in the RPG
    private int index;                                  // Index of this fluent
    private ArrayList<LandmarkAction> producers;        // Productor actions of this fluent
    //All the producers of the fluent, even if they come after the fluent in the RPG
    private ArrayList<LandmarkAction> totalProducers;
    private final boolean isGoal;                       // Indicates if the fluent is a task goal
    private final ArrayList<String> agents;             // Agents that can share this fluent

    /**
     * Creates a new fluent for the LG.
     *
     * @param v Variable
     * @param val Value for the variable
     * @param t Level of the fluent in the RPG
     * @param ag Agents that can share this fluent
     * @param goal Indicates if the fluent is a task goal
     */
    public LMLiteral(GroundedVar v, String val, int t, String[] ag, boolean goal) {
        var = v;
        value = val;
        level = t;
        isGoal = goal;

        //agents variable stores the agents that share the LMLiteral
        agents = new ArrayList<>(ag.length);
        if (ag.length == 1) {
            agents.add(ag[0]);
        } else {
            //Add all the agents that share the literal
            for (String a : ag) {
                agents.add(a);
            }
        }
    }

    /**
     * Creates a new fluent for the LG.
     *
     * @param val Value for the variable
     * @param ag Agents that can share this fluent
     */
    public LMLiteral(String val, ArrayList<String> ag) {
        value = val;
        agents = ag;
        var = null;
        level = -1;
        index = -1;
        isGoal = false;
    }

    /**
     * Sets the producer actions that come before the fluent in the RPG.
     *
     * @param p Arraylist of producer actions
     * @since 1.0
     */
    public void setProducers(ArrayList<LandmarkAction> p) {
        this.producers = p;
    }

    /**
     * Gets producer actions that come before the fluent in the RPG.
     *
     * @return Arraylist of producer actions
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkAction> getProducers() {
        return this.producers;
    }

    /**
     * Sets the producer actions of the fluent, even if they come after the
     * fluent in the RPG.
     *
     * @param p Arraylist of producer actions
     * @since 1.0
     */
    public void setTotalProducers(ArrayList<LandmarkAction> p) {
        this.totalProducers = p;
    }

    /**
     * Gets producer actions of the fluent, even if they come after the fluent
     * in the RPG.
     *
     * @return Arraylist of producer actions
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkAction> getTotalProducers() {
        return this.totalProducers;
    }

    /**
     * Gets index of the landmark fluent.
     *
     * @return Landmark fluent index
     * @since 1.0
     */
    @Override
    public int getIndex() {
        return index;
    }

    /**
     * Sets index of the landmark fluent.
     *
     * @param index Landmark fluent index
     * @since 1.0
     */
    public void setIndex(int index) {
        this.index = index;
    }

    /**
     * Gets the variable associated to the landmark fluent.
     *
     * @return Grounded variable
     * @since 1.0
     */
    @Override
    public GroundedVar getVar() {
        return var;
    }

    /**
     * Gets value assigned to the variable of the landmark fluent.
     *
     * @return Value of the variable that defines the landmark fluent
     * @since 1.0
     */
    @Override
    public String getValue() {
        return value;
    }

    /**
     * Sets level of the landmark fluent in the RPG.
     *
     * @param l Fluent level in the RPG
     * @since 1.0
     */
    public void setLevel(int l) {
        level = l;
    }

    /**
     * Gets level of the landmark fluent in the RPG.
     *
     * @return Fluent level in the RPG
     * @since 1.0
     */
    @Override
    public int getLevel() {
        return level;
    }

    /**
     * Verifies if the landmark fluent is a task goal.
     *
     * @return <code>true</code>, if the fluent is a goal; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    @Override
    public boolean isGoal() {
        return isGoal;
    }

    /**
     * Returns a description of this fluent.
     * 
     * @return Description of this fluent
     * @since 1.0
     */
    @Override
    public String toString() {
        if (var != null) {
            return var.toString() + " " + value;
        }
        return value;
    }

    /**
     * Gets the name of the variable associated to the landmark fluent.
     *
     * @return Variable name
     * @since 1.0
     */
    @Override
    public String getVarName() {
        return var.toString();
    }

    /**
     * Gets agents that are aware of the landmark fluent.
     *
     * @return Arraylist of agent identifiers
     * @since 1.0
     */
    @Override
    public ArrayList<String> getAgents() {
        return agents;
    }
    
}
