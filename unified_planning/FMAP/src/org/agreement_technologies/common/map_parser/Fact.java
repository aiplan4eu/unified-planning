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
 * Fact interface provides methods to deal with ungrounded facts.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Fact extends java.io.Serializable {

    /**
     * Gets the function name.
     *
     * @return Function name
     * @since 1.0
     */
    String getFunctionName();

    /**
     * Returns the function parameters.
     *
     * @return Array of parameter names
     * @since 1.0
     */
    String[] getParameters();

    /**
     * Returns the list of values assigned to the function.
     *
     * @return Array of values assigned to the function
     * @since 1.0
     */
    String[] getValues();

    /**
     * Checks whether the assignment is negated.
     *
     * @return <code>true</code>, if the assignment is negated (not);
     * <code>false</code>, otherwise
     * @since 1.0
     */
    boolean negated();

}
