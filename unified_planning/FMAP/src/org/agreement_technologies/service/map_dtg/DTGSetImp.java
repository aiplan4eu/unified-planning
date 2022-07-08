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
package org.agreement_technologies.service.map_dtg;

import java.util.ArrayList;
import java.util.Enumeration;
import java.util.Hashtable;
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_dtg.DTG;
import org.agreement_technologies.common.map_dtg.DTGSet;
import org.agreement_technologies.common.map_dtg.DTGTransition;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedEff;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.GroundedVar;

/**
 * DTGSetImp class represents a set of Domain Transition Graphs (one DTG per
 * variable).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class DTGSetImp implements DTGSet {

    // Links each variable with its DTG
    private final Hashtable<String, DTG> dtgs;

    /**
     * Constructor of the set of DTGs
     *
     * @param task Grounded task
     * @since 1.0
     */
    public DTGSetImp(GroundedTask task) {
        GroundedVar[] vars = task.getVars();
        dtgs = new Hashtable<>(vars.length);
        for (GroundedVar v : vars) {
            DTG dtg = new DTGImp(this, v, task);
            dtgs.put(v.toString(), dtg);
        }
    }

    /**
     * Distributes the public DTGs information among the other agents.
     *
     * @param comm Agent communication
     * @param gTask Grounded task
     * @since 1.0
     */
    @Override
    public void distributeDTGs(AgentCommunication comm, GroundedTask gTask) {
        if (comm.numAgents() > 1) {
            boolean endDTG[] = new boolean[comm.numAgents()];	// Initialized to false
            do {
                sendDTGTransitions(comm, endDTG);
                receiveDTGTransitions(comm, gTask, endDTG);
            } while (!checkEndDTG(comm, endDTG));
        }
    }

    /**
     * Returns the Domain Transition Graph for the given variable
     *
     * @param v Variable
     * @return DTG of the variable
     * @since 1.0
     */
    @Override
    public DTG getDTG(GroundedVar v) {
        return dtgs.get(v.toString());
    }

    /**
     * Returns the Domain Transition Graph for the given variable
     *
     * @param varName Name of the variable
     * @return DTG of the variable
     * @since 1.0
     */
    @Override
    public DTG getDTG(String varName) {
        return dtgs.get(varName);
    }

    /**
     * Returns a description of this set of DTGs.
     *
     * @return Description of this set of DTGs
     * @since 1.0
     */
    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        Enumeration<String> e = dtgs.keys();
        while (e.hasMoreElements()) {
            DTG dtg = dtgs.get(e.nextElement());
            sb.append(dtg.toString()).append("\n");
        }
        return sb.toString();
    }

    /**
     * Adds a new transition to the DTG of the corresponding variable.
     *
     * @param varName Name of the variable
     * @param startValue Initial value
     * @param finalValue End value
     * @param commonPrecs Common preconditions to all the actions that produce
     * this transition
     * @param commonEffs Common effects to all the actions that produce this
     * transition
     * @param fromAgent Agent that produces this transition
     * @since 1.0
     */
    private void addTransition(String varName, String startValue,
            String finalValue, GroundedCond[] commonPrecs,
            GroundedEff[] commonEffs, String fromAgent) {
        DTG dtg = dtgs.get(varName);
        if (dtg == null) {
            return;
        }
        ((DTGImp) dtg).addTransition(startValue, finalValue, commonPrecs, commonEffs, fromAgent);
    }

    /**
     * Returns an array with the last transitions computed.
     *
     * @return Array with the last transitions computed
     * @since 1.0
     */
    private DTGTransition[] getNewTransitions() {
        ArrayList<DTGTransition> newTransitions = new ArrayList<>();
        Enumeration<String> e = dtgs.keys();
        while (e.hasMoreElements()) {
            DTG dtg = dtgs.get(e.nextElement());
            DTGTransition[] tList = ((DTGImp) dtg).getNewTransitions();
            for (DTGTransition t : tList) {
                newTransitions.add(t);
            }
        }
        return newTransitions.toArray(new DTGTransition[newTransitions.size()]);
    }

    /**
     * Receives new transitions from the other agents.
     *
     * @param comm Communication utility
     * @param gTask Grounded task
     * @param endDTG Array with flags that indicates which agents finished to
     * build ther DTGs
     * @since 1.0
     */
    private void receiveDTGTransitions(AgentCommunication comm, GroundedTask gTask, boolean[] endDTG) {
        for (String ag : comm.getOtherAgents()) {
            java.io.Serializable data = comm.receiveMessage(ag, false);
            if (data instanceof String) {
                if (((String) data).equals(AgentCommunication.END_STAGE_MESSAGE)) {
                    endDTG[comm.getAgentIndex(ag)] = true;
                } else {
                    throw new RuntimeException("Agent " + ag + " is not following the DTG protocol");
                }
            } else {
                @SuppressWarnings("unchecked")
                ArrayList<DTGData> dataReceived = (ArrayList<DTGData>) data;
                endDTG[comm.getAgentIndex(ag)] = false;
                for (DTGData d : dataReceived) {
                    addTransition(d.getVarName(), d.getStartValue(),
                            d.getFinalValue(), d.getCommonPrecs(gTask),
                            d.getCommonEffs(gTask), ag);
                }
            }
        }
    }

    /**
     * Sends new transitions to the other agents.
     *
     * @param comm Communication utility
     * @param endDTG Array with flags that indicates which agents finished to
     * build ther DTGs
     * @since 1.0
     */
    private void sendDTGTransitions(AgentCommunication comm, boolean[] endDTG) {
        String myAgent = comm.getThisAgentName();
        DTGTransition[] newTransitions = getNewTransitions();
        boolean somethingToSend = newTransitions.length > 0;
        endDTG[comm.getThisAgentIndex()] = !somethingToSend;
        if (somethingToSend) {
            for (String ag : comm.getOtherAgents()) {
                ArrayList<DTGData> data = new ArrayList<>(newTransitions.length);
                for (DTGTransition t : newTransitions) {
                    if (DTGData.shareable(t, ag) && t.getAgents().contains(myAgent)) {
                        data.add(new DTGData(t, ag));
                    }
                }
                comm.sendMessage(ag, data, false);
            }
        } else {
            comm.sendMessage(AgentCommunication.END_STAGE_MESSAGE, false);
        }
    }

    /**
     * Checks if all the agents have finished to build their DTGs.
     *
     * @param comm Communication utility
     * @param endDTG Array with flags that indicates which agents finished to
     * build ther DTGs
     * @return <code>true</code> if all agents have finished;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    private boolean checkEndDTG(AgentCommunication comm, boolean[] endDTG) {
        boolean finished = true;
        for (boolean end : endDTG) {
            if (!end) {
                finished = false;
                break;
            }
        }
        if (!finished) {	// Synchronization message
            if (comm.batonAgent()) {
                comm.sendMessage(AgentCommunication.SYNC_MESSAGE, true);
            } else {
                comm.receiveMessage(comm.getBatonAgent(), true);
            }
        }
        return finished;
    }

    /**
     * Clears the cache, which stores already computed paths for value
     * transitions.
     *
     * @param threadIndex Thread index (for multi-thread purposes)
     * @since 1.0
     */
    @Override
    public void clearCache(int threadIndex) {
        for (DTG dtg : dtgs.values()) {
            dtg.clearCache(threadIndex);
        }
    }
}
