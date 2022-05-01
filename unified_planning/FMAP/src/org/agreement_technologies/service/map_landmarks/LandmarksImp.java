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
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_landmarks.LandmarkGraph;
import org.agreement_technologies.common.map_landmarks.LandmarkNode;
import org.agreement_technologies.common.map_landmarks.LandmarkOrdering;
import org.agreement_technologies.common.map_landmarks.Landmarks;
import org.agreement_technologies.service.tools.Graph;
import org.agreement_technologies.service.tools.Graph.Adjacent;

/**
 * LandmarksImp is the main class to calculate and work with landmarks.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class LandmarksImp implements Landmarks {

    private final ArrayList<LandmarkOrdering> orderings;    // List of orderings
    private ArrayList<LandmarkNode> nodes;                  // List of nodes
    private final int numGlobalNodes;                       // Number of global nodes
    private final int numTotalNodes;                        // Total number of nodes

    /**
     * Creates a new object to calculate landmarks.
     *
     * @param gt Grounded task
     * @param c Communication utility
     * @since 1.0
     */
    public LandmarksImp(GroundedTask gt, AgentCommunication c) {
        long time = System.currentTimeMillis();
        RPG rpg = new RPG(gt, c);
        LandmarkGraph LG = gt.getAgentNames().length > 1
                ? new MALandmarkGraph(gt, c, rpg, rpg.getGoals())
                : new SALandmarkGraph(gt, rpg, rpg.getGoals());
        numGlobalNodes = LG.numGlobalNodes();
        numTotalNodes = LG.numTotalNodes();
        orderings = new ArrayList<>();
        if (LG.getReasonableOrderingList() != null) {
            orderings.addAll(LG.getReasonableOrderingList());
        }
        if (LG.getNeccessaryOrderingList() != null) {
            orderings.addAll(LG.getNeccessaryOrderingList());
        }
        ArrayList<LandmarkNode> allNodes = LG.getNodes();
        nodes = new ArrayList<>(allNodes.size());
        for (int i = 0; i < allNodes.size(); i++) {
            assert allNodes.get(i).getIndex() == i;
            nodes.add(allNodes.get(i));
        }
    }

    /**
     * Retrieves all the orderings between landmarks in the LG.
     *
     * @param type Type of orderings to return (NECESSARY_ORDERINGS,
     * REASONABLE_ORDERINGS or ALL_ORDERINGS)
     * @param onlyGoals If true, return only orderings that affect the task
     * goals; otherwise, return all the orederings
     * @return List of orderings between landmarks
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkOrdering> getOrderings(int type, boolean onlyGoals) {
        ArrayList<LandmarkOrdering> ords = new ArrayList<>(orderings.size());
        if (onlyGoals) {
            if ((type & REASONABLE_ORDERINGS) > 0) {
                for (LandmarkOrdering o : orderings) {
                    if (o.getType() == LandmarkOrdering.REASONABLE && o.getNode1().isGoal()
                            && o.getNode2().isGoal()) {
                        ords.add(o);
                    }
                }
            }
            if ((type & NECESSARY_ORDERINGS) > 0) {
                for (LandmarkOrdering o : orderings) {
                    if (o.getType() == LandmarkOrdering.NECESSARY && o.getNode1().isGoal()
                            && o.getNode2().isGoal()) {
                        ords.add(o);
                    }
                }
            }
        } else {
            if (type == ALL_ORDERINGS) {
                ords.addAll(orderings);
            } else {
                if ((type & REASONABLE_ORDERINGS) > 0) {
                    for (LandmarkOrdering o : orderings) {
                        if (o.getType() == LandmarkOrdering.REASONABLE) {
                            ords.add(o);
                        }
                    }
                }
                if ((type & NECESSARY_ORDERINGS) > 0) {
                    for (LandmarkOrdering o : orderings) {
                        if (o.getType() == LandmarkOrdering.NECESSARY) {
                            ords.add(o);
                        }
                    }
                }
            }
        }
        return ords;
    }

    /**
     * Retrieves nodes of the LG.
     *
     * @return List of landmark nodes (single and disjunctive landmarks)
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkNode> getNodes() {
        return nodes;
    }

    /**
     * Sets the nodes of the LG.
     *
     * @param nodes List of landmark nodes (single and disjunctive landmarks)
     * @since 1.0
     */
    public void setNodes(ArrayList<LandmarkNode> nodes) {
        this.nodes = nodes;
    }

    /**
     * Removes transitive orderings between landmarks.
     *
     * @since 1.0
     */
    @Override
    public void filterTransitiveOrders() {
        Graph<LandmarkNode, LandmarkOrdering> g = new Graph<>();
        for (LandmarkOrdering o : orderings) {
            g.addEdge(o.getNode1(), o.getNode2(), o);
        }
        int numOrd = 0;
        while (numOrd < orderings.size()) {
            LandmarkOrdering o = orderings.get(numOrd);
            int n1 = g.getNodeIndex(o.getNode1()), n2 = g.getNodeIndex(o.getNode2());	// n1 -> n2
            boolean remove = false;
            for (Graph.Adjacent<LandmarkOrdering> a : g.getAdjacents(n1)) {
                if (a.dst != n2) {
                    int dst = g.minDistance(a.dst, n2);
                    if (dst != Graph.INFINITE) {
                        remove = true;		//n1 -> nx -> n2
                        break;
                    }
                }
            }
            if (remove) {
                orderings.remove(numOrd);
            } else {
                numOrd++;
            }
        }
    }

    /**
     * Removes cycles in the LG.
     *
     * @since 1.0
     */
    @Override
    public void removeCycles() {
        Graph<LandmarkNode, LandmarkOrdering> g = new Graph<>();
        for (LandmarkOrdering o : orderings) {
            g.addEdge(o.getNode1(), o.getNode2(), o);
        }
        int[] marks = new int[nodes.size()];
        int nodeOrder[] = g.sortNodesByIndegree();
        for (int i = 0; i < nodeOrder.length; i++) {
            int orig = nodes.get(nodeOrder[i]).getIndex();
            if (marks[orig] == 0) {
                removeCycles(orig, marks, g);
            }
        }
    }

    /**
     * Private recursive method to remove cycles in the LG.
     *
     * @param orig Current node
     * @param marks Array to mark the visited nodes
     * @param g Landmarks graph
     * @since 1.0
     */
    private void removeCycles(int orig, int marks[], Graph<LandmarkNode, LandmarkOrdering> g) {
        marks[orig] = 2;	// Visited in the current branch
        ArrayList<Adjacent<LandmarkOrdering>> adj = g.getAdjacents(orig);
        int i = 0;
        while (i < adj.size()) {
            int dst = adj.get(i).dst;
            if (marks[dst] == 0) {	// Not visited
                removeCycles(dst, marks, g);
                i++;
            } else if (marks[dst] == 2) {	// Return edge
                orderings.remove(adj.get(i).label);
                adj.remove(i);
            } else {
                i++;	// Visited	
            }
        }
        marks[orig] = 1;	// Visited
    }

    /**
     * Gets the total number of single and disjunctive landmarks.
     *
     * @return Number of landmarks of the LG
     * @since 1.0
     */
    @Override
    public int numGlobalNodes() {
        return numGlobalNodes;
    }

    /**
     * Returns current number of landmarks (during plan construction).
     *
     * @return Number of landmarks of the LG
     * @since 1.0
     */
    @Override
    public int numTotalNodes() {
        return numTotalNodes;
    }
}
