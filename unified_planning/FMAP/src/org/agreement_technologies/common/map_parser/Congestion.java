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
package org.agreement_technologies.common.map_parser;

/**
 * Congestion interface provides methods to deal with congestion operators.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Congestion {

    /**
     * Gets the name of the congestion operator.
     *
     * @return Name of the congestion operator
     * @since 1.0
     */
    public String getName();

    /**
     * Gets the number of parameters of the congestion operator.
     *
     * @return Number of parameters of the congestion operator
     * @since 1.0
     */
    public int getNumParams();

    /**
     * Gets the list of types of a given parameter.
     *
     * @param paramNumber Parameter index (0 <= paramNumber < getNumParams())
     * @return List of types of the given parameter
     * @since 1.0
     */
    public String[] getParamTypes(int paramNumber);

    /**
     * Gets the name of the variables defined in the congestion operator.
     *
     * @return Array with the name of the variables defined in the congestion
     * operator
     * @since 1.0
     */
    public String[] getVariableNames();

    /**
     * Gets the list of types of a given parameter.
     *
     * @param varNumber Variable index (0 <= varNumber < getVariableNames().size()) 
     * @return List of types of the given variable
     * @since 1.0
     */
    public String[] getVarTypes(int varNumber);

    /**
     * Gets the usage section in the congestion operator.
     *
     * @return Usage section
     * @since 1.0
     */
    public CongestionUsage getUsage();

    /**
     * Gets the index of a parameter from its name.
     *
     * @param paramName Name of the parameter
     * @return Parameter index
     * @since 1.0
     */
    public int getParamIndex(String paramName);

    /**
     * Gets the number of penalties.
     *
     * @return Number of penalties
     * @since 1.0
     */
    public int getNumPenalties();

    /**
     * Gets a penalty of the the congestion operator.
     *
     * @param index Penalty index (0 <= index < getNumPenalties()) 
     * @return Penalty of the the congestion operator
     * @since 1.0
     */
    public CongestionPenalty getPenalty(int index);

}
