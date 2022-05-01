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

import org.agreement_technologies.common.map_planner.POPSearchMethod;
import org.agreement_technologies.common.map_planner.IPlan;
import java.util.ArrayList;
import java.util.Hashtable;

/**
 * Manages the search tree for an A* search with two priority queues sorted by
 * different evaluation functions.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPSearchMethodTwoQueues implements POPSearchMethod {

    private static final int INITIAL_SIZE = 10000;  // Initial size of priority queues
    private IPlan[] dtgQueue;                       // First priority queue
    private IPlan[] prefQueue;                      // Second priority queue
    private Hashtable<String, Integer> dtgPlanPosition;     // Maps plan name -> position in the array "dtgQueue"
    private Hashtable<String, Integer> prefPlanPosition;    // Maps plan name -> position in the array "prefQueue"
    private boolean firstQueue;                     // Indicates if we are using the first qeueue or the second
    private int dtgSize, prefSize;                  // Number of plans in the priority queues
    private final PlanComparator dtgComparator;     // Plan comparator for the first queue
    private final PlanComparator prefComparator;    // Plan comparator for the second queue

    /**
     * Plan comparator.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    private interface PlanComparator {

        /**
         * Compares two plans.
         *
         * @param p1 First plan to compare.
         * @param p2 Second plan to compare.
         * @return A negative integer, zero, or a positive integer as the first
         * argument is less than, equal to, or greater than the second
         * @since 1.0
         */
        int compare(IPlan p1, IPlan p2);
    }

    /**
     * Plan comparator based on the hDTG heuristic.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    private class DTGComparator implements PlanComparator {

        /**
         * Compares two plans.
         *
         * @param p1 First plan to compare.
         * @param p2 Second plan to compare.
         * @return A negative integer, zero, or a positive integer as the first
         * argument is less than, equal to, or greater than the second
         * @since 1.0
         */
        @Override
        public int compare(IPlan p1, IPlan p2) {
            int f1 = (p1.getH() << 1) + p1.getG();
            int f2 = (p2.getH() << 1) + p2.getG();
            return f1 - f2;
        }
    }

    /**
     * Plan comparator based on the hLAND heuristic.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    private class PrefComparator implements PlanComparator {

        /**
         * Compares two plans.
         *
         * @param p1 First plan to compare.
         * @param p2 Second plan to compare.
         * @return A negative integer, zero, or a positive integer as the first
         * argument is less than, equal to, or greater than the second
         * @since 1.0
         */
        @Override
        public int compare(IPlan p1, IPlan p2) {
            return p1.getHLan() - p2.getHLan();
        }
    }

    /**
     * Constructor.
     *
     * @param initialIncrementalPlan Base plan of the search process
     * @since 1.0
     */
    public POPSearchMethodTwoQueues(POPIncrementalPlan initialIncrementalPlan) {
        dtgQueue = new IPlan[INITIAL_SIZE];
        prefQueue = new IPlan[INITIAL_SIZE];
        dtgPlanPosition = new Hashtable<>(INITIAL_SIZE);
        prefPlanPosition = new Hashtable<>(INITIAL_SIZE);
        firstQueue = true;
        dtgSize = prefSize = 0;
        dtgComparator = new DTGComparator();
        prefComparator = new PrefComparator();
        addToQueue(initialIncrementalPlan);
    }

    /**
     * Gets the next base plan.
     *
     * @return Next plan; <code>null</code>, if the queue is empty
     * @since 1.0
     */
    @Override
    public IPlan getNextPlan() {
        if (dtgSize == 0 && prefSize == 0) {
            return null;
        }
        if (dtgSize == 0 && firstQueue) {
            firstQueue = false;
        }
        if (prefSize == 0 && !firstQueue) {
            firstQueue = true;
        }
        IPlan min;
        if (firstQueue) {	// From the DTG queue
            min = dtgQueue[1];
        } else {
            min = prefQueue[1];
        }
        dtgSize = removePlan(min.getName(), dtgQueue, dtgSize, dtgPlanPosition, dtgComparator);
        prefSize = removePlan(min.getName(), prefQueue, prefSize, prefPlanPosition, prefComparator);
        firstQueue = !firstQueue;
        return min;
    }

    /**
     * Removes a plan from the given queues
     *
     * @param name Plan name
     * @param queue Priority queue
     * @param size Queue size
     * @param planPosition Position of the plan in the queue
     * @param comp Plan comparator
     * @return Removed plan
     * @since 1.0
     */
    private int removePlan(String name, IPlan[] queue, int size, Hashtable<String, Integer> planPosition,
            PlanComparator comp) {
        Integer k = planPosition.get(name);
        if (k == null) {
            return size;
        }
        int parent;
        IPlan plan = queue[k];
        IPlan ult = queue[size--];
        if (comp.compare(ult, plan) < 0) {
            while (k > 1 && comp.compare(ult, queue[k >> 1]) < 0) {
                parent = k >> 1;
                planPosition.put(queue[parent].getName(), k);
                queue[k] = queue[parent];
                k = parent;
            }
            queue[k] = ult;
            planPosition.put(ult.getName(), k);
        } else {
            queue[k] = ult;
            planPosition.put(ult.getName(), k);
            sink(k, queue, size, planPosition, comp);
        }
        return size;
    }

    /**
     * Retrieves the next partial order plan according to its F value.
     *
     * @param gap Position of the element to sink
     * @param queue Priority queue
     * @param size Queue size
     * @param planPosition Position of the plan in the queue
     * @param comp Plan comparator
     * @return Next plan; <code>null</code>, if the queue is empty
     * @since 1.0
     */
    private void sink(int gap, IPlan[] queue, int size,
            Hashtable<String, Integer> planPosition, PlanComparator comp) {
        IPlan aux = queue[gap];
        int child = gap << 1;
        boolean ok = false;
        while (child <= size && !ok) {
            if (child != size && comp.compare(queue[child + 1], queue[child]) < 0) {
                child++;
            }
            if (comp.compare(queue[child], aux) < 0) {
                planPosition.put(queue[child].getName(), gap);
                queue[gap] = queue[child];
                gap = child;
                child = gap << 1;
            } else {
                ok = true;
            }
        }
        queue[gap] = aux;
        planPosition.put(aux.getName(), gap);
    }

    /**
     * Gets the next plan to resume the search after finding a solution
     *
     * @return Next plan in the queue
     * @since 1.0
     */
    @Override
    public IPlan getNextPlanResume() {
        return checkNextPlan();
    }

    /**
     * Checks the following plan to be processed without extracting it.
     *
     * @return Next plan
     * @since 1.0
     */
    @Override
    public IPlan checkNextPlan() {
        if (dtgSize == 0 && prefSize == 0) {
            return null;
        }
        if (dtgSize == 0 && firstQueue) {
            firstQueue = false;
        }
        if (prefSize == 0 && !firstQueue) {
            firstQueue = true;
        }
        IPlan min;
        if (firstQueue) {	// From the DTG queue
            min = dtgQueue[1];
        } else {
            min = prefQueue[1];
        }
        return min;
    }

    /**
     * Adds to the queues the new plans generated when solving a flaw.
     *
     * @param successors Array of successors generated when a flaw of the parent
     * plan is solved
     * @since 1.0
     */
    @Override
    public void addSuccessors(ArrayList<IPlan> successors) {
        for (IPlan s : successors) {
            addToQueue(s);
        }
    }

    /**
     * Adds a new plan to the queues.
     *
     * @param plan New plan
     * @since 1.0
     */
    @Override
    public void addPlan(IPlan plan) {
        addToQueue(plan);
    }

    /**
     * Checks if the queues of plans is empty.
     *
     * @return <code>true</code>, if the queues are empty; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    @Override
    public boolean isEmpty() {
        return dtgSize > 0 || prefSize > 0;
    }

    /**
     * Gets the number of plans.
     *
     * @return Number of plans
     * @since 1.0
     */
    @Override
    public int size() {
        return dtgSize + prefSize;
    }

    /**
     * Store a solution plan. Not used.
     *
     * @param solution Solution plan
     * @since 1.0
     */
    @Override
    public void addSolution(IPlan solution) {
    }

    /**
     * Removes a plan from the queues.
     *
     * @param planName Plan name
     * @return Deleted plan
     * @since 1.0
     */
    @Override
    public IPlan removePlan(String planName) {
        IPlan plan = getPlanByName(planName);
        if (plan != null) {
            dtgSize = removePlan(planName, dtgQueue, dtgSize, dtgPlanPosition, dtgComparator);
            prefSize = removePlan(planName, prefQueue, prefSize, prefPlanPosition, prefComparator);
        }
        return plan;
    }

    /**
     * Returns the n first plans in the queues. Not used.
     *
     * @param n Number of plans to return
     * @return Array with the n first plans
     * @since 1.0
     */
    @Override
    public IPlan[] getFirstPlans(int n) {
        return null;
    }

    /**
     * Gets a plan in the queues by its name.
     *
     * @param planName Plan name
     * @return Plan with the given name
     * @since 1.0
     */
    @Override
    public IPlan getPlanByName(String planName) {
        IPlan plan;
        Integer pos = dtgPlanPosition.get(planName);
        if (pos != null) {
            plan = dtgQueue[pos];
        } else {
            pos = prefPlanPosition.get(planName);
            if (pos != null) {
                plan = prefQueue[pos];
            } else {
                return null;
            }
        }
        return plan;
    }

    /**
     * Gets the public evaluation function value for the given plan.
     *
     * @param p Plan
     * @return Evaluation function value for the plan
     * @since 1.0
     */
    @Override
    public int getPublicValue(IPlan p) {
        return p.getG() + 2 * p.getH();
    }

    /**
     * Adds a plan to the queues.
     *
     * @param x Plan to add
     * @since 1.0
     */
    private void addToQueue(IPlan x) {
        if (x.getName() == null) {
            throw new RuntimeException("Cannot add a plan without name");
        }
        dtgSize = addToQueue(x, dtgQueue, dtgSize, dtgPlanPosition, dtgComparator);
        if (x.getFather() != null && x.getFather().getHLan() > x.getHLan()) // Preferred
        {
            prefSize = addToQueue(x, prefQueue, prefSize, prefPlanPosition, prefComparator);
        }
    }

    /**
     * Adds a plan to the given queue.
     *
     * @param x Plan to add
     * @param queue Priority queue
     * @param size Number of elements in the queue
     * @param planPosition Plan position in the queue
     * @param comp Plan comparator
     * @return Added plan position
     */
    private int addToQueue(IPlan x, IPlan[] queue, int size, Hashtable<String, Integer> planPosition,
            PlanComparator comp) {
        int gap = ++size, parent;
        if (size >= queue.length) {
            if (queue == dtgQueue) {
                queue = dtgQueue = growQueue(queue);
            } else {
                queue = prefQueue = growQueue(queue);
            }
        }
        while (gap > 1 && comp.compare(x, queue[gap >> 1]) < 0) {
            parent = gap >> 1;
            planPosition.put(queue[parent].getName(), gap);
            queue[gap] = queue[parent];
            gap = parent;
        }
        queue[gap] = x;
        planPosition.put(x.getName(), gap);
        return size;
    }

    /**
     * Increases the size of a queue.
     *
     * @param queue Queue to resize
     * @return Resized queue
     */
    private IPlan[] growQueue(IPlan[] queue) {
        IPlan[] newQueue = new IPlan[2 * queue.length];
        System.arraycopy(queue, 0, newQueue, 0, queue.length);
        return newQueue;
    }

}
