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
 * Fact interface provides methods to deal with ungrounded functions.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Function extends java.io.Serializable {

    /**
     * Retrieves the function name.
     *
     * @return Function name
     * @since 1.0
     */
    String getName();

    /**
     * Returns the function parameters.
     *
     * @return Array of the function parameters
     * @since 1.0
     */
    Parameter[] getParameters();

    /**
     * Returns the function co-domain.
     *
     * @return Array of type names of the function
     * @since 1.0
     */
    String[] getDomain();

    /**
     * Checks if this is a multi-function.
     *
     * @return <code>true</code>, if this one is a multi-function;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    boolean isMultifunction();

}
