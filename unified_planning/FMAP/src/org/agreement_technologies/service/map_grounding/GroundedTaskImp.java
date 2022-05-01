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
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Hashtable;
import org.agreement_technologies.common.map_grounding.Action;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedEff;
import org.agreement_technologies.common.map_grounding.GroundedNumericEff;
import org.agreement_technologies.common.map_grounding.GroundedNumericExpression;
import org.agreement_technologies.common.map_grounding.GroundedRule;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.GroundedVar;
import org.agreement_technologies.common.map_grounding.ReachedValue;
import org.agreement_technologies.common.map_parser.Fact;
import org.agreement_technologies.common.map_parser.Function;
import org.agreement_technologies.common.map_parser.Metric;
import org.agreement_technologies.common.map_parser.Parameter;
import org.agreement_technologies.common.map_parser.SharedData;
import org.agreement_technologies.common.map_parser.Task;

/**
 * Implementation of a grounded planning task
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class GroundedTaskImp implements GroundedTask {

    // Serial number for serialization
    private static final long serialVersionUID = 9198476578040469582L;

    static final int UNDEFINED = 0;                 // Undefined value

    String domainName;                              // Domain name
    String problemName;                             // Problem name
    String[] requirements;                          // Requirements
    String[] types;                                 // Type names
    boolean[][] typesMatrix;                        // Matrix of types
    Hashtable<String, Integer> typeIndex;           // Type indexes
    int booleanTypeIndex;                           // Index of boolean type
    ArrayList<String> objects;                      // Objects
    Hashtable<String, Integer> objectIndex;         // Object indexes
    ArrayList<ArrayList<Integer>> objectTypes;      // Types of the objects
    ArrayList<Function> functions;                  // Functions
    Hashtable<String, Integer> functionIndex;       // Function index by name
    ArrayList<Boolean> staticFunction;              // Static functions
    ArrayList<GroundedVarImp> vars;                 // List of variables
    ArrayList<GroundedVarImp> numericVars;          // List of numeric variables
    Hashtable<GroundedVarImp, Integer> varIndex;    // Variables indexes
    Hashtable<String, GroundedVarImp> varNames;     // Variables indexed by name
    ArrayList<Action> actions;                      // Array of actions
    Hashtable<String, Integer> actionIndex;         // Action indexes
    ArrayList<ActionImp> rules;                     // Array of belief rules
    Hashtable<String, Integer> ruleIndex;           // Belief rules indexes
    ArrayList<GroundedValue> values;                // Values
    Hashtable<GroundedValue, Integer> valueIndex;   // Value indexes
    ArrayList<GroundedValue> newValues;             // Only for the re-grounding process
    ArrayList<GroundedCond> globalGoals;            // Set of global goals
    Hashtable<String, Integer> agentIndex;          // Agent indexes
    int thisAgentIndex;                             // Index of this agent
    String agentName;                               // Name of this agent
    ArrayList<ArrayList<GroundedSharedData>> sharedDataByFunction;	// Shared data by function index
    int sameObjects;                                // Same objects filtering
    double selfInterest;                            // Self-interest level
    double metricThreshold;                         // Metric threshold
    ArrayList<GroundedCond> preferences;            // Preferences
    Hashtable<String, Integer> preferenceIndex;     // Preference indexes by name
    ArrayList<String> preferenceNames;              // Preference names
    GroundedMetric metric;                          // Metric function
    double violatedCost[];                          // Weight for violated preferences
    boolean metricRequiresMakespan;                 // Flag to check if the metric optimizes the makespan
    final boolean negationByFailure;                // Flag to check if the information model is negation by failure

    /**
     * Constructor of a grounded task.
     *
     * @param task Parsed planning task
     * @param sameObjects Type of same-objects filtering. See constants in
     * GroundedTask
     * @param negationByFailure <code>true</code>, if the model type is negation
     * by failure; <code>false</code> is the model is unknown by failure
     * @since 1.0
     */
    public GroundedTaskImp(Task task, int sameObjects, boolean negationByFailure) {
        this.domainName = task.getDomainName();
        this.problemName = task.getProblemName();
        this.sameObjects = sameObjects;
        this.negationByFailure = negationByFailure;
        String[] aux = task.getRequirements();
        this.requirements = new String[aux.length];                 // Requirements
        System.arraycopy(aux, 0, this.requirements, 0, aux.length);
        aux = task.getTypes();                                      // Types
        this.types = new String[aux.length];
        System.arraycopy(aux, 0, this.types, 0, aux.length);
        initTypesMatrix(task);
        aux = task.getObjects();                                    // Objects
        this.objects = new ArrayList<>(aux.length + 1);
        this.objects.add("?");
        for (String obj : aux) {
            this.objects.add(obj);
        }
        initObjects(task);
        vars = new ArrayList<>();                                   // Variables
        numericVars = new ArrayList<>();
        initVariables(task);
        actions = new ArrayList<>();                                // Actions
        actionIndex = new Hashtable<>();
        rules = new ArrayList<>();                                  // Rules
        ruleIndex = new Hashtable<>();
        values = new ArrayList<>();                                 // Values
        valueIndex = new Hashtable<>();
        newValues = null;
        globalGoals = initGoals(task);                              // Goals
        selfInterest = task.getSelfInterest();
        metricThreshold = task.getMetricThreshold();
        preferences = initPreferences(task);                        // Preferences
        metric = new GroundedMetric(task.getMetric());              // Metric
        computeViolatedCosts();
    }

    /**
     * Calculates the cost of the preferences violation.
     *
     * @since 1.0
     */
    private void computeViolatedCosts() {
        violatedCost = new double[preferences.size()];
        computeViolatedCosts(metric, null);
    }

    /**
     * Calculates the cost of the preferences violation.
     *
     * @param m Expression in the metric function
     * @param parent Parent expression of the expression (metric funcion is a
     * tree of expressions)
     * @since 1.0
     */
    private void computeViolatedCosts(GroundedMetric m, GroundedMetric parent) {
        switch (m.metricType) {
            case GroundedMetric.MT_PREFERENCE:
                int prefIndex = -1;
                for (int i = 0; i < preferences.size() && prefIndex == -1; i++) {
                    if (preferences.get(i) == m.preference) {
                        prefIndex = i;
                    }
                }
                violatedCost[prefIndex] = 1.0;
                if (parent != null) {
                    for (GroundedMetric t : parent.term) {
                        if (t.metricType == GroundedMetric.MT_NUMBER) {
                            violatedCost[prefIndex] *= t.number;
                        }
                    }
                }
                break;
            case GroundedMetric.MT_NUMBER:
            case GroundedMetric.MT_TOTAL_TIME:
            case GroundedMetric.MT_NONE:
                break;
            default:
                for (GroundedMetric t : m.term) {
                    computeViolatedCosts(t, m);
                }
        }
    }

    /**
     * Prepares the structures for preferences for the grounding process.
     *
     * @param task Parsed planning task
     * @return List of preferences
     * @since 1.0
     */
    private ArrayList<GroundedCond> initPreferences(Task task) {
        preferenceIndex = new Hashtable<>();
        preferenceNames = new ArrayList<>();
        ArrayList<GroundedCond> pref = new ArrayList<>();
        Fact[] g = task.getPreferences();
        for (int i = 0; i < g.length; i++) {
            String pname = task.getPreferenceName(i);
            int index = functionIndex.get(g[i].getFunctionName());
            Function func = functions.get(index);
            if (func.isMultifunction() || g[i].getValues().length != 1) {
                throw new RuntimeException("Invalid preference '" + pname + "'");
            }
            GroundedVarImp v = initSingleFunctionVariable(g[i], func, false);
            String value = g[i].getValues()[0];
            GroundedValue gv = new GroundedValue(v.varIndex, objectIndex.get(value));
            ActionCondition ac = new ActionCondition(gv, !g[i].negated());
            preferenceIndex.put(pname, pref.size());
            preferenceNames.add(pname);
            pref.add(ac);
        }
        return pref;
    }

    /**
     * Optimizes the structures after the grounding process.
     *
     * @since 1.0
     */
    @Override
    public void optimize() {
        for (Action a : actions) {
            a.optimize();
        }
        varNames = new Hashtable<>(vars.size());
        for (GroundedVarImp v : vars) {
            varNames.put(v.toString(), v);
        }
    }

    /**
     * Creates a new grounded condition.
     *
     * @param condition Condition type (EQUAL or DISTINCT)
     * @param var Grounded variable
     * @param value Value
     * @return New grounded condition
     * @since 1.0
     */
    @Override
    public GroundedCond createGroundedCondition(int condition, GroundedVar var, String value) {
        if (var == null) {
            return null;
        }
        Integer varIndex = getVarIndex((GroundedVarImp) var);
        if (varIndex == null) {
            return null;
        }
        Integer valueIndex = getObjectIndex(value);
        if (valueIndex == null) {
            valueIndex = UNDEFINED;
        }
        GroundedValue gVar = new GroundedValue(varIndex, valueIndex);
        ActionCondition ac = new ActionCondition(gVar, condition == GroundedCond.EQUAL);
        return ac;
    }

    /**
     * Creates a new grounded effect.
     *
     * @param var Grounded variable
     * @param value Value
     * @return New grounded effect
     * @since 1.0
     */
    @Override
    public GroundedEff createGroundedEffect(GroundedVar var, String value) {
        if (var == null) {
            return null;
        }
        Integer varIndex = getVarIndex((GroundedVarImp) var);
        if (varIndex == null) {
            return null;
        }
        Integer valueIndex = getObjectIndex(value);
        if (valueIndex == null) {
            valueIndex = UNDEFINED;
        }
        GroundedValue gVar = new GroundedValue(varIndex, valueIndex);
        ActionCondition ac = new ActionCondition(gVar);
        return ac;
    }

    /**
     * Creates a new action.
     *
     * @param opName Operator name
     * @param params Action parameters
     * @param prec Action preconditions
     * @param eff Action effects
     * @return New action
     * @since 1.0
     */
    @Override
    public Action createAction(String opName, String[] params,
            GroundedCond[] prec, GroundedEff[] eff) {
        ActionImp a = new ActionImp(opName, params.length, prec.length, eff.length);
        for (int i = 0; i < params.length; i++) {
            Integer objIndex = getObjectIndex(params[i]);
            if (objIndex == null) {
                objIndex = UNDEFINED;
            }
            a.setParam(i, objIndex, params[i]);
        }
        for (int i = 0; i < prec.length; i++) {
            a.prec[i] = new ActionCondition(prec[i]);
        }
        for (int i = 0; i < eff.length; i++) {
            a.eff[i] = new ActionCondition(eff[i]);
        }
        return a;
    }

    /**
     * Initializes the agents data.
     *
     * @param task Parsed planning task
     * @param agentName Name of the agent
     * @since 1.0
     */
    public void initAgents(Task task, String agentName) {
        this.agentName = agentName;
        int agType[] = new int[1];
        agType[0] = typeIndex.get("agent");
        ArrayList<String> agentList = new ArrayList<>();
        for (int i = 0; i < objects.size(); i++) {
            if (objectIsCompatible(i, agType)) {
                agentList.add(objects.get(i));
            }
        }
        if (!agentList.contains(agentName)) {
            agentList.add(agentName);
        }
        Collections.sort(agentList);
        thisAgentIndex = agentList.indexOf(agentName);
        agentIndex = new Hashtable<>();                 // Agents
        for (int i = 0; i < agentList.size(); i++) {
            String agName = agentList.get(i);
            agentIndex.put(agName, i);
        }
        initSharedData(task);				// Shared data
    }

    /**
     * Initializes the shared data.
     *
     * @param task Parsed planning task
     * @since 1.0
     */
    private void initSharedData(Task task) {
        sharedDataByFunction = new ArrayList<>();
        for (int i = 0; i < functions.size(); i++) {
            sharedDataByFunction.add(new ArrayList<GroundedSharedData>());
        }
        for (SharedData sd : task.getSharedData()) {
            GroundedSharedData gsd = new GroundedSharedData(sd);
            sharedDataByFunction.get(gsd.fncIndex).add(gsd);
        }
    }

    /**
     * Initializes the task goals.
     *
     * @param task Parsed planning task
     * @param globalGoals <code>true</code> for grounding the global goals,
     * <code>false</code> for private goals
     * @return List of goals
     * @since 1.0
     */
    private ArrayList<GroundedCond> initGoals(Task task) {
        ArrayList<GroundedCond> goals = new ArrayList<>();
        Fact[] g = task.getGoals();
        for (int i = 0; i < g.length; i++) {
            int index = functionIndex.get(g[i].getFunctionName());
            Function func = functions.get(index);
            if (func.isMultifunction()) {
                GroundedVarImp[] varList = initMultiFunctionVariable(g[i], false);
                for (GroundedVarImp v : varList) {
                    GroundedValue gv = new GroundedValue(v.varIndex, g[i].negated()
                            ? objectIndex.get("false") : objectIndex.get("true"));
                    goals.add(new ActionCondition(gv, true));
                }
            } else {
                GroundedVarImp v = initSingleFunctionVariable(g[i], func, false);
                String values[] = g[i].getValues();
                for (String value : values) {
                    GroundedValue gv = new GroundedValue(v.varIndex, objectIndex.get(value));
                    goals.add(new ActionCondition(gv, !g[i].negated()));
                }
            }
        }
        return goals;
    }

    /**
     * Initializes the list of variables through the information in the initial
     * state.
     *
     * @param task Parsed planning task
     * @since 1.0
     */
    private void initVariables(Task task) {
        Function[] funcList = task.getFunctions();
        functions = new ArrayList<>(funcList.length);
        functionIndex = new Hashtable<>(funcList.length);
        for (int i = 0; i < funcList.length; i++) {
            functions.add(funcList[i]);
            functionIndex.put(funcList[i].getName(), i);
        }
        varIndex = new Hashtable<>();
        for (Fact fact : task.getInit()) {
            int index = functionIndex.get(fact.getFunctionName());
            Function func = functions.get(index);
            if (func.isMultifunction()) {
                initMultiFunctionVariable(fact, true);
            } else {
                initSingleFunctionVariable(fact, func, true);
            }
        }
    }

    /**
     * Initializes a single-function variable.
     *
     * @param fact Parsed Fact
     * @param initialState <code>true</code> if the fact is in the initial state
     * @return The initialized variables
     * @since 1.0
     */
    private GroundedVarImp[] initMultiFunctionVariable(Fact fact, boolean initialState) {
        String values[] = fact.getValues();
        GroundedVarImp[] gvList = new GroundedVarImp[values.length];
        for (int i = 0; i < values.length; i++) {
            int fncIndex = getFunctionIndex(fact.getFunctionName());
            GroundedVarImp v = new GroundedVarImp(fact.getFunctionName(), varIndex.size(),
                    fncIndex, fact.getParameters(), values[i]);
            if (varIndex.containsKey(v)) {	// Existing variable
                v = vars.get(varIndex.get(v));
                if (initialState) {
                    updateInitialVariableValues(v, fact, true);
                }
            } else {						// New variable
                if (initialState) {
                    updateInitialVariableValues(v, fact, true);
                }
                v.setDomain(new String[]{"boolean"});
                varIndex.put(v, vars.size());
                vars.add(v);
            }
            gvList[i] = v;
        }
        return gvList;
    }

    /**
     * Initializes a single-function variable.
     *
     * @param fact Parsed Fact
     * @param func Parsed function
     * @param task Parsed planning task
     * @param initialState <code>true</code>, if the fact is in the initial
     * state
     * @return The initialized variable
     * @since 1.0
     */
    private GroundedVarImp initSingleFunctionVariable(Fact fact, Function func,
            boolean initialState) {
        int fncIndex = getFunctionIndex(fact.getFunctionName());
        GroundedVarImp v = new GroundedVarImp(fact.getFunctionName(), varIndex.size(),
                fncIndex, fact.getParameters());
        if (varIndex.containsKey(v)) {	// Existing variable
            v = vars.get(varIndex.get(v));
            if (initialState) {
                updateInitialVariableValues(v, fact, false);
            }
        } else {			// New variable
            if (initialState) {
                updateInitialVariableValues(v, fact, false);
            }
            v.setDomain(func.getDomain());
            varIndex.put(v, vars.size());
            vars.add(v);
        }
        return v;
    }

    /**
     * Sets/updates the initial value of a variable.
     *
     * @param v Variable to update
     * @param fact Fact with the initial assignment
     * @param multi <code>true</code> if the variable comes from a
     * multi-function
     * @since 1.0
     */
    private void updateInitialVariableValues(GroundedVarImp v, Fact fact, boolean multi) {
        if (multi) {
            if (fact.negated()) {
                v.setTrueValue("false", objectIndex);
                v.addFalseValue("true", objectIndex);
            } else {
                v.setTrueValue("true", objectIndex);
                v.addFalseValue("false", objectIndex);
            }
        } else {
            String values[] = fact.getValues();
            for (String value : values) {
                if (value.equalsIgnoreCase("true") && values.length == 1) {
                    if (fact.negated()) {
                        v.setTrueValue("false", objectIndex);
                        v.addFalseValue(value, objectIndex);
                    } else {
                        v.setTrueValue(value, objectIndex);
                        v.addFalseValue("false", objectIndex);
                    }
                } else if (value.equalsIgnoreCase("false") && values.length == 1) {
                    if (fact.negated()) {
                        v.setTrueValue("true", objectIndex);
                        v.addFalseValue(value, objectIndex);
                    } else {
                        v.setTrueValue(value, objectIndex);
                        v.addFalseValue("true", objectIndex);
                    }
                } else {
                    if (fact.negated()) {
                        v.addFalseValue(value, objectIndex);
                    } else {
                        v.setTrueValue(value, objectIndex);
                    }
                }
            }
        }
    }

    /**
     * Initializes the information about the planning objects For each object an
     * array-list of type indexes is stored.
     *
     * @param task Parsed planning task
     * @since 1.0
     */
    private void initObjects(Task task) {
        int numObjs = objects.size();
        objectIndex = new Hashtable<>(numObjs);
        objectTypes = new ArrayList<>(numObjs);
        String[] types;
        for (int i = 0; i < numObjs; i++) {
            objectIndex.put(objects.get(i), i);
            if (i != UNDEFINED) {
                types = task.getObjectTypes(objects.get(i));
            } else {
                types = new String[0];	// No types for the 'undefined' object
            }
            objectTypes.add(new ArrayList<Integer>(types.length));
            for (int j = 0; j < types.length; j++) {
                objectTypes.get(i).add(typeIndex.get(types[j]));
            }
        }
    }

    /**
     * Creates a new object (received from other agent).
     *
     * @param objName Object name
     * @param objTypes Object types
     * @return Index of the new object
     * @since 1.0
     */
    public int createNewObject(String objName, String[] objTypes) {
        int index = objects.size();
        objects.add(objName);
        objectIndex.put(objName, index);
        ArrayList<Integer> types = new ArrayList<>();
        for (String t : objTypes) {
            Integer tindex = typeIndex.get(t);
            if (tindex != null) {
                types.add(tindex);
            }
        }
        objectTypes.add(types);
        return index;
    }

    /**
     * Creates the types matrix such that <code>typesMatrix[x][y] == true</code>
     * if type <code>x</code> is equal or a sub-type of <code>y</code>.
     *
     * @param task Parsed planning task
     * @since 1.0
     */
    private void initTypesMatrix(Task task) {
        int numTypes = types.length;
        booleanTypeIndex = -1;
        typeIndex = new Hashtable<>(numTypes);
        for (int i = 0; i < numTypes; i++) {
            typeIndex.put(types[i], i);
            if (types[i].equalsIgnoreCase("boolean")) {
                booleanTypeIndex = i;
            }
        }
        ArrayList<Integer> list = new ArrayList<>();
        typesMatrix = new boolean[numTypes][numTypes];	// Initialized to false
        for (int i = 0; i < numTypes; i++) {
            typesMatrix[i][i] = true;
            getParentTypes(task, i, list);
            for (Integer j : list) {
                typesMatrix[i][j] = true;
            }
            list.clear();
        }
    }

    /**
     * Fills a list with all the (indexes of the) parent types of a given type.
     *
     * @param task Parser planning task
     * @param typeIndex	Index of the given type
     * @param list List to be filled
     * @since 1.0
     */
    private void getParentTypes(Task task, int typeIndex, ArrayList<Integer> list) {
        String[] pTypes = task.getParentTypes(types[typeIndex]);
        for (String pType : pTypes) {
            int pTypeIndex = this.typeIndex.get(pType);
            if (!list.contains(pTypeIndex)) {	// New parent type
                list.add(pTypeIndex);
                getParentTypes(task, pTypeIndex, list);
            }
        }
    }

    /**
     * Returns the new values achieved in the grounding process.
     *
     * @return Array of reached values
     * @since 1.0
     */
    public ReachedValue[] getNewValues() {
        ArrayList<GroundedValue> nv = newValues == null ? values : newValues;
        int numValues = 0;
        for (GroundedValue v : nv) {
            if (!staticFunction.get(v.var().fncIndex)) {
                numValues++;
            }
        }
        ReachedValue[] res = new ReachedValue[numValues];
        int i = 0;
        for (GroundedValue v : nv) {
            if (!staticFunction.get(v.var().fncIndex)) {
                res[i++] = v;
            }
        }
        return res;
    }

    /**
     * Clears the list of new values. This method must be called before any
     * re-grounding process.
     *
     * @since 1.0
     */
    public void resetNewValues() {
        newValues = new ArrayList<>();
    }

    /**
     * Sets the static functions.
     *
     * @param staticFunctions Hash table with the name of the static functions
     * @since 1.0
     */
    public void setStaticFunctions(Hashtable<String, Boolean> staticFunctions) {
        staticFunction = new ArrayList<>(functions.size());
        for (Function f : functions) {
            staticFunction.add(staticFunctions.containsKey(f.getName()));
        }
    }

    /**
     * Gets the domain name.
     *
     * @return Name of the domain
     * @since 1.0
     */
    @Override
    public String getDomainName() {
        return domainName;
    }

    /**
     * Gets the problem name.
     *
     * @return Name of the problem
     * @since 1.0
     */
    @Override
    public String getProblemName() {
        return problemName;
    }

    /**
     * Gets the name of this agent.
     *
     * @return Name of this agent
     * @since 1.0
     */
    @Override
    public String getAgentName() {
        return agentName;
    }

    /**
     * Returns the list of agents in the MAP task.
     *
     * @return Array of string (agent names)
     * @since 1.0
     */
    @Override
    public String[] getAgentNames() {
        java.util.Enumeration<String> list = agentIndex.keys();
        String ags[] = new String[agentIndex.size()];
        int n = 0;
        while (list.hasMoreElements()) {
            ags[n++] = list.nextElement();
        }
        return ags;
    }

    /**
     * Gets the requirement list.
     *
     * @return List of requirements
     * @since 1.0
     */
    @Override
    public String[] getRequirements() {
        return requirements;
    }

    /**
     * Gets the list of types.
     *
     * @return Array of types
     * @since 1.0
     */
    @Override
    public String[] getTypes() {
        return types;
    }

    /**
     * Gets the parent types of a given type.
     *
     * @param type Name of the type
     * @return Array of parent types
     * @since 1.0
     */
    @Override
    public String[] getParentTypes(String type) {
        int n = 0;
        int typeIndex = this.typeIndex.get(type);
        for (int i = 0; i < types.length; i++) {
            if (typesMatrix[typeIndex][i] && typeIndex != i) {
                n++;
            }
        }
        String[] pTypes = new String[n];
        n = 0;
        for (int i = 0; i < types.length; i++) {
            if (typesMatrix[typeIndex][i] && typeIndex != i) {
                pTypes[n++] = types[i];
            }
        }
        return pTypes;
    }

    /**
     * Gets the object list (including 'undefined').
     *
     * @return Array of object names
     * @since 1.0
     */
    @Override
    public String[] getObjects() {
        return objects.toArray(new String[objects.size()]);
    }

    /**
     * Gets the list of types for a given object.
     *
     * @param objName Name of the object
     * @return Array of types of the object
     * @since 1.0
     */
    @Override
    public String[] getObjectTypes(String objName) {
        int objIndex = objectIndex.get(objName);
        ArrayList<Integer> objTypes = objectTypes.get(objIndex);
        String res[] = new String[objTypes.size()];
        for (int i = 0; i < res.length; i++) {
            res[i] = this.types[objTypes.get(i)];
        }
        return res;
    }

    /**
     * Gets the list of non-static variables.
     *
     * @return Array of grounded variables
     * @since 1.0
     */
    @Override
    public GroundedVar[] getVars() {
        int numVars = 0;
        for (GroundedVarImp v : vars) {
            if (!staticFunction.get(v.fncIndex)) {
                numVars++;
            }
        }
        GroundedVar[] res = new GroundedVar[numVars];
        int i = 0;
        for (GroundedVarImp v : vars) {
            if (!staticFunction.get(v.fncIndex)) {
                res[i++] = v;
            }
        }
        return res;
    }

    /**
     * Gets the list of grounded actions.
     *
     * @return List of grounded actions
     * @since 1.0
     */
    @Override
    public ArrayList<Action> getActions() {
        return actions;
    }

    /**
     * Returns the list of grounded belief rules.
     *
     * @return List of grounded belief rules
     * @since 1.0
     */
    @Override
    public GroundedRule[] getBeliefs() {
        return rules.toArray(new GroundedRule[rules.size()]);
    }

    /**
     * Returns the global goals (public goals).
     *
     * @return List of global goals
     * @since 1.0
     */
    @Override
    public ArrayList<GroundedCond> getGlobalGoals() {
        return globalGoals;
    }

    /**
     * Gets a description of this grounded domain.
     *
     * @return Domain description
     * @since 1.0
     */
    @Override
    public String toString() {
        StringBuilder s = new StringBuilder();
        s.append("Domain: ").append(getDomainName()).append("\n");
        s.append("Problem: ").append(getProblemName()).append("\n");
        s.append("Agent: ").append(getAgentName()).append("\n");
        for (String a : getAgentNames()) {
            s.append("* ").append(a).append("\n");
        }
        s.append("Requirements:\n");
        for (String r : getRequirements()) {
            s.append("* ").append(r).append("\n");
        }
        s.append("Types:\n");
        for (String t : getTypes()) {
            String pt[] = getParentTypes(t);
            s.append("* ").append(t).append(" [ ");
            for (String t2 : pt) {
                s.append(t2).append(" ");
            }
            s.append("]\n");
        }
        s.append("Objects:\n");
        for (String t : getObjects()) {
            String pt[] = getObjectTypes(t);
            s.append("* ").append(t).append(" [ ");
            for (String t2 : pt) {
                s.append(t2).append(" ");
            }
            s.append("]\n");
        }
        s.append("Variables:\n");
        for (GroundedVar gv : getVars()) {
            s.append("* ").append(gv).append("\n");
        }
        s.append("Global goals:\n");
        for (GroundedCond g : getGlobalGoals()) {
            s.append("* ").append(g).append("\n");
        }
        return s.toString();
    }

    /**
     * Returns the index of a given type.
     *
     * @param name Type name
     * @return Type index
     * @since 1.0
     */
    public int getTypeIndex(String name) {
        return typeIndex.get(name);
    }

    /**
     * Returns the index of the given function.
     *
     * @param name Function name
     * @return Function index
     * @since 1.0
     */
    public int getFunctionIndex(String name) {
        return functionIndex.get(name);
    }

    /**
     * Returns the index of the given object.
     *
     * @param name Object name
     * @return Object index
     * @since 1.0
     */
    public Integer getObjectIndex(String name) {
        return objectIndex.get(name);
    }

    /**
     * Returns all objects that can be a value in the given domain.
     *
     * @param domainIndex List of (indexes of) types
     * @return List of (indexes of) objects
     * @since 1.0
     */
    public ArrayList<Integer> getAllDomainValues(int[] domainIndex) {
        ArrayList<Integer> dv = new ArrayList<>();
        for (int i = 0; i < objects.size(); i++) {
            ArrayList<Integer> types = objectTypes.get(i);
            boolean isCompatible = false;
            for (Integer type : types) {
                for (int j = 0; j < domainIndex.length; j++) {
                    if (typesMatrix[type][domainIndex[j]]) {
                        isCompatible = true;
                    }
                }
                if (isCompatible) {
                    dv.add(i);
                    break;
                }
            }
        }
        return dv;
    }

    /**
     * Checks if a given object is compatible with (at least) one of the given
     * types.
     *
     * @param objIndex Object index
     * @param types List of types (indexes)
     * @return <code>true</code>, if the object is compatible;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean objectIsCompatible(int objIndex, int[] types) {
        ArrayList<Integer> objTypes = objectTypes.get(objIndex);
        for (Integer ot : objTypes) {
            for (int t : types) {
                if (typesMatrix[ot][t]) {
                    return true;
                }
            }
        }
        return false;
    }

    /**
     * Adds a new variable.
     *
     * @param var Basic data of the variable to add
     * @return Variable added
     * @since 1.0
     */
    public GroundedVarImp addVariable(GroundedVarImp var) {
        int fncIndex = functionIndex.get(var.name);
        if (fncIndex == -1) {
            throw new RuntimeException("Unknown function: " + var.name);
        }
        String[] params = new String[var.paramIndex.length];
        for (int i = 0; i < params.length; i++) {
            params[i] = this.objects.get(var.paramIndex[i]);
        }
        GroundedVarImp newVar = new GroundedVarImp(var.name, this.vars.size(), fncIndex,
                params);
        newVar.setDomain(var.domain);
        varIndex.put(newVar, newVar.varIndex);
        vars.add(newVar);
        return newVar;
    }

    /**
     * Adds a new value reached by this agent.
     *
     * @param varIndex	Variable index
     * @param value Value (object index)
     * @param currentLevel RPG level
     * @param agIndex Agent index
     * @return Index of the value
     * @since 1.0
     */
    private int addValue(int varIndex, int value, int currentLevel, int agIndex) {
        GroundedValue gv = new GroundedValue(varIndex, value);
        Integer gvIndex = valueIndex.get(gv);
        if (gvIndex == null) {	// New value
            gv.minTime = new int[agentIndex.size()];
            Arrays.fill(gv.minTime, -1);
            gvIndex = this.values.size();
            this.valueIndex.put(gv, gvIndex);
            this.values.add(gv);
        } else {
            gv = values.get(gvIndex);
        }
        if (currentLevel < gv.minTime[agIndex] || gv.minTime[agIndex] == -1) {
            gv.minTime[agIndex] = currentLevel;
        }
        return gvIndex;
    }

    /**
     * Adds a new value reached by this agent.
     *
     * @param varIndex Variable index
     * @param value Value (object index)
     * @param currentLevel RPG level
     * @return Index of the value
     * @since 1.0
     */
    public int addValue(int varIndex, int value, int currentLevel) {
        return addValue(varIndex, value, currentLevel, thisAgentIndex);
    }

    /**
     * Returns the index of a given variable.
     *
     * @param v Variable
     * @return Variable index
     * @since 1.0
     */
    public Integer getVarIndex(GroundedVarImp v) {
        return varIndex.get(v);
    }

    /**
     * Creates a new variable.
     *
     * @param v Incomplete variable (only with its name and parameter indexes)
     * @return Variable index
     * @since 1.0
     */
    public int createNewVariable(GroundedVarImp v) {
        v.varIndex = vars.size();
        v.fncIndex = functionIndex.get(v.name);
        v.paramNames = new String[v.paramIndex.length];
        for (int i = 0; i < v.paramIndex.length; i++) {
            v.paramNames[i] = objects.get(v.paramIndex[i]);
        }
        Function f = functions.get(v.fncIndex);
        String domain[] = f.getDomain();
        v.domain = new String[domain.length];
        v.domainIndex = new int[domain.length];
        for (int i = 0; i < domain.length; i++) {
            v.domain[i] = domain[i];
            v.domainIndex[i] = typeIndex.get(domain[i]);
        }
        v.trueValue = -1;
        v.falseValues = new ArrayList<>();
        vars.add(v);
        varIndex.put(v, v.varIndex);
        return v.varIndex;
    }

    /**
     * Creates a new numeric variable.
     *
     * @param v Incomplete variable (only with its name and parameter indexes)
     * @return Variable index
     * @since 1.0
     */
    public GroundedVarImp createNewNumericVariable(GroundedVarImp v) {
        v.varIndex = numericVars.size();
        v.fncIndex = functionIndex.get(v.name);
        v.paramNames = new String[v.paramIndex.length];
        for (int i = 0; i < v.paramIndex.length; i++) {
            v.paramNames[i] = objects.get(v.paramIndex[i]);
        }
        Function f = functions.get(v.fncIndex);
        String domain[] = f.getDomain();
        v.domain = new String[domain.length];
        v.domainIndex = new int[domain.length];
        for (int i = 0; i < domain.length; i++) {
            v.domain[i] = domain[i];
            v.domainIndex[i] = typeIndex.get(domain[i]);
        }
        v.trueValue = -1;
        v.falseValues = new ArrayList<>();
        numericVars.add(v);
        return v;
    }

    /**
     * Checks if the used model is negation by failure.
     *
     * @return <code>true</code>, if the model type is negation by failure;
     * <code>false</code> is the model is unknown by failure
     * @since 1.0
     */
    @Override
    public boolean negationByFailure() {
        return negationByFailure;
    }

    /**
     * Gets a grounded variable through its name
     *
     * @param varName Name of the variable
     * @return Grounded variable
     * @since 1.0
     */
    @Override
    public GroundedVar getVarByName(String varName) {
        return varNames.get(varName);
    }

    /**
     * Returns the level of self-interest of the agent. The self-interest is a
     * number from 0 to 1, where 0 means fully coopertive and 1 means fully
     * self-interested.
     *
     * @return Self-interest level
     * @since 1.0
     */
    @Override
    public double getSelfInterestLevel() {
        return selfInterest;
    }

    /**
     * Gets the metric threshold. This threshold indicates the minimum metric
     * value for the agent to accept a plan as a solution.
     *
     * @return Metric threshold
     * @since 1.0
     */
    @Override
    public double getMetricThreshold() {
        return metricThreshold;
    }

    /**
     * Evaluates the metric function in a given state.
     *
     * @param state State
     * @param makespan Makespan of the plan
     * @return Metric function value
     * @since 1.0
     */
    @Override
    public double evaluateMetric(HashMap<String, String> state, double makespan) {
        return evaluateMetric(metric, state, makespan);
    }

    /**
     * Recursive private method for metric evaluation.
     *
     * @param m Metric expression
     * @param state State
     * @param makespan Makespan of the plan
     * @return Metric function value
     * @since 1.0
     */
    private double evaluateMetric(GroundedMetric m, HashMap<String, String> state, double makespan) {
        double res;
        switch (m.metricType) {
            case GroundedMetric.MT_PREFERENCE:
                String value = state.get(m.preference.getVar().toString());
                res = value.equals(m.preference.getValue()) ? 0 : 1;
                break;
            case GroundedMetric.MT_ADD:
                res = 0;
                for (GroundedMetric mt : m.term) {
                    res += evaluateMetric(mt, state, makespan);
                }
                break;
            case GroundedMetric.MT_MULT:
                res = evaluateMetric(m.term.get(0), state, makespan);
                for (int i = 1; i < m.term.size(); i++) {
                    res *= evaluateMetric(m.term.get(i), state, makespan);
                }
                break;
            case GroundedMetric.MT_TOTAL_TIME:
                res = makespan;
                break;
            case GroundedMetric.MT_NONE:
                res = 0;
                break;
            default:
                res = m.number;
        }
        return res;
    }

    /**
     * Evaluates the metric function in a given state.
     *
     * @param state Multi-state (it is a state where a variable can have several
     * values)
     * @param makespan Makespan of the plan
     * @return Metric function value
     * @since 1.0
     */
    @Override
    public double evaluateMetricMulti(HashMap<String, ArrayList<String>> state, double makespan) {
        return evaluateMetricMulti(metric, state, makespan);
    }

    /**
     * Private recursive method for metric evaluation.
     *
     * @param m Metric expression
     * @param state Multi-state (it is a state where a variable can have several
     * values)
     * @param makespan Makespan of the plan
     * @return Metric function value
     * @since 1.0
     */
    private double evaluateMetricMulti(GroundedMetric m, HashMap<String, ArrayList<String>> state,
            double makespan) {
        double res;
        switch (m.metricType) {
            case GroundedMetric.MT_PREFERENCE:
                ArrayList<String> values = state.get(m.preference.getVar().toString());
                res = 1;
                if (values != null) {
                    for (String value : values) {
                        if (value.equals(m.preference.getValue())) {
                            res = 0;
                            break;
                        }
                    }
                }
                break;
            case GroundedMetric.MT_ADD:
                res = 0;
                for (GroundedMetric mt : m.term) {
                    res += evaluateMetricMulti(mt, state, makespan);
                }
                break;
            case GroundedMetric.MT_MULT:
                res = evaluateMetricMulti(m.term.get(0), state, makespan);
                for (int i = 1; i < m.term.size(); i++) {
                    res *= evaluateMetricMulti(m.term.get(i), state, makespan);
                }
                break;
            case GroundedMetric.MT_TOTAL_TIME:
                res = makespan;
                break;
            default:
                res = m.number;
        }
        return res;
    }

    /**
     * Gets the lst of preferences.
     *
     * @return List of preferences (grounded conditions)
     * @since 1.0
     */
    @Override
    public ArrayList<GroundedCond> getPreferences() {
        return preferences;
    }

    /**
     * Returns the number of preferences.
     *
     * @return Number of preferences
     * @since 1.0
     */
    @Override
    public int getNumPreferences() {
        return preferences.size();
    }

    /**
     * Gets the cost of violating a given preference.
     *
     * @param prefIndex Preference index (in [0,getNumPreferences()-1])
     * @return Violation cost
     * @since 1.0
     */
    @Override
    public double getViolatedCost(int prefIndex) {
        return violatedCost[prefIndex];
    }

    /**
     * Indicates if the metric function contains the total-time keyword, i.e.
     * that tries to optimize the makespan.
     *
     * @return <code>true</code>, if the metric includes the total-time as a
     * parameter; <code>false</code>, otherwise
     * @since 1.0
     */
    @Override
    public boolean metricRequiresMakespan() {
        return metricRequiresMakespan;
    }

    /**
     * Implementation of a grounded variable.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    public class GroundedVarImp implements GroundedVar {

        // Serial number for serialization
        private static final long serialVersionUID = -1727789113615885154L;
        int varIndex;				// Variable index
        String name;				// Variable name
        int fncIndex;				// Function index of the variable name
        String[] paramNames;                    // Parameter names
        int[] paramIndex;			// Parameter indexes
        String[] domain;			// Variable domain
        int[] domainIndex;			// Indexes of the domain types
        int trueValue;				// Initial true value
        ArrayList<Integer> falseValues;         // List of initial false values

        /**
         * Common constructor.
         *
         * @param name Variable name
         * @since 1.0
         */
        private GroundedVarImp(String name, int varIndex, int fncIndex) {
            this.name = name;
            this.varIndex = varIndex;
            this.fncIndex = fncIndex;
            trueValue = -1;
            falseValues = new ArrayList<>();
        }

        /**
         * Constructor (only for finding an existing variable).
         *
         * @param name Variable name
         * @param numParams Number of parameters
         * @since 1.0
         */
        public GroundedVarImp(String name, int numParams) {
            this.name = name;
            paramIndex = new int[numParams];
        }

        /**
         * Constructor for a single-function variable.
         *
         * @param name Variable name
         * @param varIndex Variable index
         * @param fncIndex Function index
         * @param params Variable parameters (names)
         * @since 1.0
         */
        public GroundedVarImp(String name, int varIndex, int fncIndex, String[] params) {
            this(name, varIndex, fncIndex);
            paramNames = new String[params.length];
            paramIndex = new int[params.length];
            for (int i = 0; i < params.length; i++) {
                paramNames[i] = params[i];
                paramIndex[i] = objectIndex.get(params[i]);
            }
        }

        /**
         * Constructor for a multi-function variable
         *
         * @param name Variable name
         * @param varIndex Variable index
         * @param fncIndex Function index
         * @param params Variable parameters (names)
         * @param value Additional parameter
         * @since 1.0
         */
        public GroundedVarImp(String name, int varIndex, int fncIndex, String[] params,
                String value) {
            this(name, varIndex, fncIndex);
            paramNames = new String[params.length + 1];
            paramIndex = new int[params.length + 1];
            for (int i = 0; i < params.length; i++) {
                paramNames[i] = params[i];
                paramIndex[i] = objectIndex.get(params[i]);
            }
            paramNames[params.length] = value;
            paramIndex[params.length] = objectIndex.get(value);
        }

        /**
         * Sets the variable domain.
         *
         * @param domain List of types
         * @since 1.0
         */
        public void setDomain(String[] domain) {
            this.domain = new String[domain.length];
            domainIndex = new int[domain.length];
            for (int i = 0; i < domain.length; i++) {
                this.domain[i] = domain[i];
                domainIndex[i] = typeIndex.get(domain[i]);
            }
        }

        /**
         * Sets the true initial value to this variable.
         *
         * @param value New value
         * @param objectIndex Hash table to obtain the value index
         * @since 1.0
         */
        public void setTrueValue(String value,
                Hashtable<String, Integer> objectIndex) {
            Integer valueIndex = objectIndex.get(value);
            if (trueValue == -1) {
                int falseIndex = falseValues.indexOf(valueIndex);
                if (falseIndex == -1) {
                    trueValue = valueIndex;
                } else {	// Contradiction
                    falseValues.remove(falseIndex);
                }
            } else {
                throw new RuntimeException("True value already set for variable: " + toString());
            }
        }

        /**
         * Adds a false initial value to this variable.
         *
         * @param value New value
         * @param objectIndex Hash table to obtain the value index
         * @since 1.0
         */
        public void addFalseValue(String value,
                Hashtable<String, Integer> objectIndex) {
            Integer valueIndex = objectIndex.get(value);
            if (!falseValues.contains(valueIndex)) {
                if (trueValue != valueIndex) {
                    falseValues.add(valueIndex);
                } else {	// Contradiction
                    trueValue = -1;
                }
            }
        }

        /**
         * Returns a String representation of this variable.
         *
         * @return Variable description
         * @since 1.0
         */
        @Override
        public String toString() {
            String res = name;
            for (int i = 0; i < paramNames.length; i++) {
                res += " " + paramNames[i];
            }
            return res;
        }

        /**
         * Compares two variables by their names and parameters.
         *
         * @param v Another variable
         * @return <code>true</code>, if both variables are equal;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object v) {
            GroundedVarImp gv = (GroundedVarImp) v;
            return name.equals(gv.name) && Arrays.equals(paramIndex, gv.paramIndex);
        }

        /**
         * Returns the hash code for this variable.
         *
         * @return Hash code for this variable
         * @since 1.0
         */
        @Override
        public int hashCode() {
            return (name + Arrays.toString(paramIndex)).hashCode();
        }

        /**
         * Returns the function name.
         *
         * @return Function name
         * @since 1.0
         */
        @Override
        public String getFuctionName() {
            return name;
        }

        /**
         * Returns the function parameters (list of object names).
         *
         * @return Function parameters
         * @since 1.0
         */
        @Override
        public String[] getParams() {
            return paramNames;
        }

        /**
         * Returns the function domain types.
         *
         * @return Array of types for the values of the function
         * @since 1.0
         */
        @Override
        public String[] getDomainTypes() {
            return domain;
        }

        /**
         * Returns the initial true value (object name) or null if it has none.
         *
         * @return Variable value in the initial state
         * @since 1.0
         */
        @Override
        public String initialTrueValue() {
            return trueValue != -1 ? objects.get(trueValue) : null;
        }

        /**
         * Returns the initial false values for this variable (list of objects).
         *
         * @return Array of false values (values of the variables that does not
         * hold in the initial state)
         * @since 1.0
         */
        @Override
        public String[] initialFalseValues() {
            String res[] = new String[falseValues.size()];
            for (int i = 0; i < res.length; i++) {
                res[i] = objects.get(falseValues.get(i));
            }
            return res;
        }

        /**
         * Gets the Minimum time, according to the disRPG, in which the variable
         * can get the given value (objName). Returns -1 if the given value is
         * not reachable.
         *
         * @param objName Value name
         * @return Minimum time needed to reach that value; -1 if it is not
         * reachable
         * @since 1.0
         */
        @Override
        public int getMinTime(String objName) {
            GroundedValue gv = new GroundedValue(varIndex, objectIndex.get(objName));
            Integer index = valueIndex.get(gv);
            if (index == null) {
                return -1;
            }
            gv = values.get(index);
            int time = gv.getMinTime();
            return time;
        }

        /**
         * Minimal time, according to the disRPG, in which a given agent can get
         * this variable to have a given value (objName). Returns -1 if the
         * given agent cannot assign the given value to this variable.
         *
         * @param objName Value name
         * @param agent Agent to generate the value
         * @return Minimum time needed to reach that value by that agent; -1 if
         * it is not reachable
         * @since 1.0
         */
        @Override
        public int getMinTime(String objName, String agent) {
            GroundedValue gv = new GroundedValue(varIndex, objectIndex.get(objName));
            Integer index = valueIndex.get(gv);
            Integer agIndex = agentIndex.get(agent);
            if (index == null || agIndex == null) {
                return -1;
            }
            gv = values.get(index);
            int time = gv.minTime[agIndex];
            return time;
        }

        /**
         * Checks whether the given value for this variable can be shared with
         * the given agent.
         *
         * @param objName Value name
         * @param agent Destination agent
         * @return <code>true</code>, if that value for this variable can be
         * shared with the destination agent; <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean shareable(String objName, String agent) {
            boolean res = false;
            int agIndex = agentIndex.get(agent);
            if (!objectIndex.containsKey(objName)) {
                return false;
            }
            int valueIndex = objectIndex.get(objName);
            ArrayList<GroundedSharedData> sdList = sharedDataByFunction.get(fncIndex);
            for (GroundedSharedData sd : sdList) {
                if (sd.isShareable(this, valueIndex, agIndex)) {
                    res = true;
                    break;
                }
            }
            return res;
        }

        /**
         * Checks whether the given variable can be shared with the given agent.
         *
         * @param agent Destination agent
         * @return <code>true</code>, if the values of this variable can be
         * shared with the destination agent; <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean shareable(String agent) {
            boolean res = false;
            int agIndex = agentIndex.get(agent);
            for (GroundedSharedData sd : sharedDataByFunction.get(fncIndex)) {
                if (sd.isShareable(this, agIndex)) {
                    res = true;
                    break;
                }
            }
            return res;
        }

        /**
         * List of reachable values for this variable.
         *
         * @return Array of reachable values for this variable
         * @since 1.0
         */
        @Override
        public String[] getReachableValues() {
            ArrayList<Integer> pv = getAllDomainValues(domainIndex);
            ArrayList<String> rv = new ArrayList<>(pv.size());
            for (Integer objIndex : pv) {
                Integer gvIndex = valueIndex.get(new GroundedValue(varIndex, objIndex));
                if (gvIndex != null) {
                    rv.add(objects.get(objIndex));
                }
            }
            return rv.toArray(new String[rv.size()]);
        }

        /**
         * Returns the list of types for a given parameter.
         *
         * @param paramNumber Number of parameter (0 .. getParams().length - 1)
         * @return Array of types
         * @since 1.0
         */
        @Override
        public String[] getParamTypes(int paramNumber) {
            Function f = functions.get(fncIndex);
            Parameter p = f.getParameters()[paramNumber];
            return p.getTypes();
        }

        /**
         * Checks if this variable is boolean, i.e. that its values can be only
         * <code>true</code> or <code>false</code>.
         *
         * @return <code>true</code>, it this variable is boolean;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean isBoolean() {
            return domainIndex[0] == booleanTypeIndex;
        }
    }

    /**
     * Grounded numeric effects. Only to increase the value of a numeric
     * variable is supported.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    public static class GroundedNumericEffImp implements GroundedNumericEff {

        int type;                       // Operator type (GroundedNumericEff.INCREASE)
        GroundedVar var;                // Numeric variable
        GroundedNumericExpression exp;  // Numeric expression

        /**
         * Creates a new numeric effect.
         *
         * @param type Operator type
         * @param var Numeric variable
         * @param exp Numeric expression
         * @since 1.0
         */
        GroundedNumericEffImp(int type, GroundedVar var, GroundedNumericExpression exp) {
            this.type = type;
            this.var = var;
            this.exp = exp;
        }

        /**
         * Returns the operator type (INCREASE).
         *
         * @return Operator type
         * @since 1.0
         */
        @Override
        public int getType() {
            return type;
        }

        /**
         * Returns the grounded numeric variable.
         *
         * @return Grounded numeric variable
         * @since 1.0
         */
        @Override
        public GroundedVar getVariable() {
            return var;
        }

        /**
         * Gets the numeric expression defined to update the value of the
         * variable.
         *
         * @return Numeric expression
         * @since 1.0
         */
        @Override
        public GroundedNumericExpression getExpression() {
            return exp;
        }
    }

    /**
     * Grounded numeric expression to define numeric action effects.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    public static class GroundedNumericExpressionImp implements GroundedNumericExpression {

        int type;           // Expression type. See constants in GroundedNumericExpression interface
        double value;                           // Numeric value
        GroundedVar var;                        // Numeric variable
        GroundedNumericExpression left, right;  // Operands

        /**
         * Creates a new numeric expression (constant value)
         *
         * @param type Expression type
         * @param value Numeric value
         * @since 1.0
         */
        GroundedNumericExpressionImp(int type, double value) {
            this.type = type;
            this.value = value;
        }

        /**
         * Creates a new numeric expression (numeric variable).
         *
         * @param var Numeric variable
         * @since 1.0
         */
        GroundedNumericExpressionImp(GroundedVar var) {
            type = VARIABLE;
            this.var = var;
        }

        /**
         * Creates a new numeric expression.
         *
         * @param type Expression type
         * @since 1.0
         */
        GroundedNumericExpressionImp(int type) {
            this.type = type;
        }

        /**
         * Creates a new numeric expression (operation).
         *
         * @param type Expression type
         * @param left Left operand
         * @param right Right operand
         * @since 1.0
         */
        GroundedNumericExpressionImp(int type, GroundedNumericExpression left, GroundedNumericExpression right) {
            this.type = type;
            this.left = left;
            this.right = right;
        }

        /**
         * Returns the expression type.
         *
         * @return Expression type
         * @since 1.0
         */
        @Override
        public int getType() {
            return type;
        }

        /**
         * If type == NUMBER, returns the numeric value.
         *
         * @return Numeric value
         * @since 1.0
         */
        @Override
        public double getValue() {
            return value;
        }

        /**
         * If type == VARIABLE, returns the grounded variable.
         *
         * @return Grounded variable
         * @since 1.0
         */
        @Override
        public GroundedVar getVariable() {
            return var;
        }

        /**
         * If type == ADD, DEL, PROD or DIV, retuns the left operand.
         *
         * @return Left operand of the expression
         * @since 1.0
         */
        @Override
        public GroundedNumericExpression getLeftOperand() {
            return left;
        }

        /**
         * If type == ADD, DEL, PROD or DIV, retuns the right operand.
         *
         * @return Right operand of the expression
         * @since 1.0
         */
        @Override
        public GroundedNumericExpression getRightOperand() {
            return right;
        }

        /**
         * Gets a description of this expression.
         *
         * @return Expression description
         * @since 1.0
         */
        @Override
        public String toString() {
            switch (type) {
                case NUMBER:
                    return "" + value;
                case VARIABLE:
                    return var.toString();
                case ADD:
                    return "(+ (" + left + ") (" + right + "))";
                case DEL:
                    return "(- (" + left + ") (" + right + "))";
                case PROD:
                    return "(* (" + left + ") (" + right + "))";
                case DIV:
                    return "(/ (" + left + ") (" + right + "))";
                case USAGE:
                    return "(usage)";
                default:
                    return "<error>";
            }
        }
    }

    /**
     * Pair (variable index, value index) for the RPG.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    public class GroundedValue implements ReachedValue {

        // Serial number for serialization
        private static final long serialVersionUID = -9105490290945167341L;
        int varIndex;           // Variable index
        int valueIndex;         // Value index
        int minTime[];		// Minimum time in which this variable can have this value for each agent

        /**
         * Initializes a pair (variable, value)
         *
         * @param varIndex Variable index
         * @param valueIndex Value index
         * @since 1.0
         */
        public GroundedValue(int varIndex, int valueIndex) {
            this.varIndex = varIndex;
            this.valueIndex = valueIndex;
        }

        /**
         * Check if two pairs are equal.
         *
         * @param x Another pair to compare
         * @return <code>true</code>, if both pairs are equal;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            GroundedValue v = (GroundedValue) x;
            return varIndex == v.varIndex && valueIndex == v.valueIndex;
        }

        /**
         * Gets a hash code for this pair.
         *
         * @return Hash code
         * @since 1.0
         */
        @Override
        public int hashCode() {
            return varIndex * 131071 + valueIndex;
        }

        /**
         * Returns the variable.
         *
         * @return Variable
         * @since 1.0
         */
        GroundedVarImp var() {
            return vars.get(varIndex);
        }

        /**
         * Gets the minimum time for the variable to get this value.
         *
         * @return Minimum time for the variable to get this value
         * @since 1.0
         */
        @Override
        public int getMinTime() {
            int min = minTime[0];
            for (int i = 1; i < minTime.length; i++) {
                if (minTime[i] != -1 && (min == -1 || minTime[i] < min)) {
                    min = minTime[i];
                }
            }
            return min;
        }

        /**
         * Gets the involved variable.
         *
         * @return Grounded variable
         * @since 1.0
         */
        @Override
        public GroundedVar getVar() {
            return var();
        }

        /**
         * Gets the value for this variable.
         *
         * @return Value name
         * @since 1.0
         */
        @Override
        public String getValue() {
            return objects.get(valueIndex);
        }

        /**
         * Returns a description of this pair.
         *
         * @return Description of this reached value
         * @since 1.0
         */
        @Override
        public String toString() {
            return "(= " + var() + " " + getValue() + ")[" + getMinTime() + "]";
        }

        /**
         * Checks if this value can be shared to another agent.
         *
         * @param agName Name of the destination agent
         * @return <code>true</code>, if this value for this variable can be
         * shared with the destination agent; <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean shareable(String agName) {
            return var().shareable(getValue(), agName);
        }
    }

    /**
     * Action condition or effect (also used for goals)
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    public class ActionCondition implements GroundedCond, GroundedEff {

        // Serial number for serialization
        private static final long serialVersionUID = -8669437306147623737L;
        GroundedValue gv;       // Pair (variable index, value index)
        int condition;		// EQUAL/DISTINCT for conditions (-1 for effects)

        /**
         * Creates a new effect.
         *
         * @param gv Pair (variable index, value index)
         * @since 1.0
         */
        public ActionCondition(GroundedValue gv) {
            this.gv = gv;
            condition = -1;
        }

        /**
         * Creates a new precondition.
         *
         * @param gv Pair (variable index, value index)
         * @param isEqual <code>true</code> for EQUAL conditions;
         * <code>false</code> for DISTINCT
         * @since 1.0
         */
        public ActionCondition(GroundedValue gv, boolean isEqual) {
            this.gv = gv;
            if (isEqual) {
                condition = GroundedCond.EQUAL;
            } else {
                condition = GroundedCond.DISTINCT;
            }
        }

        /**
         * Createa a new precondition.
         *
         * @param cond Grounded condition
         * @since 1.0
         */
        public ActionCondition(GroundedCond cond) {
            this(cond.getCondition(), cond.getVar(), cond.getValue());
        }

        /**
         * Creates a new effect.
         *
         * @param eff Grounded effect
         * @since 1.0
         */
        public ActionCondition(GroundedEff eff) {
            this(-1, eff.getVar(), eff.getValue());
        }

        /**
         * Creates a new precondition.
         *
         * @param condition Condition type
         * @param var Grounded variable
         * @param value Value
         * @since 1.0
         */
        public ActionCondition(int condition, GroundedVar var, String value) {
            this.condition = condition;
            int valueIndex = getObjectIndex(value);
            int variableIndex = varIndex.get(var);
            gv = new GroundedValue(variableIndex, valueIndex);
        }

        /**
         * Returns the condition type (EQUAL or DISTINCT).
         *
         * @return Condition type
         * @since 1.0
         */
        @Override
        public int getCondition() {
            return condition;
        }

        /**
         * Returns the grounded variable.
         *
         * @return Grounded variable
         * @since 1.0
         */
        @Override
        public GroundedVar getVar() {
            return gv.var();
        }

        /**
         * Returns the value (object name, 'undefined' is not allowed).
         *
         * @return Value
         * @since 1.0
         */
        @Override
        public String getValue() {
            return gv.getValue();
        }

        /**
         * Returns a description of this condition.
         *
         * @return Condition description
         * @since 1.0
         */
        @Override
        public String toString() {
            String res = condition != GroundedCond.DISTINCT ? "=" : "<>";
            return res + " (" + gv.var() + ") " + gv.getValue();
        }

    }

    /**
     * Planning action (grounded operator).
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    public class ActionImp implements Action, GroundedRule {

        // Serial number for serialization
        private static final long serialVersionUID = 379765009600369268L;
        String opName;                      // Operator name
        String params[];                    // Action parameters
        int paramIndex[];                   // Action parameters indexes
        ActionCondition prec[];             // Action preconditions
        ActionCondition eff[];              // Action effects
        GroundedNumericEff[] numEff;        // Action numeric effects
        ArrayList<GroundedVar> mutexVar;    // List of mutex variables

        /**
         * Creates a new action.
         *
         * @param opName Operator name
         * @param numParams Number of parameters
         * @param numPrecs Number of preconditions
         * @param numEffs Number of effects
         * @since 1.0
         */
        public ActionImp(String opName, int numParams, int numPrecs, int numEffs) {
            this.opName = opName;
            params = new String[numParams];
            paramIndex = new int[numParams];
            prec = new ActionCondition[numPrecs];
            eff = new ActionCondition[numEffs];
            mutexVar = null;
        }

        /**
         * Sets a parameter value.
         *
         * @param paramIndex Parameter index
         * @param objIndex Value index
         * @param objName Value name
         * @since 1.0
         */
        public void setParam(int paramIndex, int objIndex, String objName) {
            params[paramIndex] = objName;
            this.paramIndex[paramIndex] = objIndex;
        }

        /**
         * Returns the action description.
         *
         * @return Action description
         * @since 1.0
         */
        @Override
        public String toString() {
            String res = opName;
            for (String param : params) {
                res += " " + param;
            }
            return res;
        }

        /**
         * Returns the operator name.
         *
         * @return Operator name
         * @since 1.0
         */
        @Override
        public String getOperatorName() {
            return opName;
        }

        /**
         * Returns the list of parameters (list of objects).
         *
         * @return Array of parameters
         * @since 1.0
         */
        @Override
        public String[] getParams() {
            return params;
        }

        /**
         * Optimize structures after grounding.
         *
         * @since 1.0
         */
        @Override
        public void optimize() {
            int n = 0;
            for (ActionCondition c : prec) {
                if (!staticFunction.get(c.gv.var().fncIndex)) {
                    n++;
                }
            }
            ActionCondition[] auxP = new ActionCondition[n];
            n = 0;
            for (ActionCondition c : prec) {
                if (!staticFunction.get(c.gv.var().fncIndex)) {
                    auxP[n++] = c;
                }
            }
            prec = auxP;
            n = 0;
            for (ActionCondition c : eff) {
                if (!staticFunction.get(c.gv.var().fncIndex)) {
                    n++;
                }
            }
            ActionCondition[] auxE = new ActionCondition[n];
            n = 0;
            for (ActionCondition c : eff) {
                if (!staticFunction.get(c.gv.var().fncIndex)) {
                    auxE[n++] = c;
                }
            }
            eff = auxE;
        }

        /**
         * Gets the action preconditions.
         *
         * @return Array of preconditions
         * @since 1.0
         */
        @Override
        public GroundedCond[] getPrecs() {
            return prec;
        }

        /**
         * Gets the action effects.
         *
         * @return Array of effects
         * @since 1.0
         */
        @Override
        public GroundedEff[] getEffs() {
            return eff;
        }

        /**
         * Returns the rule name
         *
         * @return Name of the rule
         * @since 1.0
         */
        @Override
        public String getRuleName() {
            return opName;
        }

        /**
         * Returns the body of the rule
         *
         * @return Array of grounded conditions
         * @since 1.0
         */
        @Override
        public GroundedCond[] getBody() {
            return getPrecs();
        }

        /**
         * Returns the head of the rule
         *
         * @return Array of grounded effects
         * @since 1.0
         */
        @Override
        public GroundedEff[] getHead() {
            return getEffs();
        }

        /**
         * Minimum time, according to the disRPG, in which the action can be
         * executed.
         *
         * @return Minimum time needed to execute this action
         * @since 1.0
         */
        @Override
        public int getMinTime() {
            int t = 0;
            for (ActionCondition c : prec) {
                if (c.condition == ActionCondition.EQUAL) {
                    int vt = c.getVar().getMinTime(c.getValue());
                    if (vt > t) {
                        t = vt;
                    }
                }
            }
            return t;
        }

        /**
         * Adds an effect to the action.
         *
         * @param effIndex Effect index
         * @param gv Pair (variable index, value index)
         * @return <code>false</code>, if a contradictory effect is found;
         * <code>true</code>, otherwise
         * @since 1.0
         */
        public boolean addEffect(int effIndex, GroundedValue gv) {
            if ((sameObjects & SAME_OBJECTS_REP_PARAMS) != 0) {
                for (String param : gv.getVar().getParams()) {
                    if (param.equals(gv.getValue())) {
                        return false;
                    }
                }
            }
            if ((sameObjects & SAME_OBJECTS_PREC_EQ_EFF) != 0) {
                for (ActionCondition c : prec) {
                    if (c.condition == ActionCondition.EQUAL
                            && c.gv.varIndex == gv.varIndex
                            && c.gv.valueIndex == gv.valueIndex) {
                        return false;
                    }
                }
            }
            eff[effIndex] = new ActionCondition(gv);
            return true;
        }

        /**
         * Adds a precondition to the action.
         *
         * @param precIndex Precondition index
         * @param gv Pair (variable index, value index)
         * @param truePrec <code>true</code> for EQUAL conditions;
         * <code>false</code> for DISTINCT
         * @since 1.0
         */
        public void addPrecondition(int precIndex, GroundedValue gv, boolean truePrec) {
            prec[precIndex] = new ActionCondition(gv, truePrec);
        }

        /**
         * Adds additional preconditions to the action.
         *
         * @param precIndex Precondition index
         * @param gv Pair (variable index, value index)
         * @param truePrec <code>true</code> for EQUAL conditions;
         * <code>false</code> for DISTINCT
         * @since 1.0
         */
        public void addAdditionalPrecondition(int precIndex, GroundedValue gv, boolean truePrec) {
            ActionCondition aux[] = new ActionCondition[prec.length + 1];
            for (int i = 0; i < precIndex; i++) {
                aux[i] = prec[i];
            }
            for (int i = precIndex; i < prec.length; i++) {
                aux[i + 1] = prec[i];
            }
            prec = aux;
            prec[precIndex] = new ActionCondition(gv, truePrec);
        }

        /**
         * Checks if this action requires a variable to have a certain value.
         *
         * @param var Grounded variable
         * @return <code>true</code>, if <code>var</code> is in the
         * preconditions of this action; <code>false</code>, otherwise
         * @since 1.0
         */
        public boolean requiresVar(GroundedVar var) {
            for (GroundedCond p : this.prec) {
                if (p.getVar().equals(var)) {
                    return true;
                }
            }
            return false;
        }

        /**
         * Gets the action numeric effects.
         *
         * @return Array of numeric effects
         * @since 1.0
         */
        @Override
        public GroundedNumericEff[] getNumEffs() {
            return numEff;
        }

        /**
         * Adds a mutex variable in this action.
         *
         * @param var Grounded variable
         * @since 1.0
         */
        void addMutexVariable(GroundedVar var) {
            if (mutexVar == null) {
                mutexVar = new ArrayList<>(1);
            }
            if (!mutexVar.contains(var)) {
                mutexVar.add(var);
            }
        }

        /**
         * Check if this action and a given one are mutex, i.e. if this action
         * deletes a precondition or add effect of the other action, or vice
         * versa.
         *
         * @param a Another action
         * @return <code>true</code>, if both actions are mutex;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean isMutex(Action a) {
            ActionImp ai = (ActionImp) a;
            return this.deletesPrecOrEff(ai) || ai.deletesPrecOrEff(this);
        }

        /**
         * Checks if this action deletes a precondition or effect of another
         * action.
         *
         * @param a Another action
         * @return <code>true</code>, if this action deletes a precondition or
         * effect of the other action; <code>false</code>, otherwise
         * @since 1.0
         */
        private boolean deletesPrecOrEff(ActionImp a) {
            for (ActionCondition e : this.eff) {
                GroundedVar v = e.getVar();
                String value = e.getValue();
                for (ActionCondition prec : a.prec) {
                    if (prec.getVar().equals(v)) {
                        if (prec.getCondition() == ActionCondition.EQUAL) {
                            if (!value.equalsIgnoreCase(prec.getValue())) {
                                return true;
                            }
                        } else {
                            if (value.equalsIgnoreCase(prec.getValue())) {
                                return true;
                            }
                        }
                    }
                }
                for (ActionCondition eff2 : a.eff) {
                    if (eff2.getVar().equals(v) && !value.equalsIgnoreCase(eff2.getValue())) {
                        return true;
                    }
                }
                if (a.mutexVar != null && a.mutexVar.contains(v)) {
                    return true;
                }
            }
            if (mutexVar != null) {
                for (GroundedVar v : mutexVar) {
                    if (a.requiresVar(v)) {
                        return true;
                    }
                    for (ActionCondition e : a.eff) {
                        if (e.getVar().equals(v)) {
                            return true;
                        }
                    }
                    if (a.mutexVar != null && a.mutexVar.contains(v)) {
                        return true;
                    }
                }
            }
            return false;
        }
    }

    /**
     * Grounded shared data.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    public class GroundedSharedData implements java.io.Serializable {

        // Serial number for serialization
        private static final long serialVersionUID = -2147732192053461311L;
        int agents[];			// Data shared with these agents
        int fncIndex;			// Function index
        int params[];			// Object index (or -1 it it is a variable)
        int paramTypes[][];		// If the parameter is a variable, this array stores its types
        int valueTypes[];		// Domain types

        /**
         * Grounds a shared data.
         *
         * @param sd Shared data
         * @since 1.0
         */
        public GroundedSharedData(SharedData sd) {
            String ag[] = sd.getAgents();		// Agents
            agents = new int[ag.length];
            for (int i = 0; i < ag.length; i++) {
                agents[i] = agentIndex.get(ag[i]);
            }
            Function f = sd.getFunction();		// Function
            fncIndex = functionIndex.get(f.getName());
            Parameter fparams[] = f.getParameters();	// Parameters
            int numParams = fparams.length;
            if (f.isMultifunction()) {
                numParams++;
            }
            params = new int[numParams];
            paramTypes = new int[numParams][];
            for (int i = 0; i < fparams.length; i++) {
                Parameter fparam = fparams[i];
                if (fparam.getName().startsWith("?")) {
                    params[i] = -1;
                    String types[] = fparam.getTypes();
                    paramTypes[i] = new int[types.length];
                    for (int j = 0; j < types.length; j++) {
                        paramTypes[i][j] = typeIndex.get(types[j]);
                    }
                } else {
                    params[i] = objectIndex.get(fparam.getName());
                }
            }						// Domain
            if (f.isMultifunction()) {	// The value is the last parameter in multi-functions
                int i = params.length - 1;
                String types[] = f.getDomain();
                paramTypes[i] = new int[types.length];
                for (int j = 0; j < types.length; j++) {
                    paramTypes[i][j] = typeIndex.get(types[j]);
                }
                valueTypes = new int[1];
                valueTypes[0] = typeIndex.get("boolean");
            } else {
                String types[] = f.getDomain();
                valueTypes = new int[types.length];
                for (int j = 0; j < types.length; j++) {
                    valueTypes[j] = typeIndex.get(types[j]);
                }
            }
        }

        /**
         * Checks if the given variable can be shared with another agent.
         *
         * @param v Grounded variable
         * @param agIndex Index of the destination agent
         * @return <code>true</code>, if this variable can be shared with the
         * destination agent; <code>false</code>, otherwise
         * @since 1.0
         */
        public boolean isShareable(GroundedVarImp v, int agIndex) {
            if (fncIndex != v.fncIndex) {
                return false;
            }
            boolean validAgent = false;
            for (int i = 0; i < agents.length; i++) {
                if (agents[i] == agIndex) {
                    validAgent = true;
                    break;
                }
            }
            if (!validAgent) {
                return false;
            }
            for (int i = 0; i < params.length; i++) {
                if (params[i] == -1) {
                    if (!objectIsCompatible(v.paramIndex[i], paramTypes[i])) {
                        return false;
                    }
                } else if (params[i] != v.paramIndex[i]) {
                    return false;
                }
            }
            return true;
        }

        /**
         * Returns true if the given variable value can be shared with the given
         * agent.
         *
         * @param v Variable
         * @param valueIndex Value
         * @param agIndex Agent
         * @return <code>true</code>, if the given value can be shared;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        public boolean isShareable(GroundedVarImp v, int valueIndex, int agIndex) {
            if (fncIndex != v.fncIndex) {
                return false;
            }
            boolean validAgent = false;
            for (int i = 0; i < agents.length; i++) {
                if (agents[i] == agIndex) {
                    validAgent = true;
                    break;
                }
            }
            if (!validAgent) {
                return false;
            }
            for (int i = 0; i < params.length; i++) {
                if (params[i] == -1) {
                    if (!objectIsCompatible(v.paramIndex[i], paramTypes[i])) {
                        return false;
                    }
                } else if (params[i] != v.paramIndex[i]) {
                    return false;
                }
            }
            return objectIsCompatible(valueIndex, valueTypes);
        }
    }

    /**
     * Grounded metric function.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @since 1.0
     */
    public class GroundedMetric {

        // Metric function types
        public static final int MT_PREFERENCE = 0;
        public static final int MT_ADD = 1;
        public static final int MT_MULT = 2;
        public static final int MT_NUMBER = 3;
        public static final int MT_TOTAL_TIME = 4;
        public static final int MT_NONE = 5;
        int metricType;                 // Metric function type
        double number;			// Numeric value, if metricType = MT_NUMBER
        GroundedCond preference;	// Preference, if metricType = MT_PREFERENCE
        ArrayList<GroundedMetric> term;	// Otherwise

        /**
         * Grounds the metric function.
         *
         * @param m Metric function
         * @since 1.0
         */
        public GroundedMetric(Metric m) {
            metricRequiresMakespan = false;
            if (m == null) {
                metricType = MT_NONE;
            } else {
                metricType = m.getMetricType();
                switch (metricType) {
                    case MT_PREFERENCE:
                        int prefIndex = preferenceIndex.get(m.getPreference());
                        preference = preferences.get(prefIndex);
                        break;
                    case MT_TOTAL_TIME:
                        metricRequiresMakespan = true;
                        break;
                    case MT_NUMBER:
                        number = m.getNumber();
                        break;
                    default:
                        int n = m.getNumTerms();
                        term = new ArrayList<>();
                        for (int i = 0; i < n; i++) {
                            term.add(new GroundedMetric(m.getTerm(i)));
                        }

                }
            }
        }

    }

}
