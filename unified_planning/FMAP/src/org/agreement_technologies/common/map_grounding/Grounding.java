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

import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_parser.Task;

/**
 * Planning task grounding.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Grounding {

    /**
     * Computes the list of static functions, i.e. functions whose values do not
     * change due to the action effects.
     *
     * @param task Planning task
     * @param comm Communication utility
     * @since 1.0
     */
    void computeStaticFunctions(Task task, AgentCommunication comm);

    /**
     * Grounds a planning task.
     *
     * @param task Planning task
     * @param comm Communication utility
     * @param negationByFailure <code>true</code> if the used model is negation
     * by failure; <code>false</code> if it is unknown by failure
     * @return Grounded task
     * @since 1.0
     */
    GroundedTask ground(Task task, AgentCommunication comm, boolean negationByFailure);

}
