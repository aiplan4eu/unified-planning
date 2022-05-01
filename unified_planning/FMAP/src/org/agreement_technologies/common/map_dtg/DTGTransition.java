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
package org.agreement_technologies.common.map_dtg;

import java.util.ArrayList;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedEff;
import org.agreement_technologies.common.map_grounding.GroundedVar;

/**
 * DTGTransition interface represents a transition between values of a variable.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface DTGTransition {

    /**
     * Gets the variable of this transition.
     *
     * @return Variable of the transition
     * @since 1.0
     */
    GroundedVar getVar();

    /**
     * Gets the initial value for the variable in this transition.
     *
     * @return Initial value
     * @since 1.0
     */
    String getStartValue();

    /**
     * Gets the fnial value for the variable in this transition.
     *
     * @return Final value
     * @since 1.0
     */
    String getFinalValue();

    /**
     * Gets a list of the common preconditions to all the actions that produce
     * this transition.
     *
     * @return List of common preconditions
     * @since 1.0
     */
    ArrayList<GroundedCond> getCommonPreconditions();

    /**
     * Gets a list of the common effects to all the actions that produce this
     * transition.
     *
     * @return List of common effects
     * @since 1.0
     */
    ArrayList<GroundedEff> getCommonEffects();

    /**
     * Gets a list of the agents that can cause this transition.
     *
     * @return List of agents that can cause this transition
     * @since 1.0
     */
    ArrayList<String> getAgents();
}
