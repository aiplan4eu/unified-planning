from typing import List
import unified_planning as up
from unified_planning.plans.time_triggered_plan import _absolute_time
from unified_planning.plans.time_triggered_plan import *


def is_time_in_interv(
    start,
    duration,
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
        self.table = {}
        self.events = {}

    def sort_condition(
        self,
        start,
        duration,
        conditions: {"up.model.timing.TimeInterval", List["up.model.fnode.FNode"]},
        effect: ("up.model.timing.Timing", List["up.model.effect.Effect"]),
    ) -> ("up.model.timing.Timing", List["up.model.fnode.FNode"]):
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
    ) -> {
        DurativeAction: {
            "up.model.timing.Timing": ("up.model.fnode.FNode", "up.model.effect.Effect")
        }
    }:
        """
        Return table : For each action (the tuple) and each timepoint of this action the couple conditions effects"""
        for start, action, duration in self.ttp.timed_actions:
            action_cpl = (start, action, duration)
            self.table[action_cpl] = {}
            for effect_time, effects in action.action._effects.items():
                pconditions = self.sort_condition(
                    start, duration, action.action._conditions, (effect_time, effects)
                )
                self.table[action_cpl].update({effect_time: (pconditions[1], effects)})

    def table_to_events(self) -> {"up.model.timing.Timepoint": InstantaneousAction}:
        """
        Return a list where each time is paired with an Instantaneous Action.
        Each Instantaneous Action is created from preconditions and effects from get_table_event()
        """
        self.get_table_event()
        for action_cpl, c_e_dict in self.table.items():
            start = action_cpl[0]
            duration = action_cpl[2]
            action = action_cpl[1]

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

                self.events.update({time: inst_action})

    def sort_events(self) -> {"up.model.timing.Timepoint": InstantaneousAction}:
        self.table_to_events()
        return self.events

    def events_to_partial_order_plan(self):
        self.sort_events()
        return

    def run(self):
        self.events_to_partial_order_plan()
        # partial order plan to STN
        return
