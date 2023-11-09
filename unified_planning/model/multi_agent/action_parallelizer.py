import unified_planning as up
from unified_planning.engines.sequential_simulator import (
    UPSequentialSimulator as SequentialSimulator,
)
import unified_planning.plans as plans
from typing import List, Dict


class Parallelizer:
    def __init__(
        self,
        _problem: "up.model.problem.Problem",
    ) -> None:
        self.problem: "up.model.problem.Problem" = _problem

    # generates the adjacency lists needed by 'GeneratePOP' to generate the final POP plan
    def Update_POPdict(self, POP_dict, GAMMA, lastAct_ins):
        if lastAct_ins is not None:
            POP_dict[lastAct_ins] = [GAMMA[0]]  # the start action
        lenG = len(GAMMA)

        if lenG == 2:
            POP_dict[GAMMA[0]] = [
                GAMMA[1]
            ]  # the endAction is in the adjacency list of the startAction

        if lenG > 2:  # at least one action was parallelized to the start action
            if lastAct_ins is not None:
                if POP_dict.get(lastAct_ins) is None:
                    POP_dict[lastAct_ins] = [GAMMA[1]]
                else:
                    POP_dict[lastAct_ins].append(GAMMA[1])
            for i in range(1, lenG - 1):
                POP_dict[GAMMA[i]] = [GAMMA[i + 1]]
            POP_dict[GAMMA[0]] = [GAMMA[lenG - 1]]

        lastAct_ins = GAMMA[lenG - 1]

        return POP_dict, lastAct_ins

    # -------------------------------------------------------------------------------------------------------#

    # generates the POP of the parallelized plan
    def GeneratePOP(self, listActs):
        POP = plans.PartialOrderPlan(listActs)

        return POP

    # -------------------------------------------------------------------------------------------------------#

    # writes in a file .plan the resulting parallelized plan
    def UpdateParallelizedPlan(self, lista, f):
        L = len(lista)

        if self.actionMovement in str(lista[0]) and L > 1:
            stringedAction = str(lista[0])
            f.write(stringedAction + "; \n")

        if L == 0:
            return

        # in 'list' there is only one action, that is or: an atomic action or a start action that cannot be parallelized
        elif L == 1:
            stringedAction = str(lista[0])
            f.write(stringedAction + "; \n")

        # I only have a 'start' and an 'end' action
        elif L == 2:
            for act in lista:
                stringedAction = str(act)
                f.write(stringedAction + "; \n")

        # in the case something has been parallelized to a start action
        else:
            stringedAction = str(lista[0])
            f.write("{" + stringedAction + "}||{")
            for act in lista[1 : L - 1]:
                stringedAction = str(act)
                f.write(stringedAction + "; ")
            f.write("} \n")
            stringedAction = str(lista[L - 1])
            f.write(stringedAction + "; \n")

    # -------------------------------------------------------------------------------------------------------#

    # check if by adding a subplan of 'goto' actions, another action becomes parallelizable
    def defineAndSolveSubproblem(self, new_goals, curren_state):
        curr_state = curren_state
        problem2 = self.problem.clone()
        initial_values = self.problem.initial_values

        # I set the initial values of prob2 equals to the current state of the simulation
        for fluent in initial_values:
            problem2.set_initial_value(fluent, curr_state.get_value(fluent))

        # I set the goal of prob2 equal to the unsatisfied conditions
        problem2.clear_goals()
        for necessaryPrecondition in new_goals:
            problem2.add_goal(necessaryPrecondition)

        with OneshotPlanner(name="fast-downward") as planner:
            assert planner.supports(problem2.kind)
            out_plan2 = planner.solve(problem2).plan

        foundSubplan = False
        # check the plan is made up pf all movement actions
        if out_plan2 is not None:
            foundSubplan = True
            contatoreAz = 0
            contatoreGoto = 0
            for act in out_plan2.actions:
                contatoreAz += 1
                curr_state = self.sim.apply(curr_state, act)
                if self.actionMovement in act.action.name:
                    contatoreGoto += 1
            if (
                contatoreGoto != contatoreAz
            ):  # not only movement actions in the subplan --> I do not return the subplan
                return curren_state, None, False

        return curr_state, out_plan2, foundSubplan

    # -------------------------------------------------------------------------------------------------------#

    # initial check that verifies if a certain action B is parallelizable to 'start_actionA'; that is if B is
    # applicable even if A is terminated.
    def initialCheck_applicability(
        self, actCercasi, actStart, actEnd, current_stateOriginal, current_stateBB
    ):
        if current_stateBB == []:
            curr_state = current_stateOriginal
        else:
            curr_state = current_stateBB

        curr_state = self.sim.apply(curr_state, actCercasi)
        applicability = self.sim.is_applicable(curr_state, actStart)
        if applicability:
            curr_state = self.sim.apply(curr_state, actStart)
            applicability = self.sim.is_applicable(curr_state, actEnd)

        return applicability

    # -------------------------------------------------------------------------------------------------------#

    # I search for the first action to be parallelized to the start_action
    def findFirstParallelizableAction(
        self, i, j, durativeAct, start_action, end_action, current_state2, applicability
    ):
        while j < self.len_plan and not (applicability):
            cercasi_action = self.seq_plan.actions[j]

            # it isn't possible to parallelize a start_action to another one
            if durativeAct in cercasi_action.action.name:
                j += 1
                continue

            current_stateBB = []
            firstParalActs_list = []
            appl = self.sim.is_applicable(current_state2, cercasi_action)
            if not (appl):
                unsat_preconds = self.sim.get_unsatisfied_conditions(
                    current_state2, cercasi_action
                )[0]
                current_stateBB, subplan, foundSubplan = self.defineAndSolveSubproblem(
                    unsat_preconds, current_state2
                )
                if not foundSubplan:
                    j += 1
                    continue
                else:
                    state = current_state2
                    for act in subplan.actions:
                        applicability = self.initialCheck_applicability(
                            act, start_action, end_action, state, []
                        )
                        if applicability:
                            state = self.sim.apply(state, act)
                            appl = True
                        else:
                            appl = False
                            break
                if appl:
                    for act in subplan.actions:
                        firstParalActs_list.append(act)
            else:
                appl = True
            # check the applicability of the first action we want to parallelize, even if the 'start_action' is still ongoing
            if appl:
                applicability = self.initialCheck_applicability(
                    cercasi_action,
                    start_action,
                    end_action,
                    current_state2,
                    current_stateBB,
                )

            j += 1
        j -= 1

        return cercasi_action, j, applicability, current_state2, firstParalActs_list

    # -----------------------------------------------------------------------------------------------------------------------------

    # application of the first parallelizable action to the current state
    def applyFirstParallelizzableAction(
        self,
        cercasi_action,
        j,
        current_state,
        GAMMAbis,
        list_acts_TOinsert,
        firstParalActs_list,
    ):
        current_stateBIS = current_state
        for act in firstParalActs_list:
            current_stateBIS = self.sim.apply(current_stateBIS, act)
            GAMMAbis.append(act)
        current_stateBIS = self.sim.apply(current_stateBIS, cercasi_action)
        GAMMAbis.append(cercasi_action)
        list_acts_TOinsert.append(j)

        return current_stateBIS, GAMMAbis, list_acts_TOinsert

    # ------------------------------------------------------------------------------------------------------------------------------

    # application of end_action to the current state. It is done after the parallelization of a sequence to start_action was terminated
    def applyEndAction(
        self,
        end_action,
        i,
        start_action,
        GAMMAbis,
        list_acts_TOinsert,
        current_stateBIS,
    ):
        GAMMAbis.append(end_action)
        list_acts_TOinsert.append(i + 1)
        current_stateBIS = self.sim.apply(current_stateBIS, start_action)
        current_stateBIS = self.sim.apply(current_stateBIS, end_action)

        return GAMMAbis, list_acts_TOinsert, current_stateBIS

    # -----------------------------------------------------------------------------------------------------------------------------

    # after having parallelied a first action, this function searches for the rest of actions
    def findRestSequenceToParallelize(
        self, j, current_stateBIS, GAMMAbis, list_acts_TOinsert
    ):
        w = 1  # one action has already been parallelized
        while w < self.N_ACTIONStoPARALLELIZE and j + w < self.len_plan:
            # j = index of the first action parallelized. It can be different from i+2
            o = j + w
            act = self.seq_plan.actions[o]
            appl = False
            if "start" in act.action.name:
                break
            else:
                appl = self.sim.is_applicable(current_stateBIS, act)

            if not (appl):
                break
            GAMMAbis.append(act)
            list_acts_TOinsert.append(o)
            current_stateBIS = self.sim.apply(current_stateBIS, act)
            w += 1

        return current_stateBIS, GAMMAbis, list_acts_TOinsert, w

    # -----------------------------------------------------------------------------------------------------------------------------

    # check the applicability of the sequence of actions found to be parallelized
    def checkInRange(self, m, n, current_stateCHECK, applicab):
        for z in range(m, n):
            act_z = self.seq_plan.actions[z]
            applicab = self.sim.is_applicable(current_stateCHECK, act_z)

            if not (applicab):
                unsat_preconds = self.sim.get_unsatisfied_conditions(
                    current_stateCHECK, act_z
                )[0]
                (
                    current_stateCHECK,
                    subplan,
                    foundSubplan,
                ) = self.defineAndSolveSubproblem(unsat_preconds, current_stateCHECK)
                applicab = self.sim.is_applicable(current_stateCHECK, act_z)

            if applicab:
                current_stateCHECK = self.sim.apply(current_stateCHECK, act_z)
            else:
                break

        return applicab, current_stateCHECK

    # --------------------------------------------------------------------------------------------------------------------

    # changing the order of appliance of some actions, we have to check that the rest of the sequential plan remains applicable
    def checkApplicability_restOfActions(self, current_stateBIS, i, j, w):
        applicability = True
        current_stateCHECK = current_stateBIS
        if i + 2 < j:
            applicability, current_stateCHECK = self.checkInRange(
                i + 2, j, current_stateCHECK, applicability
            )

        if applicability and j + w < self.len_plan:
            applicability, current_stateCHECK = self.checkInRange(
                j + w, self.len_plan, current_stateCHECK, applicability
            )

        return applicability

    # --------------------------------------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------------------------------------

    def parallelize(
        self,
        seq_plan,
        LenSeq_daParallelizzare,
        pathFile,
        durativeAct,
        fluentWhere,
        actionMovement,
    ):  # problem, ORA PASSATO ALLA INIT
        # parameters:
        # - problem = the compiled problem
        # - seq_plan = sequential plan solution found through a classical solver
        # - LenSeq_daParallelizzare = maximum length of the sequence we want to parallelize to a start-end action
        # - pathFile = file path on which we want to write the final parallelized plan
        # - durativeAct = action that we want to parallelize to a sequence of other actions.
        #                 Usually it is an action that takes a lot of time to be executed
        # - actionMovement = name of the action of your planning formalism that implies a movement of an agent between two locations
        #
        # output:
        # - POP_adjList : adjacency list of the parallelized plan. Used for generating POP_plan
        # - POP_plan : final resuling Partial Order Plan

        # self.problem = problem
        self.seq_plan = seq_plan
        self.len_plan = len(
            self.seq_plan.actions
        )  # number of actions in the sequential plan
        self.sim = SequentialSimulator(self.problem)
        self.current_state = (
            self.sim.get_initial_state()
        )  # Initial value of the fluents of the problem
        self.actionMovement = actionMovement
        self.list_actions_inserted: List[
            int
        ] = (
            []
        )  # actions of the sequential plan, already inserted in the parallelized plan
        self.N_ACTIONStoPARALLELIZE = LenSeq_daParallelizzare

        f = open(
            pathFile, "w"
        )  # Sequential file .plan where the parallelized plan will be written

        # needed in order to create the POP structure
        lastAct_ins = None
        POP_adjList: Dict[up.model.action.Action, up.model.action.Action] = {}

        i = 0
        while i < self.len_plan:
            GAMMA = (
                []
            )  # actions that will be inserted in the parallelized plan at the end of the curret iteration
            curr_action = seq_plan.actions[i]  # the i-th action of the sequential plan

            # case 1: action already inserted in the output parallelizedd plan
            if i in self.list_actions_inserted:
                i += 1
                continue

            # ------------------- AZIONE ATOMICA -----------------------
            # case 2: atomic action
            # I simply write the action in the plan and simulate the respective event.
            if "start" not in curr_action.action.name:
                firstParalActs_list = []

                if not (self.sim.is_applicable(self.current_state, curr_action)):
                    unsat_preconds = self.sim.get_unsatisfied_conditions(
                        self.current_state, curr_action
                    )[0]
                    (
                        self.current_state,
                        subplan,
                        foundSubplan,
                    ) = self.defineAndSolveSubproblem(
                        unsat_preconds, self.current_state
                    )
                    for act in subplan.actions:
                        firstParalActs_list.append(act)

                self.current_state = self.sim.apply(self.current_state, curr_action)

                firstParalActs_list.append(curr_action)
                for act in firstParalActs_list:
                    GAMMA.append(act)

                self.list_actions_inserted.append(i)
                i += 1

            # durative action: a start action
            else:
                start_action = curr_action  # curr_action is the 'startDurative' action
                GAMMA.append(start_action)
                self.list_actions_inserted.append(i)
                end_action = seq_plan.actions[i + 1]

                applicability = False
                j = (
                    i + 2
                )  # +2 because I have to skip the 'start durative action' and the 'end durative action'
                while j < self.len_plan and not (applicability):
                    (
                        cercasi_action,
                        j,
                        applicability,
                        current_stateBIS,
                        firstParalActs_list,
                    ) = self.findFirstParallelizableAction(
                        i,
                        j,
                        durativeAct,
                        start_action,
                        end_action,
                        self.current_state,
                        applicability,
                    )
                    # j is the index of the first parallelizable action, if one exists

                    if applicability:
                        list_acts_TOinsert: List[int] = []
                        GAMMAbis = GAMMA.copy()

                        (
                            current_stateBIS,
                            GAMMAbis,
                            list_acts_TOinsert,
                        ) = self.applyFirstParallelizzableAction(
                            cercasi_action,
                            j,
                            current_stateBIS,
                            GAMMAbis,
                            list_acts_TOinsert,
                            firstParalActs_list,
                        )

                        (
                            current_stateBIS,
                            GAMMAbis,
                            list_acts_TOinsert,
                            w,
                        ) = self.findRestSequenceToParallelize(
                            j, current_stateBIS, GAMMAbis, list_acts_TOinsert
                        )

                        if applicability:
                            (
                                GAMMAbis,
                                list_acts_TOinsert,
                                current_stateBIS,
                            ) = self.applyEndAction(
                                end_action,
                                i,
                                start_action,
                                GAMMAbis,
                                list_acts_TOinsert,
                                current_stateBIS,
                            )

                            applicability = self.checkApplicability_restOfActions(
                                current_stateBIS, i, j, w
                            )

                    j += 1
                # end of the while used to search for a sequence of actions to be parallelized to 'start action'

                if applicability:
                    self.current_state = current_stateBIS
                    GAMMA = GAMMAbis
                    for k in list_acts_TOinsert:
                        self.list_actions_inserted.append(k)

                else:
                    self.current_state = self.sim.apply(
                        self.current_state, start_action
                    )

                i += 1

            # update of the .plan file and of the POP
            self.UpdateParallelizedPlan(GAMMA, f)
            POP_adjList, lastAct_ins = self.Update_POPdict(
                POP_adjList, GAMMA, lastAct_ins
            )

            # end of the main while

        POP_plan = self.GeneratePOP(POP_adjList)
        f.close()

        return POP_adjList, POP_plan
