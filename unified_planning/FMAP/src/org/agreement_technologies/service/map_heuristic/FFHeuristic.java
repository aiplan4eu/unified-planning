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
package org.agreement_technologies.service.map_heuristic;

import java.util.ArrayList;
import java.util.BitSet;
import java.util.HashMap;
import java.util.PriorityQueue;
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_grounding.Action;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedEff;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.GroundedVar;
import org.agreement_technologies.common.map_heuristic.HPlan;
import org.agreement_technologies.common.map_heuristic.Heuristic;
import org.agreement_technologies.common.map_planner.PlannerFactory;

/**
 * FF heuristic function evaluator. This heuristic in only implemented for
 * centralized problems.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class FFHeuristic implements Heuristic {

    private static final int PENALTY = 1000;                // Penalty for unreachable goals
    protected GroundedTask groundedTask;                    // Grounded task
    protected AgentCommunication comm;                      // Communication utility
    protected ArrayList<GroundedCond> goals, pgoals;        // Task goals (public and private)
    protected HashMap<String, ArrayList<Action>> productors;    // Productor actions
    protected HashMap<String, ArrayList<Action>> requirers;     // Requirer actions
    protected PlannerFactory pf;                            // Planner factory
    private int[] totalOrder;   // Indexes of the plan steps sorted in a topological order

    /**
     * Constructs a new FF heuristic function evaluator.
     *
     * @param comm Communication utility
     * @param gTask Grounded task
     * @param pf Planner factory
     * @since 1.0
     */
    public FFHeuristic(AgentCommunication comm, GroundedTask gTask, PlannerFactory pf) {
        this.pf = pf;
        this.groundedTask = gTask;
        this.comm = comm;
        this.goals = new ArrayList<>();
        this.pgoals = groundedTask.getPreferences();
        ArrayList<GoalCondition> gc = HeuristicToolkit.computeTaskGoals(comm, gTask);
        for (GoalCondition g : gc) {
            GroundedVar var = null;
            for (GroundedVar v : gTask.getVars()) {
                if (v.toString().equals(g.varName)) {
                    var = v;
                    break;
                }
            }
            if (var != null) {
                goals.add(gTask.createGroundedCondition(GroundedCond.EQUAL, var, g.value));
            }
        }
        productors = new HashMap<>();
        requirers = new HashMap<>();
        for (Action a : gTask.getActions()) {
            for (GroundedEff e : a.getEffs()) {
                String desc = e.getVar().toString() + "=" + e.getValue();
                ArrayList<Action> list = productors.get(desc);
                if (list == null) {
                    list = new ArrayList<>();
                    productors.put(desc, list);
                }
                list.add(a);
            }
            for (GroundedCond c : a.getPrecs()) {
                String desc = c.getVar().toString() + "=" + c.getValue();
                ArrayList<Action> list = requirers.get(desc);
                if (list == null) {
                    list = new ArrayList<>();
                    requirers.put(desc, list);
                }
                list.add(a);
            }
        }
    }

    /**
     * Heuristic evaluation of a plan. The resulting value is stored inside the
     * plan (see setH method in Plan interface).
     *
     * @param p Plan to evaluate
     * @param threadIndex Thread index, for multi-threading purposes
     * @since 1.0
     */
    @Override
    public void evaluatePlan(HPlan p, int threadIndex) {
        if (p.isSolution() || comm.numAgents() > 1) {
            p.setH(0, 0);
            for (int i = 0; i < pgoals.size(); i++) {
                p.setHPriv(0, i);
            }
            return;
        }
        totalOrder = p.linearization();
        HashMap<String, ArrayList<String>> varValues = p.computeMultiState(totalOrder, pf);
        RPG rpg = new RPG(varValues, goals, pgoals, requirers);
        p.setH(solveGoals(rpg, goals), 0);
        ArrayList<GroundedCond> privateGoal = new ArrayList<>(1);
        for (int i = 0; i < pgoals.size(); i++) {
            privateGoal.add(pgoals.get(i));
            p.setHPriv(solveGoals(rpg, privateGoal), i);
            privateGoal.clear();
        }
    }

    /**
     * Returns the cost of solving a given set of (sub)goals.
     *
     * @param rpg Relaxed planning graph
     * @param goals Set of (sub)goals to solve
     * @return Estimated cost
     * @since 1.0
     */
    private int solveGoals(RPG rpg, ArrayList<GroundedCond> goals) {
        int h = 0;
        PriorityQueue<RPG.VarValue> openConditions = new PriorityQueue<>();
        for (GroundedCond g : goals) {
            RPG.VarValue vg = rpg.getVarValue(g);
            if (vg == null) {
                h = PENALTY;
                break;
            }
            if (vg.level > 0) {
                openConditions.add(vg);
            }
        }
        Action bestAction;
        int bestCost = 0;
        if (h == 0) {
            while (!openConditions.isEmpty()) {
                RPG.VarValue v = openConditions.poll();
                bestAction = null;
                ArrayList<Action> prod = productors.get(v.getId());
                for (Action a : prod) {
                    if (rpg.getLevel(a) == v.level - 1) {
                        if (bestAction == null) {
                            bestAction = a;
                            bestCost = rpg.getDifficulty(a);
                        } else {
                            int cost = rpg.getDifficulty(a);
                            if (cost < bestCost) {
                                bestAction = a;
                                bestCost = cost;
                            }
                        }
                    }
                }
                h++;
                for (GroundedCond prec : bestAction.getPrecs()) {
                    RPG.VarValue vp = rpg.getVarValue(prec);
                    if (vp.level > 0 && !openConditions.contains(vp)) {
                        openConditions.add(vp);
                    }
                }
            }
        }
        return h;
    }

    /**
     * Synchronization step after the distributed heuristic evaluation.
     *
     * @since 1.0
     */
    @Override
    public void waitEndEvaluation() {
    }

    /**
     * Begining of the heuristic evaluation stage.
     *
     * @param basePlan Base plan, whose successors will be evaluated
     * @since 1.0
     */
    @Override
    public void startEvaluation(HPlan basePlan) {
    }

    /**
     * Gets information about a given topic.
     *
     * @param infoFlag Topic to get information about. For this heuristic, no
     * topics are defined
     * @return <code>null</code>, as no information is available to retrieve
     * @since 1.0
     */
    @Override
    public Object getInformation(int infoFlag) {
        return null;
    }

    /**
     * Checks if the current heuristic evaluator supports multi-threading.
     *
     * @return <code>true</code>, if multi-therading evaluation is available.
     * <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean supportsMultiThreading() {
        return false;
    }

    /**
     * Heuristically evaluates the cost of reaching the agent's private goals.
     *
     * @param p Plan to evaluate
     * @param threadIndex Thread index, for multi-threading purposes
     * @since 1.0
     */
    @Override
    public void evaluatePlanPrivacy(HPlan p, int threadIndex) {
        if (p.isSolution() || comm.numAgents() > 1 || pgoals.isEmpty()) {
            for (int i = 0; i < pgoals.size(); i++) {
                p.setHPriv(0, i);
            }
            return;
        }
        totalOrder = p.linearization();
        HashMap<String, ArrayList<String>> varValues = p.computeMultiState(totalOrder, pf);
        RPG rpg = new RPG(varValues, goals, pgoals, requirers);
        ArrayList<GroundedCond> privateGoal = new ArrayList<>(1);
        for (int i = 0; i < pgoals.size(); i++) {
            privateGoal.add(pgoals.get(i));
            p.setHPriv(solveGoals(rpg, privateGoal), i);
            privateGoal.clear();
        }
    }

    /**
     * Checks if the current heuristic evaluator requieres an additional stage
     * for landmarks evaluation.
     *
     * @return <code>true</code>, if a landmarks evaluation stage is required.
     * <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean requiresHLandStage() {
        return false;
    }

    /**
     * Multi-heuristic evaluation of a plan, also evaluates the remaining
     * landmarks to achieve. The resulting value is stored inside the plan (see
     * setH method in Plan interface).
     *
     * @param p Plan to evaluate
     * @param threadIndex Thread index, for multi-threading purposes
     * @param achievedLandmarks List of already achieved landmarks
     * @since 1.0
     */
    @Override
    public void evaluatePlan(HPlan p, int threadIndex, ArrayList<Integer> achievedLandmarks) {
    }

    /**
     * Returns the total number of global (public) landmarks.
     *
     * @return Total number of global (public) landmarks
     * @since 1.0
     */
    @Override
    public int numGlobalLandmarks() {
        return 0;
    }

    /**
     * Returns the new landmarks achieved in this plan.
     *
     * @param plan Plan to check
     * @param achievedLandmarks Already achieved landmarks
     * @return List of indexes of the new achieved landmarks
     * @since 1.0
     */
    @Override
    public ArrayList<Integer> checkNewLandmarks(HPlan plan,
            BitSet achievedLandmarks) {
        return null;
    }

}
