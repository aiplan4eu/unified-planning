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
package org.agreement_technologies.service.map_planner;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;

/**
 * HeuristicAdjustment class implements a message with heuristic information
 * about landmarks to properly adjust the landmarks heuristic in multi-agent
 * planning.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class HeuristicAdjustment implements Serializable {

    // Serial number for serialization
    private static final long serialVersionUID = 8516447848966468906L;
    // New landmarks achieved: plan name -> List of achieved landmark indexes
    private final HashMap<String, ArrayList<Integer>> newLandmarks;
    // Own plan proposals to the other agents
    private ArrayList<ProposalToSend> proposals;

    /**
     * Creates a new empty message.
     * 
     * @param size Initial hash table size
     * @since 1.0
     */
    public HeuristicAdjustment(int size) {
        newLandmarks = new HashMap<>(size);
        proposals = null;
    }

    /**
     * Sets the list of new achieved landmarks for a given plan proposal.
     * 
     * @param name Plan name
     * @param newLandmarks New achieved landmarks
     * @since 1.0
     */
    public void add(String name, ArrayList<Integer> newLandmarks) {
        this.newLandmarks.put(name, newLandmarks);
    }

    /**
     * Add the agent's plan proposals to the message.
     * 
     * @param proposals Own plan proposals
     * @since 1.0
     */
    public void addOwnProposals(ArrayList<ProposalToSend> proposals) {
        this.proposals = proposals;
    }

    /**
     * Gets the list of plan proposals.
     * 
     * @return List of plan proposals
     * @since 1.0
     */
    public ArrayList<ProposalToSend> getProposals() {
        return proposals;
    }

    /**
     * Merges the new achieved landmarks for a given plan with the ones which
     * already exists in the message.
     * 
     * @param name Plan name
     * @param newLand New achieved landmarks 
     * @since 1.0
     */
    public void merge(String name, ArrayList<Integer> newLand) {
        if (newLand == null || newLand.isEmpty()) {
            return;
        }
        ArrayList<Integer> storedLand = newLandmarks.get(name);
        if (storedLand == null) {
            add(name, newLand);
        } else {
            for (Integer l : newLand) {
                if (!storedLand.contains(l)) {
                    storedLand.add(l);
                }
            }
        }
    }

    /**
     * Gets the number of new achieved landmarks for a given plan.
     * 
     * @param name Plan name
     * @return Number of new achieved landmarks for the plan
     * @since 1.0
     */
    public int getNumNewLandmarks(String name) {
        ArrayList<Integer> storedLand = newLandmarks.get(name);
        if (storedLand == null) {
            return 0;
        } else {
            return storedLand.size();
        }
    }

    /**
     * Gets a description of the new achieved landmarks for a given plan.
     * 
     * @param name Plan name
     * @return Description of the new achieved landmarks for the plan
     * @since 1.0
     */
    public String newLandmarksList(String name) {
        ArrayList<Integer> storedLand = newLandmarks.get(name);
        return storedLand == null ? "[]" : storedLand.toString();
    }

    /**
     * Gets the list of new achieved landmarks for a given plan.
     * 
     * @param name Plan name
     * @return List of new achieved landmarks for the plan
     * @since 1.0
     */
    public ArrayList<Integer> getNewLandmarks(String name) {
        return newLandmarks.get(name);
    }

    /**
     * Gets the list of proposals with needed adjustments in their landmarks
     * heuristic value.
     * 
     * @return List of proposals with needed adjustments in their hLand value
     * @since 1.0
     */
    public ArrayList<String> proposalsWithAdjustments() {
        ArrayList<String> plans = new ArrayList<>();
        for (String name : newLandmarks.keySet()) {
            if (!newLandmarks.get(name).isEmpty()) {
                plans.add(name);
            }
        }
        return plans;
    }
    
}
