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

import java.util.ArrayList;
import java.util.Stack;

/**
 * POPInternalSearchTree class manages the internal search tree (for the
 * calculation of successor plans of a base plan) with a Depth-First Search.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
class POPInternalSearchTree {

    private final Stack<POPInternalPlan> planStack;     // Stack of internal plans
    private final POPInternalPlan basePlan;             // Base plan

    /**
     * Constructor; builds the depth search manager.
     *
     * @param initialIncrementalPlan Base plan of the search process
     * @param planComparator Comparator used to evaluate the partial order plans
     * and extract them in tha appropriate order
     * @since 1.0
     */
    public POPInternalSearchTree(POPInternalPlan initialIncrementalPlan) {
        this.planStack = new Stack<>();
        this.basePlan = initialIncrementalPlan;
        this.planStack.push(this.basePlan);
    }

    /**
     * Retrieves the next partial order plan according to its F value
     *
     * @return Next plan; <code>null</code>, if the queue is empty
     * @since 1.0
     */
    public POPInternalPlan getNextPlan() {
        return this.planStack.pop();
    }

    /**
     * Adds to the queue the new plans generated when solving a flaw
     *
     * @param successors Array of successors generated when a flaw of the parent
     * plan is solved
     * @since 1.0
     */
    public void addSuccessors(ArrayList<POPInternalPlan> successors) {
        for (POPInternalPlan s : successors) {
            this.planStack.push(s);
        }
    }

    /**
     * Checks if the stack is empty.
     * 
     * @return <code>true</code>, if the stack is empty; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    public boolean isEmpty() {
        return this.planStack.isEmpty();
    }

    /**
     * Adds a new plan to the stack.
     * 
     * @param plan Plan to add
     * @since 1.0
     */
    public void addPlan(POPInternalPlan plan) {
        this.planStack.push(plan);
    }

    /**
     * Gets a description of this search manager.
     * 
     * @return Search manager description
     * @since 1.0
     */
    @Override
    public String toString() {
        return "Plans stored: " + this.planStack.size();
    }
    
}
