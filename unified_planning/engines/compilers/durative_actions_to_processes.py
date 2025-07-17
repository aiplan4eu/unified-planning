# Copyright 2021-2023 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from itertools import chain
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    Problem,
    ProblemKind,
    Fluent,
    Action,
    InstantaneousAction,
    DurativeAction,
    Process,
    Event,
    Timing,
    TimeInterval,
)
from unified_planning.model.fnode import FNode
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.model.fluent import get_all_fluent_exp
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
    replace_action,
)
from typing import Dict, Iterator, Optional, OrderedDict, Tuple, List, Union
from functools import partial
from unified_planning.model.timing import DurationInterval
import unified_planning.plans as plans
from unified_planning.plans import ActionInstance, TimeTriggeredPlan
from fractions import Fraction
from unified_planning.exceptions import UPUsageError


class DurativeActionToProcesses(engines.engine.Engine, CompilerMixin):
    # def __init__(self, use_counter: bool = True):
    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(
            self, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
        )
        # self._use_counter = use_counter

    @property
    def name(self):
        return "datp"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("REAL_ACTION_PARAMETERS")
        supported_kind.set_numbers("BOUNDED_TYPES")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_fluents_type("INT_FLUENTS")
        supported_kind.set_fluents_type("REAL_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FORALL_EFFECTS")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECTS")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_time("SELF_OVERLAPPING")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("INT_TYPE_DURATIONS")
        supported_kind.set_expression_duration("REAL_TYPE_DURATIONS")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_constraints_kind("STATE_INVARIANTS")
        supported_kind.set_constraints_kind("TRAJECTORY_CONSTRAINTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_initial_state("UNDEFINED_INITIAL_NUMERIC")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= DurativeActionToProcesses.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return (
            compilation_kind == CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
        )

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = problem_kind.clone()
        # TODO this removed durative actions, adds processes and events. and increasing_cont_effects
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        assert isinstance(problem, Problem)
        env = problem.environment
        mgr = env.expression_manager
        tm = env.type_manager
        new_to_old: Dict[Action, Optional[Action]] = {}  # TODO should not be needed

        new_problem = problem.clone()
        new_problem.name = f"{problem.name}_DurativeActionsToProcesses"
        new_problem.clear_actions()

        alive = Fluent(
            get_fresh_name(new_problem, "alive"), tm.BoolType(), environment=env
        )
        new_problem.add_fluent(alive, default_initial_value=mgr.TRUE())

        # TODO old code
        # if self._use_counter:
        #     new_fluent = Fluent("process_active", tm.IntType(), environment=env)
        #     new_problem.add_fluent(new_fluent, default_initial_value=0)

        for action in problem.actions:
            if isinstance(action, InstantaneousAction):
                new_action = action.clone()
                new_action.name = get_fresh_name(new_problem, new_action.name)
                new_action.add_precondition(alive)
                new_to_old[new_action] = action
                new_problem.add_action(new_action)
            elif isinstance(action, DurativeAction):
                params = OrderedDict(((p.name, p.type) for p in action.parameters))

                action_running_fluent = Fluent(
                    get_fresh_name(new_problem, action.name, trailing_info="running"),
                    tm.BoolType(),
                    params,
                    env,
                )
                new_problem.add_fluent(
                    action_running_fluent, default_initial_value=mgr.FALSE()
                )
                action_running = action_running_fluent(new_action.parameters)
                new_clock_fluent = Fluent(
                    get_fresh_name(new_problem, action.name, trailing_info="clock"),
                    tm.RealType(),
                    params,
                    env,
                )
                new_problem.add_fluent(new_clock_fluent, default_initial_value=0)
                action_clock = new_clock_fluent(new_action.parameters)

                new_action = InstantaneousAction(
                    get_fresh_name(new_problem, action.name, trailing_info="start"),
                    _parameters=params,
                    _env=env,
                )
                action_running_process = Process(
                    get_fresh_name(new_problem, action.name, trailing_info="during"),
                    _parameters=params,
                    _env=env,
                )
                action_running_process.add_precondition(action_running)
                action_running_process.add_increase_continuous_effect(action_clock, 1)

                # TODO stop event has to be added
                has_variable_duration = action_variable_duration(action)
                first_end_timing = None
                action_duration = None

                if has_variable_duration:
                    first_end_timing = get_first_end_timing(action)
                    action_duration_fluent = Fluent(
                        get_fresh_name(
                            new_problem, action.name, trailing_info="duration"
                        ),
                        tm.RealType(),
                        params,
                        env,
                    )
                    new_problem.add_fluent(
                        action_duration_fluent, default_initial_value=0
                    )  # TODO which should be the default here? Could zero be a problem? The initial action should set this to a non-problematic number
                    action_duration = action_duration_fluent(new_action.parameters)

                for interval, conditions in action.conditions:
                    fail_condition_event = mgr.Or(map(mgr.Not, conditions))

                # for effects we add an Event that does the effect. If it's the same as effect
                # for effect_timing, effects_list in

                # if action.duration.lower == action.duration.upper:
                #     new_stop_event = Event(
                #         f"{get_fresh_name(new_problem, action.name)}_stop",
                #         _parameters=params,
                #         _env=env,
                #     )
                #     new_stop_event.add_precondition(alive)
                # else:
                #     (delay_variable_duration_effect, delay_variable_duration) = min(
                #         (
                #             (eff_control, te_control.delay)
                #             for te_control, eff_control in action.effects.items()
                #             if te_control.delay < 0
                #         ),
                #         key=lambda x: x[1],
                #         default=(None, 0),
                #     )
                #     if delay_variable_duration_effect is not None:
                #         new_stop_event = Event(
                #             f"{get_fresh_name(new_problem, action.name)}_stop",
                #             _parameters=params,
                #             _env=env,
                #         )
                #         new_stop_event.add_precondition(alive)
                #         new_fluent_clock_delay_end = Fluent(
                #             f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, delay_variable_duration_effect[0].fluent.fluent().name)}_clock",
                #             tm.RealType(),
                #             params,
                #             env,
                #         )
                #         new_problem.add_fluent(
                #             new_fluent_clock_delay_end,
                #             default_initial_value=0,
                #         )
                #         delay_control_end = Fluent(
                #             f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, delay_variable_duration_effect[0].fluent.fluent().name)}_end_triggered",
                #             tm.BoolType(),
                #             params,
                #             env,
                #         )
                #         new_problem.add_fluent(
                #             delay_control_end,
                #             default_initial_value=em.FALSE(),
                #         )
                #     else:
                #         new_stop_action = InstantaneousAction(
                #             f"{get_fresh_name(new_problem, action.name)}_stop",
                #             _parameters=params,
                #             _env=env,
                #         )
                #         new_stop_action.add_precondition(alive)

                new_action.add_precondition(alive)
                action_running_process.add_precondition(alive)

                for t, cond in action.conditions.items():
                    if t.lower.is_from_start() and t.upper.is_from_start():
                        for c in cond:
                            if t.lower.delay > 0 and t.upper.delay > 0:
                                if t.lower.delay == t.upper.delay:
                                    if c.is_fluent_exp():
                                        new_intermediate_condition_start = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_intermediate_codition_start",
                                            _parameters=params,
                                            _env=env,
                                        )
                                    else:
                                        new_intermediate_condition_start = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_intermediate_codition_start",
                                            _parameters=params,
                                            _env=env,
                                        )
                                    new_intermediate_condition_start.add_precondition(
                                        alive
                                    )
                                    new_intermediate_condition_start.add_precondition(
                                        mgr.FluentExp(
                                            action_running_fluent,
                                            params=new_action.parameters,
                                        )
                                    )
                                    new_intermediate_condition_start.add_precondition(
                                        mgr.Equals(
                                            mgr.FluentExp(
                                                new_clock_fluent,
                                                params=new_action.parameters,
                                            ),
                                            t.lower.delay,
                                        )
                                    )
                                    new_intermediate_condition_start.add_precondition(
                                        mgr.Not(c)
                                    )
                                    new_intermediate_condition_start.add_effect(
                                        mgr.FluentExp(alive), mgr.FALSE()
                                    )
                                    new_intermediate_condition_start.add_effect(
                                        mgr.FluentExp(
                                            action_running_fluent,
                                            params=new_action.parameters,
                                        ),
                                        mgr.FALSE(),
                                    )
                                    new_problem.add_event(
                                        new_intermediate_condition_start
                                    )
                                elif t.lower.delay < t.upper.delay:
                                    if c.is_fluent_exp():
                                        new_intermediate_condition_start = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_intermediate_codition_start",
                                            _parameters=params,
                                            _env=env,
                                        )
                                        new_intermediate_running = Fluent(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_running",
                                            tm.BoolType(),
                                            params,
                                            env,
                                        )
                                        new_intermediate_condition_stop = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_intermediate_codition_stop",
                                            _parameters=params,
                                            _env=env,
                                        )
                                        new_intermediate_condition_error = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_intermediate_codition_error",
                                            _parameters=params,
                                            _env=env,
                                        )
                                    else:
                                        new_intermediate_condition_start = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_intermediate_codition_start",
                                            _parameters=params,
                                            _env=env,
                                        )
                                        new_intermediate_running = Fluent(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_running",
                                            tm.BoolType(),
                                            params,
                                            env,
                                        )
                                        new_intermediate_condition_stop = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_intermediate_codition_stop",
                                            _parameters=params,
                                            _env=env,
                                        )
                                        new_intermediate_condition_error = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_intermediate_codition_error",
                                            _parameters=params,
                                            _env=env,
                                        )
                                    new_problem.add_fluent(
                                        new_intermediate_running,
                                        default_initial_value=mgr.FALSE(),
                                    )

                                    new_intermediate_condition_start.add_precondition(
                                        alive
                                    )
                                    new_intermediate_condition_start.add_precondition(
                                        mgr.FluentExp(
                                            action_running_fluent,
                                            params=new_action.parameters,
                                        )
                                    )
                                    new_intermediate_condition_start.add_precondition(
                                        mgr.Not(
                                            mgr.FluentExp(
                                                new_intermediate_running,
                                                params=new_action.parameters,
                                            )
                                        )
                                    )

                                    if not (t.is_left_open()):
                                        new_intermediate_condition_start.add_precondition(
                                            c
                                        )
                                        new_intermediate_condition_start.add_precondition(
                                            mgr.Equals(
                                                mgr.FluentExp(
                                                    new_clock_fluent,
                                                    params=new_action.parameters,
                                                ),
                                                t.lower.delay,
                                            )
                                        )
                                    else:
                                        new_intermediate_condition_start.add_precondition(
                                            mgr.GT(
                                                mgr.FluentExp(
                                                    new_clock_fluent,
                                                    params=new_action.parameters,
                                                ),
                                                t.lower.delay,
                                            )
                                        )
                                    new_intermediate_condition_start.add_effect(
                                        mgr.FluentExp(
                                            new_intermediate_running,
                                            params=new_action.parameters,
                                        ),
                                        mgr.TRUE(),
                                    )

                                    new_intermediate_condition_stop.add_precondition(
                                        alive
                                    )
                                    new_intermediate_condition_stop.add_precondition(
                                        mgr.FluentExp(
                                            action_running_fluent,
                                            params=new_action.parameters,
                                        )
                                    )
                                    new_intermediate_condition_stop.add_precondition(
                                        mgr.FluentExp(
                                            new_intermediate_running,
                                            params=new_action.parameters,
                                        )
                                    )

                                    if not (t.is_right_open()):
                                        new_intermediate_condition_stop.add_precondition(
                                            c
                                        )
                                        new_intermediate_condition_stop.add_precondition(
                                            mgr.Equals(
                                                mgr.FluentExp(
                                                    new_clock_fluent,
                                                    params=new_action.parameters,
                                                ),
                                                t.upper.delay,
                                            )
                                        )
                                    else:
                                        new_intermediate_condition_stop.add_precondition(
                                            mgr.Not(
                                                mgr.LT(
                                                    mgr.FluentExp(
                                                        new_clock_fluent,
                                                        params=new_action.parameters,
                                                    ),
                                                    t.upper.delay,
                                                )
                                            )
                                        )
                                    new_intermediate_condition_stop.add_effect(
                                        mgr.FluentExp(
                                            new_intermediate_running,
                                            params=new_action.parameters,
                                        ),
                                        mgr.FALSE(),
                                    )

                                    new_intermediate_condition_error.add_precondition(
                                        alive
                                    )
                                    new_intermediate_condition_error.add_precondition(
                                        mgr.FluentExp(
                                            action_running_fluent,
                                            params=new_action.parameters,
                                        )
                                    )
                                    if t.is_left_open():
                                        new_intermediate_condition_error.add_precondition(
                                            mgr.FluentExp(
                                                new_intermediate_running,
                                                params=new_action.parameters,
                                            )
                                        )
                                    else:
                                        new_intermediate_condition_error.add_precondition(
                                            mgr.Or(
                                                mgr.FluentExp(
                                                    new_intermediate_running,
                                                    params=new_action.parameters,
                                                ),
                                                mgr.And(
                                                    mgr.Not(
                                                        mgr.FluentExp(
                                                            new_intermediate_running,
                                                            params=new_action.parameters,
                                                        )
                                                    ),
                                                    mgr.Equals(
                                                        mgr.FluentExp(
                                                            new_clock_fluent,
                                                            params=new_action.parameters,
                                                        ),
                                                        t.lower.delay,
                                                    ),
                                                ),
                                            )
                                        )
                                    new_intermediate_condition_error.add_precondition(
                                        mgr.Not(c)
                                    )
                                    new_intermediate_condition_error.add_effect(
                                        mgr.FluentExp(alive), mgr.FALSE()
                                    )
                                    new_intermediate_condition_error.add_effect(
                                        mgr.FluentExp(
                                            new_intermediate_running,
                                            params=new_action.parameters,
                                        ),
                                        mgr.FALSE(),
                                    )
                                    new_intermediate_condition_error.add_effect(
                                        mgr.FluentExp(
                                            action_running_fluent,
                                            params=new_action.parameters,
                                        ),
                                        mgr.FALSE(),
                                    )

                                    new_problem.add_event(
                                        new_intermediate_condition_start
                                    )
                                    new_problem.add_event(
                                        new_intermediate_condition_stop
                                    )
                                    new_problem.add_event(
                                        new_intermediate_condition_error
                                    )
                                else:
                                    raise NotImplementedError
                            elif t.lower.delay == 0:
                                new_action.add_precondition(c)
                            else:
                                raise NotImplementedError
                    elif t.lower.is_from_end() and t.upper.is_from_end():
                        for c in cond:
                            if action.duration.lower == action.duration.upper:
                                if t.lower.delay < 0 and t.upper.delay < 0:
                                    if t.lower.delay == t.upper.delay:
                                        if c.is_fluent_exp():
                                            new_intermediate_condition_end = Event(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_intermediate_codition_end",
                                                _parameters=params,
                                                _env=env,
                                            )
                                        else:
                                            new_intermediate_condition_end = Event(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_intermediate_codition_end",
                                                _parameters=params,
                                                _env=env,
                                            )
                                        new_intermediate_condition_end.add_precondition(
                                            alive
                                        )
                                        new_intermediate_condition_end.add_precondition(
                                            mgr.FluentExp(
                                                action_running_fluent,
                                                params=new_action.parameters,
                                            )
                                        )
                                        new_intermediate_condition_end.add_precondition(
                                            mgr.Equals(
                                                mgr.FluentExp(
                                                    new_clock_fluent,
                                                    params=new_action.parameters,
                                                ),
                                                action.duration.lower + (t.lower.delay),
                                            )
                                        )
                                        new_intermediate_condition_end.add_precondition(
                                            mgr.Not(c)
                                        )
                                        new_intermediate_condition_end.add_effect(
                                            mgr.FluentExp(alive),
                                            mgr.FALSE(),
                                        )
                                        new_intermediate_condition_end.add_effect(
                                            mgr.FluentExp(
                                                action_running_fluent,
                                                params=new_action.parameters,
                                            ),
                                            mgr.FALSE(),
                                        )
                                        new_problem.add_event(
                                            new_intermediate_condition_end
                                        )
                                    elif t.lower.delay < t.upper.delay:
                                        if c.is_fluent_exp():
                                            new_intermediate_condition_start = Event(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_intermediate_codition_end",
                                                _parameters=params,
                                                _env=env,
                                            )
                                            new_intermediate_running = Fluent(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_running",
                                                tm.BoolType(),
                                                params,
                                                env,
                                            )
                                            new_intermediate_condition_stop = Event(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_intermediate_codition_stop",
                                                _parameters=params,
                                                _env=env,
                                            )
                                            new_intermediate_condition_error = Event(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_intermediate_codition_error",
                                                _parameters=params,
                                                _env=env,
                                            )
                                        else:
                                            new_intermediate_condition_start = Event(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_intermediate_codition_end",
                                                _parameters=params,
                                                _env=env,
                                            )
                                            new_intermediate_running = Fluent(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_running",
                                                tm.BoolType(),
                                                params,
                                                env,
                                            )
                                            new_intermediate_condition_stop = Event(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_intermediate_codition_stop",
                                                _parameters=params,
                                                _env=env,
                                            )
                                            new_intermediate_condition_error = Event(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_intermediate_codition_error",
                                                _parameters=params,
                                                _env=env,
                                            )
                                        new_problem.add_fluent(
                                            new_intermediate_running,
                                            default_initial_value=mgr.FALSE(),
                                        )

                                        new_intermediate_condition_start.add_precondition(
                                            alive
                                        )
                                        new_intermediate_condition_start.add_precondition(
                                            mgr.FluentExp(
                                                action_running_fluent,
                                                params=new_action.parameters,
                                            )
                                        )
                                        new_intermediate_condition_start.add_precondition(
                                            mgr.Not(
                                                mgr.FluentExp(
                                                    new_intermediate_running,
                                                    params=new_action.parameters,
                                                )
                                            )
                                        )

                                        if not (t.is_left_open()):
                                            new_intermediate_condition_start.add_precondition(
                                                c
                                            )
                                            new_intermediate_condition_start.add_precondition(
                                                mgr.Equals(
                                                    mgr.FluentExp(
                                                        new_clock_fluent,
                                                        params=new_action.parameters,
                                                    ),
                                                    action.duration.lower
                                                    + (t.lower.delay),
                                                )
                                            )
                                        else:
                                            new_intermediate_condition_start.add_precondition(
                                                mgr.GT(
                                                    mgr.FluentExp(
                                                        new_clock_fluent,
                                                        params=new_action.parameters,
                                                    ),
                                                    action.duration.lower
                                                    + (t.lower.delay),
                                                )
                                            )
                                        new_intermediate_condition_start.add_effect(
                                            mgr.FluentExp(
                                                new_intermediate_running,
                                                params=new_action.parameters,
                                            ),
                                            mgr.TRUE(),
                                        )

                                        new_intermediate_condition_stop.add_precondition(
                                            alive
                                        )
                                        new_intermediate_condition_stop.add_precondition(
                                            mgr.FluentExp(
                                                action_running_fluent,
                                                params=new_action.parameters,
                                            )
                                        )
                                        new_intermediate_condition_stop.add_precondition(
                                            mgr.FluentExp(
                                                new_intermediate_running,
                                                params=new_action.parameters,
                                            )
                                        )

                                        if not (t.is_right_open()):
                                            new_intermediate_condition_stop.add_precondition(
                                                c
                                            )
                                            new_intermediate_condition_stop.add_precondition(
                                                mgr.Equals(
                                                    mgr.FluentExp(
                                                        new_clock_fluent,
                                                        params=new_action.parameters,
                                                    ),
                                                    action.duration.lower
                                                    + (t.upper.delay),
                                                )
                                            )
                                        else:
                                            new_intermediate_condition_stop.add_precondition(
                                                mgr.Not(
                                                    mgr.LT(
                                                        mgr.FluentExp(
                                                            new_clock_fluent,
                                                            params=new_action.parameters,
                                                        ),
                                                        action.duration.lower
                                                        + (t.upper.delay),
                                                    )
                                                )
                                            )
                                        new_intermediate_condition_stop.add_effect(
                                            mgr.FluentExp(
                                                new_intermediate_running,
                                                params=new_action.parameters,
                                            ),
                                            mgr.FALSE(),
                                        )

                                        new_intermediate_condition_error.add_precondition(
                                            alive
                                        )
                                        new_intermediate_condition_error.add_precondition(
                                            mgr.FluentExp(
                                                action_running_fluent,
                                                params=new_action.parameters,
                                            )
                                        )
                                        if t.is_left_open():
                                            new_intermediate_condition_error.add_precondition(
                                                mgr.FluentExp(
                                                    new_intermediate_running,
                                                    params=new_action.parameters,
                                                )
                                            )
                                        else:
                                            new_intermediate_condition_error.add_precondition(
                                                mgr.Or(
                                                    mgr.FluentExp(
                                                        new_intermediate_running,
                                                        params=new_action.parameters,
                                                    ),
                                                    mgr.And(
                                                        mgr.Not(
                                                            mgr.FluentExp(
                                                                new_intermediate_running,
                                                                params=new_action.parameters,
                                                            )
                                                        ),
                                                        mgr.Equals(
                                                            mgr.FluentExp(
                                                                new_clock_fluent,
                                                                params=new_action.parameters,
                                                            ),
                                                            action.duration.lower
                                                            + (t.lower.delay),
                                                        ),
                                                    ),
                                                )
                                            )
                                        new_intermediate_condition_error.add_precondition(
                                            mgr.Not(c)
                                        )
                                        new_intermediate_condition_error.add_effect(
                                            mgr.FluentExp(alive), mgr.FALSE()
                                        )
                                        new_intermediate_condition_error.add_effect(
                                            mgr.FluentExp(
                                                new_intermediate_running,
                                                params=new_action.parameters,
                                            ),
                                            mgr.FALSE(),
                                        )
                                        new_intermediate_condition_error.add_effect(
                                            mgr.FluentExp(
                                                action_running_fluent,
                                                params=new_action.parameters,
                                            ),
                                            mgr.FALSE(),
                                        )

                                        new_problem.add_event(
                                            new_intermediate_condition_start
                                        )
                                        new_problem.add_event(
                                            new_intermediate_condition_stop
                                        )
                                        new_problem.add_event(
                                            new_intermediate_condition_error
                                        )
                                    else:
                                        raise NotImplementedError
                                elif t.lower.delay == 0:
                                    new_stop_event.add_precondition(c)
                                else:
                                    raise NotImplementedError
                            else:
                                if t.lower.delay == 0 and t.upper.delay == 0:
                                    new_stop_action.add_precondition(c)
                                else:
                                    raise NotImplementedError
                    elif t.lower.is_from_start() and t.upper.is_from_end():
                        if t.lower.delay > 0 and t.upper.delay < 0:
                            if action.duration.lower == action.duration.upper:
                                for c in cond:
                                    if c.is_fluent_exp():
                                        new_intermediate_condition_start = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_intermediate_codition_start",
                                            _parameters=params,
                                            _env=env,
                                        )
                                        new_intermediate_condition_stop = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_intermediate_codition_end",
                                            _parameters=params,
                                            _env=env,
                                        )
                                        new_intermediate_condition_error = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_intermediate_codition_error",
                                            _parameters=params,
                                            _env=env,
                                        )
                                        new_intermediate_running = Fluent(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.fluent().name)}_running",
                                            tm.BoolType(),
                                            params,
                                            env,
                                        )
                                    else:
                                        new_intermediate_condition_start = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_intermediate_codition_start",
                                            _parameters=params,
                                            _env=env,
                                        )
                                        new_intermediate_condition_stop = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_intermediate_codition_end",
                                            _parameters=params,
                                            _env=env,
                                        )
                                        new_intermediate_condition_error = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_intermediate_codition_error",
                                            _parameters=params,
                                            _env=env,
                                        )
                                        new_intermediate_running = Fluent(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, c.args[0].fluent().name)}_running",
                                            tm.BoolType(),
                                            params,
                                            env,
                                        )
                                    new_problem.add_fluent(
                                        new_intermediate_running,
                                        default_initial_value=mgr.FALSE(),
                                    )

                                    new_intermediate_condition_start.add_precondition(
                                        alive
                                    )
                                    new_intermediate_condition_start.add_precondition(
                                        mgr.FluentExp(
                                            action_running_fluent,
                                            params=new_action.parameters,
                                        )
                                    )
                                    new_intermediate_condition_start.add_precondition(
                                        mgr.Not(
                                            mgr.FluentExp(
                                                new_intermediate_running,
                                                params=new_action.parameters,
                                            )
                                        )
                                    )
                                    new_intermediate_condition_start.add_precondition(
                                        mgr.Equals(
                                            mgr.FluentExp(
                                                new_clock_fluent,
                                                params=new_action.parameters,
                                            ),
                                            t.lower.delay,
                                        )
                                    )
                                    if not (t.is_left_open()):
                                        new_intermediate_condition_start.add_precondition(
                                            c
                                        )
                                    new_intermediate_condition_start.add_effect(
                                        mgr.FluentExp(
                                            new_intermediate_running,
                                            params=new_action.parameters,
                                        ),
                                        mgr.TRUE(),
                                    )

                                    new_intermediate_condition_stop.add_precondition(
                                        alive
                                    )
                                    new_intermediate_condition_stop.add_precondition(
                                        mgr.FluentExp(
                                            action_running_fluent,
                                            params=new_action.parameters,
                                        )
                                    )
                                    new_intermediate_condition_stop.add_precondition(
                                        mgr.FluentExp(
                                            new_intermediate_running,
                                            params=new_action.parameters,
                                        )
                                    )
                                    new_intermediate_condition_stop.add_precondition(
                                        mgr.Equals(
                                            mgr.FluentExp(
                                                new_clock_fluent,
                                                params=new_action.parameters,
                                            ),
                                            action.duration.lower + (t.upper.delay),
                                        )
                                    )
                                    if not (t.is_right_open()):
                                        new_intermediate_condition_stop.add_precondition(
                                            c
                                        )
                                    new_intermediate_condition_stop.add_effect(
                                        mgr.FluentExp(
                                            new_intermediate_running,
                                            params=new_action.parameters,
                                        ),
                                        mgr.FALSE(),
                                    )

                                    new_intermediate_condition_error.add_precondition(
                                        alive
                                    )
                                    new_intermediate_condition_error.add_precondition(
                                        mgr.FluentExp(
                                            action_running_fluent,
                                            params=new_action.parameters,
                                        )
                                    )
                                    if t.is_left_open():
                                        new_intermediate_condition_error.add_precondition(
                                            mgr.FluentExp(
                                                new_intermediate_running,
                                                params=new_action.parameters,
                                            )
                                        )
                                    else:
                                        new_intermediate_condition_error.add_precondition(
                                            mgr.Or(
                                                mgr.FluentExp(
                                                    new_intermediate_running,
                                                    params=new_action.parameters,
                                                ),
                                                mgr.And(
                                                    mgr.Not(
                                                        mgr.FluentExp(
                                                            new_intermediate_running,
                                                            params=new_action.parameters,
                                                        )
                                                    ),
                                                    mgr.Equals(
                                                        mgr.FluentExp(
                                                            new_clock_fluent,
                                                            params=new_action.parameters,
                                                        ),
                                                        t.lower.delay,
                                                    ),
                                                ),
                                            )
                                        )
                                    new_intermediate_condition_error.add_precondition(
                                        mgr.Not(c)
                                    )
                                    new_intermediate_condition_error.add_effect(
                                        mgr.FluentExp(alive),
                                        mgr.FALSE(),
                                    )
                                    new_intermediate_condition_error.add_effect(
                                        mgr.FluentExp(
                                            new_intermediate_running,
                                            params=new_action.parameters,
                                        ),
                                        mgr.FALSE(),
                                    )
                                    new_intermediate_condition_error.add_effect(
                                        mgr.FluentExp(
                                            action_running_fluent,
                                            params=new_action.parameters,
                                        ),
                                        mgr.FALSE(),
                                    )
                                    new_problem.add_event(
                                        new_intermediate_condition_start
                                    )
                                    new_problem.add_event(
                                        new_intermediate_condition_stop
                                    )
                                    new_problem.add_event(
                                        new_intermediate_condition_error
                                    )
                            else:
                                raise NotImplementedError
                        elif t.lower.delay == 0 and t.upper.delay == 0:
                            new_event_over_all = Event(
                                f"{get_fresh_name(new_problem, action.name)}_error",
                                _parameters=params,
                                _env=env,
                            )
                            new_event_over_all.add_precondition(alive)
                            new_event_over_all.add_precondition(
                                mgr.FluentExp(
                                    action_running_fluent,
                                    params=new_event_over_all.parameters,
                                )
                            )
                            new_event_over_all.add_precondition(mgr.Not(mgr.And(cond)))
                            for c in cond:
                                if not (t.is_left_open()):
                                    new_action.add_precondition(c)
                                if not (t.is_right_open()):
                                    if action.duration.lower == action.duration.upper:
                                        new_stop_event.add_precondition(c)
                                    else:
                                        new_stop_action.add_precondition(c)
                            new_event_over_all.add_effect(
                                mgr.FluentExp(alive), mgr.FALSE()
                            )
                            new_event_over_all.add_effect(
                                mgr.FluentExp(
                                    action_running_fluent,
                                    params=new_event_over_all.parameters,
                                ),
                                mgr.FALSE(),
                            )
                            new_problem.add_event(new_event_over_all)
                        else:
                            raise NotImplementedError
                    else:
                        raise NotImplementedError

                for te, eff in action.effects.items():
                    if te.is_from_start():
                        for e in eff:
                            if te.delay > 0:
                                new_delay_event = Event(
                                    f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, e.fluent.fluent().name)}_start_delay",
                                    _parameters=params,
                                    _env=env,
                                )
                                delay_control = Fluent(
                                    f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, e.fluent.fluent().name)}_start_triggered",
                                    tm.BoolType(),
                                    params,
                                    env,
                                )
                                new_problem.add_fluent(
                                    delay_control, default_initial_value=mgr.FALSE()
                                )
                                new_action.add_effect(
                                    mgr.FluentExp(
                                        delay_control, params=new_action.parameters
                                    ),
                                    mgr.FALSE(),
                                )

                                new_delay_event.add_precondition(alive)
                                new_delay_event.add_precondition(
                                    mgr.FluentExp(
                                        action_running_fluent,
                                        params=new_action.parameters,
                                    )
                                )
                                new_delay_event.add_precondition(
                                    mgr.Equals(
                                        mgr.FluentExp(
                                            new_clock_fluent,
                                            params=new_action.parameters,
                                        ),
                                        te.delay,
                                    )
                                )
                                new_delay_event.add_precondition(
                                    mgr.Not(
                                        mgr.FluentExp(
                                            delay_control, params=new_action.parameters
                                        )
                                    )
                                )
                                new_delay_event._add_effect_instance(e)
                                new_delay_event.add_effect(
                                    mgr.FluentExp(
                                        delay_control, params=new_action.parameters
                                    ),
                                    mgr.TRUE(),
                                )
                                new_problem.add_event(new_delay_event)
                            elif te.delay == 0:
                                new_action._add_effect_instance(e)
                            else:
                                raise NotImplementedError
                    elif te.is_from_end():
                        for e in eff:
                            if action.duration.lower == action.duration.upper:
                                if te.delay < 0:
                                    new_end_delay_event_c = Event(
                                        f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, e.fluent.fluent().name)}_end_delay",
                                        _parameters=params,
                                        _env=env,
                                    )
                                    delay_control = Fluent(
                                        f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, e.fluent.fluent().name)}_end_triggered",
                                        tm.BoolType(),
                                        params,
                                        env,
                                    )
                                    new_problem.add_fluent(
                                        delay_control, default_initial_value=mgr.FALSE()
                                    )
                                    new_action.add_effect(
                                        mgr.FluentExp(
                                            delay_control, params=new_action.parameters
                                        ),
                                        mgr.FALSE(),
                                    )

                                    new_end_delay_event_c.add_precondition(alive)
                                    new_end_delay_event_c.add_precondition(
                                        mgr.FluentExp(
                                            action_running_fluent,
                                            params=new_action.parameters,
                                        )
                                    )
                                    new_end_delay_event_c.add_precondition(
                                        mgr.Equals(
                                            mgr.FluentExp(
                                                new_clock_fluent,
                                                params=new_action.parameters,
                                            ),
                                            action.duration.lower + (te.delay),
                                        )
                                    )
                                    new_end_delay_event_c.add_precondition(
                                        mgr.Not(
                                            mgr.FluentExp(
                                                delay_control,
                                                params=new_action.parameters,
                                            )
                                        )
                                    )
                                    new_end_delay_event_c._add_effect_instance(e)
                                    new_end_delay_event_c.add_effect(
                                        mgr.FluentExp(
                                            delay_control, params=new_action.parameters
                                        ),
                                        mgr.TRUE(),
                                    )
                                    new_problem.add_event(new_end_delay_event_c)
                                elif te.delay == 0:
                                    new_stop_event._add_effect_instance(e)
                                else:
                                    raise NotImplementedError
                            else:
                                if delay_variable_duration_effect is not None:
                                    if te.delay < 0:
                                        if (
                                            delay_variable_duration_effect[0]
                                            .fluent.fluent()
                                            .name
                                            == e.fluent.fluent().name
                                            and delay_variable_duration == te.delay
                                        ):
                                            new_action_delay = InstantaneousAction(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem,e.fluent.fluent().name)}_end_delay",
                                                _parameters=params,
                                                _env=env,
                                            )

                                            new_action.add_effect(
                                                mgr.FluentExp(
                                                    delay_control_end,
                                                    params=new_action.parameters,
                                                ),
                                                mgr.FALSE(),
                                            )

                                            new_action_delay.add_precondition(alive)
                                            new_action_delay.add_precondition(
                                                mgr.FluentExp(
                                                    action_running_fluent,
                                                    params=new_action.parameters,
                                                )
                                            )
                                            if action.duration.is_left_open():
                                                new_action_delay.add_precondition(
                                                    mgr.GT(
                                                        mgr.FluentExp(
                                                            new_clock_fluent,
                                                            params=new_action.parameters,
                                                        ),
                                                        action.duration.lower
                                                        + (te.delay),
                                                    )
                                                )
                                            else:
                                                new_action_delay.add_precondition(
                                                    mgr.GE(
                                                        mgr.FluentExp(
                                                            new_clock_fluent,
                                                            params=new_action.parameters,
                                                        ),
                                                        action.duration.lower
                                                        + (te.delay),
                                                    )
                                                )
                                            if action.duration.is_right_open():
                                                new_action_delay.add_precondition(
                                                    mgr.LT(
                                                        mgr.FluentExp(
                                                            new_clock_fluent,
                                                            params=new_action.parameters,
                                                        ),
                                                        action.duration.upper
                                                        + (te.delay),
                                                    )
                                                )
                                            else:
                                                new_action_delay.add_precondition(
                                                    mgr.LE(
                                                        mgr.FluentExp(
                                                            new_clock_fluent,
                                                            params=new_action.parameters,
                                                        ),
                                                        action.duration.upper
                                                        + (te.delay),
                                                    )
                                                )
                                            new_action_delay.add_precondition(
                                                mgr.Not(
                                                    mgr.FluentExp(
                                                        delay_control_end,
                                                        params=new_action.parameters,
                                                    )
                                                )
                                            )
                                            new_action_delay._add_effect_instance(e)
                                            new_action_delay.add_effect(
                                                mgr.FluentExp(
                                                    new_fluent_clock_delay_end,
                                                    params=new_action.parameters,
                                                ),
                                                mgr.FluentExp(
                                                    new_clock_fluent,
                                                    params=new_action.parameters,
                                                ),
                                            )
                                            new_action_delay.add_effect(
                                                mgr.FluentExp(
                                                    delay_control_end,
                                                    params=new_action.parameters,
                                                ),
                                                mgr.TRUE(),
                                            )
                                            new_problem.add_action(new_action_delay)

                                            new_stop_event.add_precondition(
                                                mgr.Equals(
                                                    mgr.FluentExp(
                                                        new_clock_fluent,
                                                        params=new_action.parameters,
                                                    )
                                                    - mgr.FluentExp(
                                                        new_fluent_clock_delay_end,
                                                        params=new_action.parameters,
                                                    ),
                                                    (te.delay * (-1)),
                                                )
                                            )
                                            new_stop_event.add_precondition(
                                                mgr.FluentExp(
                                                    delay_control_end,
                                                    params=new_action.parameters,
                                                )
                                            )
                                        else:
                                            new_event_delay = Event(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem,e.fluent.fluent().name)}_end_delay",
                                                _parameters=params,
                                                _env=env,
                                            )
                                            delay_control = Fluent(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, e.fluent.fluent().name)}_end_triggered",
                                                tm.BoolType(),
                                                params,
                                                env,
                                            )
                                            new_problem.add_fluent(
                                                delay_control,
                                                default_initial_value=mgr.FALSE(),
                                            )
                                            new_action.add_effect(
                                                mgr.FluentExp(
                                                    delay_control,
                                                    params=new_action.parameters,
                                                ),
                                                mgr.FALSE(),
                                            )

                                            new_event_delay.add_precondition(alive)
                                            new_event_delay.add_precondition(
                                                mgr.FluentExp(
                                                    action_running_fluent,
                                                    params=new_action.parameters,
                                                )
                                            )
                                            new_event_delay.add_precondition(
                                                mgr.Equals(
                                                    mgr.FluentExp(
                                                        new_clock_fluent,
                                                        params=new_action.parameters,
                                                    )
                                                    - mgr.FluentExp(
                                                        new_fluent_clock_delay_end,
                                                        params=new_action.parameters,
                                                    ),
                                                    (delay_variable_duration * (-1))
                                                    + te.delay,
                                                )
                                            )
                                            new_event_delay.add_precondition(
                                                mgr.Not(
                                                    mgr.FluentExp(
                                                        delay_control,
                                                        params=new_action.parameters,
                                                    )
                                                )
                                            )
                                            new_event_delay.add_precondition(
                                                mgr.FluentExp(
                                                    delay_control_end,
                                                    params=new_action.parameters,
                                                )
                                            )

                                            new_event_delay._add_effect_instance(e)
                                            new_event_delay.add_effect(
                                                mgr.FluentExp(
                                                    delay_control,
                                                    params=new_action.parameters,
                                                ),
                                                mgr.TRUE(),
                                            )

                                            new_problem.add_event(new_event_delay)
                                    elif te.delay == 0:
                                        new_stop_event._add_effect_instance(e)
                                    else:
                                        raise NotImplementedError
                                else:
                                    new_stop_action._add_effect_instance(e)
                    else:
                        raise NotImplementedError

                new_action.add_precondition(
                    mgr.Not(
                        mgr.FluentExp(
                            action_running_fluent, params=new_action.parameters
                        )
                    )
                )
                new_action.add_effect(
                    mgr.FluentExp(action_running_fluent, params=new_action.parameters),
                    mgr.TRUE(),
                )
                new_action.add_effect(
                    mgr.FluentExp(new_clock_fluent, params=new_action.parameters), 0
                )
                # if self._use_counter:
                #     new_action.add_increase_effect(new_fluent, 1)

                if action.duration.lower == action.duration.upper:
                    new_stop_event.add_precondition(
                        mgr.Equals(
                            mgr.FluentExp(
                                new_clock_fluent, params=new_action.parameters
                            ),
                            action.duration.lower,
                        )
                    )
                else:
                    if not (delay_variable_duration_effect):
                        if action.duration.is_left_open():
                            new_stop_action.add_precondition(
                                mgr.GT(
                                    mgr.FluentExp(
                                        new_clock_fluent, params=new_action.parameters
                                    ),
                                    action.duration.lower,
                                )
                            )
                        else:
                            new_stop_action.add_precondition(
                                mgr.GE(
                                    mgr.FluentExp(
                                        new_clock_fluent, params=new_action.parameters
                                    ),
                                    action.duration.lower,
                                )
                            )
                        if action.duration.is_right_open():
                            new_stop_action.add_precondition(
                                mgr.LT(
                                    mgr.FluentExp(
                                        new_clock_fluent, params=new_action.parameters
                                    ),
                                    action.duration.upper,
                                )
                            )
                        else:
                            new_stop_action.add_precondition(
                                mgr.LE(
                                    mgr.FluentExp(
                                        new_clock_fluent, params=new_action.parameters
                                    ),
                                    action.duration.upper,
                                )
                            )

                if (
                    action.duration.lower == action.duration.upper
                    or delay_variable_duration_effect is not None
                ):
                    new_stop_event.add_precondition(
                        mgr.FluentExp(
                            action_running_fluent, params=new_action.parameters
                        )
                    )
                    new_stop_event.add_effect(
                        mgr.FluentExp(
                            action_running_fluent, params=new_action.parameters
                        ),
                        mgr.FALSE(),
                    )
                    # if self._use_counter:
                    #     new_stop_event.add_decrease_effect(new_fluent, 1)
                else:
                    new_stop_action.add_precondition(
                        mgr.FluentExp(
                            action_running_fluent, params=new_action.parameters
                        )
                    )
                    new_stop_action.add_effect(
                        mgr.FluentExp(
                            action_running_fluent, params=new_action.parameters
                        ),
                        mgr.FALSE(),
                    )
                    # if self._use_counter:
                    #     new_stop_action.add_decrease_effect(new_fluent, 1)

                new_to_old[new_action] = action

                if (
                    action.duration.lower == action.duration.upper
                    or delay_variable_duration_effect is not None
                ):
                    new_problem.add_event(new_stop_event)
                else:
                    new_problem.add_action(new_stop_action)

                new_problem.add_action(new_action)
                new_problem.add_process(action_running_process)

                if not (self._use_counter):
                    for g in get_all_fluent_exp(new_problem, action_running_fluent):
                        new_problem.add_goal(mgr.Not(g))

            else:
                raise NotImplementedError

        new_problem.add_goal(alive)
        # if self._use_counter:
        #     new_problem.add_goal(em.Equals(new_fluent, 0))

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )

    def plantoplan(
        self,
        plan_result: "up.plans.TimeTriggeredPlan",
        map: Dict["up.model.Action", Optional["up.model.Action"]],
    ) -> Optional["up.plans.TimeTriggeredPlan"]:
        translatePlan: List[
            Tuple[Fraction, "plans.plan.ActionInstance", Optional[Fraction]]
        ] = []
        if isinstance(plan_result, TimeTriggeredPlan):
            for index, action_plans in enumerate(plan_result.timed_actions):
                fraction = action_plans[0]
                try:
                    action_durative = map[action_plans[1].action]
                except:
                    action_durative = None
                if isinstance(action_durative, DurativeAction):
                    if action_durative is not None:
                        if not (
                            action_durative.duration.lower
                            == action_durative.duration.upper
                        ):
                            target_name = action_durative.name + "_stop"
                            (found_action, _) = next(
                                (
                                    (i, action_start)
                                    for i, (_, action_start, _) in enumerate(
                                        plan_result.timed_actions[index:]
                                    )
                                    if action_start.action.name == target_name
                                    and action_plans[1].actual_parameters
                                    == action_start.actual_parameters
                                ),
                                (None, None),
                            )
                            if found_action == None:
                                (delay_variable_duration_effect, te_delay) = min(
                                    (
                                        (eff_control, te_control.delay)
                                        for te_control, eff_control in action_durative.effects.items()
                                        if te_control.delay < 0
                                    ),
                                    key=lambda x: x[1],
                                    default=(None, None),
                                )
                                if (
                                    delay_variable_duration_effect is not None
                                    and te_delay is not None
                                ):
                                    delay_found = []
                                    for i, (_, action_start, _) in enumerate(
                                        plan_result.timed_actions[index:]
                                    ):
                                        for (
                                            delay_effect
                                        ) in delay_variable_duration_effect:
                                            if (
                                                delay_effect.fluent.fluent().name
                                                in action_start.action.name
                                                and "_end_delay"
                                                in action_start.action.name
                                                and action_durative.name
                                                in action_start.action.name
                                                and action_plans[1].actual_parameters
                                                == action_start.actual_parameters
                                            ):
                                                delay_found.append(i)
                                    found_action = next(
                                        ((i) for i in delay_found if i is not None),
                                        None,
                                    )
                                    if found_action is not None:
                                        found_action = index + found_action
                                        action_time = (
                                            plan_result.timed_actions[found_action][0]
                                            + (te_delay * (-1))
                                            - fraction
                                        )
                                    else:
                                        raise UPUsageError(
                                            "The Action of the given ActionInstance does not have a valid replacement."
                                        )
                                else:
                                    raise UPUsageError(
                                        "The Action of the given ActionInstance does not have a valid replacement."
                                    )
                            else:
                                found_action = index + found_action
                                action_time = (
                                    plan_result.timed_actions[found_action][0]
                                    - fraction
                                )

                        else:
                            if action_durative.duration.lower.is_int_constant():
                                action_time = Fraction(
                                    action_durative.duration.lower.int_constant_value()
                                )
                            else:
                                action_time = None
                        translateAction = ActionInstance(
                            action_durative, action_plans[1].actual_parameters
                        )
                        translatePlan.append((fraction, translateAction, action_time))
                elif isinstance(action_durative, InstantaneousAction):
                    translateAction = ActionInstance(
                        action_durative, action_plans[1].actual_parameters
                    )
                    translatePlan.append((fraction, translateAction, Fraction(0)))
                elif action_durative is not None:
                    raise NotImplementedError

        return TimeTriggeredPlan(translatePlan)


def action_variable_duration(action: DurativeAction) -> bool:
    return action.duration.lower == action.duration.upper
    # TODO could we add an assert that if they are the same is_{right/left}_open have to be False?


def get_first_end_timing(action: DurativeAction) -> Optional[Timing]:

    # utility function to take timing or intervals and return the respective timing or timings
    def timing_from_interval(
        timing_or_interval: Union[Timing, TimeInterval], conds_or_effs
    ) -> Iterator[Timing]:
        if isinstance(timing_or_interval, Timing):
            yield timing_or_interval
        else:
            assert isinstance(
                timing_or_interval, TimeInterval
            ), f"Wrong durative action {action.name} typing associated to {conds_or_effs}"
            yield timing_or_interval.lower, timing_or_interval.upper

    first_end_timing: Optional[Timing] = None
    for timing_or_interval, conds_or_effs in chain(
        action.conditions.items(), action.effects.items()
    ):
        for timing in timing_from_interval(timing_or_interval):
            assert isinstance(
                timing, Timing
            ), f"Wrong durative action {action.name} typing associated to {conds_or_effs}"
            if timing.is_from_end():
                assert timing.delay <= 0
                if first_end_timing is None or first_end_timing.delay > timing.delay:
                    first_end_timing = timing

    return first_end_timing


def get_relative_timing(
    timing: Timing,
    first_end_timing: Optional[Timing],
    action_clock: FNode,
    action_duration_exp: Optional[FNode],
    action_duration: DurationInterval,
    mgr,
) -> Tuple[FNode, Union[int, Fraction, FNode]]:
    if timing.is_from_start():
        return action_clock, timing.delay
    assert timing.delay <= 0
    if action_duration_exp is None:
        assert action_duration.lower == action_duration.upper
        # duration is not variable, so end_timing can be returned as timing from start
        return action_clock, mgr.Plus(action_duration.lower, timing.delay)
    # complex case where the timing is from end and the action duration is variable
    assert action_duration_exp is not None and first_end_timing is not None
    return mgr.Minus(action_clock, action_duration_exp), mgr.Minus(
        timing.delay, first_end_timing.delay
    )
