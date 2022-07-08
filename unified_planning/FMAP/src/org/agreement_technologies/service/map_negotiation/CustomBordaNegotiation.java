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
package org.agreement_technologies.service.map_negotiation;

import java.util.ArrayList;
import java.util.Hashtable;
import java.util.Map;
import java.util.Set;
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_negotiation.PlanSelection;
import org.agreement_technologies.common.map_planner.Plan;
import org.agreement_technologies.common.map_planner.IPlan;
import org.agreement_technologies.service.map_planner.POPIncrementalPlan;
import org.agreement_technologies.common.map_planner.POPSearchMethod;

/**
 * Borda-based negotiation method for self-interested agents.
 * 
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class CustomBordaNegotiation implements PlanSelection {
    
    private final AgentCommunication comm;      // Communication utility
    private final int numProposals;             // Number of proposals for voting
    private final POPSearchMethod searchTree;   // Search tree
    
    /**
     * Creates a new borda plan selector.
     *
     * @param c Communication utility
     * @param pst Search tree
     * @param n Number of proposals
     * @since 1.0
     */
    public CustomBordaNegotiation(AgentCommunication c, POPSearchMethod pst, int n) {
        this.comm = c;
        this.searchTree = pst;
        this.numProposals = n;
    }
    
    /**
     * Selects next base plan to expand according to the borda-voting criterion.
     *
     * @return Base plan to expand
     * @since 1.0
     */
    @Override
    public Plan selectNextPlan() {
        //Single agent
    	if (comm.numAgents() == 1)
            return (POPIncrementalPlan) searchTree.getNextPlan();
        //Multi-agent
        POPIncrementalPlan plan;
        IPlan[] plans;
        //Baton agent
    	if (comm.batonAgent()) {
            Hashtable<String, Integer> votes = new Hashtable<>();
            //Receive other agents' messages (votes)
            int value;
            for(int i = 0; i < comm.getOtherAgents().size(); i++) {
                String[] agentVotes = (String[]) comm.receiveMessage(true);
                //Size of the plan list: n
                //First plan in the list: n points
                //Last plan in the list: 1 point
                value = agentVotes.length;
                //Add agent's votes to the hash table
                for(String v: agentVotes) {
                    if(votes.contains(v))
                        votes.put(v, votes.get(v) + value);
                    else
                        votes.put(v, value);
                    value--;
                }
            }
            //Compute and add baton agent's votes
            plans = this.searchTree.getFirstPlans(numProposals);
            
            value = plans.length;
            for(IPlan p: plans) {
                if(votes.containsKey(p.getName()))
                    votes.put(p.getName(), votes.get(p.getName()) + value);
                    else
                        votes.put(p.getName(), value);
                value--;
            }
            
            //Select most voted plan as the next base plan
            Set<Map.Entry<String, Integer>> voteSet = votes.entrySet();            
            int nVotes = 0;
            ArrayList<String> planNames = new ArrayList<>();
            for(Map.Entry<String, Integer> pv: voteSet) {
                if(pv.getValue() > nVotes) {
                    nVotes = pv.getValue();
                    planNames.clear();
                    planNames.add(pv.getKey());
                }
                else if(pv.getValue() == nVotes)
                    planNames.add(pv.getKey());
            }
            
            if(planNames.size() == 1)
                plan = (POPIncrementalPlan) searchTree.removePlan(planNames.get(0));
            else
                plan = (POPIncrementalPlan) searchTree.removePlan(tieBreak(planNames).getName());
            
            if (plan != null) 
                //The baton agent sends only the name of the plan
                comm.sendMessage(plan.getName(), true);
            else 
                comm.sendMessage(AgentCommunication.NO_SOLUTION_MESSAGE, true);
        } 
        
        //Non-baton agent
        else {
            plans = this.searchTree.getFirstPlans(numProposals);
            String[] names = new String[plans.length];
            
            for(int i = 0; i < plans.length; i++)
                names[i] = plans[i].getName(); 
            //Send this agent's list of candidate plans to the baton agent
            comm.sendMessage(comm.getBatonAgent(), names, true);
            
            //Receive the next base plan as a result of the Borda voting
            String planName = (String) comm.receiveMessage(comm.getBatonAgent(), true);
            if (planName.equals(AgentCommunication.NO_SOLUTION_MESSAGE)) 
                plan = null;
            else 
                //The agent selects and extracts a plan that matches the plan name it received
                plan = (POPIncrementalPlan) searchTree.removePlan(planName);
	}
	return plan;
    }
    
    /**
     * Chooses a plan in case of a tie in the initial Borda voting.
     *
     * @param planNames Name of the tied plans
     * @return Selected plan
     * @since 1.0
     */
    private IPlan tieBreak(ArrayList<String> planNames) {
        IPlan bestPlan = null, current;
        int publicValue, bestValue = Integer.MAX_VALUE;
        
        for(String n: planNames) {
            current = this.searchTree.getPlanByName(n);
            publicValue = this.searchTree.getPublicValue(current);
            if(publicValue < bestValue) {
                bestValue = publicValue;
                bestPlan = current;
            }
        }
        return bestPlan;
    }
    
}
