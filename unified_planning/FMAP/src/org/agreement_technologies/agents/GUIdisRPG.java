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

import java.awt.event.MouseEvent;
import java.awt.event.MouseListener;
import java.util.ArrayList;
import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import org.agreement_technologies.common.map_grounding.Action;
import org.agreement_technologies.common.map_grounding.GroundedCond;
import org.agreement_technologies.common.map_grounding.GroundedEff;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_grounding.GroundedVar;

/**
 * Graphical interface to show the disRPG data (distributed relaxed planning
 * graph).
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class GUIdisRPG extends JFrame implements MouseListener {

    // Serial number for serialization.
    private static final long serialVersionUID = 3080890313036553788L;
    private final AgentListener ag;	// Planning agent
    private JTable jTableRPG;           // Graphical table to show the disRPG

    /**
     * Creates a new RPG form.
     *
     * @param ag Agent listener
     * @since 1.0
     */
    public GUIdisRPG(AgentListener ag) {
        this.ag = ag;
        setTitle("disRPG: " + this.ag.getShortName());
        this.setSize(700, 600);
        this.setLocationRelativeTo(null);
        initComponents();
    }

    /**
     * This method is called from within the constructor to initialize the form.
     *
     * @since 1.0
     */
    private void initComponents() {
        JScrollPane jScrollPaneRPG = new JScrollPane();
        jTableRPG = new JTable();
        jTableRPG.setModel(new RPGTableModel());
        jTableRPG.setFillsViewportHeight(true);
        jTableRPG.setShowHorizontalLines(false);
        jTableRPG.setAutoResizeMode(JTable.AUTO_RESIZE_OFF);
        jTableRPG.addMouseListener(this);
        for (int i = 0; i < jTableRPG.getModel().getColumnCount(); i++) {
            jTableRPG.getColumnModel().getColumn(i).setPreferredWidth(150);
        }
        jScrollPaneRPG.setViewportView(jTableRPG);
        getContentPane().add(jScrollPaneRPG);
    }

    /**
     * Detects double clicks on a cell to show additional information.
     *
     * @param event Mouse event
     * @since 1.0
     */
    @Override
    public void mouseClicked(MouseEvent event) {
        if (event.getButton() == MouseEvent.BUTTON1 && event.getClickCount() == 2) {
            java.awt.Point p = event.getPoint();
            int row = jTableRPG.rowAtPoint(p);
            int column = jTableRPG.columnAtPoint(p);
            Object obj = jTableRPG.getModel().getValueAt(row, column);
            String desc = null, title = "";
            if (obj instanceof Action) {
                Action a = (Action) obj;
                title = a.toString();
                desc = a.getOperatorName() + " (";
                for (String param : a.getParams()) {
                    desc += " " + param;
                }
                desc += ")\n* Precs:\n";
                for (GroundedCond prec : a.getPrecs()) {
                    desc += "    (" + prec + ")\n";
                }
                desc += "* Effs:";
                for (GroundedEff eff : a.getEffs()) {
                    desc += "\n    (" + eff + ")";
                }
            } else if (obj instanceof RPGTableModel.RPGFact) {
                RPGTableModel.RPGFact f = (RPGTableModel.RPGFact) obj;
                title = f.v.toString();
                desc = "(" + f.v + ")";
                for (String a : ag.getCommunication().getAgentList()) {
                    int time = f.v.getMinTime(f.obj, a);
                    if (time != -1) {
                        desc += "\n* " + a + ": level " + time;
                    }
                }
            }
            if (desc != null) {
                JOptionPane.showMessageDialog(this, desc, title, JOptionPane.INFORMATION_MESSAGE);
            }
        }
    }

    /**
     * Listener when the mouse enters in the table. Not used.
     *
     * @param event Mouse event
     * @since 1.0
     */
    @Override
    public void mouseEntered(MouseEvent event) {
    }

    /**
     * Listener when the mouse exits from the table. Not used.
     *
     * @param event Mouse event
     * @since 1.0
     */
    @Override
    public void mouseExited(MouseEvent event) {
    }

    /**
     * Listener when the mouse is pressed. Not used.
     *
     * @param event Mouse event
     * @since 1.0
     */
    @Override
    public void mousePressed(MouseEvent event) {
    }

    /**
     * Listener when the mouse is released. Not used.
     *
     * @param event Mouse event
     * @since 1.0
     */
    @Override
    public void mouseReleased(MouseEvent event) {
    }

    /**
     * Table model for the disRPG.
     *
     * @since 1.0
     */
    private class RPGTableModel extends javax.swing.table.AbstractTableModel {

        // Serial number for serialization
        private static final long serialVersionUID = -6431770911028834234L;
        private final ArrayList<ArrayList<Object>> levels;  // disRPG levels
        private int largestLevel;                // Last level in the disRPG

        /**
         * Initializes the distRPG levels.
         *
         * @since 1.0
         */
        public RPGTableModel() {
            largestLevel = 0;
            levels = new ArrayList<>();
            GroundedTask g = ag.getGroundedTask();
            for (GroundedVar v : g.getVars()) {
                for (String obj : v.getReachableValues()) {
                    int time = v.getMinTime(obj);
                    if (time != -1) {
                        addFact(v, obj, time);
                    }
                }
            }
            for (Action a : g.getActions()) {
                addAction(a, a.getMinTime());
            }
        }

        /**
         * Adds an action to the disRPG.
         *
         * @param a Action to add
         * @param time Level to add the action in
         * @since 1.0
         */
        private void addAction(Action a, int time) {
            time = 2 * time + 1;
            while (levels.size() <= time) {
                levels.add(new ArrayList<>());
            }
            levels.get(time).add(a);
            if (levels.get(time).size() > largestLevel) {
                largestLevel = levels.get(time).size();
            }
        }

        /**
         * Adds a fact to a disRPG level. The fact is in the form
         * (variable=value)
         *
         * @param v Variable involved
         * @param obj Value for the variable
         * @param time disRPG level
         */
        private void addFact(GroundedVar v, String obj, int time) {
            time *= 2;
            while (levels.size() <= time) {
                levels.add(new ArrayList<>());
            }
            levels.get(time).add(new RPGFact(v, obj));
            if (levels.get(time).size() > largestLevel) {
                largestLevel = levels.get(time).size();
            }
        }

        /**
         * Returns the column name.
         *
         * @param col Number of column
         * @return Name of the column
         * @since 1.0
         */
        @Override
        public String getColumnName(int col) {
            if (col % 2 == 0) {
                return "Fact level " + (col / 2);
            }
            return "Action level " + (col / 2);
        }

        /**
         * Returns the number of columns in the table, which is the number of
         * levels in the disRPG.
         *
         * @return Number of columns
         * @since 1.0
         */
        @Override
        public int getColumnCount() {
            return levels.size();
        }

        /**
         * Gets the number of rows in the disRPG.
         *
         * @return Number of rows
         * @since 1.0
         */
        @Override
        public int getRowCount() {
            return largestLevel;
        }

        /**
         * Returns the value of a cell in the table.
         *
         * @param row Row number of the cell
         * @param col Column number of the cell
         * @return Value in the cell
         */
        @Override
        public Object getValueAt(int row, int col) {
            if (col >= 0 && col < levels.size()) {
                ArrayList<Object> level = levels.get(col);
                if (row >= 0 && row < level.size()) {
                    return level.get(row);
                }
            }
            return "";
        }

        /**
         * Class to store facts in the disRPG.
         *
         * @since 1.0
         */
        private class RPGFact {

            GroundedVar v;      // Variable
            String obj;         // Value for the variable

            /**
             * Constructor.
             *
             * @param v Variable
             * @param obj Value for the variable
             * @since 1.0
             */
            public RPGFact(GroundedVar v, String obj) {
                this.v = v;
                this.obj = obj;
            }

            /**
             * Returns a description of this fact.
             *
             * @return Description of this fact
             * @since 1.0
             */
            @Override
            public String toString() {
                String desc = "[";
                boolean first = true;
                for (String a : ag.getCommunication().getAgentList()) {
                    if (v.getMinTime(obj, a) != -1) {
                        desc += first ? a : "," + a;
                        first = false;
                    }
                }
                return desc + "](= (" + v + ") " + obj + ")";
            }
        }
    }
}
