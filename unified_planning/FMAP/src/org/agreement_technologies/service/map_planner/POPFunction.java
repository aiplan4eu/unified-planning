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

import org.agreement_technologies.common.map_grounding.GroundedVar;
import java.util.ArrayList;

/**
 * POPFunction class defines a POP variables.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPFunction {

    private final GroundedVar var;              // Original grounded variable
    private final String name;                  // Variable name
    private final ArrayList<String> params;     // Variable parameters
    private final ArrayList<String> types;      // List of types of this variable
    private final String initialTrueValue;      // Initial value of the variable
    private final ArrayList<String> initialFalseValues; // Values that the variable does not have in the initial state
    private final ArrayList<String> reachableValues;    // List of reachable values for this variable
    private String key;                         // Variable description

    /**
     * Creates a new POP variable.
     *
     * @param variable Original grounded variable
     * @since 1.0
     */
    public POPFunction(GroundedVar variable) {
        int i;
        this.key = null;
        this.var = variable;

        this.name = var.getFuctionName();
        this.initialTrueValue = var.initialTrueValue();

        this.params = new ArrayList<>(var.getParams().length);
        for (i = 0; i < var.getParams().length; i++) {
            this.params.add(var.getParams()[i]);
        }

        this.types = new ArrayList<>(var.getDomainTypes().length);
        for (i = 0; i < var.getDomainTypes().length; i++) {
            this.types.add(var.getDomainTypes()[i]);
        }

        this.initialFalseValues = new ArrayList<>(var.initialFalseValues().length);
        for (i = 0; i < var.initialFalseValues().length; i++) {
            this.initialFalseValues.add(var.initialFalseValues()[i]);
        }

        this.reachableValues = new ArrayList<>(var.getReachableValues().length);
        for (i = 0; i < var.getReachableValues().length; i++) {
            this.reachableValues.add(var.getReachableValues()[i]);
        }
    }

    /**
     * Gets the original grounded variable.
     *
     * @return Original grounded variable
     * @since 1.0
     */
    public GroundedVar getVariable() {
        return this.var;
    }

    /**
     * Gets the name of the variable.
     *
     * @return Name of the variable
     * @since 1.0
     */
    public String getName() {
        return this.name;
    }

    /**
     * Gets the list of variable parameters.
     *
     * @return List of variable parameters
     * @since 1.0
     */
    public ArrayList<String> getParams() {
        return this.params;
    }

    /**
     * Gets the list of types of the variable.
     *
     * @return List of types
     * @since 1.0
     */
    public ArrayList<String> getTypes() {
        return this.types;
    }

    /**
     * Gets the initial value of the variable.
     *
     * @return Initial value
     * @since 1.0
     */
    public String getInitialTrueValue() {
        return this.initialTrueValue;
    }

    /**
     * Gets the list of values that the variable does not have in the initial
     * state.
     *
     * @return List of values that the variable does not have in the initial
     * state
     * @since 1.0
     */
    public ArrayList<String> getInitialFalseValues() {
        return this.initialFalseValues;
    }

    /**
     * Gets the reachable values for this variable.
     * 
     * @return List of reachable values
     * @since 1.0
     */
    public ArrayList<String> getReachableValues() {
        return this.reachableValues;
    }

    /**
     * Gets a description of this variable.
     * 
     * @return Variable description
     * @since 1.0
     */
    public String toKey() {
        if (this.key == null) {
            key = name;
            for (String param : params) {
                key += " " + param;
            }
        }

        return this.key;
    }

    /**
     * Gets a description of this variable.
     * 
     * @return Variable description
     * @since 1.0
     */
    @Override
    public String toString() {
        String res = name;
        for (String param : params) {
            res += " " + param;
        }
        return res;
    }
    
}
