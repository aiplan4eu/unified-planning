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
package org.agreement_technologies.service.map_planner;

import java.util.ArrayList;
import org.agreement_technologies.common.map_grounding.Action;
import org.agreement_technologies.common.map_planner.Condition;

/**
 * Actions for POP planning.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class POPAction {

    private String actionName;              // Action name
    private ArrayList<POPPrecEff> precs;    // List of POP action preconditions
    private ArrayList<POPPrecEff> effects;  // List of POP action effects
    private Condition[] precConds;          // Array of action preconditions
    private Condition[] effConds;           // Array of action effects
    // For each variable, indicates if is requires in the action preconditions
    // and updated in the action effects
    private boolean[] effectInVariable;

    /**
     * Creates a new POP action.
     *
     * @param actionName Action name
     * @param precs List of POP action preconditions
     * @param effs List of POP action effects
     * @since 1.0
     */
    public POPAction(String actionName, ArrayList<POPPrecEff> precs, ArrayList<POPPrecEff> effs) {
        int i;
        this.actionName = actionName;
        if (precs != null) {
            this.precs = new ArrayList<>(precs.size());
            this.precConds = new Condition[precs.size()];
            for (i = 0; i < precs.size(); i++) {
                POPPrecEff p = precs.get(i);
                this.precs.add(p);
                this.precConds[i] = p.getCondition();
            }
        } else {
            this.precs = new ArrayList<>(0);
            this.precConds = new Condition[0];
        }
        if (effs != null) {
            this.effects = new ArrayList<>(effs.size());
            this.effConds = new Condition[effs.size()];
            for (i = 0; i < effs.size(); i++) {
                POPPrecEff e = effs.get(i);
                this.effects.add(e);
                this.effConds[i] = e.getCondition();
            }
        } else {
            this.effects = new ArrayList<>(0);
            this.effConds = new Condition[0];
        }
        if (this.actionName.equals("Initial") || this.actionName.equals("Final")) {
            effectInVariable = new boolean[0];
        } else {
            effectInVariable = new boolean[this.precs.size()];
            for (i = 0; i < effectInVariable.length; i++) {
                effectInVariable[i] = false;
            }
            POPPrecEff p;
            for (i = 0; i < this.precs.size(); i++) {
                p = this.precs.get(i);
                for (POPPrecEff e : this.effects) {
                    if (e.getVarCode() == p.getVarCode()) {
                        effectInVariable[i] = true;
                        break;
                    }
                }
            }
        }
    }

    /**
     * Creates a new POP action.
     *
     * @param act Action
     * @param precs List of POP action preconditions
     * @param effs List of POP action effects
     * @since 1.0
     */
    public POPAction(Action act, ArrayList<POPPrecEff> precs, ArrayList<POPPrecEff> effs) {
        int i;
        if (act != null) {
            this.actionName = act.getOperatorName();
            for (i = 0; i < act.getParams().length; i++) {
                this.actionName += " " + act.getParams()[i];
            }
        } else {
            this.actionName = null;
        }
        if (precs != null) {
            this.precs = new ArrayList<>(precs.size());
            this.precConds = new Condition[precs.size()];
            for (i = 0; i < precs.size(); i++) {
                POPPrecEff p = precs.get(i);
                this.precs.add(p);
                this.precConds[i] = p.getCondition();
            }
        } else {
            this.precs = new ArrayList<>(0);
            this.precConds = new Condition[0];
        }
        if (effs != null) {
            this.effects = new ArrayList<>(effs.size());
            this.effConds = new Condition[effs.size()];
            for (i = 0; i < effs.size(); i++) {
                POPPrecEff e = effs.get(i);
                this.effects.add(e);
                this.effConds[i] = e.getCondition();
            }
        } else {
            this.effects = new ArrayList<>(0);
            this.effConds = new Condition[0];
        }
        if (this.actionName.equals("Initial") || this.actionName.equals("Final")) {
            effectInVariable = new boolean[0];
        } else {
            effectInVariable = new boolean[this.precs.size()];
            for (i = 0; i < effectInVariable.length; i++) {
                effectInVariable[i] = false;
            }
            POPPrecEff p;
            for (i = 0; i < this.precs.size(); i++) {
                p = this.precs.get(i);
                for (POPPrecEff e : this.effects) {
                    if (e.getVarCode() == p.getVarCode()) {
                        effectInVariable[i] = true;
                        break;
                    }
                }
            }
        }
    }

    /**
     * Checks if a given variable is required and updated by the action.
     *
     * @param index Variable index
     * @return <code>true</code>, if the variable is required and updated by the
     * action; <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean hasEffectInVariable(int index) {
        return effectInVariable[index];
    }

    /**
     * Gets the action name.
     *
     * @return Action name
     * @since 1.0
     */
    public String getName() {
        return this.actionName;
    }

    /**
     * Gets the list of POP preconditions.
     *
     * @return List of POP preconditions
     * @since 1.0
     */
    public ArrayList<POPPrecEff> getPrecs() {
        return this.precs;
    }

    /**
     * Gets the list of POP effects.
     *
     * @return List of POP effects
     * @since 1.0
     */
    public ArrayList<POPPrecEff> getEffects() {
        return this.effects;
    }

    /**
     * Sets the action name.
     *
     * @param name Action name
     * @since 1.0
     */
    public void setName(String name) {
        this.actionName = name;
    }

    /**
     * Gets a description of this action.
     *
     * @return Action description
     * @since 1.0
     */
    @Override
    public String toString() {
        return this.actionName;
    }

    /**
     * Gets the array of action preconditions.
     *
     * @return Array of action preconditions
     * @since 1.0
     */
    public Condition[] getPrecConditions() {
        return precConds;
    }

    /**
     * Gets the array of action effects.
     *
     * @return Array of action effects
     * @since 1.0
     */
    public Condition[] getEffConditions() {
        return effConds;
    }

}
