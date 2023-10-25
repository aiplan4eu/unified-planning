from typing import List, Dict
import networkx as nx
import re
import copy
import unified_planning as up
from unified_planning.plans.time_triggered_plan import _absolute_time
from unified_planning.plans.time_triggered_plan import *
from unified_planning.plans.plan import ActionInstance
from unified_planning.model.mixins.timed_conds_effs import *
from unified_planning.plans.sequential_plan import SequentialPlan
from unified_planning.plans.partial_order_plan import PartialOrderPlan
from unified_planning.plot.plan_plot import plot_partial_order_plan

EPSILON = Fraction(1, 1000)
MAX_TIME = Fraction(5000, 1)


def is_time_in_interv(
    start: Fraction,
    duration: Fraction,
    timing: "up.model.timing.Timing",
    interval: "up.model.timing.TimeInterval",
) -> bool:
    """
    Return if the timepoint is in the interval given.
    """
    time_pt = _absolute_time(timing, start=start, duration=duration)
    upper_time = _absolute_time(interval._upper, start=start, duration=duration)
    lower_time = _absolute_time(interval._lower, start=start, duration=duration)
    if (time_pt > lower_time if interval._is_left_open else time_pt >= lower_time) and (
        time_pt < upper_time if interval._is_right_open else time_pt <= upper_time
    ):
        return True
    return False


class TTP_to_STN:

    """Create a STN from a TimeTriggeredPlan"""

    def __init__(
        self, plan: TimeTriggeredPlan, problem: "up.model.mixins.ObjectsSetMixin"
    ):
        self.ttp = plan
        self.problem = problem
        self.table: Dict[
            Tuple[Fraction, ActionInstance, Optional[Fraction]],
            Dict[
                "up.model.timing.Timing",
                Tuple[List["up.model.fnode.FNode"], List["up.model.effect.Effect"]],
            ],
        ] = {}
        self.events: List[Tuple[Fraction, InstantaneousAction]] = []
        self.events_sorted: List[Tuple[Fraction, InstantaneousAction]] = []
        self.act_to_time_map: Dict[str, Fraction] = {}
        self.ai_act_map: Dict[str, ActionInstance] = {}
        self.action_to_pieces: List[
            Tuple[ActionInstance, Dict[str, InstantaneousAction]]
        ] = []
        self.seq_plan: SequentialPlan
        self.partial_order_plan: PartialOrderPlan
        self.stn: nx.DiGraph

    def get_timepoint_conditions(
        self,
        start: Fraction,
        duration: Fraction,
        conditions: Dict["up.model.timing.TimeInterval", List["up.model.fnode.FNode"]],
        effect_timing: "up.model.timing.Timing",
    ) -> List["up.model.fnode.FNode"]:
        """
        From the dict of condition get all conditions for the specific timepoint from the couple timepoint effect.
        Return the corresponding timepoint conditions couple.
        """
        cond_result = []
        for time_interval, cond_list in conditions.items():
            if is_time_in_interv(start, duration, effect_timing, time_interval):
                cond_result += cond_list
        return cond_result

    def get_table_event(
        self,
    ) -> Dict[
        Tuple[Fraction, ActionInstance, Optional[Fraction]],
        Dict[
            "up.model.timing.Timing",
            Tuple[List["up.model.fnode.FNode"], List["up.model.effect.Effect"]],
        ],
    ]:
        """
        Return table : For each action (the tuple) and each timepoint of this action the couple conditions effects
        """
        for start, ai, duration in self.ttp.timed_actions:
            action = ai.action
            action_cpl = (start, ai, duration)
            assert action_cpl not in self.table
            timing_to_cond_effects: Dict[
                "up.model.timing.Timing",
                Tuple[List["up.model.fnode.FNode"], List["up.model.effect.Effect"]],
            ] = self.table.setdefault(action_cpl, {})
            if duration is None:
                assert isinstance(
                    ai.action, InstantaneousAction
                ), "Error, None duration specified for non InstantaneousAction"
                continue
            assert isinstance(
                action, DurativeAction
            ), "Error, Action is not a DurativeAction nor a InstantaneousAction"
            for effect_time, effects in action.effects.items():
                pconditions = self.get_timepoint_conditions(
                    start, duration, action.conditions, effect_time
                )
                timing_to_cond_effects[effect_time] = (pconditions, effects)
        return self.table

    def table_to_events(self) -> List[Tuple[Fraction, InstantaneousAction]]:
        """
        Return a list where each time is paired with an Instantaneous Action.
        Each Instantaneous Action is created from preconditions and effects from get_table_event()
        """
        self.get_table_event()

        for (start, ai, duration), c_e_dict in self.table.items():
            pieces = {}
            if duration is None:
                assert isinstance(
                    ai.action, InstantaneousAction
                ), "Error, None duration specified for non InstantaneousAction"
                inst_action = InstantaneousAction(str(ai) + str(start))
                self.events.append((start, inst_action))
                pieces.update({"start": inst_action})
                continue
            for time_pt, (conditions, effects) in c_e_dict.items():
                time = _absolute_time(time_pt, start, duration)
                inst_action = InstantaneousAction(str(ai) + str(time_pt))

                for cond in conditions:
                    inst_action.add_precondition(cond)
                for effect in effects:
                    inst_action._add_effect_instance(effect)
                self.events.append((time, inst_action))
                pieces.update({str(time_pt): inst_action})
            self.action_to_pieces.append((ai, pieces))
        return self.events

    def sort_events(self) -> List[Tuple[Fraction, InstantaneousAction]]:
        """
        Return the table of instant action sorted by time.
        """
        self.table_to_events()

        self.events_sorted = sorted(self.events, key=lambda acts: acts[0])
        self.act_to_time_map = dict(
            [(value.name, key) for key, value in self.events_sorted]
        )

        return self.events_sorted

    def events_to_partial_order_plan(self):
        """
        Return the partial order plan from the list of events sorted.
        """
        self.sort_events()
        list_act = [ActionInstance(i[1]) for i in self.events_sorted]
        self.ai_act_map = dict([(ai.action.name, ai) for ai in list_act])
        self.seq_plan = SequentialPlan(list_act)
        partial_order_plan = self.seq_plan._to_partial_order_plan(self.problem)
        self.partial_order_plan = partial_order_plan
        return partial_order_plan

    def partial_order_plan_to_stn(self) -> nx.DiGraph:
        """
        Stn with Start and End nodes
        Return the stn from the partial order plan.
        """
        graph = self.partial_order_plan._graph

        for ai_current, l_next_ai in self.partial_order_plan.get_adjacency_list.items():
            ai_current_time = self.act_to_time_map[ai_current.action.name]
            for ai_next in l_next_ai:
                name_current = re.findall(
                    r"(.+)(start|end) *(\+|\-)* *(\d*)", str(ai_current.action._name)
                )
                name_next = re.findall(
                    r"(.+)(start|end) *(\+|\-)* *(\d*)", str(ai_next.action._name)
                )
                # Time between two differents actions depend on epsilon
                if name_current[0][0] != name_next[0][0]:
                    graph[ai_current][ai_next]["interval"] = [
                        EPSILON,
                        MAX_TIME,
                    ]
                else:
                    ai_next_time = self.act_to_time_map[ai_next.action.name]
                    time_edge = ai_next_time - ai_current_time
                    graph[ai_current][ai_next]["interval"] = [time_edge, time_edge]

        # Add edges between ActionStart and ActionEnd
        for action, pieces in self.action_to_pieces:
            act_start, act_end = pieces["start"], pieces["end"]
            ai_start, ai_end = (
                self.ai_act_map[act_start.name],
                self.ai_act_map[act_end.name],
            )
            graph.add_edge(ai_start, ai_end)
            interval = (
                self.act_to_time_map[act_end.name]
                - self.act_to_time_map[act_start.name]
            )
            graph[ai_start][ai_end]["interval"] = [interval, interval]

        # Add start and end nodes

        start = ActionInstance(InstantaneousAction("START"))
        end = ActionInstance(InstantaneousAction("END"))
        graph.add_node(start)
        graph.add_node(end)

        # Add edge between start and first node
        graph.add_edge(
            start,
            list(self.partial_order_plan.get_adjacency_list.keys())[0],
            interval=[Fraction(0, 1), Fraction(0, 1)],
        )
        # Add edge between end and last node
        graph.add_edge(
            [
                item
                for item in list(self.partial_order_plan.get_adjacency_list.keys())[
                    ::-1
                ]
                if item.action._name != "START" and item.action._name != "END"
            ][0],
            end,
            interval=[Fraction(0, 1), Fraction(0, 1)],
        )

        self.stn = graph
        return graph

    def stn_clean(self, graph: nx.DiGraph):
        """
        Delete nodes of actions in between start and end. And create new edges from edges deleted.
        It clean the graph given in place.
        """
        nodes_list = list(graph.nodes(data=True))

        to_jump = []
        for node, data in nodes_list:
            if node in to_jump:
                continue
            neighbors_node = copy.copy(graph.neighbors(node))
            for next_node in neighbors_node:
                if bool(
                    re.match("(.*)(end|start) (\+|\-) [0-9]+$", next_node.action._name)
                ):
                    neighbors_next_node = copy.copy(graph.neighbors(next_node))
                    for next_next_node in neighbors_next_node:
                        if next_next_node == node:
                            continue
                        graph.add_edge(node, next_next_node)
                        a = graph[node][next_node]["interval"]
                        b = graph[next_node][next_next_node]["interval"]
                        graph[node][next_next_node]["interval"] = [
                            a[0] + b[0],
                            a[1] + b[1],
                        ]
                        graph.remove_edge(next_node, next_next_node)

                    graph.remove_edge(node, next_node)
                    graph.remove_node(next_node)
                    to_jump += [item[0] for item in nodes_list if item[0] == next_node]

    def run(self):
        # partial order plan to STN
        self.events_to_partial_order_plan()
        graph = self.partial_order_plan_to_stn()
        self.stn_clean(graph)
        return graph
