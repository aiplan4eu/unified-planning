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
package org.agreement_technologies.service.map_grounding;

import java.util.ArrayList;
import java.util.Deque;
import java.util.Hashtable;
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_grounding.GroundedNumericEff;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.GroundedVar;
import org.agreement_technologies.common.map_grounding.Grounding;
import org.agreement_technologies.common.map_grounding.ReachedValue;
import org.agreement_technologies.common.map_parser.Condition;
import org.agreement_technologies.common.map_parser.Function;
import org.agreement_technologies.common.map_parser.NumericEffect;
import org.agreement_technologies.common.map_parser.NumericExpression;
import org.agreement_technologies.common.map_parser.Operator;
import org.agreement_technologies.common.map_parser.Parameter;
import org.agreement_technologies.common.map_parser.Task;
import org.agreement_technologies.service.map_grounding.GroundedTaskImp.ActionCondition;
import org.agreement_technologies.service.map_grounding.GroundedTaskImp.GroundedValue;
import org.agreement_technologies.service.map_grounding.GroundedTaskImp.GroundedVarImp;

/**
 * Planning task grounding process.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class GroundingImp implements Grounding {

    private Hashtable<String, Boolean> staticFunctions;     // Static functions
    private GroundedTaskImp gTask;                          // Grounded planning task
    private OpGrounding[] gOps;                             // Operators for grounding
    private ArrayList<OpGrounding> opRequireFunction[];     // For each function, list of operators that need it (in positive way)
    private ArrayList<ProgrammedValue> newTrueValues;       // Last reached true values
    private ArrayList<ProgrammedValue> auxTrueValues;       // Auxiliary array of true values
    private ArrayList<ArrayList<ProgrammedValue>> trueValuesByFunction;  // Reached true values classified by the variable function index
    private ArrayList<ArrayList<ProgrammedValue>> falseValuesByFunction; // Reached true values classified by the variable function index
    private Hashtable<ProgrammedValue, Boolean> falseValueReached;       // Stores the reached false values for the variables
    private int currentLevel;               // Current RPG level
    private int startNewValues;             // Start of the new values added to the RPG
    private int currentTrueValueIndex;      // Current index for reached values
    private int currentFalseValueIndex;     // Current index for reached false values             
    private final int sameObjects;          // Same objects filtering type. See constants in GroundedTask
    private boolean isReground;             // Flag to check if we are extending the initial grounding

    /**
     * Constructor for the grounder.
     *
     * @param sameObjects Same objects filtering type. See constants in
     * GroundedTask
     * @since 1.0
     */
    public GroundingImp(int sameObjects) {
        staticFunctions = new Hashtable<>();
        this.sameObjects = sameObjects;
    }

    /**
     * Computes the list of static functions, i.e. functions whose values do not
     * change due to the action effects.
     *
     * @param task Planning task
     * @param comm Communication utility
     * @since 1.0
     */
    @Override
    public void computeStaticFunctions(Task task, AgentCommunication comm) {
        String[] sf = getStaticFunctions(task);
        if (comm.numAgents() == 1) { // Single agent
            for (String s : sf) {
                setStaticFunction(s);
            }
        } else { // Communication protocol to figure out the static functions
            if (comm.batonAgent()) {
                // Retrieve all static functions from all agents
                ArrayList<String> allSF = new ArrayList<>();
                for (String ag : comm.getOtherAgents()) {
                    String[] osf = (String[]) comm.receiveMessage(ag, true);
                    if (osf != null) {
                        for (String f : osf) {
                            if (!allSF.contains(f)) {
                                allSF.add(f);
                            }
                        }
                    }
                }
                // Check each function to reach a consensus
                for (String f : allSF) {
                    if (checkStaticFunction(task, f, sf)) {
                        comm.sendMessage(f, true);
                        boolean isStatic = true;
                        for (String ag : comm.getOtherAgents()) {
                            String resp = (String) comm
                                    .receiveMessage(ag, true);
                            if (resp.equalsIgnoreCase("no")) {
                                isStatic = false;
                            }
                        }
                        comm.sendMessage(isStatic ? "yes" : "no", true);
                        if (isStatic) {
                            setStaticFunction(f);
                        }
                    }
                }
                comm.sendMessage(AgentCommunication.END_STAGE_MESSAGE, true);
            } else {
                comm.sendMessage(comm.getBatonAgent(), sf, true);
                String f = "";
                while (!f.equals(AgentCommunication.END_STAGE_MESSAGE)) {
                    f = (String) comm
                            .receiveMessage(comm.getBatonAgent(), true);
                    if (!f.equals(AgentCommunication.END_STAGE_MESSAGE)) {
                        comm.sendMessage(
                                comm.getBatonAgent(),
                                checkStaticFunction(task, f, sf) ? "yes" : "no",
                                true);
                        String resp = (String) comm.receiveMessage(
                                comm.getBatonAgent(), true);
                        if (resp.equalsIgnoreCase("yes")) {
                            setStaticFunction(f);
                        }
                    }
                }
            }
        }
    }

    /**
     * Checks if a given function is static
     *
     * @param task Parsed planning task
     * @param f Function name
     * @param sf Set of static functions
     * @return <code>true</code>, if f is static. Function f is static if f is
     * not known by this agents or if f is in the set of static functions
     * @since 1.0
     */
    protected boolean checkStaticFunction(Task task, String f, String[] sf) {
        for (String s : sf) {
            if (s.equalsIgnoreCase(f)) {
                return true;
            }
        }
        Function func[] = task.getFunctions();
        for (Function aux : func) {
            if (aux.getName().equalsIgnoreCase(f)) {
                return false;
            }
        }
        return true;
    }

    /**
     * Returns the list of static functions.
     *
     * @param task Parsed planning task
     * @return Array of static functions
     * @since 1.0
     */
    private String[] getStaticFunctions(Task task) {
        ArrayList<String> sf = new ArrayList<>();
        Function func[] = task.getFunctions();
        Operator ops[] = task.getOperators();
        for (Function f : func) {
            boolean isEffect = false, isInRules = false;
            // Functions in rules are not considered static
            for (Operator rule : task.getBeliefs()) {
                Condition effs[] = rule.getEffect();
                for (Condition e : effs) {
                    if (e.getFunction().getName().equals(f.getName())) {
                        isInRules = true;
                        break;
                    }
                }
                if (!isInRules) {
                    Condition precs[] = rule.getPrecondition();
                    for (Condition p : precs) {
                        if (p.getFunction().getName().equals(f.getName())) {
                            isInRules = true;
                            break;
                        }
                    }
                }
                if (isInRules) {
                    break;
                }
            }
            if (!isInRules) {
                for (Operator op : ops) {
                    Condition effs[] = op.getEffect();
                    for (Condition e : effs) {
                        if (e.getFunction().getName().equals(f.getName())) {
                            isEffect = true;
                            break;
                        }
                    }
                    if (isEffect) {
                        break;
                    }
                }
            }
            if (!isEffect && !isInRules) {
                sf.add(f.getName()); // Static
            }
        }
        String res[] = new String[sf.size()];
        for (int i = 0; i < sf.size(); i++) {
            res[i] = sf.get(i);
        }
        return res;
    }

    /**
     * Sets a function as static.
     *
     * @param fnc Static function name
     * @since 1.0
     */
    protected void setStaticFunction(String fnc) {
        staticFunctions.put(fnc, true);
    }

    /**
     * Checks if a function has been set as static.
     *
     * @param fnc Function name
     * @return <code>true</code>, if the function is static; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    protected boolean isStaticFunction(String fnc) {
        return staticFunctions.containsKey(fnc);
    }

    /**
     * Grounds a planning task.
     *
     * @param task Planning task
     * @param comm Communication utility
     * @param negationByFailure <code>true</code> if the used model is negation
     * by failure; <code>false</code> if it is unknown by failure
     * @return Grounded task
     * @since 1.0
     */
    @Override
    public GroundedTask ground(Task task, AgentCommunication comm, boolean negationByFailure) {
        GroundedTask groundedTask = ground(task, comm.getThisAgentName(), negationByFailure);
        // Communication with the other agents
        if (comm.numAgents() > 1) {
            boolean endRPG[] = new boolean[comm.numAgents()]; // Initialized to false
            do {
                sendRPGFacts(endRPG, groundedTask, comm);
                receiveRPGFacts(endRPG, comm);
            } while (!checkEndRPG(endRPG, comm));
        }
        return groundedTask;
    }

    /**
     * Receives new facts from other agents.
     *
     * @param endRPG Semaphore to know the end of the disRPG construction
     * @param comm Communication utility
     * @since 1.0
     */
    protected void receiveRPGFacts(boolean[] endRPG, AgentCommunication comm) {
        ArrayList<ReachedValue> newData = new ArrayList<>();
        for (String ag : comm.getOtherAgents()) {
            java.io.Serializable data = comm.receiveMessage(ag, false);
            if (data instanceof String) {
                if (((String) data)
                        .equals(AgentCommunication.END_STAGE_MESSAGE)) {
                    endRPG[comm.getAgentIndex(ag)] = true;
                } else {
                    throw new RuntimeException("Agent " + ag
                            + " is not following the RPG protocol");
                }
            } else {
                @SuppressWarnings("unchecked")
                ArrayList<RPGData> dataReceived = (ArrayList<RPGData>) data;
                endRPG[comm.getAgentIndex(ag)] = false;
                for (RPGData d : dataReceived) {
                    newData.add(createReachedValue(d));
                }
            }
        }
        reground(newData.toArray(new ReachedValue[newData.size()]));
    }

    /**
     * Sends the new achieved facts to the other agents.
     *
     * @param endRPG Semaphore to know the end of the disRPG construction
     * @param gTask Grounded task
     * @param comm Communication utility
     * @since 1.0
     */
    protected void sendRPGFacts(boolean[] endRPG, GroundedTask gTask,
            AgentCommunication comm) {
        ReachedValue[] newValues = getNewValues();
        boolean somethingToSend = false;
        for (String ag : comm.getOtherAgents()) {
            for (ReachedValue v : newValues) {
                if (v.shareable(ag)) {
                    somethingToSend = true;
                    break;
                }
            }
            if (somethingToSend) {
                break;
            }
        }
        endRPG[comm.getThisAgentIndex()] = !somethingToSend;
        if (somethingToSend) {
            for (String ag : comm.getOtherAgents()) {
                ArrayList<RPGData> dataToSend = new ArrayList<>();
                for (ReachedValue v : newValues) {
                    if (v.shareable(ag)) {
                        dataToSend.add(new RPGData(v, gTask, comm
                                .getAgentList()));
                    }
                }
                comm.sendMessage(ag, dataToSend, false);
            }
        } else {
            comm.sendMessage(AgentCommunication.END_STAGE_MESSAGE, false);
        }
    }

    /**
     * Checks whether the RPG building has finished.
     *
     * @param endRPG Semaphore to know the end of the disRPG construction
     * @param comm Communication utility
     * @return <code>true</code> if the RPG building has finished
     * @since 1.0
     */
    protected boolean checkEndRPG(boolean[] endRPG, AgentCommunication comm) {
        boolean finished = true;
        for (boolean end : endRPG) {
            if (!end) {
                finished = false;
                break;
            }
        }
        if (!finished) { // Synchronization message
            if (comm.batonAgent()) {
                comm.sendMessage(AgentCommunication.SYNC_MESSAGE, true);
            } else {
                comm.receiveMessage(comm.getBatonAgent(), true);
            }
        }
        return finished;
    }

    /**
     * Grounds a planning task.
     *
     * @param task Parsed planning task
     * @param agentName Name of this agent
     * @param negationByFailure <code>true</code> if the used model is negation
     * by failure; <code>false</code> if it is unknown by failure
     * @return Grounded task
     * @since 1.0
     */
    protected GroundedTask ground(Task task, String agentName, boolean negationByFailure) {
        currentLevel = 0;
        currentTrueValueIndex = 0;
        currentFalseValueIndex = 0;
        startNewValues = 0;
        isReground = false;
        gTask = new GroundedTaskImp(task, sameObjects, negationByFailure);
        gTask.initAgents(task, agentName);
        gTask.setStaticFunctions(staticFunctions);
        initOperators(task);
        initInitialState();
        while (newTrueValues.size() > 0) {
            auxTrueValues = new ArrayList<>();
            for (OpGrounding op : gOps) // Operators without positive preconditions
            {
                if (op.numTruePrec == 0) {
                    matchNegativeConditions(op, false);
                }
            }
            for (ProgrammedValue pv : newTrueValues) {
                match(pv, false);
            }
            for (ProgrammedValue pv : auxTrueValues) {
                GroundedTaskImp.GroundedVarImp v = gTask.vars.get(pv.varIndex);
                trueValuesByFunction.get(v.fncIndex).add(pv);
            }
            startNewValues += newTrueValues.size();
            newTrueValues = auxTrueValues;
            currentLevel++;
        }
        return gTask;
    }

    /**
     * Obtains a reached value from the received data.
     *
     * @param data Received data
     * @return Reached value
     * @since 1.0
     */
    protected ReachedValue createReachedValue(RPGData data) {
        GroundedVarImp v = gTask.new GroundedVarImp(data.varName,
                data.params.length);
        for (int i = 0; i < data.params.length; i++) {
            Integer pIndex = gTask.objectIndex.get(data.params[i]);
            if (pIndex == null) // New object
            {
                pIndex = gTask.createNewObject(data.params[i],
                        data.paramTypes[i]);
            }
            v.paramIndex[i] = pIndex;
        }
        Integer varIndex = gTask.getVarIndex(v);
        if (varIndex == null) // New variable
        {
            varIndex = gTask.createNewVariable(v);
        }
        Integer valueIndex = gTask.objectIndex.get(data.value);
        if (valueIndex == null) // New object
        {
            valueIndex = gTask.createNewObject(data.value, data.valueTypes);
        }
        GroundedValue gv = gTask.new GroundedValue(varIndex, valueIndex);
        gv.minTime = data.minTime;
        return gv;
    }

    /**
     * Re-grounds a planning task by adding new values.
     *
     * @param newValues Array of new values
     * @since 1.0
     */
    protected void reground(ReachedValue[] newValues) {
        isReground = true;
        gTask.resetNewValues();
        newTrueValues = addNewReachedValues(newValues);
        while (newTrueValues.size() > 0) {
            auxTrueValues = new ArrayList<>();
            for (OpGrounding op : gOps) // Operators without positive preconditions
            {
                if (op.numTruePrec == 0) {
                    matchNegativeConditions(op, true);
                }
            }
            for (ProgrammedValue pv : newTrueValues) {
                match(pv, true);
            }
            for (ProgrammedValue pv : auxTrueValues) {
                GroundedTaskImp.GroundedVarImp v = gTask.vars.get(pv.varIndex);
                trueValuesByFunction.get(v.fncIndex).add(pv);

            }
            newTrueValues = auxTrueValues;
        }
    }

    /**
     * Adds the new reached values to the RPG.
     *
     * @param newValues List of new values
     * @return Set of values that have not been reached before
     * @since 1.0
     */
    private ArrayList<ProgrammedValue> addNewReachedValues(
            ReachedValue[] newValues) {
        ArrayList<ProgrammedValue> res = new ArrayList<>();
        for (ReachedValue rv : newValues) {
            GroundedValue gv = (GroundedValue) rv;
            Integer rvIndex = gTask.valueIndex.get(gv);
            if (rvIndex == null) { // New value
                rvIndex = gTask.values.size();
                gTask.valueIndex.put(gv, rvIndex);
                gTask.values.add(gv);
                ProgrammedValue pv = new ProgrammedValue(
                        currentTrueValueIndex++, gv.varIndex, gv.valueIndex);
                trueValuesByFunction.get(gv.var().fncIndex).add(pv);
                res.add(pv);
                // Negative values derived from this new value
                ArrayList<Integer> domainValues = gTask.getAllDomainValues(gv
                        .var().domainIndex);
                for (Integer value : domainValues) {
                    if (value != gv.valueIndex) {
                        pv = new ProgrammedValue(currentFalseValueIndex++,
                                gv.varIndex, value);
                        if (!falseValueReached.containsKey(pv)) {
                            falseValueReached.put(pv, true);
                            falseValuesByFunction.get(gv.var().fncIndex)
                                    .add(pv);
                        }
                    }
                }
            } else { // Existing value
                GroundedValue oldGV = gTask.values.get(rvIndex);
                for (int i = 0; i < oldGV.minTime.length; i++) {
                    if (gv.minTime[i] != -1) {
                        if (oldGV.minTime[i] == -1) {
                            oldGV.minTime[i] = gv.minTime[i];
                        } else {
                            oldGV.minTime[i] = Math.min(oldGV.minTime[i],
                                    gv.minTime[i]);
                        }
                    }
                }
            }
        }
        return res;
    }

    /**
     * Returns the new values achieved in the grounding process.
     *
     * @return Array of reached values
     * @since 1.0
     */
    protected ReachedValue[] getNewValues() {
        return gTask.getNewValues();
    }

    /**
     * Matching process for operator grounding.
     *
     * @param pv Programmed value
     * @param isTrue <code>true</code>, if the value for the variable is
     * positive; <code>false</code>, if it is negative
     * @since 1.0
     */
    private void match(ProgrammedValue pv, boolean reGround) {
        GroundedTaskImp.GroundedVarImp v = gTask.vars.get(pv.varIndex);
        ArrayList<OpGrounding> opList = opRequireFunction[v.fncIndex];
        for (OpGrounding op : opList) {
            int precIndex = -1;
            do {
                precIndex = op.matches(v, pv.valueIndex, precIndex + 1);
                if (precIndex != -1
                        && op.stackParameters(precIndex, v, pv.valueIndex, true)) { // Match
                    // found
                    op.indexFirstValue = pv.index;
                    completeMatch(0, op, reGround);
                    op.unstackParameters(precIndex, true);
                }
            } while (precIndex != -1);
        }
    }

    /**
     * Completes the grounding of a partially grounded operator.
     *
     * @param startPrec Index of the first ungrounded precondition
     * @param op Partially grounded operator
     * @param reGround <code>true</code>, if we are not in the first grounding
     * stage; <code>false</code>, otherwise
     * @since 1.0
     */
    private void completeMatch(int startPrec, OpGrounding op, boolean reGround) {
        if (op.numUngroundedTruePrecs == 0) {
            matchNegativeConditions(op, reGround);
            return;
        }
        int numPrec = startPrec;
        while (op.truePrec[numPrec].grounded) {
            numPrec++;
        }
        OpCondGrounding p = op.truePrec[numPrec];
        ArrayList<ProgrammedValue> valueList = trueValuesByFunction
                .get(p.fncIndex);
        for (ProgrammedValue pv : valueList) {
            if ((isReground || pv.index < startNewValues || pv.index >= op.indexFirstValue)
                    && op.precMatches(p, gTask.vars.get(pv.varIndex),
                            pv.valueIndex)) {
                if (op.stackParameters(numPrec, gTask.vars.get(pv.varIndex),
                        pv.valueIndex, true)) {
                    completeMatch(numPrec + 1, op, reGround);
                    op.unstackParameters(numPrec, true);
                }
            }
        }
    }

    /**
     * Grounds the negative conditions of a partially grounded operator.
     *
     * @param op Partially grounded operator
     * @param reGround <code>true</code>, if we are not in the first grounding
     * stage; <code>false</code>, otherwise
     * @since 1.0
     */
    private void matchNegativeConditions(OpGrounding op, boolean reGround) {
        if (op.numUngroundedFalsePrecs == 0) { // Operator grounding
            groundRemainingParameters(op, reGround);
            return;
        }
        for (int i = 0; i < op.numFalsePrec; i++) {
            OpCondGrounding p = op.falsePrec[i];
            if (!p.grounded) {
                ArrayList<ProgrammedValue> valueList = falseValuesByFunction
                        .get(p.fncIndex);
                for (ProgrammedValue pv : valueList) {
                    if (op.negPrecMatches(p, gTask.vars.get(pv.varIndex),
                            pv.valueIndex)) {
                        if (op.stackParameters(i, gTask.vars.get(pv.varIndex),
                                pv.valueIndex, false)) {
                            matchNegativeConditions(op, reGround);
                            op.unstackParameters(i, false);
                        }
                    }
                }
            }
        }
    }

    /**
     * Grounds the remaining parameters of an operator with all possible values.
     *
     * @param op Partially gorunded operator
     * @param reGround <code>true</code>, if we are not in the first grounding
     * stage; <code>false</code>, otherwise
     * @since 1.0
     */
    private void groundRemainingParameters(OpGrounding op, boolean reGround) {
        int pIndex = -1;
        for (int i = 0; i < op.numParams; i++) {
            int objIndex = op.paramValues[i].isEmpty() ? -1 : op.paramValues[i]
                    .peek();
            if (objIndex == -1) {
                pIndex = i;
                break;
            }
        }
        if (pIndex == -1) {
            groundAction(op, reGround);
        } else {
            for (int i = 0; i < gTask.objects.size(); i++) {
                if (gTask.objectIsCompatible(i, op.paramTypes[pIndex])) {
                    op.paramValues[pIndex].push(i);
                    groundRemainingParameters(op, reGround);
                    op.paramValues[pIndex].pop();
                }
            }
        }
    }

    /**
     * Grounds an operator as a new action.
     *
     * @param op Grounded operator
     * @param reGround <code>true</code>, if we are not in the first grounding
     * stage; <code>false</code>, otherwise
     * @since 1.0
     */
    private void groundAction(OpGrounding op, boolean reGround) {
        if (op.isRule) {
            if (gTask.ruleIndex.get(op.toString()) != null) {
                return; // Existing rule
            }
        } else {
            if (gTask.actionIndex.get(op.toString()) != null) {
                return; // Existing action
            }
        }
        GroundedTaskImp.ActionImp a = gTask.new ActionImp(op.name,
                op.numParams, op.numTruePrec + op.numFalsePrec, op.eff.length);
        // Action parameters grounding
        for (int i = 0; i < op.numParams; i++) {
            int objIndex = op.paramValues[i].peek();
            a.setParam(i, objIndex, gTask.objects.get(objIndex));
        }
        // Action preconditions grounding
        for (int i = 0; i < op.numTruePrec; i++) {
            GroundedTaskImp.GroundedValue gv = groundActionCondition(a,
                    op.truePrec[i], false);
            a.addPrecondition(i, gv, true);
        }
        for (int i = 0; i < op.numFalsePrec; i++) {
            GroundedTaskImp.GroundedValue gv = groundActionCondition(a,
                    op.truePrec[i], false);
            a.addPrecondition(i + op.numTruePrec, gv, false);
        }
        // Action effects grounding
        for (int i = 0; i < op.eff.length; i++) {
            GroundedTaskImp.GroundedValue gv = groundActionCondition(a,
                    op.eff[i], true);
            if (!a.addEffect(i, gv)) {
                return; // Same objects action -> invalid action
            }
        }
        if (!checkContradictoryEffects(a)) {
            return;
        }
        // Add effects to the RPG
        if (reGround) {
            currentLevel = a.getMinTime();
        }
        for (GroundedTaskImp.ActionCondition eff : a.eff) {
            boolean newValue = !gTask.valueIndex.containsKey(eff.gv);
            int gvIndex = gTask.addValue(eff.gv.varIndex, eff.gv.valueIndex,
                    currentLevel + 1);
            eff.gv = gTask.values.get(gvIndex);
            if (reGround && !gTask.newValues.contains(eff.gv)) {
                gTask.newValues.add(eff.gv);
            }
            if (newValue) { // New value reached
                auxTrueValues.add(new ProgrammedValue(currentTrueValueIndex++,
                        eff.gv.varIndex, eff.gv.valueIndex));
                // Negative values derived from this new value
                ArrayList<Integer> domainValues = gTask
                        .getAllDomainValues(eff.gv.var().domainIndex);
                for (Integer value : domainValues) {
                    if (value != eff.gv.valueIndex) {
                        ProgrammedValue pv = new ProgrammedValue(
                                currentFalseValueIndex++, eff.gv.varIndex,
                                value);
                        if (!falseValueReached.containsKey(pv)) {
                            falseValueReached.put(pv, true);
                            falseValuesByFunction.get(eff.gv.var().fncIndex)
                                    .add(pv);
                        }
                    }
                }
            }
        }
        if (op.numEff.length > 0) {
            groundActionNumericEffect(a, op);
        }
        // Action storage
        if (op.isRule) {
            gTask.ruleIndex.put(a.toString(), gTask.actions.size());
            gTask.rules.add(a);
        } else {
            gTask.actionIndex.put(a.toString(), gTask.actions.size());
            gTask.actions.add(a);
        }
    }

    /**
     * Grounds an action condition/effect.
     *
     * @param a Action
     * @param cond Condition to be grounded
     * @param canAddVariable <code>true</code>, if new variables can be added to
     * the domain; <code>false</code>, otherwise
     * @return Grounded condition
     * @since 1.0
     */
    private GroundedTaskImp.GroundedValue groundActionCondition(
            GroundedTaskImp.ActionImp a, OpCondGrounding cond,
            boolean canAddVariable) {
        Function f = gTask.functions.get(cond.fncIndex);
        GroundedTaskImp.GroundedVarImp var = gTask.new GroundedVarImp(
                f.getName(), cond.numParams);
        for (int j = 0; j < cond.numParams; j++) {
            if (cond.paramConstant[j]) {
                var.paramIndex[j] = cond.paramIndex[j];
            } else {
                var.paramIndex[j] = a.paramIndex[cond.paramIndex[j]];
            }
        }
        Integer varIndex = gTask.varIndex.get(var);
        if (varIndex != null) {
            var = gTask.vars.get(varIndex);
        } else if (canAddVariable) {
            var.domain = f.getDomain();
            var = gTask.addVariable(var);
        } else {
            throw new RuntimeException("Unknown variable in action '" + a + "'");
        }
        int valueIndex = cond.constantValue ? cond.valueIndex
                : a.paramIndex[cond.valueIndex];
        return gTask.new GroundedValue(var.varIndex, valueIndex);
    }

    /**
     * Adds the initial state to the RPG.
     *
     * @since 1.0
     */
    private void initInitialState() {
        int booleanTypeIndex = gTask.typeIndex.get("boolean");
        int falseObjIndex = gTask.objectIndex.get("false");
        trueValuesByFunction = new ArrayList<>();
        falseValuesByFunction = new ArrayList<>();
        falseValueReached = new Hashtable<>();
        for (int i = 0; i < gTask.functions.size(); i++) {
            trueValuesByFunction.add(new ArrayList<ProgrammedValue>());
            falseValuesByFunction.add(new ArrayList<ProgrammedValue>());
        }
        newTrueValues = new ArrayList<>();
        for (int i = 0; i < gTask.vars.size(); i++) {
            GroundedTaskImp.GroundedVarImp v = gTask.vars.get(i);
            if (v.trueValue == -1) { // True value is not set for this variable
                if (v.domainIndex.length == 1
                        && v.domainIndex[0] == booleanTypeIndex) {
                    // <> true is the same as == false
                    ProgrammedValue pv = new ProgrammedValue(
                            currentTrueValueIndex++, v.varIndex, falseObjIndex);
                    newTrueValues.add(pv);
                    trueValuesByFunction.get(v.fncIndex).add(pv);
                    gTask.addValue(i, falseObjIndex, currentLevel);
                }
                for (Integer value : v.falseValues) {
                    ProgrammedValue pv = new ProgrammedValue(
                            currentFalseValueIndex++, v.varIndex, value);
                    falseValuesByFunction.get(v.fncIndex).add(pv);
                    falseValueReached.put(pv, true);
                }
            } else {
                ProgrammedValue pv = new ProgrammedValue(
                        currentTrueValueIndex++, v.varIndex, v.trueValue);
                newTrueValues.add(pv);
                trueValuesByFunction.get(v.fncIndex).add(pv);
                gTask.addValue(i, v.trueValue, currentLevel);
                ArrayList<Integer> domainValues = gTask
                        .getAllDomainValues(v.domainIndex);
                for (Integer value : domainValues) {
                    if (value != v.trueValue) {
                        pv = new ProgrammedValue(currentFalseValueIndex++,
                                v.varIndex, value);
                        falseValueReached.put(pv, true);
                        falseValuesByFunction.get(v.fncIndex).add(pv);
                        v.addFalseValue(gTask.objects.get(value),
                                gTask.objectIndex);
                    }
                }
            }
        }
    }

    /**
     * Initializes the operators to be grounded.
     *
     * @param task Parsed planning task
     * @since 1.0
     */
    @SuppressWarnings("unchecked")
    private void initOperators(Task task) {
        int numFnc = gTask.functions.size();
        opRequireFunction = new ArrayList[numFnc];
        for (int i = 0; i < numFnc; i++) {
            opRequireFunction[i] = new ArrayList<>();
        }
        Operator[] ops = task.getOperators();
        Operator[] b = task.getBeliefs();
        gOps = new OpGrounding[ops.length + b.length];
        for (int i = 0; i < ops.length; i++) {
            gOps[i] = new OpGrounding(ops[i], i, false);
        }
        for (int i = 0; i < b.length; i++) {
            gOps[i + ops.length] = new OpGrounding(b[i], i, true);
        }
    }

    /**
     * Grounds a numeric effect.
     *
     * @param a Action
     * @param op Operator
     * @since 1.0
     */
    private void groundActionNumericEffect(GroundedTaskImp.ActionImp a, OpGrounding op) {
        a.numEff = new GroundedNumericEff[op.numEff.length];
        int i = 0;
        for (NumericEffect e : op.numEff) {
            int type = e.getType();
            GroundedTaskImp.GroundedVarImp var = groundNumericVariable(e.getNumericVariable(), op);
            GroundedTaskImp.GroundedNumericExpressionImp exp = groundNumericExpression(e.getNumericExpression(), op);
            a.numEff[i++] = new GroundedTaskImp.GroundedNumericEffImp(type, var, exp);
        }
    }

    /**
     * Grounds a numeric variable.
     *
     * @param var Function to ground
     * @param op Operator
     * @return Grounded variable
     * @since 1.0
     */
    private GroundedVarImp groundNumericVariable(Function var, OpGrounding op) {
        int numParams = var.getParameters().length;
        GroundedTaskImp.GroundedVarImp gvar = gTask.new GroundedVarImp(var.getName(), numParams);
        int objIndex;
        for (int i = 0; i < numParams; i++) {
            Parameter param = var.getParameters()[i];
            if (param.getName().startsWith("?")) {
                int paramIndex = -1;
                for (int j = 0; j < op.numParams; j++) {
                    if (op.paramNames[j].equalsIgnoreCase(param.getName())) {
                        paramIndex = j;
                        break;
                    }
                }
                objIndex = op.paramValues[paramIndex].peek();
            } else {    // Constant
                objIndex = gTask.objectIndex.get(param.getName());
            }
            gvar.paramIndex[i] = objIndex;
        }
        int varIndex = gTask.numericVars.indexOf(gvar);
        if (varIndex >= 0) {
            return gTask.numericVars.get(varIndex);
        }
        return gTask.createNewNumericVariable(gvar);
    }

    /**
     * Grounds a numeric expression.
     *
     * @param exp Numeric expression
     * @param op Operator
     * @return Grounded numeric expression
     * @since 1.0
     */
    private GroundedTaskImp.GroundedNumericExpressionImp groundNumericExpression(NumericExpression exp, OpGrounding op) {
        int type = exp.getType();
        GroundedTaskImp.GroundedNumericExpressionImp res;
        switch (type) {
            case NumericExpression.NUMBER:
                res = new GroundedTaskImp.GroundedNumericExpressionImp(type, exp.getValue());
                break;
            case NumericExpression.VARIABLE:
                GroundedVarImp var = groundNumericVariable(exp.getNumericVariable(), op);
                res = new GroundedTaskImp.GroundedNumericExpressionImp(var);
                break;
            case NumericExpression.USAGE:
                res = new GroundedTaskImp.GroundedNumericExpressionImp(type);
                break;
            default:
                GroundedTaskImp.GroundedNumericExpressionImp left = groundNumericExpression(exp.getLeftExp(), op);
                GroundedTaskImp.GroundedNumericExpressionImp right = groundNumericExpression(exp.getRightExp(), op);
                res = new GroundedTaskImp.GroundedNumericExpressionImp(type, left, right);
        }
        return res;
    }

    /**
     * Check if an action has contradictory effects.
     *
     * @param a Action to check
     * @return <code>true</code>, if the action has contradictory effects;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    private boolean checkContradictoryEffects(GroundedTaskImp.ActionImp a) {
        int effIndex = 0;
        while (effIndex < a.eff.length - 1) {
            GroundedVar var = a.eff[effIndex].getVar();
            int effIndex2 = effIndex + 1;
            while (effIndex2 < a.eff.length) {
                if (var.equals(a.eff[effIndex2].getVar())) {
                    int remove;
                    String v1 = a.eff[effIndex].getValue();
                    String v2 = a.eff[effIndex2].getValue();
                    if (v1.equalsIgnoreCase(v2)) { // Redundant effect (duplicated)
                        remove = effIndex2;
                    } else { // Contradictory effects
                        if (!var.isBoolean()) {
                            return false;
                        }
                        remove = v1.equalsIgnoreCase("false") ? effIndex : effIndex2;
                    }
                    a.addMutexVariable(var);
                    ActionCondition v[] = new ActionCondition[a.eff.length - 1];
                    System.arraycopy(a.eff, 0, v, 0, remove);
                    for (int i = remove + 1; i < a.eff.length; i++) {
                        v[i - 1] = a.eff[i];
                    }
                    a.eff = v;
                    if (remove == effIndex) {
                        effIndex--;
                        break;
                    }
                } else {
                    effIndex2++;
                }
            }
            effIndex++;
        }
        return true;
    }

    /**
     * Class for operator conditions grounding.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    private class OpCondGrounding {

        int fncIndex;               // Function index
        int numParams;              // Number of parameters
        boolean paramConstant[];    // <code>true</code> if the function parameter is a constant
        int paramIndex[];           // Object index if the parameter is a constant,
        // otherwise the index of the operator parameter
        boolean constantValue;      // <code>true</code>  if the value is a constant
        int valueIndex;             // Object index if the value is a constant,
        // otherwise the index of the operator parameter
        boolean grounded;           // <code>true</code> if the precondition has been grounded

        /**
         * Initializes an operator condition.
         *
         * @param cond Condition
         * @param paramNames Name of the parameters
         * @since 1.0
         */
        public OpCondGrounding(Condition cond, String[] paramNames) {
            Function fnc = cond.getFunction();
            fncIndex = gTask.getFunctionIndex(fnc.getName());
            Parameter params[] = fnc.getParameters();
            numParams = params.length;
            if (fnc.isMultifunction()) {
                numParams++;
            }
            paramConstant = new boolean[numParams];
            paramIndex = new int[numParams];
            for (int i = 0; i < params.length; i++) {
                paramConstant[i] = !params[i].getName().startsWith("?");
                paramIndex[i] = getParamIndex(paramConstant[i],
                        params[i].getName(), paramNames);
            }
            if (fnc.isMultifunction()) {
                paramConstant[numParams - 1] = !cond.getValue().startsWith("?");
                paramIndex[numParams - 1] = getParamIndex(
                        paramConstant[numParams - 1], cond.getValue(),
                        paramNames);
                constantValue = true;
                valueIndex = gTask.getObjectIndex("true");
            } else {
                constantValue = !cond.getValue().startsWith("?");
                valueIndex = getParamIndex(constantValue, cond.getValue(),
                        paramNames);
            }
            grounded = false;
        }

        /**
         * Computes the parameter index.
         *
         * @param isConstant <code>true</code>, if the parameter is a defined
         * constant; <code>false</code>, it it is a variable
         * @param name Parameter name
         * @param paramNames Names of the operator parameters
         * @return Index of the parameter
         * @since 1.0
         */
        private int getParamIndex(boolean isConstant, String name,
                String[] paramNames) {
            if (isConstant) {
                return gTask.getObjectIndex(name);
            }
            int index = -1;
            for (int i = 0; i < paramNames.length && index == -1; i++) {
                if (paramNames[i].equalsIgnoreCase(name)) {
                    index = i;
                }
            }
            return index;
        }
    }

    /**
     * Class for operator grounding.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    private class OpGrounding {

        int opIndex;                    // Operator index
        String name;                    // Operator name
        String paramNames[];            // Names of the parametes
        int[][] paramTypes;             // Types of the parameters
        Deque<Integer>[] paramValues;   // Queue for grounding the operator parameters
        int numParams;                  // Number of parameters
        int numUngroundedTruePrecs;     // Number of ungrounded positive preconditions
        int numUngroundedFalsePrecs;    // Number of ungrounded negative preconditions
        int numTruePrec;                // Total number of positive preconditions
        int numFalsePrec;               // Total number of negative preconditions
        OpCondGrounding[] truePrec;     // Positive preconditions for grounding
        OpCondGrounding[] falsePrec;    // Negative preconditions for grounding
        OpCondGrounding[] eff;          // Effects for grounding
        boolean isRule;                 // <code>true</code>, if this operator is a belief rule
        int indexFirstValue;            // Index of the first value of the RPG used to ground this operator
        NumericEffect[] numEff;         // Array of numeric effects

        /**
         * Initializes a grounding operator.
         *
         * @param op Operator
         * @param opIndex Index of the operator
         * @param isRule <code>true</code>, if this operator is a belief rule;
         * <code>false</code>, if it is an operator
         * @since 1.0
         */
        @SuppressWarnings("unchecked")
        public OpGrounding(Operator op, int opIndex, boolean isRule) {
            this.opIndex = opIndex;
            this.isRule = isRule;
            name = op.getName();
            Parameter[] params = op.getParameters();
            numParams = params.length;
            paramNames = new String[numParams];
            paramTypes = new int[numParams][];
            paramValues = (Deque<Integer>[]) new Deque[numParams];
            for (int i = 0; i < params.length; i++) {
                paramNames[i] = params[i].getName();
                String types[] = params[i].getTypes();
                paramTypes[i] = new int[types.length];
                for (int j = 0; j < types.length; j++) {
                    paramTypes[i][j] = gTask.getTypeIndex(types[j]);
                }
                paramValues[i] = new java.util.ArrayDeque<>();
            }
            numTruePrec = numFalsePrec = 0;
            for (int i = 0; i < op.getPrecondition().length; i++) {
                Condition c = op.getPrecondition()[i];
                if (c.getType() == Condition.EQUAL
                        || c.getType() == Condition.MEMBER) {
                    numTruePrec++;
                } else {
                    numFalsePrec++;
                }
            }
            numUngroundedTruePrecs = numTruePrec;
            numUngroundedFalsePrecs = numFalsePrec;
            truePrec = new OpCondGrounding[numTruePrec];
            falsePrec = new OpCondGrounding[numFalsePrec];
            eff = new OpCondGrounding[op.getEffect().length];
            int nt = 0, nf = 0;
            for (int i = 0; i < op.getPrecondition().length; i++) {
                Condition c = op.getPrecondition()[i];
                if (c.getType() == Condition.EQUAL
                        || c.getType() == Condition.MEMBER) {
                    truePrec[nt] = new OpCondGrounding(c, paramNames);
                    setFunctionUsage(truePrec[nt++]);
                } else {
                    falsePrec[nf++] = new OpCondGrounding(c, paramNames);
                }
            }
            for (int i = 0; i < eff.length; i++) {
                eff[i] = new OpCondGrounding(op.getEffect()[i], paramNames);
            }
            numEff = op.getNumericEffects();
        }

        /**
         * Unstacks the current parameter values.
         *
         * @param precIndex Precondition index
         * @param isTrue <code>true</code>, if it is a positive precondition;
         * <code>false</code>, it it is negative
         * @since 1.0
         */
        public void unstackParameters(int precIndex, boolean isTrue) {
            OpCondGrounding p = isTrue ? truePrec[precIndex]
                    : falsePrec[precIndex];
            for (int i = 0; i < numParams; i++) {
                paramValues[i].pop();
            }
            p.grounded = false;
            if (isTrue) {
                numUngroundedTruePrecs++;
            } else {
                numUngroundedFalsePrecs++;
            }
        }

        /**
         * Stacks the matched parameter values.
         *
         * @param precIndex Precondition index
         * @param v Grounded variable
         * @param valueIndex Value index
         * @param isTrue <code>true</code>, if it is a positive precondition;
         * <code>false</code>, it it is negative
         * @return <code>true</code>, if it is possible; <code>false</code>,
         * otherwise
         * @since 1.0
         */
        public boolean stackParameters(int precIndex,
                GroundedTaskImp.GroundedVarImp v, int valueIndex, boolean isTrue) {
            OpCondGrounding p = isTrue ? truePrec[precIndex]
                    : falsePrec[precIndex];
            int currentParams[] = new int[numParams];
            for (int i = 0; i < numParams; i++) {
                currentParams[i] = paramValues[i].isEmpty() ? -1
                        : paramValues[i].peek();
            }
            int objIndex, paramIndex;
            for (int i = 0; i < p.numParams; i++) {
                if (!p.paramConstant[i]) {
                    paramIndex = p.paramIndex[i];
                    objIndex = currentParams[paramIndex];
                    if (objIndex == -1) {
                        currentParams[paramIndex] = v.paramIndex[i];
                    } else if (v.paramIndex[i] != objIndex) {
                        return false;
                    }
                }
            }
            if (!p.constantValue) {
                paramIndex = p.valueIndex;
                objIndex = currentParams[paramIndex];
                if (objIndex == -1) {
                    currentParams[paramIndex] = valueIndex;
                } else if (valueIndex != objIndex) {
                    return false;
                }
            }
            for (int i = 0; i < numParams; i++) {
                paramValues[i].push(currentParams[i]);
            }
            p.grounded = true;
            if (isTrue) {
                numUngroundedTruePrecs--;
            } else {
                numUngroundedFalsePrecs--;
            }
            return true;
        }

        /**
         * Checks if a given pair (variable,value) matches an operator
         * precondition.
         *
         * @param v Grounded variable
         * @param valueIndex Value index
         * @param startPrec Precondition index
         * @return <code>true</code>, if it matches the precondition;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        public int matches(GroundedTaskImp.GroundedVarImp v, int valueIndex,
                int startPrec) {
            int precIndex = -1;
            OpCondGrounding p;
            for (int i = startPrec; i < numTruePrec; i++) {
                p = truePrec[i];
                if (!p.grounded && p.fncIndex == v.fncIndex
                        && precMatches(p, v, valueIndex)) {
                    precIndex = i;
                    break;
                }
            }
            return precIndex;
        }

        /**
         * Checks if a positive precondition matches a pair (variable, value).
         *
         * @param p Precondition
         * @param v Grounded variable
         * @param valueIndex Value index
         * @return <code>true</code>, if it matches the precondition;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        public boolean precMatches(OpCondGrounding p,
                GroundedTaskImp.GroundedVarImp v, int valueIndex) {
            boolean matches = true;
            int paramIndex, objIndex;
            for (int i = 0; i < p.numParams && matches; i++) { // Check the parameters
                paramIndex = p.paramIndex[i];
                if (p.paramConstant[i]) {
                    matches = paramIndex == v.paramIndex[i];
                } else {
                    objIndex = paramValues[paramIndex].isEmpty() ? -1
                            : paramValues[paramIndex].peek();
                    if (objIndex == -1) { // Ungrounded parameter, types should match
                        matches = gTask.objectIsCompatible(v.paramIndex[i],
                                paramTypes[paramIndex]);
                    } else { // Grounded parameter, objects must coincide
                        matches = objIndex == v.paramIndex[i];
                    }
                }
            }
            if (matches) { // Check the value
                if (p.constantValue) {
                    matches = valueIndex == p.valueIndex;
                } else {
                    paramIndex = p.valueIndex;
                    objIndex = paramValues[paramIndex].isEmpty() ? -1
                            : paramValues[paramIndex].peek();
                    if (objIndex == -1) { // Ungrounded parameter, types should
                        // match
                        matches = gTask.objectIsCompatible(valueIndex,
                                paramTypes[paramIndex]);
                    } else { // Grounded parameter, objects must coincide
                        matches = objIndex == valueIndex;
                    }
                }
            }
            return matches;
        }

        /**
         * Checks if a negative precondition matches a pair (variable, value).
         *
         * @param p Precondition
         * @param v Grounded variable
         * @param valueIndex Value index
         * @return <code>true</code>, if it matches the precondition;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        public boolean negPrecMatches(OpCondGrounding p,
                GroundedTaskImp.GroundedVarImp v, int valueIndex) {
            boolean matches = true;
            int paramIndex, objIndex;
            for (int i = 0; i < p.numParams && matches; i++) { // Check the parameters
                paramIndex = p.paramIndex[i];
                if (p.paramConstant[i]) {
                    matches = paramIndex == v.paramIndex[i];
                } else {
                    objIndex = paramValues[paramIndex].isEmpty() ? -1
                            : paramValues[paramIndex].peek();
                    if (objIndex == -1) { // Ungrounded parameter, types should match
                        matches = gTask.objectIsCompatible(v.paramIndex[i],
                                paramTypes[paramIndex]);
                    } else { // Grounded parameter, objects must coincide
                        matches = objIndex == v.paramIndex[i];
                    }
                }
            }
            if (matches) { // Check the value
                if (p.constantValue) {
                    matches = valueIndex != p.valueIndex;
                } else {
                    paramIndex = p.valueIndex;
                    objIndex = paramValues[paramIndex].isEmpty() ? -1
                            : paramValues[paramIndex].peek();
                    if (objIndex == -1) { // Ungrounded parameter, types should match
                        matches = gTask.objectIsCompatible(valueIndex,
                                paramTypes[paramIndex]);
                    } else { // Grounded parameter, objects must differ
                        matches = objIndex != valueIndex;
                    }
                }
            }
            return matches;
        }

        /**
         * States that the function is used by this operator.
         *
         * @param cond Condition
         * @since 1.0
         */
        private void setFunctionUsage(OpCondGrounding cond) {
            ArrayList<OpGrounding> opList = opRequireFunction[cond.fncIndex];
            if (!opList.contains(this)) {
                opList.add(this);
            }
        }

        /**
         * Compares two operators by their indexes.
         *
         * @param op Another operator
         * @return <code>true</code>, if both operators have the same index;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object op) {
            return opIndex == ((OpGrounding) op).opIndex;
        }

        /**
         * Returns a description of this operator.
         *
         * @return Operator description
         * @since 1.0
         */
        @Override
        public String toString() {
            String res = name;
            for (int i = 0; i < numParams; i++) {
                int objIndex = paramValues[i].isEmpty() ? -1 : paramValues[i]
                        .peek();
                if (objIndex == -1) {
                    res += " " + paramNames[i];
                } else {
                    res += " " + gTask.objects.get(objIndex);
                }
            }
            return res;
        }
    }

    /**
     * Pair (variable,value) for the RPG construction.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    public class ProgrammedValue {

        int index;          // Programmed value index
        int varIndex;       // Variable index
        int valueIndex;     // Value index

        /**
         * Creates a pair (variable, value)
         *
         * @param index Programmed value index
         * @param varIndex Variable index
         * @param value Value index
         * @since 1.0
         */
        public ProgrammedValue(int index, int varIndex, int value) {
            this.index = index;
            this.varIndex = varIndex;
            this.valueIndex = value;
        }

        /**
         * Check if two pairs are equal.
         *
         * @param x Another pair
         * @return <code>true</code>, if both pairs are equal;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            ProgrammedValue v = (ProgrammedValue) x;
            return varIndex == v.varIndex && valueIndex == v.valueIndex;
        }

        /**
         * Returns a hash code for this pair.
         * 
         * @return Hash code
         * @since 1.0
         */
        @Override
        public int hashCode() {
            return varIndex * 131071 + valueIndex;
        }
    }
}
