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
 * Grounded belief rule
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface GroundedRule extends java.io.Serializable {

    /**
     * Returns the rule name
     *
     * @return Name of the rule
     * @since 1.0
     */
    String getRuleName();

    /**
     * Returns the list of parameters (list of objects)
     *
     * @return List of parameters
     * @since 1.0
     */
    String[] getParams();

    /**
     * Returns the body of the rule
     *
     * @return Array of grounded conditions
     * @since 1.0
     */
    GroundedCond[] getBody();

    /**
     * Returns the head of the rule
     *
     * @return Array of grounded effects
     * @since 1.0
     */
    GroundedEff[] getHead();

}
