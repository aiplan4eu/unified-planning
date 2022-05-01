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
 * NumericExpression interface provides methods to deal with numeric
 * expressions.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface NumericExpression {

    // Numeric expression types
    static final int NUMBER = 0;
    static final int VARIABLE = 1;
    static final int ADD = 2;
    static final int DEL = 3;
    static final int PROD = 4;
    static final int DIV = 5;
    static final int USAGE = 6;

    /**
     * Gets the numeric expression type.
     * 
     * @return Numeric expression type
     * @since 1.0
     */
    public int getType();

    /**
     * Gets the numeric constant value (only if type == NUMBER).
     * 
     * @return Numeric constant value 
     * @since 1.0
     */
    public double getValue();

    /**
     * Gets the numeric function (only if type == VARIABLE).
     * 
     * @return Numeric function
     * @since 1.0
     */
    public Function getNumericVariable();

    /**
     * Gets the left operand (only if type == ADD, DEL, PROD, or DIV).
     * 
     * @return Left operand of this expression
     * @since 1.0
     */
    public NumericExpression getLeftExp();

    /**
     * Gets the right operand (only if type == ADD, DEL, PROD, or DIV).
     * 
     * @return Right operand of this expression
     * @since 1.0
     */
    public NumericExpression getRightExp();

    /**
     * Gets the congestion fluent (only if type == USAGE).
     * 
     * @return Congestion fluent 
     * @since 1.0
     */
    public CongestionFluent getCongestionFluent();

}
