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
package org.agreement_technologies.common.map_landmarks;

import java.util.ArrayList;
import org.agreement_technologies.common.map_grounding.GroundedVar;

/**
 * LandmarkFluent interface provides the necessary methods to work with fluents,
 * i.e. (variable, value), in the landmarks graph.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface LandmarkFluent {

    /**
     * Gets the variable associated to the landmark fluent.
     *
     * @return Grounded variable
     * @since 1.0
     */
    GroundedVar getVar();

    /**
     * Gets the name of the variable associated to the landmark fluent.
     *
     * @return Variable name
     * @since 1.0
     */
    String getVarName();

    /**
     * Gets value assigned to the variable of the landmark fluent.
     *
     * @return Value of the variable that defines the landmark fluent
     * @since 1.0
     */
    String getValue();

    /**
     * Gets agents that are aware of the landmark fluent.
     *
     * @return Arraylist of agent identifiers
     * @since 1.0
     */
    ArrayList<String> getAgents();

    /**
     * Gets index of the landmark fluent.
     *
     * @return Landmark fluent index
     * @since 1.0
     */
    int getIndex();

    /**
     * Gets producer actions of the fluent, even if they come after the fluent
     * in the RPG.
     *
     * @return Arraylist of producer actions
     * @since 1.0
     */
    ArrayList<LandmarkAction> getTotalProducers();

    /**
     * Gets producer actions that come before the fluent in the RPG.
     *
     * @return Arraylist of producer actions
     * @since 1.0
     */
    ArrayList<LandmarkAction> getProducers();

    /**
     * Gets level of the landmark fluent in the RPG.
     *
     * @return Fluent level in the RPG
     * @since 1.0
     */
    int getLevel();

    /**
     * Verifies if the landmark fluent is a task goal.
     *
     * @return <code>true</code>, if the fluent is a goal; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    boolean isGoal();

}
