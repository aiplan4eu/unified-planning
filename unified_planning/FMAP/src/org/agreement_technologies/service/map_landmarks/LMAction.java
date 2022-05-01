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
import java.util.Hashtable;
import org.agreement_technologies.common.map_grounding.Action;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedEff;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.GroundedVar;
import org.agreement_technologies.common.map_landmarks.LandmarkAction;
import org.agreement_technologies.common.map_landmarks.LandmarkFluent;

/**
 * LMAction class implements actions in the landmarks graph.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class LMAction implements LandmarkAction {

    private String name;                                // Name of the action
    private int level;                                  // Level of the action  in the RPG
    private final ArrayList<LandmarkFluent> preconditions;    // Action preconditions
    private final ArrayList<LandmarkFluent> effects;          // Action effects

    /**
     * Creates a new action for the LG.
     *
     * @param a Action
     * @param vars Relationship between the name of the variables and the
     * variables
     * @param lits Relationship between the name of the fluents and the fluents
     * @param rpg Relaxed Planning Graph
     * @since 1.0
     */
    public LMAction(Action a, Hashtable<String, GroundedVar> vars,
            Hashtable<String, LMLiteral> lits, RPG rpg) {
        LMLiteral l;
        String[] agents;

        name = a.getOperatorName();
        for (String s : a.getParams()) {
            name += " " + s;
        }
        level = a.getMinTime();
        preconditions = new ArrayList<>();
        effects = new ArrayList<>();

        for (GroundedCond p : a.getPrecs()) {
            if (vars.get(p.getVar().toString()) == null) {
                vars.put(p.getVar().toString(), p.getVar());
            }
            if (lits.get(p.getVar().toString() + " " + p.getValue()) == null) {
                agents = rpg.getAgents(p.getVar(), p.getValue());
                l = new LMLiteral(vars.get(p.getVar().toString()), p.getValue(), p.getVar().getMinTime(p.getValue()), agents, false);
                lits.put(l.toString(), l);
            }
            preconditions.add(lits.get(p.getVar().toString() + " " + p.getValue()));
        }
        for (GroundedEff e : a.getEffs()) {
            if (vars.get(e.getVar().toString()) == null) {
                vars.put(e.getVar().toString(), e.getVar());
            }
            if (lits.get(e.getVar().toString() + " " + e.getValue()) == null) {
                agents = rpg.getAgents(e.getVar(), e.getValue());
                l = new LMLiteral(vars.get(e.getVar().toString()), e.getValue(), e.getVar().getMinTime(e.getValue()), agents, false);
                lits.put(l.toString(), l);
            }
            effects.add(lits.get(e.getVar().toString() + " " + e.getValue()));
        }
    }

    /**
     * Returns the array of agents with whom a LMLiteral is shareable.
     *
     * @param gt Grounded task
     * @param v Variable associated to the LMLiteral
     * @param val Value associated to the LMLiteral
     * @return Array of agent names
     * @since 1.0
     */
    private String[] getAgents(GroundedTask gt, GroundedVar v, String val) {
        ArrayList<String> agents = new ArrayList<>();
        for (int i = 0; i < gt.getAgentNames().length; i++) {
            if (gt.getAgentNames()[i].equals(gt.getAgentName())) {
                agents.add(gt.getAgentNames()[i]);
            } else if (v.shareable(val, gt.getAgentNames()[i])) {
                agents.add(gt.getAgentNames()[i]);
            }
        }
        String[] agentsArray = new String[agents.size()];
        int pos = 0;
        for (String ag : agents) {
            agentsArray[pos] = ag;
            pos++;
        }

        return agentsArray;
    }

    /**
     * Gets action name.
     *
     * @return Action name
     * @since 1.0
     */
    @Override
    public String getName() {
        return name;
    }

    /**
     * Gets level of the action in the RPG used to calculate landmarks.
     *
     * @return Action level in the RPG
     * @since 1.0
     */
    @Override
    public int getLevel() {
        return level;
    }

    /**
     * Sets the level of the action in the RPG used to calculate landmarks.
     *
     * @param l Action level in the RPG
     * @since 1.0
     */
    @Override
    public void setLevel(int l) {
        level = l;
    }

    /**
     * Gets action preconditions.
     *
     * @return List of preconditions
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkFluent> getPreconditions() {
        return preconditions;
    }

    /**
     * Gets the action effects.
     *
     * @return List of effects
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkFluent> getEffects() {
        return effects;
    }

    /**
     * Gets a description of this action.
     *
     * @return Name of the action
     * @since 1.0
     */
    @Override
    public String toString() {
        return name;
    }

}
