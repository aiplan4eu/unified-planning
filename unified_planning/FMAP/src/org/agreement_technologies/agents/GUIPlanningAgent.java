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

import java.awt.Color;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.LayoutManager;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JPanel;
import org.agreement_technologies.common.map_communication.PlanningAgentListener;
import org.agreement_technologies.common.map_planner.Plan;
import org.agreement_technologies.common.map_planner.PlannerFactory;

/**
 * GUIPlanningAgent is the graphical interface for a planning agent.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class GUIPlanningAgent extends JDialog implements PlanningAgentListener,
        ActionListener {

    // Serial number for serialization
    private static final long serialVersionUID = -730178402960432486L;
    private static final int FORM_WIDTH = 210;      // Form width
    private final AgentListener ag;                 // Planning agent
    private int status;                             // Current planning stage,
    // see constants in PlanningAlgorithm to check the possible values

    // Graphic components
    private JButton btnTrace, btnRPG, btnSerachTree, btnLND;
    private JLabel lblStatus;
    private StatusPanel statusPanel;

    // Sub-forms
    private GUITrace guiTrace;
    private GUIdisRPG guiRPG;
    private GUISearchTree guiSearchTree;
    private GUILandmarks guiLandmarks;

    /**
     * Creates a new graphical interface for an agent
     *
     * @param ag Planning agent
     * @since 1.0
     */
    public GUIPlanningAgent(AgentListener ag) {
        this.ag = ag;
        status = PlanningAlgorithm.STATUS_STARTING;
        ag.setAgentListener(this);
        setTitle(this.ag.getShortName());
        this.setSize(FORM_WIDTH, 200);
        this.setResizable(true);
        initComponents();
        initSubforms();
        setVisible(true);
    }

    /**
     * Initializes the sub-forms
     *
     * @since 1.0
     */
    private void initSubforms() {
        guiTrace = new GUITrace(ag);
        guiRPG = null;
        guiSearchTree = null;
        guiLandmarks = null;
        addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                if (guiTrace != null && guiTrace.isVisible()) {
                    guiTrace.setVisible(false);
                }
                if (guiRPG != null && guiRPG.isVisible()) {
                    guiRPG.setVisible(false);
                }
                if (guiLandmarks != null && guiLandmarks.isVisible()) {
                    guiLandmarks.setVisible(false);
                }
                if (guiSearchTree != null && guiSearchTree.isVisible()) {
                    guiSearchTree.setVisible(false);
                }
                guiTrace = null;
                guiRPG = null;
                guiSearchTree = null;
                guiLandmarks = null;
            }
        });
    }

    /**
     * This method is called from within the constructor to initialize the form.
     *
     * @since 1.0
     */
    private void initComponents() {
        java.awt.Container panel = getContentPane();
        panel.setLayout(new java.awt.GridLayout(5, 1));
        ((java.awt.GridLayout) panel.getLayout()).setVgap(1);
        btnTrace = new JButton("Trace");
        btnRPG = new JButton("disRPG");
        btnLND = new JButton("Landmarks");
        btnSerachTree = new JButton("Search tree");
        btnRPG.setEnabled(false);
        btnLND.setEnabled(false);
        btnSerachTree.setEnabled(false);
        panel.add(btnTrace);
        panel.add(btnRPG);
        panel.add(btnLND);
        panel.add(btnSerachTree);
        btnTrace.addActionListener(this);
        btnRPG.addActionListener(this);
        btnLND.addActionListener(this);
        btnSerachTree.addActionListener(this);
        statusPanel = new StatusPanel(new FlowLayout(FlowLayout.LEFT));
        JLabel label = new JLabel("Status: ");
        label.setFont(new Font("TimesRoman", Font.BOLD, 12));
        statusPanel.add(label);
        lblStatus = new JLabel("starting");
        lblStatus.setFont(new Font("TimesRoman", Font.ITALIC, 12));
        statusPanel.add(lblStatus);
        panel.add(statusPanel);
    }

    /**
     * Handler for an action performed by the user.
     *
     * @param e Action event
     * @since 1.0
     */
    @Override
    public void actionPerformed(ActionEvent e) {
        if (e.getSource() == btnTrace) {
            guiTrace.setVisible(!guiTrace.isVisible());
        } else if (e.getSource() == btnRPG) {
            guiRPG.setVisible(!guiRPG.isVisible());
        } else if (e.getSource() == btnSerachTree) {
            guiSearchTree.setVisible(!guiSearchTree.isVisible());
        } else if (e.getSource() == btnLND) {
            guiLandmarks.setVisible(!guiLandmarks.isVisible());
        }
    }

    /**
     * Agent status changed notification.
     *
     * @param status New planner status
     * @since 1.0
     */
    @Override
    public void statusChanged(int status) {
        lblStatus.setText(PlanningAlgorithm.getStatusDesc(status));
        switch (this.status) {
            case PlanningAlgorithm.STATUS_GROUNDING:
                if (status != PlanningAlgorithm.STATUS_ERROR && !btnRPG.isEnabled()) {
                    guiRPG = new GUIdisRPG(ag);
                    btnRPG.setEnabled(true);
                }
                break;
            case PlanningAlgorithm.STATUS_LANDMARKS:
                if (status != PlanningAlgorithm.STATUS_ERROR && !btnLND.isEnabled()) {
                    guiLandmarks = new GUILandmarks(ag);
                    btnLND.setEnabled(true);
                }
                break;
        }
        this.status = status;
    }

    /**
     * Notifies an error message.
     *
     * @param msg Error message to display.
     * @since 1.0
     */
    @Override
    public void notyfyError(String msg) {
        guiTrace.showError(msg);
    }

    /**
     * Shows a trace message.
     *
     * @param indentLevel Indentation level
     * @param msg Message to display
     * @since 1.0
     */
    @Override
    public void trace(int indentLevel, String msg) {
        guiTrace.showInfo(indentLevel, msg);
    }

    /**
     * Adds a new plan to the trace.
     *
     * @param plan Plan to add.
     * @param pf Plan factory.
     * @since 1.0
     */
    @Override
    public void newPlan(Plan plan, PlannerFactory pf) {
        if (guiSearchTree == null) {
            guiSearchTree = new GUISearchTree(ag);
            btnSerachTree.setEnabled(true);
        }
        guiSearchTree.newPlan(plan, pf);
        statusPanel.setH(plan.getH());
    }

    /**
     * Shows a plan.
     *
     * @param plan Plan to show.
     * @param pf Plan factory.
     * @since 1.0
     */
    @Override
    public void showPlan(Plan plan, PlannerFactory pf) {
        if (guiSearchTree == null) {
            guiSearchTree = new GUISearchTree(ag);
            btnSerachTree.setEnabled(true);
        }
        guiSearchTree.showPlan(plan, pf);
    }

    /**
     * Selects a plan.
     *
     * @param planName Name of the plan to be selected.
     * @since 1.0
     */
    @Override
    public void selectPlan(String planName) {
        if (guiSearchTree != null) {
            if (!guiSearchTree.isVisible()) {
                guiSearchTree.setVisible(true);
            }
            guiSearchTree.toFront();
            guiSearchTree.selectPlan(planName);
        }
    }

    /**
     * StatusPanel class shows the heuristic progress during search.
     *
     * @since 1.0
     */
    private static class StatusPanel extends JPanel {

        // Serial number for serialization
        private static final long serialVersionUID = 317308883562686365L;
        private int maxH, minH;     // Maximum and minimum heuristic values reached
        private float blue;         // Amount of blue color. Blue color means fast
        // progress during search, while red color means that search is in a plateau

        /**
         * Constructor of a StatusPanel
         * 
         * @param layout Layout manager
         * @since 1.0
         */
        public StatusPanel(LayoutManager layout) {
            super(layout);
            maxH = minH = -1;
            blue = 255;
        }

        /**
         * Notifies the status panel about the new heuristic values reached.
         * 
         * @param h Heuristic value reached
         * @since 1.0
         */
        public void setH(int h) {
            if (maxH == -1 && h > 0) {
                maxH = minH = h;
            }
            if (h < minH) {
                minH = h;
                blue = 255;
            } else {
                blue -= 0.25;
                if (blue < 0) {
                    blue = 0;
                }
            }
            repaint();
        }

        /**
         * Paints the component.
         * 
         * @param g Graphic context
         * @since 1.0
         */
        @Override
        public void paintComponent(Graphics g) {
            super.paintComponent(g);
            if (maxH > 0 && minH > 0) {
                int w = minH * (getWidth() - 10) / maxH, b = (int) blue;
                g.setColor(new Color(255 - b, 0, b));
                g.fillRect(5, 24, w, 6);
            }
        }
    }
}
