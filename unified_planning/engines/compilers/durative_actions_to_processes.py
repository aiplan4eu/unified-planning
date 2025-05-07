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
)
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.model.fluent import get_all_fluent_exp
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
    replace_action,
)
from typing import Dict, Optional, OrderedDict, Tuple, List
from functools import partial
import unified_planning.plans as plans
from unified_planning.plans import ActionInstance, TimeTriggeredPlan
from fractions import Fraction
from unified_planning.exceptions import UPUsageError


class DurativeActionToProcesses(engines.engine.Engine, CompilerMixin):
    def __init__(self, use_counter: bool = True):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(
            self, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
        )
        self._use_counter = use_counter

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
        # ...
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        assert isinstance(problem, Problem)
        env = problem.environment
        em = env.expression_manager
        tm = env.type_manager
        new_to_old: Dict[Action, Optional[Action]] = {}

        new_problem = problem.clone()
        new_problem.name = f"{problem.name}_DurativeActionsToProcesses"
        new_problem.clear_actions()

        alive_fluent = Fluent("alive", tm.BoolType(), environment=env)
        new_problem.add_fluent(alive_fluent, default_initial_value=em.TRUE())

        if self._use_counter:
            new_fluent = Fluent("process_active", tm.IntType(), environment=env)
            new_problem.add_fluent(new_fluent, default_initial_value=0)

        for action in problem.actions:
            if isinstance(action, InstantaneousAction):
                new_action = action.clone()
                new_action.add_precondition(alive_fluent)
                new_to_old[new_action] = action
                new_problem.add_action(new_action)
            elif isinstance(action, DurativeAction):
                params = OrderedDict(((p.name, p.type) for p in action.parameters))

                new_fluent_running = Fluent(
                    f"{get_fresh_name(new_problem, action.name)}_running",
                    tm.BoolType(),
                    params,
                    env,
                )
                new_problem.add_fluent(
                    new_fluent_running, default_initial_value=em.FALSE()
                )
                new_fluent_clock = Fluent(
                    f"{get_fresh_name(new_problem, action.name)}_clock",
                    tm.RealType(),
                    params,
                    env,
                )
                new_problem.add_fluent(new_fluent_clock, default_initial_value=0)

                new_action = InstantaneousAction(
                    f"{get_fresh_name(new_problem, action.name)}_start",
                    _parameters=params,
                    _env=env,
                )
                new_process = Process(
                    f"{get_fresh_name(new_problem, action.name)}_during",
                    _parameters=params,
                    _env=env,
                )
                delay_variable_duration_effect = False
                if action.duration.lower == action.duration.upper:
                    new_stop_event = Event(
                        f"{get_fresh_name(new_problem, action.name)}_stop",
                        _parameters=params,
                        _env=env,
                    )
                    new_stop_event.add_precondition(alive_fluent)
                else:
                    delay_variable_duration_effect = any(
                        te_control.delay < 0 for te_control, _ in action.effects.items()
                    )
                    if delay_variable_duration_effect:
                        new_stop_event = Event(
                            f"{get_fresh_name(new_problem, action.name)}_stop",
                            _parameters=params,
                            _env=env,
                        )
                        new_stop_event.add_precondition(alive_fluent)
                    else:
                        new_stop_action = InstantaneousAction(
                            f"{get_fresh_name(new_problem, action.name)}_stop",
                            _parameters=params,
                            _env=env,
                        )
                        new_stop_action.add_precondition(alive_fluent)

                new_action.add_precondition(alive_fluent)
                new_process.add_precondition(alive_fluent)

                for t, cond in action.conditions.items():
                    if t.lower.is_from_start() and t.upper.is_from_start():
                        for c in cond:
                            if t.lower.delay > 0:
                                if t.lower.delay == t.upper.delay:
                                    if action.duration.lower.is_int_constant():
                                        if (
                                            action.duration.lower.int_constant_value()
                                            > t.lower.delay
                                        ):
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
                                                alive_fluent
                                            )
                                            new_intermediate_condition_start.add_precondition(
                                                em.FluentExp(
                                                    new_fluent_running,
                                                    params=new_action.parameters,
                                                )
                                            )
                                            new_intermediate_condition_start.add_precondition(
                                                em.Equals(
                                                    em.FluentExp(
                                                        new_fluent_clock,
                                                        params=new_action.parameters,
                                                    ),
                                                    t.lower.delay,
                                                )
                                            )
                                            new_intermediate_condition_start.add_precondition(
                                                em.Not(c)
                                            )
                                            new_intermediate_condition_start.add_effect(
                                                em.FluentExp(alive_fluent), em.FALSE()
                                            )
                                            new_intermediate_condition_start.add_effect(
                                                em.FluentExp(
                                                    new_fluent_running,
                                                    params=new_action.parameters,
                                                ),
                                                em.FALSE(),
                                            )
                                            new_problem.add_event(
                                                new_intermediate_condition_start
                                            )
                                        else:
                                            raise NotImplementedError
                                    else:
                                        raise NotImplementedError
                                else:
                                    raise NotImplementedError
                            elif t.lower.delay == 0:
                                new_action.add_precondition(c)
                            else:
                                raise NotImplementedError
                    elif t.lower.is_from_end() and t.upper.is_from_end():
                        for c in cond:
                            if action.duration.lower == action.duration.upper:
                                if t.lower.delay < 0:
                                    if t.lower.delay == t.upper.delay:
                                        if action.duration.lower.is_int_constant():
                                            if (
                                                action.duration.lower.int_constant_value()
                                                + t.lower.delay
                                                > 0
                                            ):
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
                                                    alive_fluent
                                                )
                                                new_intermediate_condition_end.add_precondition(
                                                    em.FluentExp(
                                                        new_fluent_running,
                                                        params=new_action.parameters,
                                                    )
                                                )
                                                new_intermediate_condition_end.add_precondition(
                                                    em.Equals(
                                                        em.FluentExp(
                                                            new_fluent_clock,
                                                            params=new_action.parameters,
                                                        ),
                                                        action.duration.lower.int_constant_value()
                                                        + t.lower.delay,
                                                    )
                                                )
                                                new_intermediate_condition_end.add_precondition(
                                                    em.Not(c)
                                                )
                                                new_intermediate_condition_end.add_effect(
                                                    em.FluentExp(alive_fluent),
                                                    em.FALSE(),
                                                )
                                                new_intermediate_condition_end.add_effect(
                                                    em.FluentExp(
                                                        new_fluent_running,
                                                        params=new_action.parameters,
                                                    ),
                                                    em.FALSE(),
                                                )
                                                new_problem.add_event(
                                                    new_intermediate_condition_end
                                                )
                                            else:
                                                raise NotImplementedError
                                        else:
                                            raise NotImplementedError
                                    else:
                                        raise NotImplementedError
                                elif t.lower.delay == 0:
                                    new_stop_event.add_precondition(c)
                                else:
                                    raise NotImplementedError
                            else:
                                new_stop_action.add_precondition(c)
                    elif t.lower.is_from_start() and t.upper.is_from_end():
                        new_event_over_all = Event(
                            f"{get_fresh_name(new_problem, action.name)}_error",
                            _parameters=params,
                            _env=env,
                        )
                        new_event_over_all.add_precondition(alive_fluent)
                        new_event_over_all.add_precondition(
                            em.FluentExp(
                                new_fluent_running, params=new_event_over_all.parameters
                            )
                        )
                        new_event_over_all.add_precondition(em.Not(em.And(cond)))
                        for c in cond:
                            if not (action.duration.is_left_open()):
                                new_action.add_precondition(c)
                            if not (action.duration.is_right_open()):
                                if action.duration.lower == action.duration.upper:
                                    new_stop_event.add_precondition(c)
                                else:
                                    new_stop_action.add_precondition(c)
                        new_event_over_all.add_effect(
                            em.FluentExp(alive_fluent), em.FALSE()
                        )
                        new_event_over_all.add_effect(
                            em.FluentExp(
                                new_fluent_running, params=new_event_over_all.parameters
                            ),
                            em.FALSE(),
                        )
                        new_problem.add_event(new_event_over_all)
                    else:
                        raise NotImplementedError

                for te, eff in action.effects.items():
                    if te.is_from_start():
                        for e in eff:
                            if te.delay > 0:
                                if action.duration.lower.is_int_constant():
                                    if (
                                        action.duration.lower.int_constant_value()
                                        > te.delay
                                    ):
                                        new_delay_event = Event(
                                            f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, e.fluent.fluent().name)}_start_delay",
                                            _parameters=params,
                                            _env=env,
                                        )
                                        new_delay_event.add_precondition(alive_fluent)
                                        new_delay_event.add_precondition(
                                            em.FluentExp(
                                                new_fluent_running,
                                                params=new_action.parameters,
                                            )
                                        )
                                        new_delay_event.add_precondition(
                                            em.Equals(
                                                em.FluentExp(
                                                    new_fluent_clock,
                                                    params=new_action.parameters,
                                                ),
                                                te.delay,
                                            )
                                        )
                                        new_delay_event._add_effect_instance(e)
                                        new_problem.add_event(new_delay_event)
                                    else:
                                        raise NotImplementedError
                                else:
                                    raise NotImplementedError
                            elif te.delay == 0:
                                new_action._add_effect_instance(e)
                            else:
                                raise NotImplementedError
                    elif te.is_from_end():
                        for e in eff:
                            if action.duration.lower == action.duration.upper:
                                if te.delay < 0:
                                    if action.duration.lower.is_int_constant():
                                        if (
                                            action.duration.lower.int_constant_value()
                                            + te.delay
                                            > 0
                                        ):
                                            new_end_delay_event_c = Event(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem, e.fluent.fluent().name)}_end_delay",
                                                _parameters=params,
                                                _env=env,
                                            )
                                            new_end_delay_event_c.add_precondition(
                                                alive_fluent
                                            )
                                            new_end_delay_event_c.add_precondition(
                                                em.FluentExp(
                                                    new_fluent_running,
                                                    params=new_action.parameters,
                                                )
                                            )
                                            new_end_delay_event_c.add_precondition(
                                                em.Equals(
                                                    em.FluentExp(
                                                        new_fluent_clock,
                                                        params=new_action.parameters,
                                                    ),
                                                    action.duration.lower.int_constant_value()
                                                    + te.delay,
                                                )
                                            )
                                            new_end_delay_event_c._add_effect_instance(
                                                e
                                            )
                                            new_problem.add_event(new_end_delay_event_c)
                                        else:
                                            raise NotImplementedError
                                    else:
                                        raise NotImplementedError
                                elif te.delay == 0:
                                    new_stop_event._add_effect_instance(e)
                                else:
                                    raise NotImplementedError
                            else:
                                if delay_variable_duration_effect:
                                    if te.delay < 0:
                                        if (
                                            action.duration.lower.is_int_constant()
                                            and action.duration.upper.is_int_constant()
                                        ):
                                            new_fluent_clock_delay_end = Fluent(
                                                f"{get_fresh_name(new_problem, e.fluent.fluent().name)}_clock",
                                                tm.RealType(),
                                                params,
                                                env,
                                            )
                                            new_problem.add_fluent(
                                                new_fluent_clock_delay_end,
                                                default_initial_value=action.duration.upper.int_constant_value(),
                                            )
                                            new_action_delay = InstantaneousAction(
                                                f"{get_fresh_name(new_problem, action.name)}_{get_fresh_name(new_problem,e.fluent.fluent().name)}_end_delay",
                                                _parameters=params,
                                                _env=env,
                                            )
                                            new_action_delay.add_precondition(
                                                alive_fluent
                                            )
                                            new_action_delay.add_precondition(
                                                em.FluentExp(
                                                    new_fluent_running,
                                                    params=new_action.parameters,
                                                )
                                            )
                                            if action.duration.is_left_open():
                                                new_action_delay.add_precondition(
                                                    em.GT(
                                                        em.FluentExp(
                                                            new_fluent_clock,
                                                            params=new_action.parameters,
                                                        ),
                                                        action.duration.lower.int_constant_value()
                                                        + te.delay,
                                                    )
                                                )
                                            else:
                                                new_action_delay.add_precondition(
                                                    em.GE(
                                                        em.FluentExp(
                                                            new_fluent_clock,
                                                            params=new_action.parameters,
                                                        ),
                                                        action.duration.lower.int_constant_value()
                                                        + te.delay,
                                                    )
                                                )
                                            if action.duration.is_right_open():
                                                new_action_delay.add_precondition(
                                                    em.LT(
                                                        em.FluentExp(
                                                            new_fluent_clock,
                                                            params=new_action.parameters,
                                                        ),
                                                        action.duration.upper.int_constant_value()
                                                        + te.delay,
                                                    )
                                                )
                                            else:
                                                new_action_delay.add_precondition(
                                                    em.LE(
                                                        em.FluentExp(
                                                            new_fluent_clock,
                                                            params=new_action.parameters,
                                                        ),
                                                        action.duration.upper.int_constant_value()
                                                        + te.delay,
                                                    )
                                                )
                                            new_action_delay._add_effect_instance(e)
                                            new_action_delay.add_effect(
                                                em.FluentExp(
                                                    new_fluent_clock_delay_end,
                                                    params=new_action.parameters,
                                                ),
                                                em.FluentExp(
                                                    new_fluent_clock,
                                                    params=new_action.parameters,
                                                ),
                                            )
                                            new_problem.add_action(new_action_delay)

                                            new_stop_event.add_precondition(
                                                em.Equals(
                                                    em.FluentExp(
                                                        new_fluent_clock,
                                                        params=new_action.parameters,
                                                    )
                                                    - em.FluentExp(
                                                        new_fluent_clock_delay_end,
                                                        params=new_action.parameters,
                                                    ),
                                                    (te.delay * (-1)),
                                                )
                                            )
                                        else:
                                            raise NotImplementedError
                                    elif te.delay == 0:
                                        new_stop_event._add_effect_instance(e)
                                    else:
                                        raise NotImplementedError
                                else:
                                    new_stop_action._add_effect_instance(e)
                    else:
                        raise NotImplementedError

                new_action.add_precondition(
                    em.Not(
                        em.FluentExp(new_fluent_running, params=new_action.parameters)
                    )
                )
                new_action.add_effect(
                    em.FluentExp(new_fluent_running, params=new_action.parameters),
                    em.TRUE(),
                )
                new_action.add_effect(
                    em.FluentExp(new_fluent_clock, params=new_action.parameters), 0
                )
                if self._use_counter:
                    new_action.add_increase_effect(new_fluent, 1)

                new_process.add_precondition(
                    em.FluentExp(new_fluent_running, params=new_action.parameters)
                )
                new_process.add_increase_continuous_effect(
                    em.FluentExp(new_fluent_clock, params=new_action.parameters), 1
                )

                if action.duration.lower == action.duration.upper:
                    new_stop_event.add_precondition(
                        em.Equals(
                            em.FluentExp(
                                new_fluent_clock, params=new_action.parameters
                            ),
                            action.duration.lower,
                        )
                    )
                else:
                    if not (delay_variable_duration_effect):
                        if action.duration.is_left_open():
                            new_stop_action.add_precondition(
                                em.GT(
                                    em.FluentExp(
                                        new_fluent_clock, params=new_action.parameters
                                    ),
                                    action.duration.lower.int_constant_value(),
                                )
                            )
                        else:
                            new_stop_action.add_precondition(
                                em.GE(
                                    em.FluentExp(
                                        new_fluent_clock, params=new_action.parameters
                                    ),
                                    action.duration.lower.int_constant_value(),
                                )
                            )
                        if action.duration.is_right_open():
                            new_stop_action.add_precondition(
                                em.LT(
                                    em.FluentExp(
                                        new_fluent_clock, params=new_action.parameters
                                    ),
                                    action.duration.upper.int_constant_value(),
                                )
                            )
                        else:
                            new_stop_action.add_precondition(
                                em.LE(
                                    em.FluentExp(
                                        new_fluent_clock, params=new_action.parameters
                                    ),
                                    action.duration.upper.int_constant_value(),
                                )
                            )

                if (
                    action.duration.lower == action.duration.upper
                    or delay_variable_duration_effect
                ):
                    new_stop_event.add_precondition(
                        em.FluentExp(new_fluent_running, params=new_action.parameters)
                    )
                    new_stop_event.add_effect(
                        em.FluentExp(new_fluent_running, params=new_action.parameters),
                        em.FALSE(),
                    )
                    if self._use_counter:
                        new_stop_event.add_decrease_effect(new_fluent, 1)
                else:
                    new_stop_action.add_precondition(
                        em.FluentExp(new_fluent_running, params=new_action.parameters)
                    )
                    new_stop_action.add_effect(
                        em.FluentExp(new_fluent_running, params=new_action.parameters),
                        em.FALSE(),
                    )
                    if self._use_counter:
                        new_stop_action.add_decrease_effect(new_fluent, 1)

                new_to_old[new_action] = action

                if (
                    action.duration.lower == action.duration.upper
                    or delay_variable_duration_effect
                ):
                    new_problem.add_event(new_stop_event)
                else:
                    new_problem.add_action(new_stop_action)

                new_problem.add_action(new_action)
                new_problem.add_process(new_process)

                if not (self._use_counter):
                    for g in get_all_fluent_exp(new_problem, new_fluent_running):
                        new_problem.add_goal(em.Not(g))

            else:
                raise NotImplementedError

        new_problem.add_goal(alive_fluent)
        if self._use_counter:
            new_problem.add_goal(em.Equals(new_fluent, 0))

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
            for action_plans in plan_result.timed_actions:
                fraction = action_plans[0]
                try:
                    action_durative = map[action_plans[1].action]
                except:
                    action_durative = None
                if isinstance(action_durative, DurativeAction):
                    index = plan_result.timed_actions.index(action_plans)
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
                                (delay_variable_duration_effect, te_delay) = next(
                                    (
                                        (eff_control, te_control.delay)
                                        for te_control, eff_control in action_durative.effects.items()
                                        if te_control.delay < 0
                                    ),
                                    (None, None),
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
