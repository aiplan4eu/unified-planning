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
package org.agreement_technologies.common.map_viewer;

import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import org.agreement_technologies.common.map_planner.Plan;
import org.agreement_technologies.common.map_planner.PlannerFactory;

/**
 * PlanViewer interface provides methods to display plans graphically.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface PlanViewer {

    /**
     * Sets the background color.
     * 
     * @param bgColor Background color
     * @since 1.0
     */
    void setBackground(Color bgColor);

    /**
     * Sets the preferred form size.
     * 
     * @param dimension Form dimension
     * @since 1.0
     */
    void setPreferredSize(Dimension dimension);

    /**
     * Gets the graphical component.
     * 
     * @return Graphical component
     * @since 1.0
     */
    Component getComponent();

    /**
     * Displays a given plan.
     * 
     * @param plan Plan to show
     * @param pf Planner factory
     * @since 1.0
     */
    void showPlan(Plan plan, PlannerFactory pf);

    /**
     * Gets the makespan of the plan that is being displayed.
     * 
     * @return Plan makespan
     * @since 1.0
     */
    int getMakespan();
}
