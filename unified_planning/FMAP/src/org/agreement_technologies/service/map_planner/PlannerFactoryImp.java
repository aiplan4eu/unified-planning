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
import java.util.Hashtable;
import java.util.Map.Entry;
import java.util.Set;
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_communication.PlanningAgentListener;
import org.agreement_technologies.common.map_grounding.Action;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedEff;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.GroundedVar;
import org.agreement_technologies.common.map_heuristic.Heuristic;
import org.agreement_technologies.common.map_negotiation.NegotiationFactory;
import org.agreement_technologies.common.map_planner.CausalLink;
import org.agreement_technologies.common.map_planner.Condition;
import org.agreement_technologies.common.map_planner.ExtendedPlanner;
import org.agreement_technologies.common.map_planner.OpenCondition;
import org.agreement_technologies.common.map_planner.Ordering;
import org.agreement_technologies.common.map_planner.Planner;
import org.agreement_technologies.common.map_planner.PlannerFactory;
import org.agreement_technologies.common.map_planner.Step;
import org.agreement_technologies.service.map_negotiation.NegotiationFactoryImp;
import org.agreement_technologies.service.tools.CustomArrayList;

/**
 * Configuration class; from the grounded task, it builds the objects necessary
 * for the planner to work.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class PlannerFactoryImp extends PlannerFactory {

    public static final int EQUAL = 1;      // Equal condition
    public static final int DISTINCT = 2;   // Distinct condition

    private ArrayList<OpenCondition> openConditions;    // List of open condtions
    private ArrayList<POPPrecEff> goals;                // List of task goals
    private String myAgent;                             // Name of this agent
    private ExtendedPlanner planner;                    // Planner
    private GroundedTask task;                          // Grounded tasl
    private ArrayList<POPPrecEff> initialState;         // Initial state (list of facts)
    private ArrayList<POPFunction> functions;           // List of variables
    private ArrayList<POPAction> actions;               // List of actions
    private Hashtable<String, POPFunction> hashVars;    // Mapping: variable name -> variable
    private Hashtable<String, POPPrecEff> hashPrecEffs; // Mapping: condition description -> condition
    // For each variable, list of actions that have that variable in their preconditions
    private Hashtable<String, ArrayList<InternalAction>> hashRequirers;
    private GroundedEff[] groundedInitialState;         // Grounded initial state (array of facts)
    private int totalThreads;                           // Amount of available threads
    private NegotiationFactory negotiationFactory;      // Negotiation factory
    private SolutionChecker solutionChecker;            // Solution checker
    private int numGlobalVariables;                     // Number of global variables
    // Mapping: variable name -> global index
    private Hashtable<String, Integer> hashGlobalIndexesVarCode;
    // Mapping: value name -> global index
    private Hashtable<String, Integer> hashGlobalIndexesValueCode;
    // Mapping: global index -> variable name 
    private Hashtable<Integer, String> hashGlobalIndexesCodeVar;
    // Mapping: global index -> value name 
    private Hashtable<Integer, String> hashGlobalIndexesCodeValue;

    /**
     * Creates a new planner factory.
     *
     * @param task Grounded task
     * @param comm Communication utility
     * @since 1.0
     */
    public PlannerFactoryImp(GroundedTask task, AgentCommunication comm) {
        Hashtable<String, InternalCondition> hashPrecEffs = new Hashtable<>();
        ArrayList<InternalCondition> goals = new ArrayList<>();
        ArrayList<InternalCondition> initialState = new ArrayList<>();
        ArrayList<InternalOpenCondition> openConditions = new ArrayList<>();
        ArrayList<InternalAction> actions = new ArrayList<>();
        initializeParameters(task, hashPrecEffs, goals, initialState,
                openConditions, actions);
        assignGlobalIndexes(comm);
        translateDataToAttributes(hashPrecEffs, goals, initialState,
                openConditions, actions);
    }
    
    /**
     * Gets the number of available threads.
     *
     * @return Number of threads
     * @since 1.0
     */
    public int getTotalThreads() {
        return totalThreads;
    }

    /**
     * Gets the number of global variables.
     *
     * @return Number of global variables
     * @since 1.0
     */
    public int getNumGlobalVariables() {
        return numGlobalVariables;
    }

    /**
     * Stores the needed data.
     *
     * @param hashPrecEffs Mapping: condition description -> condition
     * @param goals List of task goals
     * @param initialState Initial state (list of facts)
     * @param openConditions List of open conditions
     * @param actions List of action
     */
    private void translateDataToAttributes(
            Hashtable<String, InternalCondition> hashPrecEffs,
            ArrayList<InternalCondition> goals,
            ArrayList<InternalCondition> initialState,
            ArrayList<InternalOpenCondition> openConditions,
            ArrayList<InternalAction> actions) {
        this.hashPrecEffs = new Hashtable<>(hashPrecEffs.size());
        Set<String> keys = hashPrecEffs.keySet();
        for (String key : keys) {
            InternalCondition condition = hashPrecEffs.get(key);
            POPPrecEff eff = condition.toPOPPrecEff(this);
            this.hashPrecEffs.put(eff.toKey(), eff);
        }
        this.goals = new ArrayList<>(goals.size());
        for (InternalCondition c : goals) {
            this.goals.add(c.toPOPPrecEff(this));
        }
        this.initialState = new ArrayList<>(initialState.size());
        for (InternalCondition c : initialState) {
            this.initialState.add(c.toPOPPrecEff(this));
        }
        this.openConditions = new ArrayList<>(
                openConditions.size());
        for (InternalOpenCondition c : openConditions) {
            this.openConditions.add(c.toPOPPrecEff(this));
        }
        this.actions = new ArrayList<>(actions.size());
        for (InternalAction a : actions) {
            this.actions.add(a.toPOPAction(this));
        }
    }

    /**
     * Gets the negotiation factory.
     *
     * @return Negotiation factory
     * @since 1.0
     */
    public NegotiationFactory getNegotiationFactory() {
        return negotiationFactory;
    }

    /**
     * Gets the solution checker.
     *
     * @return Solution checker
     * @since 1.0
     */
    public SolutionChecker getSolutionChecker() {
        return solutionChecker;
    }

    /**
     * Gets the list of actions.
     *
     * @return Actions list
     * @since 1.0
     */
    public ArrayList<POPAction> getActions() {
        return this.actions;
    }

    /**
     * Gets the name of this agent.
     *
     * @return This agent's name
     * @since 1.0
     */
    public String getAgent() {
        return myAgent;
    }

    /**
     * Gets the grounded task.
     *
     * @return Grounded task
     * @since 1.0
     */
    public GroundedTask getGroundedTask() {
        return this.task;
    }

    /**
     * Initializes the needed data.
     *
     * @param gTask Grounded task
     * @param hashPrecEffs Mapping: condition description -> condition
     * @param goals List of goals
     * @param initialState Initial state (list of facts)
     * @param openConditions List of open condition
     * @param actions List of action
     * @since 1.0
     */
    private void initializeParameters(GroundedTask gTask,
            Hashtable<String, InternalCondition> hashPrecEffs,
            ArrayList<InternalCondition> goals,
            ArrayList<InternalCondition> initialState,
            ArrayList<InternalOpenCondition> openConditions,
            ArrayList<InternalAction> actions) {
        int i, j;
        POPFunction func;
        InternalCondition pe;
        GroundedCond prec;
        GroundedEff eff;
        InternalAction act;
        ArrayList<InternalCondition> precs;
        ArrayList<InternalCondition> effs;
        String key;
        ArrayList<GroundedCond> groundedGoals;
        ArrayList<InternalAction> requirers;
        CustomArrayList<InternalCondition> effects;

        this.task = gTask;
        this.myAgent = this.task.getAgentName();
        this.hashVars = new Hashtable<>(gTask.getVars().length);
        this.functions = new ArrayList<>();
        effects = new CustomArrayList<>();
        groundedGoals = new ArrayList<>();

        // Process the variables and create the POPFunctions
        for (i = 0; i < gTask.getVars().length; i++) {
            func = new POPFunction(gTask.getVars()[i]);
            this.functions.add(func);
            this.hashVars.put(func.toKey(), func);
        }

        // Process the actions and buld the POPPrecEffs and POPActions
        for (i = 0; i < gTask.getActions().size(); i++) {
            precs = new ArrayList<InternalCondition>();
            effs = new ArrayList<InternalCondition>();
            Action action = gTask.getActions().get(i);
            // Procesamos las precondiciones de la accion
            for (j = 0; j < action.getPrecs().length; j++) {
                prec = action.getPrecs()[j];
                key = groundedCondToKey(prec);
                // Si la precondiciÃ³n no existe aÃºn, la creamos
                if (hashPrecEffs.get(key) == null) {
                    // agents = this.getAgents(prec.getVar(), prec.getValue());
                    pe = new InternalCondition(prec, this.hashVars.get(this
                            .groundedVarToKey(prec.getVar())), prec.getValue(),
                            prec.getCondition());
                    // , prec.getVar().getMinTime(prec.getValue()), agents, 0);
                    hashPrecEffs.put(key, pe);
                    precs.add(pe);
                } // Si no, la buscamos y la guardamos en la lista de
                // precondiciones
                else {
                    pe = hashPrecEffs.get(key);
                    precs.add(pe);
                    if (pe.prec == null) {
                        pe.prec = prec;
                    }
                }
            }
            // Process the action effects
            for (j = 0; j < action.getEffs().length; j++) {
                eff = action.getEffs()[j];
                key = groundedEffToKey(eff);

                if (hashPrecEffs.get(key) == null) {
                    pe = new InternalCondition(gTask.createGroundedCondition(
                            EQUAL, eff.getVar(), eff.getValue()),
                            this.hashVars.get(this.groundedVarToKey(eff
                                    .getVar())), eff.getValue(), EQUAL);
                    hashPrecEffs.put(key, pe);
                    effects.addNotRepeated(pe);
                    effs.add(pe);
                } else {
                    pe = hashPrecEffs.get(key);
                    effs.add(pe);
                    effects.addNotRepeated(pe);
                }
            }
            // Create the action
            act = new InternalAction(gTask.getActions().get(i), precs, effs);
            actions.add(act);
        }
        // Create the goals and the first open conditions
        for (GroundedCond c : gTask.getGlobalGoals()) {
            groundedGoals.add(c);
        }
        for (GroundedCond c : groundedGoals) {
            key = groundedCondToKey(c);
            if (hashPrecEffs.get(key) == null) {
                pe = new InternalCondition(c, this.hashVars.get(this
                        .groundedVarToKey(c.getVar())), c.getValue(),
                        c.getCondition());
                hashPrecEffs.put(key, pe);
                openConditions
                        .add(new InternalOpenCondition(pe, null, false/* , null */));
            } else {
                openConditions.add(new InternalOpenCondition(hashPrecEffs
                        .get(key), null, false));
            }
        }
        // Generate the POPPrecEff corresponding to the initial state
        for (POPFunction f : this.functions) {
            if (f.getInitialTrueValue() != null) {
                key = f.toKey() + " = " + f.getInitialTrueValue();
                if (hashPrecEffs.get(key) == null) {
                    pe = new InternalCondition(gTask.createGroundedCondition(
                            EQUAL, f.getVariable(), f.getInitialTrueValue()),
                            f, f.getInitialTrueValue(), EQUAL);
                    initialState.add(pe);
                    effects.addNotRepeated(pe);
                    hashPrecEffs.put(pe.toKey(), pe);
                } else {
                    initialState.add(hashPrecEffs.get(key));
                }
            } else {
                boolean valueReceived = false;
                GroundedVar v = f.getVariable();
                for (String value : v.getReachableValues()) {
                    if (v.getMinTime(value) == 0) {
                        valueReceived = true;
                        key = f.toKey() + " = " + value;
                        if (hashPrecEffs.get(key) == null) {
                            pe = new InternalCondition(
                                    gTask.createGroundedCondition(EQUAL,
                                            f.getVariable(), value), f, value,
                                    EQUAL); // ,
                            initialState.add(pe);
                            effects.addNotRepeated(pe);
                            hashPrecEffs.put(pe.toKey(), pe);
                        } else {
                            initialState.add(hashPrecEffs.get(key));
                        }
                        break;
                    }
                }
                // Generate the special effects of type DISTINCT, corresponding
                // to the facts in the initial step which does not have an 
                // initial true value
                if (!valueReceived) {
                    for (i = 0; i < f.getInitialFalseValues().size(); i++) {
                        pe = new InternalCondition(
                                gTask.createGroundedCondition(EQUAL,
                                        f.getVariable(), null), f, f
                                .getInitialFalseValues().get(i),
                                DISTINCT);
                        initialState.add(pe);
                        hashPrecEffs.put(pe.toKey(), pe);
                    }
                }
            }
        }

        ArrayList<GroundedEff> initialStateEffs = new ArrayList<>();
        for (InternalCondition ppe : initialState) {
            initialStateEffs.add(this.task.createGroundedEffect(
                    ppe.prec.getVar(), ppe.prec.getValue()));
        }
        this.groundedInitialState = new GroundedEff[initialStateEffs.size()];
        initialStateEffs.toArray(this.groundedInitialState);

        // Store the preconditions of the final step
        for (InternalOpenCondition oc : openConditions) {
            goals.add(oc.condition);
        }

        for (i = 0; i < effects.size(); i++) {
            effects.get(i).setIndex(i);
        }

        // For each grounded effect, provides the actions that require it as a precondition
        this.hashRequirers = new Hashtable<>();
        for (String spe : hashPrecEffs.keySet()) {
            pe = hashPrecEffs.get(spe);
            requirers = new ArrayList<>();
            for (InternalAction ac : actions) {
                for (InternalCondition pre : ac.precs) {
                    if (pre.toKey().equals(pe.toKey())) {
                        requirers.add(ac);
                    }
                }
            }
            this.hashRequirers.put(pe.toKey(), requirers);
        }
    }

    /**
     * Gets the global identifier of a variable from its string key.
     *
     * @param var String key of a variable
     * @return Global identifier of the variable; -1 if the variable is not in
     * the agent's domain
     * @since 1.0
     */
    @Override
    public int getCodeFromVarName(String var) {
        Integer code = this.hashGlobalIndexesVarCode.get(var);
        return code != null ? code : -1;
    }

    /**
     * Gets the string key of a variable from its global identifier.
     *
     * @param code Global identifier of a variable
     * @return String key of the variable; null if the variable is not in the
     * agent's domain
     * @since 1.0
     */
    @Override
    public String getVarNameFromCode(int code) {
        return hashGlobalIndexesCodeVar.get(code);
    }

    /**
     * Gets the global identifier of a variable.
     *
     * @param var variable
     * @return Global identifier of the variable; -1 if the variable is not in
     * the agent's domain
     * @since 1.0
     */
    @Override
    public int getCodeFromVar(GroundedVar var) {
        return getCodeFromVarName(var.toString());
    }

    /**
     * Gets the global identifier of a value.
     *
     * @param val Value
     * @return Global identifier of the value; -1 if the value is not in the
     * agent's domain
     * @since 1.0
     */
    @Override
    public int getCodeFromValue(String val) {
        Integer code = this.hashGlobalIndexesValueCode.get(val);
        return code != null ? code : -1;
    }

    /**
     * Gets a value from its global identifier.
     *
     * @param code Global identifier of a value
     * @return Value; <code>null</code>, if the value is not in the agent's
     * domain
     * @since 1.0
     */
    @Override
    public String getValueFromCode(int code) {
        return this.hashGlobalIndexesCodeValue.get(code);
    }

    /**
     * Agents set a global index for each variable and value. Non-visible vars
     * and values are encoded through their global index.
     *
     * @param comm Agent communication object
     * @since 1.0
     */
    private void assignGlobalIndexes(AgentCommunication comm) {
        int globalIdVars = 0, globalIdValues = 0, iter = 0;
        boolean found;

        // Hash tables that contain the global indexes for variables and fluents
        this.hashGlobalIndexesVarCode = new Hashtable<>();
        this.hashGlobalIndexesValueCode = new Hashtable<>();
        this.hashGlobalIndexesCodeVar = new Hashtable<>();
        this.hashGlobalIndexesCodeValue = new Hashtable<>();

        ArrayList<ArrayList<GlobalIndexVarValueInfo>> globalIndexesToSend = new ArrayList<>();

        //Iterate until all the agents have played the role of baton agent once
        while (iter < comm.getAgentList().size()) {
            // Baton agent
            if (comm.batonAgent()) {
                //Assign a global index to the values that do not have one already
                for (String val : this.task.getObjects()) {
                    if (this.hashGlobalIndexesValueCode.get(val) == null) {
                        this.hashGlobalIndexesValueCode.put(val, globalIdValues);
                        this.hashGlobalIndexesCodeValue.put(globalIdValues, val);
                        globalIdValues++;
                    }
                }
                //Assign a global index to the vars that do not have one already
                for (GroundedVar var : this.task.getVars()) {
                    String name = var.toString();
                    if (this.hashGlobalIndexesVarCode.get(name) == null) {
                        this.hashGlobalIndexesVarCode.put(name, globalIdVars);
                        this.hashGlobalIndexesCodeVar.put(globalIdVars, name);
                        globalIdVars++;
                    }
                }
                //Prepare the message
                ArrayList<GlobalIndexVarValueInfo> vars = new ArrayList<>(),
                        values = new ArrayList<>();
                for (Entry<Integer, String> e : this.hashGlobalIndexesCodeVar.entrySet()) {
                    vars.add(new GlobalIndexVarValueInfo(e.getKey(), e.getValue()));
                }
                for (Entry<Integer, String> e : this.hashGlobalIndexesCodeValue.entrySet()) {
                    values.add(new GlobalIndexVarValueInfo(e.getKey(), e.getValue()));
                }
                globalIndexesToSend.add(vars);
                globalIndexesToSend.add(values);
                //Send vars and values to the rest of agents
                comm.sendMessage(new MessageContentEncodedVarsValues(globalIndexesToSend, globalIdVars, globalIdValues), false);
            } // Non-baton agent
            else {
                // Receive baton agent's global indexes
                MessageContentEncodedVarsValues msg = (MessageContentEncodedVarsValues) comm.receiveMessage(comm.getBatonAgent(), false);
                // Update globalIds
                globalIdVars = msg.getCurrentGlobalIndexVars();
                globalIdValues = msg.getCurrentGlobalIndexValues();

                // Add global indexes to the agent's hash tables
                ArrayList<ArrayList<GlobalIndexVarValueInfo>> indexes = msg.getGlobalIndexes();
                //Add vars info (indexes[0])
                for (GlobalIndexVarValueInfo var : indexes.get(0)) {
                    if (this.hashVars.get(var.getItem()) != null) {
                        if (this.hashGlobalIndexesVarCode.get(var.getItem()) == null) {
                            this.hashGlobalIndexesVarCode.put(var.getItem(), var.getGlobalIndex());
                            this.hashGlobalIndexesCodeVar.put(var.getGlobalIndex(), var.getItem());
                        }
                    }
                }
                //Add values info (indexes[1])
                for (GlobalIndexVarValueInfo val : indexes.get(1)) {
                    //Check if the agent knows the value
                    found = false;
                    for (String s : this.task.getObjects()) {
                        if (s.equals(val.getItem())) {
                            found = true;
                            break;
                        }
                    }
                    //Store the global index if the agent knows the value
                    if (found) {
                        if (this.hashGlobalIndexesValueCode.get(val.getItem()) == null) {
                            this.hashGlobalIndexesValueCode.put(val.getItem(), val.getGlobalIndex());
                            this.hashGlobalIndexesCodeValue.put(val.getGlobalIndex(), val.getItem());
                        }
                    }
                }
            }
            comm.passBaton();
            iter++;
        }
        numGlobalVariables = globalIdVars;
    }

    /**
     * Gets the key identifier for a grounded variable.
     *
     * @param v Grounded variable
     * @return Key identifier
     * @since 1.0
     */
    private String groundedVarToKey(GroundedVar v) {
        String res = v.getFuctionName();
        for (String s : v.getParams()) {
            res += " " + s;
        }
        return res;
    }

    /**
     * Gets the key identifier for a grounded condition.
     *
     * @param v Grounded condition
     * @return Key identifier
     * @since 1.0
     */
    private String groundedCondToKey(GroundedCond c) {
        String res = "(" + groundedVarToKey(c.getVar());
        if (c.getCondition() == EQUAL) {
            res += ") = ";
        }
        if (c.getCondition() == DISTINCT) {
            res += ") <> ";
        }
        return res + c.getValue();
    }

    /**
     * Gets the key identifier for a grounded effect.
     *
     * @param v Grounded effect
     * @return Key identifier
     * @since 1.0
     */
    private String groundedEffToKey(GroundedEff e) {
        String res;
        int n = 0;
        res = e.getVar().getFuctionName() + "(";
        for (String s : e.getVar().getParams()) {
            if (n == 0) {
                n++;
            } else {
                res += ", ";
            }
            res += s;
        }
        res += ") = ";
        res += e.getValue();

        return res;
    }

    /**
     * Creates a new plan ordering.
     *
     * @param stepIndex1 Index of the first plan step
     * @param stepIndex2 Index of the second plan step
     * @return New ordering
     * @since 1.0
     */
    @Override
    public Ordering createOrdering(int stepIndex1, int stepIndex2) {
        return new POPOrdering(stepIndex1, stepIndex2);
    }

    /**
     * Builds a new causal link.
     *
     * @param condition Grounded condition
     * @param step1 First plan step
     * @param step2 Second plan step
     * @return New causal link
     * @since 1.0
     */
    @Override
    public CausalLink createCausalLink(Condition condition, Step step1,
            Step step2) {
        POPPrecEff cond = this.condToPrecEff(condition);
        return new POPCausalLink((POPStep) step1, cond, (POPStep) step2);
    }

    /**
     * Translate a condition to a POPPrecEff.
     *
     * @param condition Condition
     * @return Translate condition into a POPPrecEff
     * @since 1.0
     */
    private POPPrecEff condToPrecEff(Condition condition) {
        String value = getValueFromCode(condition.getValueCode());
        String varName = getVarNameFromCode(condition.getVarCode());
        POPFunction f = null;
        if (varName != null) {
            GroundedVar gv = task.getVarByName(varName);
            if (gv != null) {
                f = new POPFunction(gv);
            }
        }
        if (value == null) {
            value = "?";
        }
        return new POPPrecEff(condition, f, value, condition.getType());
    }

    /**
     * Creates a new step
     *
     * @param stepIndex	Step index in the plan
     * @param agent	Executor agent
     * @param actionName Action name
     * @param prec	Array of preconditions
     * @param eff	Array of effects
     * @return New plan step
     * @since 1.0
     */
    @Override
    public Step createStep(int stepIndex, String agent, String actionName,
            Condition[] prec, Condition[] eff) {
        ArrayList<POPPrecEff> precs = new ArrayList<>();
        ArrayList<POPPrecEff> effs = new ArrayList<>();
        for (Condition c : prec) {
            precs.add(condToPrecEff(c));
        }
        for (Condition c : eff) {
            effs.add(condToPrecEff(c));
        }
        POPAction a = new POPAction(actionName, precs, effs);
        return new POPStep(a, stepIndex, agent);
    }

    /**
     * Synchronizes an array of steps.
     *
     * @param st Array of steps
     * @since 1.0
     */
    public void synchronizeStep(Step st) {
        int j;
        POPStep stp;

        stp = (POPStep) st;
        if (stp.getAction().getPrecs() != null) {
            for (j = 0; j < stp.getAction().getPrecs().size(); j++) {
                if (this.hashPrecEffs.get(stp.getAction().getPrecs().get(j)
                        .toKey()) != null) {
                    stp.getAction()
                            .getPrecs()
                            .set(j,
                                    this.hashPrecEffs.get(stp.getAction()
                                            .getPrecs().get(j).toKey()));
                } else if (this.hashVars.get(stp.getAction().getPrecs().get(j)
                        .getFunction().toKey()) != null) {
                    stp.getAction()
                            .getPrecs()
                            .get(j)
                            .setFunction(
                                    this.hashVars.get(stp.getAction()
                                            .getPrecs().get(j).getFunction()
                                            .toKey()));
                }
            }
        }
        if (stp.getAction().getEffects() != null) {
            for (j = 0; j < stp.getAction().getEffects().size(); j++) {
                if (this.hashPrecEffs.get(stp.getAction().getEffects().get(j)
                        .toKey()) != null) {
                    stp.getAction()
                            .getEffects()
                            .set(j,
                                    this.hashPrecEffs.get(stp.getAction()
                                            .getEffects().get(j).toKey()));
                } else if (this.hashVars.get(stp.getAction().getEffects().get(j)
                        .getFunction().toKey()) != null) {
                    stp.getAction()
                            .getEffects()
                            .get(j)
                            .setFunction(
                                    this.hashVars.get(stp.getAction()
                                            .getEffects().get(j).getFunction()
                                            .toKey()));
                }
            }
        }
    }

    /**
     * Creates a new planner.
     *
     * @param gTask Grounded task
     * @param h Heuristic function
     * @param comm Communications object
     * @param agentListener Agent listener
     * @param searchType Search method
     * @return New planner
     * @since 1.0
     */
    @Override
    public Planner createPlanner(GroundedTask gTask, Heuristic h,
            AgentCommunication comm, PlanningAgentListener agentListener,
            int searchType) {
        ArrayList<POPPrecEff> precs = new ArrayList<>();
        for (POPPrecEff p : goals) {
            precs.add(p);
        }
        String[] params = new String[0];
        Action a = task.createAction("Initial", params, new GroundedCond[0],
                groundedInitialState);
        POPAction pa = new POPAction(a, new ArrayList<POPPrecEff>(),
                initialState);
        POPStep initial = new POPStep(pa, 0, null);
        ArrayList<GroundedCond> goalsArray = task.getGlobalGoals();
        a = task.createAction("Final", params,
                goalsArray.toArray(new GroundedCond[goalsArray.size()]),
                new GroundedEff[0]);
        pa = new POPAction(a, precs, null);
        POPStep last = new POPStep(pa, 1, null);
        for (OpenCondition oc : openConditions) {
            if (oc.getStep() == null) {
                ((POPOpenCondition) oc).setStep(last);
            }
        }

        this.totalThreads = java.lang.Runtime.getRuntime()
                .availableProcessors() / comm.numAgents();
        if (totalThreads <= 0) {
            totalThreads = 1;
        }
        if (agentListener != null) {
            agentListener.trace(0, "Using " + totalThreads
                    + " thread(s) per agent");
        }

        negotiationFactory = new NegotiationFactoryImp(NegotiationFactory.COOPERATIVE);
        // Solution checker intitialization
        switch (negotiationFactory.getNegotiationType()) {
            case NegotiationFactory.BORDA:
                solutionChecker = new POPSolutionCheckerPrivateGoals(comm, task);
                break;
            default:
                solutionChecker = new POPSolutionCheckerCooperative();
        }

        if (totalThreads == 1) {
            this.planner = new POP(this, initial, last, openConditions, h,
                    comm, agentListener, searchType);
        } else {
            this.planner = new POPMultiThread(this, initial, last,
                    openConditions, h, comm, agentListener, searchType);
        }
        return this.planner;
    }

    /**
     * InternalCondition is a internal class to store conditions.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    private static class InternalCondition {

        GroundedCond prec;          // Original grounded condition
        POPFunction popFunction;    // Variable
        String value;               // Value
        int condition;              // Condition type (EQUAL or DISTINCT)
        int index;                  // Condition index

        /**
         * Creates a new condition.
         *
         * @param prec Original grounded condition
         * @param popFunction Variable
         * @param value Value
         * @param condition Condition type
         * @since 1.0
         */
        public InternalCondition(GroundedCond prec, POPFunction popFunction,
                String value, int condition) {
            this.prec = prec;
            this.popFunction = popFunction;
            this.value = value;
            this.condition = condition;
            this.index = -1;
        }

        /**
         * Translates this condition into a POPPrecEff.
         *
         * @param pf Planner factory
         * @return Condition translated into POPPrecEff
         * @since 1.0
         */
        public POPPrecEff toPOPPrecEff(PlannerFactory pf) {
            POPCondition pCond = new POPCondition(condition,
                    pf.getCodeFromVar(prec.getVar()), pf.getCodeFromValue(prec
                    .getValue()));
            return new POPPrecEff(pCond, popFunction, value, condition);
        }

        /**
         * Sets the index of this condition.
         *
         * @param i Condition index
         * @since 1.0
         */
        public void setIndex(int i) {
            index = i;
        }

        /**
         * Gets a key identifier for this condition.
         * 
         * @return Key identifier
         * @since 1.0
         */
        public String toKey() {
            String res;
            if (prec.getCondition() == EQUAL) {
                res = "=";
            } else if (prec.getCondition() == DISTINCT) {
                res = "<>";
            } else {
                res = "?";
            }
            return prec.getVar().toString() + res + prec.getValue();
        }
    }

    /**
     * InternalAction is a internal class to store actions.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    private class InternalAction {

        Action action;                          // Original action
        ArrayList<InternalCondition> precs;     // Action preconditions
        ArrayList<InternalCondition> effs;      // Action effects

        /**
         * Creates a new internal action.
         * 
         * @param action Original action
         * @param precs Action preconditions
         * @param effs Action effects
         * @since 1.0
         */
        public InternalAction(Action action,
                ArrayList<InternalCondition> precs,
                ArrayList<InternalCondition> effs) {
            this.action = action;
            this.precs = precs;
            this.effs = effs;
        }

        /**
         * Translates this action into a POPAction.
         * 
         * @param pf Planner factory
         * @return Action translated into a POPAction
         * @since 1.0
         */
        public POPAction toPOPAction(PlannerFactoryImp pf) {
            ArrayList<POPPrecEff> precs = new ArrayList<>(
                    this.precs.size());
            for (InternalCondition c : this.precs) {
                precs.add(c.toPOPPrecEff(pf));
            }
            ArrayList<POPPrecEff> effs = new ArrayList<>(
                    this.effs.size());
            for (InternalCondition c : this.effs) {
                effs.add(c.toPOPPrecEff(pf));
            }
            return new POPAction(action, precs, effs);
        }
    }

    /**
     * InternalOpenCondition is a internal class to store open conditions.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    private class InternalOpenCondition {

        InternalCondition condition;    // Condition
        POPStep step;                   // Step owner of the condition
        boolean isGoal;                 // Indicates if this condition is a goal

        /**
         * Creates a new internal open condition.
         * 
         * @param pe Condition
         * @param step Step owner of the condition
         * @param isGoal Indicates if this condition is a goal
         * @since 1.0
         */
        public InternalOpenCondition(InternalCondition pe, POPStep step,
                boolean isGoal) {
            this.condition = pe;
            this.step = step;
            this.isGoal = isGoal;
        }

        /**
         * Translates this open condition into a POPOpenCondition.
         * 
         * @param pf Planner factory
         * @return Open condition translated into a POPOpenCondition
         * @since 1.0
         */
        public POPOpenCondition toPOPPrecEff(PlannerFactoryImp pf) {
            POPPrecEff cond = condition.toPOPPrecEff(pf);
            return new POPOpenCondition(cond, step, isGoal);
        }
    }
    
}
