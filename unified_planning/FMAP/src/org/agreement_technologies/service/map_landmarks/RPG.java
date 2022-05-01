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
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_grounding.Action;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.GroundedVar;
import org.agreement_technologies.common.map_landmarks.LandmarkAction;
import org.agreement_technologies.common.map_landmarks.LandmarkFluent;

/**
 * RPG class represents the disRPG (distributed relaxed planning graph) of the
 * planning agent.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class RPG {

    private GroundedTask groundedTask;                      // Grounded task
    private AgentCommunication comm;                        // Communication utility
    private ArrayList<LMLiteral> literals;                  // List of literals
    private ArrayList<ArrayList<LMLiteral>> litLevels;      // Literal levels
    private ArrayList<ArrayList<LandmarkAction>> actLevels; // Action levels
    private ArrayList<LandmarkFluent> goals;                // Task goals
    private ArrayList<LandmarkAction> actions;              // List of actions
    private Hashtable<String, GroundedVar> vars;            // Gets the variables from their names
    private Hashtable<String, LMLiteral> hashLiterals;      // Gets the literals from their names
    private Hashtable<Integer, LMLiteral> indexLiterals;    // Gets the literals from their indexes
    private Hashtable<String, Integer> hashAgents;          // Gets the agent index from its name
    private Hashtable<Integer, Integer> RPG;                // Gets the literal level from the literal index

    /**
     * Createa a new disRPG.
     *
     * @param gt Grounded task
     * @param c Communication utility
     * @since 1.0
     */
    public RPG(GroundedTask gt, AgentCommunication c) {
        groundedTask = gt;
        comm = c;
        vars = new Hashtable<>();
        hashLiterals = new Hashtable<>();
        indexLiterals = new Hashtable<>();

        //Extracting goals and calculating max. RPG level
        int maxRPGLevel = 0;
        goals = new ArrayList<>();
        for (GroundedCond gg : gt.getGlobalGoals()) {
            LMLiteral l = new LMLiteral(gg.getVar(), gg.getValue(),
                    gg.getVar().getMinTime(gg.getValue()), gt.getAgentNames(),
                    true);
            if (vars.get(l.getVar().toString()) == null) {
                vars.put(l.getVar().toString(), l.getVar());
            }
            hashLiterals.put(l.toString(), l);
            goals.add(l);
            if (gg.getVar().getMinTime(gg.getValue()) > maxRPGLevel) {
                maxRPGLevel = gg.getVar().getMinTime(gg.getValue());
            }
        }

        //Creating LandmarkActions
        actions = new ArrayList<>();
        for (Action a : gt.getActions()) {
            actions.add(new LMAction(a, vars, hashLiterals, this));
        }

        //Initialising literal levels of the RPG
        literals = new ArrayList<>();
        litLevels = new ArrayList<>(maxRPGLevel + 1);
        for (int i = 0; i < maxRPGLevel + 1; i++) {
            litLevels.add(new ArrayList<LMLiteral>());
        }
        for (GroundedVar v : gt.getVars()) {
            for (String val : v.getReachableValues()) {
                if (v.getMinTime(val) != -1) {
                    addLiteral(v, val, v.getMinTime(val));
                }
            }
        }

        //Initialising action levels of the RPG
        actLevels = new ArrayList<>(maxRPGLevel);
        for (int i = 0; i < maxRPGLevel; i++) {
            actLevels.add(new ArrayList<LandmarkAction>());
        }
        for (LandmarkAction a : actions) {
            if (a.getLevel() != -1 && a.getLevel() < maxRPGLevel) {
                addAction(a, a.getLevel());
            }
        }

        //Setting literals indexes and index hashtable
        for (int i = 0; i < literals.size(); i++) {
            literals.get(i).setIndex(i);
            indexLiterals.put(i, literals.get(i));
        }

        //Calculating actions that produce each literal
        ArrayList<LandmarkAction> producers;
        ArrayList<LandmarkAction> totalProducers;
        for (LMLiteral prl : literals) {
            producers = new ArrayList<>();
            totalProducers = new ArrayList<>();
            for (LandmarkAction pra : actions) {
                for (LandmarkFluent eff : pra.getEffects()) {
                    if (prl.getVar() == eff.getVar() && prl.getValue().equals(eff.getValue())) {
                        if (pra.getLevel() < prl.getLevel()) {
                            producers.add(pra);
                        }
                        totalProducers.add(pra);
                        break;
                    }
                }
            }
            prl.setProducers(producers);
            prl.setTotalProducers(totalProducers);
        }
        //Multi-agent RPG - iteratively arrange the graph until the shareable
        //fluents are in the same level for all the agents
        if (groundedTask.getAgentNames().length > 1) {
            this.arrangeRPG();
        }
    }

    /**
     * Multi-agent procedure: rearranges the dis-RPG until the shareable
     * literals are placed in the same level for all the agents involved.
     * 
     * @since 1.0
     */
    private void arrangeRPG() {
        RPG = new Hashtable<>();
        int level = 0, maxLevel;
        ArrayList<String> fluentAgents;
        //Data received from othe agents
        ArrayList<MessageContentRPG> receivedData = new ArrayList<>();
        ArrayList<MessageContentRPG> totalReceivedData = new ArrayList<>();
        //Hashtable that maps received fluents to their position in the totalReceivedData list
        Hashtable<String, Integer> hashReceivedData = new Hashtable<>();
        //Maps each of the rest of agents to an integer (its index on the dataToSend list)
        hashAgents = new Hashtable<>();
        MessageContentRPG oldData;
        //Fluents that do not have any producers
        ArrayList<LMLiteral> fluentsNoProducers = new ArrayList<>();
        for (LMLiteral l : this.literals) {
            if (l.getProducers().isEmpty()) {
                fluentsNoProducers.add(l);
            }
        }
        //act and auxAct - Actions of the domain
        ArrayList<LandmarkAction> act = new ArrayList<>();
        ArrayList<LandmarkAction> auxAct = new ArrayList<>();
        boolean reached, stop = false;
        //Number of agents that have not changed the level of any shareable fluents
        int unchangedAgents = 0;
        boolean changed;
        Integer effLevel;
        //Fill hashAgents structure
        int i = 0;
        for (String ag : comm.getOtherAgents()) {
            hashAgents.put(ag, i);
            i++;
        }
        //dataToSend includes an ArrayList of data to be sent to each of the rest of agents in the task
        ArrayList<ArrayList<MessageContentRPG>> dataToSend = new ArrayList<>();
        for (i = 0; i < groundedTask.getAgentNames().length - 1; i++) {
            dataToSend.add(new ArrayList<MessageContentRPG>());
        }

        //Main loop 
        while (!stop) {
            //Baton agent - update RPG / send shareable fluents
            if (comm.batonAgent()) {
                changed = false;
                //Add initial state to the RPG
                for (LMLiteral il : this.litLevels.get(0)) {
                    RPG.put(il.getIndex(), level);
                }
                //Add fluents without producers to the RPG (if they are not already in a lower level of the RPG)
                for (LMLiteral l : fluentsNoProducers) {
                    if (RPG.get(l.getIndex()) == null || RPG.get(l.getIndex()) > l.getLevel()) {
                        RPG.put(l.getIndex(), l.getLevel());
                    }
                }

                for (LandmarkAction a : actions) {
                    auxAct.add(a);
                }

                boolean moreLiterals = false;
                level = 0;
                while (act.size() != auxAct.size() || moreLiterals) {
                    level++;
                    act = auxAct;
                    auxAct = new ArrayList<>();

                    moreLiterals = false;
                    //Analyze all the actions in act
                    for (LandmarkAction a : act) {
                        maxLevel = 0;
                        //Check if the preconditions of action a are already in the RPG
                        reached = true;
                        for (LandmarkFluent pre : a.getPreconditions()) {
                            if (RPG.get(pre.getIndex()) != null && RPG.get(pre.getIndex()) >= level) {
                                moreLiterals = true;
                            }
                            if (RPG.get(pre.getIndex()) == null || RPG.get(pre.getIndex()) >= level) {
                                reached = false;
                                break;
                            } else {
                                if (RPG.get(pre.getIndex()) > maxLevel) {
                                    maxLevel = RPG.get(pre.getIndex());
                                }
                            }
                        }
                        //If all the preconditions of the action a are already in the RPG put its effects
                        //in the following level (unless they have already been added in lower levels)
                        if (reached) {
                            //Overwrite action level according to the maximum level of its preconditions
                            a.setLevel(maxLevel);
                            for (LandmarkFluent eff : a.getEffects()) {
                                effLevel = RPG.get(eff.getIndex());
                                if (effLevel == null || effLevel > maxLevel + 1) {
                                    RPG.put(eff.getIndex(), maxLevel + 1);
                                    //Process shareable effects
                                    fluentAgents = eff.getAgents();
                                    if (fluentAgents.size() > 1) {
                                        if (changed == false) {
                                            changed = true;
                                        }
                                        //Send the level of the fluent to the rest of agents that share it
                                        for (String ag : fluentAgents) {
                                            if (!ag.equals(groundedTask.getAgentName())) {
                                                dataToSend.get(hashAgents.get(ag)).add(new MessageContentRPG(eff.getVar().toString(), eff.getValue(), maxLevel + 1));
                                            }
                                        }
                                    }
                                }
                            }
                        } else {
                            auxAct.add(a);
                        }
                    }
                }
                if (changed) {
                    unchangedAgents = 0;
                } else {
                    unchangedAgents++;
                }
                if (unchangedAgents == groundedTask.getAgentNames().length) {
                    stop = true;
                }

                //Send shareable data - without ack
                for (String ag : comm.getOtherAgents()) {
                    comm.sendMessage(ag, new RPGMessageContent(dataToSend.get(hashAgents.get(ag)), changed), false);
                }
            } //Non-baton agent - receive data on the shareable fluents / check stop condition / store new fluents
            else {
                //Receive information from baton agent
                RPGMessageContent content = (RPGMessageContent) comm.receiveMessage(comm.getBatonAgent(), false);
                //If the sender agent has updated the level of any of its shareable fluents
                //set the unchanged agents count to 0
                if (content.isRPGChanged()) {
                    unchangedAgents = 0;
                } else {
                    unchangedAgents++;
                }
                //Stop condition: if any agent in the last round has modified its RPG, terminate the procedure
                if (unchangedAgents == groundedTask.getAgentNames().length) {
                    stop = true;
                }
                receivedData = content.getData();
                //Update totalReceivedData with the new data received from other agent
                if (receivedData.size() > 0) {
                    for (MessageContentRPG newData : receivedData) {
                        if (hashReceivedData.get(newData.getFluent()) == null) {
                            totalReceivedData.add(newData);
                            hashReceivedData.put(newData.getFluent(), totalReceivedData.size() - 1);
                        } else {
                            oldData = totalReceivedData.get(hashReceivedData.get(newData.getFluent()));
                            if (newData.getLevel() < oldData.getLevel()) {
                                oldData.setLevel(newData.getLevel());
                            }
                        }
                    }
                }
                //Add the external data to the RPG before start rearranging it
                for (MessageContentRPG d : receivedData) {
                    //Update data only if the level of the fluent is lower than the level registered by the agent
                    if (RPG.get(hashLiterals.get(d.getFluent()).getIndex()) == null
                            || RPG.get(hashLiterals.get(d.getFluent()).getIndex()) > d.getLevel()) {
                        RPG.put(hashLiterals.get(d.getFluent()).getIndex(), d.getLevel());
                    }
                }
            }
            //Iteration completed, the baton is passed among agents
            comm.passBaton();
        }

        //Rebuild RPG lists
        for (ArrayList<LMLiteral> l : litLevels) {
            l.clear();
        }
        for (ArrayList<LandmarkAction> a : actLevels) {
            a.clear();
        }
        ArrayList<LandmarkAction> producers;
        for (LMLiteral l : literals) {
            if (RPG.get(l.getIndex()) == null) {
                System.out.println("Agent " + comm.getThisAgentName() + " does not have an assigned RPG level for literal " + l.toString());
            }
            if (RPG.get(l.getIndex()) < litLevels.size()) {
                litLevels.get(RPG.get(l.getIndex())).add(l);
            }
            //Update RPG level of the literal
            l.setLevel(RPG.get(l.getIndex()));
            //Update producers of the literal
            producers = l.getProducers();
            producers.clear();
            for (LandmarkAction prod : l.getTotalProducers()) {
                if (prod.getLevel() < l.getLevel()) {
                    producers.add(prod);
                }
            }
        }
        for (LandmarkAction a : actions) {
            if (a.getLevel() < actLevels.size()) {
                actLevels.get(a.getLevel()).add(a);
            }
        }
    }

    /**
     * Gets the map to obtain the literals from their names.
     *
     * @return Hashtable to obtain the literals from their names
     * @since 1.0
     */
    public Hashtable<String, LMLiteral> getHashLiterals() {
        return hashLiterals;
    }

    /**
     * Adds a new literal to the disRPG.
     *
     * @param v Variable
     * @param val Value
     * @param t disRPG level
     * @since 1.0
     */
    private void addLiteral(GroundedVar v, String val, int t) {
        LMLiteral l;

        String[] agents = this.getAgents(v, val);

        if (hashLiterals.get(v.toString() + " " + val) == null) {
            l = new LMLiteral(v, val, t, agents, false);
            hashLiterals.put(l.toString(), l);
        } else {
            l = hashLiterals.get(v.toString() + " " + val);
        }

        literals.add(l);
        if (t < litLevels.size()) {
            if (litLevels.get(t) == null) {
                litLevels.add(t, new ArrayList<LMLiteral>());
            }
            litLevels.get(t).add(l);
        }
    }

    /**
     * Returns the array of agents with whom a LMLiteral is shareable.
     *
     * @param v Variable associated to the LMLiteral
     * @param val Value associated to the LMLiteral
     * @return Array of agent names
     * @since 1.0
     */
    public String[] getAgents(GroundedVar v, String val) {
        ArrayList<String> agents = new ArrayList<>();
        for (int i = 0; i < groundedTask.getAgentNames().length; i++) {
            if (groundedTask.getAgentNames()[i].equals(groundedTask.getAgentName())) {
                agents.add(groundedTask.getAgentNames()[i]);
            } else if (v.shareable(val, groundedTask.getAgentNames()[i])) {
                agents.add(groundedTask.getAgentNames()[i]);
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
     * Adds a new action to the disRPG.
     *
     * @param a Action to add
     * @param t disRPG level
     * @since 1.0
     */
    private void addAction(LandmarkAction a, int t) {
        if (actLevels.get(t) == null) {
            actLevels.add(t, new ArrayList<LandmarkAction>());
        }
        actLevels.get(t).add(a);
    }

    /**
     * Uses the disRPG to verify that a given fluent is a landmark.
     *
     * @param p Fluent to check
     * @return <code>true</code>, if the fluent is a landamrk;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean verify(LandmarkFluent p) {
        //If a landmark candidate belongs to the initial state, it is a landmark
        if (p.getLevel() == 0) {
            return true;
        }

        Hashtable<Integer, Boolean> RPGp = new Hashtable<>();
        Hashtable<Integer, Boolean> hashGoals = new Hashtable<>();
        int pendingGoals = this.goals.size();
        for (LandmarkFluent g : this.goals) {
            hashGoals.put(g.getIndex(), Boolean.TRUE);
        }
        for (LMLiteral il : this.litLevels.get(0)) {
            RPGp.put(il.getIndex(), Boolean.TRUE);
        }
        //Actions that do not contain p as an effect
        ArrayList<LandmarkAction> Ap = new ArrayList<>();
        ArrayList<LandmarkAction> auxAp = new ArrayList<>();
        boolean found;
        for (LandmarkAction a : actions) {
            found = false;
            for (LandmarkFluent eff : a.getEffects()) {
                if (eff == p) {
                    found = true;
                }
            }
            if (!found) {
                auxAp.add(a);
            }
        }

        while (pendingGoals > 0 && Ap.size() != auxAp.size()) {
            Ap = auxAp;
            auxAp = new ArrayList<>();
            for (LandmarkAction a : Ap) {
                found = true;
                for (LandmarkFluent pre : a.getPreconditions()) {
                    if (RPGp.get(pre.getIndex()) == null) {
                        found = false;
                        break;
                    }
                }
                if (found) {
                    for (LandmarkFluent eff : a.getEffects()) {
                        if (hashGoals.get(eff.getIndex()) != null) {
                            if (hashGoals.get(eff.getIndex()) == Boolean.TRUE) {
                                hashGoals.put(eff.getIndex(), Boolean.FALSE);
                                pendingGoals--;
                            }
                        }
                        RPGp.put(eff.getIndex(), Boolean.TRUE);
                    }
                } else {
                    auxAp.add(a);
                }
            }
        }
        return pendingGoals != 0;
    }

    /**
     * Verifies if a set of actions ac are necessary to complete the task.
     *
     * @param ac List of actions to check
     * @return <code>true</code>, if the given actions are necessary to reach
     * the goals; <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean verify(ArrayList<LandmarkAction> ac) {
        Hashtable<Integer, Boolean> RPGp = new Hashtable<>();
        Hashtable<Integer, Boolean> hashGoals = new Hashtable<>();
        int pendingGoals = this.goals.size();
        for (LandmarkFluent g : this.goals) {
            hashGoals.put(g.getIndex(), Boolean.TRUE);
        }
        for (LMLiteral il : this.litLevels.get(0)) {
            RPGp.put(il.getIndex(), Boolean.TRUE);
        }
        //Calculate Aa = {actions / ac}
        ArrayList<LandmarkAction> Aac = new ArrayList<>();
        ArrayList<LandmarkAction> auxAac = new ArrayList<>();
        boolean found;
        for (LandmarkAction a : actions) {
            if (!ac.contains(a)) {
                auxAac.add(a);
            }
        }

        while (pendingGoals > 0 && Aac.size() != auxAac.size()) {
            Aac = auxAac;
            auxAac = new ArrayList<>();
            for (LandmarkAction a : Aac) {
                found = true;
                for (LandmarkFluent pre : a.getPreconditions()) {
                    if (RPGp.get(pre.getIndex()) == null) {
                        found = false;
                        break;
                    }
                }
                if (found) {
                    for (LandmarkFluent eff : a.getEffects()) {
                        if (hashGoals.get(eff.getIndex()) != null) {
                            if (hashGoals.get(eff.getIndex()) == Boolean.TRUE) {
                                hashGoals.put(eff.getIndex(), Boolean.FALSE);
                                pendingGoals--;
                            }
                        }
                        RPGp.put(eff.getIndex(), Boolean.TRUE);
                    }
                } else {
                    auxAac.add(a);
                }
            }
        }
        return pendingGoals != 0;
    }

    /**
     * Verifies if a single landmark candidate is actually a landmark.
     *
     * @param p Single landmark candidate
     * @return <code>true</code>, if the literal is a confirmed landmark;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean verifySingleLandmark(LMLiteral p) {
        ArrayList<LandmarkAction> ap = new ArrayList<>();
        //If a landmark candidate belongs to the initial state
        //or if the candidate is a goal, it is a landmark
        if (p != null) {
            //If p does not have producers, consider all the actions in the domain
            if (p.getTotalProducers().isEmpty()) {
                ap.addAll(actions);
            } else {
                for (LandmarkAction a : actions) {
                    if (!p.getTotalProducers().contains(a)) {
                        ap.add(a);
                    }
                }
            }
        } else {
            ap.addAll(actions);
        }
        //Call verifyMA to check whether the reduced set of actions leads to all the goals
        return verifyMA(ap);
    }

    /**
     * Verifies if a disjunctive landmark candidate is actually a landmark.
     *
     * @param disj Literals in the disjunctive landmark candidate
     * @return <code>true</code>, if the disjunction of literals is a confirmed
     * landmark; <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean verifyDisjunctiveLandmark(ArrayList<LMLiteral> disj) {
        ArrayList<LandmarkAction> ap = new ArrayList<>();
        ArrayList<LandmarkAction> producers = new ArrayList<>();
        //If a landmark candidate belongs to the initial state, it is a landmark
        for (LMLiteral p : disj) {
            for (LandmarkAction prod : p.getTotalProducers()) {
                if (!producers.contains(prod)) {
                    producers.add(prod);
                }
            }
        }
        if (producers.size() == 0) {
            ap.addAll(actions);
        } else {
            for (LandmarkAction a : actions) {
                if (!producers.contains(a)) {
                    ap.add(a);
                }
            }
        }

        //Call verifyMA to check whether the reduced set of actions leads to all the goals
        return verifyMA(ap);
    }

    /**
     * Verifies an edge of the landmark graph.
     *
     * @param A Actions that cause the transition in the edge of the landmark
     * graph
     * @return <code>true</code>, if the edge is correct; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    public boolean verifyEdge(ArrayList<LandmarkAction> A) {
        ArrayList<LandmarkAction> ap = new ArrayList<>();
        boolean found;
        //Exclude the actions in the A set
        for (LandmarkAction act : actions) {
            found = false;
            for (LandmarkAction a : A) {
                if (a.getName().equals(act.getName())) {
                    found = true;
                    break;
                }
            }
            if (!found) {
                ap.add(act);
            }
        }
        //Call verifyMA to check whether the reduced set of actions leads to all the goals
        return verifyMA(ap);
    }

    /**
     * Multi-agent verification procedure. Agents jointly verify if a candidate
     * literal is actually a landmark.
     *
     * @param act Actions of the domain, excluding the producers of the
     * candidate literal
     * @return <code>true</code>, if the literal is a confirmed landmark;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean verifyMA(ArrayList<LandmarkAction> act) {
        int i;
        ArrayList<ArrayList<String>> litsToSend = new ArrayList<>();
        for (i = 0; i < comm.getOtherAgents().size(); i++) {
            litsToSend.add(new ArrayList<String>());
        }
        Hashtable<Integer, Boolean> RPGp = new Hashtable<>();
        Hashtable<Integer, Boolean> hashGoals = new Hashtable<>();
        Hashtable<Integer, Boolean> hashMAGoals;
        int pendingMAGoals;
        for (LandmarkFluent g : this.goals) {
            hashGoals.put(g.getIndex(), Boolean.FALSE);
        }
        for (LMLiteral il : this.litLevels.get(0)) {
            RPGp.put(il.getIndex(), Boolean.TRUE);
        }
        //Actions that do not contain p as an effect
        ArrayList<LandmarkAction> ap = new ArrayList<>();
        ArrayList<LandmarkAction> auxAp = act;
        ArrayList<String> reachedGoals = new ArrayList<>();
        MessageContentLandmarkGraph received;
        boolean found, RPGChanged;

        //Iterate - repeat the RPG building procedure until all the agents remain unchanged
        while (true) {
            RPGChanged = false;
            //Clear list of literals to send
            for (i = 0; i < comm.getOtherAgents().size(); i++) {
                litsToSend.get(i).clear();
            }
            //Build a complete RPG from the initial state
            while (ap.size() != auxAp.size()) {
                ap = auxAp;
                auxAp = new ArrayList<>();
                //Analyze all the actions in the RPG
                for (LandmarkAction a : ap) {
                    found = true;
                    for (LandmarkFluent pre : a.getPreconditions()) {
                        if (RPGp.get(pre.getIndex()) == null) {
                            found = false;
                            break;
                        }
                    }
                    if (found) {
                        RPGChanged = true;
                        for (LandmarkFluent eff : a.getEffects()) {
                            if (hashGoals.get(eff.getIndex()) != null) {
                                if (hashGoals.get(eff.getIndex()) == Boolean.FALSE) {
                                    hashGoals.put(eff.getIndex(), Boolean.TRUE);
                                }
                            }
                            //Mark the effect as found and prepare it to be sent to involved agents
                            RPGp.put(eff.getIndex(), Boolean.TRUE);
                            for (String ag : eff.getAgents()) {
                                if (!ag.equals(groundedTask.getAgentName())) {
                                    litsToSend.get(hashAgents.get(ag)).add(eff.toString());
                                }
                            }
                        }
                    } else {
                        auxAp.add(a);
                    }
                }
            }
            ap.clear();
            //Prepare shareable information
            reachedGoals.clear();
            for (Integer k : hashGoals.keySet()) {
                if (hashGoals.get(k) == Boolean.TRUE) {
                    reachedGoals.add(literals.get(k).toString());
                }
            }
            //Send shareable information
            if (comm.batonAgent()) {
                //Take account of the pending goals
                hashMAGoals = new Hashtable<Integer, Boolean>();
                for (int k : hashGoals.keySet()) {
                    if (hashGoals.get(k) == Boolean.TRUE) {
                        hashMAGoals.put(k, Boolean.TRUE);
                    }
                }
                //Receive literals and goals from the rest of agents
                for (i = 0; i < comm.getOtherAgents().size(); i++) {
                    received = (MessageContentLandmarkGraph) comm.receiveMessage(false);
                    for (String l : received.getRPGLiterals()) {
                        RPGp.put(hashLiterals.get(l).getIndex(), Boolean.TRUE);
                    }
                    for (String g : received.getReachedGoals()) {
                        if (hashGoals.get(hashLiterals.get(g).getIndex()) != Boolean.TRUE) {
                            hashMAGoals.put(hashLiterals.get(g).getIndex(), Boolean.TRUE);
                        }
                    }
                    //If someone changed its RPG, agents should proceed with another iteration
                    if (received.getMessageType() != MessageContentLandmarkGraph.RPG_UNCHANGED) {
                        RPGChanged = true;
                    }
                }
                //Calculate the number of pending goals
                pendingMAGoals = groundedTask.getGlobalGoals().size() - hashMAGoals.keySet().size();
                //If all the goals are reached, or if none of the agents have modified their RPGs, send a stop message
                //In other case, send agents the shareable information and inform them to proceed
                if (pendingMAGoals == 0) {
                    for (String ag : comm.getOtherAgents()) {
                        comm.sendMessage(ag, new MessageContentLandmarkGraph(null, 
                                null, null, null, null, null, null, null, 
                                MessageContentLandmarkGraph.IS_NOT_LANDMARK), false);
                    }
                    return false;
                } else if (!RPGChanged) {
                    for (String ag : comm.getOtherAgents()) {
                        comm.sendMessage(ag, new MessageContentLandmarkGraph(null, 
                                null, null, null, null, null, null, null, 
                                MessageContentLandmarkGraph.IS_LANDMARK), false);
                    }
                    return true;
                } else {
                    for (String ag : comm.getOtherAgents()) {
                        comm.sendMessage(ag, new MessageContentLandmarkGraph(null, 
                                null, null, null, litsToSend.get(hashAgents.get(ag)), 
                                null, comm.getThisAgentName(), null, 
                                MessageContentLandmarkGraph.VERIFICATION_STAGE), false);
                    }
                }

            } //Participant agent
            else {
                //Send shareable literals found and goals reached to the baton agent
                //If the RPG has not changed since the previous iteration, warn the baton agent
                if (RPGChanged) {
                    comm.sendMessage(comm.getBatonAgent(), new MessageContentLandmarkGraph(null, 
                            null, null, null, litsToSend.get(hashAgents.get(comm.getBatonAgent())),
                            reachedGoals, comm.getThisAgentName(), null, MessageContentLandmarkGraph.VERIFICATION_STAGE), false);
                } else {
                    comm.sendMessage(comm.getBatonAgent(), new MessageContentLandmarkGraph(null, 
                            null, null, null, litsToSend.get(hashAgents.get(comm.getBatonAgent())),
                            reachedGoals, comm.getThisAgentName(), null, MessageContentLandmarkGraph.RPG_UNCHANGED), false);
                }
                //Receive answer from baton agent
                received = (MessageContentLandmarkGraph) comm.receiveMessage(comm.getBatonAgent(), false);
                switch (received.getMessageType()) {
                    case MessageContentLandmarkGraph.IS_LANDMARK:
                        return true;
                    case MessageContentLandmarkGraph.IS_NOT_LANDMARK:
                        return false;                 
                }
                //Send and receive shareable data from/to the rest of agents
                for (String ag : comm.getOtherAgents()) {
                    if (!ag.equals(comm.getBatonAgent())) {
                        comm.sendMessage(ag, new MessageContentLandmarkGraph(null, null, null, null, litsToSend.get(hashAgents.get(ag)),
                                null, comm.getThisAgentName(), null, MessageContentLandmarkGraph.VERIFICATION_STAGE), false);
                    }
                }
                for (String ag : comm.getOtherAgents()) {
                    if (!ag.equals(comm.getBatonAgent())) {
                        received = (MessageContentLandmarkGraph) comm.receiveMessage(false);
                        for (String l : received.getRPGLiterals()) {
                            RPGp.put(hashLiterals.get(l).getIndex(), Boolean.TRUE);
                        }
                    }
                }
            }
        }
    }

    /**
     * Gets the lteral levels.
     * 
     * @return Literal levels
     * @since 1.0
     */
    public ArrayList<ArrayList<LMLiteral>> getLitLevels() {
        return litLevels;
    }

    /**
     * Gets the action levels.
     * 
     * @return Action levels
     * @since 1.0
     */
    public ArrayList<ArrayList<LandmarkAction>> getActLevels() {
        return actLevels;
    }

    /**
     * Gets the list of actions.
     * 
     * @return Action list
     * @since 1.0
     */
    public ArrayList<LandmarkAction> getActions() {
        return actions;
    }

    /**
     * Gets the list of goals.
     * 
     * @return Goal list
     * @since 1.0
     */
    public ArrayList<LandmarkFluent> getGoals() {
        return goals;
    }

    /**
     * Gets the list of literals.
     * 
     * @return List of literals
     * @since 1.0
     */
    public ArrayList<LMLiteral> getLiterals() {
        return literals;
    }

    /**
     * Gets a literal through its name.
     * 
     * @param id Literal name
     * @return Literal with the given name
     * @since 1.0
     */
    public LMLiteral getLiteral(String id) {
        return hashLiterals.get(id);
    }

    /**
     * Gets the map that obtains the literals from their indexes.
     * 
     * @return Hashtable to get the literals from their indexes
     * @since 1.0
     */
    public Hashtable<Integer, LMLiteral> getIndexLiterals() {
        return indexLiterals;
    }

    /**
     * Gets the literals in the initial state.
     * 
     * @return Initial-state literals
     * @since 1.0
     */
    public ArrayList<LMLiteral> getInitialState() {
        return litLevels.get(0);
    }

    /**
     * Gets a description of this disRPG.
     * 
     * @return Description of this disRPG
     * @since 1.0
     */
    @Override
    public String toString() {
        String res = new String();
        int c;

        for (int i = 0; i < litLevels.size(); i++) {
            c = 0;
            for (int key : RPG.keySet()) {
                if (RPG.get(key) == i) {
                    c++;
                }
            }
            res += c + " ";
        }

        res += "\nLiteral list:";
        res += "\n-------------\n";
        for (int i = 0; i < litLevels.size(); i++) {
            for (int key : RPG.keySet()) {
                if (RPG.get(key) == i) {
                    res += "[" + i + "] " + literals.get(key).toString() + "\n";
                }
            }
        }

        return res;
    }
}
