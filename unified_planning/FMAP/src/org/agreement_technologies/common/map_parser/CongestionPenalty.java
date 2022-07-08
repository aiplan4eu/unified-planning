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
 * CongestionPenalty interface provides methods to deal with congestion
 * penalties.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface CongestionPenalty {

    // Condition types
    public static final int EQUAL = 0;
    public static final int GREATER = 1;
    public static final int GREATER_EQ = 2;
    public static final int LESS = 3;
    public static final int LESS_EQ = 4;
    public static final int DISTINCT = 5;

    /**
     * Gets the condition type.
     * 
     * @return Condition type
     * @since 1.0
     */
    public int getConditionType();

    /**
     * Gets the fluent for the condition.
     * 
     * @return Condition fluent
     * @since 1.0
     */
    public CongestionFluent getIncVariable();

    /**
     * Gets the condition value.
     * 
     * @return Condition value
     * @since 1.0
     */
    public double getConditionValue();

    /**
     * Gest the numeric expression for this condition.
     * 
     * @return Numeric expression
     * @since 1.0
     */
    public NumericExpression getIncExpression();

}
