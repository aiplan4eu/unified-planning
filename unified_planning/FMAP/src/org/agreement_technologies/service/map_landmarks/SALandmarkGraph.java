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
package org.agreement_technologies.service.map_landmarks;

import java.util.ArrayList;
import java.util.Hashtable;
import org.agreement_technologies.common.map_grounding.GroundedTask;
import org.agreement_technologies.common.map_landmarks.LandmarkAction;
import org.agreement_technologies.common.map_landmarks.LandmarkFluent;
import org.agreement_technologies.common.map_landmarks.LandmarkGraph;
import org.agreement_technologies.common.map_landmarks.LandmarkNode;
import org.agreement_technologies.common.map_landmarks.LandmarkOrdering;
import org.agreement_technologies.common.map_landmarks.LandmarkSet;

/**
 * SALandmarkGraph is the single-agent landmark graph (LG) implementation.
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class SALandmarkGraph implements LandmarkGraph {

    private final ArrayList<LandmarkNode> nodes;        // List of landmark nodes
    private final ArrayList<LandmarkOrdering> edges;    // List of orderings between nodes
    private final RPG r;                                // Relaxed planning graph
    private final Boolean[][] matrix;                   // Orderings matrix
    private final ArrayList<Integer> literalNode;       // Maps literals and nodes of the LG
    private final ArrayList<ArrayList<LandmarkFluent>> objs;    // Goal landmarks per RPG level
    private final ArrayList<ArrayList<LandmarkSet>> disjObjs;   // For each disjunction of literals, producer actions of each literal in the disjunction
    private boolean[][] mutexMatrix;                            // Matrix of mutex literals 
    private boolean[][] reasonableOrderings;                    // Matrix of reasonable orderings
    private ArrayList<LandmarkOrdering> reasonableOrderingsList;        // List of reasonable orderings
    private ArrayList<LandmarkOrdering> reasonableOrderingsGoalsList;   // List of reasonable orderings to goals
    private final GroundedTask groundedTask;                            // Gorunded task

    /**
     * Creates a new distributed landmarks graph.
     *
     * @param gt Grounded task
     * @param r Relaxed planning graph
     * @param g List of landmark fluents
     * @since 1.0
     */
    public SALandmarkGraph(GroundedTask gt, RPG r, ArrayList<LandmarkFluent> g) {
        groundedTask = gt;
        //N: Landmark tree nodes
        nodes = new ArrayList<>();
        //E: landmark tree links (necessary orderings)
        edges = new ArrayList<>();
        //A: set of actions that produce a certain literal or disjunction of literals
        ArrayList<LandmarkAction> A;
        //r: RPG associated to the LT
        this.r = r;

        //literalNode maps literals and nodes of the landmark graph
        literalNode = new ArrayList<>(r.getLiterals().size());
        for (int i = 0; i < r.getLiterals().size(); i++) {
            literalNode.add(-1);
        }

        //Initializing objs array
        objs = new ArrayList<>(r.getLitLevels().size());
        for (int i = 0; i < r.getLitLevels().size(); i++) {
            objs.add(new ArrayList<LandmarkFluent>());
        }
        //Initializing disjObjs array
        disjObjs = new ArrayList<>(r.getLitLevels().size());
        for (int i = 0; i < r.getLitLevels().size(); i++) {
            disjObjs.add(new ArrayList<LandmarkSet>());
        }

        //Adding goals to N and objs(lvl), where lvl is the RPG level in which each goal first appears
        for (LandmarkFluent goal : g) {
            nodes.add(new LGNode(goal));
            nodes.get(nodes.size() - 1).setIndex(nodes.size() - 1);
            literalNode.set(goal.getIndex(), nodes.size() - 1);
            objs.get(goal.getLevel()).add(goal);
        }

        //The RPG is explored backwards, beginning from the last literal level
        int level = r.getLitLevels().size() - 1;
        while (level > 0) {
            if (objs.get(level).size() > 0) {
                for (int i = 0; i < objs.get(level).size(); i++) {
                    LandmarkFluent obj = objs.get(level).get(i);
                    //For each literal in objs[level], we calculate the set A of actions that produce the literal
                    A = obj.getProducers();
                    //Once A is calculated, the action processing method is invoked
                    //actionProcessing is only launched if there are producers, that is, if A is not an empty set
                    if (A.size() > 0) {
                        actionProcessing(A, this.nodes.get(this.literalNode.get(obj.getIndex())), level);
                    }
                }
            }
            if (disjObjs.get(level).size() > 0) {
                for (LandmarkSet disjObj : disjObjs.get(level)) {
                    //For each disjunction of literals in disjObjs[level], we calculate A
                    //as the union of the producer actions of each literal in the disjunction
                    A = new ArrayList<>();
                    for (LandmarkFluent obj : disjObj.getElements()) {
                        for (LandmarkAction pa : obj.getProducers()) {
                            if (!A.contains(pa)) {
                                A.add(pa);
                            }
                        }
                    }
                    //Once A is calculated, the action processing method is invoked
                    actionProcessing(A, disjObj.getLTNode(), level);
                }
            }
            level--;
        }

        //Creating the adjacency matrix
        matrix = new Boolean[nodes.size()][nodes.size()];
        for (int i = 0; i < nodes.size(); i++) {
            for (int j = 0; j < nodes.size(); j++) {
                matrix[i][j] = false;
            }
        }
        for (LandmarkOrdering o : edges) {
            matrix[o.getNode1().getIndex()][o.getNode2().getIndex()] = true;
        }

        //Verifying necessary orderings
        postProcessing();
    }

    /**
     * Gets nodes of the LG.
     *
     * @return Arraylist of nodes of the LG
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkNode> getNodes() {
        return nodes;
    }

    /**
     * Postprocessing that verifies the edges of the landmark tree.
     *
     * @since 1.0
     */
    private void postProcessing() {
        //P: Candidate landmarks that precede necessarily a given candidate landmark g
        ArrayList<LandmarkFluent> P = new ArrayList<>();
        //A: Actions that produce a landmark g
        ArrayList<LandmarkAction> A;

        //We analyze all the literal nodes g of the Landmark Tree
        for (int i = 0; i < nodes.size(); i++) {
            //Only single literals are processed
            if (nodes.get(i).isSingleLiteral()) {
                for (int j = 0; j < nodes.size(); j++) {
                    //Check g column of the matrix to find literals l such that l <=n g
                    if (matrix[j][i] == true) {
                        if (nodes.get(j).isSingleLiteral()) {
                            A = getActions(nodes.get(j).getLiteral(), nodes.get(i).getLiteral());
                            //We check if the actions in A are necessary to reach the goals
                            if (!r.verify(A)) {
                                matrix[j][i] = false;
                                //We also remove the ordering from the orderings list
                                for (int ord = 0; ord < edges.size(); ord++) {
                                    LandmarkOrdering e = edges.get(ord);
                                    if (e.getNode1().isSingleLiteral() && e.getNode2().isSingleLiteral()) {
                                        if (e.getNode1().getIndex() == j && e.getNode2().getIndex() == i) {
                                            edges.remove(ord);
                                            ord--;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    /**
     * Calculates the actions that generate the edge l1 -> l2.
     *
     * @param l1 Start landmark
     * @param l2 End landmark
     * @return List of actions that generate the edge l1 -> l2
     * @since 1.0
     */
    private ArrayList<LandmarkAction> getActions(LandmarkFluent l1, LandmarkFluent l2) {
        ArrayList<LandmarkAction> A = new ArrayList<>();

        for (LandmarkAction a : r.getActions()) {
            for (LandmarkFluent pre : a.getPreconditions()) {
                if (l1 == pre && l2.getTotalProducers().contains(a)) {
                    A.add(a);
                }
            }
        }

        return A;
    }

    /**
     * Action processing for LG calculation.
     *
     * @param A List of actions
     * @param g Landmark node
     * @param level Level in the RPG
     * @since 1.0
     */
    private void actionProcessing(ArrayList<LandmarkAction> A, LandmarkNode g, int level) {
        //U: set of grouped literals
        ArrayList<LandmarkSet> D;
        //Calculating I set: preconditions that are common to all the actions in A
        ArrayList<LandmarkFluent> I = new ArrayList<>();
        ArrayList<LandmarkFluent> U = new ArrayList<>();
        int[] common = new int[r.getLiterals().size()];
        for (int i = 0; i < common.length; i++) {
            common[i] = 0;
        }
        for (LandmarkAction a : A) {
            for (LandmarkFluent l : a.getPreconditions()) {
                common[l.getIndex()] = common[l.getIndex()] + 1;
            }
        }
        if (A.size() > 0) {
            for (int i = 0; i < common.length; i++) {
                if (common[i] == A.size()) {
                    I.add(r.getIndexLiterals().get(i));
                } else if (common[i] > 0) {
                    U.add(r.getIndexLiterals().get(i));
                }
            }
        }
        //Exploring candidate landmarks in I
        for (LandmarkFluent p : I) {
            if (r.verify(p)) {
                //Adding landmark p to N, and transition p -> g in E
                //The literal is stored only if it hasn't appeared before (it is ensured by checking literalNode)
                if (literalNode.get(p.getIndex()) == -1) {
                    nodes.add(new LGNode(p));
                    nodes.get(nodes.size() - 1).setIndex(nodes.size() - 1);
                    literalNode.set(p.getIndex(), nodes.size() - 1);
                }
                //Adding a new transition to E
                edges.add(new LMOrdering(nodes.get(literalNode.get(p.getIndex())), g,
                        LandmarkOrdering.NECESSARY));
                if (!objs.get(p.getLevel()).contains(p)) {
                    objs.get(p.getLevel()).add(p);
                }
            }
        }
        //Exploring candidate disjunctive landmarks in D
        D = groupLandmarkSet(U, A);
        for (LandmarkSet d : D) {
            LandmarkSet d1 = findDisjObject(d, level);
            if (d1 == null) {
                nodes.add(new LGNode(d));
                d.setLGNode(nodes.get(nodes.size() - 1));
                nodes.get(nodes.size() - 1).setIndex(nodes.size() - 1);
                edges.add(new LMOrdering(nodes.get(nodes.size() - 1), g,
                        LandmarkOrdering.NECESSARY));
                disjObjs.get(level - 1).add(d);
            } else {
                edges.add(new LMOrdering(d1.getLTNode(), g, LandmarkOrdering.NECESSARY));
            }
        }
    }

    /**
     * Search for a set of landmark fluents.
     *
     * @param u Set of landmark fluents
     * @param level Level in the RPG
     * @return The set of landmark fluents if found; <code>null</code>,
     * otherwise
     * @since 1.0
     */
    private LandmarkSet findDisjObject(LandmarkSet u, int level) {
        for (int i = disjObjs.size() - 1; i >= level - 1; i--) {
            for (LandmarkSet obj : disjObjs.get(i)) {
                if (u.compareTo(obj) == 0) {
                    return obj;
                }
            }
        }
        return null;
    }

    /**
     * Groups a set of landmark fluents according to the actions that generated
     * them.
     *
     * @param u Set of landmark fluents
     * @param A List of landmark actions
     * @return Grouped set of landmark fluents
     * @since 1.0
     */
    private ArrayList<LandmarkSet> groupLandmarkSet(ArrayList<LandmarkFluent> u, ArrayList<LandmarkAction> A) {
        ArrayList<LandmarkSet> U = new ArrayList<>();
        Hashtable<String, LandmarkSet> hashU = new Hashtable<>();

        for (LandmarkFluent l : u) {
            if (hashU.get(l.getVar().getFuctionName()) == null) {
                U.add(new uSet(l));
                hashU.put(l.getVar().getFuctionName(), U.get(U.size() - 1));
            } else {
                hashU.get(l.getVar().getFuctionName()).addElement(l);
            }
        }

        //Verify if the LandmarkSets are correct
        //All the actions must have provided the LandmarkSet with at least a precondition of each type
        int instances, actions;
        boolean visited;
        ArrayList<LandmarkSet> U1 = new ArrayList<>(U.size());
        for (LandmarkSet s : U) {
            instances = 0;
            actions = 0;
            if (s.getElements().size() == 1) {
                continue;
            }
            for (LandmarkAction a : A) {
                visited = false;
                for (LandmarkFluent p : a.getPreconditions()) {
                    if (s.match(p)) {
                        instances++;
                        if (!visited) {
                            actions++;
                            visited = true;
                        }
                    }
                }
            }
            //If there is one instance per action, the LandmarkSet is added to u1
            if (actions == A.size() && instances == A.size()) {
                U1.add(s);
            } else if (actions == A.size() && instances > A.size()) {
                analyzeSet(s, A, U1);
            }
        }

        return U1;
    }

    /**
     * Analizes if a set of landmarks is valid.
     *
     * @param s Set of landmarks
     * @param A List of productor actions
     * @param U1 List of landmark sets
     * @since 1.0
     */
    private void analyzeSet(LandmarkSet s, ArrayList<LandmarkAction> A, ArrayList<LandmarkSet> U1) {
        ArrayList<ArrayList<LandmarkFluent>> literalProducers = new ArrayList<>(A.size());
        int i;
        LandmarkAction a;
        LandmarkSet u;

        for (i = 0; i < A.size(); i++) {
            literalProducers.add(new ArrayList<LandmarkFluent>());
        }

        //Grouping the literals in the set according to the actions that generated them
        for (i = 0; i < A.size(); i++) {
            a = A.get(i);
            for (LandmarkFluent p : a.getPreconditions()) {
                if (p.getVar().getFuctionName().equals(s.identify())
                        && s.getElements().contains(p)) {
                    literalProducers.get(i).add(p);
                }
            }
        }

        ArrayList<LandmarkFluent> actionLiterals;
        LandmarkFluent similar;
        boolean finish = false, add;
        //An LandmarkSet has only one element per action in A
        for (LandmarkFluent l : literalProducers.get(0)) {
            add = true;
            if (finish) {
                break;
            }
            u = new uSet(l);
            for (i = 1; i < literalProducers.size(); i++) {
                if (literalProducers.get(i).isEmpty()) {
                    finish = true;
                    add = false;
                    break;
                }
                actionLiterals = literalProducers.get(i);
                similar = equalParameters(l, actionLiterals);
                if (similar == null) {
                    add = false;
                    break;
                }
                actionLiterals.remove(similar);
                u.addElement(similar);
            }
            if (add) {
                U1.add(u);
            }
        }
    }

    /**
     * Checks the similarity of one fluent to the given ones.
     *
     * @param l Fluent to check
     * @param actionLiterals List of fluents
     * @return The similar fluent found; <code>null</code>, if any similar is
     * found
     * @since 1.0
     */
    private LandmarkFluent equalParameters(LandmarkFluent l, ArrayList<LandmarkFluent> actionLiterals) {
        ArrayList<LandmarkFluent> candidates = new ArrayList<>(actionLiterals.size());
        ArrayList<LandmarkFluent> auxCandidates = new ArrayList<>(actionLiterals.size());
        String p1[] = l.getVar().getParams(), p2[];
        int equalParameters = 0, min;
        boolean equal;
        LandmarkFluent candidate;

        for (LandmarkFluent al : actionLiterals) {
            candidates.add(al);
        }

        //Check if the candidate and the target literal are equal
        for (LandmarkFluent c : candidates) {
            p2 = c.getVar().getParams();
            equal = true;
            for (int i = 0; i < p1.length; i++) {
                if (!p1[i].equals(p2[i])) {
                    equal = false;
                    break;
                }
            }
            if (equal) {
                auxCandidates.add(c);
            }
        }

        //If there is only one candidate left, return it
        if (auxCandidates.size() == 1) {
            return auxCandidates.get(0);
        } else if (auxCandidates.size() > 1) {
            candidates = auxCandidates;
        }
        //If there are no candidates left, apply next criteria        
        min = Integer.MAX_VALUE;
        candidate = candidates.get(0);
        String[] lt, ct;
        int j;
        //Check which candidate has most parameters of the same type than the target literal
        for (LandmarkFluent c : candidates) {
            equalParameters = 0;
            for (int i = 0; i < c.getVar().getParams().length; i++) {
                ct = this.groundedTask.getObjectTypes(c.getVar().getParams()[i]);
                lt = this.groundedTask.getObjectTypes(l.getVar().getParams()[i]);

                for (j = 0; j < ct.length; j++) {
                    if (!ct[j].equals(lt[j])) {
                        break;
                    }
                }

                if (j == ct.length - 1) {
                    equalParameters++;
                }
            }
            if (min > equalParameters) {
                min = equalParameters;
                candidate = c;
            }

        }
        if (equalParameters == 0) {
            return null;
        }
        return candidate;
    }

    /**
     * Gets the node of a given fluent.
     *
     * @param l Fluent
     * @return The container landmark node; <code>null</code>, if not found
     * @since 1.0
     */
    public LandmarkNode getNode(LandmarkFluent l) {
        if (literalNode.get(l.getIndex()) != -1) {
            return nodes.get(literalNode.get(l.getIndex()));
        } else {
            return null;
        }
    }

    /**
     * Checks if there is a reasonable ordering between two nodes.
     *
     * @param n1 First node
     * @param n2 Second node
     * @return <code>true</code>, if the ordering n1 -> n2 exists;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean getReasonableOrdering(LandmarkNode n1, LandmarkNode n2) {
        return reasonableOrderings[n1.getIndex()][n2.getIndex()];
    }

    /**
     * Retrieves reasonable orderings of the LG.
     *
     * @return Arraylist of reasonable landmark orderings
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkOrdering> getReasonableOrderingList() {
        return this.reasonableOrderingsList;
    }

    /**
     * Retrieves reasonable orderings to goals of the LG.
     *
     * @return Arraylist of reasonable landmark orderings to goal nodes
     * @since 1.0
     */
    public ArrayList<LandmarkOrdering> getReasonableGoalOrderingList() {
        return this.reasonableOrderingsGoalsList;
    }

    /**
     * Gets a description of this LG.
     *
     * @return Landmarks graph description
     * @since 1.0
     */
    @Override
    public String toString() {
        String res = "";
        for (LandmarkOrdering o : edges) {
            res += o.getNode1().toString() + " -> " + o.getNode2().toString() + "\n";
        }

        for (int i = 0; i < nodes.size(); i++) {
            for (int j = 0; j < nodes.size(); j++) {
                if (matrix[i][j] == true) {
                    res += 1 + " ";
                } else {
                    res += 0 + " ";
                }
            }
            res += "\n";
        }
        res += "\nMutex matrix: \n";

        for (int i = 0; i < r.getLiterals().size(); i++) {
            for (int j = 0; j < r.getLiterals().size(); j++) {
                if (mutexMatrix[i][j] == true) {
                    res += r.getLiterals().get(i) + " <-> " + r.getLiterals().get(j) + "\n";
                }
            }
        }

        res += "\nReasonable orderings: \n";

        for (int i = 0; i < nodes.size(); i++) {
            for (int j = 0; j < nodes.size(); j++) {
                if (reasonableOrderings[i][j] == true) {
                    res += nodes.get(i) + " -> " + nodes.get(j) + "\n";
                }
            }
        }

        return res;
    }

    /**
     * Retrieves necessary orderings to goals of the LG.
     *
     * @return Arraylist of necessary landmark orderings to goal nodes
     * @since 1.0
     */
    public ArrayList<LandmarkOrdering> getNeccessaryGoalOrderingList() {
        ArrayList<LandmarkOrdering> res = new ArrayList<>();
        for (LandmarkOrdering o : edges) {
            if (o.getNode1().isSingleLiteral() && o.getNode2().isSingleLiteral()) {
                if (o.getNode1().getLiteral().isGoal() && o.getNode2().getLiteral().isGoal()) {
                    res.add(o);
                }
            }
        }
        return res;
    }

    /**
     * Retrieves necessary orderings of the LG.
     *
     * @return Arraylist of necessary landmark orderings
     * @since 1.0
     */
    @Override
    public ArrayList<LandmarkOrdering> getNeccessaryOrderingList() {
        return edges;
    }

    /**
     * Gets number of landmark nodes in the LG.
     *
     * @return Number of landmark nodes in the LG
     * @since 1.0
     */
    @Override
    public int numGlobalNodes() {
        return nodes.size();
    }

    /**
     * Gets current number of nodes in the LG (during LG construction).
     *
     * @return Current number of landmark nodes in the LG
     * @since 1.0
     */
    @Override
    public int numTotalNodes() {
        return nodes.size();
    }
}
