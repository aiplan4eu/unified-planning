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
 * Metric interface provides methods to deal with metric functions.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface Metric {

    // Metric types
    public static final int MT_PREFERENCE = 0;
    public static final int MT_ADD = 1;
    public static final int MT_MULT = 2;
    public static final int MT_NUMBER = 3;
    public static final int MT_TOTAL_TIME = 4;

    /**
     * Gets the metric type.
     * 
     * @return Metric type
     * @since 1.0
     */
    int getMetricType();

    /**
     * Gets the preference name (only if type == MT_PREFERENCE).
     * 
     * @return Preference name
     * @since 1.0
     */
    String getPreference();

    /**
     * Gets the numeric constant (only if type == MT_NUMBER).
     * 
     * @return Constant numeric value
     * @since 1.0
     */
    double getNumber();

    /** 
     * Gets the number of terms (only if type == MT_ADD or MT_MULT).
     * 
     * @return Number of terms
     * @since 1.0
     */
    int getNumTerms();

    /**
     * Gets a given term by its index.
     * 
     * @param index Term index (0 <= index < getNumTerms())
     * @return metric term
     * @since 1.0
     */
    Metric getTerm(int index);

}
