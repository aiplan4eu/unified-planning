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
 * Condition interface represents an ungrounded condition.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Condition {

    // Condition type
    static final int EQUAL = 0;
    static final int DISTINCT = 1;
    static final int MEMBER = 2;
    static final int NOT_MEMBER = 3;
    static final int ASSIGN = 4;
    static final int ADD = 5;
    static final int DEL = 6;

    /**
     * Returns the condition type.
     * 
     * @return Condition type
     * @since 1.0
     */
    int getType();

    /**
     * Returns the condition function.
     
     * @return Function in the condition
     * @since 1.0
     */
    Function getFunction();

    /**
     * Returns the condition value.
     * 
     * @return Value of the condition
     * @since 1.0
     */
    String getValue();

}
