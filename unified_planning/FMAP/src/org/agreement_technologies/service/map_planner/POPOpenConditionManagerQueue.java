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
import java.util.Iterator;
import java.util.Comparator;
import java.util.PriorityQueue;
import org.agreement_technologies.common.map_planner.OpenCondition;

/**
 * POPOpenConditionManagerQueue class implements the open-condition manager
 * using a priority queue.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPOpenConditionManagerQueue implements POPOpenConditionManager {

    PriorityQueue<OpenCondition> queue;             // Priority queue
    ArrayList<OpenCondition> initialOpenConditions; // List of initial open conditions

    /**
     * Creates a new open-condition manager.
     * 
     * @param comp Comparator that sets the priority among open conditions
     * @since 1.0
     */
    POPOpenConditionManagerQueue(Comparator<OpenCondition> comp) {
        this.initialOpenConditions = new ArrayList<>();
        this.queue = new PriorityQueue<>(30, comp);
    }

    /**
     * Extracts the next open condition.
     *
     * @return Open condition
     * @since 1.0
     */
    @Override
    public POPOpenCondition getNextOpenCondition() {
        return (POPOpenCondition) queue.poll();
    }

    /**
     * Consults, without removing, the next open condition.
     *
     * @return Open condition
     * @since 1.0
     */
    @Override
    public POPOpenCondition checkNextOpenCondition() {
        return (POPOpenCondition) queue.peek();
    }

    /**
     * Adds the new open conditions to the successor plan.
     *
     * @param precs List of open conditions to add
     * @since 1.0
     */
    @Override
    public void addOpenConditions(ArrayList<OpenCondition> precs) {
        for (OpenCondition p : precs) {
            queue.add(p);
        }
    }

    /**
     * Cleans the open condition and restores the corresponding ones to the base
     * plan.
     *
     * @since 1.0
     */
    @Override
    public void restoreOpenConditions() {
        queue.clear();
        for (OpenCondition o : this.initialOpenConditions) {
            queue.add(o);
        }
    }

    /**
     * Cleans all the open conditions of the plan.
     *
     * @since 1.0
     */
    @Override
    public void clearOpenConditions() {
        queue.clear();
    }

    /**
     * Gets an iteraton on the open conditions.
     *
     * @return Iterator
     * @since 1.0
     */
    @Override
    public Iterator<OpenCondition> getIterator() {
        return queue.iterator();
    }

    /**
     * Returns the number of open conditions in the plan.
     *
     * @return Number of open conditions
     * @since 1.0
     */
    @Override
    public int size() {
        return queue.size();
    }

    /**
     * Gets the list of open conditions in the plan.
     *
     * @return List of open conditions
     * @since 1.0
     */
    @Override
    public ArrayList<OpenCondition> getList() {
        ArrayList<OpenCondition> precs = new ArrayList<>(queue.size());
        Iterator<OpenCondition> it = this.queue.iterator();
        while (it.hasNext()) {
            precs.add((POPOpenCondition) it.next());
        }
        return precs;
    }

    /**
     * Adds the preconditions of the initial plan to the manager.
     *
     * @param precs List of open conditions to add
     * @since 1.0
     */
    @Override
    public void addInitialOpenConditions(ArrayList<OpenCondition> precs) {
        for (OpenCondition p : precs) {
            queue.add(p);
        }
        this.initialOpenConditions = precs;
    }

    /**
     * Sorts the open conditions by safety.
     *
     * @since 1.0
     */
    @Override
    public void update() {
        ArrayList<POPOpenCondition> precs = new ArrayList<>();
        while (!this.queue.isEmpty()) {
            precs.add((POPOpenCondition) this.queue.poll());
        }
        this.queue.clear();
        for (POPOpenCondition p : precs) {
            this.queue.add(p);
        }
    }

    /**
     * Gets the list of open conditions in the plan.
     *
     * @return Array of open conditions
     * @since 1.0
     */
    @Override
    public OpenCondition[] getOpenConditions() {
        return (OpenCondition[]) this.queue.toArray();
    }

}
