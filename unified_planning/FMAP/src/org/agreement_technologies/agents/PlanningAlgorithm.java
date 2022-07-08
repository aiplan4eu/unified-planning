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
import org.agreement_technologies.common.map_communication.AgentCommunication;
import org.agreement_technologies.common.map_communication.PlanningAgentListener;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.Grounding;
import org.agreement_technologies.common.map_heuristic.Heuristic;
import org.agreement_technologies.common.map_heuristic.HeuristicFactory;
import org.agreement_technologies.common.map_landmarks.Landmarks;
import org.agreement_technologies.common.map_parser.AgentList;
import org.agreement_technologies.common.map_parser.PDDLParser;
import org.agreement_technologies.common.map_parser.Task;
import org.agreement_technologies.common.map_planner.Plan;
import org.agreement_technologies.common.map_planner.Planner;
import org.agreement_technologies.common.map_planner.PlannerFactory;
import org.agreement_technologies.common.map_viewer.PlanViewer;
import org.agreement_technologies.service.map_communication.AgentCommunicationImp;
import org.agreement_technologies.service.map_grounding.GroundingImp;
import org.agreement_technologies.service.map_heuristic.HeuristicFactoryImp;
import org.agreement_technologies.service.map_parser.MAPDDLParserImp;
import org.agreement_technologies.service.map_parser.ParserImp;
import org.agreement_technologies.service.map_planner.PlannerFactoryImp;
import org.agreement_technologies.service.map_viewer.PlanViewerImp;
import org.agreement_technologies.service.tools.Redirect;

/**
 * PlanningAlgorithm class implements the distributed planning protocol.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class PlanningAlgorithm {

    // Possible planning statuses
    public static final int STATUS_STARTING = 0;
    public static final int STATUS_PARSING = 1;
    public static final int STATUS_GROUNDING = 2;
    public static final int STATUS_PLANNING = 3;
    public static final int STATUS_LANDMARKS = 4;
    public static final int STATUS_IDLE = 8;
    public static final int STATUS_ERROR = 9;
    public static final int STATUS_ARGUMENTATION = 10;
    protected static final String[] STATUS_DESC = {"starting", "parsing",
        "grounding", "planning", "landmarks", "undefined", "undefined",
        "undefined", "idle", "error", "arguing"};

    /**
     * Gets the status description.
     *
     * @param status Agent status
     * @return Status description
     * @since 1.0
     */
    public static String getStatusDesc(int status) {
        return STATUS_DESC[status];
    }

    protected String name;			// Agent name
    protected String domainFile;		// Domain filename
    protected String problemFile;		// Problem filename

    protected int status;			// Agent status (see constants above)
    protected int sameObjects;                  // Same-object filetring flag
    protected boolean traceOn;                  // Trace flag
    protected int heuristicType;                // Heuristic function

    protected AgentCommunication comm;          // Agent communication utility
    protected Task planningTask;		// Parsed planning task
    protected GroundedTask groundedTask;        // Grounded planning task
    protected Landmarks landmarks;		// Landmarks information

    protected PlannerFactory plannerFactory;    // Planner factory
    protected Planner planner;                  // Planner
    protected PlanningAgentListener paListener; // Planning agent listener
    protected Plan solutionPlan;                // Solution found flag
    protected long planningTime;                // Planning time in milliseconds
    protected int iterations;                   // Number of planning iterations
    protected int searchPerformance;            // Search performance type. See constants in PlannerFactory
    protected AgentList agList;                 // List of participating agents
    protected boolean waitSynch;                // Wait for synchronous start flag
    protected boolean negationByFailure;        // Flag required in LandmarksHeuristic class. Depends on the type of the PDDL used
    protected boolean isMAPDDL;                 // Flag that indicates if the input is given in MAPDDL format

    /**
     * Constructor of a planning agent.
     *
     * @param name Name of the agent
     * @param domainFile Domain filename
     * @param problemFile Problem filename
     * @param agList List of agents
     * @param waitSynch Wait for synchronized start flag
     * @param sameObjects Same-object filtering flag
     * @param traceOn Trace enabled flag
     * @param h Heuristic function
     * @param searchPerformance Search performance type
     * @throws Exception Error during the planning process
     * @since 1.0
     */
    public PlanningAlgorithm(String name, String domainFile, String problemFile, AgentList agList,
            boolean waitSynch, int sameObjects, boolean traceOn, int h, int searchPerformance)
            throws Exception {
        this.name = name.toLowerCase();
        this.comm = new AgentCommunicationImp(this.name, agList);
        this.waitSynch = waitSynch;
        this.agList = agList;
        this.plannerFactory = null;
        this.domainFile = domainFile;
        this.problemFile = problemFile;
        this.sameObjects = sameObjects;
        this.traceOn = traceOn;
        this.searchPerformance = searchPerformance;
        this.status = STATUS_STARTING;
        this.heuristicType = h;
        this.paListener = null;
        this.solutionPlan = null;
        this.landmarks = null;
        this.isMAPDDL = new ParserImp().isMAPDDL(domainFile);
        this.negationByFailure = this.isMAPDDL;
    }

    /**
     * Shows a trace message.
     *
     * @param indentLevel Indentation level
     * @param msg Message
     * @since 1.0
     */
    protected void trace(int indentLevel, String msg) {
        if (paListener != null) {
            paListener.trace(indentLevel, msg);
        }
    }

    /**
     * Changes the agent status.
     *
     * @param status New status
     * @since 1.0
     */
    protected void changeStatus(int status) {
        this.status = status;
        if (paListener != null) {
            paListener.statusChanged(this.status);
        }
    }

    /**
     * Notifies an error.
     *
     * @param msg Error message
     * @since 1.0
     */
    protected void notifyError(String msg) {
        changeStatus(STATUS_ERROR);
        if (paListener != null) {
            paListener.notyfyError(msg);
        } else {
            System.out.println(msg);
        }
    }

    /**
     * Execution code for the planning agent.
     *
     * @since 1.0
     */
    protected void execute() {
        if (waitSynch) {
            executeWithAsynchronousStart();
        } else {
            executeWithSynchronousStart();
        }
        if (comm != null) {
            comm.close();
        }
    }

    /**
     * Task parsing from PDDL files.
     *
     * @return Time used for parsing in milliseconds
     * @since 1.0
     */
    protected long parseTask() {
        changeStatus(STATUS_PARSING);
        long startTime = System.currentTimeMillis();
        planningTask = null;
        PDDLParser parser = isMAPDDL ? new MAPDDLParserImp() : new ParserImp();
        try {
            planningTask = parser.parseDomain(domainFile);
        } catch (ParseException e) {
            notifyError(e.getMessage() + ", at line " + e.getErrorOffset()
                    + " (" + domainFile + ")");
        } catch (IOException e) {
            notifyError("Read error: " + e.getMessage() + " (" + domainFile + ")");
        }
        if (status != STATUS_ERROR) {
            try {
                parser.parseProblem(problemFile, planningTask, agList, name);
            } catch (ParseException e) {
                notifyError(e.getMessage() + ", at line " + e.getErrorOffset()
                        + " (" + problemFile + ")");
            } catch (IOException e) {
                notifyError("Read error: " + e.getMessage() + " (" + problemFile + ")");
            }
        }
        long endTime = System.currentTimeMillis() - startTime;
        trace(0, "Parsing completed in " + endTime + "ms.");
        return endTime;
    }

    /**
     * Task grounding from the parsed task.
     *
     * @return Time in milliseconds used for grounding
     * @throws java.io.IOException Error detected in the input files
     * @since 1.0
     */
    protected long groundTask() throws IOException {
        if (status == STATUS_ERROR) {
            return 0;
        }
        changeStatus(STATUS_GROUNDING);
        long startTime = System.currentTimeMillis();
        Grounding g = new GroundingImp(sameObjects);
        g.computeStaticFunctions(planningTask, comm);
        groundedTask = g.ground(planningTask, comm, negationByFailure);
        groundedTask.optimize();
        long endTime = System.currentTimeMillis() - startTime;
        trace(0, "Grounding completed in " + endTime + "ms. ("
                + comm.getNumMessages() + " messages, " + groundedTask.getActions().size()
                + " actions)");
        return endTime;
    }

    /**
     * Planning stage.
     *
     * @return Time in milliseconds used for planning.
     * @since 1.0
     */
    protected long planningStage() {
        boolean usesLandmarks;
        if (status == STATUS_ERROR) {
            return 0;
        }
        PlanningAgentListener al = traceOn ? paListener : null;
        plannerFactory = new PlannerFactoryImp(groundedTask, comm);
        HeuristicFactory hf = new HeuristicFactoryImp();
        usesLandmarks = hf.getHeuristicInfo(heuristicType, HeuristicFactory.INFO_USES_LANDMARKS).equals("yes");
        if (usesLandmarks) {
            changeStatus(STATUS_LANDMARKS);
        }
        Heuristic heuristic = hf.getHeuristic(heuristicType, comm, groundedTask, plannerFactory);
        landmarks = usesLandmarks ? (Landmarks) heuristic.getInformation(Heuristic.INFO_LANDMARKS) : null;
        changeStatus(STATUS_PLANNING);
        planner = plannerFactory.createPlanner(groundedTask, heuristic, comm, al, searchPerformance);
        long startTime = System.currentTimeMillis();
        solutionPlan = planner.computePlan(startTime);
        long endTime = System.currentTimeMillis() - startTime;
        trace(0, String.format("Planning completed in %.3f sec.", endTime / 1000.0));
        trace(0, "Used memory: " + (Runtime.getRuntime().totalMemory() / 1024) + "kb.");
        if (solutionPlan != null) {
            trace(0, "Plan length: " + (solutionPlan.countSteps()));
            if (!traceOn && paListener != null) {
                paListener.showPlan(solutionPlan, plannerFactory);
            }
        }
        iterations = planner.getIterations();
        return endTime;
    }

    /**
     * Checks if a solution has been found.
     *
     * @return <code>true</code> if a solution has been found;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean solutionFound() {
        return solutionPlan != null;
    }

    /**
     * Returns the metric value of the solution plan.
     *
     * @return Metric value of the solution plan
     * @since 1.0
     */
    public double getSolutionMetric() {
        return solutionPlan.getMetric();
    }

    /**
     * Returns the name of steps (actions) in the solution plan.
     *
     * @return Number of steps in the solution plan
     * @since 1.0
     */
    public int getSolutionLength() {
        return solutionPlan.numSteps() - 2;
    }

    /**
     * Returns the makespan of the solution plan.
     *
     * @return Makespan of the solution plan
     * @since 1.0
     */
    public int getSolutionMakespan() {
        PlanViewer pv = new PlanViewerImp();
        pv.showPlan(solutionPlan, plannerFactory);
        return pv.getMakespan() - 2;
    }

    /**
     * Returns the planning time in seconds.
     *
     * @return Planning time in seconds
     * @since 1.0
     */
    public double getPlanningTime() {
        return planningTime / 1000.0;
    }

    /**
     * Returns the number of planning iterations.
     *
     * @return Number of iterations
     * @since 1.0
     */
    public int getIterations() {
        return iterations;
    }

    /**
     * Executes the agents. Using this method, waiting for the rest of the
     * agents is not needed as all the agents start at the same time.
     *
     * @since 1.0
     */
    private void executeWithSynchronousStart() {
        try {
            long totalTime;
            totalTime = parseTask();            // Task parsing from PDDL files
            totalTime += groundTask();          // Task grounding from the parsed task
            planningTime = planningStage();	// Planning stage
            totalTime += planningTime;
            if (status != STATUS_ERROR) {
                changeStatus(STATUS_IDLE);
                trace(0, "Number of messages: " + comm.getNumMessages());
                trace(0, String.format("Total time: %.3f sec.", totalTime / 1000.0));
            }
        } catch (Throwable e) {
            String error = e.toString() + "\n";
            java.io.StringWriter sw = new java.io.StringWriter();
            java.io.PrintWriter pw = new java.io.PrintWriter(sw);
            e.printStackTrace(pw);
            notifyError(error + sw.toString());
        }
    }

    /**
     * Executes the agents. Using this method, it is necessary to wait for the
     * rest of agents to start, as they do not start at the same time.
     *
     * @since 1.0
     */
    private void executeWithAsynchronousStart() {
        try {
            parseTask();
            if (waitSynch) {
                waitSynchronization();
            }
            planningTime = maPDDLGroundTask();
            planningTime += planningStage();
            showResult();
        } catch (Throwable e) {
            String error = e.toString() + "\n";
            java.io.StringWriter sw = new java.io.StringWriter();
            java.io.PrintWriter pw = new java.io.PrintWriter(sw);
            e.printStackTrace(pw);
            System.out.println(error + sw.toString());
        }
    }

    /**
     * Waits for the rest of agents to start.
     *
     * @since 1.0
     */
    private void waitSynchronization() {
        System.out.println("; Waiting to start");
        ArrayList<String> agentNames = comm.getAgentList();
        boolean registered[] = new boolean[comm.numAgents()];
        registered[comm.getThisAgentIndex()] = true;
        int activeAgents = 1;
        Redirect red = Redirect.captureOutput();
        do {
            for (int i = 0; i < comm.numAgents(); i++) {
                if (!registered[i]) {
                    if (comm.registeredAgent(agentNames.get(i))) {
                        registered[i] = true;
                        activeAgents++;
                    }
                }
            }
        } while (activeAgents < comm.numAgents());
        red.releaseOutput();
    }

    /**
     * Task grounding from the parsed task. This method is similar to
     * "groundTask", but some changes are necessary when the input files are
     * given in MAPDDL format.
     *
     * @return Time in milliseconds used for grounding
     * @since 1.0
     */
    private long maPDDLGroundTask() {
        if (status == STATUS_ERROR) {
            return 0;
        }
        long startTime = System.currentTimeMillis();
        Grounding g = new GroundingImp(sameObjects);
        g.computeStaticFunctions(planningTask, comm);
        groundedTask = g.ground(planningTask, comm, negationByFailure);
        groundedTask.optimize();
        long endTime = System.currentTimeMillis() - startTime;
        System.out.println("; Grounding time: " + String.format("%.3f sec.", endTime / 1000.0));
        return endTime;
    }

    /**
     * Displays the result of the planning search.
     * 
     * @since 1.0
     */
    private void showResult() {
        System.out.println("; Planning time: " + String.format("%.3f sec.", planningTime / 1000.0));
        if (solutionPlan != null) {
            System.out.println("; Plan length: " + (solutionPlan.countSteps()));
            solutionPlan.printPlan(Plan.CoDMAP_CENTRALIZED, comm.getThisAgentName(), comm.getAgentList());
        } else {
            System.out.println("; No plan found");
        }
    }
}
