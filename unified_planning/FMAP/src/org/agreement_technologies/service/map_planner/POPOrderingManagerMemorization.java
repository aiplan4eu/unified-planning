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

import org.agreement_technologies.common.map_planner.CausalLink;
import org.agreement_technologies.common.map_planner.Ordering;
import org.agreement_technologies.service.tools.CustomArrayList;

/**
 * Ordering manager with memorization.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPOrderingManagerMemorization implements OrderingManager {

    private int indexT, indexF;     // Indexes for true and false values
    private int size;               // Plan size
    private int matrix[][];         // Orderings matrix
    private CustomArrayList<CustomArrayList<Integer>> list; // Adjacency list

    /**
     * Creates a new ordering manager.
     *
     * @param x Plan size (in number of steps)
     * @since 1.0
     */
    public POPOrderingManagerMemorization(int x) {
        int i, j;

        this.matrix = new int[x][x];
        this.indexT = -1;
        this.indexF = 0;
        this.size = 0;

        list = new CustomArrayList<>(x);

        for (i = 0; i < x; i++) {
            list.insert(new CustomArrayList<Integer>(x));
            for (j = 0; j < x; j++) {
                this.matrix[i][j] = 0;
            }
        }
    }

    /**
     * Creates a new ordering manager with an initial plan size of 20.
     *
     * @since 1.0
     */
    public POPOrderingManagerMemorization() {
        this(20);
    }

    /**
     * Checks if there is a (transitive) ordering between two steps.
     *
     * @param i First step index
     * @param j Second step index
     * @return <code>true</code>, if there is a (transitive) ordering between
     * both steps; <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean checkOrdering(int i, int j) {
        //Base cases: step 0 is ordered before all the steps, and step 1 is always ordered after the rest of steps
        if (i == 0 || j == 1) {
            return true;
        }
        if (i == 1 || j == 0) {
            return false;
        }
        //If step i is out of range (the step is new), there is not an ordering
        if (i > this.size) {
            return false;
        }
        //If the ordering (or absence of ordering) is stored in the matrix, return the result
        if (matrix[i][j] == this.indexT) {
            return true;
        }
        if (matrix[i][j] == this.indexF) {
            return false;
        }

        return findAntecessors(j, i);
    }

    /**
     * Checks if one given step is ordered before another one.
     * 
     * @param node First step
     * @param target Last step
     * @return <code>true</code>, if the node is ordered before the target;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    private boolean findAntecessors(int node, int target) {
        int aux;

        CustomArrayList<Integer> nodes = new CustomArrayList<>();
        CustomArrayList<Integer> memorization = new CustomArrayList<>();

        nodes.add(node);
        memorization.add(node);

        while (!nodes.isEmpty()) {
            aux = nodes.retrieve();
            //Base case
            if (matrix[target][aux] == this.indexT) {
                this.memorize(memorization, node);
                return true;
            }
            //Check if the target node is adjacent to aux
            if (this.list.get(aux).contains(target)) {
                this.memorize(memorization, node);
                return true;
            }
            //Explore the nodes adjacent to aux
            nodes.append(this.list.get(aux));
            memorization.append(this.list.get(aux));
        }
        this.memorize(memorization, node);
        return false;
    }

    /**
     * Memorizes a set of orderings.
     * 
     * @param mem List of antecessors
     * @param node Target node
     * @since 1.0
     */
    private void memorize(CustomArrayList<Integer> mem, int node) {
        int i, j;

        for (i = 0; i < this.size; i++) {
            for (j = 0; j < mem.size(); j++) {
                if (matrix[node][i] == this.indexT) {
                    matrix[mem.get(j)][i] = this.indexT;
                }
            }
        }
    }

    /**
     * Updates the manager with a new plan.
     * 
     * @param p Plan
     * @since 1.0
     */
    @Override
    public void update(POPInternalPlan p) {
        POPInternalPlan iter = p;

        this.indexF += 2;
        this.indexT += 2;

        this.size = 0;

        while (this.size == 0) {
            if (this.size == 0) {
                if (iter.getStep() != null) {
                    this.resize(iter.getStep().getIndex() + 1);
                    this.size = iter.getStep().getIndex() + 1;
                }
            }
            iter = iter.getFather();
        }

        iter = p;

        while (iter != null) {
            if (iter.getOrdering() != null) {
                this.list.get(iter.getOrdering().getIndex2()).addNotRepeated(iter.getOrdering().getIndex1());
                this.matrix[iter.getOrdering().getIndex1()][iter.getOrdering().getIndex2()] = this.indexT;
                this.matrix[iter.getOrdering().getIndex2()][iter.getOrdering().getIndex1()] = this.indexF;
            }
            if (iter.getCausalLink() != null) {
                this.list.get(iter.getCausalLink().getIndex2()).addNotRepeated(iter.getCausalLink().getIndex1());
                this.matrix[iter.getCausalLink().getIndex1()][iter.getCausalLink().getIndex2()] = this.indexT;
                this.matrix[iter.getCausalLink().getIndex2()][iter.getCausalLink().getIndex1()] = this.indexF;
            }
            iter = iter.getFather();
        }
    }

    /**
     * Prepares the manager to store a new plan's orderings.
     * 
     * @since 1.0
     */
    @Override
    public void newPlan() {
        this.indexF += 2;
        this.indexT += 2;
        for (int i = 0; i < this.list.size(); i++) {
            this.list.get(i).clear();
        }
    }

    /**
     * Sets the number of steps in the current plan.
     * 
     * @param size Number of steps
     * @since 1.0
     */
    @Override
    public void setSize(int size) {
        if (this.size < size) {
            this.size = size;
            this.resize(size);
        }
    }

    /**
     * Gets the number of steps in the current plan.
     * 
     * @return Number of steps
     * @since 1.0
     */
    @Override
    public int getSize() {
        return this.size;
    }

    /**
     * Resizes the matrix and the array.
     * 
     * @param s New size 
     * @since 1.0
     */
    public void resize(int s) {
        if (s > this.matrix.length) {
            int i, j, newSize;

            newSize = s + (s >> 1);
            for (i = size; i < newSize; i++) {
                this.list.add(new CustomArrayList<Integer>(newSize));
            }
            this.matrix = new int[newSize][newSize];
            for (i = 0; i < newSize; i++) {
                for (j = 0; j < newSize; j++) {
                    this.matrix[i][j] = 0;
                }
            }
        }
    }

    /**
     * Prints the matrix data.
     * 
     * @since 1.0
     */
    public void printMatrix() {
        int i, j;
        String res;

        res = "[0]\n";
        res += "[1]\n";
        res += "[2] ";

        for (i = 2; i < this.size; i++) {
            for (j = 2; j < this.size; j++) {
                if (this.matrix[i][j] == this.indexT) {
                    res += "1 ";
                } else if (this.matrix[i][j] == this.indexF) {
                    res += "0 ";
                } else {
                    res += "8 ";
                }
            }
            if ((i + 1) < size) {
                res += "\n[" + (i + 1) + "] ";
            }
        }
        System.out.print(res + "\n");
    }

    /**
     * Gets a description of the ordering matrix.
     * 
     * @return Description of the ordering matrix
     * @since 1.0
     */
    @Override
    public String toString() {
        int i, j;
        String res;

        res = "[0]\n";
        res += "[1]\n";
        res += "[2] ";

        for (i = 2; i < this.size; i++) {
            for (j = 2; j < this.size; j++) {
                if (this.matrix[i][j] == this.indexT) {
                    res += "1 ";
                } else if (this.matrix[i][j] == this.indexF) {
                    res += "0 ";
                }
            }
            if ((i + 1) < size) {
                res += "\n[" + (i + 1) + "] ";
            }
        }

        return res;
    }
    
    /**
     * Adds a new ordering between two steps.
     * 
     * @param o1 First step
     * @param o2 Second step
     * @since 1.0
     */
    @Override
    public void addOrdering(int o1, int o2) {
        this.list.get(o2).addNotRepeated(o1);
        this.matrix[o1][o2] = this.indexT;
        this.matrix[o2][o1] = this.indexF;
    }

    /**
     * Computes the accessibility matrix. Not used.
     * 
     * @since 1.0
     */
    @Override
    public void computeAccessibilityMatrix() {
    }

    /**
     * Removes an ordering between two steps. Not used.
     * 
     * @param o1 First step index
     * @param o2 Second step index
     * @since 1.0
     */
    @Override
    public void removeOrdering(int o1, int o2) {
        throw new UnsupportedOperationException("Not supported yet.");
    }

    /**
     * Prepares and updates the manager with a new plan.
     * 
     * @param plan Plan
     * @since 1.0
     */
    @Override
    public void rebuild(POPInternalPlan plan) {
        this.newPlan();
        this.setSize(plan.numSteps());

        // Store the plan orderings in the matrix
        if (!plan.getTotalOrderings().isEmpty()) {
            for (Ordering o : plan.getTotalOrderings()) {
                this.addOrdering(o.getIndex1(), o.getIndex2());
            }
        }
        if (!plan.getTotalCausalLinks().isEmpty()) {
            for (CausalLink l : plan.getTotalCausalLinks()) {
                this.addOrdering(l.getIndex1(), l.getIndex2());
            }
        }
    }

}
