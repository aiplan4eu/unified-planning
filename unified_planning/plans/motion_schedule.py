from unified_planning.plans.schedule import Schedule, Variable, Value
from unified_planning.model.scheduling import Activity
from unified_planning.environment import Environment
from unified_planning.model.motion.activity import MotionActivity
from unified_planning.model.motion.constraint import MotionConstraint
from typing import Optional, Tuple, List, Dict


class MotionSchedule(Schedule):
    def __init__(
        self,
        activities: Optional[List[Activity]] = None,
        assignment: Optional[Dict[Variable, Value]] = None,
        motion_paths: Dict[
            Tuple[MotionActivity, MotionConstraint], List[Tuple[float, ...]]
        ] = {},
        environment: Optional[Environment] = None,
    ):
        super().__init__(activities, assignment, environment)
        self._motion_paths = motion_paths

    @property
    def motion_paths(
        self,
    ) -> Dict[Tuple[MotionActivity, MotionConstraint], List[Tuple[float, ...]]]:
        return self._motion_paths

    @motion_paths.setter
    def motion_paths(
        self,
        motion_paths: Dict[
            Tuple[MotionActivity, MotionConstraint], List[Tuple[float, ...]]
        ],
    ):
        self._motion_paths = motion_paths
