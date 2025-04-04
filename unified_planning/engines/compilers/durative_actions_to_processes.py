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
from typing import Dict, Optional, OrderedDict
from functools import partial


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

        if self._use_counter:
            new_fluent = Fluent("process_active", tm.IntType(), environment=env)
            new_problem.add_fluent(new_fluent, default_initial_value=0)

        for action in problem.actions:
            if isinstance(action, InstantaneousAction):
                new_action = action.clone()
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
                new_event = Event(
                    f"{get_fresh_name(new_problem, action.name)}_stop",
                    _parameters=params,
                    _env=env,
                )

                for t, cond in action.conditions.items():
                    if t.lower.is_from_start() and t.upper.is_from_start():
                        for c in cond:
                            new_action.add_precondition(c)
                    elif t.lower.is_from_end() and t.upper.is_from_end():
                        for c in cond:
                            new_event.add_precondition(c)
                    elif t.lower.is_from_start() and t.upper.is_from_end():
                        for c in cond:
                            new_action.add_precondition(c)
                            new_event.add_precondition(c)
                    else:
                        raise NotImplementedError

                for t, eff in action.effects.items():
                    if t.is_from_start():
                        for e in eff:
                            new_action.add_effect(e.fluent, e.value)
                    elif t.is_from_end():
                        for e in eff:
                            new_event.add_effect(e.fluent, e.value)
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

                duration = action.duration.upper
                new_event.add_precondition(
                    em.Equals(
                        em.FluentExp(new_fluent_clock, params=new_action.parameters),
                        duration,
                    )
                )
                new_event.add_precondition(
                    em.FluentExp(new_fluent_running, params=new_action.parameters)
                )
                new_event.add_effect(
                    em.FluentExp(new_fluent_running, params=new_action.parameters),
                    em.FALSE(),
                )
                if self._use_counter:
                    new_event.add_decrease_effect(new_fluent, 1)

                new_to_old[new_action] = action
                new_to_old[new_process] = action
                new_to_old[new_event] = action

                new_problem.add_action(new_action)
                new_problem.add_process(new_process)
                new_problem.add_event(new_event)

                if not (self._use_counter):
                    for g in get_all_fluent_exp(new_problem, new_fluent_running):
                        new_problem.add_goal(em.Not(g))

            else:
                raise NotImplementedError

        if self._use_counter:
            new_problem.add_goal(em.Equals(new_fluent, 0))

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )
