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

import org.agreement_technologies.common.map_parser.*;

/**
 * TaskTypes class contains several types for ungrounded task elements.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class TaskTypes {

    /**
     * A parameter represents a name with a list of types.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class ParameterImp implements Parameter {

        String name;        // Parameter name
        String[] types;     // List of types of this parameter

        /**
         * Constructor of a parameter.
         *
         * @param name Parameter name
         * @since 1.0
         */
        public ParameterImp(String name) {
            this.name = name;
        }

        /**
         * Gets the parameter name.
         *
         * @return Name of the parameter
         * @since 1.0
         */
        @Override
        public String getName() {
            return name;
        }

        /**
         * Return the parameter type list.
         *
         * @return Array with the type names of this parameter
         * @since 1.0
         */
        @Override
        public String[] getTypes() {
            return types;
        }

        /**
         * Returns a description of this parameter.
         *
         * @return Parameter description
         * @since 1.0
         */
        @Override
        public String toString() {
            String res = name;
            if (types.length > 0) {
                res += " -";
                for (String t : types) {
                    res += " " + t;
                }
            }
            return res;
        }
    }

    /**
     * FunctionImp class represents ungrounded functions.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class FunctionImp implements Function {

        String name;                // Function name
        boolean multifunction;      // Indicates if this is a multi-function
        ParameterImp[] parameters;  // Function parameters
        String[] domain;            // Function co-domain

        /**
         * Constructor of an ungrounded function.
         *
         * @param name Function name
         * @param multifunction True if this is a multi-function
         * @since 1.0
         */
        public FunctionImp(String name, boolean multifunction) {
            this.name = name;
            this.multifunction = multifunction;
        }

        /**
         * Retrieves the function name.
         *
         * @return Function name
         * @since 1.0
         */
        @Override
        public String getName() {
            return name;
        }

        /**
         * Returns the function parameters.
         *
         * @return Array of the function parameters
         * @since 1.0
         */
        @Override
        public Parameter[] getParameters() {
            return parameters;
        }

        /**
         * Returns the function co-domain.
         *
         * @return Array of type names of the function
         * @since 1.0
         */
        @Override
        public String[] getDomain() {
            return domain;
        }

        /**
         * Checks if this is a multi-function.
         *
         * @return <code>true</code>, if this one is a multi-function;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean isMultifunction() {
            return multifunction;
        }

        /**
         * Returns a description of this function.
         *
         * @return Description of this function
         * @since 1.0
         */
        @Override
        public String toString() {
            String res = "((" + name;
            for (Parameter p : parameters) {
                res += " " + p;
            }
            res += ")";
            if (domain.length > 0) {
                res += " -";
                for (String d : domain) {
                    res += " " + d;
                }
            }
            if (multifunction) {
                res += "*";
            }
            return res + ")";
        }
    }

    /**
     * ConditionImp class represents an ungrounded condition.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class ConditionImp implements Condition {

        int type;               // Condition type
        FunctionImp fnc;        // Function/variable to check
        String value;           // Value for the variable
        private static final String[] typeName = {"=", "<>", "member",
            "not member", "assign", "add", "del"};

        /**
         * Returns the condition type.
         *
         * @return Condition type
         * @since 1.0
         */
        @Override
        public int getType() {
            return type;
        }

        /**
         * Returns the condition function.
         *
         * @return Function in the condition
         * @since 1.0
         */
        @Override
        public Function getFunction() {
            return fnc;
        }

        /**
         * Returns the condition value.
         *
         * @return Value of the condition
         * @since 1.0
         */
        @Override
        public String getValue() {
            return value;
        }

        /**
         * Returns a description of this condition.
         *
         * @return Description of this condition
         * @since 1.0
         */
        @Override
        public String toString() {
            return "(" + typeName[type] + " " + fnc + " " + value + ")";
        }
    }

    /**
     * NumericExpressionImp class implements a numeric expression.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class NumericExpressionImp implements NumericExpression {

        int type;                       // Expression type 
        double value;                   // Constant value
        FunctionImp var;                // Numeric variable
        NumericExpressionImp left;      // Left operand
        NumericExpressionImp right;     // Right operand

        /**
         * Creates a new numeric expression.
         *
         * @param type Expression type
         * @since 1.0
         */
        NumericExpressionImp(int type) {
            this.type = type;
        }

        /**
         * Gets a description of this expression.
         *
         * @return Description of this expression
         * @since 1.0
         */
        @Override
        public String toString() {
            String res;
            switch (type) {
                case NUMBER:
                    res = "" + value;
                    break;
                case VARIABLE:
                    res = var.toString();
                    break;
                case USAGE:
                    res = "(usage)";
                    break;
                case ADD:
                    res = "(+ " + left + " " + right + ")";
                    break;
                case DEL:
                    res = "(- " + left + " " + right + ")";
                    break;
                case PROD:
                    res = "(* " + left + " " + right + ")";
                    break;
                case DIV:
                    res = "(/ " + left + " " + right + ")";
                    break;
                default:
                    res = "<error>";
            }
            return res;
        }

        /**
         * Gets the numeric expression type.
         *
         * @return Numeric expression type
         * @since 1.0
         */
        @Override
        public int getType() {
            return type;
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
        public Function getNumericVariable() {
            return var;
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
            return null;
        }
    }

    /**
     * NumericEffectImp class implements action numeric effects. Only "increase"
     * effects are implemented in this version.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class NumericEffectImp implements NumericEffect {

        int type;                   // Effect type
        FunctionImp var;            // Numeric variable to update
        NumericExpressionImp exp;   // Expression for updating the variable
        private static final String[] typeName = {"increase"};

        NumericEffectImp(int type) {
            this.type = type;
        }

        /**
         * Returns a description of this effect.
         *
         * @return Effect description
         * @since 1.0
         */
        @Override
        public String toString() {
            return "(" + typeName[type] + " " + var + " " + exp + ")";
        }

        /**
         * Gets the effect type.
         *
         * @return Effect type
         * @since 1.0
         */
        @Override
        public int getType() {
            return type;
        }

        /**
         * Gets the numeric function that will be updated.
         *
         * @return Numeric function
         * @since 1.0
         */
        @Override
        public Function getNumericVariable() {
            return var;
        }

        /**
         * Gets the numeric expression that will be used to update the function.
         *
         * @return Numeric expression
         * @since 1.0
         */
        @Override
        public NumericExpression getNumericExpression() {
            return exp;
        }
    }

    /**
     * OperatorImp class implements operators (ungrounded actions).
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class OperatorImp implements Operator {

        String name;                // Operator name
        ParameterImp[] parameters;  // Operator parametes
        ConditionImp[] prec, eff;   // Preconditions and effects
        NumericEffectImp[] numEff;  // Numeric effects
        int preference;             // Preference index

        /**
         * Constructor of an operator.
         *
         * @param name Operator name
         * @param preference Preference index (-1 if this is not a preference)
         * @since 1.0
         */
        public OperatorImp(String name, int preference) {
            this.name = name;
            this.preference = preference;
        }

        /**
         * Returns the operator name.
         *
         * @return Operator name
         * @since 1.0
         */
        @Override
        public String getName() {
            return name;
        }

        /**
         * Returns the operator parameters.
         *
         * @return Array with the operator parameters
         * @since 1.0
         */
        @Override
        public Parameter[] getParameters() {
            return parameters;
        }

        /**
         * Returns the operator parameters.
         *
         * @return Array with the operator parameters
         * @since 1.0
         */
        @Override
        public Condition[] getPrecondition() {
            return prec;
        }

        /**
         * Get the operator effect (list of effects)
         *
         * @return Array with the operator effects
         * @since 1.0
         */
        @Override
        public Condition[] getEffect() {
            return eff;
        }

        /**
         * Returns a description of this operator.
         *
         * @return Description of this operator
         * @since 1.0
         */
        @Override
        public String toString() {
            String res = "(" + name;
            if (parameters.length > 0) {
                res += "(";
                for (int i = 0; i < parameters.length; i++) {
                    if (i == 0) {
                        res += parameters[i];
                    } else {
                        res += " " + parameters[i];
                    }
                }
                res += ")";
            }
            if (prec.length > 0) {
                res += "\n\tPrec: (and";
                for (Condition c : prec) {
                    res += " " + c;
                }
                res += ")";
            }
            if (eff.length > 0) {
                res += "\n\tEff: (and";
                for (Condition c : eff) {
                    res += " " + c;
                }
                res += ")";
            }
            return res;
        }

        /**
         * Returns the preference value. Returns -1 if it is not set.
         *
         * @return Preference value; -1 if it is not set
         * @since 1.0
         */
        @Override
        public int getPreferenceValue() {
            return preference;
        }

        /**
         * Get the numeric effects (list of effects) of the operator.
         *
         * @return Array of numeric effects
         * @since 1.0
         */
        @Override
        public NumericEffect[] getNumericEffects() {
            return numEff;
        }
    }

    /**
     * SharedDataImp class represents shared data, i.e. public information that
     * the current agent can share with other agents.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class SharedDataImp implements SharedData {

        FunctionImp fnc;    // Function to share
        String[] agents;    // List of agents to share with

        /**
         * Returns the function to share.
         *
         * @return Function to share
         * @since 1.0
         */
        @Override
        public Function getFunction() {
            return fnc;
        }

        /**
         * Gets the list of agents that can observe this function.
         *
         * @return Array of agent names
         * @since 1.0
         */
        @Override
        public String[] getAgents() {
            return agents;
        }

        /**
         * Returns a description of this shared data.
         *
         * @return Description of this shared data
         * @since 1.0
         */
        @Override
        public String toString() {
            String res = "(" + fnc + " -";
            for (String ag : agents) {
                res += " " + ag;
            }
            return res + ")";
        }
    }

    /**
     * FactImp class reprenets ungrounded facts.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class FactImp implements Fact {

        String name;            // Function name
        String parameters[];    // Function parameters
        String values[];        // Assigned values
        boolean neg;            // Indicates if the fact is negated (not)

        /**
         * Creates a new fact.
         *
         * @param name Function name
         * @param neg Indicates if the fact is negated (not)
         * @since 1.0
         */
        public FactImp(String name, boolean neg) {
            this.name = name;
            this.neg = neg;
        }

        /**
         * Gets the function name.
         *
         * @return Function name
         * @since 1.0
         */
        @Override
        public String getFunctionName() {
            return name;
        }

        /**
         * Returns the function parameters.
         *
         * @return Array of parameter names
         * @since 1.0
         */
        @Override
        public String[] getParameters() {
            return parameters;
        }

        /**
         * Returns the list of values assigned to the function.
         *
         * @return Array of values assigned to the function
         * @since 1.0
         */
        @Override
        public String[] getValues() {
            return values;
        }

        /**
         * Returns a description of this fact.
         *
         * @return Description of this fact
         * @since 1.0
         */
        @Override
        public String toString() {
            String res;
            if (neg) {
                res = "(not (= (" + name;
            } else {
                res = "(= (" + name;
            }
            for (String p : parameters) {
                res += " " + p;
            }
            res += ") ";
            if (values.length != 1) {
                res += "{";
            }
            for (int i = 0; i < values.length; i++) {
                if (i == 0) {
                    res += values[i];
                } else {
                    res += " " + values[i];
                }
            }
            if (values.length != 1) {
                res += "}";
            }
            if (neg) {
                res += ")";
            }
            return res + ")";
        }

        /**
         * Checks whether the assignment is negated.
         *
         * @return <code>true</code>, if the assignment is negated (not);
         * <code>false</code>, otherwise
         * @since 1.0
         */
        @Override
        public boolean negated() {
            return neg;
        }
    }
}
