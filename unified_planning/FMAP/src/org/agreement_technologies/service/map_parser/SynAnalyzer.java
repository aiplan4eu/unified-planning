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

/**
 * Syntactic analyzer for the native PDDL-FMAP Language.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class SynAnalyzer {

    // Input file
    private final java.util.Scanner file;
    // Allows to read again the last token
    private boolean useLastToken;
    // Stores the last read token
    private Token lastToken;
    // Read buffer
    private String buffer;
    // Current line number
    private int lineNumber;

    /**
     * Constructor.
     *
     * @param fileContent Content of the file as a String
     * @since 1.0
     */
    public SynAnalyzer(String fileContent) {
        useLastToken = false;
        lastToken = null;
        buffer = "";
        lineNumber = 0;
        file = new java.util.Scanner(fileContent);
    }

    /**
     * Retrieves the next token.
     *
     * @return Next token in the file
     * @since 1.0
     */
    public Token nextToken() {
        if (useLastToken) {
            useLastToken = false;
            return lastToken;
        }
        Token res = new Token();
        if (buffer.length() > 0
                && // Skip comments
                (buffer.charAt(0) == ';' || buffer.charAt(0) == '\\')) {
            buffer = "";
        }
        while (buffer.length() == 0 && file.hasNext()) {
            buffer = file.nextLine().trim();
            lineNumber++;
            if (buffer.length() > 0 && (buffer.charAt(0) == ';' || buffer.charAt(0) == '\\')) {
                buffer = "";
            }
        }
        if (buffer.length() > 0) {
            switch (buffer.charAt(0)) {
                case '(':
                    res.set(Symbol.SS_OPEN_PAR, "(");
                    break;
                case ')':
                    res.set(Symbol.SS_CLOSE_PAR, ")");
                    break;
                case '{':
                    res.set(Symbol.SS_OPEN_SET, "{");
                    break;
                case '}':
                    res.set(Symbol.SS_CLOSE_SET, "}");
                    break;
                case ':':
                    res.set(Symbol.SS_COLON, ":");
                    break;
                case '-':
                    res.set(Symbol.SS_DASH, "-");
                    break;
                case '=':
                    res.set(Symbol.SS_EQUAL, "=");
                    break;
                case '+':
                    res.set(Symbol.SS_PLUS, "+");
                    break;
                case '*':
                    res.set(Symbol.SS_MULT, "*");
                    break;
                case '/':
                    res.set(Symbol.SS_DIV, "/");
                    break;
                case '>':
                    if (buffer.length() > 1 && buffer.charAt(1) == '=') {
                        buffer = buffer.substring(1).trim();
                        res.set(Symbol.SS_GREATER_EQ, ">=");
                    } else {
                        res.set(Symbol.SS_GREATER, ">");
                    }
                    break;
                case '<':
                    if (buffer.length() > 1 && buffer.charAt(1) == '=') {
                        buffer = buffer.substring(1).trim();
                        res.set(Symbol.SS_LESS_EQ, "<=");
                    } else {
                        res.set(Symbol.SS_LESS, "<");
                    }
                    break;
                case '!':
                    if (buffer.length() > 1 && buffer.charAt(1) == '=') {
                        res.set(Symbol.SS_DISTINCT, "!=");
                        buffer = buffer.substring(1).trim();
                    }
                    break;
            }
            if (res.undefined()) {
                int pos = 1;
                while (pos < buffer.length() && buffer.charAt(pos) > ' '
                        && buffer.charAt(pos) != ')' && buffer.charAt(pos) != '('
                        && buffer.charAt(pos) != '[' && buffer.charAt(pos) != ']'
                        && buffer.charAt(pos) != '{' && buffer.charAt(pos) != '}'
                        && buffer.charAt(pos) != ',') {
                    pos++;
                }
                String word = buffer.substring(0, pos);
                if (word.startsWith("?")) {
                    res.set(Symbol.SS_VAR, word);
                } else {
                    if ((word.charAt(0) >= '0' && word.charAt(0) <= '9') || word.startsWith(".")) {
                        res.set(Symbol.SS_NUMBER, word);
                    } else {
                        res.set(Symbol.SS_ID, word);
                    }
                }
                buffer = buffer.substring(pos).trim();
            } else {
                buffer = buffer.substring(1).trim();
            }
        }
        lastToken = res;
        return res;
    }

    /**
     * Reads a given symbol
     *
     * @param sym Expected symbols
     * @return Read token
     * @throws java.text.ParseException If error is detected
     * @since 1.0
     */
    public Token readSym(Symbol... sym) throws java.text.ParseException {
        Token res = nextToken();
        boolean found = false;
        for (int i = 0; i < sym.length && !found; i++) {
            if (res.isSym(sym[i])) {
                found = true;
                res.symbol = sym[i];
            }
        }
        if (!found) {
            notifyError("Unexpected token: '" + res.desc + "'");
        }
        return res;
    }

    /**
     * Reads an open parentheses.
     *
     * @throws java.text.ParseException If an error is detected
     * @since 1.0
     */
    public void openPar() throws java.text.ParseException {
        Token res = nextToken();
        if (!res.isSym(Symbol.SS_OPEN_PAR)) {
            notifyError("Open parenthesis expected");
        }
    }

    /**
     * Reads a close parentheses.
     *
     * @throws java.text.ParseException If an error is detected
     * @since 1.0
     */
    public void closePar() throws java.text.ParseException {
        Token res = nextToken();
        if (!res.isSym(Symbol.SS_CLOSE_PAR)) {
            notifyError("Close parenthesis expected");
        }
    }

    /**
     * Reads a colon.
     *
     * @throws java.text.ParseException If an error is detected
     * @since 1.0
     */
    public void colon() throws java.text.ParseException {
        Token res = nextToken();
        if (!res.isSym(Symbol.SS_COLON)) {
            notifyError("Colon expected");
        }
    }

    /**
     * Read an identifier.
     *
     * @return Identifier
     * @throws java.text.ParseException If an error is detected
     * @since 1.0
     */
    public String readId() throws java.text.ParseException {
        Token res = nextToken();
        if (!res.isSym(Symbol.SS_ID)) {
            notifyError("Identifier expected");
        }
        return res.desc;
    }

    /**
     * Notifies a parser error.
     *
     * @param msg Error message
     * @throws java.text.ParseException Notifies the error
     * @since 1.0
     */
    public void notifyError(String msg) throws java.text.ParseException {
        throw new java.text.ParseException("Parser error: " + msg, lineNumber);
    }

    /**
     * Restores the last read token.
     *
     * @since 1.0
     */
    public void restoreLastToken() {
        useLastToken = true;
    }

    /**
     * Syntactic symbols.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static enum Symbol {

        SS_UNDEFINED,
        SS_OPEN_PAR, SS_CLOSE_PAR,
        SS_OPEN_SET, SS_CLOSE_SET,
        SS_COLON, SS_DASH, SS_EQUAL,
        SS_ID,
        SS_DEFINE, SS_DOMAIN, SS_PROBLEM,
        SS_REQUIREMENTS, SS_TYPES, SS_CONSTANTS,
        SS_PREDICATES, SS_FUNCTIONS, SS_MULTI_FUNCTIONS,
        SS_EITHER, SS_ACTION, SS_PREC, SS_EFF, SS_PARAMS,
        SS_AND, SS_NOT, SS_MEMBER,
        SS_ASSIGN, SS_ADD, SS_DEL,
        SS_OBJECTS, SS_SHARED_DATA,
        SS_INIT, SS_BELIEFS,
        SS_GLOBAL_GOAL, SS_GOAL, SS_CONSTRAINTS,
        SS_PREFERENCE, SS_METRIC, SS_MINIMIZE,
        SS_IS_VIOLATED, SS_BEHAVIOUR,
        SS_SELF_INTEREST, SS_METRIC_THRESHOLD,
        SS_PLUS, SS_MULT,
        SS_VAR, SS_HEAD, SS_BODY, SS_DEF_RULE,
        SS_ACTION_PREF, SS_NUMBER,
        SS_TOTAL_TIME,
        SS_INCREASE, SS_DIV,
        SS_CONGESTION, SS_VARIABLES, SS_USAGE, SS_PENALTY,
        SS_OR, SS_WHEN,
        SS_GREATER, SS_GREATER_EQ, SS_LESS, SS_LESS_EQ, SS_DISTINCT;

        // Names for the symbols
        private static final String sname[] = {"undefined", "(", ")",
            "{", "}", ":", "-", "=", "identifier", "define", "domain",
            "problem", "requirements", "types", "constants",
            "predicates", "functions", "multi-functions", "either", "action",
            "precondition", "effect", "parameters", "and", "not", "member",
            "assign", "add", "del", "objects", "shared-data", "init",
            "beliefs", "global-goal", "goal", "constraints",
            "preference", "metric", "minimize", "is-violated", "behaviour",
            "self-interest", "metric-threshold", "+", "*",
            "variable", "head", "body", "def-rule", "action-preferences",
            "number", "total-time", "increase", "/", "congestion",
            "variables", "usage", "penalty", "or", "when",
            ">", ">=", "<", "<=", "!="};

        /**
         * Gets a description of the syntactic symbol.
         *
         * @param sym	Symbol
         * @return Symbol description
         * @since 1.0
         */
        public static String getName(Symbol sym) {
            return sname[sym.ordinal()];
        }
    }

    /**
     * Syntactic tokens.
     *
     * @author Oscar Sapena
     * @author Alejandro Torreno
     * @version %I%, %G%
     * @since 1.0
     */
    public static class Token {

        // Syntactic symbol
        private Symbol symbol;
        // Token description, also in lower case
        private String desc;
        private String descLower;

        /**
         * Constructor: creates an undefined token.
         *
         * @since 1.0
         */
        public Token() {
            symbol = Symbol.SS_UNDEFINED;
            desc = descLower = "";
        }

        /**
         * Checks if this token is of the expected type
         *
         * @param sym	Expected symbol
         * @return <code>true</code>, if this token if of the expected type;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        public boolean isSym(Symbol sym) {
            if (symbol.equals(sym)) {
                return true;
            }
            return descLower.equals(Symbol.getName(sym));
        }

        /**
         * Checks if the token is undefined.
         *
         * @return <code>true</code>, if the token is undefined;
         * <code>false</code>, otherwise
         * @since 1.0
         */
        public boolean undefined() {
            return symbol == Symbol.SS_UNDEFINED;
        }

        /**
         * Changes the symbol.
         *
         * @param s Syntactic symbol
         * @param desc	Token description
         * @since 1.0
         */
        public void set(Symbol s, String desc) {
            symbol = s;
            this.desc = desc;
            descLower = desc.toLowerCase();
        }

        /**
         * Returns the token symbol.
         *
         * @return Symbol of the token
         * @since 1.0
         */
        public Symbol getSym() {
            return symbol;
        }

        /**
         * Returns the token description.
         *
         * @return Description of the token
         * @since 1.0
         */
        public String getDesc() {
            return desc;
        }

        /**
         * Returns the lower case token description.
         *
         * @return Description of the token in lower case
         * @since 1.0
         */
        public String getDescLower() {
            return descLower;
        }
    }
}
