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
package org.agreement_technologies.common.map_heuristic;

import java.util.ArrayList;
import java.util.HashMap;
import org.agreement_technologies.common.map_planner.Plan;
import org.agreement_technologies.common.map_planner.PlannerFactory;
import org.agreement_technologies.common.map_planner.Step;

/**
 * HPlan interface provides the necessary methods in a plan to compute heuristic
 * values.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface HPlan extends Plan {

    /**
     * Gets the steps of the plan sorted in a topological order.
     *
     * @return Array of step indexes
     * @since 1.0
     */
    int[] linearization();

    /**
     * Computes the resulting frontier state after the plan execution. This
     * method is used in distributed problems.
     *
     * @param totalOrder Indexes of the plan steps sorted in a topological order
     * @param pf Planner factory
     * @return Frontier multi-state. It is a multi-state as this structure
     * allows to store several values for each variable
     * @since 1.0
     */
    HashMap<String, ArrayList<String>> computeMultiState(int totalOrder[], PlannerFactory pf);

    /**
     * Computes the resulting frontier state after the plan execution. This
     * method is used in centralized problems.
     *
     * @param totalOrder Indexes of the plan steps sorted in a topological order
     * @param pf Planner factory
     * @return Frontier state. In this structure only one value is stored for
     * each variable
     * @since 1.0
     */
    HashMap<String, String> computeState(int totalOrder[], PlannerFactory pf);

    /**
     * Computes the resulting frontier state after the plan execution. This
     * method is used in centralized problems, and works with indexes instead of
     * variables and values names.
     *
     * @param totalOrder Indexes of the plan steps sorted in a topological order
     * @param numVars Number of (non-numeric) variables in the state
     * @return State. For each variable, this array stores the index of its
     * value
     * @since 1.0
     */
    int[] computeCodeState(int totalOrder[], int numVars);

    /**
     * Gets the last step added to the plan.
     *
     * @return Last added step
     * @since 1.0
     */
    Step lastAddedStep();

}
