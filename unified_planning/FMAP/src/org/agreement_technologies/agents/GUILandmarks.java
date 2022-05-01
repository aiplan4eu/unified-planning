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
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;
import java.awt.event.MouseListener;
import java.awt.event.MouseMotionListener;
import java.awt.event.MouseWheelEvent;
import java.awt.event.MouseWheelListener;
import java.awt.image.BufferedImage;
import java.util.ArrayList;
import java.util.Random;
import javax.swing.JFrame;
import javax.swing.JMenuItem;
import javax.swing.JPanel;
import javax.swing.JPopupMenu;
import javax.swing.JScrollPane;
import org.agreement_technologies.common.map_landmarks.LandmarkFluent;
import org.agreement_technologies.common.map_landmarks.LandmarkNode;
import org.agreement_technologies.common.map_landmarks.LandmarkOrdering;
import org.agreement_technologies.common.map_landmarks.Landmarks;
import org.agreement_technologies.service.map_viewer.PlanViewerImp.ImageSelection;
import org.agreement_technologies.service.tools.Graph;
import org.agreement_technologies.service.tools.Graph.Adjacent;

/**
 * GUILandmarks is the class that shows the landmark graph graphically.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class GUILandmarks extends JFrame {

    // Serial number for serialization
    private static final long serialVersionUID = 5812446400385328544L;
    // GUI components
    private LandmarksPane landmarksPane;
    private JScrollPane jScrollPane;

    /**
     * Creates a new landmarks form.
     *
     * @param ag Listener to retrieve information from the agent
     * @since 1.0
     */
    public GUILandmarks(AgentListener ag) {
        if (ag != null) {
            setTitle("Landmarks: " + ag.getShortName());
        }
        this.setSize(800, 600);
        this.setLocationRelativeTo(null);
        initComponents(ag);
    }

    /**
     * This method is called from within the constructor to initialize the form.
     *
     * @param ag Listener to retrieve information from the agent
     * @since 1.0
     */
    private void initComponents(AgentListener ag) {
        getContentPane().setLayout(new java.awt.BorderLayout());
        landmarksPane = new LandmarksPane(ag.getLandmarks());
        jScrollPane = new JScrollPane();
        jScrollPane.setHorizontalScrollBarPolicy(javax.swing.ScrollPaneConstants.HORIZONTAL_SCROLLBAR_ALWAYS);
        jScrollPane.setPreferredSize(new java.awt.Dimension(200, 150));
        jScrollPane.add(landmarksPane);
        jScrollPane.setViewportView(landmarksPane);
        getContentPane().add(jScrollPane);
    }

    /**
     * LandmarkSet stores a single landmark (variable = value) or a disjunction
     * of single landmarks.
     *
     * @since 1.0
     */
    private static class LandmarkSet {

        // Set of one or more single landmarks
        private final ArrayList<String> landmarks;
        // Flag to know if it is a single landmark or a disjunctive set of landmarks
        private final boolean disjunctive;

        /**
         * Constructor of a LandmarkSet from a LandmarkNode. LandmarkNodes are
         * generated when the landmark graph is built, but they contain more
         * information which is not needed in this GUI.
         *
         * @param n LandmarkNode to copy the information from.
         * @since 1.0
         */
        public LandmarkSet(LandmarkNode n) {
            landmarks = new ArrayList<>();
            disjunctive = !n.isSingleLiteral();
            for (LandmarkFluent f : n.getLiterals()) {
                landmarks.add(f.toString());
            }
        }

        /**
         * Checks if two sets of landmarks are equal.
         *
         * @param x Other landmark set to compare with this one.
         * @return <code>true</code> if both sets are equal; <code>false</code>
         * otherwise.
         * @since 1.0
         */
        @Override
        public boolean equals(Object x) {
            LandmarkSet ls = (LandmarkSet) x;
            if (ls.landmarks.size() != landmarks.size()
                    || ls.disjunctive != disjunctive) {
                return false;
            }
            for (String l : ls.landmarks) {
                if (!landmarks.contains(l)) {
                    return false;
                }
            }
            return true;
        }

        /**
         * Returns a hash code for this set of landmarks.
         *
         * @return Hash code for this landmarks set
         * @since 1.0
         */
        @Override
        public int hashCode() {
            int res = 0;
            for (String l : landmarks) {
                res += l.hashCode();
            }
            return res;
        }

        /**
         * Returns a description of this set of landmarks.
         *
         * @return Description of this landmarks set
         * @since 1.0
         */
        @Override
        public String toString() {
            String res = disjunctive ? "{" : "";
            for (int i = 0; i < landmarks.size(); i++) {
                if (i > 0) {
                    res += "\n";
                }
                res += landmarks.get(i);
            }
            return disjunctive ? res + "}" : res;
        }
    }

    /**
     * DrawNode is a class to show graphically a set of landmarks.
     *
     * @since 1.0
     */
    private static class DrawNode {

        // Font for the text
        static java.awt.Font NODE_FONT = new java.awt.Font("Arial Narrow",
                java.awt.Font.PLAIN, 16);
        // Width of the box in pixels
        static final int BOX_WIDTH = 150;
        int index;          // Index of this node
        int x, y;           // Coordinates of the box
        int level;          // Level in the graph
        int lineHeight;     // Height of each line of text
        double scale;       // Scale used to display the node
        LandmarkSet lset;   // Set of landmarks to display in the box
        // Set of nodes that must be achieved right after this one
        ArrayList<DrawNode> nextNodes;
        // Arrow type to link this node with the next ones. The type can be
        // LandmarkOrdering.NECESSARY or LandmarkOrdering.REASONABLE 
        ArrayList<Integer> arrowTypes;

        /**
         * Constructor of a DrawNode.
         *
         * @param i Index of this node
         * @param ls Set of landmarks to display in this node
         * @param scale Initial scale factor
         * @since 1.0
         */
        public DrawNode(int i, LandmarkSet ls, double scale) {
            index = i;
            lset = ls;
            level = -1;
            this.scale = scale;
            lineHeight = 14;
            nextNodes = new ArrayList<>();
            arrowTypes = new ArrayList<>();
        }

        /**
         * Scales a number according to the scale factor of this node.
         *
         * @param n Number to be scaled
         * @return Scaled number
         * @since 1.0
         */
        private int scale(int n) {
            return (int) (scale * n);
        }

        /**
         * Method to draw an arrow
         *
         * @param g Graphic context
         * @param x Horizontal start coordinate
         * @param y Vertical start coordinate
         * @param xx Horizontal end coordinate
         * @param yy Vertical end coordinate
         * @since 1.0
         */
        private void drawArrow(Graphics2D g, int x, int y, int xx, int yy) {
            float arrowWidth = 6.0f;
            float theta = 0.423f;
            int[] xPoints = new int[3];
            int[] yPoints = new int[3];
            float[] vecLine = new float[2];
            float[] vecLeft = new float[2];
            float fLength;
            float th;
            float ta;
            float baseX, baseY;

            xPoints[0] = xx;
            yPoints[0] = yy;

            // build the line vector
            vecLine[0] = (float) xPoints[0] - x;
            vecLine[1] = (float) yPoints[0] - y;

            // build the arrow base vector - normal to the line
            vecLeft[0] = -vecLine[1];
            vecLeft[1] = vecLine[0];

            // setup length parameters
            fLength = (float) Math.sqrt(vecLine[0] * vecLine[0] + vecLine[1] * vecLine[1]);
            th = arrowWidth / (2.0f * fLength);
            ta = arrowWidth / (2.0f * ((float) Math.tan(theta) / 2.0f) * fLength);

            // find the base of the arrow
            baseX = ((float) xPoints[0] - ta * vecLine[0]);
            baseY = ((float) yPoints[0] - ta * vecLine[1]);

            // build the points on the sides of the arrow
            xPoints[1] = (int) (baseX + th * vecLeft[0]);
            yPoints[1] = (int) (baseY + th * vecLeft[1]);
            xPoints[2] = (int) (baseX - th * vecLeft[0]);
            yPoints[2] = (int) (baseY - th * vecLeft[1]);

            g.drawLine(x, y, (int) baseX, (int) baseY);
            g.fillPolygon(xPoints, yPoints, 3);
        }

        /**
         * Returns the height of the box.
         *
         * @return height of the box in pixels.
         * @since 1.0
         */
        public int height() {
            return lset.landmarks.size() * lineHeight + 8;
        }

        /**
         * Draws the current node.
         *
         * @param g2d Graphic context
         * @since 1.0
         */
        public void paintNode(Graphics2D g2d) {
            g2d.setFont(NODE_FONT);
            java.awt.FontMetrics metrics = g2d.getFontMetrics(NODE_FONT);
            lineHeight = metrics.getHeight();
            int h = height(), w = scale(BOX_WIDTH);
            if (lset.disjunctive) {
                g2d.setColor(Color.lightGray);
            } else {
                g2d.setColor(Color.white);
            }
            g2d.fillRect(scale(x), scale(y), w, h);
            g2d.setColor(Color.black);
            g2d.drawRect(scale(x), scale(y), w, h);
            int ty = scale(y);
            for (int i = 0; i < lset.landmarks.size(); i++) {
                String l = lset.landmarks.get(i);
                if (lset.disjunctive) {
                    if (i == 0) {
                        l = "{" + l;
                    }
                    if (i == lset.landmarks.size() - 1) {
                        l = l + "}";
                    }
                }
                int ws = metrics.stringWidth(l);
                g2d.drawString(l, scale(x) + (w - ws) / 2, ty + lineHeight);
                ty += lineHeight;
            }
        }

        /**
         * Draws the arrow to the next nodes.
         *
         * @param g2d Graphic context
         * @since 1.0
         */
        public void paintArrows(Graphics2D g2d) {
            int py;
            py = scale(this.y) + height() / 2;
            for (int i = 0; i < nextNodes.size(); i++) {
                DrawNode n = nextNodes.get(i);
                switch (arrowTypes.get(i)) {
                    case LandmarkOrdering.REASONABLE:
                        g2d.setColor(Color.blue);
                        break;
                    default:
                        g2d.setColor(Color.darkGray);
                }
                drawArrow(g2d, scale(x + BOX_WIDTH), py, scale(n.x),
                        scale(n.y) + n.height() / 2);
            }
        }

        /**
         * Adds a new node after this one.
         *
         * @param next Next node
         * @param type Type of the next node. It can be
         * LandmarkOrdering.NECESSARY or LandmarkOrdering.REASONABLE
         * @since 1.0
         */
        public void addNext(DrawNode next, int type) {
            for (DrawNode n : nextNodes) {
                if (n.index == next.index) {
                    return;
                }
            }
            nextNodes.add(next);
            arrowTypes.add(type);
        }

        /**
         * Changes the scale factor.
         *
         * @param s Scale factor
         * @since 1.0
         */
        public void setScale(double s) {
            scale = s;
            int fs;
            if (s <= 0.25) {
                fs = 8;
            } else if (s <= 0.5) {
                fs = 9;
            } else if (s <= 0.75) {
                fs = 12;
            } else if (s <= 1.5) {
                fs = 16;
            } else if (s <= 2.5) {
                fs = 18;
            } else {
                fs = 16;
            }
            NODE_FONT = new java.awt.Font("Arial Narrow", java.awt.Font.PLAIN, fs);
        }

        /**
         * Check if this node is selected.
         *
         * @param x Horizontal mouse position
         * @param y Vertical mouse position
         * @return <code>true</code> if the mouse was pressed inside this box;
         * <code>false</code> otherwise.
         * @since 1.0
         */
        public boolean isSelected(int x, int y) {
            int rx = (int) (x / scale), ry = (int) (y / scale);
            return rx >= this.x && ry >= this.y && rx <= this.x + BOX_WIDTH && ry <= this.y + height();
        }

        /**
         * Moves the position of the box.
         *
         * @param incX Horizontal increase of the position
         * @param incY Vertical increase of the position
         * @since 1.0
         */
        public void move(int incX, int incY) {
            x += (int) incX / scale;
            y += (int) incY / scale;
        }
    }

    /**
     * LandmarksPane displays the graph of landmark nodes in the form, where
     * each node shown is a DrawNode.
     *
     * @since 1.0
     */
    private static class LandmarksPane extends JPanel implements MouseListener, MouseMotionListener,
            MouseWheelListener, ActionListener {

        // Serial number for serialization
        private static final long serialVersionUID = -1659156643473507799L;
        // Back image for double buffering
        private BufferedImage back;
        // Graph of landmark nodes, where vertices are sets of landmarks and edges are types of landmarks
        private Graph<LandmarkSet, Integer> graph;
        // Set of graphic landmark nodes
        private ArrayList<DrawNode> nodes;
        private int maxLevel;           // Last level in the landmarks graph
        private int width, height;      // Dimensions of the graphic area
        private int mouseX, mouseY;     // Last mouse position
        private double scale;           // Scale factor
        private DrawNode selected;      // Selected node by the user
        private PopUpMenu popUpMenu;    // Contextual menu
        private Landmarks landmarks;    // Reference to the landmarks graph

        // Separation between nodes and margins
        private static final int HORIZ_DST = 300, VERT_GAP = 60;
        private static final int HORIZ_MARGIN = 20, VERT_MARGIN = 20;

        /**
         * Constructor of a LandmarksPane from the graph of landmarks.
         *
         * @param landmarks Graph of landmarks.
         * @since 1.0
         */
        public LandmarksPane(Landmarks landmarks) {
            setBackground(Color.WHITE);
            scale = 1;
            selected = null;
            this.landmarks = landmarks;
            generateNodes();
            addMouseListener(this);
            addMouseMotionListener(this);
            addMouseWheelListener(this);
            popUpMenu = new PopUpMenu();
            popUpMenu.itemTrans.addActionListener(this);
            popUpMenu.itemCycles.addActionListener(this);
            popUpMenu.itemCopy.addActionListener(this);
        }

        /**
         * Generates the graphic nodes (DrawNodes) from the landmarks graph.
         *
         * @since 1.0
         */
        private void generateNodes() {
            graph = new Graph<>();
            nodes = new ArrayList<>();
            if (landmarks != null) {
                preprocessOrderings(landmarks);
                deleteEmptyLevels();
                locateNodes();
            }
            graph = null;
            width = 100;
            height = 100;
            for (DrawNode n : nodes) {
                if (n.x + DrawNode.BOX_WIDTH > width) {
                    width = n.x + DrawNode.BOX_WIDTH + 20;
                }
                if (n.y + n.height() > height) {
                    height = n.y + n.height() + 20;
                }
            }
            width += 20;
            height += 20;
            back = new BufferedImage(width, height, BufferedImage.TYPE_3BYTE_BGR);
            setPreferredSize(new java.awt.Dimension(width, height));
        }

        /**
         * Calculates and deletes the empty levels in the graph.
         *
         * @since 1.0
         */
        private void deleteEmptyLevels() {
            maxLevel = 0;
            for (DrawNode n : nodes) {
                if (n.level > maxLevel) {
                    maxLevel = n.level;
                }
            }
            int level = 0;
            while (level <= maxLevel) {
                boolean empty = true;
                for (DrawNode n : nodes) {
                    if (n.level == level) {
                        empty = false;
                        break;
                    }
                }
                if (empty) {
                    for (DrawNode n : nodes) {
                        if (n.level > level) {
                            n.level--;
                        }
                    }
                    maxLevel--;
                } else {
                    level++;
                }
            }
        }

        /**
         * Paints this pane.
         *
         * @param g Graphic context
         * @since 1.0
         */
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            if (back != null) {
                draw(back.getGraphics());
                g.drawImage(back, 0, 0, null);
            }
        }

        /**
         * Draws the content of this pane in the given graphic context.
         *
         * @param g Graphic contex
         * @since 1.0
         */
        private void draw(Graphics g) {
            Graphics2D g2d = (Graphics2D) g;
            g2d.setColor(Color.white);
            g2d.fillRect(0, 0, back.getWidth(), back.getHeight());
            g2d.setRenderingHint(java.awt.RenderingHints.KEY_TEXT_ANTIALIASING,
                    java.awt.RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
            g2d.setRenderingHint(java.awt.RenderingHints.KEY_ANTIALIASING,
                    java.awt.RenderingHints.VALUE_ANTIALIAS_ON);
            for (DrawNode n : nodes) {
                n.paintArrows(g2d);
            }
            for (DrawNode n : nodes) {
                n.paintNode(g2d);
            }
        }

        /**
         * Calculates the position of the nodes.
         *
         * @since 1.0
         */
        private void locateNodes() {
            Random rnd = new Random();
            DrawNode levels[] = new DrawNode[maxLevel + 1];
            for (DrawNode n : nodes) {
                n.x = HORIZ_MARGIN + n.level * HORIZ_DST;
                DrawNode prev = levels[n.level];
                n.y = prev == null ? VERT_MARGIN : prev.y + prev.height() + VERT_GAP
                        + rnd.nextInt(VERT_GAP / 4) - (VERT_GAP / 8);
                levels[n.level] = n;
            }
        }

        /**
         * Processes the orderings between nodes extracted from the landmarks
         * graph.
         *
         * @param landmarks Landmarks graph
         * @since 1.0
         */
        private void preprocessOrderings(Landmarks landmarks) {
            ArrayList<DrawNode> rootNodes = new ArrayList<>();
            ArrayList<LandmarkOrdering> ords = landmarks.getOrderings(Landmarks.ALL_ORDERINGS, false);
            for (LandmarkOrdering o : ords) {
                LandmarkSet ls1 = new LandmarkSet(o.getNode1()),
                        ls2 = new LandmarkSet(o.getNode2());
                graph.addEdge(ls1, ls2, o.getType());
            }
            for (int i = 0; i < graph.numNodes(); i++) {
                nodes.add(new DrawNode(i, graph.getNode(i), scale));
            }
            for (DrawNode n : nodes) {
                ArrayList<Adjacent<Integer>> adj = graph.getAdjacents(n.index);
                for (Adjacent<Integer> a : adj) {
                    n.addNext(nodes.get(a.dst), a.label);
                }
                if (graph.isRoot(n.index)) {
                    rootNodes.add(n);
                }
            }
            if (rootNodes.isEmpty() && graph.numNodes() > 0) {
                int[] nList = graph.sortNodesByIndegree();
                int minDegree = graph.inDegree(nList[0]);
                for (int i = 0; i < nList.length; i++) {
                    if (graph.inDegree(nList[i]) == minDegree) {
                        rootNodes.add(nodes.get(nList[i]));
                    }
                }
            }
            boolean placedNodes[] = new boolean[nodes.size()];
            for (DrawNode n : rootNodes) {
                n.level = 0;
                placedNodes[n.index] = true;
            }
            for (int i = 0; i < placedNodes.length; i++) {
                if (!placedNodes[i]) {
                    placeNode(nodes.get(i), rootNodes);
                }
            }
        }

        /**
         * Sets the position of a node.
         *
         * @param n Node to place
         * @param rootNodes Set of root nodes of the graph
         * @since 1.0
         */
        private void placeNode(DrawNode n, ArrayList<DrawNode> rootNodes) {
            n.level = 0;
            for (DrawNode orig : rootNodes) {
                int dist = graph.maxDistanceWithCycles(orig.index, n.index);
                if (dist != Graph.INFINITE && dist > n.level) {
                    n.level = dist;
                }
            }
        }

        /**
         * Listener when the mouse is clicked. Not used.
         *
         * @param e Mouse event
         * @since 1.0
         */
        @Override
        public void mouseClicked(MouseEvent e) {
        }

        /**
         * Listener when the mouse enters in the pane. Not used.
         *
         * @param e Mouse event
         * @since 1.0
         */
        @Override
        public void mouseEntered(MouseEvent e) {
        }

        /**
         * Listener when the mouse exits from the pane. Not used.
         *
         * @param e Mouse event
         * @since 1.0
         */
        @Override
        public void mouseExited(MouseEvent e) {
        }

        /**
         * Listener when the mouse is pressed. Using the left button, it is
         * possible to change the position of a node. Using the right button,
         * the contextual menu is shown.
         *
         * @param e Mouse event
         * @since 1.0
         */
        @Override
        public void mousePressed(MouseEvent e) {
            if (e.getButton() == MouseEvent.BUTTON1 && selected == null) {
                mouseX = e.getX();
                mouseY = e.getY();
                for (DrawNode n : nodes) {
                    if (n.isSelected(mouseX, mouseY)) {
                        selected = n;
                        break;
                    }
                }
            } else if (e.getButton() == MouseEvent.BUTTON3) {
                popUpMenu.show(e.getComponent(), e.getX(), e.getY());
            }
        }

        /**
         * Listener when the mouse is released.
         *
         * @param e Mouse event
         * @since 1.0
         */
        @Override
        public void mouseReleased(MouseEvent e) {
            selected = null;
            if (e.getButton() == MouseEvent.BUTTON3) {
                popUpMenu.show(e.getComponent(), e.getX(), e.getY());
            }
        }

        /**
         * Listener when the mouse is dragged. Moves the selected node, if any.
         *
         * @param e Mouse event
         * @since 1.0
         */
        @Override
        public void mouseDragged(MouseEvent e) {
            if (selected != null) {
                selected.move(e.getX() - mouseX, e.getY() - mouseY);
                mouseX = e.getX();
                mouseY = e.getY();
                repaint();
            }
        }

        /**
         * Listener when the mouse is moved. Not used.
         *
         * @param e Mouse event
         * @since 1.0
         */
        @Override
        public void mouseMoved(MouseEvent e) {
        }

        /**
         * Listener when the mouse wheel is moved. Changes the scale factor.
         *
         * @param e Mouse wheel event
         * @since 1.0
         */
        @Override
        public void mouseWheelMoved(MouseWheelEvent e) {
            int m = e.getWheelRotation();
            if (m > 0 && scale < 4) {
                scale += 0.25;
            } else if (m < 0 && scale > 0.25) {
                scale -= 0.25;
            }
            setPreferredSize(new Dimension((int) (width * scale), (int) (height * scale)));
            back = new BufferedImage((int) (width * scale), (int) (height * scale), BufferedImage.TYPE_3BYTE_BGR);
            for (DrawNode n : nodes) {
                n.setScale(scale);
            }
            repaint();
            revalidate();
        }

        /**
         * Manages the options in the contextual menu.
         *
         * @param e Action event
         * @since 1.0
         */
        @Override
        public void actionPerformed(ActionEvent e) {
            if (e.getSource() == popUpMenu.itemTrans) {
                landmarks.filterTransitiveOrders();
                generateNodes();
                popUpMenu.itemTrans.setEnabled(false);
                repaint();
                revalidate();
            } else if (e.getSource() == popUpMenu.itemCycles) {
                landmarks.removeCycles();
                generateNodes();
                popUpMenu.itemCycles.setEnabled(false);
                repaint();
                revalidate();
            } else if (e.getSource() == popUpMenu.itemCopy) {
                if (back == null) {
                    return;
                }
                ImageSelection imageSelection = new ImageSelection(back);
                Toolkit.getDefaultToolkit().getSystemClipboard()
                        .setContents(imageSelection, null);
            }
        }

        /**
         * PopUpMenu defines a contextual menu for the landmarks GUI. It has
         * three options: remove the transitive orderings in the landmarks
         * graph, remove the cycles, and copy the graph to clipboard.
         *
         * @since 1.0
         */
        private class PopUpMenu extends JPopupMenu {

            // Serial number for serialization
            private static final long serialVersionUID = 1L;
            // Menu items
            JMenuItem itemTrans, itemCycles, itemCopy;

            /**
             * Menu constructor.
             *
             * @since 1.0
             */
            public PopUpMenu() {
                itemTrans = new JMenuItem("Filter transitive orderings");
                add(itemTrans);
                itemCycles = new JMenuItem("Remove cycles");
                add(itemCycles);
                itemCopy = new JMenuItem("Copy to clipboard");
                add(itemCopy);
            }
        }
    }
}
