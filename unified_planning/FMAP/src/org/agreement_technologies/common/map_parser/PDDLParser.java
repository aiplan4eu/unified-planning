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

import java.io.IOException;
import java.text.ParseException;

/**
 * PDDLParser interface provides methods to parse PDDL files.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public interface PDDLParser {

    /**
     * Parses a PDDL domain file.
     *
     * @param domainFile Domain file name
     * @return Parsed task
     * @throws ParseException If a parse error is detected
     * @throws IOException If the file cannot be read
     * @since 1.0
     */
    Task parseDomain(String domainFile) throws ParseException, IOException;

    /**
     * Parses a PDDL problem file. Domain should have been parsed before.
     *
     * @param problemFile Problem file name
     * @param planningTask Parsed task
     * @param agList List of participating agents
     * @param agentName Name of this planning agent
     * @throws ParseException If a parse error is detected
     * @throws IOException If the file cannot be read
     * @since 1.0
     */
    void parseProblem(String problemFile, Task planningTask, AgentList agList, String agentName) throws ParseException, IOException;

    /**
     * Checks if the format of the input files is MAPDDL.
     *
     * @param domainFile Domain file name
     * @return <code>true</code>, if the input file is in MAPDDL format;
     * <code>false</code>, if it is the native FMAP-PDDL format.
     * @throws IOException If the file cannot be read
     * @since 1.0
     */
    boolean isMAPDDL(String domainFile) throws IOException;

    /**
     * Parses a file with the list of participating agents.
     * 
     * @param agentsFile Agents' file name
     * @return List of agents
     * @throws ParseException If a parse error is detected
     * @throws IOException If the file cannot be read
     * @since 1.0
     */
    AgentList parseAgentList(String agentsFile) throws ParseException, IOException;

    /**
     * Returns an empty agents list.
     * 
     * @return Empty agents list
     * @since 1.0
     */
    AgentList createEmptyAgentList();

}
