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
package org.agreement_technologies.common.map_planner;

import org.agreement_technologies.service.map_planner.POPFunction;

/**
 * Common interface for causal links (a causal link represents a step supporting
 * a precondition of another step).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface CausalLink extends Ordering {

    /**
     * Returns the precondition supported in the causal link.
     *
     * @return Precondition
     * @since 1.0
     */
    Condition getCondition();

    /**
     * Returns step 1 of the causal link 1 --cond--> 2.
     *
     * @return Step 1 of the causal link
     * @since 1.0
     */
    Step getStep1();

    /**
     * Returns step 2 of the causal link 1 --cond--> 2.
     *
     * @return Step 2 of the causal link
     * @since 1.0
     */
    Step getStep2();

    /**
     * Gets the supported function (wrapper of Condition).
     *
     * @return Supported function
     * @since 1.0
     */
    POPFunction getFunction();
}
