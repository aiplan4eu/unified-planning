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
import javax.swing.JFrame;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTree;
import javax.swing.tree.DefaultMutableTreeNode;
import javax.swing.tree.DefaultTreeModel;
import javax.swing.tree.TreePath;
import org.agreement_technologies.common.map_planner.Plan;
import org.agreement_technologies.common.map_planner.PlannerFactory;
import org.agreement_technologies.common.map_viewer.PlanViewer;
import org.agreement_technologies.service.map_viewer.PlanViewerImp;

/**
 * GUISearchTree is a graphic form that shows the search tree.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class GUISearchTree extends JFrame implements java.awt.event.MouseListener {

    private static final long serialVersionUID = 978564368530575647L;

    // Graphic components
    private JScrollPane jScrollPanePlan, jScrollPaneTree;
    private JTree jTreePlans;
    private PlanViewer planViewer;

    // Planner factory
    private PlannerFactory pf;

    /**
     * Creates a new search tree form.
     *
     * @param ag Agent listener
     * @since 1.0
     */
    public GUISearchTree(AgentListener ag) {
        pf = null;
        if (ag != null) {
            setTitle("Search tree: " + ag.getShortName());
        }
        this.setSize(800, 600);
        this.setLocationRelativeTo(null);
        initComponents();
    }

    /**
     * This method is called from within the constructor to initialize the form.
     *
     * @since 1.0
     */
    private void initComponents() {
        getContentPane().setLayout(new java.awt.BorderLayout());
        planViewer = new PlanViewerImp();
        planViewer.setBackground(java.awt.Color.white);
        planViewer.setPreferredSize(new java.awt.Dimension(3200, 1000));
        jScrollPanePlan = new JScrollPane();
        jScrollPanePlan.setHorizontalScrollBarPolicy(javax.swing.ScrollPaneConstants.HORIZONTAL_SCROLLBAR_ALWAYS);
        jScrollPanePlan.setPreferredSize(new java.awt.Dimension(200, 150));
        jScrollPanePlan.add(planViewer.getComponent());
        jScrollPanePlan.setViewportView(planViewer.getComponent());
        jTreePlans = new JTree();
        jTreePlans.setModel(new DefaultTreeModel(new DefaultMutableTreeNode()));
        jTreePlans.addMouseListener(this);
        jTreePlans.setPreferredSize(null);
        jScrollPaneTree = new JScrollPane();
        jScrollPaneTree.setPreferredSize(new java.awt.Dimension(200, 100));
        jScrollPaneTree.setViewportView(jTreePlans);
        JSplitPane jsPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, jScrollPaneTree, jScrollPanePlan);
        getContentPane().add(jsPane);
    }

    /**
     * Shows a new plan in the tree.
     *
     * @param plan New plan
     * @param pf Planner factory
     * @since 1.0
     */
    public void newPlan(Plan plan, PlannerFactory pf) {
        this.pf = pf;
        DefaultTreeModel m = (DefaultTreeModel) jTreePlans.getModel();
        if (plan.isRoot()) {
            m.setRoot(new DefaultMutableTreeNode(plan));
        } else {
            String pName = plan.getName();
            int pos = pName.lastIndexOf('-');
            pName = pName.substring(0, pos);
            DefaultMutableTreeNode pNode = searchNode((DefaultMutableTreeNode) m.getRoot(), pName);
            if (pNode != null) {
                pNode.add(new DefaultMutableTreeNode(plan));
            }
        }
    }

    /**
     * Clears the tree and shows a single plan in the tree.
     *
     * @param plan New plan
     * @param pf Planer factory
     * @since 1.0
     */
    public void showPlan(Plan plan, PlannerFactory pf) {
        this.pf = pf;
        DefaultTreeModel m = (DefaultTreeModel) jTreePlans.getModel();
        m.setRoot(new DefaultMutableTreeNode(plan));
    }

    /**
     * Search a given node in the tree.
     *
     * @param n Node to search
     * @param parentName Name of the parent plan
     * @return The node if it is found; <code>null</code>, otherwise.
     * @since 1.0
     */
    private DefaultMutableTreeNode searchNode(DefaultMutableTreeNode n, String parentName) {
        Plan p = (Plan) n.getUserObject();
        if (p.getName().equals(parentName)) {
            return n;
        } else {
            for (int i = 0; i < n.getChildCount(); i++) {
                DefaultMutableTreeNode cn = (DefaultMutableTreeNode) n.getChildAt(i);
                p = (Plan) cn.getUserObject();
                if (parentName.equals(p.getName())) {
                    return cn;
                }
                if (parentName.startsWith(p.getName() + "-")) {
                    return searchNode(cn, parentName);
                }
            }
            return null;
        }
    }

    /**
     * Listener for mouse click events. Allows to select plans from the tree.
     *
     * @param e Mouse event
     * @since 1.0
     */
    @Override
    public void mouseClicked(MouseEvent e) {
        if (e.getSource() == jTreePlans) {
            if (e.getClickCount() == 1) {
                DefaultMutableTreeNode node = (DefaultMutableTreeNode) this.jTreePlans.getLastSelectedPathComponent();
                if (node == null) {
                    return;
                }
                Plan plan = (Plan) node.getUserObject();
                if (e.getButton() == java.awt.event.MouseEvent.BUTTON1) {   // Plan selection
                    planViewer.showPlan(plan, pf);
                }
            }
        }
    }

    /**
     * Listener when the mouse enters in the tree. Not used.
     *
     * @param e Mouse event
     * @since 1.0
     */
    @Override
    public void mouseEntered(MouseEvent e) {
    }

    /**
     * Listener when the mouse exits from the tree. Not used.
     *
     * @param e Mouse event
     * @since 1.0
     */
    @Override
    public void mouseExited(MouseEvent e) {
    }

    /**
     * Listener when the mouse is pressed. Not used.
     *
     * @param e Mouse event
     * @since 1.0
     */
    @Override
    public void mousePressed(MouseEvent e) {
    }

    /**
     * Listener when the mouse is released. Not used.
     *
     * @param e Mouse event
     * @since 1.0
     */
    @Override
    public void mouseReleased(MouseEvent e) {
    }

    /**
     * Select a plan from the tree, searching by its name.
     *
     * @param planName Name of the plan.
     * @since 1.0
     */
    public void selectPlan(String planName) {
        DefaultTreeModel m = (DefaultTreeModel) jTreePlans.getModel();
        DefaultMutableTreeNode pNode = searchNode((DefaultMutableTreeNode) m.getRoot(), planName);
        if (pNode != null) {
            TreePath path = new TreePath(pNode.getPath());
            jTreePlans.setExpandsSelectedPaths(true);
            jTreePlans.expandPath(path);
            jTreePlans.setSelectionPath(path);
            jTreePlans.scrollPathToVisible(path);
            planViewer.showPlan((Plan) pNode.getUserObject(), pf);
        }
    }
}
