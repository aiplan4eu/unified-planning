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

import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.GroundedVar;

/**
 * DTGSet interface represents a set of Domain Transition Graphs (one DTG per
 * variable).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface DTGSet {

    /**
     * Distributes the public DTGs information among the other agents.
     *
     * @param comm Agent communication
     * @param gTask Grounded task
     * @since 1.0
     */
    void distributeDTGs(AgentCommunication comm, GroundedTask gTask);

    /**
     * Returns the Domain Transition Graph for the given variable
     *
     * @param v Variable
     * @return DTG of the variable
     * @since 1.0
     */
    DTG getDTG(GroundedVar v);

    /**
     * Returns the Domain Transition Graph for the given variable
     *
     * @param varName Name of the variable
     * @return DTG of the variable
     * @since 1.0
     */
    DTG getDTG(String varName);

    /**
     * Clears the cache, which stores already computed paths for value
     * transitions.
     *
     * @param threadIndex Thread index (for multi-thread purposes)
     * @since 1.0
     */
    void clearCache(int threadIndex);
}
