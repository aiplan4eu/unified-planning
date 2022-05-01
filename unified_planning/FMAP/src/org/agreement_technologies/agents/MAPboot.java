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
package org.agreement_technologies.agents;

import java.io.IOException;
import java.text.ParseException;
import java.util.ArrayList;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_heuristic.HeuristicFactory;
import org.agreement_technologies.common.map_parser.AgentList;
import org.agreement_technologies.common.map_parser.PDDLParser;
import org.agreement_technologies.common.map_planner.PlannerFactory;
import org.agreement_technologies.service.map_parser.MAPDDLParserImp;
import org.agreement_technologies.service.map_parser.ParserImp;

/**
 * MAPboot is the main class of this project (FMAP). It is the Multi-Agent
 * Planning Process launcher.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class MAPboot {

    // Set of planning agents
    public static ArrayList<PlanningAgent> planningAgents;

    /**
     * Main method.
     *
     * @param args Command line parameters
     * @since 1.0
     */
    public static void main(String args[]) {
        planningAgents = new ArrayList<>();
        Runtime rt = Runtime.getRuntime();
        rt.addShutdownHook(new Thread() {
            @Override
            public void run() {
                shutdown();
            }
        ;
        });
        if (args.length == 0) // Graphical interface if no parameters are given
        {
            launchGUI();
        } else {
            launchCommandLine(args);    // Command-line start
        }
    }

    /**
     * Creates and shows the graphical interface.
     *
     * @since 1.0
     */
    private static void launchGUI() {
        java.awt.EventQueue.invokeLater(new Runnable() {
            @Override
            public void run() {
                new GUIBoot().setVisible(true);
            }
        });
    }

    /**
     * Non-graphical start. This method reads the command-line paremeters
     * (<code>[<agent-name> <domain> <problem>]+ <agent_list></code>) and
     * launches the agents.
     *
     * @param args Command-line parameters
     * @since 1.0
     */
    private static void launchCommandLine(String[] args) {
        int searchType = PlannerFactory.getDefaultSearchMethod();
        int heuristic = HeuristicFactory.LAND_DTG_NORM;
        boolean ok = true;
        ArrayList<String> mandatoryArgs = new ArrayList<>();
        int i = 0;
        while (ok && i < args.length) {
            String arg = args[i].trim().toLowerCase();
            if (arg.equals("-help")) {  // Help
                ok = false;
            } else if (arg.equals("-s")) { // Search type
                searchType = getSearchType(args, ++i);
                ok = searchType != -1;
                i++;
            } else if (arg.equals("-h")) {  // Heuristic function
                heuristic = getHeuristicFunction(args, ++i);
                ok = heuristic != -1;
                i++;
            } else {
                mandatoryArgs.add(args[i++]);
            }
        }
        if (!ok || mandatoryArgs.size() < 3) {  // Lack of parameters, error or -help
            printUsage();
            return;
        }
        if (!PlannerFactory.checkSearchConstraints(searchType, heuristic)) {
            System.out.println("Error: the search method and the heuristic function are not compatible");
            return;
        }
        if (mandatoryArgs.size() <= 4) {        // Single agent
            String agentFile = mandatoryArgs.size() == 4 ? mandatoryArgs.get(3) : null;
            launchAgent(mandatoryArgs.get(0), mandatoryArgs.get(1), mandatoryArgs.get(2), 
                    agentFile, searchType, heuristic);
        } else {                                // Several agents at once
             if (HeuristicFactory.getHeuristicInfo(heuristic, HeuristicFactory.INFO_DISTRIBUTED).equals("no")) {
                System.out.println("The selected heuristic function is not available for multi-agent tasks");
                return;
            }
            AgentList agList;
            int last = mandatoryArgs.size() - 1;
            PDDLParser p = new MAPDDLParserImp();
            try {
                switch (mandatoryArgs.size() % 3) {
                    case 0:
                        // No agents file
                        agList = p.createEmptyAgentList();
                        for (int n = 0; n < last; n += 3) {
                            agList.addAgent(mandatoryArgs.get(n).toLowerCase(), "127.0.0.1");
                        }
                        break;
                    case 1:
                        // Agents file
                        agList = p.parseAgentList(mandatoryArgs.get(last));
                        break;
                    default:
                        printUsage();
                        return;
                }
                int n = 0;
                while (n < last) {
                    PlanningAgent ag = new PlanningAgent(mandatoryArgs.get(n).toLowerCase(), 
                            mandatoryArgs.get(n + 1), mandatoryArgs.get(n + 2),
                            agList, false, GroundedTask.SAME_OBJECTS_REP_PARAMS, false,
                            heuristic, searchType);
                    planningAgents.add(ag);
                    n += 3;
                }
                for (PlanningAgent ag : planningAgents) {
                    ag.start();
                }
            } catch (ParseException ex) {
                System.out.println(ex.getMessage() + ", at line " + ex.getErrorOffset() + " (" + args[last] + ")");
            } catch (IOException ex) {
                System.out.println("Read error: " + ex.getMessage() + " (" + args[last] + ")");
            } catch (Exception ex) {
                System.out.println("Error  " + ex.getMessage());
            }
        }
    }

    /**
     * Prints the correct ussage of the command-line parameters.
     *
     * @since 1.0
     */
    private static void printUsage() {
        System.out.println("Invalid number of parameters.");
        System.out.println("Usage:");
        System.out.println("  java -jar FMAP.jar [<agent-name> <domain-file> <problem-file>]+ <agent-list-file>");
        System.out.println("Optional parameters:");
        System.out.println("  -s N\t\tChooses the search method. Valid values of N are:");
        for (int i = 0; i < PlannerFactory.SEARCH_METHODS.length; i++) {
            System.out.println("\t\t\t" + i + ": " + PlannerFactory.SEARCH_METHODS[i] +
                    (i == PlannerFactory.getDefaultSearchMethod() ? " -> default" : ""));
        }
        System.out.println("  -h N\t\tChooses the heuristic function. Valid values of N are:");
        for (int i = 0; i < HeuristicFactory.HEURISTICS.length; i++) {
            System.out.println("\t\t\t" + i + ": " + HeuristicFactory.HEURISTICS[i] +
                    (i == HeuristicFactory.LAND_DTG_NORM ? " -> default" : ""));
        }
        System.out.println("  -help\t\tDisplays this help and exits");
        
    }

    /**
     * Launches a planning agent.
     *
     * @param agentName Name of the agent
     * @param domainFile Domain filename
     * @param problemFile Problem filename
     * @param agentsFile Agents filename
     * @param searchType Search type
     * @param heuristic Heuristic function
     * 
     * @since 1.0
     */
    private static void launchAgent(String agentName, String domainFile, String problemFile, 
            String agentsFile, int searchType, int heuristic) {
        try {
            boolean isMAPDDL = new ParserImp().isMAPDDL(domainFile);
            PDDLParser p = isMAPDDL ? new MAPDDLParserImp() : new ParserImp();
            AgentList agList;
            if (agentsFile == null) {
                agList = p.createEmptyAgentList();
                agList.addAgent(agentName.toLowerCase(), "127.0.0.1");
            } else {
                agList = p.parseAgentList(agentsFile);
            }
            PlanningAgent ag = new PlanningAgent(agentName.toLowerCase(), domainFile,
                    problemFile, agList, true, GroundedTask.SAME_OBJECTS_REP_PARAMS,
                    false, heuristic, searchType);
            MAPboot.planningAgents.add(ag);
            ag.start();
        } catch (ParseException ex) {
            System.out.println(ex.getMessage() + ", at line " + ex.getErrorOffset() + " (" + agentsFile + ")");
        } catch (IOException ex) {
            System.out.println("Read error: " + ex.getMessage() + " (" + agentsFile + ")");
        } catch (Exception ex) {
            System.out.println("Error  " + ex.getMessage());
        }
    }

    /**
     * Stops the planning agents.
     * 
     * @since 1.0
     */
    public static void shutdown() {
        System.out.println("; Stopping...");
        for (PlanningAgent ag : planningAgents) {
            ag.shutdown();
        }
        planningAgents.clear();
    }

    /**
     * Reads the search method from the arguments
     * @param args Command-line arguments
     * @param n Number of argument
     * @return Search type (-1 if error)
     * 
     * @since 1.0
     */
    private static int getSearchType(String[] args, int n) {
        if (n >= args.length) return -1;
        try {
            int s = Integer.parseInt(args[n]);
            return s >= 0 && s < PlannerFactory.SEARCH_METHODS.length ? s : -1;
        } catch (NumberFormatException e) {
            return -1;
        }
    }
    
    /**
     * Reads the heuristic function from the arguments
     * @param args Command-line arguments
     * @param n Number of argument
     * @return Heuristic function (-1 if error)
     * 
     * @since 1.0
     */
    private static int getHeuristicFunction(String[] args, int n) {
        if (n >= args.length) return -1;
        try {
            int h = Integer.parseInt(args[n]);
            return h >= 0 && h < HeuristicFactory.HEURISTICS.length ? h : -1;
        } catch (NumberFormatException e) {
            return -1;
        }
    }
}
