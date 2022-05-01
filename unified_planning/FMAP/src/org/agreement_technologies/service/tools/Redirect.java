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
package org.agreement_technologies.service.tools;

import java.io.PrintStream;

/**
 * Redirect class allows to redirect the standard outputs.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class Redirect {
    
    private final PrintStream outputStream; // Output stream
    private final PrintStream errorStream;  // Output error stream
    
    /**
     * Captures the standard outputs.
     * 
     * @since 1.0
     */
    public Redirect() {
        outputStream = captureStandardOutput();
        errorStream = captureStandardError();
    }
    
    /**
     * Captures the standard outputs.
     * 
     * @return Redirect object to be able to release the outputs later
     * @since 1.0
     */
    public static Redirect captureOutput() {
        return new Redirect();
    }

    /**
     * Captures the standard output.
     * 
     * @return Previous output stream
     * @since 1.0
     */
    public static PrintStream captureStandardOutput() {
        PrintStream consoleOut = System.out;
        try {
          java.io.PipedInputStream readBuffer = new java.io.PipedInputStream();
          java.io.PipedOutputStream outBuffer = new java.io.PipedOutputStream(readBuffer);
          System.setOut(new java.io.PrintStream(outBuffer));
        } catch (java.io.IOException e) { }
        return consoleOut;
    }

    /**
     * Captures the standard error output.
     * 
     * @return Previous error output stream
     * @since 1.0
     */
    public static PrintStream captureStandardError() {
        PrintStream consoleOut = System.err;
        try {
          java.io.PipedInputStream readBuffer = new java.io.PipedInputStream();
          java.io.PipedOutputStream outBuffer = new java.io.PipedOutputStream(readBuffer);
          System.setErr(new java.io.PrintStream(outBuffer));
        } catch (java.io.IOException e) { }
        return consoleOut;
    }

    /**
     * Releases the output streams.
     * 
     * @since 1.0
     */
    public void releaseOutput() {
        System.setErr(errorStream);
        System.setOut(outputStream);
    }
}
