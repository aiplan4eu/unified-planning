from typing import List, Dict
import networkx as nx
import unified_planning as up
from unified_planning.plans.time_triggered_plan import _absolute_time
from unified_planning.plans.time_triggered_plan import *
from unified_planning.plans.plan import ActionInstance
from unified_planning.model.mixins.timed_conds_effs import *
from unified_planning.plans.sequential_plan import SequentialPlan
from unified_planning.plans.partial_order_plan import PartialOrderPlan
from unified_planning.model.action import Action


def is_time_in_interv(
    start: Fraction,
    duration: Fraction,
    timing: "up.model.timing.Timing",
    interval: "up.model.timing.TimeInterval",
) -> bool:
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
        self.seq_plan: SequentialPlan
        self.partial_order_plan: "up.plans.partial_order_plan.PartialOrderPlan"

    def sort_condition(
        self,
        start: Fraction,
        duration: Fraction,
        conditions: Dict["up.model.timing.TimeInterval", List["up.model.fnode.FNode"]],
        effect: Tuple["up.model.timing.Timing", List["up.model.effect.Effect"]],
    ) -> Tuple["up.model.timing.Timing", List["up.model.fnode.FNode"]]:
        """
        From the dict of condition get all conditions for the specific timepoint from the couple timepoint effect.
        Return the coresponding timepoint conditions couple.
        """
        time_point = effect[0]
        cond_result = []
        for time_interval, condition in conditions.items():
            if is_time_in_interv(
                start, duration, time_point, time_interval
            ):  # Time point in interval
                cond_result += condition
        result = (time_point, cond_result)
        return result

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
        Return table : For each action (the tuple) and each timepoint of this action the couple conditions effects"""
        for start, ai, duration in self.ttp.timed_actions:
            action = ai.action
            action_cpl = (start, ai, duration)
            self.table[action_cpl] = {}
            assert isinstance(action, DurativeAction)
            if duration is None:
                assert isinstance(
                    ai.action, InstantaneousAction
                ), "Error, None duration specified for non InstantaneousAction"
                continue
            for effect_time, effects in action.effects.items():
                pconditions = self.sort_condition(
                    start, duration, action.conditions, (effect_time, effects)
                )
                self.table[action_cpl].update({effect_time: (pconditions[1], effects)})
        return self.table

    def table_to_events(self) -> List[Tuple[Fraction, InstantaneousAction]]:
        """
        Return a list where each time is paired with an Instantaneous Action.
        Each Instantaneous Action is created from preconditions and effects from get_table_event()
        """
        self.get_table_event()
        for action_cpl, c_e_dict in self.table.items():
            start = action_cpl[0]
            duration = action_cpl[2]
            action = action_cpl[1]
            if duration is None:
                assert isinstance(
                    action.action, InstantaneousAction
                ), "Error, None duration specified for non InstantaneousAction"
                continue
            for time_pt, cond_eff_couple in c_e_dict.items():

                time = _absolute_time(time_pt, start, duration)
                inst_action = InstantaneousAction(str(action) + str(time_pt))

                # set condition and effect to each instant action
                if len(cond_eff_couple[0]) > 0:
                    for cond in cond_eff_couple[0]:
                        inst_action.add_precondition(cond)

                if len(cond_eff_couple[1]) > 0:
                    for effect in cond_eff_couple[1]:
                        inst_action.effects.append(effect)

                self.events += [(time, inst_action)]
        return self.events

    def sort_events(self) -> List[Tuple[Fraction, InstantaneousAction]]:
        self.table_to_events()
        print("BEFORE")
        for tim, act in self.events:
            print("%s: %s" % (float(tim), act._name))

        self.events_sorted = sorted(self.events, key=lambda acts: acts[0])

        print("\r\nAFTER")
        for tim, act in self.events_sorted:
            print("%s: %s" % (float(tim), act._name))
        return self.events_sorted

    def events_to_partial_order_plan(self):
        self.sort_events()
        list_act = [ActionInstance(i[1]) for i in self.events_sorted]
        seqplan = SequentialPlan(list_act)
        print("\r\nseq plan", seqplan)
        partial_order_plan = seqplan._to_partial_order_plan(self.problem)
        self.partial_order_plan = partial_order_plan
        print("\r\npartial order plan ", partial_order_plan)
        return partial_order_plan

    def partial_order_plan_to_stn(self) -> nx.DiGraph:
        return

    def run(self):
        # partial order plan to STN
        self.events_to_partial_order_plan()
        self.partial_order_plan_to_stn()
        return
