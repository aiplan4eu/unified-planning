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

import static java.awt.Frame.ICONIFIED;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Scanner;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_heuristic.HeuristicFactory;
import org.agreement_technologies.common.map_parser.AgentList;
import org.agreement_technologies.common.map_planner.PlannerFactory;
import org.agreement_technologies.service.map_parser.ParserImp;

/**
 * GUIBoot is the class that implements the graphical interface that allow to
 * launch the planning agents and monitorize the search process. This GUI does
 * not allow to launch agents in different computers; for this purpose, see the
 * MAPboot launcher.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class GUIBoot extends JFrame {

    // Version number for serialization
    private static final long serialVersionUID = -5039304283931395812L;
    // Start folder for selecting files
    private String startDir;

    // Variables declaration
    private javax.swing.JButton jButtonAddAgent;
    private javax.swing.JButton jButtonClearAgents;
    private javax.swing.JButton jButtonLoadConfig;
    private javax.swing.JButton jButtonLoadDomain;
    private javax.swing.JButton jButtonLoadProblem;
    private javax.swing.JButton jButtonSaveConfig;
    private javax.swing.JButton jButtonStart;
    @SuppressWarnings("rawtypes")
    private javax.swing.JList jListAgents;
    private javax.swing.JPanel jPanel;
    private javax.swing.JScrollPane jScrollPane1;
    private javax.swing.JTextField jTextFieldAgent;
    private javax.swing.JTextField jTextFieldDomain;
    private javax.swing.JTextField jTextFieldProblem;
    @SuppressWarnings("rawtypes")
    private javax.swing.JComboBox searchMethod;
    private javax.swing.JComboBox heuristicType;
    private javax.swing.JCheckBox sameObjects;
    private javax.swing.JCheckBox trace;

    /**
     * Constructor. Creates the GUI for launching agents.
     *
     * @since 1.0
     */
    public GUIBoot() {
        startDir = null;    // Retrieve the last start folder
        try {
            Scanner f = new Scanner(new File("configuration/startDir.txt"));
            startDir = f.nextLine();
            f.close();
        } catch (FileNotFoundException e) {
        }
        try {
            if (startDir == null) {
                startDir = new java.io.File(".").getCanonicalPath();
            }
        } catch (IOException e) {
            startDir = "";
        }
        initComponents();   // Initialize the graphical components
        setSize(648, 380);
        setLocationRelativeTo(null);
    }

    /**
     * Saves the start folder in the configuration file.
     *
     * @since 1.0
     */
    public void saveStartDir() {
        FileWriter outFile;
        try {
            outFile = new FileWriter("configuration/startDir.txt");
            PrintWriter out = new PrintWriter(outFile);
            out.println(startDir);
            out.close();
        } catch (IOException e) {
        }
    }

    /**
     * This method is called from within the constructor to initialize the form.
     *
     * @since 1.0
     */
    @SuppressWarnings({"rawtypes", "unchecked"})
    private void initComponents() {
        javax.swing.JLabel jLabelAgentName = new javax.swing.JLabel();     // Create the components
        jTextFieldAgent = new javax.swing.JTextField();
        javax.swing.JLabel jLabelDomain = new javax.swing.JLabel();
        jTextFieldDomain = new javax.swing.JTextField();
        javax.swing.JLabel jLabelProblem = new javax.swing.JLabel();
        jTextFieldProblem = new javax.swing.JTextField();
        jButtonLoadDomain = new javax.swing.JButton();
        jButtonLoadProblem = new javax.swing.JButton();
        jPanel = new javax.swing.JPanel();
        jButtonClearAgents = new javax.swing.JButton();
        jScrollPane1 = new javax.swing.JScrollPane();
        jListAgents = new javax.swing.JList();
        jButtonAddAgent = new javax.swing.JButton();
        jButtonLoadConfig = new javax.swing.JButton();
        jButtonSaveConfig = new javax.swing.JButton();
        jButtonStart = new javax.swing.JButton();
        // Initialize the form
        setDefaultCloseOperation(javax.swing.WindowConstants.EXIT_ON_CLOSE);
        setTitle("FMAP - Multi-Agent Planning");
        setResizable(false);
        getContentPane().setLayout(null);

        int posY = 20;
        jLabelAgentName.setText("Agent's name:");       // Edit box for the agent's name
        getContentPane().add(jLabelAgentName);
        jLabelAgentName.setBounds(20, posY, 120, 14);
        getContentPane().add(jTextFieldAgent);
        jTextFieldAgent.setBounds(140, posY, 130, 20);

        posY += 32;
        jLabelDomain.setText("Domain file:");        // Edit box for the domain-file name
        getContentPane().add(jLabelDomain);
        jLabelDomain.setBounds(20, posY, 110, 14);
        getContentPane().add(jTextFieldDomain);
        jTextFieldDomain.setBounds(140, posY, 408, 20);
        jButtonLoadDomain.setBounds(558, posY, 70, 20);

        posY += 24;
        jLabelProblem.setText("Problem file:");       // Edit box for the problem-file name
        getContentPane().add(jLabelProblem);
        jLabelProblem.setBounds(20, posY, 110, 14);
        getContentPane().add(jTextFieldProblem);
        jTextFieldProblem.setBounds(140, posY, 408, 20);
        jButtonLoadProblem.setBounds(558, posY, 70, 20);
        
        posY += 32;
        JLabel jLabelSearch = new JLabel("Search method:"); // Combo box for the search method
        getContentPane().add(jLabelSearch);
        jLabelSearch.setBounds(20, posY, 130, 16);
        searchMethod = new JComboBox(PlannerFactory.SEARCH_METHODS);
        searchMethod.setSelectedIndex(PlannerFactory.getDefaultSearchMethod());
        getContentPane().add(searchMethod);
        searchMethod.setBounds(140, posY, 170, 18);

        JLabel jLabelHeuristic = new JLabel("Heuristic function:"); // Combo box for the heuristic function
        getContentPane().add(jLabelHeuristic);
        jLabelHeuristic.setBounds(320, posY, 130, 16);
        heuristicType = new JComboBox(HeuristicFactory.HEURISTICS);
        heuristicType.setSelectedIndex(HeuristicFactory.LAND_DTG_NORM);
        getContentPane().add(heuristicType);
        heuristicType.setBounds(458, posY, 170, 18);

        jButtonLoadDomain.setText("Load");                  // Load domain button
        jButtonLoadDomain.setFocusable(false);
        jButtonLoadDomain.addActionListener(new java.awt.event.ActionListener() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButtonLoadDomainActionPerformed(evt);
            }
        });
        getContentPane().add(jButtonLoadDomain);
        
        jButtonLoadProblem.setText("Load");                 // Load problem button
        jButtonLoadProblem.setFocusable(false);
        jButtonLoadProblem.addActionListener(new java.awt.event.ActionListener() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButtonLoadProblemActionPerformed(evt);
            }
        });
        getContentPane().add(jButtonLoadProblem);
        
        // Middle panel
        jPanel.setBorder(javax.swing.BorderFactory.createBevelBorder(javax.swing.border.BevelBorder.RAISED));
        jPanel.setLayout(null);

        jButtonClearAgents.setText("Clear agents");         // Clear agent list button
        jButtonClearAgents.setFocusable(false);
        jButtonClearAgents.addActionListener(new java.awt.event.ActionListener() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButtonClearAgentsActionPerformed(evt);
            }
        });
        jPanel.add(jButtonClearAgents);
        jButtonClearAgents.setBounds(10, 40, 130, 23);

        jListAgents.setModel(new javax.swing.DefaultListModel());   // List of agents
        jListAgents.setFocusable(false);
        jScrollPane1.setViewportView(jListAgents);
        jPanel.add(jScrollPane1);
        jScrollPane1.setBounds(160, 10, 448, 130);

        jButtonAddAgent.setText("Add agent");               // Button to add agents
        jButtonAddAgent.setFocusable(false);
        jButtonAddAgent.addActionListener(new java.awt.event.ActionListener() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButtonAddAgentActionPerformed(evt);
            }
        });
        jPanel.add(jButtonAddAgent);
        jButtonAddAgent.setBounds(10, 10, 130, 30);

        jButtonLoadConfig.setText("Load agents");           // Button to load agents
        jButtonLoadConfig.setFocusable(false);
        jButtonLoadConfig.addActionListener(new java.awt.event.ActionListener() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButtonLoadConfigActionPerformed(evt);
            }
        });
        jPanel.add(jButtonLoadConfig);
        jButtonLoadConfig.setBounds(10, 110, 130, 30);

        jButtonSaveConfig.setText("Save agents");           // Button to save the list of agents
        jButtonSaveConfig.setFocusable(false);
        jButtonSaveConfig.addActionListener(new java.awt.event.ActionListener() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButtonSaveConfigActionPerformed(evt);
            }
        });
        jPanel.add(jButtonSaveConfig);
        jButtonSaveConfig.setBounds(10, 80, 130, 30);
        getContentPane().add(jPanel);
        int posPanel = posY + 32;
        jPanel.setBounds(10, posPanel, 618, 150);

        jButtonStart.setText("Start agents");               // Button to start planning
        jButtonStart.setFocusable(false);
        jButtonStart.addActionListener(new java.awt.event.ActionListener() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButtonStartActionPerformed(evt);
            }
        });
        getContentPane().add(jButtonStart);
        jButtonStart.setBounds(249, posPanel + 160, 150, 40);
        // Planning options
        sameObjects = new JCheckBox("Same objects filtering");
        getContentPane().add(sameObjects);
        sameObjects.setBounds(450, posPanel + 160, 190, 16);
        sameObjects.setSelected(true);
        trace = new JCheckBox("Planning trace");
        getContentPane().add(trace);
        trace.setBounds(450, posPanel + 180, 170, 16);
        trace.setSelected(true);
        pack();
    }

    /**
     * Selects the domain file.
     *
     * @param evt Event information
     * @since 1.0
     */
    private void jButtonLoadDomainActionPerformed(java.awt.event.ActionEvent evt) {
        javax.swing.JFileChooser fileChooser = new javax.swing.JFileChooser(startDir);
        if (fileChooser.showOpenDialog(this) == javax.swing.JFileChooser.APPROVE_OPTION) {
            startDir = fileChooser.getCurrentDirectory().toString();
            saveStartDir();
            jTextFieldDomain.setText(fileChooser.getSelectedFile().toString());
        }
    }

    /**
     * Selects the problem file.
     *
     * @param evt Event information
     * @since 1.0
     */
    private void jButtonLoadProblemActionPerformed(java.awt.event.ActionEvent evt) {
        javax.swing.JFileChooser fileChooser = new javax.swing.JFileChooser(startDir);
        if (fileChooser.showOpenDialog(this) == javax.swing.JFileChooser.APPROVE_OPTION) {
            startDir = fileChooser.getCurrentDirectory().toString();
            saveStartDir();
            jTextFieldProblem.setText(fileChooser.getSelectedFile().toString());
        }
    }

    /**
     * Clears the agents list.
     *
     * @param evt Event information
     * @since 1.0
     */
    @SuppressWarnings("rawtypes")
    private void jButtonClearAgentsActionPerformed(java.awt.event.ActionEvent evt) {
        javax.swing.DefaultListModel model
                = (javax.swing.DefaultListModel) jListAgents.getModel();
        model.clear();
    }

    /**
     * Adds an agent to the list.
     *
     * @param evt Event information
     * @since 1.0
     */
    @SuppressWarnings({"rawtypes", "unchecked"})
    private void jButtonAddAgentActionPerformed(java.awt.event.ActionEvent evt) {
        GUIBoot.Agent a = new GUIBoot.Agent(jTextFieldAgent.getText(),
                jTextFieldDomain.getText(), jTextFieldProblem.getText());
        if (a.name.equals("")) {
            javax.swing.JOptionPane.showMessageDialog(this, "The agent must have a name",
                    "Error", javax.swing.JOptionPane.ERROR_MESSAGE);
        } else {
            javax.swing.DefaultListModel model
                    = (javax.swing.DefaultListModel) jListAgents.getModel();
            model.addElement(a);
        }
    }

    /**
     * Loads the agents list from a file.
     *
     * @param evt Event information
     * @since 1.0
     */
    @SuppressWarnings({"rawtypes", "unchecked"})
    private void jButtonLoadConfigActionPerformed(java.awt.event.ActionEvent evt) {
        javax.swing.DefaultListModel model
                = (javax.swing.DefaultListModel) jListAgents.getModel();
        javax.swing.JFileChooser fileChooser = new javax.swing.JFileChooser(startDir);
        if (fileChooser.showOpenDialog(this) == javax.swing.JFileChooser.APPROVE_OPTION) {
            startDir = fileChooser.getCurrentDirectory().toString();
            saveStartDir();
            String fileName = fileChooser.getSelectedFile().toString();
            try {
                java.util.Scanner s = new java.util.Scanner(new java.io.File(fileName));
                while (s.hasNext()) {
                    String agName = s.nextLine();
                    String domain = s.nextLine();
                    String problem = s.nextLine();
                    GUIBoot.Agent a = new GUIBoot.Agent(agName, domain, problem);
                    model.addElement(a);
                }
                s.close();
            } catch (Exception e) {
                javax.swing.JOptionPane.showMessageDialog(this, "The file could not be read",
                        "Error", javax.swing.JOptionPane.ERROR_MESSAGE);
            }
        }
    }

    /**
     * Saves the list of agents to a file.
     *
     * @param evt Event information
     * @since 1.0
     */
    @SuppressWarnings("rawtypes")
    private void jButtonSaveConfigActionPerformed(java.awt.event.ActionEvent evt) {
        javax.swing.DefaultListModel model
                = (javax.swing.DefaultListModel) jListAgents.getModel();
        javax.swing.JFileChooser fileChooser = new javax.swing.JFileChooser(startDir);
        if (fileChooser.showSaveDialog(this) == javax.swing.JFileChooser.APPROVE_OPTION) {
            startDir = fileChooser.getCurrentDirectory().toString();
            saveStartDir();
            String fileName = fileChooser.getSelectedFile().toString();
            try {
                java.io.PrintWriter w = new java.io.PrintWriter(fileName);
                for (int i = 0; i < model.size(); i++) {
                    GUIBoot.Agent a = (GUIBoot.Agent) model.elementAt(i);
                    w.println(a.name);
                    w.println(a.domain);
                    w.println(a.problem);
                }
                w.close();
            } catch (Exception e) {
                javax.swing.JOptionPane.showMessageDialog(this, "The file could not be saved",
                        "Error", javax.swing.JOptionPane.ERROR_MESSAGE);
            }
        }
    }

    /**
     * Launches the agents to start the planning process.
     *
     * @param evt Event information
     * @since 1.0
     */
    @SuppressWarnings("rawtypes")
    private void jButtonStartActionPerformed(java.awt.event.ActionEvent evt) {
        saveStartDir();
        javax.swing.DefaultListModel model = (javax.swing.DefaultListModel) jListAgents.getModel();
        java.awt.Dimension screenSize = java.awt.Toolkit.getDefaultToolkit().getScreenSize();
        int x = 0, y = 0;                                   // Coordinates of each agent GUI form
        int h = heuristicType.getSelectedIndex();           // Selected heuristic function
        int searchType = searchMethod.getSelectedIndex();   // Selected search method
        if (!PlannerFactory.checkSearchConstraints(searchType, h)) {
            javax.swing.JOptionPane.showMessageDialog(this,
                "The search method and the heuristic function are not compatible",
                "Error", javax.swing.JOptionPane.ERROR_MESSAGE);
            return;
        }
        if (model.size() > 1 && HeuristicFactory.getHeuristicInfo(h, HeuristicFactory.INFO_DISTRIBUTED).equals("no")) {
            javax.swing.JOptionPane.showMessageDialog(this,
                "The selected heuristic function is not available for multi-agent tasks",
                "Error", javax.swing.JOptionPane.ERROR_MESSAGE);
            return;
        }
        try {
            // Same-objects filtering flag
            int sameObjects = this.sameObjects.isSelected()
                    ? GroundedTask.SAME_OBJECTS_REP_PARAMS + GroundedTask.SAME_OBJECTS_PREC_EQ_EFF
                    : GroundedTask.SAME_OBJECTS_DISABLED;
            AgentList agList = new ParserImp().createEmptyAgentList();  // Create the list of agents
            for (int i = 0; i < model.size(); i++) {
                agList.addAgent(((GUIBoot.Agent) model.getElementAt(i)).name.toLowerCase(), "127.0.0.1");
            }
            
            for (int i = 0; i < model.size(); i++) {        // Create the planning agents
                GUIBoot.Agent a = (GUIBoot.Agent) model.getElementAt(i);
                PlanningAgent ag = new PlanningAgent(a.name.toLowerCase(), a.domain, a.problem,
                        agList, false, sameObjects, trace.isSelected(), h, searchType);
                GUIPlanningAgent gui = new GUIPlanningAgent(ag);
                gui.setLocation(x, y);
                y += gui.getHeight();
                if (y + gui.getHeight() > screenSize.height) {
                    x += gui.getWidth();
                    y = 0;
                }
                MAPboot.planningAgents.add(ag);
            }
        } catch (Exception e) {
            javax.swing.JOptionPane.showMessageDialog(this,
                    "Could not create the planning agents",
                    "Error", javax.swing.JOptionPane.ERROR_MESSAGE);
            return;
        }
        try {                                           // Start the planning process
            for (PlanningAgent ag : MAPboot.planningAgents) {
                ag.start();
            }
        } catch (Exception e) {
            javax.swing.JOptionPane.showMessageDialog(this,
                    "Could not start the planning agents",
                    "Error", javax.swing.JOptionPane.ERROR_MESSAGE);
            return;
        }
        jButtonStart.setEnabled(false);
        setState(ICONIFIED);
    }

    /**
     * Agent class stores the initial parameters for an agent, i.e., its name
     * and the domain and problem file names.
     *
     * @since 1.0
     */
    private class Agent {

        String name;                // Name of the agent
        String domain;              // Domain file names
        String problem;             // Problem file names
        
        /**
         * Constructor. Stores the agent information.
         *
         * @param n Name of the agent
         * @param d Doman-file name
         * @param p Problem-file name
         */
        Agent(String n, String d, String p) {
            name = n;
            domain = d;
            problem = p;
        }

        /**
         * Returns a description of the agent parameters.
         *
         * @return Description of the agent parameters.
         */
        @Override
        public String toString() {
            return name + " (" + domain + "," + problem + ")";
        }
    }
}
