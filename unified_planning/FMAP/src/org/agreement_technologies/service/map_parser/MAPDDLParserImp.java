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

import java.io.IOException;
import java.io.Reader;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import org.agreement_technologies.common.map_parser.AgentList;
import org.agreement_technologies.common.map_parser.PDDLParser;
import org.agreement_technologies.common.map_parser.Task;
import org.agreement_technologies.service.map_parser.SynAnalyzer.Symbol;
import org.agreement_technologies.service.map_parser.TaskImp.MetricImp;

/**
 * MAPDDLParserImp class implements a MAPDDL parser.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class MAPDDLParserImp implements PDDLParser {

    private final ArrayList<TaskImp.Variable> privatePredicates;
    private final ArrayList<TaskImp.Value> privateObjects;

    /**
     * Creates a new parser.
     *
     * @since 1.0
     */
    public MAPDDLParserImp() {
        privatePredicates = new ArrayList<>();
        privateObjects = new ArrayList<>();
    }

    /**
     * Parses a PDDL domain file.
     *
     * @param domainFile Domain file name
     * @return Parsed task
     * @throws ParseException If a parse error is detected
     * @throws IOException If the file cannot be read
     * @since 1.0
     */
    @Override
    public Task parseDomain(String domainFile) throws ParseException, IOException {
        String content = readToString(domainFile);
        SynAnalyzer syn = new SynAnalyzer(content);
        TaskImp task = new TaskImp();
        syn.openPar();
        syn.readSym(SynAnalyzer.Symbol.SS_DEFINE);				// Domain name
        syn.openPar();
        syn.readSym(SynAnalyzer.Symbol.SS_DOMAIN);
        task.domainName = syn.readId();
        syn.closePar();
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        while (token.isSym(Symbol.SS_OPEN_PAR)) {	// Domain sections
            syn.colon();
            token = syn.readSym(Symbol.SS_REQUIREMENTS, Symbol.SS_TYPES,
                    Symbol.SS_CONSTANTS, Symbol.SS_PREDICATES,
                    Symbol.SS_FUNCTIONS, Symbol.SS_MULTI_FUNCTIONS,
                    Symbol.SS_ACTION);
            switch (token.getSym()) {
                case SS_REQUIREMENTS:
                    parseRequirements(syn, task);
                    break;
                case SS_TYPES:
                    parseTypes(syn, task);
                    break;
                case SS_CONSTANTS:
                    parseObjects(syn, task, false);
                    break;
                case SS_PREDICATES:
                    parsePredicates(syn, task, false);
                    break;
                case SS_FUNCTIONS:
                    parseFunctions(syn, task, false);
                    break;
                case SS_ACTION:
                    parseAction(syn, task);
                    break;
            }
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        }
        return task;
    }

    /**
     * Reads a file into a String.
     *
     * @param fileName File name
     * @return String with the content of the file
     * @throws IOException If the file cannot be read
     * @since 1.0
     */
    private String readToString(String fileName) throws IOException {
        Reader source = new java.io.FileReader(fileName);
        StringBuilder buf = new StringBuilder();
        try {
            for (int c = source.read(); c != -1; c = source.read()) {
                buf.append((char) c);
            }
            return buf.toString();
        } catch (IOException e) {
            throw e;
        } finally {
            try {
                source.close();
            } catch (Exception e) {
            }
        }
    }

    /**
     * Parses a file with the list of participating agents.
     *
     * @param agentsFile Agents' file name
     * @return List of agents
     * @throws ParseException If a parse error is detected
     * @throws IOException If the file cannot be read
     * @since 1.0
     */
    @Override
    public AgentList parseAgentList(String agentsFile) throws ParseException, IOException {
        String content = readToString(agentsFile);
        SynAnalyzer syn = new SynAnalyzer(content);
        AgentList agList = new AgentListImp();
        SynAnalyzer.Token t;
        do {
            t = syn.readSym(SynAnalyzer.Symbol.SS_ID, SynAnalyzer.Symbol.SS_UNDEFINED);
            if (!t.undefined()) {
                String agName = t.getDesc();
                t = syn.readSym(SynAnalyzer.Symbol.SS_NUMBER);
                String ip = t.getDesc();
                agList.addAgent(agName, ip);
            }
        } while (!t.undefined());
        if (agList.isEmpty()) {
            throw new ParseException("No agents defined in the file", 1);
        }
        return agList;
    }

    /**
     * Parses the requirement section.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parseRequirements(SynAnalyzer syn, TaskImp task) throws ParseException {
        SynAnalyzer.Token token;
        do {
            token = syn.readSym(Symbol.SS_COLON, Symbol.SS_CLOSE_PAR);
            if (token.isSym(Symbol.SS_COLON)) {
                String req = syn.readId().toUpperCase();
                task.addRequirement(req);
            }
        } while (!token.isSym(Symbol.SS_CLOSE_PAR));
    }

    /**
     * Parses the types section.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parseTypes(SynAnalyzer syn, TaskImp task) throws ParseException {
        SynAnalyzer.Token token;
        ArrayList<String> typeNames;
        ArrayList<String> parentTypes;
        token = syn.readSym(Symbol.SS_ID, Symbol.SS_CLOSE_PAR);
        while (!token.isSym(Symbol.SS_CLOSE_PAR)) {    			// Types list
            typeNames = new ArrayList<>();
            while (token.isSym(Symbol.SS_ID)) {
                typeNames.add(token.getDescLower());
                token = syn.readSym(Symbol.SS_ID, Symbol.SS_DASH, Symbol.SS_CLOSE_PAR);
            }
            parentTypes = new ArrayList<>();
            if (token.isSym(Symbol.SS_DASH)) {
                parseTypeList(syn, parentTypes, task);
                token = syn.readSym(Symbol.SS_ID, Symbol.SS_CLOSE_PAR);
            } else {
                parentTypes.add("object");
            }
            addTypes(syn, typeNames, parentTypes, task);
        }
    }

    /**
     * Parses a list of types.
     *
     * @param syn Syntactic analyzer
     * @param parentTypes List of parent types
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parseTypeList(SynAnalyzer syn, ArrayList<String> parentTypes,
            TaskImp task) throws ParseException {
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_ID);
        if (token.isSym(Symbol.SS_ID)) {
            TaskImp.Type type = task.new Type(token.getDescLower());
            parentTypes.add(type.name);
        } else {
            syn.readSym(Symbol.SS_EITHER);
            do {
                token = syn.readSym(Symbol.SS_ID, Symbol.SS_CLOSE_PAR);
                if (token.isSym(Symbol.SS_ID)) {
                    TaskImp.Type type = task.new Type(token.getDescLower());
                    parentTypes.add(type.name);
                }
            } while (!token.isSym(Symbol.SS_CLOSE_PAR));
        }
    }

    /**
     * Adds a new type to the parsed task.
     *
     * @param syn Syntactic analyzer
     * @param typeName Type name to add
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.Type addNewType(SynAnalyzer syn, String typeName, TaskImp task)
            throws ParseException {
        TaskImp.Type type = task.new Type(typeName);
        int pos = task.types.indexOf(type);
        if (pos == -1) {
            task.types.add(type);
        } else {
            if (pos > TaskImp.AGENT_TYPE) {
                syn.notifyError("Type '" + typeName + "' redefined");
            } else {
                type = task.types.get(pos);
            }
        }
        return type;
    }

    /**
     * Adds new types to the parsed task.
     *
     * @param syn Syntactic analyzer
     * @param typeNames Type names to add
     * @param parentTypes Parent types for the new types
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void addTypes(SynAnalyzer syn, ArrayList<String> typeNames, ArrayList<String> parentTypes, TaskImp task) throws ParseException {
        for (String name : typeNames) {
            TaskImp.Type type = addNewType(syn, name, task);
            if (parentTypes.contains(name)) {
                type.addParentType(task.types.get(TaskImp.OBJECT_TYPE), syn);
            } else {
                for (String parent : parentTypes) {
                    int typeIndex = task.types.indexOf(task.new Type(parent));
                    if (typeIndex == -1) {
                        TaskImp.Type ptype = addNewType(syn, parent, task);
                        ptype.addParentType(task.types.get(TaskImp.OBJECT_TYPE), syn);
                        typeIndex = task.types.indexOf(ptype);
                    }
                    type.addParentType(task.types.get(typeIndex), syn);
                }
            }
        }
    }

    /**
     * Parses the predicates section.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parsePredicates(SynAnalyzer syn, TaskImp task, boolean priv) throws ParseException {
        SynAnalyzer.Token token;
        do {
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
            if (token.isSym(Symbol.SS_OPEN_PAR)) {
                syn.restoreLastToken();
                TaskImp.Variable v = parsePredicate(syn, task, false, true, priv);
                if (v != null) {
                    task.predicates.add(v);
                    if (priv) {
                        privatePredicates.add(v);
                    }
                }
            }
        } while (!token.isSym(Symbol.SS_CLOSE_PAR));
    }

    /**
     * Parses a single predicate.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param allowDuplicates Indicates if duplicated predicates are allowed
     * @param readPar Indicates the open parentheses must be read
     * @param priv Indicates if the predicate is private
     * @return Parsed predicate
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.Variable parsePredicate(SynAnalyzer syn, TaskImp task,
            boolean allowDuplicates, boolean readPar, boolean priv) throws ParseException {
        if (readPar) {
            syn.openPar();
        }
        SynAnalyzer.Token token;
        if (priv) {
            token = syn.readSym(Symbol.SS_ID);
        } else {
            token = syn.readSym(Symbol.SS_ID, Symbol.SS_COLON);
        }
        if (token.isSym(Symbol.SS_COLON)) {
            readPrivateToken(syn);
            parsePredicates(syn, task, true);
            return null;
        } else {
            TaskImp.Variable v = task.new Variable(token.getDesc());
            if (!allowDuplicates && task.existVariable(v)) {
                syn.notifyError("Predicate '" + v.name + "' redefined");
            }
            ArrayList<TaskImp.Value> params = parseParameters(syn, task);
            for (TaskImp.Value p : params) {
                v.params.add(p);
            }
            if (readPar) {
                syn.closePar();
            }
            return v;
        }
    }

    /**
     * Parses a list of parameters.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @return List of parameters
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private ArrayList<TaskImp.Value> parseParameters(SynAnalyzer syn, TaskImp task) throws ParseException {
        ArrayList<TaskImp.Value> res = new ArrayList<>();
        SynAnalyzer.Token token;
        ArrayList<String> paramList;
        ArrayList<String> typeList;
        do {
            token = syn.readSym(Symbol.SS_VAR, Symbol.SS_CLOSE_PAR);
            if (!token.isSym(Symbol.SS_CLOSE_PAR)) {
                String desc = token.getDescLower();
                paramList = new ArrayList<>();
                typeList = new ArrayList<>();
                do {
                    paramList.add(desc);
                    token = syn.readSym(Symbol.SS_VAR, Symbol.SS_DASH, Symbol.SS_CLOSE_PAR);
                    desc = token.getDescLower();
                } while (token.isSym(Symbol.SS_VAR));
                if (token.isSym(Symbol.SS_DASH)) {
                    parseTypeList(syn, typeList, task);
                } else {
                    typeList.add("object");
                }
                for (String paramName : paramList) {
                    TaskImp.Value v = task.new Value(paramName);
                    v.isVariable = true;
                    if (res.contains(v)) {
                        syn.notifyError("Parameter '" + paramName + "' redefined");
                    }
                    for (String t : typeList) {
                        v.addType(getType(t, task, syn), syn);
                    }
                    res.add(v);
                }
            }
        } while (!token.isSym(Symbol.SS_CLOSE_PAR));
        syn.restoreLastToken();
        return res;
    }

    /**
     * Searches for a type by its name.
     *
     * @param typeName Type name
     * @param task Parsed task
     * @param syn Syntactic analyzer
     * @return Type with that name
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.Type getType(String typeName, TaskImp task, SynAnalyzer syn) throws ParseException {
        int index = task.types.indexOf(task.new Type(typeName));
        if (index == -1) {
            syn.notifyError("Type '" + typeName + "' undefined");
        }
        return task.types.get(index);
    }

    /**
     * Check that the next token to read is the "private" token.
     *
     * @param syn Syntactic analyzer
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void readPrivateToken(SynAnalyzer syn) throws ParseException {
        String id = syn.readId();
        if (!id.equalsIgnoreCase("private")) {
            syn.notifyError("Keyword 'private' expected");
        }
    }

    /**
     * Parses an action.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parseAction(SynAnalyzer syn, TaskImp task) throws ParseException {
        TaskImp.Operator op = task.new Operator(syn.readId());
        if (task.operators.contains(op)) {
            syn.notifyError("Operator '" + op.name + "' redefined");
        }
        task.operators.add(op);
        syn.colon();
        boolean precRead = false, effRead = false;
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_PARAMS, Symbol.SS_PREC, Symbol.SS_EFF);
        do {
            switch (token.getSym()) {
                case SS_PARAMS:
                    syn.openPar();
                    ArrayList<TaskImp.Value> params = parseParameters(syn, task);
                    for (TaskImp.Value p : params) {
                        op.params.add(p);
                    }
                    syn.closePar();
                    break;
                case SS_PREC:
                    parseOperatorCondition(syn, task, op, true);
                    precRead = true;
                    break;
                case SS_EFF:
                    parseOperatorCondition(syn, task, op, false);
                    effRead = true;
                    break;
            }
            token = syn.readSym(Symbol.SS_OPEN_PAR,
                    Symbol.SS_COLON, Symbol.SS_CLOSE_PAR);
            if (token.isSym(Symbol.SS_COLON)) {
                if (!precRead) {
                    token = syn.readSym(Symbol.SS_PREC, Symbol.SS_EFF);
                } else if (!effRead) {
                    token = syn.readSym(Symbol.SS_EFF);
                } else {
                    syn.notifyError("Unexpected colon");
                }
            }
        } while (!token.isSym(Symbol.SS_CLOSE_PAR) && !token.isSym(Symbol.SS_OPEN_PAR));
        if (token.isSym(Symbol.SS_OPEN_PAR)) {
            syn.restoreLastToken();
        }
    }

    /**
     * Parses the operator preconditions or effects.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param op Operator
     * @param isPrec <code>true</code> indicates to parse a precondition;
     * <code>false</code>, an effect
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parseOperatorCondition(SynAnalyzer syn, TaskImp task,
            TaskImp.Operator op, boolean isPrec) throws ParseException {
        TaskImp.OperatorCondition cond;
        syn.openPar();
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_AND, Symbol.SS_ID,
                Symbol.SS_EQUAL);
        if (token.isSym(Symbol.SS_AND)) {  			// Set of conditions
            do {
                token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
                if (token.isSym(Symbol.SS_OPEN_PAR)) {
                    cond = parseSingleOperatorCondition(syn, task, op, isPrec);
                    syn.closePar();
                    if (isPrec) {
                        op.prec.add(cond);
                    } else {
                        op.eff.add(cond);
                    }
                }
            } while (!token.isSym(Symbol.SS_CLOSE_PAR));
        } else {                                    // Single condition         
            syn.restoreLastToken();
            cond = parseSingleOperatorCondition(syn, task, op, isPrec);
            syn.closePar();
            if (isPrec) {
                op.prec.add(cond);
            } else {
                op.eff.add(cond);
            }
        }
    }

    /**
     * Parses an operator precondition or effect.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param op Operator
     * @param isPrec <code>true</code> indicates to parse a precondition;
     * <code>false</code>, an effect
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.OperatorCondition parseSingleOperatorCondition(SynAnalyzer syn,
            TaskImp task, TaskImp.Operator op, boolean isPrec) throws ParseException {
        TaskImp.OperatorCondition cond;
        SynAnalyzer.Token token;
        if (isPrec) {
            token = syn.readSym(Symbol.SS_NOT, Symbol.SS_EQUAL, Symbol.SS_MEMBER, Symbol.SS_ID);
        } else {
            token = syn.readSym(Symbol.SS_NOT, Symbol.SS_ASSIGN, Symbol.SS_ADD, Symbol.SS_DEL,
                    Symbol.SS_INCREASE, Symbol.SS_ID);
        }
        if (token.isSym(Symbol.SS_NOT)) {			// Negation
            syn.openPar();
            cond = parseSingleOperatorCondition(syn, task, op, isPrec);
            syn.closePar();
            cond.neg = !cond.neg;
        } else if (token.isSym(Symbol.SS_INCREASE)) {
            cond = task.new OperatorCondition(TaskImp.OperatorConditionType.CT_INCREASE);
            syn.openPar();
            cond.var = parseOperatorVariable(syn, task, op);
            syn.closePar();
            TaskImp.Function function = checkFunction(cond.var, syn, task);
            if (!function.isNumeric()) {
                syn.notifyError("Function '" + cond.var.name + "' is not numeric");
            }
            cond.exp = parseNumericExpression(syn, task, op, null);
        } else if (token.isSym(Symbol.SS_ID)) {		// Predicate
            syn.restoreLastToken();
            cond = task.new OperatorCondition(TaskImp.OperatorConditionType.CT_NONE);
            cond.var = parseOperatorVariable(syn, task, op);
            checkPredicate(cond.var, syn, task);
        } else {
            TaskImp.OperatorConditionType type = null;
            switch (token.getSym()) {
                case SS_EQUAL:
                    type = TaskImp.OperatorConditionType.CT_EQUAL;
                    break;
                case SS_MEMBER:
                    type = TaskImp.OperatorConditionType.CT_MEMBER;
                    break;
                case SS_ASSIGN:
                    type = TaskImp.OperatorConditionType.CT_ASSIGN;
                    break;
                case SS_ADD:
                    type = TaskImp.OperatorConditionType.CT_ADD;
                    break;
                case SS_DEL:
                    type = TaskImp.OperatorConditionType.CT_DEL;
                    break;
                default:
                    syn.notifyError("Unknown condition type");
            }
            cond = task.new OperatorCondition(type);
            syn.openPar();
            cond.var = parseOperatorVariable(syn, task, op);
            syn.closePar();
            cond.value = parseOperatorValue(syn, task, op);
            checkFunction(cond, syn, task);
        }
        return cond;
    }

    /**
     * Parses an operator variable.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param op Operator
     * @return Parsed variable
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.Variable parseOperatorVariable(SynAnalyzer syn, TaskImp task,
            TaskImp.Operator op) throws ParseException {
        TaskImp.Variable v = task.new Variable(syn.readId());
        SynAnalyzer.Token token;
        do {
            token = syn.readSym(Symbol.SS_VAR, Symbol.SS_CLOSE_PAR, Symbol.SS_ID);
            if (!token.isSym(Symbol.SS_CLOSE_PAR)) {
                syn.restoreLastToken();
                v.params.add(parseOperatorValue(syn, task, op));
            }
        } while (!token.isSym(Symbol.SS_CLOSE_PAR));
        syn.restoreLastToken();
        return v;
    }

    /**
     * Parses an operator value.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param op Operator
     * @return Parsed value
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.Value parseOperatorValue(SynAnalyzer syn, TaskImp task,
            TaskImp.Operator op) throws ParseException {
        TaskImp.Value v;
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_VAR, Symbol.SS_ID);
        if (token.isSym(Symbol.SS_VAR)) {			// Parameter
            int paramIndex = op.params.indexOf(task.new Value(token.getDescLower()));
            if (paramIndex == -1) {
                syn.notifyError("Parameter '" + token.getDesc()
                        + "' undefined in operator '" + op.name + "'");
            }
            v = op.params.get(paramIndex);
        } else {									// Constant
            int objIndex = task.values.indexOf(task.new Value(token.getDescLower()));
            if (objIndex == -1) {
                syn.notifyError("Constant '" + token.getDesc() + "' undefined");
            }
            v = task.values.get(objIndex);
        }
        return v;
    }

    /**
     * Checks if a predicate is well defined.
     *
     * @param var Parsed predicate
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void checkPredicate(TaskImp.Variable var, SynAnalyzer syn, TaskImp task) throws ParseException {
        int vIndex = task.predicates.indexOf(var);
        if (vIndex == -1) {
            syn.notifyError("Predicate '" + var.name + "' undefined");
        }
        TaskImp.Variable pred = task.predicates.get(vIndex);
        if (var.params.size() != pred.params.size()) {
            syn.notifyError("Wrong number of parameters in predicate '" + var.name + "'");
        }
        for (int i = 0; i < pred.params.size(); i++) {
            TaskImp.Value predParam = pred.params.get(i),
                    varParam = var.params.get(i);
            if (!varParam.isCompatible(predParam)) {
                syn.notifyError("Invalid parameter '"
                        + varParam.name + "' in predicate '" + var.name + "'");
            }
        }
    }

    /**
     * Checks if the function in a predicate is well defined.
     *
     * @param var Parsed predicate
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @return Function of the predicate
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.Function checkFunction(TaskImp.Variable var, SynAnalyzer syn,
            TaskImp task) throws ParseException {
        int fIndex = task.functions.indexOf(task.new Function(var, false));
        if (fIndex == -1) {
            syn.notifyError("Function '" + var.name + "' undefined");
        }
        TaskImp.Function fnc = task.functions.get(fIndex);
        if (var.params.size() != fnc.var.params.size()) {
            syn.notifyError("Wrong number of parameters in function '" + var.name + "'");
        }
        for (int i = 0; i < var.params.size(); i++) {
            TaskImp.Value fncParam = fnc.var.params.get(i),
                    varParam = var.params.get(i);
            if (!varParam.isCompatible(fncParam)) {
                syn.notifyError("Invalid parameter '"
                        + varParam.name + "' in function '" + var.name + "'");
            }
        }
        return fnc;
    }

    /**
     * Checks if a function in a condition is well defined.
     *
     * @param cond Parsed condition
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void checkFunction(TaskImp.OperatorCondition cond, SynAnalyzer syn,
            TaskImp task) throws ParseException {
        int fIndex = task.functions.indexOf(task.new Function(cond.var, false));
        if (fIndex == -1) {
            syn.notifyError("Function '" + cond.var.name + "' undefined");
        }
        TaskImp.Function fnc = task.functions.get(fIndex);
        switch (cond.type) {
            case CT_EQUAL:
                if (fnc.multiFunction) {
                    syn.notifyError("Operator '=' not valid for multi-functions");
                }
                break;
            case CT_MEMBER:
                if (!fnc.multiFunction) {
                    syn.notifyError("Operator 'member' not valid for functions");
                }
                break;
            case CT_ASSIGN:
                if (fnc.multiFunction) {
                    syn.notifyError("Operator 'assign' not valid for multi-functions");
                }
                break;
            case CT_ADD:
                if (!fnc.multiFunction) {
                    syn.notifyError("Operator 'add' not valid for functions");
                }
                break;
            case CT_DEL:
                if (!fnc.multiFunction) {
                    syn.notifyError("Operator 'del' not valid for functions");
                }
                break;
            case CT_NONE:
                syn.notifyError("Operator expected");
        }
        if (cond.var.params.size() != fnc.var.params.size()) {
            syn.notifyError("Wrong number of parameters in function '" + cond.var.name + "'");
        }
        for (int i = 0; i < cond.var.params.size(); i++) {
            TaskImp.Value fncParam = fnc.var.params.get(i),
                    varParam = cond.var.params.get(i);
            if (!varParam.isCompatible(fncParam)) {
                syn.notifyError("Invalid parameter '"
                        + varParam.name + "' in function '" + cond.var.name + "'");
            }
        }
        if (!cond.value.isCompatible(fnc.domain)) {
            syn.notifyError("Wrong value '"
                    + cond.value.name + "' for function '" + cond.var.name + "'");
        }
    }

    /**
     * Parses a PDDL problem file. Domain should have been parsed before.
     *
     * @param problemFile Problem file name
     * @param planningTask Parsed task
     * @param agList List of participating agents
     * @param agentName Name of this planning agent
     * @throws ParseException If a parse error is detected
     * @throws IOException If the file cannot be read
     * @since 1.0
     */
    @Override
    public void parseProblem(String problemFile, Task planningTask, AgentList agList, String agentName) throws ParseException, IOException {
        String content = readToString(problemFile);
        SynAnalyzer syn = new SynAnalyzer(content);
        TaskImp taskImp = (TaskImp) planningTask;
        syn.openPar();
        syn.readSym(Symbol.SS_DEFINE);				// Problem name
        syn.openPar();
        syn.readSym(Symbol.SS_PROBLEM);
        taskImp.problemName = syn.readId();
        syn.closePar();
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        while (token.isSym(Symbol.SS_OPEN_PAR)) {	// Problem sections
            syn.colon();
            token = syn.readSym(Symbol.SS_DOMAIN, Symbol.SS_OBJECTS,
                    Symbol.SS_INIT, Symbol.SS_GOAL, Symbol.SS_METRIC);
            switch (token.getSym()) {
                case SS_DOMAIN:
                    syn.readId();
                    syn.closePar();
                    break;
                case SS_OBJECTS:
                    parseObjects(syn, taskImp, false);
                    break;
                case SS_INIT:
                    parseInit(syn, taskImp);
                    break;
                case SS_GOAL:
                    parseGoal(syn, taskImp);
                    break;
                case SS_METRIC:
                    parseMetric(syn, taskImp);
                    break;
            }
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        }
        processSharedData(syn, taskImp, agList, agentName);
    }

    /**
     * Parses the objects in the problem.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param priv Indicates id the objects are private
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parseObjects(SynAnalyzer syn, TaskImp task, boolean priv) throws ParseException {
        SynAnalyzer.Token token;
        ArrayList<String> objNames;
        ArrayList<String> parentTypes;
        token = priv ? syn.readSym(Symbol.SS_ID, Symbol.SS_CLOSE_PAR)
                : syn.readSym(Symbol.SS_ID, Symbol.SS_CLOSE_PAR, Symbol.SS_OPEN_PAR);
        while (!token.isSym(Symbol.SS_CLOSE_PAR)) {
            if (token.isSym(Symbol.SS_OPEN_PAR)) {
                syn.colon();
                readPrivateToken(syn);
                parseObjects(syn, task, true);
            } else {
                objNames = new ArrayList<>();
                parentTypes = new ArrayList<>();
                while (token.isSym(Symbol.SS_ID)) {
                    objNames.add(token.getDescLower());
                    token = syn.readSym(Symbol.SS_ID, Symbol.SS_CLOSE_PAR, Symbol.SS_DASH);
                }
                if (token.isSym(Symbol.SS_DASH)) {
                    parseTypeList(syn, parentTypes, task);
                } else {
                    parentTypes.add("object");
                }
                for (String objName : objNames) {
                    TaskImp.Value obj = addNewObject(syn, objName, task, priv);
                    for (String parent : parentTypes) {
                        TaskImp.Type type = getType(parent, task, syn);
                        obj.addType(type, syn);
                    }
                }
            }
            token = priv ? syn.readSym(Symbol.SS_ID, Symbol.SS_CLOSE_PAR)
                    : syn.readSym(Symbol.SS_ID, Symbol.SS_CLOSE_PAR, Symbol.SS_OPEN_PAR);
        }
    }

    /**
     * Adds a new object to the task.
     *
     * @param syn Syntactic analyzer
     * @param objName Object name
     * @param task Parsed task
     * @param priv Indicates if the objects are private
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.Value addNewObject(SynAnalyzer syn, String objName, TaskImp task, boolean priv)
            throws ParseException {
        TaskImp.Value v = task.new Value(objName);
        if (task.values.contains(v)) {
            syn.notifyError("Object '" + objName + "' redefined");
        }
        task.values.add(v);
        if (priv) {
            privateObjects.add(v);
        }
        return v;
    }

    /**
     * Parses the initial state.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parseInit(SynAnalyzer syn, TaskImp task) throws ParseException {
        SynAnalyzer.Token token;
        do {
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
            if (token.isSym(Symbol.SS_OPEN_PAR)) {
                syn.restoreLastToken();
                TaskImp.Assignment a = parseAssignment(syn, task, true);
                task.init.add(a);
            }
        } while (!token.isSym(Symbol.SS_CLOSE_PAR));
    }

    /**
     * Parses an assigment.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param readPar Indicates if the enclosing parentheses must be read
     * @return Parsed assignment
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.Assignment parseAssignment(SynAnalyzer syn, TaskImp task, boolean readPar)
            throws ParseException {
        TaskImp.Assignment a;
        if (readPar) {
            syn.openPar();
        }
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_EQUAL, Symbol.SS_NOT,
                Symbol.SS_PREFERENCE, Symbol.SS_ID);
        if (token.isSym(Symbol.SS_PREFERENCE)) {
            String name = syn.readId();
            a = parseAssignment(syn, task, true);
            task.addPreference(name, a, syn);
            syn.closePar();
            return null;
        }
        boolean isLiteral = !token.isSym(Symbol.SS_EQUAL);
        boolean neg = token.isSym(Symbol.SS_NOT);
        if (!neg) {
            if (isLiteral) {
                syn.restoreLastToken();
            } else {
                syn.openPar();
            }
        } else {
            syn.openPar();
            token = syn.readSym(Symbol.SS_EQUAL, Symbol.SS_ID);
            isLiteral = !token.isSym(Symbol.SS_EQUAL);
            if (isLiteral) {
                syn.restoreLastToken();
            } else {
                syn.openPar();
            }
        }
        String varName = syn.readId();
        if (isLiteral) {	// Variable
            int index = task.predicates.indexOf(task.new Variable(varName));
            if (index == -1) {
                syn.notifyError("Predicate '" + varName + "' undefined");
            }
            a = task.new Assignment(task.predicates.get(index), neg);
        } else {
            int index = task.functions.indexOf(task.new Function(task.new Variable(varName), false));
            if (index == -1) {
                syn.notifyError("Function '" + varName + "' undefined");
            }
            a = task.new Assignment(task.functions.get(index), neg);
        }
        do {				// Parameters
            token = syn.readSym(Symbol.SS_CLOSE_PAR, Symbol.SS_ID);
            if (token.isSym(Symbol.SS_ID)) {
                syn.restoreLastToken();
                TaskImp.Value param = parseAssignmentValue(syn, task);
                a.params.add(param);
            }
        } while (!token.isSym(Symbol.SS_CLOSE_PAR));
        if (isLiteral) {	// Values
            a.values.add(task.values.get(TaskImp.TRUE_VALUE));
        } else {
            if (a.fnc.multiFunction) {
                syn.readSym(Symbol.SS_OPEN_SET);
                do {
                    token = syn.readSym(Symbol.SS_CLOSE_SET, Symbol.SS_ID);
                    if (token.isSym(Symbol.SS_ID)) {
                        syn.restoreLastToken();
                        a.values.add(parseAssignmentValue(syn, task));
                    }
                } while (!token.isSym(Symbol.SS_CLOSE_SET));
            } else {
                token = syn.readSym(Symbol.SS_NUMBER, Symbol.SS_ID);
                if (token.isSym(Symbol.SS_NUMBER)) {
                    a.isNumeric = true;
                    try {
                        a.value = Double.parseDouble(token.getDesc());
                    } catch (NumberFormatException e) {
                        syn.notifyError("'" + token.getDesc() + "' is not a valid number");
                    }
                } else {
                    syn.restoreLastToken();
                    a.values.add(parseAssignmentValue(syn, task));
                }
            }
            syn.closePar();
        }
        if (neg) {
            syn.closePar();
        }
        checkAssignment(syn, task, a);
        if (!readPar) {
            syn.restoreLastToken();
        }
        return a;
    }

    /**
     * Parses the value of an assigment.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @return Parsed value
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.Value parseAssignmentValue(SynAnalyzer syn, TaskImp task) throws ParseException {
        String valueName = syn.readId().toLowerCase();
        int valueIndex = task.values.indexOf(task.new Value(valueName));
        if (valueIndex == -1) {
            syn.notifyError("Object '" + valueName + "' undefined");
        }
        return task.values.get(valueIndex);
    }

    /**
     * Checks if an assigment is well defined.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param a Parsed assignment
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void checkAssignment(SynAnalyzer syn, TaskImp task, TaskImp.Assignment a) throws ParseException {
        boolean isLiteral = a.var != null;
        TaskImp.Variable var = isLiteral ? a.var : a.fnc.var;
        if (var.params.size() != a.params.size()) {
            syn.notifyError("Wrong number of parameters for literal '" + var.name + "'");
        }
        for (int i = 0; i < a.params.size(); i++) {
            TaskImp.Value predParam = var.params.get(i),
                    varParam = a.params.get(i);
            if (!varParam.isCompatible(predParam)) {
                syn.notifyError("Invalid parameter '"
                        + varParam.name + "' for literal '" + var.name + "'");
            }
        }
        if (!isLiteral) {
            for (TaskImp.Value v : a.values) {
                if (!v.isCompatible(a.fnc.domain)) {
                    syn.notifyError("Wrong value '" + v.name + "' for function '" + var.name + "'");
                }
            }
        }
    }

    /**
     * Parses the task goal.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parseGoal(SynAnalyzer syn, TaskImp task) throws ParseException {
        TaskImp.Assignment a;
        syn.openPar();
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_AND, Symbol.SS_EQUAL,
                Symbol.SS_ID, Symbol.SS_PREFERENCE);
        if (token.isSym(Symbol.SS_AND)) {
            do {
                token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
                if (token.isSym(Symbol.SS_OPEN_PAR)) {
                    syn.restoreLastToken();
                    a = parseAssignment(syn, task, true);
                    if (a != null) {
                        task.gGoals.add(a);
                    }
                }
            } while (!token.isSym(Symbol.SS_CLOSE_PAR));
            syn.closePar();
        } else if (token.isSym(Symbol.SS_PREFERENCE)) {
            String name = syn.readId();
            a = parseAssignment(syn, task, true);
            task.addPreference(name, a, syn);
            syn.closePar();
        } else {
            syn.restoreLastToken();
            a = parseAssignment(syn, task, false);
            task.gGoals.add(a);
        }
    }

    /**
     * Processes the shared data (translation from MAPDDL to native FMAP-PDDL).
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param agList List of agents
     * @param agentName Name of this agent
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void processSharedData(SynAnalyzer syn, TaskImp task, AgentList agList, String agentName) throws ParseException {
        Map<TaskImp.Type, ArrayList<TaskImp.Type>> subtypesMap = generateRequiredSubtypes(syn, task);
        Map<String, TaskImp.Value> agents = generateAgentValues(agList, task, syn);
        changeObjectTypes(subtypesMap, task);
        for (TaskImp.Variable pred : task.predicates) {
            if (!privatePredicates.contains(pred)) { // Public predicate
                generateSharedData(pred, subtypesMap, task, agents, agentName);
            }
        }
    }

    /**
     * Checks if a given value is used in a public predicate.
     *
     * @param obj Parsed value
     * @param task Parsed task
     * @return <code>true</code>, if the value is used in a public predicate;
     * <code>false</code>, otherwise
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private boolean usedInPublicPredicate(TaskImp.Value obj, TaskImp task) {
        boolean used = false;
        for (TaskImp.Variable pred : task.predicates) {
            if (!privatePredicates.contains(pred)) {
                for (TaskImp.Value param : pred.params) {
                    if (obj.isCompatible(param)) {
                        used = true;
                        break;
                    }
                }
                if (used) {
                    break;
                }
            }
        }
        return used;
    }

    /**
     * Generates fictituous sub-types to keep the same level of privacy (due to
     * the translation from MAPDDL to native FMAP-PDDL).
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @return Map of each type with its generated sub-types
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private Map<TaskImp.Type, ArrayList<TaskImp.Type>> generateRequiredSubtypes(SynAnalyzer syn, TaskImp task) throws ParseException {
        Map<TaskImp.Type, ArrayList<TaskImp.Type>> subtypesMap = new HashMap<>();
        for (TaskImp.Value obj : privateObjects) {
            if (usedInPublicPredicate(obj, task)) {
                if (obj.types.size() != 1) {
                    throw new UnsupportedOperationException("Private objects with multiple types not supported");
                }
                TaskImp.Type type = obj.types.get(0);
                if (!subtypesMap.containsKey(type)) {
                    TaskImp.Type pubSubtype = addNewType(syn, "pub-" + type.name, task);
                    pubSubtype.addParentType(type, syn);
                    TaskImp.Type privSubtype = addNewType(syn, "priv-" + type.name, task);
                    privSubtype.addParentType(type, syn);
                    ArrayList<TaskImp.Type> subtypes = new ArrayList<>(2);
                    subtypes.add(pubSubtype);
                    subtypes.add(privSubtype);
                    subtypesMap.put(type, subtypes);
                }
            }
        }
        return subtypesMap;
    }

    /**
     * Changes the types of the objects to keep the same level of privacy
     * (translation from MAPDDL to native FMAP-PDDL).
     *
     * @param subtypesMap Map of each type with its generated sub-types
     * @param task Parsed task
     * @since 1.0
     */
    private void changeObjectTypes(Map<TaskImp.Type, ArrayList<TaskImp.Type>> subtypesMap, TaskImp task) {
        ArrayList<TaskImp.Type> subtypes;
        for (TaskImp.Value obj : task.values) {
            boolean priv = privateObjects.contains(obj);
            for (int i = 0; i < obj.types.size(); i++) {
                TaskImp.Type type = obj.types.get(i);
                subtypes = subtypesMap.get(type);
                if (subtypes != null) {
                    TaskImp.Type newType = subtypes.get(priv ? 1 : 0);
                    obj.types.set(i, newType);
                    // System.out.println(obj + " -> " + newType);
                }
            }
        }
    }

    /**
     * Generates the shared-data, keeping the same level of privacy (due to the
     * translation from MAPDDL to native FMAP-PDDL).
     *
     * @param pred Parsed predicate
     * @param subtypesMap Map of each type with its generated sub-types
     * @param task Parsed task
     * @param agList Map of agent names to problem objects
     * @param agentName This agent name
     * @since 1.0
     */
    private void generateSharedData(TaskImp.Variable pred, Map<TaskImp.Type, ArrayList<TaskImp.Type>> subtypesMap,
            TaskImp task, Map<String, TaskImp.Value> agList, String agentName) {
        TaskImp.Variable sharedPred = task.new Variable(pred.name);
        for (TaskImp.Value param : pred.params) {
            ArrayList<TaskImp.Type> paramTypes = getBasicTypes(param, subtypesMap, task);
            TaskImp.Value newParam = task.new Value(param.name);
            newParam.isVariable = param.isVariable;
            for (TaskImp.Type type : paramTypes) {
                ArrayList<TaskImp.Type> subtypes = subtypesMap.get(type);
                if (subtypes == null) {
                    newParam.types.add(type);
                } else {
                    newParam.types.add(subtypes.get(0));
                }
            }
            sharedPred.params.add(newParam);
        }
        TaskImp.SharedData sd = task.new SharedData(sharedPred);
        for (String agName : agList.keySet()) {
            if (!agentName.equalsIgnoreCase(agName)) {
                TaskImp.Value agent = agList.get(agName);
                sd.agents.add(agent);
            }
        }
        task.sharedData.add(sd);
    }

    /**
     * Gest the list of basic types of a parameter.
     *
     * @param param Parameter
     * @param subtypesMap Map of each type with its generated sub-types
     * @param task Parsed task
     * @return List of types
     * @since 1.0
     */
    private ArrayList<TaskImp.Type> getBasicTypes(TaskImp.Value param, Map<TaskImp.Type, ArrayList<TaskImp.Type>> subtypesMap, TaskImp task) {
        ArrayList<TaskImp.Type> paramTypes = new ArrayList<>();
        for (TaskImp.Type type : param.types) {
            addBasicTypes(type, paramTypes, subtypesMap, task);
        }
        return paramTypes;
    }

    /**
     * Adds subtypes to a given type.
     *
     * @param type Type
     * @param paramTypes List of types of a parameter
     * @param subtypesMap Map of each type with its generated sub-types
     * @param task Parsed task
     * @since 1.0
     */
    private void addBasicTypes(TaskImp.Type type, ArrayList<TaskImp.Type> paramTypes, Map<TaskImp.Type, ArrayList<TaskImp.Type>> subtypesMap, TaskImp task) {
        if (!hasSubtypes(type, task)) {
            paramTypes.add(type);
        } else {
            ArrayList<TaskImp.Type> subtypes = subtypesMap.get(type);
            if (subtypes != null || areObjectsOfThisType(type, task)) {
                paramTypes.add(type);
            }
            for (TaskImp.Type t : task.types) {
                if (t.parentTypes.contains(type)) {
                    if (subtypes == null
                            || (!t.equals(subtypes.get(0)) && !t.equals(subtypes.get(1)))) {
                        addBasicTypes(t, paramTypes, subtypesMap, task);
                    }
                }
            }
        }
    }

    /**
     * Checks if a given type has subtypes.
     *
     * @param type Type
     * @param task Parsed task
     * @return <code>true</code>, if the given type has subtypes;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    private boolean hasSubtypes(TaskImp.Type type, TaskImp task) {
        for (TaskImp.Type t : task.types) {
            if (t.parentTypes.contains(type)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Checks if there are objects of a given type.
     *
     * @param type Type
     * @param task Parsed task
     * @return <code>true</code>, if the are objects of the given type;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    private boolean areObjectsOfThisType(TaskImp.Type type, TaskImp task) {
        for (TaskImp.Value obj : task.values) {
            if (obj.types.contains(type)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Generates objects for each planning agent.
     *
     * @param agList List of agents
     * @param task Parsed task
     * @param syn Syntactic analyzer
     * @return Map from agent names to task objects
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private Map<String, TaskImp.Value> generateAgentValues(AgentList agList, TaskImp task, SynAnalyzer syn) throws ParseException {
        Map<String, TaskImp.Value> agents = new HashMap<>(agList.numAgents());
        TaskImp.Type agType = getType("agent", task, syn);
        ArrayList<TaskImp.Type> agTypeList = new ArrayList<>(1);
        agTypeList.add(agType);
        for (int i = 0; i < agList.numAgents(); i++) {
            String name = agList.getName(i);
            TaskImp.Value value = task.new Value(name);
            int objIndex = task.values.indexOf(value);
            if (objIndex < 0) {
                value.types.add(agType);
                task.values.add(value);
            } else {
                value = task.values.get(objIndex);
                if (!value.isCompatible(agTypeList)) {
                    value.types.add(agType);
                }
            }
            agents.put(name, value);
        }
        return agents;
    }

    /**
     * Parses the functions section.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param multi Indicates if they are multi-functions
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parseFunctions(SynAnalyzer syn, TaskImp task, boolean multi) throws ParseException {
        SynAnalyzer.Token token;
        ArrayList<TaskImp.Variable> functionList;
        ArrayList<TaskImp.Type> domain;
        do {
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
            if (token.isSym(Symbol.SS_OPEN_PAR)) {
                functionList = new ArrayList<>();
                domain = new ArrayList<>();
                do {
                    syn.restoreLastToken();
                    functionList.add(parsePredicate(syn, task, false, true, false));
                    token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_DASH);
                } while (token.isSym(Symbol.SS_OPEN_PAR));
                ArrayList<String> typeNames = new ArrayList<>();
                parseTypeList(syn, typeNames, task);
                domain.clear();
                for (String type : typeNames) {
                    TaskImp.Type t = getType(type, task, syn);
                    domain.add(t);
                }
                for (TaskImp.Variable v : functionList) {
                    if (task.existVariable(v)) {
                        syn.notifyError("Function '" + v.name + "' redefined");
                    }
                    TaskImp.Function f = task.new Function(v, multi);
                    f.setDomain(domain);
                    task.functions.add(f);
                }
            }
        } while (!token.isSym(Symbol.SS_CLOSE_PAR));
    }

    /**
     * Parses a numeric expression.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param op Operator in which the expression is defined (can be null)
     * @param congestion Congestion operator in which the expression is defined
     * (can be null)
     * @return Parsed numeric expression
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.NumericExpressionImp parseNumericExpression(SynAnalyzer syn, TaskImp task,
            TaskImp.Operator op, TaskImp.CongestionImp congestion) throws ParseException {
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_NUMBER);
        TaskImp.NumericExpressionImp exp = null;
        if (token.isSym(Symbol.SS_NUMBER)) {
            try {
                double value = Double.parseDouble(token.getDesc());
                exp = task.new NumericExpressionImp(value);
            } catch (NumberFormatException e) {
                syn.notifyError("Invalid number: " + token.getDesc());
            }
        } else {
            token = syn.readSym(Symbol.SS_PLUS, Symbol.SS_DASH, Symbol.SS_MULT,
                    Symbol.SS_DIV, Symbol.SS_NUMBER, Symbol.SS_ID);
            if (token.isSym(Symbol.SS_NUMBER)) {
                syn.restoreLastToken();
                exp = parseNumericExpression(syn, task, op, congestion);
            } else if (token.isSym(Symbol.SS_ID)) {
                if (token.getDesc().equalsIgnoreCase("usage")) {
                    exp = task.new NumericExpressionImp(TaskImp.NumericExpressionType.NET_USAGE);
                } else {
                    syn.restoreLastToken();
                    TaskImp.Variable v = parseOperatorVariable(syn, task, op);
                    TaskImp.Function function = checkFunction(v, syn, task);
                    if (!function.isNumeric()) {
                        syn.notifyError("Function '" + v.name + "' is not numeric");
                    }
                    exp = task.new NumericExpressionImp(v);
                }
            } else {
                switch (token.getSym()) {
                    case SS_PLUS:
                        exp = task.new NumericExpressionImp(TaskImp.NumericExpressionType.NET_ADD);
                        break;
                    case SS_DASH:
                        exp = task.new NumericExpressionImp(TaskImp.NumericExpressionType.NET_DEL);
                        break;
                    case SS_MULT:
                        exp = task.new NumericExpressionImp(TaskImp.NumericExpressionType.NET_PROD);
                        break;
                    case SS_DIV:
                        exp = task.new NumericExpressionImp(TaskImp.NumericExpressionType.NET_DIV);
                        break;
                }
                exp.left = parseNumericExpression(syn, task, op, congestion);
                exp.right = parseNumericExpression(syn, task, op, congestion);
            }
            syn.closePar();
        }
        return exp;
    }

    /**
     * Parses the metric function.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parseMetric(SynAnalyzer syn, TaskImp task) throws ParseException {
        syn.readSym(Symbol.SS_MINIMIZE);
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR, Symbol.SS_TOTAL_TIME);
        if (token.isSym(Symbol.SS_TOTAL_TIME)) {
            syn.restoreLastToken();
            task.metric = parseMetricTerm(syn, task);
        } else {
            while (token.isSym(Symbol.SS_OPEN_PAR)) {
                task.metric = parseMetricTerm(syn, task);
                token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
            }
        }
    }

    /**
     * Parses a term of the metric function.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @return Parsed metric term
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private MetricImp parseMetricTerm(SynAnalyzer syn, TaskImp task) throws ParseException {
        MetricImp m = null;
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_IS_VIOLATED, Symbol.SS_PLUS,
                Symbol.SS_MULT, Symbol.SS_TOTAL_TIME, Symbol.SS_ID);
        if (token.isSym(Symbol.SS_IS_VIOLATED)) {
            m = task.new MetricImp(syn.readId(), syn);
            syn.closePar();
        } else if (token.isSym(Symbol.SS_TOTAL_TIME)) {
            m = task.new MetricImp();
            syn.closePar();
        } else if (!token.isSym(Symbol.SS_ID)) {
            m = task.new MetricImp(token.getSym());
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR, Symbol.SS_NUMBER);
            while (!token.isSym(Symbol.SS_CLOSE_PAR)) {
                if (token.isSym(Symbol.SS_OPEN_PAR)) {
                    m.term.add(parseMetricTerm(syn, task));
                } else {
                    try {
                        m.term.add(task.new MetricImp(Double.parseDouble(token.getDesc())));
                    } catch (NumberFormatException e) {
                        syn.notifyError("Invalid number format in metric: " + token.getDesc());
                    }
                }
                token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR, Symbol.SS_NUMBER);
            }
        } else {
            m = task.new MetricImp();
            syn.closePar();
        }
        return m;
    }

    /**
     * Checks if the format of the input files is MAPDDL.
     *
     * @param domainFile Domain file name
     * @return <code>true</code>, if the input file is in MAPDDL format;
     * <code>false</code>, if it is the native FMAP-PDDL format.
     * @throws IOException If the file cannot be read
     * @since 1.0
     */
    @Override
    public boolean isMAPDDL(String domainFile) throws IOException {
        String content = readToString(domainFile).toLowerCase();
        return content.contains(":factored");
    }

    /**
     * Returns an empty agents list.
     * 
     * @return Empty agents list
     * @since 1.0
     */
    @Override
    public AgentList createEmptyAgentList() {
        return new AgentListImp();
    }
}
