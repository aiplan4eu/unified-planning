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

import org.agreement_technologies.common.map_landmarks.LandmarkAction;
import org.agreement_technologies.common.map_landmarks.LandmarkFluent;
import org.agreement_technologies.common.map_landmarks.LandmarkNode;
import org.agreement_technologies.common.map_landmarks.LandmarkSet;

/**
 * LGNode class implements a node in the landmarks graph (LG).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class LGNode implements LandmarkNode {

    private final LandmarkFluent literal;   // Fluent, if this node contains a single fluent
    private final LandmarkSet disjunction;  // Disjunction of fluents, if there is more than one fluent
    private final boolean type;             // Node type (SINGLE_LITERAL or DISJUNCTION)
    private int index;                      // Index of this node
    private ArrayList<String> agents;       // Agents that share the landmark node
    private ArrayList<Integer> antecessors; // Nodes preceding directly this one in the LG
    private int globalId;                   // Global identifier for this node

    /**
     * Constructs a new node which consists of a disjunction of fluents.
     *
     * @param u Disjunction of fluents
     * @since 1.0
     */
    public LGNode(LandmarkSet u) {
        literal = null;
        disjunction = u;
        type = DISJUNCTION;
        antecessors = new ArrayList<>();
        globalId = -1;
    }

    /**
     * Constructs a new node which consists of a single fluents.
     *
     * @param lit Fluent
     * @since 1.0
     */
    public LGNode(LandmarkFluent lit) {
        literal = lit;
        disjunction = null;
        type = SINGLE_LITERAL;
        antecessors = new ArrayList<>();
        globalId = -1;
    }

    /**
     * Sets a unique global (multi-agent) identifier for the landmark node.
     *
     * @param globalIndex Global identifier
     * @return Next global identifier
     * @since 1.0
     */
    @Override
    public int setGlobalId(int globalIndex) {
        globalId = globalIndex;
        return globalIndex + 1;
    }

    /**
     * Gets the unique global (multi-agent) identifier of the landmark node.
     *
     * @return Global identifier
     * @since 1.0
     */
    @Override
    public int getGlobalId() {
        return globalId;
    }

    /**
     * Establishes predecessor landmark nodes in the LG.
     *
     * @param ant Local indexes of landmark nodes that precede this landmark
     * node
     * @since 1.0
     */
    @Override
    public void setAntecessors(ArrayList<Integer> ant) {
        this.antecessors = ant;
    }

    /**
     * Returns the predecessor landmark nodes in the LG.
     *
     * @return List of predecessor nodes
     * @since 1.0
     */
    public ArrayList<Integer> getAntecessors() {
        return this.antecessors;
    }

    /**
     * Gets list of actions that produce the literal or literals of the landmark
     * node as effects.
     *
     * @return Arraylist of producer landmark actions
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkAction> getProducers() {
        if (type == SINGLE_LITERAL) {
            return literal.getProducers();
        }
        ArrayList<LandmarkAction> a = new ArrayList<>();
        for (LandmarkFluent l : disjunction.getElements()) {
            for (LandmarkAction p : l.getProducers()) {
                if (!a.contains(p)) {
                    a.add(p);
                }
            }
        }

        return a;
    }

    /**
     * Gets producer actions of the fluents in this node, even if they come
     * after the fluents in the RPG.
     *
     * @return Arraylist of producer actions
     * @since 1.0
     */
    public ArrayList<LandmarkAction> getTotalProducers() {
        if (type == SINGLE_LITERAL) {
            return literal.getTotalProducers();
        }
        ArrayList<LandmarkAction> a = new ArrayList<>();
        for (LandmarkFluent l : disjunction.getElements()) {
            for (LandmarkAction p : l.getTotalProducers()) {
                if (!a.contains(p)) {
                    a.add(p);
                }
            }
        }

        return a;
    }

    /**
     * Gets agents that share the landmark node.
     *
     * @return Arraylist of agent identifiers
     * @since 1.0
     */
    @Override
    public ArrayList<String> getAgents() {
        if (type == SINGLE_LITERAL) {
            return literal.getAgents();
        }
        return agents;
    }

    /**
     * Assigns list of agents that share the landmark node.
     *
     * @param ag List of agent names
     * @since 1.0
     */
    @Override
    public void setAgents(ArrayList<String> ag) {
        this.agents = ag;
    }

    /**
     * Checks if the landmark node is single or disjunctive.
     *
     * @return SINGLE_LITERAL if the landmark is single, DISJUNCTION if the
     * landmark is disjunctive
     * @since 1.0
     */
    @Override
    public boolean isSingleLiteral() {
        return type;
    }

    /**
     * Gets the literal associated to the single landmark node.
     *
     * @return Literal of the node, <code>null</code> if the landmark is
     * DISJUNCTION
     * @since 1.0
     */
    @Override
    public LandmarkFluent getLiteral() {
        return literal;
    }

    /**
     * Gets local index of the landmark node.
     *
     * @return Landmark index
     * @since 1.0
     */
    @Override
    public int getIndex() {
        return index;
    }

    /**
     * Establishes local index of the landmark node.
     *
     * @param index Landmark index
     * @since 1.0
     */
    @Override
    public void setIndex(int index) {
        this.index = index;
    }

    /**
     * Gets landmark node metadata.
     *
     * @return String of landmark node data
     * @since 1.0
     */
    @Override
    public String identify() {
        if (type == SINGLE_LITERAL) {
            return literal.toString();
        }
        return this.disjunction.identify();
    }

    /**
     * Gets a description of this node.
     *
     * @return Description of this node
     * @since 1.0
     */
    @Override
    public String toString() {
        if (type == SINGLE_LITERAL) {
            if (literal != null) {
                if (this.isGoal()) {
                    return "Global[" + this.getGlobalId() + "]Local[" + this.index + "] " + literal.toString() + " [Goal]";
                } else if (this.literal.getLevel() == 0) {
                    return "Global[" + this.getGlobalId() + "]Local[" + this.index + "] " + literal.toString() + " [Initial state]";
                } else {
                    return "Global[" + this.getGlobalId() + "]Local[" + this.index + "] " + literal.toString();
                }
            } else {
                return "[" + this.index + "] " + literal.toString();
            }
        } else {
            String res = "[" + this.index + "] " + "{";

            for (LandmarkFluent l : disjunction.getElements()) {
                res += l.toString() + ", ";
            }

            return res + "}";
        }
    }

    /**
     * Returns the disjunction of a disjunctive landmark node.
     *
     * @return Disjunction of the landmark node, <code>null</code> if
     * SINGLE_LITERAL
     * @since 1.0
     */
    @Override
    public LandmarkSet getDisjunction() {
        if (type == LGNode.SINGLE_LITERAL) {
            return null;
        } else {
            return disjunction;
        }
    }

    /**
     * Gets the list of literals associated to the disjunctive landmark node.
     *
     * @return List of literals, null if the landmark is SINGLE_LITERAL
     * @since 1.0
     */
    @Override
    public LandmarkFluent[] getLiterals() {
        LandmarkFluent[] f;
        if (type == LGNode.SINGLE_LITERAL) {
            f = new LandmarkFluent[1];
            f[0] = this.literal;
        } else {
            f = new LandmarkFluent[disjunction.getElements().size()];
            for (int i = 0; i < disjunction.getElements().size(); i++) {
                f[i] = disjunction.getElements().get(i);
            }
        }

        return f;
    }

    /**
     * Checks if the landmark node is a goal.
     *
     * @return <code>true</code>, if the landmark is a goal; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    @Override
    public boolean isGoal() {
        return type == SINGLE_LITERAL && literal.isGoal();
    }

    /**
     * Checks if two nodes have the same index.
     *
     * @param x Another node to compare with this one
     * @return <code>true</code>, if both nodes have the same index;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean equals(Object x) {
        return index == ((LandmarkNode) x).getIndex();
    }

    /**
     * Gets a hash code for this node.
     * 
     * @return Hash code
     * @since 1.0
     */
    @Override
    public int hashCode() {
        return index;
    }
    
}
