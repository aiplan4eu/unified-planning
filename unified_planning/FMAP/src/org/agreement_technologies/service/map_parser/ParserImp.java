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

import java.io.File;
import java.io.IOException;
import java.io.Reader;
import java.net.URL;
import java.text.ParseException;
import java.util.ArrayList;
import org.agreement_technologies.common.map_parser.AgentList;
import org.agreement_technologies.common.map_parser.PDDLParser;
import org.agreement_technologies.common.map_parser.Task;
import org.agreement_technologies.service.map_parser.SynAnalyzer.Symbol;
import org.agreement_technologies.service.map_parser.TaskImp.MetricImp;

/**
 * ParserImp class implements a native FMAP-PDDL parser.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class ParserImp implements PDDLParser {

    /**
     * Parses a planning domain from a generic reader.
     *
     * @param source Reader containing the MAP domain description
     * @return Parsed planning task
     * @throws ParseException if there are syntactic errors
     * @throws IOException if the source cannot be read
     * @since 1.0
     */
    public Task parseDomain(Reader source) throws ParseException, IOException {
        String content = readToString(source);
        SynAnalyzer syn = new SynAnalyzer(content);
        TaskImp task = new TaskImp();
        syn.openPar();
        syn.readSym(Symbol.SS_DEFINE);				// Domain name
        syn.openPar();
        syn.readSym(Symbol.SS_DOMAIN);
        task.domainName = syn.readId();
        syn.closePar();
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        while (token.isSym(Symbol.SS_OPEN_PAR)) {	// Domain sections
            syn.colon();
            token = syn.readSym(Symbol.SS_REQUIREMENTS, Symbol.SS_TYPES,
                    Symbol.SS_CONSTANTS, Symbol.SS_PREDICATES,
                    Symbol.SS_FUNCTIONS, Symbol.SS_MULTI_FUNCTIONS,
                    Symbol.SS_ACTION, Symbol.SS_CONGESTION);
            switch (token.getSym()) {
                case SS_REQUIREMENTS:
                    parseRequirements(syn, task);
                    break;
                case SS_TYPES:
                    parseTypes(syn, task);
                    break;
                case SS_CONSTANTS:
                    parseObjects(syn, task);
                    break;
                case SS_PREDICATES:
                    parsePredicates(syn, task);
                    break;
                case SS_FUNCTIONS:
                    parseFunctions(syn, task, false);
                    break;
                case SS_MULTI_FUNCTIONS:
                    parseFunctions(syn, task, true);
                    break;
                case SS_ACTION:
                    parseAction(syn, task);
                    break;
                case SS_CONGESTION:
                    parseCongestion(syn, task);
                    break;
            }
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        }
        return task;
    }

    /**
     * Parses a planning domain from a file.
     *
     * @param source File containing the MAP domain description
     * @return Parsed planning task
     * @throws ParseException if there are syntactic errors
     * @throws IOException if the source cannot be read
     * @since 1.0
     */
    public Task parseDomain(File source) throws ParseException, IOException {
        return parseDomain(new java.io.FileReader(source));
    }

    /**
     * Parses a planning domain from an URL address.
     *
     * @param source URL Address
     * @return Parsed planning task
     * @throws ParseException if there are syntactic errors
     * @throws IOException if the source cannot be read
     * @since 1.0
     */
    public Task parseDomain(URL source) throws ParseException, IOException {
        return parseDomain(new java.io.InputStreamReader(source.openStream()));
    }

    /**
     * Parses a planning problem from a generic reader.
     *
     * @param source Reader containing the MAP problem description
     * @param task Parsed planning task
     * @throws ParseException if there are syntactic errors
     * @throws IOException if the source cannot be read
     * @since 1.0
     */
    public void parseProblem(Reader source, Task task) throws ParseException,
            IOException {
        String content = readToString(source);
        SynAnalyzer syn = new SynAnalyzer(content);
        TaskImp taskImp = (TaskImp) task;
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
                    Symbol.SS_SHARED_DATA, Symbol.SS_INIT, Symbol.SS_BELIEFS,
                    Symbol.SS_GLOBAL_GOAL, Symbol.SS_GOAL, Symbol.SS_ACTION_PREF,
                    Symbol.SS_CONSTRAINTS, Symbol.SS_METRIC, Symbol.SS_BEHAVIOUR);
            switch (token.getSym()) {
                case SS_DOMAIN:
                    String domainName = syn.readId();
                    if (!taskImp.domainName.equalsIgnoreCase(domainName)) {
                        syn.notifyError("Wrong domain name");
                    }
                    syn.closePar();
                    break;
                case SS_OBJECTS:
                    parseObjects(syn, taskImp);
                    break;
                case SS_SHARED_DATA:
                    parseSharedData(syn, taskImp);
                    break;
                case SS_INIT:
                    parseInit(syn, taskImp);
                    break;
                case SS_BELIEFS:
                    parseBeliefs(syn, taskImp);
                    break;
                case SS_GOAL:
                case SS_GLOBAL_GOAL:
                    parseGoal(syn, taskImp);
                    break;
                case SS_ACTION_PREF:
                    parseActionPreferences(syn, taskImp);
                    break;
                case SS_CONSTRAINTS:
                    parsePreferences(syn, taskImp);
                    break;
                case SS_METRIC:
                    parseMetric(syn, taskImp);
                    break;
                case SS_BEHAVIOUR:
                    parseBehaviour(syn, taskImp);
                    break;
            }
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        }
    }

    /**
     * Parses the behaviour section (for self-interested agents).
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parseBehaviour(SynAnalyzer syn, TaskImp task) throws ParseException {
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        while (token.isSym(Symbol.SS_OPEN_PAR)) {
            token = syn.readSym(Symbol.SS_SELF_INTEREST, Symbol.SS_METRIC_THRESHOLD);
            if (token.isSym(Symbol.SS_SELF_INTEREST)) {
                try {
                    token = syn.readSym(Symbol.SS_NUMBER);
                    task.selfInterest = Double.parseDouble(token.getDesc());
                    if (task.selfInterest < 0 || task.selfInterest > 1) {
                        syn.notifyError("Self-interest level must be defined bewteen 0 and 1");
                    }
                } catch (NumberFormatException e) {
                    syn.notifyError("Invalid number format for self-interest level: " + token.getDesc());
                }
            } else if (token.isSym(Symbol.SS_METRIC_THRESHOLD)) {
                try {
                    token = syn.readSym(Symbol.SS_NUMBER);
                    task.metricThreshold = Double.parseDouble(token.getDesc());
                } catch (NumberFormatException e) {
                    syn.notifyError("Invalid number format for metric threshold: " + token.getDesc());
                }
            }
            syn.closePar();
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        }
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
                Symbol.SS_MULT, Symbol.SS_TOTAL_TIME);
        if (token.isSym(Symbol.SS_IS_VIOLATED)) {
            m = task.new MetricImp(syn.readId(), syn);
            syn.closePar();
        } else if (token.isSym(Symbol.SS_TOTAL_TIME)) {
            m = task.new MetricImp();
            syn.closePar();
        } else {
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
        }
        return m;
    }

    /**
     * Parses the preferences section.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parsePreferences(SynAnalyzer syn, TaskImp task) throws ParseException {
        TaskImp.Assignment a;
        syn.openPar();
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_AND, Symbol.SS_PREFERENCE);
        if (token.isSym(Symbol.SS_AND)) {
            do {
                token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
                if (token.isSym(Symbol.SS_OPEN_PAR)) {
                    syn.readSym(Symbol.SS_PREFERENCE);
                    String name = syn.readId();
                    a = parseAssignment(syn, task, true);
                    task.addPreference(name, a, syn);
                    syn.closePar();
                }
            } while (!token.isSym(Symbol.SS_CLOSE_PAR));
            syn.closePar();
        } else {
            String name = syn.readId();
            a = parseAssignment(syn, task, false);
            task.addPreference(name, a, syn);
            syn.closePar();
        }
    }

    /**
     * Parses a planning problem from a file.
     *
     * @param source File containing the MAP problem description
     * @param task Parsed planning task
     * @throws ParseException if there are syntactic errors
     * @throws IOException if the source cannot be read
     * @since 1.0
     */
    public void parseProblem(File source, Task task) throws ParseException,
            IOException {
        parseProblem(new java.io.FileReader(source), task);
    }

    /**
     * Parses a planning problem from an URL address.
     *
     * @param source URL Address
     * @param task Parsed planning task
     * @throws ParseException if there are syntactic errors
     * @throws IOException if the source cannot be read
     * @since 1.0
     */
    public void parseProblem(URL source, Task task) throws ParseException,
            IOException {
        parseProblem(new java.io.InputStreamReader(source.openStream()), task);
    }

    /**
     * Stores the source in a String.
     *
     * @param source Reader containing the MAP task description
     * @return String with the read content
     * @throws IOException if the source cannot be read
     * @since 1.0
     */
    private String readToString(Reader source) throws IOException {
        StringBuffer buf = new StringBuffer();
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
     * Parses the requirements section.
     *
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @throws ParseException if an error is detected
     * @since 1.0
     */
    private void parseRequirements(SynAnalyzer syn, TaskImp task) throws ParseException {
        SynAnalyzer.Token token;
        do {
            token = syn.readSym(Symbol.SS_COLON, Symbol.SS_CLOSE_PAR);
            if (token.isSym(Symbol.SS_COLON)) {
                String req = syn.readId().toUpperCase();
                if (!req.equals("STRIPS") && !req.equals("TYPING")
                        && !req.equals("FLUENTS") && !req.equals("MULTI-AGENT")
                        && !req.equals("EQUALITY") && !req.equals("NEGATIVE-PRECONDITIONS")) {
                    syn.notifyError("Requirement '" + req + "' not supported");
                }
                task.addRequirement(req);
            }
        } while (!token.isSym(Symbol.SS_CLOSE_PAR));
    }

    /**
     * Parses a set of parent types: it can be a single type of a set using the
     * EITHER keyword.
     *
     * @param syn	Syntactic analyzer
     * @param parentTypes	Array to store the set of parent types
     * @param task	Planning task
     * @throws ParseException if an error is detected
     * @since 1.0
     */
    private void parseTypeList(SynAnalyzer syn, ArrayList<TaskImp.Type> parentTypes,
            TaskImp task) throws ParseException {
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_ID);
        if (token.isSym(Symbol.SS_ID)) {
            TaskImp.Type type = task.new Type(token.getDescLower());
            int typeIndex = task.types.indexOf(type);
            if (typeIndex == -1) {
                syn.notifyError("Type '" + type.name + "' undefined");
            }
            parentTypes.add(task.types.get(typeIndex));
        } else {
            syn.readSym(Symbol.SS_EITHER);
            do {
                token = syn.readSym(Symbol.SS_ID, Symbol.SS_CLOSE_PAR);
                if (token.isSym(Symbol.SS_ID)) {
                    TaskImp.Type type = task.new Type(token.getDescLower());
                    int typeIndex = task.types.indexOf(type);
                    if (typeIndex == -1) {
                        syn.notifyError("Type '" + type.name + "' undefined");
                    }
                    parentTypes.add(task.types.get(typeIndex));
                }
            } while (!token.isSym(Symbol.SS_CLOSE_PAR));
        }
    }

    /**
     * Adds a new type to the planning task.
     *
     * @param syn	Syntactic analyzer
     * @param typeName	Name of the new type
     * @param task	Planning task
     * @return	New created type
     * @throws ParseException	If the type name is not valid
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
     * Parses the types section.
     *
     * @param syn Syntactic analyzer
     * @param task Planning task
     * @throws ParseException if errors are detected
     * @since 1.0
     */
    private void parseTypes(SynAnalyzer syn, TaskImp task) throws ParseException {
        SynAnalyzer.Token token;
        ArrayList<String> typeNames;
        ArrayList<TaskImp.Type> parentTypes;
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
                parentTypes.add(task.types.get(TaskImp.OBJECT_TYPE));
            }
            for (String typeName : typeNames) {
                TaskImp.Type type = addNewType(syn, typeName, task);
                for (TaskImp.Type parent : parentTypes) {
                    type.addParentType(parent, syn);
                }
            }
        }
    }

    /**
     * Parses the objects/constants section.
     *
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @throws ParseException If an error is detected
     * @since 1.0
     */
    private void parseObjects(SynAnalyzer syn, TaskImp task) throws ParseException {
        SynAnalyzer.Token token;
        ArrayList<String> objNames;
        ArrayList<TaskImp.Type> parentTypes;
        token = syn.readSym(Symbol.SS_ID, Symbol.SS_CLOSE_PAR);
        while (!token.isSym(Symbol.SS_CLOSE_PAR)) {
            objNames = new ArrayList<String>();
            parentTypes = new ArrayList<TaskImp.Type>();
            while (token.isSym(Symbol.SS_ID)) {
                objNames.add(token.getDescLower());
                token = syn.readSym(Symbol.SS_ID, Symbol.SS_CLOSE_PAR,
                        Symbol.SS_DASH);
            }
            if (token.isSym(Symbol.SS_DASH)) {
                parseTypeList(syn, parentTypes, task);
            } else {
                parentTypes.add(task.types.get(TaskImp.OBJECT_TYPE));
            }
            for (String objName : objNames) {
                TaskImp.Value obj = addNewObject(syn, objName, task);
                for (TaskImp.Type parent : parentTypes) {
                    obj.addType(parent, syn);
                }
            }
            token = syn.readSym(Symbol.SS_ID, Symbol.SS_CLOSE_PAR);
        }
    }

    /**
     * Adds a new object/constant to the planning task.
     *
     * @param syn	Syntactic analyzer
     * @param objName	Name of the new object
     * @param task	Planning task
     * @return	New created object
     * @throws ParseException	If the object name is not valid
     * @since 1.0
     */
    private TaskImp.Value addNewObject(SynAnalyzer syn, String objName, TaskImp task)
            throws ParseException {
        TaskImp.Value v = task.new Value(objName);
        if (task.values.contains(v)) {
            syn.notifyError("Object '" + objName + "' redefined");
        }
        task.values.add(v);
        return v;
    }

    /**
     * Parses the predicates section.
     *
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @throws ParseException If an error is detected
     * @since 1.0
     */
    private void parsePredicates(SynAnalyzer syn, TaskImp task) throws ParseException {
        SynAnalyzer.Token token;
        do {
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
            if (token.isSym(Symbol.SS_OPEN_PAR)) {
                syn.restoreLastToken();
                TaskImp.Variable v = parsePredicate(syn, task, false, true);
                task.predicates.add(v);
            }
        } while (!token.isSym(Symbol.SS_CLOSE_PAR));
    }

    /**
     * Parses a single predicate.
     *
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @param allowDuplicates True if duplicated predicates are allowed
     * @param readPar True if enclosing parenthesis must be read
     * @return	New predicate
     * @throws ParseException If an error is detected
     * @since 1.0
     */
    private TaskImp.Variable parsePredicate(SynAnalyzer syn, TaskImp task,
            boolean allowDuplicates, boolean readPar) throws ParseException {
        if (readPar) {
            syn.openPar();
        }
        TaskImp.Variable v = task.new Variable(syn.readId());
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

    /**
     * Parses the function/multi-function section.
     *
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @param multi	Multi-function or function
     * @throws ParseException If an error is detected
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
                    functionList.add(parsePredicate(syn, task, false, true));
                    token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_DASH);
                } while (token.isSym(Symbol.SS_OPEN_PAR));
                parseTypeList(syn, domain, task);
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
     * Parses an action.
     *
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @throws ParseException If an error is detected
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
     * Parses a parameter list (list of typed variables).
     *
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @return Array of values (typed variables)
     * @throws ParseException If an error is detected
     * @since 1.0
     */
    private ArrayList<TaskImp.Value> parseParameters(SynAnalyzer syn, TaskImp task) throws ParseException {
        ArrayList<TaskImp.Value> res = new ArrayList<TaskImp.Value>();
        SynAnalyzer.Token token;
        ArrayList<String> paramList;
        ArrayList<TaskImp.Type> typeList;
        do {
            token = syn.readSym(Symbol.SS_VAR, Symbol.SS_CLOSE_PAR);
            if (!token.isSym(Symbol.SS_CLOSE_PAR)) {
                String desc = token.getDescLower();
                paramList = new ArrayList<String>();
                typeList = new ArrayList<TaskImp.Type>();
                do {
                    paramList.add(desc);
                    token = syn.readSym(Symbol.SS_VAR, Symbol.SS_DASH, Symbol.SS_CLOSE_PAR);
                    desc = token.getDescLower();
                } while (token.isSym(Symbol.SS_VAR));
                if (token.isSym(Symbol.SS_DASH)) {
                    parseTypeList(syn, typeList, task);
                } else {
                    typeList.add(task.types.get(TaskImp.OBJECT_TYPE));
                }
                for (String paramName : paramList) {
                    TaskImp.Value v = task.new Value(paramName);
                    v.isVariable = true;
                    if (res.contains(v)) {
                        syn.notifyError("Parameter '" + paramName + "' redefined");
                    }
                    for (TaskImp.Type t : typeList) {
                        v.addType(t, syn);
                    }
                    res.add(v);
                }
            }
        } while (!token.isSym(Symbol.SS_CLOSE_PAR));
        syn.restoreLastToken();
        return res;
    }

    /**
     * Parses the operator precondition or effect.
     *
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @param op	Operator
     * @param isPrec	True for parsing a precondition, false for an effect
     * @throws ParseException If an error is detected
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
     * Parses the operator precondition or effect.
     *
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @param op	Operator
     * @param isPrec	True for parsing a precondition, false for an effect
     * @return Parsed operator condition
     * @throws ParseException If an error is detected
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
     * Checks the correctness of an operator's function condition.
     *
     * @param cond	Function condition to check
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @throws ParseException If an error is detected
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
     * Checks the correctness of a function.
     *
     * @param var	Variable corresponding to the function to check
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @return Original function corresponding to the variable
     * @throws ParseException If an error is detected
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
     * Checks the correctness of an operator's predicate condition.
     *
     * @param var	Variable corresponding to the function to check
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @throws ParseException If an error is detected
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
     * Parses a variable within an operator condition.
     *
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @param op	Operator
     * @return	Parsed variable
     * @throws ParseException If an error is detected
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
     * Parses a value (a reference to an operator parameter or a constant).
     *
     * @param syn	Syntactic analyzer
     * @param task	Planning task
     * @param op	Operator
     * @return	Parsed value
     * @throws ParseException If an error is detected
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
     * Parses the shared data.
     *
     * @param syn Syntactic analyzer
     * @param task Planning task
     * @throws ParseException If an error is detected
     * @since 1.0
     */
    private void parseSharedData(SynAnalyzer syn, TaskImp task) throws ParseException {
        SynAnalyzer.Token token;
        ArrayList<Object> data = new ArrayList<>();
        ArrayList<String> agents = new ArrayList<>();
        do {
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
            if (token.isSym(Symbol.SS_OPEN_PAR)) {
                token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_ID);
                syn.restoreLastToken();
                if (token.isSym(Symbol.SS_OPEN_PAR)) { 	// Function
                    TaskImp.Variable v = parsePredicate(syn, task, true, true);
                    TaskImp.Function origFnc = checkFunction(v, syn, task);
                    TaskImp.Function f = task.new Function(v, origFnc.multiFunction);
                    syn.readSym(Symbol.SS_DASH);
                    token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_ID);
                    if (token.isSym(Symbol.SS_OPEN_PAR)) {	// Either
                        syn.readSym(Symbol.SS_EITHER);
                        do {
                            f.addDomainType(syn, syn.readId().toLowerCase());
                            token = syn.readSym(Symbol.SS_CLOSE_PAR, Symbol.SS_ID);
                            if (token.isSym(Symbol.SS_ID)) {
                                syn.restoreLastToken();
                            }
                        } while (!token.isSym(Symbol.SS_CLOSE_PAR));
                    } else {
                        f.addDomainType(syn, token.getDescLower());
                    }
                    for (TaskImp.Type t : f.domain) {
                        if (!t.isCompatible(origFnc.domain)) {
                            syn.notifyError("Type '"
                                    + t.name + "' is not in the function's domain");
                        }
                    }
                    data.add(f);
                } else {								// Predicate
                    TaskImp.Variable v = parsePredicate(syn, task, true, false);
                    checkPredicate(v, syn, task);
                    data.add(v);
                }
                syn.closePar();
                token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_DASH);
                if (token.isSym(Symbol.SS_OPEN_PAR)) {
                    syn.restoreLastToken();
                } else {									// Agent list
                    token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_ID);
                    if (token.isSym(Symbol.SS_OPEN_PAR)) {	// Either
                        syn.readSym(Symbol.SS_EITHER);
                        do {
                            agents.add(syn.readId());
                            token = syn.readSym(Symbol.SS_CLOSE_PAR, Symbol.SS_ID);
                            if (token.isSym(Symbol.SS_ID)) {
                                syn.restoreLastToken();
                            }
                        } while (!token.isSym(Symbol.SS_CLOSE_PAR));
                        token.set(Symbol.SS_UNDEFINED, "");
                    } else {
                        agents.add(token.getDescLower());
                    }
                    for (Object d : data) {
                        addSharedData(syn, task, d, agents);
                    }
                    data.clear();
                    agents.clear();
                }
            }
        } while (!token.isSym(Symbol.SS_CLOSE_PAR));
        if (!data.isEmpty()) {
            syn.notifyError("Expected agent list");
        }
    }

    /**
     * Adds a variable/function to the shared data.
     *
     * @param syn Syntactic analyzer
     * @param task Planning task
     * @param data Variable or Function
     * @param agents Agent list
     * @throws ParseException If an error is detected
     * @since 1.0
     */
    private void addSharedData(SynAnalyzer syn, TaskImp task, Object data,
            ArrayList<String> agents) throws ParseException {
        TaskImp.SharedData sd;
        TaskImp.Type agType = task.getAgentType();
        if (agType == null) {
            syn.notifyError("Agent type is not defined");
        }
        if (data instanceof TaskImp.Variable) {
            sd = task.new SharedData((TaskImp.Variable) data);
        } else {
            sd = task.new SharedData((TaskImp.Function) data);
        }
        for (String agName : agents) {
            int objIndex = task.values.indexOf(task.new Value(agName.toLowerCase()));
            if (objIndex == -1) {
                syn.notifyError("Agent '" + agName + "' undefined");
            }
            TaskImp.Value v = task.values.get(objIndex);
            boolean isAgent = false;
            for (TaskImp.Type t : v.types) {
                if (t.isCompatible(agType)) {
                    isAgent = true;
                    break;
                }
            }
            if (!isAgent) {
                syn.notifyError("Object '" + agName + "' is not an agent");
            }
            sd.agents.add(v);
        }
        task.sharedData.add(sd);
    }

    /**
     * Parses the init section.
     *
     * @param syn Syntactic analyzer
     * @param task Planning task
     * @throws ParseException If an error is detected
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
     * Parses an assignment.
     *
     * @param syn Syntactic analyzer
     * @param task Planning task
     * @param readPar True to read enclosing parenthesis
     * @throws ParseException If an error is detected
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
     * Check if an assignment is correct.
     *
     * @param syn Syntactic analyzer
     * @param task Planning task
     * @param a Assignment
     * @throws ParseException If an error is detected
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
            if (!a.isNumeric) {
                for (TaskImp.Value v : a.values) {
                    if (!v.isCompatible(a.fnc.domain)) {
                        syn.notifyError("Wrong value '" + v.name + "' for function '" + var.name + "'");
                    }
                }
            } else {
                TaskImp.Function fn = checkFunction(var, syn, task);
                if (!fn.isNumeric()) {
                    syn.notifyError("Function '" + var.name + "' is not numeric");
                }
                if (a.neg) {
                    syn.notifyError("Cannot negate a numeric function");
                }
            }
        }
    }

    /**
     * Parses a value within an assignment.
     *
     * @param syn Syntactic analyzer
     * @param task Planning task
     * @return Parsed value
     * @throws ParseException If the value is undefined
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
     * Parses a goal section.
     *
     * @param syn Syntactic analyzer
     * @param task Planning task
     * @param global True for global goals
     * @throws ParseException If an error is detected
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
     * Parses the action preferences.
     *
     * @param syn Syntactic analyzer
     * @param task Planning task
     * @throws ParseException If an error is detected
     * @since 1.0
     */
    private void parseActionPreferences(SynAnalyzer syn, TaskImp task) throws ParseException {
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        while (token.isSym(Symbol.SS_OPEN_PAR)) {
            String opName = syn.readId();
            String value = syn.readId();
            int v = -1;
            try {
                v = Integer.parseInt(value);
            } catch (NumberFormatException e) {
                syn.notifyError("Preference value '" + value + "' is not a valid integer value");
            }
            boolean opFound = false;
            for (TaskImp.Operator op : task.operators) {
                if (op.name.equalsIgnoreCase(opName)) {
                    opFound = true;
                    if (op.preference != -1) {
                        syn.notifyError("Preference for operator '" + opName + "' already set");
                    }
                    op.preference = v;
                    break;
                }
            }
            if (!opFound) {
                syn.notifyError("Operator '" + opName + "' undefined");
            }
            syn.closePar();
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        }
    }

    /**
     * Parses the beliefs section.
     *
     * @param syn Syntactic analyzer
     * @param task Planning task
     * @throws ParseException If an error is detected
     * @since 1.0
     */
    private void parseBeliefs(SynAnalyzer syn, TaskImp task) throws ParseException {
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        while (token.isSym(Symbol.SS_OPEN_PAR)) {
            parseRule(syn, task);
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        }
    }

    /**
     * Parses a belief rule.
     *
     * @param syn Syntactic analyzer
     * @param task Planning task
     * @throws ParseException If an error is detected
     * @since 1.0
     */
    private void parseRule(SynAnalyzer syn, TaskImp task) throws ParseException {
        syn.colon();
        syn.readSym(Symbol.SS_DEF_RULE);
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_COLON, Symbol.SS_ID);
        String name;
        if (token.isSym(Symbol.SS_COLON)) {
            name = "R" + task.beliefs.size();
        } else {
            name = token.getDesc();
            syn.colon();
        }
        TaskImp.Operator op = task.new Operator(name);
        task.beliefs.add(op);
        boolean precRead = false, effRead = false;
        token = syn.readSym(Symbol.SS_PARAMS, Symbol.SS_BODY, Symbol.SS_HEAD);
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
                case SS_BODY:
                    parseOperatorCondition(syn, task, op, true);
                    precRead = true;
                    break;
                case SS_HEAD:
                    parseOperatorCondition(syn, task, op, false);
                    effRead = true;
                    break;
            }
            token = syn.readSym(Symbol.SS_OPEN_PAR,
                    Symbol.SS_COLON, Symbol.SS_CLOSE_PAR);
            if (token.isSym(Symbol.SS_COLON)) {
                if (!precRead) {
                    token = syn.readSym(Symbol.SS_BODY, Symbol.SS_HEAD);
                } else if (!effRead) {
                    token = syn.readSym(Symbol.SS_HEAD);
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
                    TaskImp.Variable v = op != null ? parseOperatorVariable(syn, task, op)
                            : parseCongestionVariable(syn, task, congestion);
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
     * Parses the congestion operators.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parseCongestion(SynAnalyzer syn, TaskImp task) throws ParseException {
        TaskImp.CongestionImp congestion = task.new CongestionImp(syn.readId());
        if (task.congestions.contains(congestion)) {
            syn.notifyError("Congestion '" + congestion.name + "' redefined");
        }
        task.congestions.add(congestion);
        syn.colon();
        boolean usageRead = false, penaltyRead = false;
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_PARAMS, Symbol.SS_VARIABLES,
                Symbol.SS_USAGE, Symbol.SS_PENALTY);
        do {
            switch (token.getSym()) {
                case SS_VARIABLES:
                case SS_PARAMS:
                    syn.openPar();
                    ArrayList<TaskImp.Value> params = parseParameters(syn, task);
                    for (TaskImp.Value p : params) {
                        if (token.isSym(Symbol.SS_PARAMS)) {
                            congestion.addParameter(p, syn);
                        } else {
                            congestion.addVariable(p, syn);
                        }
                    }
                    syn.closePar();
                    break;
                case SS_USAGE:
                    if (usageRead) {
                        syn.notifyError("Usage duplicated in congestion");
                    }
                    usageRead = true;
                    congestion.usage = parseCongestionUsage(syn, task, congestion);
                    break;
                case SS_PENALTY:
                    if (penaltyRead) {
                        syn.notifyError("Penalty duplicated in congestion");
                    }
                    penaltyRead = true;
                    parseCongestionPenalty(syn, task, congestion);
                    break;
            }
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_COLON, Symbol.SS_CLOSE_PAR);
            if (token.isSym(Symbol.SS_COLON)) {
                token = syn.readSym(Symbol.SS_PARAMS, Symbol.SS_VARIABLES,
                        Symbol.SS_USAGE, Symbol.SS_PENALTY);
            }
        } while (!token.isSym(Symbol.SS_CLOSE_PAR) && !token.isSym(Symbol.SS_OPEN_PAR));
        if (token.isSym(Symbol.SS_OPEN_PAR)) {
            syn.restoreLastToken();
        }
    }

    /**
     * Parses the congestion operator usage.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param congestion Congestion operator
     * @return Parsed congestion usage
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.CongestionUsageImp parseCongestionUsage(SynAnalyzer syn, TaskImp task, TaskImp.CongestionImp congestion) throws ParseException {
        syn.openPar();
        TaskImp.CongestionUsageImp usage;
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_OR, Symbol.SS_AND, Symbol.SS_ID);
        if (token.isSym(Symbol.SS_OR) || token.isSym(Symbol.SS_AND)) {
            if (token.isSym(Symbol.SS_OR)) {
                usage = task.new CongestionUsageImp(TaskImp.CongestionUsageType.CUT_OR);
            } else {
                usage = task.new CongestionUsageImp(TaskImp.CongestionUsageType.CUT_AND);
            }
            do {
                token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
                if (token.isSym(Symbol.SS_OPEN_PAR)) {
                    syn.restoreLastToken();
                    usage.addCondition(parseCongestionUsage(syn, task, congestion));
                }
            } while (!token.isSym(Symbol.SS_CLOSE_PAR));
        } else {
            syn.restoreLastToken();
            TaskImp.CongestionAction action = parseCongestionAction(syn, task, congestion);
            usage = task.new CongestionUsageImp(action);
        }
        return usage;
    }

    /**
     * Parses the congestion operator penalty.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param congestion Congestion operator
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private void parseCongestionPenalty(SynAnalyzer syn, TaskImp task, TaskImp.CongestionImp congestion) throws ParseException {
        syn.openPar();
        syn.readSym(Symbol.SS_AND);
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        while (token.isSym(Symbol.SS_OPEN_PAR)) {
            syn.restoreLastToken();
            TaskImp.CongestionPenaltyImp penalty = parseCongestionPenaltyExpression(syn, task, congestion);
            congestion.addPenalty(penalty);
            token = syn.readSym(Symbol.SS_OPEN_PAR, Symbol.SS_CLOSE_PAR);
        }
    }

    /**
     * Parses a congestion action.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param congestion Congestion operator
     * @return Parsed congestion action
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.CongestionAction parseCongestionAction(SynAnalyzer syn, TaskImp task, TaskImp.CongestionImp congestion) throws ParseException {
        String name = syn.readId();
        int opIndex = task.operators.indexOf(task.new Operator(name));
        if (opIndex < 0) {
            syn.notifyError("Operator '" + name + "' undefined");
        }
        TaskImp.CongestionAction action = task.new CongestionAction(task.operators.get(opIndex));
        for (int i = 0; i < action.op.params.size(); i++) {
            SynAnalyzer.Token token = syn.readSym(Symbol.SS_VAR, Symbol.SS_ID);
            name = token.getDesc();
            TaskImp.Value value;
            if (token.isSym(Symbol.SS_VAR)) {
                value = congestion.getParamOrVar(name);
                if (value == null) {
                    syn.notifyError("Parameter '" + name + "' undefined");
                }
                if (!value.isCompatible(action.op.params.get(i).types)) {
                    syn.notifyError("Invalid type of parameter '" + name + "'");
                }
            } else {
                int objIndex = task.values.indexOf(task.new Value(name));
                if (objIndex < 0) {
                    syn.notifyError("Constant '" + name + "' undefined");
                }
                value = task.values.get(objIndex);
            }
            action.addParameter(value);
        }
        syn.closePar();
        return action;
    }

    /**
     * Parses an expression in a congestion operator penalty.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param congestion Congestion operator
     * @return Parsed expression
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.CongestionPenaltyImp parseCongestionPenaltyExpression(SynAnalyzer syn, TaskImp task, TaskImp.CongestionImp congestion) throws ParseException {
        syn.openPar();
        syn.readSym(Symbol.SS_WHEN);
        syn.openPar();
        SynAnalyzer.Token token = syn.readSym(Symbol.SS_EQUAL, Symbol.SS_GREATER,
                Symbol.SS_GREATER_EQ, Symbol.SS_LESS, Symbol.SS_LESS_EQ,
                Symbol.SS_DISTINCT);
        TaskImp.CongestionPenaltyImp penalty = null;
        switch (token.getSym()) {
            case SS_EQUAL:
                penalty = task.new CongestionPenaltyImp(TaskImp.ConditionType.CT_EQUAL);
                break;
            case SS_GREATER:
                penalty = task.new CongestionPenaltyImp(TaskImp.ConditionType.CT_GREATER);
                break;
            case SS_GREATER_EQ:
                penalty = task.new CongestionPenaltyImp(TaskImp.ConditionType.CT_GREATER_EQ);
                break;
            case SS_LESS:
                penalty = task.new CongestionPenaltyImp(TaskImp.ConditionType.CT_LESS);
                break;
            case SS_LESS_EQ:
                penalty = task.new CongestionPenaltyImp(TaskImp.ConditionType.CT_LESS_EQ);
                break;
            case SS_DISTINCT:
                penalty = task.new CongestionPenaltyImp(TaskImp.ConditionType.CT_DISTINCT);
                break;
        }
        syn.openPar();
        String id = syn.readId();
        if (!id.equalsIgnoreCase("usage")) {
            syn.notifyError(id + " found, but 'usage' expected");
        }
        syn.closePar();
        token = syn.readSym(Symbol.SS_NUMBER);
        try {
            penalty.conditionValue = Double.parseDouble(token.getDesc());
        } catch (NumberFormatException e) {
            syn.notifyError("'" + token.getDesc() + "' is not a valid number");
        }
        syn.closePar();
        syn.openPar();
        syn.readSym(Symbol.SS_INCREASE);
        syn.openPar();
        penalty.setVariable(parseCongestionVariable(syn, task, congestion));
        penalty.setIncrement(parseNumericExpression(syn, task, null, congestion));
        syn.closePar();
        return penalty;
    }

    /**
     * Parses a variable in a congestion operator.
     *
     * @param syn Syntactic analyzer
     * @param task Parsed task
     * @param congestion Congestion operator
     * @return Parsed variable
     * @throws ParseException If a parse error is detected
     * @since 1.0
     */
    private TaskImp.Variable parseCongestionVariable(SynAnalyzer syn, TaskImp task, TaskImp.CongestionImp congestion) throws ParseException {
        TaskImp.Variable v = task.new Variable(syn.readId());
        int fnIndex = task.functions.indexOf(task.new Function(v, false));
        TaskImp.Function fn = task.functions.get(fnIndex);
        if (!fn.isNumeric()) {
            syn.notifyError("Function '" + v.name + "' is not numeric");
        }
        SynAnalyzer.Token token;
        for (int i = 0; i < fn.var.params.size(); i++) {
            token = syn.readSym(Symbol.SS_VAR);
            String name = token.getDesc();
            TaskImp.Value value = congestion.getParamOrVar(name);
            if (value == null) {
                syn.notifyError("Parameter '" + name + "' undefined");
            }
            if (!value.isCompatible(fn.var.params.get(i).types)) {
                syn.notifyError("Invalid type of parameter '" + name + "'");
            }
            v.params.add(value);
        }
        syn.closePar();
        return v;
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
        return parseDomain(new java.io.File(domainFile));
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
        parseProblem(new java.io.File(problemFile), planningTask);
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
        String content = readToString(new java.io.FileReader(new java.io.File(domainFile))).toLowerCase();
        return content.contains(":factored");
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
        String content = readToString(new java.io.FileReader(new java.io.File(agentsFile)));
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

}
