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
import javax.swing.JFrame;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.event.CaretEvent;
import javax.swing.event.CaretListener;
import javax.swing.text.BadLocationException;

/**
 * GUITrace is a graphical interface to show trace data of a planning agent.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class GUITrace extends JFrame implements CaretListener, MouseListener {

    // Serial number for serialization
    private static final long serialVersionUID = 3465968268556479994L;
    // Vignettes to display different levels in the trace
    private static final String[] VIGNETTE = {"", "*", "+", "-"};
    private final AgentListener ag;	// Planning agent
    private JTextArea taTrace;          // Text area to show the trace
    private int lineNum;                // Line number

    /**
     * Creates a new trace form.
     *
     * @param ag Agent listener
     * @since 1.0
     */
    public GUITrace(AgentListener ag) {
        this.ag = ag;
        setTitle("Trace: " + this.ag.getShortName());
        this.setSize(500, 600);
        this.setLocationRelativeTo(null);
        initComponents();
    }

    /**
     * This method is called from within the constructor to initialize the form.
     *
     * @since 1.0
     */
    private void initComponents() {
        lineNum = -1;
        taTrace = new javax.swing.JTextArea();
        taTrace.setEditable(false);
        taTrace.addCaretListener(this);
        taTrace.addMouseListener(this);
        JScrollPane jspScroll = new JScrollPane();
        jspScroll.setViewportView(taTrace);
        getContentPane().add(jspScroll);
    }

    /**
     * Shows an error message.
     *
     * @param msg Error message
     * @since 1.0
     */
    public void showError(String msg) {
        showInfo(0, "ERROR: " + msg);
    }

    /**
     * Shows trace information.
     *
     * @param level Indentation level
     * @param msg Trace message
     * @since 1.0
     */
    public void showInfo(int level, String msg) {
        String pre = level < VIGNETTE.length ? VIGNETTE[level] : ">";
        for (int i = 0; i < level; i++) {
            pre = "  " + pre;
        }
        if (level != 0) {
            pre += " ";
        }
        taTrace.append(pre + msg + "\n");
        taTrace.setCaretPosition(taTrace.getDocument().getLength());
    }

    /**
     * Listener for caret updates.
     *
     * @param arg0 Caret event
     * @since 1.0
     */
    @Override
    public void caretUpdate(CaretEvent arg0) {
        int caretPos = taTrace.getCaretPosition();
        try {
            lineNum = taTrace.getLineOfOffset(caretPos);
        } catch (BadLocationException e) {
        }
    }

    /**
     * Listener for mouse clicks. Allows to show a plan if the user clicks on
     * its name in the trace.
     *
     * @param e Mouse event
     * @since 1.0
     */
    @Override
    public void mouseClicked(MouseEvent e) {
        if (e.getButton() == MouseEvent.BUTTON1 && e.getClickCount() == 2 && lineNum >= 0) {
            try {
                int start = taTrace.getLineStartOffset(lineNum);
                int end = taTrace.getLineEndOffset(lineNum);
                String line = taTrace.getText().substring(start, end).trim();
                int pos = line.indexOf("\u03A0");
                if (pos >= 0) {
                    line = line.substring(pos);
                    pos = line.indexOf(" ");
                    if (pos >= 0) {
                        line = line.substring(0, pos);
                    }
                    ag.selectPlan(line.trim());
                }
            } catch (BadLocationException e1) {
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
     * Listener when the mouse is pressed. Not used.
     *
     * @param e Mouse event
     * @since 1.0
     */
    @Override
    public void mouseReleased(MouseEvent e) {
    }
}
