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
package org.agreement_technologies.service.tools;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;

/**
 * Graph class implements a generic graph represented with adjacent lists.
 *
 * @param <N> Type for the nodes
 * @param <E> Type for the edges
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class Graph<N, E> {

    // Infinite value for computing short paths
    public static final int INFINITE = Integer.MAX_VALUE / 4;
    private final ArrayList<GraphNode<N, E>> nodes; // Adjacent lists
    private final HashMap<N, Integer> labels;       // Mapping from a node to its index
    private boolean visited[];                      // Visited nodes
    private int count;                              // Counter for iterations count

    /**
     * Adjacent class implements an adjacent to a node.
     *
     * @param <E> Type for the edges
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class Adjacent<E> {

        public int dst;     // Adjacent node index
        public E label;     // Label of the link

        /**
         * Creates a new adjacent.
         *
         * @param dst Adjacent node index
         * @param label Label of the link
         * @since 1.0
         */
        public Adjacent(int dst, E label) {
            this.dst = dst;
            this.label = label;
        }

        /**
         * Compares two adjacents by their node indexes.
         *
         * @param x Another adjacent to compare with,
         * @return <code>true</code>, if both adjacents have the same index;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @SuppressWarnings("unchecked")
        @Override
        public boolean equals(Object x) {
            return dst == ((Adjacent<E>) x).dst;
        }
    }

    /**
     * GraphNode class implements a generic node in the graph.
     *
     * @param <N> Type for the nodes
     * @param <E> Type for the edges
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    private static class GraphNode<N, E> {

        N data;                             // Node information
        ArrayList<Adjacent<E>> adjacents;   // List of adjacent nodes

        /**
         * Creates a new node.
         * 
         * @param data Node information
         * @since 1.0
         */
        public GraphNode(N data) {
            this.data = data;
            adjacents = new ArrayList<>();
        }

        /**
         * Adds a new adjacent to this node.
         * 
         * @param nextNode Adjacent node
         * @param label Edge label
         * @since 1.0
         */
        public void add(int nextNode, E label) {
            Adjacent<E> a = new Adjacent<>(nextNode, label);
            if (!adjacents.contains(a)) {
                adjacents.add(a);
            }
        }

        /**
         * Removes an adjacent of this node.
         * 
         * @param dst Adjacent node index
         * @since 1.0
         */
        public void removeAdjacent(int dst) {
            for (int i = 0; i < adjacents.size(); i++) {
                Adjacent<E> a = adjacents.get(i);
                if (a.dst == dst) {
                    adjacents.remove(i);
                    break;
                }
            }
        }
    }

    /**
     * Creates a new empty graph.
     * 
     * @since 1.0
     */
    public Graph() {
        nodes = new ArrayList<>();
        labels = new HashMap<>();
    }

    /**
     * Adds a node to this graph.
     * 
     * @param data Node information
     * @return Index of the new node
     * @since 1.0
     */
    public int addNode(N data) {
        Integer index = labels.get(data);
        GraphNode<N, E> n;
        if (index == null) {
            n = new GraphNode<>(data);
            index = nodes.size();
            nodes.add(n);
            labels.put(data, index);
        }
        return index;
    }

    /**
     * Adds a new edge to this graph.
     * 
     * @param node1 Start node
     * @param node2 End node
     * @param label Edge label
     * @since 1.0
     */
    public void addEdge(N node1, N node2, E label) {
        int n1 = addNode(node1), n2 = addNode(node2);
        nodes.get(n1).add(n2, label);
    }

    /**
     * Gets a node by its index.
     * 
     * @param index Node index
     * @return Node with that index
     * @since 1.0
     */
    public N getNode(int index) {
        return nodes.get(index).data;
    }

    /**
     * Gets the number of nodes in this graph.
     * 
     * @return Number of nodes
     * @since 1.0
     */
    public int numNodes() {
        return nodes.size();
    }

    /**
     * Gets the number of edgesin this graph.
     * 
     * @return Number of edges
     * @since 1.0
     */
    public int numEdges() {
        int n = 0;
        for (GraphNode<N, E> gn : nodes) {
            n += gn.adjacents.size();
        }
        return n;
    }

    /**
     * Gets the list of adjacent to a given node.
     * 
     * @param index Node index
     * @return List of adjacent to the node
     * @since 1.0
     */
    public ArrayList<Adjacent<E>> getAdjacents(int index) {
        return nodes.get(index).adjacents;
    }

    /**
     * Sorts the nodes by input degree.
     * 
     * @return Array of node indexes sorted by input degree
     * @since 1.0
     */
    public int[] sortNodesByIndegree() {
        int[] inDegree = new int[nodes.size()], res = new int[nodes.size()];
        for (GraphNode<N, E> n : nodes) {
            for (Adjacent<E> adj : n.adjacents) {
                inDegree[adj.dst]++;
            }
        }
        for (int i = 0; i < res.length; i++) {
            res[i] = i;
        }
        sort(inDegree, res);
        return res;
    }

    /**
     * Sorts the keys and values by the natural ordering of the keys.
     * 
     * @param key Array of keys
     * @param values Array of values
     * @since 1.0
     */
    public static void sort(int key[], int values[]) {
        for (int i = 1; i < key.length; i++) {
            int pos, elem = key[i], val = values[i];
            for (pos = i; pos > 0 && elem < key[pos - 1]; pos--) {
                key[pos] = key[pos - 1];
                values[pos] = values[pos - 1];
            }
            key[pos] = elem;
            values[pos] = val;
        }
    }

    /**
     * Computes the maximum distance (in number of edges) from two nodes.
     * 
     * @param vOrigen Source node
     * @param vDestino Destination node
     * @return Maximum distance from the source to the destination node. -1 if
     * the destination is not reachable from the source
     * @since 1.0
     */
    public int maxDistance(int vOrigen, int vDestino) {
        int distanciaMax[] = new int[nodes.size()];
        for (int i = 0; i < nodes.size(); i++) {
            distanciaMax[i] = -1;
        }
        distanciaMax[vOrigen] = 0;
        ArrayDeque<Integer> q = new ArrayDeque<>();
        q.add(vOrigen);
        while (!q.isEmpty()) {
            int vActual = q.poll();
            ArrayList<Adjacent<E>> aux = nodes.get(vActual).adjacents;
            for (int i = 0; i < aux.size(); i++) {
                int vSiguiente = aux.get(i).dst;
                if (distanciaMax[vSiguiente] <= distanciaMax[vActual]) {
                    distanciaMax[vSiguiente] = distanciaMax[vActual] + 1;
                    if (distanciaMax[vSiguiente] > nodes.size()) {
                        return INFINITE;
                    }
                    q.add(vSiguiente);
                }
            }
        }
        return distanciaMax[vDestino];
    }

    /**
     * Computes the maximum distance (in number of edges) from two nodes,
     * considering cycles in the graph.
     * 
     * @param orig Source node
     * @param dst Destination node
     * @return Maximum distance from the source to the destination node. -1 if
     * the destination is not reachable from the source
     * @since 1.0
     */
    public int maxDistanceWithCycles(int orig, int dst) {
        visited = new boolean[nodes.size()];
        count = 0;
        return maxDistanceWithCyclesRec(orig, dst);
    }

    /**
     * Recursively computes the maximum distance (in number of edges) from two 
     * nodes, considering cycles in the graph.
     * 
     * @param orig Source node
     * @param dst Destination node
     * @return Maximum distance from the source to the destination node. -1 if
     * the destination is not reachable from the source
     * @since 1.0
     */
    private int maxDistanceWithCyclesRec(int orig, int dst) {
        if (orig == dst) {
            return 0;
        }
        visited[orig] = true;
        count++;
        if (count > 10000) {
            return maxDistance(orig, dst);
        }
        int max = 0;
        for (Adjacent<E> actual : nodes.get(orig).adjacents) {
            if (!visited[actual.dst]) {
                int dist = maxDistanceWithCyclesRec(actual.dst, dst);
                if (dist != INFINITE) {
                    dist++;
                    if (dist > max) {
                        max = dist;
                    }
                }
                visited[actual.dst] = false;
            }
        }
        if (max == 0) {
            max = INFINITE;
        }
        return max;
    }

    /**
     * Checks if a given node is root, i.e. it is not an adjacent of any other
     * node.
     * 
     * @param node Node to check
     * @return <code>true</code>, if the given node is root; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    public boolean isRoot(int node) {
        for (GraphNode<N, E> n : nodes) {
            for (Adjacent<E> adj : n.adjacents) {
                if (adj.dst == node) {
                    return false;
                }
            }
        }
        return true;
    }

    /**
     * Computes the input degree of a node.
     * 
     * @param node Node to check
     * @return Input degree of the node
     * @since 1.0
     */
    public int inDegree(int node) {
        int d = 0;
        for (GraphNode<N, E> n : nodes) {
            for (Adjacent<E> adj : n.adjacents) {
                if (adj.dst == node) {
                    d++;
                }
            }
        }
        return d;
    }

    /**
     * Gets the index of a node.
     * 
     * @param node Node
     * @return Node index. -1 if the node is not found
     * @since 1.0
     */
    public int getNodeIndex(N node) {
        Integer index = labels.get(node);
        return index != null ? index : -1;
    }

    /**
     * Computest the shortest distance (in number of edges) between two nodes.
     * 
     * @param vOrig Origin node
     * @param vDst Destination node
     * @return Minimum distance from the origin to the destination node. -1 if
     * the destination node is not reachable from the origin
     * @since 1.0
     */
    public int minDistance(int vOrig, int vDst) {
        int distanceMin[] = new int[nodes.size()];
        for (int i = 0; i < nodes.size(); i++) {
            distanceMin[i] = INFINITE;
        }
        ArrayDeque<Integer> q = new ArrayDeque<>();
        q.add(vOrig);
        distanceMin[vOrig] = 0;
        while (!q.isEmpty()) {
            int v = q.poll();
            for (Adjacent<E> a : nodes.get(vOrig).adjacents) {
                int w = a.dst;
                if (distanceMin[w] == INFINITE) { // w not visited
                    distanceMin[w] = distanceMin[v] + 1;
                    q.add(w);
                }
            }
        }
        return distanceMin[vDst];
    }

    /**
     * Checks if the graph is acyclic.
     * 
     * @return <code>true</code>, if the graph is acyclic; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    public boolean isAcyclic() {
        int[] marks = new int[nodes.size()];
        for (int i = 0; i < nodes.size(); i++) {
            if (marks[i] == 0 && !isAcyclic(i, marks)) {
                return false;
            }
        }
        return true;
    }

    /**
     * Recursively checks if the graph is acyclic.
     * 
     * @param orig Current node
     * @param marks Auxiliar array to store the already visited nodes
     * @return <code>true</code>, if the graph is acyclic; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    private boolean isAcyclic(int orig, int marks[]) {
        marks[orig] = 2;	// Visited in the current branch
        for (Adjacent<E> a : nodes.get(orig).adjacents) {
            if (marks[a.dst] == 0) {
                if (!isAcyclic(a.dst, marks)) {
                    return false;
                }
            } else if (marks[a.dst] == 2) {
                return false;	// Return edge
            }
        }
        marks[orig] = 1;	// Visited
        return true;
    }

    /**
     * Removes an edge from the graph.
     * 
     * @param orig Index of the origin node
     * @param dst Index of the destination node
     * @since 1.0
     */
    public void removeEdge(int orig, int dst) {
        nodes.get(orig).removeAdjacent(dst);
    }
}
