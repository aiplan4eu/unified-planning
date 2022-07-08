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
package org.agreement_technologies.common.map_grounding;

/**
 * Grounded numeric expression to define numeric action effects.
 * 
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0 
 */
public interface GroundedNumericExpression {
    
    // Expression types
    static final int NUMBER     = 0;
    static final int VARIABLE   = 1; 
    static final int ADD        = 2;
    static final int DEL        = 3;
    static final int PROD       = 4;
    static final int DIV        = 5;
    static final int USAGE      = 6;
    
    /**
     * Returns the expression type.
     * 
     * @return Expression type
     * @since 1.0 
     */
    int getType();
    
    /**
     * If type == NUMBER, returns the numeric value.
     * 
     * @return Numeric value
     * @since 1.0 
     */
    double getValue();      
        
    /**
     * If type == VARIABLE, returns the grounded variable.
     * 
     * @return Grounded variable
     * @since 1.0 
     */
    GroundedVar getVariable();  
    
    /**
     * If type == ADD, DEL, PROD or DIV, retuns the left operand.
     * 
     * @return Left operand of the expression
     * @since 1.0 
     */
    GroundedNumericExpression getLeftOperand(); 
    
    /**
     * If type == ADD, DEL, PROD or DIV, retuns the right operand.
     * 
     * @return Right operand of the expression
     * @since 1.0 
     */
    GroundedNumericExpression getRightOperand(); 
    
}
