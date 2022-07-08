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
package org.agreement_technologies.service.map_parser;

import java.text.ParseException;
import java.util.ArrayList;
import org.agreement_technologies.common.map_parser.Congestion;
import org.agreement_technologies.common.map_parser.CongestionFluent;
import org.agreement_technologies.common.map_parser.CongestionPenalty;
import org.agreement_technologies.common.map_parser.CongestionUsage;
import org.agreement_technologies.common.map_parser.Fact;
import org.agreement_technologies.common.map_parser.Metric;
import org.agreement_technologies.common.map_parser.NumericEffect;
import org.agreement_technologies.common.map_parser.NumericExpression;
import org.agreement_technologies.common.map_parser.NumericFact;
import org.agreement_technologies.common.map_parser.Task;
import org.agreement_technologies.service.map_parser.SynAnalyzer.Symbol;

/**
 * Implementation of an ungrounded planning task. Stores the problem and domain
 * information of a parsed planning task.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class TaskImp implements Task {

    static final int OBJECT_TYPE = 0;	// Index of the predefined type 'object'
    static final int BOOLEAN_TYPE = 1;	// Index of the predefined type 'boolean'
    static final int AGENT_TYPE = 2;	// Index of the predefined type 'agent'
    static final int NUMBER_TYPE = 3;	// Index of the predefined type 'number'

    static final int TRUE_VALUE = 0;	// Index of the predefined object 'true'
    static final int FALSE_VALUE = 1;	// Index of the predefined object 'false'

    String domainName;						// Domain name
    String problemName;						// Problem name
    ArrayList<String> requirements;			// Requirements list
    ArrayList<Type> types;				// Variable types
    ArrayList<Value> values;				// Objects and constants
    ArrayList<Variable> predicates;			// Predicates
    ArrayList<Function> functions;			// Functions and multi-functions
    ArrayList<Operator> operators;			// Operators list
    ArrayList<SharedData> sharedData;                   // Shared predicates/functions
    ArrayList<Assignment> init;				// Init section
    ArrayList<Operator> beliefs;			// Belief rules
    ArrayList<Assignment> gGoals;			// Global goals
    ArrayList<PreferenceImp> preferences;		// Preferences
    ArrayList<CongestionImp> congestions;               // Congestions
    MetricImp metric;                                   // Metric
    double selfInterest;				// Self-interest level
    double metricThreshold;				// Metric threshold

    /**
     * Crates an empty planning task.
     *
     * @since 1.0
     */
    public TaskImp() {
        types = new ArrayList<>();
        types.add(new Type("object"));			// Predefined type
        types.add(new Type("boolean"));			// Predefined type
        types.add(new Type("agent"));			// Predefined type
        types.add(new Type("number"));			// Predefined type
        requirements = new ArrayList<>();
        values = new ArrayList<>();
        Value bv = new Value("true");			// Predefined object "true"
        bv.types.add(types.get(BOOLEAN_TYPE));
        values.add(bv);
        bv = new Value("false");				// Predefined object "false"
        bv.types.add(types.get(BOOLEAN_TYPE));
        values.add(bv);
        predicates = new ArrayList<>();
        functions = new ArrayList<>();
        operators = new ArrayList<>();
        sharedData = new ArrayList<>();
        init = new ArrayList<>();
        beliefs = new ArrayList<>();
        gGoals = new ArrayList<>();
        preferences = new ArrayList<>();
        congestions = new ArrayList<>();
        metric = null;
        selfInterest = 0;
        metricThreshold = 0;
    }

    /**
     * Adds a planning requirement.
     *
     * @param reqName	Requirement name
     * @since 1.0
     */
    public void addRequirement(String reqName) {
        if (!requirements.contains(reqName)) {
            requirements.add(reqName);
        }
    }

    /**
     * Checks whether the variable is already defined.
     *
     * @param v	Variable
     * @return <code>true</code>, if the variable is already defined;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean existVariable(Variable v) {
        if (predicates.contains(v)) {
            return true;
        }
        return functions.contains(new Function(v, false));
    }

    /**
     * Return the agent type.
     *
     * @return Agent type
     * @since 1.0
     */
    public Type getAgentType() {
        int typeIndex = types.indexOf(new Type("agent"));
        if (typeIndex == -1) {
            return null;
        }
        return types.get(typeIndex);
    }

    /**
     * Returns the domain name.
     *
     * @return Domain name
     * @since 1.0
     */
    @Override
    public String getDomainName() {
        return domainName;
    }

    /**
     * Return the problem name.
     *
     * @return Problem name
     * @since 1.0
     */
    @Override
    public String getProblemName() {
        return problemName;
    }

    /**
     * Returns the requirements list.
     *
     * @return Array of strings, each string representing a requirement
     * specified in the domain file. Supported requirements are: strips, typing,
     * negative-preconditions and object-fluents
     * @since 1.0
     */
    @Override
    public String[] getRequirements() {
        String res[] = new String[requirements.size()];
        for (int i = 0; i < res.length; i++) {
            res[i] = requirements.get(i);
        }
        return res;
    }

    /**
     * Returns the list of types.
     *
     * @return Array of strings, each string is a type defined in the domain
     * file
     * @since 1.0
     */
    @Override
    public String[] getTypes() {
        String res[] = new String[types.size()];
        for (int i = 0; i < res.length; i++) {
            res[i] = types.get(i).name;
        }
        return res;
    }

    /**
     * Returns the base types of a given type.
     *
     * @param type Name of the type
     * @return Array of strings which contains the super-types for the given
     * type
     * @since 1.0
     */
    @Override
    public String[] getParentTypes(String type) {
        int index = types.indexOf(new Type(type));
        if (index == -1) {
            return null;
        }
        Type t = types.get(index);
        String res[] = new String[t.parentTypes.size()];
        for (int i = 0; i < res.length; i++) {
            res[i] = t.parentTypes.get(i).name;
        }
        return res;
    }

    /**
     * Returns the list of objects.
     *
     * @return Array of string containing the names of the objects declared in
     * the domain (constants section) and problem (objects section) files
     * @since 1.0
     */
    @Override
    public String[] getObjects() {
        String res[] = new String[values.size()];
        for (int i = 0; i < res.length; i++) {
            res[i] = values.get(i).name;
        }
        return res;
    }

    /**
     * Returns the type list of a given object.
     *
     * @param objName Object name
     * @return Array of string containing the set of types of the given object
     * @since 1.0
     */
    @Override
    public String[] getObjectTypes(String objName) {
        int index = values.indexOf(new Value(objName));
        if (index == -1) {
            return null;
        }
        Value v = values.get(index);
        String res[] = new String[v.types.size()];
        for (int i = 0; i < res.length; i++) {
            res[i] = v.types.get(i).name;
        }
        return res;
    }

    /**
     * Returns the list of functions (predicates are also included as they are
     * considered boolean functions).
     *
     * @return Array of functions defined in the domain file
     * @since 1.0
     */
    @Override
    public org.agreement_technologies.common.map_parser.Function[] getFunctions() {
        TaskTypes.FunctionImp res[] = new TaskTypes.FunctionImp[predicates.size() + functions.size()];
        TaskTypes.FunctionImp f;
        Variable v;
        Value param;
        for (int i = 0; i < predicates.size(); i++) {
            v = predicates.get(i);
            f = new TaskTypes.FunctionImp(v.name, false);
            f.parameters = new TaskTypes.ParameterImp[v.params.size()];
            for (int p = 0; p < f.parameters.length; p++) {
                param = v.params.get(p);
                f.parameters[p] = new TaskTypes.ParameterImp(param.name);
                f.parameters[p].types = new String[param.types.size()];
                for (int t = 0; t < param.types.size(); t++) {
                    f.parameters[p].types[t] = param.types.get(t).name;
                }
            }
            f.domain = new String[1];
            f.domain[0] = types.get(BOOLEAN_TYPE).name;
            res[i] = f;
        }
        for (int i = 0; i < functions.size(); i++) {
            Function fnc = functions.get(i);
            v = fnc.var;
            f = new TaskTypes.FunctionImp(v.name, fnc.multiFunction);
            f.parameters = new TaskTypes.ParameterImp[v.params.size()];
            for (int p = 0; p < f.parameters.length; p++) {
                param = v.params.get(p);
                f.parameters[p] = new TaskTypes.ParameterImp(param.name);
                f.parameters[p].types = new String[param.types.size()];
                for (int t = 0; t < param.types.size(); t++) {
                    f.parameters[p].types[t] = param.types.get(t).name;
                }
            }
            f.domain = new String[fnc.domain.size()];
            for (int t = 0; t < f.domain.length; t++) {
                f.domain[t] = fnc.domain.get(t).name;
            }
            res[i + predicates.size()] = f;
        }
        return res;
    }

    /**
     * Returns the list of operators.
     *
     * @return Array of operators defined in the domain file
     * @since 1.0
     */
    @Override
    public org.agreement_technologies.common.map_parser.Operator[] getOperators() {
        TaskTypes.OperatorImp res[] = new TaskTypes.OperatorImp[operators.size()];
        for (int i = 0; i < res.length; i++) {
            res[i] = getOperator(operators.get(i));
        }
        return res;
    }

    /**
     * Returns a parsed operator.
     *
     * @param operator Stored operator
     * @return Parsed operator
     * @since 1.0
     */
    private TaskTypes.OperatorImp getOperator(Operator operator) {
        TaskTypes.OperatorImp op = new TaskTypes.OperatorImp(operator.name,
                operator.preference);
        op.parameters = new TaskTypes.ParameterImp[operator.params.size()];
        for (int i = 0; i < op.parameters.length; i++) {
            Value p = operator.params.get(i);
            op.parameters[i] = new TaskTypes.ParameterImp(p.name);
            op.parameters[i].types = new String[p.types.size()];
            for (int t = 0; t < p.types.size(); t++) {
                op.parameters[i].types[t] = p.types.get(t).name;
            }
        }
        op.prec = getOperatorCondition(operator.prec, true);
        op.eff = getOperatorCondition(operator.eff, false);
        op.numEff = getOperatorNumericEffects(operator.eff);
        return op;
    }

    /**
     * Returns a list of parsed conditions.
     *
     * @param cond Stored condition
     * @param cmp <code>true</code>, if it is a comparison; <code>false</code>,
     * for assignments
     * @return Parsed conditions
     * @since 1.0
     */
    private TaskTypes.ConditionImp[] getOperatorCondition(ArrayList<OperatorCondition> cond, boolean cmp) {
        int numConditions = 0;
        for (OperatorCondition oc : cond) {
            if (oc.type != OperatorConditionType.CT_INCREASE) {
                numConditions++;
            }
        }
        TaskTypes.ConditionImp[] res = new TaskTypes.ConditionImp[numConditions];
        numConditions = 0;
        for (OperatorCondition oc : cond) {
            if (oc.type == OperatorConditionType.CT_INCREASE) {
                continue;
            }
            Variable varCond = null;
            Function fncCond = null;
            int index = this.predicates.indexOf(new Variable(oc.var.name));
            if (index == -1) {	// Function
                index = this.functions.indexOf(new Function(new Variable(oc.var.name), false));
                fncCond = this.functions.get(index);
            } else {			// Predicate
                varCond = this.predicates.get(index);
            }
            res[numConditions] = new TaskTypes.ConditionImp();
            switch (oc.type) {
                case CT_NONE:	// Predicate
                    if (cmp) {
                        res[numConditions].type = TaskTypes.ConditionImp.EQUAL;
                    } else {
                        res[numConditions].type = TaskTypes.ConditionImp.ASSIGN;
                    }
                    break;
                case CT_EQUAL:
                    if (oc.neg) {
                        res[numConditions].type = TaskTypes.ConditionImp.DISTINCT;
                    } else {
                        res[numConditions].type = TaskTypes.ConditionImp.EQUAL;
                    }
                    break;
                case CT_MEMBER:
                    if (oc.neg) {
                        res[numConditions].type = TaskTypes.ConditionImp.NOT_MEMBER;
                    } else {
                        res[numConditions].type = TaskTypes.ConditionImp.MEMBER;
                    }
                    break;
                case CT_ASSIGN:
                    res[numConditions].type = TaskTypes.ConditionImp.ASSIGN;
                    break;
                case CT_ADD:
                    res[numConditions].type = TaskTypes.ConditionImp.ADD;
                    break;
                case CT_DEL:
                    res[numConditions].type = TaskTypes.ConditionImp.DEL;
                    break;
            }
            res[numConditions].fnc = new TaskTypes.FunctionImp(oc.var.name, fncCond != null && fncCond.multiFunction);
            res[numConditions].fnc.parameters = new TaskTypes.ParameterImp[oc.var.params.size()];
            for (int p = 0; p < oc.var.params.size(); p++) {
                Value param = oc.var.params.get(p);
                res[numConditions].fnc.parameters[p] = new TaskTypes.ParameterImp(param.name);
                res[numConditions].fnc.parameters[p].types = new String[param.types.size()];
                for (int t = 0; t < param.types.size(); t++) {
                    res[numConditions].fnc.parameters[p].types[t] = param.types.get(t).name;
                }
            }
            if (varCond != null) {	// Predicate
                res[numConditions].fnc.domain = new String[1];
                res[numConditions].fnc.domain[0] = this.types.get(BOOLEAN_TYPE).name;
                if (oc.neg) {
                    res[numConditions].value = this.values.get(FALSE_VALUE).name;
                } else {
                    res[numConditions].value = this.values.get(TRUE_VALUE).name;
                }
            } else {				// Function
                res[numConditions].fnc.domain = new String[fncCond.domain.size()];
                for (int t = 0; t < res[numConditions].fnc.domain.length; t++) {
                    res[numConditions].fnc.domain[t] = fncCond.domain.get(t).name;
                }
                res[numConditions].value = oc.value.name;
            }
            numConditions++;
        }
        return res;
    }

    /**
     * Returns the shared data, which defines the information the current agent
     * can share with the other ones.
     *
     * @return Array of shared data defined in the problem file
     * @since 1.0
     */
    @Override
    public org.agreement_technologies.common.map_parser.SharedData[] getSharedData() {
        TaskTypes.SharedDataImp[] sd = new TaskTypes.SharedDataImp[sharedData.size()];
        for (int i = 0; i < sd.length; i++) {
            SharedData sData = this.sharedData.get(i);
            sd[i] = new TaskTypes.SharedDataImp();
            Variable v = sData.var != null ? sData.var : sData.fnc.var;
            sd[i].fnc = new TaskTypes.FunctionImp(v.name, sData.fnc != null && sData.fnc.multiFunction);
            sd[i].fnc.parameters = new TaskTypes.ParameterImp[v.params.size()];
            for (int p = 0; p < v.params.size(); p++) {
                Value param = v.params.get(p);
                sd[i].fnc.parameters[p] = new TaskTypes.ParameterImp(param.name);
                sd[i].fnc.parameters[p].types = new String[param.types.size()];
                for (int t = 0; t < param.types.size(); t++) {
                    sd[i].fnc.parameters[p].types[t] = param.types.get(t).name;
                }
            }
            if (sData.fnc == null) {	// Predicate
                sd[i].fnc.domain = new String[1];
                sd[i].fnc.domain[0] = this.types.get(BOOLEAN_TYPE).name;
            } else {					// Function
                sd[i].fnc.domain = new String[sData.fnc.domain.size()];
                for (int t = 0; t < sd[i].fnc.domain.length; t++) {
                    sd[i].fnc.domain[t] = sData.fnc.domain.get(t).name;
                }
            }
            sd[i].agents = new String[sData.agents.size()];
            for (int a = 0; a < sd[i].agents.length; a++) {
                sd[i].agents[a] = sData.agents.get(a).name;
            }
        }
        return sd;
    }

    /**
     * Returns the initial state information.
     *
     * @return Array of facts
     * @since 1.0
     */
    @Override
    public Fact[] getInit() {
        TaskTypes.FactImp res[] = new TaskTypes.FactImp[init.size()];
        for (int i = 0; i < res.length; i++) {
            res[i] = getFact(init.get(i));
        }
        return res;
    }

    /**
     * Returns a parsed fact.
     *
     * @param as Stored assignment
     * @return Parsed fact
     * @since 1.0
     */
    private TaskTypes.FactImp getFact(Assignment as) {
        Variable v = as.var != null ? as.var : as.fnc.var;
        TaskTypes.FactImp f = new TaskTypes.FactImp(v.name, as.neg);
        f.parameters = new String[as.params.size()];
        for (int i = 0; i < f.parameters.length; i++) {
            Value param = as.params.get(i);
            f.parameters[i] = param.name;
        }
        f.values = new String[as.values.size()];
        for (int i = 0; i < f.values.length; i++) {
            f.values[i] = as.values.get(i).name;
        }
        return f;
    }

    /**
     * Returns the list of belief rules.
     *
     * @return Array of belief rules
     * @since 1.0
     */
    @Override
    public org.agreement_technologies.common.map_parser.Operator[] getBeliefs() {
        TaskTypes.OperatorImp res[] = new TaskTypes.OperatorImp[beliefs.size()];
        for (int i = 0; i < res.length; i++) {
            res[i] = getOperator(beliefs.get(i));
        }
        return res;
    }

    /**
     * Returns the list of goals.
     *
     * @return Array of goals (facts)
     * @since 1.0
     */
    @Override
    public Fact[] getGoals() {
        TaskTypes.FactImp res[] = new TaskTypes.FactImp[gGoals.size()];
        for (int i = 0; i < res.length; i++) {
            res[i] = getFact(gGoals.get(i));
        }
        return res;
    }

    /**
     * Returns a description of this task.
     *
     * @return String with the task description
     * @since 1.0
     */
    @Override
    public String toString() {
        StringBuilder s = new StringBuilder();
        s.append("(domain ").append(domainName).append(")\n");
        s.append("(problem ").append(problemName).append(")\n");
        s.append("(requirements ").append(toString(getRequirements())).append(")\n");
        s.append("(types\n");
        for (String t : getTypes()) {
            s.append("\t").append(t);
            if (getParentTypes(t).length == 0) {
                s.append("\n");
            } else {
                s.append(" - ").append(toString(getParentTypes(t))).append("\n");
            }
        }
        s.append(")\n(objects\n");
        for (String o : getObjects()) {
            s.append("\t").append(o);
            if (getObjectTypes(o).length == 0) {
                s.append("\n");
            } else {
                s.append(" - ").append(toString(getObjectTypes(o))).append("\n");
            }
        }
        s.append(")\n(functions\n");
        for (org.agreement_technologies.common.map_parser.Function f : getFunctions()) {
            s.append("\t").append(f).append("\n");
        }
        for (org.agreement_technologies.common.map_parser.Operator o : getOperators()) {
            s.append(o).append("\n");
        }
        s.append("(shared-data\n");
        for (org.agreement_technologies.common.map_parser.SharedData d : getSharedData()) {
            s.append("\t").append(d).append("\n");
        }
        s.append(")\n(init\n");
        for (org.agreement_technologies.common.map_parser.Fact f : getInit()) {
            s.append("\t").append(f).append("\n");
        }
        s.append(")\n");
        for (org.agreement_technologies.common.map_parser.Operator b : getBeliefs()) {
            s.append(b).append("\n");
        }
        s.append("(global-goal\n");
        for (org.agreement_technologies.common.map_parser.Fact f : getGoals()) {
            s.append("\t").append(f).append("\n");
        }
        s.append(")\n");
        return s.toString();
    }

    /**
     * Displays a String array as a String.
     *
     * @param v Array of string
     * @return String with the array description
     * @since 1.0
     */
    private String toString(String[] v) {
        if (v.length == 0) {
            return "";
        }
        String res = v[0];
        for (int i = 1; i < v.length; i++) {
            res += " " + v[i];
        }
        return res;
    }

    /**
     * Gets the numeric effects of an operator.
     *
     * @param eff List of effects
     * @return Array with the numeric effects
     * @since 1.0
     */
    private TaskTypes.NumericEffectImp[] getOperatorNumericEffects(ArrayList<OperatorCondition> eff) {
        int numConditions = 0;
        for (OperatorCondition e : eff) {
            if (e.type == OperatorConditionType.CT_INCREASE) {
                numConditions++;
            }
        }
        TaskTypes.NumericEffectImp[] res = new TaskTypes.NumericEffectImp[numConditions];
        if (numConditions == 0) {
            return res;
        }
        numConditions = 0;
        for (OperatorCondition e : eff) {
            if (e.type != OperatorConditionType.CT_INCREASE) {
                continue;
            }
            res[numConditions] = new TaskTypes.NumericEffectImp(NumericEffect.INCREASE);
            res[numConditions].var = getOperatorNumericVariable(e.var);
            res[numConditions].exp = getOperatorNumericEffectsExpression(e.exp);
            numConditions++;
        }
        return res;
    }

    /**
     * Gets the numeric variable in an operator numeric effect.
     *
     * @param var Parsed variable
     * @return Numeric variable
     * @since 1.0
     */
    private TaskTypes.FunctionImp getOperatorNumericVariable(Variable var) {
        TaskTypes.FunctionImp res = new TaskTypes.FunctionImp(var.name, false);
        int index = this.functions.indexOf(new Function(new Variable(var.name), false));
        Function fncEff = this.functions.get(index);
        res.parameters = new TaskTypes.ParameterImp[var.params.size()];
        for (int p = 0; p < var.params.size(); p++) {
            Value param = var.params.get(p);
            res.parameters[p] = new TaskTypes.ParameterImp(param.name);
            res.parameters[p].types = new String[param.types.size()];
            for (int t = 0; t < param.types.size(); t++) {
                res.parameters[p].types[t] = param.types.get(t).name;
            }
        }
        res.domain = new String[fncEff.domain.size()];
        for (int t = 0; t < res.domain.length; t++) {
            res.domain[t] = fncEff.domain.get(t).name;
        }
        return res;
    }

    /**
     * Gets the numeric expression in an operator numeric effect.
     *
     * @param exp Parsed numeric expression
     * @return Numeric expression
     * @since 1.0
     */
    private TaskTypes.NumericExpressionImp getOperatorNumericEffectsExpression(NumericExpressionImp exp) {
        int type = -1;
        switch (exp.type) {
            case NET_NUMBER:
                type = org.agreement_technologies.common.map_parser.NumericExpression.NUMBER;
                break;
            case NET_VAR:
                type = org.agreement_technologies.common.map_parser.NumericExpression.VARIABLE;
                break;
            case NET_ADD:
                type = org.agreement_technologies.common.map_parser.NumericExpression.ADD;
                break;
            case NET_DEL:
                type = org.agreement_technologies.common.map_parser.NumericExpression.DEL;
                break;
            case NET_PROD:
                type = org.agreement_technologies.common.map_parser.NumericExpression.PROD;
                break;
            case NET_DIV:
                type = org.agreement_technologies.common.map_parser.NumericExpression.DIV;
                break;
            case NET_USAGE:
                type = org.agreement_technologies.common.map_parser.NumericExpression.USAGE;
                break;
        }
        TaskTypes.NumericExpressionImp e = new TaskTypes.NumericExpressionImp(type);
        if (exp.type == NumericExpressionType.NET_NUMBER) {
            e.value = exp.value;
        } else if (exp.type == NumericExpressionType.NET_VAR) {
            e.var = getOperatorNumericVariable(exp.var);
        } else {
            e.left = getOperatorNumericEffectsExpression(exp.left);
            e.right = getOperatorNumericEffectsExpression(exp.right);
        }
        return e;
    }

    /**
     * Gets the congestion operators.
     *
     * @return Array of congestion operators
     * @since 1.0
     */
    @Override
    public Congestion[] getCongestion() {
        Congestion[] res = new Congestion[congestions.size()];
        for (int i = 0; i < res.length; i++) {
            res[i] = congestions.get(i);
        }
        return res;
    }

    /**
     * Get the initial-state numeric facts.
     *
     * @return Array of initial-state numeric facts
     * @since 1.0
     */
    @Override
    public NumericFact[] getInitialNumericFacts() {
        ArrayList<NumericFact> res = new ArrayList<>();
        for (Assignment a : init) {
            if (a.isNumeric) {
                res.add(a);
            }
        }
        return res.toArray(new NumericFact[res.size()]);
    }

    /**
     * Adds a new preference.
     *
     * @param name Preference name
     * @param a Preference condition
     * @param syn Syntactic analyzer
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    public void addPreference(String name, Assignment a, SynAnalyzer syn) throws ParseException {
        for (PreferenceImp p : preferences) {
            if (p.name.equalsIgnoreCase(name)) {
                syn.notifyError("Preference '" + name + "' redefined");
            }
        }
        preferences.add(new PreferenceImp(name, a));
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
    public double getSelfInterest() {
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
     * Gets the lst of preferences.
     *
     * @return List of preferences (facts)
     * @since 1.0
     */
    @Override
    public Fact[] getPreferences() {
        TaskTypes.FactImp res[] = new TaskTypes.FactImp[preferences.size()];
        for (int i = 0; i < res.length; i++) {
            res[i] = getFact(preferences.get(i).goal);
        }
        return res;
    }

    /**
     * Gets the name of a given preference by its index.
     * 
     * @param index Preference index
     * @return Preference name
     * @since 1.0
     */
    @Override
    public String getPreferenceName(int index) {
        return preferences.get(index).name;
    }

    /**
     * Gets the metric function.
     * 
     * @return Metric function
     * @since 1.0
     */
    @Override
    public Metric getMetric() {
        return metric;
    }

    /**
     * Type class.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class Type {

        String name;				// Name of the type
        ArrayList<Type> parentTypes;		// Parent types

        /**
         * Constructor.
         *
         * @param name Name of the type
         * @since 1.0
         */
        public Type(String name) {
            this.name = name;
            parentTypes = new ArrayList<>();
        }

        /**
         * Add a parent type to the current type.
         *
         * @param parent Name of the parent type
         * @param syn Syntactic analyzer
         * @throws ParseException if the parent type is repeated
         * @since 1.0
         */
        public void addParentType(Type parent, SynAnalyzer syn) throws ParseException {
            if (parentTypes.contains(parent)) {
                syn.notifyError("Parent type '" + parent.name
                        + "' already defined for type '" + name + "'");
            }
            parentTypes.add(parent);
        }

        /**
         * Compares two types by their names.
         *
         * @param x Another type to compare with
         * @return <code>true</code>, if both types are equal;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            return name.equals(((Type) x).name);
        }

        /**
         * Returns a hash code for this type.
         *
         * @return Hash code
         * @since 1.0
         */
        @Override
        public int hashCode() {
            return name.hashCode();
        }

        /**
         * Checks if this type is compatible with the given type.
         *
         * @param tp Given type
         * @return <code>true</code>, if this type is compatible with the given
         * type; <code>false</code>, otherwise
         * @since 1.0
         */
        public boolean isCompatible(Type tp) {
            boolean comp = equals(tp);
            if (!comp) {
                for (Type t : parentTypes) {
                    if (t.isCompatible(tp)) {
                        comp = true;
                        break;
                    }
                }
            }
            return comp;
        }

        /**
         * Checks if this type is in the given domain.
         *
         * @param domain List of types
         * @return <code>true</code>, if this type belongs to the domain;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        public boolean isCompatible(ArrayList<Type> domain) {
            for (Type t : domain) {
                if (this.isCompatible(t)) {
                    return true;
                }
            }
            return false;
        }

        /**
         * Gets a description of this type.
         *
         * @return Type description
         * @since 1.0
         */
        @Override
        public String toString() {
            return name;
        }
    }

    /**
     * PDDL objects and constants. Also used for variables in parameters.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class Value {

        String name;				// Object name
        ArrayList<Type> types;                  // Object types
        boolean isVariable;			// Variable in a parameter list

        /**
         * Constructor.
         *
         * @param name Name of the object/constant
         * @since 1.0
         */
        public Value(String name) {
            this.name = name;
            types = new ArrayList<>();
            isVariable = false;
        }

        /**
         * Compares two values by their names.
         *
         * @param x Another value to compare with
         * @return <code>true</code>, if both values are equal;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            return name.equals(((Value) x).name);
        }

        /**
         * Gets a hash code for this value.
         *
         * @return Hash code
         * @since 1.0
         */
        @Override
        public int hashCode() {
            return name.hashCode();
        }

        /**
         * Adds a type to this object.
         *
         * @param type	New type
         * @param syn	Syntactic analyzer
         * @throws ParseException If the type is redefined for this object
         * @since 1.0
         */
        public void addType(Type type, SynAnalyzer syn) throws ParseException {
            if (types.contains(type)) {
                syn.notifyError("Type '" + type.name
                        + "' already defined for object '" + name + "'");
            }
            types.add(type);
        }

        /**
         * Checks if this value is compatible with (at least) one of the types
         * of the parameter.
         *
         * @param param Parameter
         * @return <code>true</code>, if this value is compatible;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        public boolean isCompatible(Value param) {
            boolean comp = false;
            for (Type t : types) {
                for (Type tp : param.types) {
                    if (t.isCompatible(tp)) {
                        comp = true;
                        break;
                    }
                }
                if (comp) {
                    break;
                }
            }
            return comp;
        }

        /**
         * Checks if this value is compatible with (at least) one of the types
         * of the domain.
         *
         * @param domain List of types
         * @return <code>true</code>, if this value is compatible;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        public boolean isCompatible(ArrayList<Type> domain) {
            boolean comp = false;
            for (Type t : types) {
                for (Type td : domain) {
                    if (t.isCompatible(td)) {
                        comp = true;
                        break;
                    }
                }
                if (comp) {
                    break;
                }
            }
            return comp;
        }

        /**
         * Gets a description of this value.
         *
         * @return Value description
         * @since 1.0
         */
        @Override
        public String toString() {
            return name;
        }
    }

    /**
     * Task predicates.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class Variable implements CongestionFluent {

        String name;                    // Predicate name
        ArrayList<Value> params;	// Parameters

        /**
         * Constructor.
         *
         * @param name Name of the predicate
         * @since 1.0
         */
        public Variable(String name) {
            this.name = name;
            params = new ArrayList<>();
        }

        /**
         * Compares two variables by their names.
         *
         * @param x Another variable to compare with
         * @return <code>true</code>, if both variables are equal;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            return name.equalsIgnoreCase(((Variable) x).name);
        }

        /**
         * Gets a hash code for this variable.
         *
         * @return Hash code
         * @since 1.0
         */
        @Override
        public int hashCode() {
            return name.hashCode();
        }

        /**
         * Gets a description of this variable.
         *
         * @return Variable description
         * @since 1.0
         */
        @Override
        public String toString() {
            return name;
        }

        /**
         * Gets the fluent name.
         *
         * @return Fluent name
         * @since 1.0
         */
        @Override
        public String getName() {
            return name;
        }

        /**
         * Gets the number of parameters in the fluent.
         *
         * @return Number of parameters
         * @since 1.0
         */
        @Override
        public int getNumParams() {
            return params.size();
        }

        /**
         * Gets the name of a parameter.
         *
         * @param index Parameter index (0 <= index < getNumParams()) 
         * @return Name of the parameter 
         * @since 1.0
         */
        @Override
        public String getParamName(int index) {
            return params.get(index).name;
        }
    }

    /**
     * Task Functions.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class Function {

        Variable var;			// Variable
        ArrayList<Type> domain;		// Co-domain
        boolean multiFunction;		// Multi-function or function

        /**
         * Constructor.
         *
         * @param v Variable
         * @param multifunction Indicates if this is a multi-function
         * @since 1.0
         */
        public Function(Variable v, boolean multifunction) {
            this.var = v;
            this.multiFunction = multifunction;
            domain = new ArrayList<>();
        }

        /**
         * Compares two functions by their variable names.
         *
         * @param x Another function to compare with
         * @return <code>true</code>, if both functions are equal;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            return var.equals(((Function) x).var);
        }

        /**
         * Sets the function co-domain.
         *
         * @param domain Function co-domain
         * @since 1.0
         */
        public void setDomain(ArrayList<Type> domain) {
            for (Type t : domain) {
                this.domain.add(t);
            }
        }

        /**
         * Add a type to the domain.
         *
         * @param syn Syntactic token
         * @param typeName Type name
         * @throws ParseException If the type is not valid
         * @since 1.0
         */
        public void addDomainType(SynAnalyzer syn, String typeName) throws ParseException {
            int typeIndex = types.indexOf(new Type(typeName));
            if (typeIndex == -1) {
                syn.notifyError("Type '" + typeName + "' undefined");
            }
            Type t = types.get(typeIndex);
            if (domain.contains(t)) {
                syn.notifyError("Type '" + typeName + "' duplicated in domain definition");
            }
            domain.add(t);
        }

        /**
         * Checks if this function is numeric.
         *
         * @return <code>true</code>, if this function is numeric;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        boolean isNumeric() {
            Type number = types.get(NUMBER_TYPE);
            for (Type t : domain) {
                if (t.isCompatible(number)) {
                    return true;
                }
            }
            return false;
        }
    }

    /**
     * Numeric expression types.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public enum NumericExpressionType {
        NET_NUMBER, NET_VAR,
        NET_ADD, NET_DEL, NET_PROD, NET_DIV,
        NET_USAGE
    }

    /**
     * Numeric expressions.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class NumericExpressionImp implements NumericExpression {

        NumericExpressionType type;         // Expression type
        double value;                       // Value, if type == NET_NUMBER
        Variable var;                       // Variable, if type == NET_VAR (numeric variable)
        NumericExpressionImp left;          // Left operand
        NumericExpressionImp right;         // Right operand

        /**
         * Creates a numeric expression that is a constant value.
         *
         * @param value Constant numeric value
         * @since 1.0
         */
        NumericExpressionImp(double value) {
            type = NumericExpressionType.NET_NUMBER;
            this.value = value;
        }

        /**
         * Creates a numeric expression that is a numeric variable.
         *
         * @param v Numeric variable
         * @since 1.0
         */
        NumericExpressionImp(Variable v) {
            type = NumericExpressionType.NET_VAR;
            this.var = v;
        }

        /**
         * Creates a numeric expression of a given type.
         *
         * @param type Numeric expression type
         * @since 1.0
         */
        NumericExpressionImp(NumericExpressionType type) {
            this.type = type;
            left = right = null;
        }

        /**
         * Gets the numeric expression type.
         *
         * @return Numeric expression type
         * @since 1.0
         */
        @Override
        public int getType() {
            switch (type) {
                case NET_NUMBER:
                    return NUMBER;
                case NET_VAR:
                    return VARIABLE;
                case NET_ADD:
                    return ADD;
                case NET_DEL:
                    return DEL;
                case NET_PROD:
                    return PROD;
                case NET_DIV:
                    return DIV;
                default:
                    return USAGE;
            }
        }

        /**
         * Gets the numeric constant value (only if type == NUMBER).
         *
         * @return Numeric constant value
         * @since 1.0
         */
        @Override
        public double getValue() {
            return value;
        }

        /**
         * Gets the numeric function (only if type == VARIABLE).
         *
         * @return Numeric function
         * @since 1.0
         */
        @Override
        public org.agreement_technologies.common.map_parser.Function getNumericVariable() {
            return null;
        }

        /**
         * Gets the left operand (only if type == ADD, DEL, PROD, or DIV).
         *
         * @return Left operand of this expression
         * @since 1.0
         */
        @Override
        public NumericExpression getLeftExp() {
            return left;
        }

        /**
         * Gets the right operand (only if type == ADD, DEL, PROD, or DIV).
         *
         * @return Right operand of this expression
         * @since 1.0
         */
        @Override
        public NumericExpression getRightExp() {
            return right;
        }

        /**
         * Gets the congestion fluent (only if type == USAGE).
         *
         * @return Congestion fluent
         * @since 1.0
         */
        @Override
        public CongestionFluent getCongestionFluent() {
            return var;
        }
    }

    /**
     * Operator condition types
     */
    public enum OperatorConditionType {
        CT_NONE, CT_EQUAL, CT_MEMBER,
        CT_ASSIGN, CT_ADD, CT_DEL,
        CT_INCREASE
    }

    /**
     * Conditions (preconditions or effects) for operators.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class OperatorCondition {

        OperatorConditionType type;		// Condition type
        boolean neg;                            // Indicates if this condition is negated
        Variable var;				// Variable
        Value value;				// Value
        NumericExpressionImp exp;               // Only for INCREASE operations

        /**
         * Constructor
         *
         * @param type	Condition type
         * @since 1.0
         */
        public OperatorCondition(OperatorConditionType type) {
            this.type = type;
            this.neg = false;
        }
    }

    /**
     * Operators.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class Operator {

        String name;				// Operator name
        ArrayList<Value> params;		// Parameters
        ArrayList<OperatorCondition> prec;	// Preconditions
        ArrayList<OperatorCondition> eff;	// Effects
        int preference;				// Preference value (-1 if no set)

        /**
         * Constructor.
         *
         * @param name Name of the operator
         * @since 1.0
         */
        public Operator(String name) {
            this.name = name;
            this.params = new ArrayList<>();
            this.prec = new ArrayList<>();
            this.eff = new ArrayList<>();
            this.preference = -1;
        }

        /**
         * Compares two operators by their names.
         *
         * @param x Another operator to compare with
         * @return <code>true</code>, if both operators have the same name;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            return name.equalsIgnoreCase(((Operator) x).name);
        }
    }

    /**
     * A variable or function to be shared with other agents.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class SharedData {

        Variable var;			// Predicate
        Function fnc;			// Function
        ArrayList<Value> agents;	// Agents that can observe the predicate/function

        /**
         * Constructor of a shared predicate.
         *
         * @param var Predicate
         * @since 1.0
         */
        public SharedData(Variable var) {
            this.var = var;
            this.fnc = null;
            agents = new ArrayList<>();
        }

        /**
         * Constructor of a shared function.
         *
         * @param fnc Function
         * @since 1.0
         */
        public SharedData(Function fnc) {
            this.var = null;
            this.fnc = fnc;
            agents = new ArrayList<>();
        }
    }

    /**
     * A variable assignment in the init or goal section.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class Assignment implements NumericFact {

        Variable var;				// Predicate if this is a literal
        Function fnc;				// Function if this is a variable
        ArrayList<Value> params;                // Predicate parameters
        ArrayList<Value> values;                // Values assigned. For literals, a true value is inserted
        boolean neg;				// Indicates if the assignment is negated
        boolean isNumeric;                      // Only for numeric assignments
        double value;

        /**
         * Constructor of a literal.
         *
         * @param var Predicate
         * @param neg Indicates if the literal is negated (not)
         * @since 1.0
         */
        public Assignment(Variable var, boolean neg) {
            this.var = var;
            this.fnc = null;
            params = new ArrayList<>();
            values = new ArrayList<>();
            this.neg = neg;
            isNumeric = false;
        }

        /**
         * Constructor of an assignment.
         *
         * @param fnc Function
         * @param neg Indicates if the assignment is negated (not)
         * @since 1.0
         */
        public Assignment(Function fnc, boolean neg) {
            this.var = null;
            this.fnc = fnc;
            params = new ArrayList<>();
            values = new ArrayList<>();
            this.neg = neg;
            isNumeric = false;
        }

        /**
         * Returns the function name.
         *
         * @return Function name
         * @since 1.0
         */
        @Override
        public String getFunctionName() {
            return fnc.var.getName();
        }

        /**
         * Returns the function parameters.
         *
         * @return Array of function parameter names
         * @since 1.0
         */
        @Override
        public String[] getParameters() {
            String[] res = new String[this.params.size()];
            for (int i = 0; i < res.length; i++) {
                res[i] = this.params.get(i).name;
            }
            return res;
        }

        /**
         * Returns the value assigned to the function.
         *
         * @return Value assigned
         * @since 1.0
         */
        @Override
        public double getValue() {
            return value;
        }
    }

    /**
     * Preferences.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class PreferenceImp {

        String name;        // Preference name
        Assignment goal;    // Condition of the preference

        /**
         * Creates a new preference.
         *
         * @param name Preference name
         * @param a Condition of the preference
         * @since 1.0
         */
        public PreferenceImp(String name, Assignment a) {
            this.name = name;
            this.goal = a;
        }
    }

    /**
     * Problem metric
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class MetricImp implements Metric {

        int metricType;
        double number;			// if metricType = MT_NUMBER
        String preference;		// if metricType = MT_PREFERENCE
        ArrayList<MetricImp> term;	// otherwise

        /**
         * Creates a new metric function.
         *
         * @param id Preference name
         * @param syn Syntactic analyzer
         * @throws ParseException If a parse error is detected
         * @since 1.0
         */
        public MetricImp(String id, SynAnalyzer syn) throws ParseException {
            metricType = MT_PREFERENCE;
            preference = id;
            boolean found = false;
            for (PreferenceImp p : preferences) {
                if (p.name.equalsIgnoreCase(id)) {
                    found = true;
                    break;
                }
            }
            if (!found) {
                syn.notifyError("Unknown preference '" + id + "' in metric");
            }
        }

        /**
         * Creates a new metric function.
         *
         * @param sym Function type
         * @since 1.0
         */
        public MetricImp(Symbol sym) {
            if (sym.equals(Symbol.SS_PLUS)) {
                metricType = MT_ADD;
            } else {
                metricType = MT_MULT;
            }
            term = new ArrayList<>();
        }

        /**
         * Creates a new metric function.
         *
         * @param n Constant numeric value
         * @since 1.0
         */
        public MetricImp(double n) {
            metricType = MT_NUMBER;
            number = n;
        }

        /**
         * Creates a new metric function.
         * 
         * @since 1.0
         */
        public MetricImp() {
            metricType = MT_TOTAL_TIME;
        }

        /**
         * Gets the metric type.
         *
         * @return Metric type
         * @since 1.0
         */
        @Override
        public int getMetricType() {
            return metricType;
        }

        /**
         * Gets the preference name (only if type == MT_PREFERENCE).
         *
         * @return Preference name
         * @since 1.0
         */
        @Override
        public String getPreference() {
            return preference;
        }

        /**
         * Gets the numeric constant (only if type == MT_NUMBER).
         *
         * @return Constant numeric value
         * @since 1.0
         */
        @Override
        public double getNumber() {
            return number;
        }

        /**
         * Gets the number of terms (only if type == MT_ADD or MT_MULT).
         *
         * @return Number of terms
         * @since 1.0
         */
        @Override
        public int getNumTerms() {
            return term.size();
        }

        /**
         * Gets a given term by its index.
         *
         * @param index Term index (0 <= index < getNumTerms()) 
         * @return metric term 
         * @since 1.0
         */
        @Override
        public MetricImp getTerm(int index) {
            return term.get(index);
        }
    }

    /**
     * Types of congestion usage functions.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public enum CongestionUsageType {
        CUT_OR, CUT_AND, CUT_ACTION
    }

    /**
     * Congestion actions.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class CongestionAction {

        Operator op;                // Corresponding operator
        ArrayList<Value> params;    // Parameter values

        /**
         * Creates a new congestion action.
         *
         * @param op Corresponding operator
         * @since 1.0
         */
        CongestionAction(Operator op) {
            this.op = op;
            params = new ArrayList<>(op.params.size());
        }

        /**
         * Adds a new parameter to this action.
         *
         * @param value Parameter value
         * @since 1.0
         */
        void addParameter(Value value) {
            params.add(value);
        }
    }

    /**
     * CongestionUsageImp class deals with the usage section in the congestion
     * actions.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class CongestionUsageImp implements CongestionUsage {

        CongestionUsageType type;              // Usage type
        CongestionAction action;               // if type == CUT_ACTION
        ArrayList<CongestionUsageImp> cond;    // otherwise     

        /**
         * Creates a new usage function.
         *
         * @param type Usage function type
         * @since 1.0
         */
        CongestionUsageImp(CongestionUsageType type) {
            this.type = type;
            cond = new ArrayList<>();
        }

        /**
         * Creates a new usage function.
         *
         * @param action Congestion action
         * @since 1.0
         */
        CongestionUsageImp(CongestionAction action) {
            type = CongestionUsageType.CUT_ACTION;
            this.action = action;
        }

        /**
         * Adds a new condition to the usage section.
         *
         * @param condition Usage condition
         * @since 1.0
         */
        void addCondition(CongestionUsageImp condition) {
            cond.add(condition);
        }

        /**
         * Gets the usage type.
         *
         * @return Usage type
         * @since 1.0
         */
        @Override
        public int getType() {
            switch (type) {
                case CUT_OR:
                    return OR;
                case CUT_AND:
                    return AND;
                default:
                    return ACTION;
            }
        }

        /**
         * Gets the number of terms, if this usage is composed of several terms,
         * i.e. if type == OR or type == AND.
         *
         * @return Number of terms
         * @since 1.0
         */
        @Override
        public int numTerms() {
            return cond.size();
        }

        /**
         * Gets a given term by its index.
         *
         * @param index Term index (0 <= index < numTerms()) 
         * @return The term with that index 
         * @since 1.0
         */
        @Override
        public CongestionUsage getTerm(int index) {
            return cond.get(index);
        }

        /**
         * Gets the action name (only if type == ACTION).
         *
         * @return Action name
         * @since 1.0
         */
        @Override
        public String getActionName() {
            return action.op.name;
        }

        /**
         * Gets the number of parameters of the action.
         *
         * @return Number of parameters of the action
         * @since 1.0
         */
        @Override
        public int numActionParams() {
            return action.params.size();
        }

        /**
         * Gets the name of an action parameter by its index.
         *
         * @param paramNumber Parameter index (0 <= paramNumber < numActionParams()) 
         * @return Name of the action parameter 
         * @since 1.0
         */
        @Override
        public String getParamName(int paramNumber) {
            return action.params.get(paramNumber).name;
        }
    }

    /**
     * Condition types.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public enum ConditionType {
        CT_EQUAL, CT_GREATER, CT_GREATER_EQ,
        CT_LESS, CT_LESS_EQ, CT_DISTINCT
    }

    /**
     * Penalties for congestion operators.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class CongestionPenaltyImp implements CongestionPenalty {

        ConditionType condition;        // Condition type
        double conditionValue;          // Condition value
        Variable incVariable;           // Numeric variable to update
        NumericExpressionImp increment; // Numeric expression to increase the variables

        /**
         * Creates a new penalty.
         *
         * @param conditionType Condition type
         * @since 1.0
         */
        CongestionPenaltyImp(ConditionType conditionType) {
            condition = conditionType;
        }

        /**
         * Sets the numeric variable.
         *
         * @param var Numeric variable
         * @since 1.0
         */
        void setVariable(Variable var) {
            incVariable = var;
        }

        /**
         * Sets the variable increment.
         *
         * @param inc Numeric expression
         * @since 1.0
         */
        void setIncrement(NumericExpressionImp inc) {
            increment = inc;
        }

        /**
         * Gets the condition type.
         *
         * @return Condition type
         * @since 1.0
         */
        @Override
        public int getConditionType() {
            switch (condition) {
                case CT_EQUAL:
                    return EQUAL;
                case CT_GREATER:
                    return GREATER;
                case CT_GREATER_EQ:
                    return GREATER_EQ;
                case CT_LESS:
                    return LESS;
                case CT_LESS_EQ:
                    return LESS_EQ;
                default:
                    return DISTINCT;
            }
        }

        /**
         * Gets the fluent for the condition.
         *
         * @return Condition fluent
         * @since 1.0
         */
        @Override
        public CongestionFluent getIncVariable() {
            return incVariable;
        }

        /**
         * Gets the condition value.
         *
         * @return Condition value
         * @since 1.0
         */
        @Override
        public double getConditionValue() {
            return conditionValue;
        }

        /**
         * Gest the numeric expression for this condition.
         *
         * @return Numeric expression
         * @since 1.0
         */
        @Override
        public NumericExpression getIncExpression() {
            return increment;
        }
    }

    /**
     * Congestion operators.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public class CongestionImp implements Congestion {

        String name;                                // Operator name
        ArrayList<Value> params;                    // Operator parameters
        ArrayList<Value> vars;                      // Local variables
        CongestionUsageImp usage;                   // Usage section
        ArrayList<CongestionPenaltyImp> penalty;    // Penalties

        /**
         * Creates a new congestion operator.
         *
         * @param name Operator name
         * @since 1.0
         */
        CongestionImp(String name) {
            this.name = name;
            params = new ArrayList<>();
            vars = new ArrayList<>();
            usage = null;
            penalty = new ArrayList<>();
        }

        /**
         * Compares two congestion operators by their names.
         *
         * @param x Another congestion operator to compare with.
         * @return <code>true</code>, if both operators have the same name;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            return ((CongestionImp) x).name.equalsIgnoreCase(name);
        }

        /**
         * Adds a new parameter to this congestion operator.
         *
         * @param p Parameter
         * @param syn Syntactic analizer
         * @throws ParseException If a parse error is detected
         * @since 1.0
         */
        void addParameter(Value p, SynAnalyzer syn) throws ParseException {
            if (params.contains(p) || vars.contains(p)) {
                syn.notifyError("Parameter '" + p.name + "' redefined");
            }
            params.add(p);
        }

        /**
         * Adds a new local variable to this congestion operator.
         *
         * @param p Variable
         * @param syn Syntactic analizer
         * @throws ParseException If a parse error is detected
         * @since 1.0
         */
        void addVariable(Value p, SynAnalyzer syn) throws ParseException {
            if (params.contains(p) || vars.contains(p)) {
                syn.notifyError("Variable '" + p.name + "' redefined");
            }
            vars.add(p);
        }

        /**
         * Gets an operator parameter or local variable by its name.
         *
         * @param name Name of the operator or local variable
         * @return Found parameter or variable; <code>null</code>, if its is not
         * found
         * @since 1.0
         */
        Value getParamOrVar(String name) {
            for (Value v : params) {
                if (v.name.equalsIgnoreCase(name)) {
                    return v;
                }
            }
            for (Value v : vars) {
                if (v.name.equalsIgnoreCase(name)) {
                    return v;
                }
            }
            return null;
        }

        /**
         * Adds a penalty to this congestion operator.
         *
         * @param p New penalty
         * @since 1.0
         */
        void addPenalty(CongestionPenaltyImp p) {
            penalty.add(p);
        }

        /**
         * Gets the number of parameters of the congestion operator.
         *
         * @return Number of parameters of the congestion operator
         * @since 1.0
         */
        @Override
        public int getNumParams() {
            return params.size();
        }

        /**
         * Gets the list of types of a given parameter.
         *
         * @param paramNumber Parameter index (0 <= paramNumber < getNumParams()) 
         * @return List of types of the given parameter 
         * @since 1.0
         */
        @Override
        public String[] getParamTypes(int paramNumber) {
            Value v = params.get(paramNumber);
            String[] types = new String[v.types.size()];
            for (int i = 0; i < types.length; i++) {
                types[i] = v.types.get(i).name;
            }
            return types;
        }

        /**
         * Gets the name of the congestion operator.
         *
         * @return Name of the congestion operator
         * @since 1.0
         */
        @Override
        public String getName() {
            return name;
        }

        /**
         * Gets the name of the variables defined in the congestion operator.
         *
         * @return Array with the name of the variables defined in the
         * congestion operator
         * @since 1.0
         */
        @Override
        public String[] getVariableNames() {
            String varNames[] = new String[vars.size()];
            for (int i = 0; i < vars.size(); i++) {
                varNames[i] = vars.get(i).name;
            }
            return varNames;
        }

        /**
         * Gets the list of types of a given parameter.
         *
         * @param varNumber Variable index (0 <= varNumber < getVariableNames().size()) 
         * @return List of type s of the given variable 
         * @since 1.0
         */
        @Override
        public String[] getVarTypes(int varNumber) {
            Value v = vars.get(varNumber);
            String[] types = new String[v.types.size()];
            for (int i = 0; i < types.length; i++) {
                types[i] = v.types.get(i).name;
            }
            return types;
        }

        /**
         * Gets the usage section in the congestion operator.
         *
         * @return Usage section
         * @since 1.0
         */
        @Override
        public CongestionUsage getUsage() {
            return usage;
        }

        /**
         * Gets the index of a parameter from its name.
         *
         * @param paramName Name of the parameter
         * @return Parameter index
         * @since 1.0
         */
        @Override
        public int getParamIndex(String paramName) {
            int index = -1;
            for (int i = 0; i < params.size(); i++) {
                if (params.get(i).name.equalsIgnoreCase(paramName)) {
                    index = i;
                    break;
                }
            }
            return index;
        }

        /**
         * Gets the number of penalties.
         *
         * @return Number of penalties
         * @since 1.0
         */
        @Override
        public int getNumPenalties() {
            return penalty.size();
        }

        /**
         * Gets a penalty of the the congestion operator.
         *
         * @param index Penalty index (0 <= index < getNumPenalties()) 
         * @return Penalty of the the congestion operator 
         * @since 1.0
         */
        @Override
        public CongestionPenalty getPenalty(int index) {
            return penalty.get(index);
        }
    }
}
