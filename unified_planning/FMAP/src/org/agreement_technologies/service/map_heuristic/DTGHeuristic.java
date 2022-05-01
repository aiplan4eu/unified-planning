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

import java.io.Serializable;
import java.util.ArrayList;
import java.util.BitSet;
import java.util.HashMap;
import java.util.PriorityQueue;
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_communication.Message;
import org.agreement_technologies.common.map_communication.MessageFilter;
import org.agreement_technologies.common.map_dtg.DTG;
import org.agreement_technologies.common.map_dtg.DTGSet;
import org.agreement_technologies.common.map_dtg.DTGTransition;
import org.agreement_technologies.common.map_grounding.Action;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedEff;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.GroundedVar;
import org.agreement_technologies.common.map_heuristic.HPlan;
import org.agreement_technologies.common.map_heuristic.Heuristic;
import org.agreement_technologies.common.map_planner.PlannerFactory;
import org.agreement_technologies.service.map_dtg.DTGSetImp;

/**
 * DTG (Domain Transition Graph) heuristic function evaluator.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class DTGHeuristic implements Heuristic {

    private static final int PENALTY = 1000;        // Penalty for unreachables values
    protected GroundedTask groundedTask;            // Grounded task
    protected AgentCommunication comm;              // Communication utility
    protected ArrayList<Goal> goals, pgoals;        // Task goals (public and private)
    protected HashMap<String, ArrayList<Action>> productors;    // Productor actions
    protected DTGSet dtgs;					// DTGs
    protected PlannerFactory pf;                                // Planner factory

    private HPlan basePlan;		// Base plan (its successors will be evaluated)
    private HPlan currentPlan;		// Plan being evaluated
    private int ready;                  // Counter of ready agents. When all agents are ready, the evaluation ends
    private int requestId;              // Identifier for requests of information
    private int[] totalOrderBase;       // Indexes of the steps in the base plan sorted in a topological order

    /**
     * Constructs a DTG heuristic evaluator.
     *
     * @param comm Communication utility
     * @param gTask Grounded task
     * @param pf Planner factory
     * @since 1.0
     */
    public DTGHeuristic(AgentCommunication comm, GroundedTask gTask, PlannerFactory pf) {
        this.pf = pf;
        this.groundedTask = gTask;
        this.comm = comm;
        dtgs = new DTGSetImp(gTask);
        dtgs.distributeDTGs(comm, gTask);
        this.goals = new ArrayList<>();
        this.pgoals = new ArrayList<>();
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
                Goal ng = new Goal(gTask.createGroundedCondition(GroundedCond.EQUAL, var, g.value), 0);
                goals.add(ng);
            }
        }
        for (GroundedCond g : gTask.getPreferences()) {
            pgoals.add(new Goal(g, 0));
        }
        productors = new HashMap<>();
        for (Action a : gTask.getActions()) {
            for (GroundedEff e : a.getEffs()) {
                String desc = e.getVar().toString() + "," + e.getValue();
                ArrayList<Action> list = productors.get(desc);
                if (list == null) {
                    list = new ArrayList<>();
                    productors.put(desc, list);
                }
                list.add(a);
            }
        }
        requestId = 0;
    }

    /**
     * Begining of the heuristic evaluation stage.
     *
     * @param basePlan Base plan, whose successors will be evaluated
     * @since 1.0
     */
    @Override
    public void startEvaluation(HPlan basePlan) {
        this.basePlan = basePlan;
        this.ready = 0;
        this.totalOrderBase = null;
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
        if (p.isSolution()) {
            return;
        }
        this.currentPlan = p;
        if (comm.numAgents() == 1) {
            evaluateMonoagentPlan();
        } else {
            evaluateMultiagentPlan();
        }
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
        if (p.isSolution() || pgoals.isEmpty()) {
            return;
        }
        this.currentPlan = p;
        if (comm.numAgents() == 1) {
            evaluateMonoagentPlanPrivacy(null, null);
        } else {
            evaluateMultiagentPlanPrivacy(null);
        }
    }

    /**
     * Evaluation of a plan in a centralized environment.
     *
     * @since 1.0
     */
    private void evaluateMonoagentPlan() {
        int h = 0;
        HashMap<String, String> state;
        HashMap<String, ArrayList<String>> newValues = new HashMap<>();
        int totalOrder[] = currentPlan.linearization();
        state = currentPlan.computeState(totalOrder, pf);
        PriorityQueue<Goal> openGoals = new PriorityQueue<>();
        for (Goal g : goals) {		// Global goals
            String v = g.varName, end = g.varValue;
            if (!holdsMono(v, end, state, newValues)) {
                String init = selectInitialValueMono(v, end, dtgs.getDTG(v), state, newValues);
                g.distance = pathCostMono(v, init, end, state, newValues);
                if (g.distance >= INFINITE) {
                    h = INFINITE;
                    break;
                }
                openGoals.add(g);
            }
        }
        while (!openGoals.isEmpty() && h < INFINITE) {
            Goal g = openGoals.poll();
            h += solveConditionMono(g, openGoals, state, newValues);
        }
        this.currentPlan.setH(h, 0);
        evaluateMonoagentPlanPrivacy(state, newValues);
    }

    /**
     * Heuristically evaluates the cost of reaching the agent's private goals in
     * a centralized environment.
     *
     * @param state Frontier state
     * @param newValues List of new values achieved in the plan for each
     * variable
     * @since 1.0
     */
    private void evaluateMonoagentPlanPrivacy(HashMap<String, String> state,
            HashMap<String, ArrayList<String>> newValues) {
        if (state == null) {
            int totalOrder[] = currentPlan.linearization();
            state = currentPlan.computeState(totalOrder, pf);
            newValues = new HashMap<>();
        }
        PriorityQueue<Goal> openGoals = new PriorityQueue<>();
        for (int i = 0; i < pgoals.size(); i++) {	// Preferences
            int hp = 0;
            Goal g = pgoals.get(i);
            String v = g.varName, end = g.varValue;
            if (!holdsMono(v, end, state, newValues)) {
                String init = selectInitialValueMono(v, end, dtgs.getDTG(v), state, newValues);
                int dst = pathCostMono(v, init, end, state, newValues);
                if (dst >= INFINITE) {
                    hp = INFINITE;
                } else {
                    openGoals.add(new Goal(v, end, dst));
                }
            }
            while (!openGoals.isEmpty() && hp < INFINITE) {
                g = openGoals.poll();
                hp += solveConditionMono(g, openGoals, state, newValues);
            }
            currentPlan.setHPriv(hp, i);
        }
    }

    /**
     * In a centralized environment, this method selects the most appropriate
     * initial value for a transition.
     *
     * @param varName Name of the variable
     * @param endValue Desired end value
     * @param dtg Domain Transition Graph
     * @param state Frontier state
     * @param newValues List of new values achieved in the plan for each
     * variable
     * @return Inital value for the variable
     * @since 1.0
     */
    private static String selectInitialValueMono(String varName, String endValue, DTG dtg,
            HashMap<String, String> state, HashMap<String, ArrayList<String>> newValues) {
        String bestValue = state.get(varName);
        int bestCost = dtg.pathCost(bestValue, endValue, state, newValues, 0);
        ArrayList<String> valueList = newValues.get(varName);
        if (valueList != null) {
            for (int i = 0; i < valueList.size(); i++) {
                String value = valueList.get(i);
                int cost = dtg.pathCost(value, endValue, state, newValues, 0);
                if (cost != -1 && cost < bestCost) {
                    bestCost = cost;
                    bestValue = value;
                }
            }
        }
        return bestValue;
    }

    /**
     * In a centralized environment, this method calculates the cost of solving
     * a given condition.
     *
     * @param goal Goal to be evaluated
     * @param openGoals	List of open goals
     * @param state Frontier state
     * @param newValues List of new values achieved in the plan for each
     * variable
     * @return Estimated goal cost
     * @since 1.0
     */
    private int solveConditionMono(Goal goal, PriorityQueue<Goal> openGoals,
            HashMap<String, String> state, HashMap<String, ArrayList<String>> newValues) {
        int h = 0;
        String varName = goal.varName, varValue = goal.varValue;
        if (holdsMono(varName, varValue, state, newValues)) {
            return h;
        }
        DTG dtg = dtgs.getDTG(varName);
        String initValue = selectInitialValueMono(varName, varValue, dtg, state, newValues);
        String[] path = dtg.getPath(initValue, varValue, state, newValues, 0);
        if (path == null) {
            return INFINITE;
        }
        String prevValue = path[0], nextValue;
        for (int i = 1; i < path.length; i++) {
            nextValue = path[i];
            Action a = selectProductorMono(varName, prevValue, nextValue, state, newValues);
            if (a == null) {
                h = INFINITE;
                break;
            }
            h++;
            updateValuesAndGoalsMono(a, openGoals, state, newValues);
            prevValue = nextValue;
        }
        return h;
    }

    /**
     * In a centralized environment, selects the best productor action for a
     * given value transition.
     *
     * @param varName Name of the variable
     * @param startValue Initial value
     * @param endValue End value
     * @param state Frontier state
     * @param newValues List of new values achieved in the plan for each
     * variable
     * @return Productor action
     * @since 1.0
     */
    private Action selectProductorMono(String varName, String startValue, String endValue,
            HashMap<String, String> state, HashMap<String, ArrayList<String>> newValues) {
        ArrayList<Action> productors = this.productors.get(varName + "," + endValue);
        if (productors == null || productors.isEmpty()) {
            return null;
        }
        Action bestAction = null;
        int costBest = INFINITE;
        for (int i = 0; i < productors.size(); i++) {
            if (hasPrecondition(productors.get(i), varName, startValue)) {
                int cost = computeCostMono(productors.get(i), state, newValues);
                if (cost < costBest) {
                    costBest = cost;
                    bestAction = productors.get(i);
                }
            }
        }
        return bestAction;
    }

    /**
     * Checks if an action has a given precondition.
     *
     * @param action Action to check
     * @param varName Name of the variable
     * @param startValue Value for the variable
     * @return <code>true</code>, if the action has the precondition
     * (varName=startValue); <code>false</code>, otherwise
     * @since 1.0
     */
    private boolean hasPrecondition(Action action, String varName, String startValue) {
        for (GroundedCond prec : action.getPrecs()) {
            if (varName.equals(prec.getVar().toString())) {
                return prec.getValue().equals(startValue);
            }
        }
        return true;	// Variable not in preconditions -> a specific value is not required
    }

    /**
     * In a centralized environment, updates the open goals with the
     * preconditions of a given action and the new reached values with the
     * effects of that action.
     *
     * @param a Action
     * @param openGoals List of open goals
     * @param state Frontier state
     * @param newValues List of new values achieved in the plan for each
     * variable
     * @since 1.0
     */
    private void updateValuesAndGoalsMono(Action a, PriorityQueue<Goal> openGoals,
            HashMap<String, String> state, HashMap<String, ArrayList<String>> newValues) {
        // Add a's preconditions to open goals if they do not hold
        for (GroundedCond p : a.getPrecs()) {
            String precVarName = p.getVar().toString();
            if (!holdsMono(precVarName, p.getValue(), state, newValues)) {
                String precInitValue = selectInitialValueMono(precVarName, p.getValue(),
                        dtgs.getDTG(precVarName), state, newValues);
                Goal newOpenGoal = new Goal(p, pathCostMono(precVarName, precInitValue, p.getValue(),
                        state, newValues));
                openGoals.add(newOpenGoal);
            }
        }
        // Add a's effects to varValues
        for (GroundedEff e : a.getEffs()) {
            String v = e.getVar().toString();
            if (!state.get(v).equals(e.getValue())) {
                ArrayList<String> values = newValues.get(v);
                if (values == null) {
                    values = new ArrayList<>();
                    values.add(e.getValue());
                    newValues.put(v, values);
                } else {
                    if (!values.contains(e.getValue())) {
                        values.add(e.getValue());
                    }
                }
            }
        }
    }

    /**
     * In a centralized environment, checks if a given condition holds.
     *
     * @param varName Name of the variable
     * @param value Value for the variable
     * @param state Frontier state
     * @param newValues List of new values achieved in the plan for each
     * variable
     * @return <code>true</code>, if the condition (varName=value) holds;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    private static boolean holdsMono(String varName, String value, HashMap<String, String> state,
            HashMap<String, ArrayList<String>> newValues) {
        String v = state.get(varName);
        if (v != null && v.equals(value)) {
            return true;
        }
        ArrayList<String> values = newValues.get(varName);
        if (values == null) {
            return false;
        }
        return values.contains(value);
    }

    /**
     * In a centralized environment, calculates the cost of a path.
     *
     * @param var Variable name
     * @param initValue Initial value
     * @param endValue End value
     * @param state Frontier state
     * @param newValues List of new values achieved in the plan for each
     * variable
     * @return Path cost
     * @since 1.0
     */
    private int pathCostMono(String var, String initValue, String endValue, HashMap<String, String> state,
            HashMap<String, ArrayList<String>> newValues) {
        DTG dtg = dtgs.getDTG(var);
        return dtg.pathCost(initValue, endValue, state, newValues, 0);
    }

    /**
     * In a centralized environment, calculates the cost of executing a given
     * action.
     *
     * @param a Action to check
     * @param state Frontier state
     * @param newValues List of new values achieved in the plan for each
     * variable
     * @return Action cost
     * @since 1.0
     */
    private int computeCostMono(Action a, HashMap<String, String> state,
            HashMap<String, ArrayList<String>> newValues) {
        int cost = 0;
        for (GroundedCond prec : a.getPrecs()) {
            String var = prec.getVar().toString();
            DTG dtg = dtgs.getDTG(var);
            String iValue = state.get(var);
            int minPrecCost = dtg.pathCost(iValue, prec.getValue(), state, newValues, 0);
            ArrayList<String> initValues = newValues.get(var);
            if (initValues != null) {
                for (String initValue : initValues) {
                    int precCost = dtg.pathCost(initValue, prec.getValue(), state, newValues, 0);
                    if (precCost < minPrecCost) {
                        minPrecCost = precCost;
                    }
                }
            }
            cost += minPrecCost;
        }
        return cost;
    }

    /**
     * In a distributed environment, evaluates the current plan.
     *
     * @since 1.0
     */
    private void evaluateMultiagentPlan() {
        int totalOrder[] = currentPlan.linearization();
        HashMap<String, ArrayList<String>> varValues = currentPlan.computeMultiState(totalOrder, pf);
        PriorityQueue<Goal> openGoals = new PriorityQueue<>();
        int h = 0;
        for (Goal g : goals) {
            String v = g.varName, end = g.varValue;
            if (!holds(v, end, varValues)) {
                String init = selectInitialValueMulti(v, end, dtgs.getDTG(v), varValues);
                g.distance = pathCostMulti(v, init, end);
                openGoals.add(g);
            }
        }
        while (!openGoals.isEmpty()) {
            h += solveConditionMulti(openGoals.poll(), varValues, openGoals, null);
        }
        currentPlan.setH(h, 0);
        evaluateMultiagentPlanPrivacy(varValues);
    }

    /**
     * Heuristically evaluates the cost of reaching the agent's private goals in
     * a distributed environment.
     *
     * @param varValues Multi-state where, for each variable, the set of
     * achieved values is stored
     * @since 1.0
     */
    private void evaluateMultiagentPlanPrivacy(
            HashMap<String, ArrayList<String>> varValues) {
        if (varValues == null) {
            int totalOrder[] = currentPlan.linearization();
            varValues = currentPlan.computeMultiState(totalOrder, pf);
        }
        PriorityQueue<Goal> openGoals = new PriorityQueue<>();
        for (int i = 0; i < pgoals.size(); i++) {	// Preferences
            int hp = 0;
            Goal g = pgoals.get(i);
            String v = g.varName, end = g.varValue;
            if (!holds(v, end, varValues)) {
                String init = selectInitialValueMulti(v, end, dtgs.getDTG(v), varValues);
                g.distance = pathCostMulti(v, init, end);
                openGoals.add(g);
            }
            while (!openGoals.isEmpty()) {
                hp += solveConditionMulti(openGoals.poll(), varValues, openGoals, null);
            }
            currentPlan.setHPriv(hp, i);
        }
    }

    /**
     * In a distributed environment, calculates the cost of a path.
     *
     * @param var Variable name
     * @param initValue Initial value
     * @param endValue End value
     * @return Path cost
     * @since 1.0
     */
    private int pathCostMulti(String var, String initValue, String endValue) {
        DTG dtg = dtgs.getDTG(var);
        return dtg.pathCostMulti(initValue, endValue);
    }

    /**
     * In a distributed environment, this method selects the most appropriate
     * initial value for a transition.
     *
     * @param varName Name of the variable
     * @param endValue Desired end value
     * @param dtg Domain Transition Graph
     * @param varValues Multi-state where, for each variable, the set of
     * achieved values is stored
     * @return Inital value for the variable
     * @since 1.0
     */
    private static String selectInitialValueMulti(String varName, String endValue, DTG dtg,
            HashMap<String, ArrayList<String>> varValues) {
        ArrayList<String> valueList = varValues.get(varName);
        if (valueList == null) {
            return "?";
        }
        String bestValue = null;
        int bestCost = -1;
        for (String value : valueList) {
            if (bestValue == null) {
                bestCost = dtg.pathCostMulti(value, endValue);
                bestValue = value;
            } else {
                int cost = dtg.pathCostMulti(value, endValue);
                if (cost != -1 && cost < bestCost) {
                    bestCost = cost;
                    bestValue = value;
                }
            }
        }
        return bestValue != null ? bestValue : "?";
    }

    /**
     * In a distributed environment, this method calculates the cost of solving
     * a given condition.
     *
     * @param goal Goal to be evaluated
     * @param varValues Multi-state where, for each variable, the set of
     * achieved values is stored
     * @param openGoals	List of open goals
     * @param tcr Request that caused this calculation
     * @return Estimated goal cost
     * @since 1.0
     */
    private int solveConditionMulti(Goal goal, HashMap<String, ArrayList<String>> varValues,
            PriorityQueue<Goal> openGoals, TransitionCostRequest tcr) {
        int h;
        String varName = goal.varName, varValue = goal.varValue;
        if (holds(varName, varValue, varValues)) {
            return 0;
        }
        DTG dtg = dtgs.getDTG(varName);
        String initValue = selectInitialValueMulti(varName, varValue, dtg, varValues);
        if (!dtg.unknownValue(varValue) && !dtg.unknownValue(initValue)) {	// Known initial value
            h = evaluateWithKnownValues(varName, initValue, varValue, dtg, varValues, tcr,
                    openGoals);
        } else {						// Unknown values
            if (dtg.unknownValue(varValue)) {
                h = evaluateWithUnknownFinalvalue(varName, initValue, varValue, dtg, varValues,
                        tcr, openGoals);
            } else {
                h = evaluateWithUnknownInitialvalue(varName, varValue, dtg, varValues,
                        tcr, openGoals);
            }
        }
        return h;
    }

    /**
     * In a distributed environment, this method calculates the cost of solving
     * a given condition without knowing the initial value of the variable.
     *
     * @param varName Variable name
     * @param varValue End value for the variable
     * @param dtg Domain Transition Graph
     * @param varValues Multi-state where, for each variable, the set of
     * achieved values is stored
     * @param tcr Request that caused this calculation
     * @param openGoals List of open goals
     * @return Estimated condition cost
     * @since 1.0
     */
    private int evaluateWithUnknownInitialvalue(String varName, String varValue, DTG dtg,
            HashMap<String, ArrayList<String>> varValues, TransitionCostRequest tcr,
            PriorityQueue<Goal> openGoals) {
        int h = PENALTY;
        DTGTransition[] transitions = dtg.getTransitionsFrom("?");
        for (DTGTransition t : transitions) {
            if (tcr == null || !tcr.varName.equals(varName) || !tcr.endValue.equals(t.getFinalValue())) {
                int cost = requestTransitionCost(varName, "?", t.getFinalValue(), varValues, dtg, tcr);
                if (cost != PENALTY) {	// Achieved
                    ArrayList<String> values = varValues.get(varName);
                    if (values == null) {
                        values = new ArrayList<>();
                        values.add(t.getFinalValue());
                        varValues.put(varName, values);
                    } else if (!values.contains(t.getFinalValue())) {
                        values.add(t.getFinalValue());
                    }
                    int restCost = evaluateWithKnownValues(varName, t.getFinalValue(), varValue, dtg,
                            varValues, tcr, openGoals);
                    if (restCost != PENALTY) {
                        h = cost + restCost;
                        break;
                    }
                }
            }
        }
        return h;
    }

    /**
     * In a distributed environment, this method calculates the cost of solving
     * a given condition without knowing the final value of the variable.
     *
     * @param varName Variable name
     * @param initValue Initial value for the variable
     * @param dtg Domain Transition Graph
     * @param varValues Multi-state where, for each variable, the set of
     * achieved values is stored
     * @param tcr Request that caused this calculation
     * @param openGoals List of open goals
     * @return Estimated condition cost
     * @since 1.0
     */
    private int evaluateWithUnknownFinalvalue(String varName, String initValue, String varValue,
            DTG dtg, HashMap<String, ArrayList<String>> varValues, TransitionCostRequest tcr,
            PriorityQueue<Goal> openGoals) {
        int h = PENALTY;
        DTGTransition[] transitions = dtg.getTransitionsTo("?");
        if (transitions != null) {
            for (DTGTransition t : transitions) {
                openGoals = new PriorityQueue<>();
                int cost = evaluateWithKnownValues(varName, initValue, t.getStartValue(), dtg,
                        varValues, tcr, openGoals);
                if (cost != PENALTY) {
                    int restCost = requestTransitionCost(varName, t.getStartValue(), varValue,
                            varValues, dtg, tcr);
                    if (restCost != PENALTY) {
                        h = cost + restCost;
                        break;
                    }
                }
            }
        }
        return h;
    }

    /**
     * In a distributed environment, checks if a given condition hols.
     *
     * @param varName Name of the variable
     * @param value Value for the variable
     * @param varValues Multi-state where, for each variable, the set of
     * achieved values is stored
     * @return <code>true</code>, if the condition holds; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    private static boolean holds(String varName, String value, HashMap<String, ArrayList<String>> varValues) {
        ArrayList<String> values = varValues.get(varName);
        if (values == null) {
            return false;
        }
        return values.contains(value);
    }

    /**
     * In a distributed environment, this method calculates the cost of solving
     * a given condition knowing the initial and the final value of the
     * variable.
     *
     * @param varName Variable name
     * @param initValue Initial value for the variable
     * @param varValue End value
     * @param dtg Domain Transition Graph
     * @param varValues Multi-state where, for each variable, the set of
     * achieved values is stored
     * @param tcr Request that caused this calculation
     * @param openGoals List of open goals
     * @return Estimated condition cost
     * @since 1.0
     */
    private int evaluateWithKnownValues(String varName, String initValue, String varValue, DTG dtg,
            HashMap<String, ArrayList<String>> varValues, TransitionCostRequest tcr,
            PriorityQueue<Goal> openGoals) {
        int h = 0;
        String[] path = dtg.getPathMulti(initValue, varValue);
        String prevValue = path[0], nextValue, precVarName;
        for (int i = 1; i < path.length; i++) {
            nextValue = path[i];
            Action a = selectProductorMulti(varName, prevValue, nextValue, varValues);
            if (a == null) {
                h += requestTransitionCost(varName, prevValue, nextValue, varValues, dtg, tcr);
                ArrayList<String> values = varValues.get(varName);
                if (values == null) {
                    values = new ArrayList<>();
                    values.add(nextValue);
                    varValues.put(varName, values);
                } else if (!values.contains(nextValue)) {
                    values.add(nextValue);
                }
            } else {
                h++;
                // Add a's preconditions to open goals if they do not hold
                for (GroundedCond p : a.getPrecs()) {
                    precVarName = p.getVar().toString();
                    if (!holds(precVarName, p.getValue(), varValues)) {
                        String precInitValue = selectInitialValueMulti(precVarName, p.getValue(),
                                dtgs.getDTG(precVarName), varValues);
                        Goal newOpenGoal = new Goal(p, pathCostMulti(precVarName, precInitValue, p.getValue()));
                        openGoals.add(newOpenGoal);
                    }
                }
                // Add a's effects to varValues
                for (GroundedEff e : a.getEffs()) {
                    ArrayList<String> values = varValues.get(e.getVar().toString());
                    if (values == null) {
                        values = new ArrayList<>();
                        values.add(e.getValue());
                        varValues.put(e.getVar().toString(), values);
                    } else if (!values.contains(e.getValue())) {
                        values.add(e.getValue());
                    }
                }
            }
            prevValue = nextValue;
        }
        return h;
    }

    /**
     * In a distributed environment, selects the best productor action for a
     * given value transition.
     *
     * @param varName Name of the variable
     * @param startValue Initial value
     * @param endValue End value
     * @param varValues Multi-state where, for each variable, the set of
     * achieved values is stored
     * @return Productor action
     * @since 1.0
     */
    private Action selectProductorMulti(String varName, String startValue, String endValue,
            HashMap<String, ArrayList<String>> varValues) {
        ArrayList<Action> productors = this.productors.get(varName + "," + endValue);
        if (productors == null || productors.isEmpty()) {
            return null;
        }
        Action bestAction = null;
        int costBest = PENALTY;
        for (int i = 0; i < productors.size(); i++) {
            if (hasPrecondition(productors.get(i), varName, startValue)) {
                int cost = computeCostMulti(productors.get(i), varValues);
                if (cost < costBest) {
                    costBest = cost;
                    bestAction = productors.get(i);
                }
            }
        }
        return bestAction;
    }

    /**
     * In a distributed environment, calculates the cost of executing a given
     * action.
     *
     * @param a Action to check
     * @param varValues Multi-state where, for each variable, the set of
     * achieved values is stored
     * @return Action cost
     * @since 1.0
     */
    private int computeCostMulti(Action a, HashMap<String, ArrayList<String>> varValues) {
        int cost = 0;
        for (GroundedCond prec : a.getPrecs()) {
            String var = prec.getVar().toString();
            DTG dtg = dtgs.getDTG(var);
            int minPrecCost = PENALTY;
            ArrayList<String> initValues = varValues.get(var);
            if (initValues != null && !initValues.isEmpty()) {
                for (String initValue : initValues) {
                    int precCost = dtg.pathCostMulti(initValue, prec.getValue());
                    if (precCost < minPrecCost) {
                        minPrecCost = precCost;
                    }
                }
                cost += minPrecCost;
            } else {
                cost += dtg.pathCostMulti("?", prec.getValue());
            }
        }
        return cost;
    }

    /**
     * In a distributed environment, request information about the cost of a
     * given value transition.
     *
     * @param varName Name of the variable
     * @param prevValue Initial value
     * @param nextValue Final value
     * @param varValues Multi-state where, for each variable, the set of
     * achieved values is stored
     * @param dtg Domain Transition Graph
     * @param prevTcr Request that caused this new request
     * @return Estimated thransition cost
     * @since 1.0
     */
    private int requestTransitionCost(String varName, String prevValue, String nextValue,
            HashMap<String, ArrayList<String>> varValues, DTG dtg, TransitionCostRequest prevTcr) {
        DTGTransition t = dtg.getTransition(prevValue, nextValue);
        ArrayList<String> askedAgents = new ArrayList<>();
        int h = PENALTY;
        for (String ag : t.getAgents()) // Send requests
        {
            if (!ag.equals(comm.getThisAgentName())) {
                if (detectLoop(ag, prevTcr)) {
                    continue;
                }
                TransitionCostRequest tcr = new TransitionCostRequest(varName, prevValue, nextValue,
                        comm.getThisAgentName(), prevTcr, requestId);
                tcr.setState(varValues, groundedTask, ag);
                comm.sendMessage(ag, tcr, false);
                askedAgents.add(ag);
            }
        }
        // Wait responses
        MessageFilter filter = new DTGMessageFilter(askedAgents, requestId++);
        while (!askedAgents.isEmpty()) {
            Serializable msg = comm.receiveMessage(filter, false);
            if (msg instanceof ReplyTransitionCost) {		// Response received
                int index = askedAgents.indexOf(comm.getSenderAgent());
                askedAgents.remove(index);
                int cost = ((ReplyTransitionCost) msg).cost;
                if (cost < h) {
                    h = cost;
                }
            } else if (msg instanceof String) { // End stage message
                assert (((String) msg).equals(AgentCommunication.END_STAGE_MESSAGE));
                ready++;
            } else {						// Transition cost request received		
                TransitionCostRequest tcr = (TransitionCostRequest) msg;
                evaluateRequest(tcr, comm.getSenderAgent());
            }
        }
        return h;
    }

    /**
     * Check if there are loop in the request to other agents.
     *
     * @param ag Destination agent
     * @param t Transition cost request
     * @return <code>true</code>, if the given agent has already been asked
     * about this transition; <code>false</code>, otherwise
     * @since 1.0
     */
    private boolean detectLoop(String ag, TransitionCostRequest t) {
        if (t == null) {
            return false;
        }
        int index = t.agents.indexOf(ag);
        return index != -1;
    }

    /**
     * Evaluates a request received from other agent.
     *
     * @param t Transition cost request
     * @param fromAgent Sender agent
     * @since 1.0
     */
    private void evaluateRequest(TransitionCostRequest t, String fromAgent) {
        if (totalOrderBase == null) {
            totalOrderBase = basePlan.linearization();
        }
        HashMap<String, ArrayList<String>> varValues = basePlan.computeMultiState(totalOrderBase, pf);
        t.updateState(varValues);
        PriorityQueue<Goal> openGoals = new PriorityQueue<>();
        openGoals.add(t.getGoal());
        int h = 0;
        while (!openGoals.isEmpty()) {
            h += solveConditionMulti(openGoals.poll(), varValues, openGoals, t);
        }
        //sop("Sending reply (" + h + ") to agent " + fromAgent);
        comm.sendMessage(fromAgent, new ReplyTransitionCost(h, t.requestId), false);
    }

    /**
     * Synchronization step after the distributed heuristic evaluation.
     *
     * @since 1.0
     */
    @Override
    public void waitEndEvaluation() {
        if (comm.batonAgent()) {
            ready++;
            while (ready < comm.numAgents()) {
                Serializable msg = comm.receiveMessage(false);
                if (msg instanceof String) {	// End of evaluation stage received
                    assert (((String) msg).equals(AgentCommunication.END_STAGE_MESSAGE));
                    ready++;
                } else {						// Evaluation request
                    String fromAgent = comm.getSenderAgent();
                    TransitionCostRequest tcr = (TransitionCostRequest) msg;
                    evaluateRequest(tcr, fromAgent);
                }
            }
            // Sending end stage messages to all agents
            comm.sendMessage(AgentCommunication.END_STAGE_MESSAGE, false);
        } else {
            boolean endStage = false;
            // Sending end stage message to baton agent
            comm.sendMessage(comm.getBatonAgent(), AgentCommunication.END_STAGE_MESSAGE, false);
            while (!endStage) {
                Serializable msg = comm.receiveMessage(false);
                if (msg instanceof String) {	// End of evaluation stage received
                    // End stage message received from baton agent
                    assert (((String) msg).equals(AgentCommunication.END_STAGE_MESSAGE));
                    endStage = true;
                } else {						// Evaluation request
                    String fromAgent = comm.getSenderAgent();
                    TransitionCostRequest tcr = (TransitionCostRequest) msg;
                    evaluateRequest(tcr, fromAgent);
                }
            }
        }
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

    /**
     * Goal class defined (sub)goals for the priority queue of open goals.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    private static class Goal implements Comparable<Goal> {

        String varName;     // Variable name
        String varValue;    // Value for the variable
        int distance;       // Path distance to reach this goal

        /**
         * Creates a new goal.
         *
         * @param goal Grounded condition
         * @param distance Path distance
         * @since 1.0
         */
        public Goal(GroundedCond goal, int distance) {
            this(goal.getVar().toString(), goal.getValue(), distance);
        }

        /**
         * Creates a new goal.
         *
         * @param varName Variable name
         * @param varValue Value for the variable
         * @param distance Path distance to reach this goal
         * @since 1.0
         */
        public Goal(String varName, String varValue, int distance) {
            this.varName = varName;
            this.varValue = varValue;
            this.distance = distance;
        }

        /**
         * Compares two goals.
         *
         * @param g Another goal to compare with this one
         * @return Value less than zero if the distance to this goal is smaller;
         * Value greater than zero if the distance to the other goal is smaller;
         * Zero, otherwise
         * @since 1.0
         */
        @Override
        public int compareTo(Goal g) {
            return g.distance - distance;
        }

        /**
         * Returns a description of this goal.
         *
         * @return Description of this goal
         * @since 1.0
         */
        @Override
        public String toString() {
            return varName + "=" + varValue + "(" + distance + ")";
        }

        /**
         * Gets a hash code for this goal.
         *
         * @return Hash code
         * @since 1.0
         */
        @Override
        public int hashCode() {
            return (varName + "=" + varValue).hashCode();
        }

        /**
         * Check if two goals are equal.
         *
         * @param x Another goal to compare with this one.
         * @return <code>true</code>, if both goals have the same variable name
         * and value; <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            Goal g = (Goal) x;
            return varName.equals(g.varName) && varValue.equals(g.varValue);
        }
    }

    /**
     * TransitionCostRequest defined a request to other agent to get the
     * estimated cost of a value transition for a given variable.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    public static class TransitionCostRequest implements java.io.Serializable {

        // Serial number of serializarion
        private static final long serialVersionUID = 5485301296724177527L;
        // List of agents that have already participated to solve this request (to avoid loops)
        public ArrayList<String> agents;
        public String varName;      // Name of the variable
        public String startValue;   // Initial value
        public String endValue;     // End value
        // Multi-state where, for each variable, the set of achieved values is stored
        public ArrayList<ArrayList<String>> varValuesList;
        public int requestId;       // Identifier code for this request

        /**
         * Builds a new transition cost request.
         *
         * @param varName Name of the variable
         * @param prevValue Initial value
         * @param nextValue End value
         * @param agentName Destination agent
         * @param prevTcr Request that caused this new request
         * @param requestId Identifier code for this request
         * @since 1.0
         */
        public TransitionCostRequest(String varName, String prevValue, String nextValue,
                String agentName, TransitionCostRequest prevTcr, int requestId) {
            this.varName = varName;
            this.startValue = prevValue;
            this.endValue = nextValue;
            this.agents = new ArrayList<>();
            if (prevTcr != null) {
                for (String ag : prevTcr.agents) {
                    this.agents.add(ag);
                }
            }
            this.agents.add(agentName);
            this.varValuesList = new ArrayList<>();
            this.requestId = requestId;
        }

        /**
         * Returns the goal of this request.
         *
         * @return Goal
         * @since 1.0
         */
        public Goal getGoal() {
            return new Goal(varName, endValue, -1);
        }

        /**
         * Updates the given multi-state with the values received through this
         * request.
         *
         * @param varValues Multi-state where, for each variable, the set of
         * achieved values is stored
         * @since 1.0
         */
        public void updateState(HashMap<String, ArrayList<String>> varValues) {
            for (ArrayList<String> list : varValuesList) {
                ArrayList<String> values = varValues.get(list.get(0));
                if (values == null) {
                    values = new ArrayList<>();
                    for (int i = 1; i < list.size(); i++) {
                        values.add(list.get(i));
                    }
                    varValues.put(list.get(0), values);
                } else {
                    for (int i = 1; i < list.size(); i++) {
                        if (!values.contains(list.get(i))) {
                            values.add(list.get(i));
                        }
                    }
                }
            }
        }

        /**
         * Calculates the multi-state to send to another agent, removing the
         * private information.
         *
         * @param varValues Multi-state where, for each variable, the set of
         * achieved values is stored
         * @param groundedTask Grounded task
         * @param toAgent Destination agent
         * @since 1.0
         */
        public void setState(HashMap<String, ArrayList<String>> varValues,
                GroundedTask groundedTask, String toAgent) {
            for (String v : varValues.keySet()) {
                GroundedVar gv = groundedTask.getVarByName(v);
                if (gv.shareable(toAgent)) {
                    ArrayList<String> list = varValues.get(v),
                            newList = new ArrayList<>(list.size() + 1);
                    newList.add(v);
                    for (String value : list) {
                        if (gv.shareable(value, toAgent)) {
                            newList.add(value);
                        }
                    }
                    this.varValuesList.add(newList);
                }
            }
        }

        /**
         * Gets a description of the requested transition.
         *
         * @return Description of the requested transition
         * @since 1.0
         */
        @Override
        public String toString() {
            return varName + "(" + startValue + "->" + endValue + ")";
        }
    }

    /**
     * Reply message for a transition cost request.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    public static class ReplyTransitionCost implements Serializable {

        // Serial number for serialization
        private static final long serialVersionUID = 8450612556336972847L;
        int cost;           // Calculated transition cost
        int requestId;      // Identification code of the request

        /**
         * Creates a new reply message.
         *
         * @param cost Calculated transition cost
         * @param requestId Identification code of the request
         * @since 1.0
         */
        public ReplyTransitionCost(int cost, int requestId) {
            this.cost = cost;
            this.requestId = requestId;
        }
    }

    /**
     * Filter for reception of messages. Allows to get messages only with a
     * given identifier and from a given set of agents.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    public static class DTGMessageFilter implements MessageFilter {

        private final int requestId;    // Request identifier code 
        private final ArrayList<String> askedAgents;    // List of agents that must reply

        /**
         * Creates a new message filter.
         *
         * @param askedAgents List of agents that must reply
         * @param requestId Request identifier code
         * @since 1.0
         */
        public DTGMessageFilter(ArrayList<String> askedAgents, int requestId) {
            this.requestId = requestId;
            this.askedAgents = askedAgents;
        }

        /**
         * Check if a given message meets the conditions of the filter.
         *
         * @param m Message to check
         * @return <code>true</code> if the message meets the conditions of the
         * filter; <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean validMessage(Message m) {
            if (m.content() instanceof ReplyTransitionCost) {
                return ((ReplyTransitionCost) m.content()).requestId == requestId
                        && askedAgents.contains(m.sender());
            }
            if (m.content() instanceof String
                    && ((String) m.content()).equals(AgentCommunication.END_STAGE_MESSAGE)) {
                return true;
            }
            return m.content() instanceof TransitionCostRequest;
        }
    }

}
