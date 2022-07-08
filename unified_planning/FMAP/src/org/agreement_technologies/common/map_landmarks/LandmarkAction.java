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

/**
 * LandmarkAction interface provides the necessary methods to work with actions
 * in the landmarks graph.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface LandmarkAction {

    /**
     * Gets the action effects.
     *
     * @return List of effects
     * @since 1.0
     */
    ArrayList<LandmarkFluent> getEffects();

    /**
     * Gets action preconditions.
     *
     * @return List of preconditions
     * @since 1.0
     */
    ArrayList<LandmarkFluent> getPreconditions();

    /**
     * Gets level of the action in the RPG used to calculate landmarks.
     *
     * @return Action level in the RPG
     * @since 1.0
     */
    int getLevel();

    /**
     * Sets the level of the action in the RPG used to calculate landmarks.
     *
     * @param maxLevel Action level in the RPG
     * @since 1.0
     */
    void setLevel(int maxLevel);

    /**
     * Gets action name.
     *
     * @return Action name
     * @since 1.0
     */
    String getName();

}
