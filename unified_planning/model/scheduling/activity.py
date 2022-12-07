from typing import Optional

from unified_planning.environment import get_env
from unified_planning.model import Timepoint, Timing, TimepointKind, Fluent, Type, Parameter
from unified_planning.model.scheduling.chronicle import Chronicle


class Activity(Chronicle):
    """Activity is essentially an interval with start and end timing that facilitates defining constraints in the
    associated SchedulingProblem"""

    def __init__(self, name: str, duration: Optional[int]):
        super().__init__(name) # TODO
        start_tp = Timepoint(TimepointKind.START, container=name)
        end_tp = Timepoint(TimepointKind.END, container=name)
        self._start = Timing(0, start_tp)
        self._end = Timing(0, end_tp)
        if duration is not None:
            self.set_fixed_duration(duration)

    @property
    def start(self) -> Timing:
        return self._start

    @property
    def end(self) -> Timing:
        return self._end

    def uses(self, resource: Fluent, amount: int = 1):
        self.add_decrease_effect(self.start, resource, amount)
        self.add_increase_effect(self.end, resource, amount)

    def add_parameter(self, name: str, tpe: Type) -> Parameter:
        assert ':' not in name, f"Usage of ':' is forbidden in names: {name}"
        scoped_name = f"{self.name}:{name}"
        if name in self._parameters:
            raise ValueError(f"Name '{name}' already used in activity '{self.name}'")
        param = Parameter(scoped_name, tpe)
        self._parameters[name] = param
        return param

    def set_release_date(self, date: int):
        self.add_constraint(get_env().expression_manager.LE(date, self._start))
