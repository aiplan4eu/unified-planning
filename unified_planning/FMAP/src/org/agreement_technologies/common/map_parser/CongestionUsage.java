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
 * CongestionUsage interface provides methods to deal with the usage section in
 * the congestion operators.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface CongestionUsage {

    // Usage type
    public static final int OR = 0;
    public static final int AND = 1;
    public static final int ACTION = 2;

    /**
     * Gets the usage type.
     *
     * @return Usage type
     * @since 1.0
     */
    public int getType();

    /**
     * Gets the number of terms, if this usage is composed of several terms,
     * i.e. if type == OR or type == AND.
     *
     * @return Number of terms
     * @since 1.0
     */
    public int numTerms();

    /**
     * Gets a given term by its index.
     * 
     * @param index Term index (0 <= index < numTerms())
     * @return The term with that index
     * @since 1.0
     */
    public CongestionUsage getTerm(int index);  

    /**
     * Gets the action name (only if type == ACTION).
     * 
     * @return Action name
     * @since 1.0
     */
    public String getActionName();  

    /**
     * Gets the number of parameters of the action.
     * 
     * @return Number of parameters of the action
     * @since 1.0
     */
    public int numActionParams();

    /**
     * Gets the name of an action parameter by its index.
     * 
     * @param paramNumber Parameter index (0 <= paramNumber < numActionParams())
     * @return Name of the action parameter
     * @since 1.0
     */
    public String getParamName(int paramNumber);    

}
