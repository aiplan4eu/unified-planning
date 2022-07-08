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
 * CongestionFluent interface provides methods to deal with congestion fluents.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface CongestionFluent {

    /**
     * Gets the fluent name.
     *
     * @return Fluent name
     * @since 1.0
     */
    public String getName();

    /**
     * Gets the number of parameters in the fluent.
     *
     * @return Number of parameters
     * @since 1.0
     */
    public int getNumParams();

    /**
     * Gets the name of a parameter.
     *
     * @param index Parameter index (0 <= index < getNumParams())
     * @return Name of the parameter
     * @since 1.0
     */
    public String getParamName(int index);

}
