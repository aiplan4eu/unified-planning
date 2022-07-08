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
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_landmarks.LandmarkAction;
import org.agreement_technologies.common.map_landmarks.LandmarkFluent;
import org.agreement_technologies.common.map_landmarks.LandmarkGraph;
import org.agreement_technologies.common.map_landmarks.LandmarkNode;
import org.agreement_technologies.common.map_landmarks.LandmarkOrdering;
import org.agreement_technologies.common.map_landmarks.LandmarkSet;

/**
 * MALandmarkGraph is the multi-agent landmark graph (LG) implementation.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class MALandmarkGraph implements LandmarkGraph {

    private ArrayList<LandmarkNode> nodes;          // List of landmark nodes
    private ArrayList<LandmarkOrdering> edges;      // List of orderings between nodes
    private RPG RPG;                                // Relaxed planning graph
    private final Boolean[][] matrix;               // Orderings matrix
    private ArrayList<Integer> literalNode;         // Maps literals and nodes of the LG
    private ArrayList<ArrayList<LandmarkNode>> objs;    // Goal landmarks per RPG level
    private boolean[][] reasonableOrderings;            // Reasobale orderings matrix
    private ArrayList<LandmarkOrdering> reasonableOrderingsList;        // List of reasonable orderings
    private ArrayList<LandmarkOrdering> reasonableOrderingsGoalsList;   // List of reasonable orderings to goals
    private final GroundedTask groundedTask;            // Grounded task
    private final AgentCommunication comm;              // Communication utility
    private ArrayList<LandmarkFluent> I;                // Common and non-common precs of a literal
    private ArrayList<LandmarkFluent> U;
    private ArrayList<LandmarkSet> D;
    private ArrayList<LMLiteralInfo> commonToSend;      //Common precs to send each agent
    private ArrayList<LMLiteralInfo> nonCommonToSend;   //Non common precs to send each agent
    private final Hashtable<String, LandmarkNode> hashLGNodes;  // Hash table for landmark nodes
    private Hashtable<String, Integer> hashAgents;              // Hash table for agents
    // Set of actions that produce a certain literal or disjunction of literals (placed before the literal in the RPG)
    private ArrayList<LandmarkAction> A;
    //Total number of landmarks (single landmarks that are not in the initial state)
    public int totalLandmarks;
    // Hash table for agents diferent than this one
    private Hashtable<Integer, ArrayList<String>> otherAgentsLandmarks;
    // Index used to label the landmarkswith a global identifier
    private int globalIndex;

    /**
     * Creates a new distributed landmarks graph.
     *
     * @param gt Grounded task
     * @param c Communication utility
     * @param r Relaxed planning graph
     * @param g List of landmark fluents
     * @since 1.0
     */
    public MALandmarkGraph(GroundedTask gt, AgentCommunication c, RPG r, ArrayList<LandmarkFluent> g) {
        globalIndex = 0;
        groundedTask = gt;
        comm = c;
        int i, messageType, visited;
        nodes = new ArrayList<>();      // N: Landmark tree nodes
        edges = new ArrayList<>();      // E: landmark tree links (necessary orderings)
        this.RPG = r;                   // r: RPG associated to the LT
        ArrayList<LMLiteralInfo> commonPrecs;
        ArrayList<LMLiteralInfo> nonCommonPrecs;
        D = new ArrayList<>();

        i = 0;
        hashAgents = new Hashtable<>();
        for (String ag : groundedTask.getAgentNames()) {
            hashAgents.put(ag, i);
            i++;
        }
        ArrayList<MessageContentLandmarkGraph> received = new ArrayList<>();

        //literalNode maps literals and nodes of the landmark graph
        literalNode = new ArrayList<>(r.getLiterals().size());
        for (i = 0; i < r.getLiterals().size(); i++) {
            literalNode.add(-1);
        }

        //Initializing objs array
        objs = new ArrayList<>(r.getLitLevels().size());
        for (i = 0; i < r.getLitLevels().size(); i++) {
            objs.add(new ArrayList<LandmarkNode>());
        }

        //Adding goals to N and objs(lvl), where lvl is the RPG level in which each goal first appears
        for (LandmarkFluent goal : g) {
            //Create the LGNode and set its global identifier
            LGNode gn = new LGNode(goal);
            globalIndex = gn.setGlobalId(globalIndex);
            nodes.add(gn);
            nodes.get(nodes.size() - 1).setIndex(nodes.size() - 1);
            literalNode.set(goal.getIndex(), nodes.size() - 1);
            if (goal.getLevel() < 0) {
                throw new AssertionError("Goal not achieved: " + goal);
            } else {
                objs.get(goal.getLevel()).add(gn);
            }
        }

        //The RPG is explored backwards, beginning from the last literal level
        int level = r.getLitLevels().size() - 1;

        I = new ArrayList<>();
        U = new ArrayList<>();
        commonToSend = new ArrayList<>();
        nonCommonToSend = new ArrayList<>();

        LandmarkNode obj;

        int remainingObjects = objs.get(level).size();
        MessageContentLandmarkGraph remainingObjectsMsg;
        LandmarkNode newNode;
        while (level > 0) {
            //Baton agent - solves a complete level of the objs structure
            if (comm.batonAgent()) {
                if (objs.get(level).size() > 0) {
                    // Exploring level "level"
                    //Analyze literals of the current level
                    for (i = 0; i < objs.get(level).size(); i++) {
                        obj = objs.get(level).get(i);
                        // Baton agent + comm.getThisAgentName() + " analyzing landmark \t(" + obj.toString() + ")");
                        // If the literal is shareable, send a warning to the related agents
                        if (obj.getAgents().size() > 1) {
                            for (String ag : obj.getAgents()) {
                                if (!ag.equals(this.groundedTask.getAgentName())) {
                                    comm.sendMessage(ag, new MessageContentLandmarkGraph(null, obj.identify(), null, null, null, null,
                                            groundedTask.getAgentName(), null, MessageContentLandmarkGraph.COMMON_PRECS_STAGE), false);
                                }
                            }
                        }
                        //Calculate the set A of actions that produce the literal selected in objs[level]
                        this.getProducers(obj, null);
                        //Clear I and U arrays before refilling them
                        I.clear();
                        U.clear();
                        D.clear();
                        //Once A is calculated, I and U are also computed
                        //getCommonNonCommonPrecs is only launched if there are producers, that is, if A is not an empty set
                        if (A.size() > 0) {
                            groupCommonNonCommonPrecs(A/*, At*/);
                        }
                        //Clear the received structure before refilling it
                        received.clear();
                        //Receive common and non common precs obtained by other agents
                        for (int j = 0; j < obj.getAgents().size() - 1; j++) {
                            received.add((MessageContentLandmarkGraph) comm.receiveMessage(false));
                        }
                        //Calculate precs that are common to all the agents' actions
                        groupMACommonNonCommonPrecs(received, A.size() != 0, obj.getAgents());
                        //Send common precs to the rest of involved agents
                        for (String ag : obj.getAgents()) {
                            if (!ag.equals(this.groundedTask.getAgentName())) {
                                comm.sendMessage(ag, new MessageContentLandmarkGraph(globalIndex, null, commonToSend,
                                        nonCommonToSend, null, null, groundedTask.getAgentName(), null,
                                        MessageContentLandmarkGraph.COMMON_PRECS_STAGE), false);
                            }
                        }
                        //Verification stage: check if the common precs identified are actually landmarks
                        //All the agents take part in the verification stage
                        //Warning the agents that have not participated in the common precs stage
                        for (String ag : comm.getOtherAgents()) {
                            if (!obj.getAgents().contains(ag)) {
                                comm.sendMessage(ag, new MessageContentLandmarkGraph(globalIndex, obj.identify(), commonToSend,
                                        nonCommonToSend, null, null, groundedTask.getAgentName(),
                                        null, MessageContentLandmarkGraph.VERIFICATION_STAGE), false);
                            }
                        }
                        //Adding nodes and transitions to the landmark graph and precs to the objs structure
                        for (LMLiteralInfo cp : commonToSend) {
                            //System.out.println("Baton agent " + comm.getThisAgentName() + " verifying common prec \t(" + cp.getLiteral() + ")");
                            this.verifyCommonPrec(cp, obj);
                        }
                        //Verification procedure for disjunctive landmark candidates
                        for (LMLiteralInfo ncp : nonCommonToSend) {
                            //System.out.println("Baton agent " + comm.getThisAgentName() + " verifying non common prec \t(" + ncp.getFunction() + ")");
                            this.verifyNonCommonPrec(ncp, commonToSend, obj, level);
                        }
                    }
                    //Clean the objs structure after analyzing the objects of the last level
                    objs.get(level).clear();
                }
            } //Non-baton agent - waits for messages and helps the baton agent to analyze shareable fluents
            else {
                if (remainingObjects > 0) {
                    for (i = remainingObjects; i > 0; i--) {
                        //Wait for a message from the baton agent
                        MessageContentLandmarkGraph m = (MessageContentLandmarkGraph) comm.receiveMessage(comm.getBatonAgent(), false);
                        //Classify the message according to its type:
                        //Common precs stage -> help the baton agent to calculate the common precs of a landmark
                        //Verification stage -> verify a set of landmark candidates in cooperation with the rest of agents
                        if (m.getMessageType() == MessageContentLandmarkGraph.COMMON_PRECS_STAGE) {
                            String l = m.getLiteral();

                            //Locate the literal associated to the info received from the baton agent (LMLiteral obj)
                            obj = locateLGNode(l, level);
                            /*if(obj != null)
                             System.out.println("Participant agent " + comm.getThisAgentName() + " analyzing landmark (" + obj.toString() + ")");
                             else
                             System.out.println("Participant agent " + comm.getThisAgentName() + " didn't locate current landmark");
                             */
                            //Obtain the set A of actions of this agent that produce the LGNode obj, whose info has been received
                            this.getProducers(obj, l);

                            //Clear I and U arrays before refilling them
                            I.clear();
                            U.clear();
                            D.clear();
                            //Once A is calculated, I and U are also computed
                            //getCommonNonCommonPrecs is only launched if there are producers, that is, if A is not an empty set
                            //If A is empty, warn the baton agent in the following message
                            if (A.size() > 0) {
                                groupCommonNonCommonPrecs(A/*, At*/);
                                messageType = MessageContentLandmarkGraph.COMMON_PRECS_STAGE;
                            } else {
                                messageType = MessageContentLandmarkGraph.NO_PRODUCER_ACTIONS;
                            }

                            //Send back the list of common preconditions to the baton agent
                            //Additionally, send a hashmap that maps the preconditions and their variables
                            commonToSend.clear();
                            for (LandmarkFluent li : I) {
                                commonToSend.add(new LMLiteralInfo(li, groundedTask.getAgentName(), li.getAgents()));
                            }
                            //Send back the list of disjunctions of preconditions to the baton agent
                            nonCommonToSend.clear();
                            for (LandmarkSet u : D) {
                                nonCommonToSend.add(new LMLiteralInfo(u.identify(), obj.getAgents()));
                            }

                            comm.sendMessage(comm.getBatonAgent(), new MessageContentLandmarkGraph(null, null, commonToSend, nonCommonToSend, null,
                                    null, groundedTask.getAgentName(), null, messageType), false);
                            //Receive the actual common and non common precs from baton agent
                            MessageContentLandmarkGraph precsMsg = ((MessageContentLandmarkGraph) comm.receiveMessage(comm.getBatonAgent(), false));
                            //Update global index, synchronizing it with the baton agent's index
                            globalIndex = precsMsg.getGlobalIndex();

                            commonPrecs = precsMsg.getLiterals();
                            nonCommonPrecs = precsMsg.getDisjunctions();
                            //Verification procedure: check if the precs are actually landmarks
                            //Adding nodes and transitions to the landmark graph and precs to the objs structure
                            for (LMLiteralInfo cp : commonPrecs) {
                                //System.out.println("Participant agent " + comm.getThisAgentName() + " verifying common prec \t(" + cp.getLiteral() + ")");
                                this.verifyCommonPrec(cp, obj);
                            }
                            //Verification procedure for disjunctive landmark candidates
                            for (LMLiteralInfo ncp : nonCommonPrecs) {
                                //System.out.println("Participant agent " + comm.getThisAgentName() + " verifying non common prec \t(" + ncp.getFunction() + ")");
                                this.verifyNonCommonPrec(ncp, commonPrecs, obj, level);
                            }

                            //Remove the object that has been already analyzed, in case the participant agent has it
                            removeObject(obj, level);
                        } //If the participant does not know the object analyzed in this iteration,
                        //it goes directly to the verification stage
                        else if (m.getMessageType() == MessageContentLandmarkGraph.VERIFICATION_STAGE) {
                            //Update global index
                            globalIndex = m.getGlobalIndex();
                            commonPrecs = m.getLiterals();
                            nonCommonPrecs = m.getDisjunctions();
                            for (LMLiteralInfo cp : commonPrecs) {
                                //Creating a landmark node for each common prec
                                LMLiteral p = r.getLiteral(cp.getLiteral());
                                if (cp.getLevel() == 0 || cp.isGoal() || r.verifySingleLandmark(p)) {
                                    //Adding a new landmark node, if it does not exist already
                                    //and if the agent knows the literal
                                    if (p != null) {
                                        if (literalNode.get(p.getIndex()) == -1) {
                                            nodes.add(new LGNode(p));
                                            //globalIndex = nodes.get(nodes.size() - 1).setGlobalId(globalIndex);
                                            nodes.get(nodes.size() - 1).setIndex(nodes.size() - 1);
                                            literalNode.set(p.getIndex(), nodes.size() - 1);
                                            newNode = nodes.get(nodes.size() - 1);
                                        } else {
                                            newNode = nodes.get(literalNode.get(p.getIndex()));
                                        }
                                        //Adding the common prec p to the objs structure
                                        if (!objs.get(p.getLevel()).contains(newNode)) {
                                            objs.get(p.getLevel()).add(newNode);
                                        }
                                        //Necessary orderings are not added, as the agent does not know obj
                                    }
                                }
                            }
                            for (LMLiteralInfo ncp : nonCommonPrecs) {
                                String func = ncp.getFunction();
                                //Locate the disjunction associated to variable var
                                LandmarkSet d = locateDisjunction(func, commonPrecs);
                                ArrayList<LandmarkFluent> dlc;
                                if (d != null) {
                                    dlc = d.getElements();
                                } else {
                                    dlc = new ArrayList<>();
                                }
                                //Verify if the disjunction is actually a landmark
                                if (/*r.verifyDisjunctiveLandmark(dlc) && */d != null) {
                                    //Add the disjunctive landmark if the agent knows it
                                    if (ncp.getAgents().contains(groundedTask.getAgentName())) {
                                        //Adding a new disjunctive landmark node (if it does not exist already)
                                        newNode = findDisjunctiveLandmarkNode(d);
                                        if (newNode == null) {
                                            newNode = new LGNode(d);
                                            nodes.add(newNode);
                                            d.setLGNode(newNode);
                                            newNode.setIndex(nodes.size() - 1);
                                            newNode.setAgents(ncp.getAgents());
                                            newNode = nodes.get(nodes.size() - 1);
                                        }
                                        //Adding the disjunctive landmark to the objs structure
                                        if (!objs.get(level - 1).contains(newNode)) {
                                            objs.get(level - 1).add(newNode);
                                        }
                                    }
                                }
                            }

                        }
                    }
                }
            }
            //Pass baton 
            //The new baton agent should inform the participants about the size of the next level to explore
            comm.passBaton();
            visited = 1;
            while (true) {
                if (comm.batonAgent()) {
                    if (objs.get(level).size() > 0) {
                        for (String ag : comm.getOtherAgents()) {
                            comm.sendMessage(ag, new MessageContentLandmarkGraph(null, null, null, null, null, null, null,
                                    objs.get(level).size(), MessageContentLandmarkGraph.COMMON_PRECS_STAGE), false);
                        }
                        break;
                    } else {
                        if (visited < groundedTask.getAgentNames().length) {
                            for (String ag : comm.getOtherAgents()) {
                                comm.sendMessage(ag, new MessageContentLandmarkGraph(null, null, null, null, null, null, null,
                                        objs.get(level).size(), MessageContentLandmarkGraph.PASS_BATON), false);
                            }
                            visited++;
                            comm.passBaton();
                        } else {
                            if (level > 0) {
                                for (String ag : comm.getOtherAgents()) {
                                    comm.sendMessage(ag, new MessageContentLandmarkGraph(null, null, null, null, null, null, null,
                                            objs.get(level - 1).size(), MessageContentLandmarkGraph.CHANGE_LEVEL), false);
                                }
                                level--;
                                if (objs.get(level).size() > 0) {
                                    break;
                                } else {
                                    visited = 1;
                                    comm.passBaton();
                                }
                            } //Level = 0 and there are no more landmarks; end the procedure
                            else {
                                for (String ag : comm.getOtherAgents()) {
                                    comm.sendMessage(ag, new MessageContentLandmarkGraph(null, null, null, null, null, null, null,
                                            null, MessageContentLandmarkGraph.END_PROCEDURE), false);
                                }
                                break;
                            }
                        }
                    }
                } //Participant agent
                else {
                    remainingObjectsMsg = ((MessageContentLandmarkGraph) comm.receiveMessage(comm.getBatonAgent(), false));
                    if (remainingObjectsMsg.getMessageType() == MessageContentLandmarkGraph.END_PROCEDURE) {
                        break;
                    }
                    remainingObjects = remainingObjectsMsg.getNextLevelSize();
                    if (remainingObjectsMsg.getMessageType() == MessageContentLandmarkGraph.PASS_BATON) {
                        visited++;
                        comm.passBaton();
                    } else if (remainingObjectsMsg.getMessageType() == MessageContentLandmarkGraph.CHANGE_LEVEL) {
                        level--;
                        if (remainingObjects > 0) {
                            break;
                        } else {
                            visited = 1;
                            comm.passBaton();
                        }
                    } else {
                        break;
                    }
                }
            }
        }

        //Creating the adjacency matrix
        hashLGNodes = new Hashtable<>();
        matrix = new Boolean[nodes.size()][nodes.size()];
        for (i = 0; i < nodes.size(); i++) {
            //Fill the LGNodes hashtable
            if (nodes.get(i).isSingleLiteral()) {
                hashLGNodes.put(nodes.get(i).getLiteral().toString(), nodes.get(i));
            }
            for (int j = 0; j < nodes.size(); j++) {
                matrix[i][j] = false;
            }
        }
        for (LandmarkOrdering o : edges) {
            matrix[o.getNode1().getIndex()][o.getNode2().getIndex()] = true;
        }

        //Verifying necessary orderings
        MAPostProcessing();

        //Creating the accessibility matrix
        this.computeAccessibilityMatrix();

        //Calculate global indexes for each landmark found
        this.setGlobalIndexes();

        //Set a vector of antecessors for each LGNode (single landmarks that are ordered before the LGNode
        this.setAntecessorLandmarks();
        //Sharing private landmarks to establish the total number of landmarks for this problem
        sharePrivateLandmarks();

        //Calculating reasonable orderings
        /**
         * ****reasonableOrderings = getReasonableOrderings();*****
         */
        int count = 0;
        for (LandmarkNode n : nodes) {
            if (n.isSingleLiteral() && !n.getLiteral().isGoal() && n.getLiteral().getLevel() != 0) {
                count++;
            }
        }
        //System.out.println("Agent " + comm.getThisAgentName() + " found " + count + " single landmarks (non-goal/non-initial state)");

        //System.out.println(nodes.size() + " landmarks found");
        //System.out.println(edges.size() + " necessary orderings found");
    }

    /**
     * Set, for each single landmark that is not part of the initial state nor
     * goal, which single landmarks (not part of the initial state nor goals)
     * precede it.
     *
     * @since 1.0
     */
    private void setAntecessorLandmarks() {
        ArrayList<Integer> antecessors;
        for (LandmarkNode n : nodes) {
            if (n.isSingleLiteral() && n.getLiteral().getLevel() != 0) {
                antecessors = new ArrayList<>();
                for (int i = 0; i < nodes.size(); i++) {
                    if (matrix[i][n.getIndex()] == true && nodes.get(i).isSingleLiteral()) {
                        antecessors.add(i);
                    }
                }
                n.setAntecessors(antecessors);
            }
        }
    }

    /**
     * Agents assign a unique index to their landmark nodes.
     *
     * @since 1.0
     */
    private void setGlobalIndexes() {
        int iter = 0;

        while (iter < comm.getAgentList().size()) {
            //Baton agent: set identifiers and communicate other agents the id of each shared landmark
            if (comm.batonAgent()) {
                //Initialize arrays of messages
                ArrayList<MessageContentGlobalId> messages = new ArrayList<>();
                ArrayList<ArrayList<GlobalIdInfo>> contents = new ArrayList<>();
                for (int i = 0; i < comm.numAgents(); i++) {
                    contents.add(new ArrayList<GlobalIdInfo>());
                }
                for (LandmarkNode n : nodes) {
                    if (n.getGlobalId() == -1 && n.isSingleLiteral()) {
                        globalIndex = n.setGlobalId(globalIndex);
                        if (n.getAgents().size() > 1) {
                            for (String name : n.getAgents()) {
                                if (!name.equals(comm.getThisAgentName())) {
                                    contents.get(comm.getAgentIndex(name)).
                                            add(new GlobalIdInfo(n.getLiteral().toString(), globalIndex - 1));
                                }
                            }
                        }
                    }
                }
                for (ArrayList<GlobalIdInfo> c : contents) {
                    messages.add(new MessageContentGlobalId(c));
                }

                for (MessageContentGlobalId m : messages) {
                    m.setCurrentGlobalIndex(globalIndex);
                }
                //Send global identifiers of the shared landmarks
                for (String ag : comm.getOtherAgents()) {
                    comm.sendMessage(ag, messages.get(comm.getAgentIndex(ag)), false);
                }
            } //Non-baton agent: receive landmarks and update global identifiers
            else {
                MessageContentGlobalId indexes = (MessageContentGlobalId) comm.receiveMessage(comm.getBatonAgent(), false);
                for (GlobalIdInfo m : indexes.getLiterals()) {
                    hashLGNodes.get(m.getLiteral()).setGlobalId(m.getGlobalId());
                }
                //Update global index
                globalIndex = indexes.getCurrentGlobalIndex();
            }
            comm.passBaton();
            iter++;
        }
    }

    /**
     * Agents share their single landmarks, so that all the agents know the
     * complete list of landmarks.
     *
     * @since 1.0
     */
    private void sharePrivateLandmarks() {
        int agentsDone = 0;
        boolean alreadySent;
        boolean[] batonAgents = new boolean[comm.getAgentList().size()];
        for (int i = 0; i < batonAgents.length; i++) {
            batonAgents[i] = false;
        }

        ArrayList<MessageContentLandmarkSharing> received;
        ArrayList<MessageContentLandmarkSharing> receivedLandmarks = new ArrayList<>();
        ArrayList<ArrayList<MessageContentLandmarkSharing>> dataToSend = new ArrayList<>();
        for (String ag : comm.getAgentList()) {
            dataToSend.add(new ArrayList<MessageContentLandmarkSharing>());
        }

        while (agentsDone < comm.getAgentList().size()) {
            if (comm.batonAgent()) {
                for (LandmarkNode n : nodes) {
                    //Only single landmarks that are not in the initial state nor goals are considered
                    if (n.isSingleLiteral() && n.getLiteral().getLevel() != 0 && !n.getLiteral().isGoal()) {
                        //Verify if another agent has already sent the landmark
                        alreadySent = false;
                        for (String label : n.getLiteral().getAgents()) {
                            if (batonAgents[comm.getAgentIndex(label)]) {
                                alreadySent = true;
                                break;
                            }
                        }
                        //If the landmark has not been already sent, prepare to send it
                        if (!alreadySent) {
                            for (String ag : comm.getOtherAgents()) {
                                if (!n.getLiteral().getAgents().contains(ag)) {
                                    //Landmark identifier, ?index, where index is a unique integer
                                    dataToSend.get(comm.getAgentIndex(ag)).
                                            add(new MessageContentLandmarkSharing(n.getGlobalId(), n.getLiteral().getAgents()));
                                }
                            }
                        }
                    }
                }
                //Send landmarks to the rest of agents
                for (String ag : comm.getOtherAgents()) {
                    comm.sendMessage(ag, dataToSend.get(comm.getAgentIndex(ag)), false);
                }
            } else {
                //Receive landmarks from current baton agent
                received = (ArrayList<MessageContentLandmarkSharing>) comm.receiveMessage(comm.getBatonAgent(), false);
                receivedLandmarks.addAll(received);
            }
            //Mark the agent that has performed the baton agent role
            batonAgents[comm.getAgentIndex(comm.getBatonAgent())] = true;
            //Pass the baton agent role
            comm.passBaton();
            //Increase the number of agents that have finished sending landmarks
            agentsDone++;
        }
        //Add landmarks to the landmark tree
        otherAgentsLandmarks = new Hashtable<>();
        for (MessageContentLandmarkSharing m : receivedLandmarks) {
            otherAgentsLandmarks.put(m.getLiteralId(), m.getAgents());
        }
        //Calculate the total number of landmarks to reach (hL value of the initial empty plan)
        totalLandmarks = 0;
        for (LandmarkNode n : nodes) {
            if (n.isSingleLiteral() && n.getLiteral().getLevel() != 0/* && !n.isGoal()*/) {
                totalLandmarks++;
            }
        }
        totalLandmarks += otherAgentsLandmarks.keySet().size();
        //System.out.println("Agent " + comm.getThisAgentName() + " found " + totalLandmarks + " relevant simple landmarks");
    }

    /**
     * Verifies a commom precondition for a landmark node.
     *
     * @param commonPrec Common preconditon
     * @param obj Landmark node
     * @since 1.0
     */
    private void verifyCommonPrec(LMLiteralInfo commonPrec, LandmarkNode obj) {
        LandmarkNode newNode;
        //Creating a landmark node for each common prec
        LMLiteral p = RPG.getLiteral(commonPrec.getLiteral());
        if (commonPrec.getLevel() == 0 || commonPrec.isGoal() || RPG.verifySingleLandmark(p)) {
            //System.out.println("Agent " + comm.getThisAgentName() + " verified landmark " + commonPrec.getLiteral());
            //Adding a new landmark node (if it does not exist already)
            //If the agent does not know the LMLiteral p, just end the procedure
            if (p != null) {
                if (literalNode.get(p.getIndex()) == -1) {
                    nodes.add(new LGNode(p));

                    nodes.get(nodes.size() - 1).setIndex(nodes.size() - 1);
                    literalNode.set(p.getIndex(), nodes.size() - 1);
                    newNode = nodes.get(nodes.size() - 1);
                } else {
                    newNode = nodes.get(literalNode.get(p.getIndex()));
                }
                //Adding a new necessary ordering p -> obj to the list of edges
                if (obj != null) {
                    edges.add(new LMOrdering(newNode,
                            nodes.get(obj.getIndex()), LandmarkOrdering.NECESSARY));
                }
                //Adding the common prec p to the objs structure
                if (!objs.get(p.getLevel()).contains(newNode)) {
                    objs.get(p.getLevel()).add(newNode);
                }
            }
        }
    }

    /**
     * Verifies a non-commom precondition for a landmark node.
     *
     * @param nonCommonPrec Non-common preconditions
     * @param commonPrecs List of common preconditons
     * @param obj Landmark node
     * @param level Level in the RPG
     * @since 1.0
     */
    private void verifyNonCommonPrec(LMLiteralInfo nonCommonPrec, ArrayList<LMLiteralInfo> commonPrecs,
            LandmarkNode obj, int level) {
        boolean valid;
        //Locate the disjunction associated to variable var
        LandmarkSet d = locateDisjunction(nonCommonPrec.getFunction(), commonPrecs);
        //Disjunctive landmarks don't require verification
        //If the agent knows the disjunction, add a node and a transition to the graph
        if (d != null) {
            //Adding a new disjunctive landmark node (if it does not exist already)
            LandmarkNode newNode = findDisjunctiveLandmarkNode(d);

            if (newNode == null) {
                newNode = new LGNode(d);
                nodes.add(newNode);
                d.setLGNode(newNode);
                newNode.setIndex(nodes.size() - 1);
                newNode.setAgents(obj.getAgents());
                newNode = nodes.get(nodes.size() - 1);
                //Adding a new necessary ordering p -> obj to the list of edges
                edges.add(new LMOrdering(newNode,
                        nodes.get(obj.getIndex()), LandmarkOrdering.NECESSARY));
            } else {
                valid = true;
                for (LandmarkOrdering o : edges) {
                    if (o.getNode1().getIndex() == obj.getIndex()
                            && o.getNode2().getIndex() == newNode.getIndex()) {
                        valid = false;
                        break;
                    }
                }
                if (valid) {
                    edges.add(new LMOrdering(newNode,
                            nodes.get(obj.getIndex()), LandmarkOrdering.NECESSARY));
                }
            }
            //Adding the disjunctive landmark to the objs structure
            if (!objs.get(level - 1).contains(newNode)) {
                objs.get(level - 1).add(newNode);
            }
        }
    }

    /**
     * Searches for a landmark node.
     *
     * @param id Identifier of the node.
     * @param level Level in the RPG to search in
     * @return The landmark node if it is found; <code>null</code>, otherwise
     * @since 1.0
     */
    private LandmarkNode locateLGNode(String id, int level) {
        for (LandmarkNode l : objs.get(level)) {
            if (l.identify().equals(id)) {
                return l;
            }
        }
        return null;
    }

    /**
     * Locate the disjunction referred to the variable received.
     *
     * @param var Variable name
     * @param common List of common preconditions
     * @return The landmark set if it is found; <code>null</code>, otherwise
     * @since 1.0
     */
    private LandmarkSet locateDisjunction(String var, ArrayList<LMLiteralInfo> common) {
        //Locate the disjunction referred to the variable received (if any) 
        for (LandmarkSet u : D) {
            if (u.identify().equals(var)) {
                return u;
            }
        }
        //The variable may refer to a precondition initially considered as a common one
        boolean found = false;
        //If a literal in I has the variable var and it has not been received in the common list
        //create a uSet from the literal and return it
        for (LandmarkFluent l : I) {
            if (l.getVar().getFuctionName().equals(var)) {
                for (LMLiteralInfo li : common) {
                    if (l.toString().equals(li.getLiteral())) {
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    return new uSet(l);
                }
            }
        }
        return null;
    }

    /**
     * Removes an explored object from the objs structure
     *
     * @param lit Identifier of the literal/disjunction
     * @param level Level of the objs structure where the object is placed
     * @since 1.0
     */
    private void removeObject(LandmarkNode obj, int level) {
        objs.get(level).remove(obj);
    }

    /**
     * Find a disjunctive landmark corresponding to a uSet if it is already in
     * the landmark graph
     *
     * @param u uSet identifying the disjunctive landmark
     * @return The disjunctive landmark, if it exists; <code>null</code>,
     * otherwise
     * @since 1.0
     */
    private LandmarkNode findDisjunctiveLandmarkNode(LandmarkSet u) {
        if (u == null) {
            return null;
        }
        for (LandmarkNode n : this.nodes) {
            if (!n.isSingleLiteral()) {
                if (n.getDisjunction().identify().equals(u.identify())) {
                    if (n.getDisjunction().getElements().size() != u.getElements().size()) {
                        return null;
                    }
                    int found = 0;
                    for (LandmarkFluent ln : n.getDisjunction().getElements()) {
                        for (LandmarkFluent lu : u.getElements()) {
                            if (ln.toString().equals(lu.toString())) {
                                found++;
                                break;
                            }
                        }
                    }
                    if (found == u.getElements().size()) {
                        return n;
                    }
                }
            }
        }
        return null;
    }

    /**
     * Calculates I and U, common and non-common preconditions of a set of
     * actions A.
     *
     * @param A Set of actions to analyze
     * @since 1.0
     */
    private void groupCommonNonCommonPrecs(ArrayList<LandmarkAction> A) {
        int[] common = new int[RPG.getLiterals().size()];
        int[] nonCommon = new int[RPG.getLiterals().size()];
        boolean valid;
        //String [] prod = new String[RPG.getLiterals().size()];
        ArrayList<ArrayList<LandmarkAction>> producers = new ArrayList<>();
        Hashtable<Integer, ArrayList<LandmarkAction>> prods = new Hashtable<>();

        for (int i = 0; i < common.length; i++) {
            common[i] = 0;
        }
        for (LandmarkAction a : A) {
            for (LandmarkFluent l : a.getPreconditions()) {
                common[l.getIndex()] = common[l.getIndex()] + 1;
                //prod[l.getIndex()] = a.toString();
                if (prods.get(l.getIndex()) == null) {
                    prods.put(l.getIndex(), new ArrayList<LandmarkAction>());
                }
                prods.get(l.getIndex()).add(a);
            }
        }

        for (int i = 0; i < common.length; i++) {
            //If the literal is common, check if all the actions in A do introdce it
            if (common[i] == A.size()) {
                valid = true;
                for (LandmarkAction a : A) {
                    if (!prods.get(i).contains(a)) {
                        valid = false;
                        break;
                    }
                }
                if (valid) {
                    I.add(RPG.getIndexLiterals().get(i));
                }
            }
        }
        for (int i = 0; i < nonCommon.length; i++) {
            if (nonCommon[i] > 0 && nonCommon[i] < A.size()) {
                U.add(RPG.getIndexLiterals().get(i));
                producers.add(prods.get(i));
            }
        }

        //D stores the uSets found
        if (U.size() > 0) {
            D = groupUSet(U, A, producers);
        }
    }

    /**
     * Group the preconditions according to their functions.
     *
     * @param u List of preconditions
     * @param A List of actions
     * @param producers For each fluent, list of actions that produce that
     * fluent
     * @return List of sets of landmaks (groups of landmarks)
     * @since 1.0
     */
    private ArrayList<LandmarkSet> groupUSet(ArrayList<LandmarkFluent> u, ArrayList<LandmarkAction> A,
            ArrayList<ArrayList<LandmarkAction>> producers) {
        ArrayList<LandmarkSet> D = new ArrayList<>();
        Hashtable<String, uSet> hashU = new Hashtable<>();
        Hashtable<String, ArrayList<String>> hashProducers = new Hashtable<>();
        uSet set;

        //Group the preconditions according to their functions
        for (int i = 0; i < u.size(); i++) {
            LandmarkFluent l = u.get(i);
            if (hashU.get(l.getVar().getFuctionName()) == null) {
                set = new uSet(l);
                hashU.put(l.getVar().getFuctionName(), set);
                //Add the producer action to the set of producers of this disjunction
                hashProducers.put(l.getVar().getFuctionName(), new ArrayList<String>());
                for (LandmarkAction p : producers.get(i)) {
                    hashProducers.get(l.getVar().getFuctionName()).add(p.toString());
                }
            } else {
                hashU.get(l.getVar().getFuctionName()).addElement(l);
                //Add the producer action to the set of producers of this disjunction
                for (LandmarkAction p : producers.get(i)) {
                    if (!hashProducers.get(l.getVar().getFuctionName()).contains(p.toString())) {
                        hashProducers.get(l.getVar().getFuctionName()).add(p.toString());
                    }
                }
            }
        }
        //Verify if the uSets are correct
        //All the actions must have provided the uSet with at least a precondition of each type
        for (String s : hashU.keySet()) {
            if (hashProducers.get(s).size() == A.size()/* && hashU.get(s).getElements().size() == A.size()*/) {
                D.add(hashU.get(s));
            }
        }
        return D;
    }

    /**
     * Obtains the set of common precs of a literal, considering all the agents
     * that attain it. The method intersects the set of common precs of each
     * agent involved in the literal.
     *
     * @param received Sets of landmarks received from each other participating
     * agent
     * @param batonHasCommonActions Indicates if the baton agent has common
     * actions
     * @param agents List of agent names
     * @since 1.0
     */
    private void groupMACommonNonCommonPrecs(ArrayList<MessageContentLandmarkGraph> received,
            boolean batonHasCommonActions, ArrayList<String> agents) {
        Hashtable<String, Integer> hashCommonPrecs = new Hashtable<>();
        Hashtable<String, LMLiteralInfo> hashInfo = new Hashtable<>();
        Hashtable<String, Integer> hashNonCommonPrecs = new Hashtable<>();
        int baton = 0;

        commonToSend = new ArrayList<>();
        nonCommonToSend = new ArrayList<>();

        //Consider only the agents that have one or more producer actions
        ArrayList<ArrayList<LMLiteralInfo>> receivedLits = new ArrayList<>();
        ArrayList<ArrayList<LMLiteralInfo>> receivedDisjs = new ArrayList<>();
        for (MessageContentLandmarkGraph m : received) {
            if (m.getMessageType() != MessageContentLandmarkGraph.NO_PRODUCER_ACTIONS) {
                receivedLits.add(m.getLiterals());
                receivedDisjs.add(m.getDisjunctions());
            }
        }

        //Add this agent's literals to the hashtable
        if (batonHasCommonActions) {
            for (LandmarkFluent l : I) {
                hashInfo.put(l.toString(), new LMLiteralInfo(l, groundedTask.getAgentName(), l.getAgents()));
                hashCommonPrecs.put(l.toString(), 1);
            }
            for (LandmarkSet u : D) {
                hashInfo.put(u.identify(), new LMLiteralInfo(u.identify(), agents));
                hashNonCommonPrecs.put(u.identify(), 1);
            }
            baton = 1;
        }
        //Add the rest of agents' literals
        for (ArrayList<LMLiteralInfo> agLits : receivedLits) {
            for (LMLiteralInfo s : agLits) {
                if (hashCommonPrecs.get(s.getLiteral()) == null) {
                    hashCommonPrecs.put(s.getLiteral(), 1);
                    hashInfo.put(s.getLiteral(), s);
                } else {
                    hashCommonPrecs.put(s.getLiteral(), hashCommonPrecs.get(s.getLiteral()) + 1);
                }
            }
        }
        for (ArrayList<LMLiteralInfo> agDisjs : receivedDisjs) {
            for (LMLiteralInfo disj : agDisjs) {
                String su = disj.getFunction();
                if (hashNonCommonPrecs.get(su) == null) {
                    hashInfo.put(su, disj);
                    hashNonCommonPrecs.put(su, 1);
                } else {
                    hashNonCommonPrecs.put(su, hashNonCommonPrecs.get(su) + 1);
                }
            }
        }

        //Calculate which preconditions are actually common and prepare the information to be sent to the rest of agents
        for (String key : hashCommonPrecs.keySet()) {
            if (hashCommonPrecs.get(key) == receivedLits.size() + baton) {
                commonToSend.add(hashInfo.get(key));
            } //A precondition that is common to all the actions of an agent may actually be a part of a disjoint set
            else {
                //Add up the number of agents that have the literal key as a common precondition
                if (hashNonCommonPrecs.get(hashInfo.get(key).getFunction()) == null) {
                    hashInfo.put(hashInfo.get(key).getFunction(),
                            new LMLiteralInfo(hashInfo.get(key).getFunction(), agents));
                    hashNonCommonPrecs.put(hashInfo.get(key).getFunction(), 1);
                } else {
                    hashNonCommonPrecs.put(hashInfo.get(key).getFunction(), hashNonCommonPrecs.get(hashInfo.get(key).getFunction()) + 1);
                }
            }
        }
        //Calculate actual disjunctions and prepare to send their identifiers
        for (String key : hashNonCommonPrecs.keySet()) {
            //If all the agents that have producer actions have a set of non-common preconditions of this type
            //(or a single precondition that has not been confirmed as a single landmark)
            //send back the disjunction as a confirmed disjunctive landmark
            if (hashNonCommonPrecs.get(key) == (receivedLits.size() + baton)) {
                nonCommonToSend.add(hashInfo.get(key));
            }
        }
    }

    /**
     * Postprocessing that verifies the edges of the landmark tree.
     *
     * @since 1.0
     */
    private void MAPostProcessing() {
        //A: Actions that produce a landmark g
        ArrayList<LandmarkAction> A = new ArrayList<>();
        ArrayList<MessageContentPostProcessing> orderings = new ArrayList<>();
        int i, j;
        boolean ordering;
        boolean done = false;
        ArrayList<LandmarkOrdering> auxEdges;

        //Edges hashtable: true -> verified edge; false -> non-verified edge
        Hashtable<String, Boolean> hashEdges = new Hashtable<>();
        for (LandmarkOrdering e : edges) {
            if (e.getNode1().isSingleLiteral() && e.getNode2().isSingleLiteral()) {
                hashEdges.put(e.getNode1().getLiteral().toString() + " -> " + e.getNode2().getLiteral().toString(), false);
            }
        }

        while (true) {
            auxEdges = new ArrayList<>();
            for (LandmarkOrdering e : edges) {
                auxEdges.add(e);
            }

            if (comm.batonAgent()) {
                orderings.clear();
                done = true;
                for (i = 0; i < nodes.size(); i++) {
                    //Only single literals are processed
                    if (nodes.get(i).isSingleLiteral()) {
                        for (j = 0; j < nodes.size(); j++) {
                            //Check g column of the matrix to find literals l such that l <=n g
                            if (matrix[j][i] == true) {
                                if (nodes.get(j).isSingleLiteral()) {
                                    if (hashEdges.get(nodes.get(j).getLiteral().toString() + " -> " + nodes.get(i).getLiteral().toString()) == false) {
                                        orderings.add(new MessageContentPostProcessing(nodes.get(j).getLiteral().toString(), nodes.get(i).getLiteral().toString()));
                                    }
                                }
                            }
                        }
                    }
                }
                //Send list of orderings to verify
                for (String ag : comm.getOtherAgents()) {
                    comm.sendMessage(ag, orderings, false);
                }
                //Verify the list of orderings
                for (MessageContentPostProcessing o : orderings) {
                    A = this.getActions(RPG.getHashLiterals().get(o.getLiteral1()),
                            RPG.getHashLiterals().get(o.getLiteral2()));

                    //System.out.println("Baton agent " + comm.getThisAgentName() +  " verifying necessary ordering " + o.getLiteral1() + " -> " + o.getLiteral2());
                    //Mark the necessary ordering as verified
                    hashEdges.put(o.getLiteral1() + " -> " + o.getLiteral2(), true);
                    //Remove the edge in case it is not verified
                    if (!RPG.verifyEdge(A)) {
                        //System.out.println("Necessary ordering " + o.getLiteral1() + " -> " + o.getLiteral2() + " not verified");
                        for (LandmarkOrdering e : edges) {
                            if (e.getNode1().isSingleLiteral() && e.getNode2().isSingleLiteral()) {
                                if (e.getNode1().getLiteral().getIndex() == RPG.getHashLiterals().get(o.getLiteral1()).getIndex()
                                        && e.getNode2().getLiteral().getIndex() == RPG.getHashLiterals().get(o.getLiteral2()).getIndex()) {
                                    auxEdges.remove(e);
                                }
                            }
                        }
                    }
                    /*else  {
                     System.out.println("Necessary ordering " + o.getLiteral1() + " -> " + o.getLiteral2() + " verified!");
                     }*/
                }
            } //Participant agent
            else {
                orderings = (ArrayList<MessageContentPostProcessing>) comm.receiveMessage(comm.getBatonAgent(), false);
                //Verify the list of orderings
                for (MessageContentPostProcessing o : orderings) {
                    A.clear();
                    ordering = false;
                    if (RPG.getHashLiterals().get(o.getLiteral1()) != null) {
                        if (RPG.getHashLiterals().get(o.getLiteral2()) != null) {
                            if (matrix[this.hashLGNodes.get(o.getLiteral1()).getIndex()][this.hashLGNodes.get(o.getLiteral2()).getIndex()] == true) {
                                A = this.getActions(this.hashLGNodes.get(o.getLiteral1()).getLiteral(),
                                        this.hashLGNodes.get(o.getLiteral2()).getLiteral());
                                ordering = true;
                            }
                        }
                    }
                    //Mark the necessary ordering as verified
                    hashEdges.put(o.getLiteral1() + " -> " + o.getLiteral2(), true);
                    if (!RPG.verifyEdge(A)) {
                        if (ordering) {
                            for (LandmarkOrdering e : edges) {
                                if (e.getNode1().isSingleLiteral() && e.getNode2().isSingleLiteral()) {
                                    if (e.getNode1().getLiteral().getIndex() == RPG.getHashLiterals().get(o.getLiteral1()).getIndex()
                                            && e.getNode2().getLiteral().getIndex() == RPG.getHashLiterals().get(o.getLiteral2()).getIndex()) {
                                        auxEdges.remove(e);
                                    }
                                }
                            }
                        }
                    }
                }
            }
            edges = auxEdges;
            //Pass baton
            //If the next baton agent has already been the baton agent,
            //warn the rest of agents and finish the procedure
            comm.passBaton();
            if (comm.batonAgent()) {
                if (done) {
                    for (String ag : comm.getOtherAgents()) {
                        comm.sendMessage(ag, true, false);
                    }
                    return;
                } else {
                    for (String ag : comm.getOtherAgents()) {
                        comm.sendMessage(ag, false, false);
                    }
                }
            }
            //Non-baton agent
            if (!comm.batonAgent()) {
                boolean finish = (Boolean) comm.receiveMessage(comm.getBatonAgent(), false);
                if (finish) {
                    return;
                }
            }
        }
    }

    /**
     * Calculates the actions that generate the edge l1 -> l2.
     *
     * @param l1 Start landmark
     * @param l2 End landmark
     * @return List of actions that generate the edge l1 -> l2
     * @since 1.0
     */
    private ArrayList<LandmarkAction> getActions(LandmarkFluent l1, LandmarkFluent l2) {
        ArrayList<LandmarkAction> A = new ArrayList<>();
        for (LandmarkAction a : RPG.getActions()) {
            for (LandmarkFluent pre : a.getPreconditions()) {
                if (l1 == pre && l2.getTotalProducers().contains(a)) {
                    A.add(a);
                }
            }
        }
        return A;
    }

    /**
     * Generates the accessibility matrix.
     *
     * @since 1.0
     */
    private void computeAccessibilityMatrix() {
        int i, j, k;

        for (k = 0; k < nodes.size(); k++) {
            for (i = 0; i < nodes.size(); i++) {
                for (j = 0; j < nodes.size(); j++) {
                    if (this.matrix[i][j] != true) {
                        if (this.matrix[i][k] == true && this.matrix[k][j] == true) {
                            this.matrix[i][j] = true;
                        }
                    }
                }
            }
        }
    }

    /**
     * Gets the landmark node for a given fluent.
     *
     * @param l Fluent
     * @return Landmark node, if it is found; <code>null</code>, otherwise
     * @since 1.0
     */
    public LandmarkNode getNode(LMLiteral l) {
        if (literalNode.get(l.getIndex()) != -1) {
            return nodes.get(literalNode.get(l.getIndex()));
        } else {
            return null;
        }
    }

    /**
     * Checks if there is a reasonable ordering between the given nodes.
     *
     * @param n1 Start node
     * @param n2 End node
     * @return <code>true</code>, if there is a reasonable ordering between the
     * given nodes; <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean getReasonableOrdering(LGNode n1, LGNode n2) {
        return reasonableOrderings[n1.getIndex()][n2.getIndex()];
    }

    /**
     * Retrieves reasonable orderings of the LG.
     *
     * @return Arraylist of reasonable landmark orderings
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkOrdering> getReasonableOrderingList() {
        return this.reasonableOrderingsList;
    }

    /**
     * Retrieves reasonable orderings to the goals of the LG.
     *
     * @return Arraylist of reasonable landmark orderings to the goals
     * @since 1.0
     */
    public ArrayList<LandmarkOrdering> getReasonableGoalOrderingList() {
        return this.reasonableOrderingsGoalsList;
    }

    /**
     * Retrieves the necessary orderings to goals of the LG.
     *
     * @return Arraylist of necessary landmark orderings to goals
     * @since 1.0
     */
    public ArrayList<LandmarkOrdering> getNeccessaryGoalOrderingList() {
        ArrayList<LandmarkOrdering> res = new ArrayList<>();
        for (LandmarkOrdering o : edges) {
            if (o.getNode1().isSingleLiteral() && o.getNode2().isSingleLiteral()) {
                if (o.getNode1().getLiteral().isGoal() && o.getNode2().getLiteral().isGoal()) {
                    res.add(o);
                }
            }
        }
        return res;
    }

    /**
     * Retrieves necessary orderings of the LG.
     *
     * @return Arraylist of necessary landmark orderings
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkOrdering> getNeccessaryOrderingList() {
        return edges;
    }

    /**
     * Gets the actions that produce a LGNode.
     *
     * @param obj LGNode to analyze
     * @param literal Literal associated to the LGNode
     * @since 1.0
     */
    private void getProducers(LandmarkNode obj, String literal) {
        if (obj != null) {
            A = obj.getProducers();
        } //Participant agents, in case they don't have the LGNode
        else {
            A = new ArrayList<>();

            if (RPG.getHashLiterals().get(literal) != null) {
                //System.out.println("Participant agent " + comm.getThisAgentName() + ": LGNode not known, LMLiteral known");
                A = RPG.getHashLiterals().get(literal).getProducers();
            }
        }
    }

    /**
     * Gets nodes of the LG.
     *
     * @return Arraylist of nodes of the LG
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkNode> getNodes() {
        return nodes;
    }

    /**
     * Gets number of landmark nodes in the LG.
     *
     * @return Number of landmark nodes in the LG
     * @since 1.0
     */
    @Override
    public int numGlobalNodes() {
        return this.totalLandmarks;
    }

    /**
     * Gets current number of nodes in the LG (during LG construction).
     *
     * @return Current number of landmark nodes in the LG
     * @since 1.0
     */
    @Override
    public int numTotalNodes() {
        return globalIndex;
    }
}
