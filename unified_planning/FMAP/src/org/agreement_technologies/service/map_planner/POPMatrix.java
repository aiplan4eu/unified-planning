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

/**
 * Matrix of orderings. It allows to check whether an ordering exists between
 * two steps with a cost O(1).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPMatrix implements OrderingManager {

    // Counter. Incremental values are used in the matrix with each new base 
    // plan to avoid initialize the matrix to zero every time
    private int index;
    private int size;           // Matrix size
    private int matrix[][];     // Matrix of orderings

    /**
     * Creates a new emty matrix (no orderings between steps).
     *
     * @param x Matrix size
     * @since 1.0
     */
    public POPMatrix(int x) {
        int i, j;
        this.matrix = new int[x][x];
        this.index = 1;
        this.size = 0;

        for (i = 0; i < x; i++) {
            for (j = 0; j < x; j++) {
                this.matrix[i][j] = 0;
            }
        }
    }

    /**
     * Increases the counter index with every new plan.
     * 
     * @since 1.0
     */
    @Override
    public void newPlan() {
        this.index++;
    }

    /**
     * Sets the number of steps in the matrix.
     *
     * @param s Number of plan steps
     * @since 1.0
     */
    @Override
    public void setSize(int s) {
        this.size = s;
        if (s >= this.matrix.length) {
            this.resizeMatrix(java.lang.Math.max(s, this.matrix.length * 2));
        }
    }

    /**
     * Gets the matrix size.
     *
     * @return Matrix size
     * @since 1.0
     */
    @Override
    public int getSize() {
        return this.size;
    }

    /**
     * Updates the matrix with a new plan.
     *
     * @param p New internal plan
     * @since 1.0
     */
    @Override
    public void update(POPInternalPlan p) {
        POPInternalPlan iter = p;

        this.newPlan();

        this.size = 0;

        while (this.size == 0) {
            if (this.size == 0) {
                if (iter.getStep() != null) {
                    this.setSize(iter.getStep().getIndex() + 1);
                }
            }
            iter = iter.getFather();
        }

        iter = p;

        while (iter != null) {
            if (iter.getOrdering() != null) {
                this.matrix[iter.getOrdering().getIndex1()][iter.getOrdering().getIndex2()] = this.index;
            }
            iter = iter.getFather();
        }
    }

    /**
     * Resizes the matrix.
     *
     * @param size New matrix size
     * @since 1.0
     */
    private void resizeMatrix(int size) {
        if (size > this.matrix.length) {
            int i, j;
            this.matrix = new int[size][size];
            for (i = 0; i < size; i++) {
                for (j = 0; j < size; j++) {
                    this.matrix[i][j] = 0;
                }
            }
        }
    }

    /**
     * Prepares and updates the matrix with a new plan.
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

        this.computeAccessibilityMatrix();
    }

    /**
     * Warshall algorithm to calculate the accesibility matrix from the
     * adjacency matrix.
     * 
     * @since 1.0
     */
    @Override
    public void computeAccessibilityMatrix() {
        int i, j, k;
        for (k = 2; k < this.size; k++) {
            for (i = 2; i < this.size; i++) {
                for (j = 2; j < this.size; j++) {
                    if (this.matrix[i][j] != this.index) {
                        if (this.matrix[i][k] == this.index && this.matrix[k][j] == this.index) {
                            this.matrix[i][j] = this.index;
                        }
                    }
                }
            }
        }
    }

    /**
     * Adds an ordering step1 -> step2 to the matrix
     *
     * @param step1 First step index
     * @param step2 Second step index
     * @since 1.0
     */
    @Override
    public void addOrdering(int step1, int step2) {
        this.matrix[step1][step2] = this.index;
    }

    /**
     * Checks if there is an ordering between two steps.
     *
     * @param i First step index
     * @param j Second step index
     * @return <code>true</code>, if there is an ordering between both steps;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean checkOrdering(int i, int j) {
        if (i == 0) {
            return true;
        }
        if (j == 1) {
            return true;
        }
        // If the first step of the ordering is out of range (new step), there is no ordering
        if (i > this.size) {
            return false;
        }

        return this.matrix[i][j] == this.index;
    }

    /**
     * Prints the matrix.
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
                if (this.matrix[i][j] == this.index) {
                    res += "1 ";
                } else {
                    res += "0 ";
                }
            }
            if ((i + 1) < size) {
                res += "\n[" + (i + 1) + "] ";
            }
        }
        System.out.print(res + "\n");
    }

    /**
     * Gets a matrix description.
     *
     * @return Matrix description
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
                if (this.matrix[i][j] == this.index) {
                    res += "1 ";
                } else {
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
     * Removes an ordering between two steps. This method is not supported.
     *
     * @param o1 First step
     * @param o2 Second step
     * @since 1.0
     */
    @Override
    public void removeOrdering(int o1, int o2) {
        throw new UnsupportedOperationException("Not supported yet.");
    }

}
