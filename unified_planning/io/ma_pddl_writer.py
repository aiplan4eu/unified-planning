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

import os as osy
from fractions import Fraction
import sys
import re

from decimal import Decimal, localcontext
from warnings import warn
import unified_planning as up
import unified_planning.environment
import unified_planning.model.walkers as walkers
from unified_planning.model import (
    InstantaneousAction,
    DurativeAction,
    Fluent,
    Parameter,
    Problem,
    Object,
)
from unified_planning.model.multi_agent.agent import Agent
from unified_planning.model.multi_agent.ma_problem import MultiAgentProblem
from unified_planning.exceptions import (
    UPTypeError,
    UPProblemDefinitionError,
    UPException,
)
from unified_planning.model.types import _UserType
from typing import Callable, Dict, List, Optional, Set, Union, cast
from io import StringIO
from unified_planning.io.pddl_writer import (
    ObjectsExtractor,
    ConverterToPDDLString,
    MangleFunction,
    WithName,
    _write_effect,
    _get_pddl_name,
)


class ConverterToMAPDDLString(ConverterToPDDLString):
    """Expression converter to a MA-PDDL string."""

    def __init__(
        self,
        problem: MultiAgentProblem,
        get_mangled_name: MangleFunction,
        agent: Optional["up.model.multi_agent.Agent"],
        unfactored: Optional[bool] = False,
    ):
        ConverterToPDDLString.__init__(self, problem.environment, get_mangled_name)
        self._problem = problem
        self._agent = agent
        self._unfactored = unfactored

    def walk_dot(self, expression, args):
        agent = self._problem.agent(expression.agent())
        fluent = expression.args[0].fluent()
        objects = expression.args[0].args
        agent_name = ""
        if (
            self._unfactored
            and self._agent is not None
            and fluent not in self._agent.public_fluents
        ):
            agent_name = f"_{self.get_mangled_name(agent)}"

        return f'(a_{self.get_mangled_name(fluent)}{agent_name} {self.get_mangled_name(agent)} {" ".join([self.convert(obj) for obj in objects])})'

    def walk_fluent_exp(self, expression, args):
        fluent = expression.fluent()
        agent_name = ""
        if (
            self._unfactored
            and self._agent is not None
            and fluent not in self._agent.public_fluents
        ):
            agent_name = f"_{self._agent.name}"

        if self._agent is not None and fluent in self._agent.fluents:
            return f'(a_{self.get_mangled_name(fluent)}{agent_name}  ?{self._agent.name}{" " if len(args) > 0 else ""}{" ".join(args)})'
        else:
            return f'({self.get_mangled_name(fluent)}{" " if len(args) > 0 else ""}{" ".join(args)})'


class MAPDDLWriter:
    """
    This class can be used to write a :class:`~unified_planning.model.MultiAgentProblem` in `MA-PDDL`.
    The constructor of this class takes the problem to write and 4 flags:

    * ``explicit_false_initial_states`` determines if this writer includes initially false predicates in the problem ``:init``,
    * ``unfactored`` when ``False`` this writer prints a domain and a problem for every agent, if ``True`` generates a single domain and a single problem,
    * ``needs_requirements`` determines if the printed problem must have the :requirements,
    * ``rewrite_bool_assignments`` determines if this writer will write non constant boolean assignment as conditional effects.
    """

    def __init__(
        self,
        problem: "up.model.multi_agent.MultiAgentProblem",
        explicit_false_initial_states: Optional[bool] = False,
        unfactored: Optional[bool] = False,
        needs_requirements: bool = True,
        rewrite_bool_assignments: bool = False,
    ):
        self._env = problem.environment
        self.problem = problem
        self.problem_kind = self.problem.kind
        self.explicit_false_initial_states = explicit_false_initial_states
        self.unfactored = unfactored
        self.needs_requirements = needs_requirements
        self.rewrite_bool_assignments = rewrite_bool_assignments
        # otn represents the old to new renamings
        self.otn_renamings: Dict[
            WithName,
            str,
        ] = {}
        # nto represents the new to old renamings
        self.nto_renamings: Dict[
            str,
            WithName,
        ] = {}
        # those 2 maps are "simmetrical", meaning that "(otn[k] == v) implies (nto[v] == k)"
        self.domain_objects: Optional[Dict[_UserType, Set[Object]]] = None
        self.domain_objects_agents: Dict[up.model.multi_agent.Agent, str]
        self.all_public_fluents: Set[Fluent] = set()

    def _write_domain(self):
        ag_domains = {}
        for ag in self.problem.agents:
            out = StringIO()
            if self.problem_kind.has_intermediate_conditions_and_effects():
                raise UPProblemDefinitionError(
                    "PDDL2.1 does not support ICE.\nICE are Intermediate Conditions and Effects therefore when an Effect (or Condition) are not at StartTIming(0) or EndTIming(0)."
                )
            if (
                self.problem_kind.has_timed_effects()
                or self.problem_kind.has_timed_goals()
            ):
                raise UPProblemDefinitionError(
                    "PDDL2.1 does not support timed effects or timed goals."
                )
            obe = ObjectsExtractor()
            out.write("(define ")
            if self.problem.name is None:
                name = "ma-pddl"
            else:
                name = _get_pddl_name(self.problem)
            out.write(f"(domain {name}-domain)\n")

            if self.needs_requirements:
                out.write(" (:requirements :multi-agent")
                if not self.unfactored:
                    out.write(" :factored-privacy")
                else:
                    out.write(" :unfactored-privacy")
                if self.problem_kind.has_flat_typing():
                    out.write(" :typing")
                if self.problem_kind.has_negative_conditions():
                    out.write(" :negative-preconditions")
                if self.problem_kind.has_disjunctive_conditions():
                    out.write(" :disjunctive-preconditions")
                if self.problem_kind.has_equalities():
                    out.write(" :equality")
                if (
                    self.problem_kind.has_int_fluents()
                    or self.problem_kind.has_real_fluents()
                ):
                    out.write(" :numeric-fluents")
                if self.problem_kind.has_conditional_effects():
                    out.write(" :conditional-effects")
                if self.problem_kind.has_existential_conditions():
                    out.write(" :existential-preconditions")
                if self.problem_kind.has_universal_conditions():
                    out.write(" :universal-preconditions")
                if (
                    self.problem_kind.has_continuous_time()
                    or self.problem_kind.has_discrete_time()
                ):
                    out.write(" :durative-actions")
                if self.problem_kind.has_duration_inequalities():
                    out.write(" :duration-inequalities")
                if (
                    self.problem_kind.has_actions_cost()
                    or self.problem_kind.has_plan_length()
                ):
                    out.write(" :action-costs")
                out.write(")\n")

            if self.problem_kind.has_hierarchical_typing():
                user_types_hierarchy = self.problem.user_types_hierarchy
                out.write(f" (:types\n")
                stack: List["unified_planning.model.Type"] = (
                    user_types_hierarchy[None] if None in user_types_hierarchy else []
                )
                out.write(
                    f'    {" ".join(self._get_mangled_name(t) for t in stack)}{" " if len(self.problem.agents) > 0 else ""}ag - object\n'
                )
                out.write(
                    f'    {" ".join(self._get_mangled_name(ag) + "_type" for ag in self.problem.agents)} - ag\n'
                )
                while stack:
                    current_type = stack.pop()
                    direct_sons: List[
                        "unified_planning.model.Type"
                    ] = user_types_hierarchy[current_type]
                    if direct_sons:
                        stack.extend(direct_sons)
                        out.write(
                            f'    {" ".join([self._get_mangled_name(t) for t in direct_sons])} - {self._get_mangled_name(current_type)}\n'
                        )
                out.write(" )\n")
            else:
                out.write(
                    f' (:types {" ".join([self._get_mangled_name(t) for t in self.problem.user_types])}{" " if len(self.problem.agents) > 0 else ""}ag - object\n'
                    if len(self.problem.user_types) > 0
                    else ""
                )
                out.write(
                    f'    {" ".join(self._get_mangled_name(ag) + "_type" for ag in self.problem.agents)} - ag\n'
                )
                out.write(" )\n")

            if self.domain_objects is None:
                if self.unfactored:
                    temp_domain_objects: Dict[_UserType, Set[Object]] = {}
                    for ag in self.problem.agents:
                        self._populate_domain_objects(obe, ag)
                        assert self.domain_objects is not None
                        temp_domain_objects = temp_domain_objects | self.domain_objects
                        self.domain_objects = None
                    self.domain_objects = temp_domain_objects
                else:
                    # This method populates the self._domain_objects map
                    self._populate_domain_objects(obe, ag)
            assert self.domain_objects is not None

            if len(self.all_public_fluents) == 0:
                self._all_public_fluents(self.all_public_fluents, self.problem.agents)

            if len(self.domain_objects) > 0:
                out.write(" (:constants")
                for ut, os in self.domain_objects.items():
                    if len(os) > 0:
                        out.write(
                            f'\n   {" ".join([self._get_mangled_name(o) for o in os])} - {self._get_mangled_name(ut)}'
                        )
            if len(self.domain_objects_agents) > 0:
                for k, v in self.domain_objects_agents.items():
                    if len(v) > 0:
                        out.write(f"\n   {self._get_mangled_name(k)} - {v}")

            if len(self.domain_objects) > 0 or len(self.domain_objects_agents) > 0:
                out.write("\n )\n")

            (
                predicates_environment,
                functions_environment,
            ) = self.get_predicates_functions(self.problem.ma_environment)

            predicates_agents = []
            functions_agent = []
            nl = "\n   "
            if self.unfactored:
                for ag in self.problem.agents:
                    predicates_agent, functions_agent = self.get_predicates_functions(
                        ag, is_private=True
                    )
                    if len(predicates_agent) > 0:
                        predicates_agents.append(
                            f"  (:private ?agent - {ag.name + '_type'}\n   {nl.join(predicates_agent)})\n"
                        )
            else:
                predicates_agents, functions_agent = self.get_predicates_functions(
                    ag, is_private=True
                )

            predicates_public_agent = []
            functions_public_agent = []
            for f in self.all_public_fluents:
                params = []
                i = 0
                for param in f.signature:
                    if param.type.is_user_type():
                        params.append(
                            f" {self._get_mangled_name(param)} - {self._get_mangled_name(param.type)}"
                        )
                        i += 1
                    else:
                        raise UPTypeError("MA-PDDL supports only user type parameters")
                expression = (
                    f'(a_{self._get_mangled_name(f)} ?agent - {"ag"}{"".join(params)})'
                )
                if f.type.is_bool_type():
                    predicates_public_agent.append(expression)
                elif f.type.is_int_type() or f.type.is_real_type():
                    functions_public_agent.append(expression)
                else:
                    raise UPTypeError(
                        "MA-PDDL supports only boolean and numerical fluents"
                    )

            predicates_agent_goal = []
            functions_agent_goal = []
            for g in self.problem.goals:
                if g.is_dot():
                    f = g.args[0].fluent()
                    agent = g.agent()
                    # args = g.args
                    # objects = g.args[0].args
                    if f not in ag.fluents and f not in self.all_public_fluents:
                        if f.type.is_bool_type():
                            params = []
                            i = 0
                            for param in f.signature:
                                if param.type.is_user_type():
                                    params.append(
                                        f" {self._get_mangled_name(param)} - {self._get_mangled_name(param.type)}"
                                    )
                                    i += 1
                                else:
                                    raise UPTypeError(
                                        "MA-PDDL supports only user type parameters"
                                    )
                            predicates_agent_goal.append(
                                f'(a_{self._get_mangled_name(f)} ?agent - {"ag"}{"".join(params)})'
                            )
                        elif f.type.is_int_type() or f.type.is_real_type():
                            params = []
                            i = 0
                            for param in f.signature:
                                if param.type.is_user_type():
                                    params.append(
                                        f" {self._get_mangled_name(param)} - {self._get_mangled_name(param.type)}"
                                    )
                                    i += 1
                                else:
                                    raise UPTypeError(
                                        "MA-PDDL supports only user type parameters"
                                    )
                            functions_agent_goal.append(
                                f'(a_{self._get_mangled_name(f)} ?agent - {"ag"}{"".join(params)})'
                            )
                        else:
                            raise UPTypeError(
                                "MA-PDDL supports only boolean and numerical fluents"
                            )

            nl = "\n  "
            out.write(
                f" (:predicates\n "
                if len(predicates_environment) > 0
                or len(predicates_agents) > 0
                or len(predicates_agent_goal) > 0
                or len(predicates_public_agent) > 0
                else ""
            )
            out.write(
                f"  {nl.join(predicates_agent_goal)}\n"
                if len(predicates_agent_goal) > 0
                else ""
            )
            out.write(
                f" {nl.join(predicates_environment)}\n"
                if len(predicates_environment) > 0
                else ""
            )
            out.write(
                f"  {nl.join(predicates_public_agent)}\n"
                if len(predicates_public_agent) > 0
                else ""
            )

            nl = "\n   "

            if self.unfactored:
                out.write(
                    "".join(predicates_agents) if len(predicates_agents) > 0 else ""
                )
            else:
                out.write(
                    f"  (:private\n   {nl.join(predicates_agents)})"
                    if len(predicates_agents) > 0
                    else ""
                )
            out.write(
                f")\n"
                if len(predicates_environment) > 0
                or len(predicates_agents) > 0
                or len(predicates_agent_goal) > 0
                or len(predicates_public_agent) > 0
                else ""
            )

            out.write(
                f" (:functions\n"
                if len(functions_environment) > 0
                or len(functions_agent) > 0
                or len(functions_agent_goal) > 0
                or len(functions_public_agent) > 0
                else ""
            )
            out.write(
                f' {" ".join(functions_environment)}\n'
                if len(functions_environment) > 0
                else ""
            )
            out.write(
                f' {" ".join(functions_agent_goal)}\n'
                if len(functions_agent_goal) > 0
                else ""
            )
            out.write(
                f' {" ".join(functions_public_agent)}\n'
                if len(functions_public_agent) > 0
                else ""
            )
            out.write(
                f'  (:private{" ".join(functions_agent)})\n'
                if len(functions_agent) > 0
                else ""
            )
            out.write(
                f" )\n"
                if len(functions_environment) > 0
                or len(functions_agent) > 0
                or len(functions_agent_goal) > 0
                or len(functions_public_agent) > 0
                else ""
            )

            costs: dict = {}

            def write_action(ag):
                converter = ConverterToMAPDDLString(
                    self.problem, self._get_mangled_name, ag, unfactored=self.unfactored
                )
                for a in ag.actions:
                    if isinstance(a, up.model.InstantaneousAction):
                        if self.unfactored:
                            out.write(
                                f" (:action {self._get_mangled_name(a)}_{ag.name}"
                            )
                        else:
                            out.write(f" (:action {self._get_mangled_name(a)}")
                        if self.unfactored:
                            out.write(f'\n  :agent ?{ag.name} - {ag.name + "_type"}')

                        out.write(f"\n  :parameters (")

                        if not self.unfactored:
                            out.write(
                                f' ?{self._get_mangled_name(ag)} - {self._get_mangled_name(ag) +"_type"}'
                            )
                        for ap in a.parameters:
                            if ap.type.is_user_type():
                                out.write(
                                    f" {self._get_mangled_name(ap)} - {self._get_mangled_name(ap.type)}"
                                )
                            else:
                                raise UPTypeError(
                                    "MA-PDDL supports only user type parameters"
                                )
                        out.write(")")
                        if len(a.preconditions) > 0:
                            out.write(f"\n  :precondition (and \n")
                            for p in a.preconditions:
                                out.write(f"   {converter.convert(p)}\n")
                            out.write(f"  )")

                        if len(a.effects) > 0:
                            out.write("\n  :effect (and\n")
                            for e in a.effects:
                                _write_effect(
                                    e,
                                    None,
                                    out,
                                    converter,
                                    self.rewrite_bool_assignments,
                                    self._get_mangled_name,
                                )

                            if a in costs:
                                out.write(
                                    f"   (increase (total-cost) {converter.convert(costs[a])})"
                                )
                            out.write(")")
                        out.write(")\n")
                    elif isinstance(a, DurativeAction):
                        out.write(f" (:durative-action {self._get_mangled_name(a)}")
                        out.write(f"\n  :parameters (")
                        for ap in a.parameters:
                            if ap.type.is_user_type():
                                out.write(
                                    f" {self._get_mangled_name(ap)} - {self._get_mangled_name(ap.type)}"
                                )
                            else:
                                raise UPTypeError(
                                    "MA-PDDL supports only user type parameters"
                                )
                        out.write(")")
                        l, r = a.duration.lower, a.duration.upper
                        if l == r:
                            out.write(
                                f"\n  :duration (= ?duration {converter.convert(l)})"
                            )
                        else:
                            out.write(f"\n  :duration (and ")
                            if a.duration.is_left_open():
                                out.write(f"(> ?duration {converter.convert(l)})")
                            else:
                                out.write(f"(>= ?duration {converter.convert(l)})")
                            if a.duration.is_right_open():
                                out.write(f"(< ?duration {converter.convert(r)})")
                            else:
                                out.write(f"(<= ?duration {converter.convert(r)})")
                            out.write(")")
                        if len(a.conditions) > 0:
                            out.write(f"\n  :condition (and ")
                            for interval, cl in a.conditions.items():
                                for c in cl:
                                    if interval.lower == interval.upper:
                                        if interval.lower.is_from_start():
                                            out.write(
                                                f"(at start {converter.convert(c)})"
                                            )
                                        else:
                                            out.write(
                                                f"(at end {converter.convert(c)})"
                                            )
                                    else:
                                        if not interval.is_left_open():
                                            out.write(
                                                f"(at start {converter.convert(c)})"
                                            )
                                        out.write(f"(over all {converter.convert(c)})")
                                        if not interval.is_right_open():
                                            out.write(
                                                f"(at end {converter.convert(c)})"
                                            )
                            out.write(")")
                        if len(a.effects) > 0:
                            out.write("\n  :effect (and")
                            for t, el in a.effects.items():
                                for e in el:
                                    _write_effect(
                                        e,
                                        t,
                                        out,
                                        converter,
                                        self.rewrite_bool_assignments,
                                        self._get_mangled_name,
                                    )
                            if a in costs:
                                out.write(
                                    f" (at end (increase (total-cost) {converter.convert(costs[a])}))"
                                )
                            out.write(")")
                        out.write(")\n")
                    else:
                        raise NotImplementedError

            if self.unfactored:
                for ag in self.problem.agents:
                    write_action(ag)
            else:
                write_action(ag)

            out.write(")\n")

            ag_domains[self._get_mangled_name(ag)] = out.getvalue()
            out.close()
            self.domain_objects = None
            self.domain_objects_agents = {}
            # self.all_public_fluents = []
            if self.unfactored:
                break

        return ag_domains

    def _write_problem(self):
        ag_problems = {}
        for ag in self.problem.agents:
            out = StringIO()
            if self.problem.name is None:
                name = "ma-pddl"
            else:
                name = _get_pddl_name(self.problem)
            out.write(f"(define (problem {name}-problem)\n")
            out.write(f" (:domain {name}-domain)\n")
            if self.domain_objects is None:
                if self.unfactored:
                    temp_domain_objects: Dict[_UserType, Set[Object]] = {}
                    for ag in self.problem.agents:
                        self._populate_domain_objects(ObjectsExtractor(), ag)
                        assert self.domain_objects is not None
                        temp_domain_objects = temp_domain_objects | self.domain_objects
                        self.domain_objects = None
                    self.domain_objects = temp_domain_objects
                else:
                    # This method populates the self._domain_objects map
                    self._populate_domain_objects(ObjectsExtractor(), ag)
            assert self.domain_objects is not None
            if len(self.problem.user_types) > 0:
                out.write(" (:objects")
                for t in self.problem.user_types:
                    constants_of_this_type = self.domain_objects.get(
                        cast(_UserType, t), None
                    )
                    if constants_of_this_type is None:
                        objects = [o for o in self.problem.all_objects if o.type == t]
                    else:
                        objects = [
                            o
                            for o in self.problem.all_objects
                            if o.type == t and o not in constants_of_this_type
                        ]
                    if len(objects) > 0:
                        out.write(
                            f'\n   {" ".join([self._get_mangled_name(o) for o in objects])} - {self._get_mangled_name(t)}'
                        )

            # If agents are not defined as "constant" in the domain, they are defined in the problem
            if len(self.problem.agents) > 0:
                for agent in self.problem.agents:
                    if agent not in self.domain_objects_agents.keys():
                        out.write(
                            f'\n   {self._get_mangled_name(agent)} - {self._get_mangled_name(agent) + "_type"}'
                        )
                    else:
                        out.write(f"")

            out.write("\n )\n")
            converter = ConverterToMAPDDLString(
                self.problem, self._get_mangled_name, ag, unfactored=self.unfactored
            )
            out.write(" (:init")

            for f, v in self.problem.initial_values.items():
                if v.is_true():
                    if f.is_dot():
                        fluent = f.args[0].fluent()
                        args = f.args
                        if not self.unfactored:
                            if (
                                fluent in self.all_public_fluents
                                or fluent in ag.fluents
                                and f.agent() == ag.name
                            ):
                                out.write(f"\n  {converter.convert(f)}")
                            elif (
                                f.agent() != ag.name
                                and fluent in self.all_public_fluents
                            ):
                                out.write(f"\n  {converter.convert(f)}")
                            else:
                                out.write(f"")
                        else:
                            out.write(f"\n  {converter.convert(f)}")
                    else:
                        out.write(f"\n  {converter.convert(f)}")
                elif v.is_false():
                    if self.explicit_false_initial_states:
                        if f.is_dot():
                            fluent = f.args[0].fluent()
                            args = f.args
                            if not self.unfactored:
                                if (
                                    fluent in self.all_public_fluents
                                    or fluent in ag.fluents
                                    and f.agent() == ag.name
                                ):
                                    out.write(f"\n  (not {converter.convert(f)})")
                                elif (
                                    f.agent() != ag.name
                                    and fluent in self.all_public_fluents
                                ):
                                    out.write(f"\n  (not {converter.convert(f)})")
                                else:
                                    out.write(f"")
                            else:
                                out.write(f"\n  (not {converter.convert(f)})")
                        else:
                            out.write(f"\n  (not {converter.convert(f)})")
                    else:
                        pass
                else:
                    out.write(f"\n  (= {converter.convert(f)} {converter.convert(v)})")
            if self.problem.kind.has_actions_cost():
                out.write(f" (= (total-cost) 0)")
            out.write(")\n")
            out.write(f" (:goal (and")
            for p in self.problem.goals:
                out.write(f" {converter.convert(p)}")
            out.write(f"))")
            out.write("\n)")
            ag_problems[self._get_mangled_name(ag)] = out.getvalue()
            out.close()
            self.domain_objects = None
            self.domain_objects_agents = {}
            # self.all_public_fluents = []
            if self.unfactored:
                break
        return ag_problems

    def print_ma_domain_agent(self, agent_name):
        """Prints to std output the `MA-PDDL` domain."""
        domains = self._write_domain()
        domain_agent = domains[agent_name]
        sys.stdout.write(domain_agent)

    def print_ma_problem_agent(self, agent_name):
        """Prints to std output the `MA-PDDL` problem."""
        problems = self._write_problem()
        problem_agent = problems[agent_name]
        sys.stdout.write(problem_agent)

    def get_ma_domains(self) -> Dict:
        """Returns the `MA-PDDL` domains."""
        domains = self._write_domain()
        return domains

    def get_ma_domain_agent(self, agent_name) -> str:
        """Returns the `MA-PDDL` agent domain."""
        domains = self._write_domain()
        domain_agent = domains[agent_name]
        return domain_agent

    def get_ma_problems(self) -> Dict:
        """Returns the `MA-PDDL` problems."""
        problems = self._write_problem()
        return problems

    def get_ma_problem_agent(self, agent_name) -> str:
        """Returns the `MA-PDDL` agent problem."""
        problems = self._write_problem()
        problem_agent = problems[agent_name]
        return problem_agent

    def write_ma_domain(self, directory_name):
        """Dumps to file the `MA-PDDL` domains."""
        ag_domains = self._write_domain()
        osy.makedirs(directory_name, exist_ok=True)
        for ag, domain in ag_domains.items():
            if not self.unfactored:
                name_domain = ag + "_"
            else:
                name_domain = ""
            path_ma_pddl = osy.path.join(directory_name, name_domain + "domain.pddl")
            with open(path_ma_pddl, "w") as f:
                f.write(domain)

    def write_ma_problem(self, directory_name):
        """Dumps to file the `MA-PDDL` problems."""
        ag_problems = self._write_problem()
        osy.makedirs(directory_name, exist_ok=True)
        for ag, problem in ag_problems.items():
            if not self.unfactored:
                name_problem = ag + "_"
            else:
                name_problem = ""
            path_ma_pddl = osy.path.join(directory_name, name_problem + "problem.pddl")
            with open(path_ma_pddl, "w") as f:
                f.write(problem)

    def get_predicates_functions(
        self,
        obj: Union[
            up.model.multi_agent.Agent,
            up.model.multi_agent.ma_environment.MAEnvironment,
        ],
        is_private: bool = False,
    ):
        if isinstance(obj, up.model.multi_agent.Agent):
            fluents_list = obj.private_fluents if is_private else obj.public_fluents
            prefix = "a_"
        else:
            fluents_list = obj.fluents
            prefix = ""
        predicates = []
        functions = []
        for f in fluents_list:
            params = []
            i = 0
            for param in f.signature:
                if param.type.is_user_type():
                    params.append(
                        f" {self._get_mangled_name(param)} - {self._get_mangled_name(param.type)}"
                    )
                    i += 1
                else:
                    raise UPTypeError("MA-PDDL supports only user type parameters")
            if isinstance(obj, up.model.multi_agent.Agent):
                if self.unfactored:
                    expression = f'({prefix}{self._get_mangled_name(f)}_{obj.name} ?agent - {obj.name + "_type"}{"".join(params)})'
                else:
                    expression = f'({prefix}{self._get_mangled_name(f)} ?agent - {"ag"}{"".join(params)})'
            else:
                expression = f'({prefix}{self._get_mangled_name(f)}{"".join(params)})'
            if f.type.is_bool_type():
                predicates.append(expression)
            elif f.type.is_int_type() or f.type.is_real_type():
                functions.append(expression)
            else:
                raise UPTypeError("MA-PDDL supports only boolean and numerical fluents")
        return predicates, functions

    def _get_mangled_name(
        self,
        item: WithName,
    ) -> str:
        """This function returns a valid and unique MA-PDDL name."""

        # If we already encountered this item, return it
        if item in self.otn_renamings:
            return self.otn_renamings[item]

        if isinstance(item, up.model.Type):
            assert item.is_user_type()
            original_name = cast(_UserType, item).name
            tmp_name = _get_pddl_name(item)
            # If the problem is hierarchical and the name is object, we want to change it
            if self.problem_kind.has_hierarchical_typing() and tmp_name == "object":
                tmp_name = f"{tmp_name}_"
        else:
            original_name = item.name
            tmp_name = _get_pddl_name(item)
        # if the ma-pddl valid name is the same of the original one and it does not create conflicts,
        # it can be returned
        if not isinstance(item, up.model.multi_agent.Agent):
            if tmp_name == original_name and tmp_name not in self.nto_renamings:
                new_name = tmp_name
            else:
                count = 0
                new_name = tmp_name
                while self.problem.has_name(new_name) or new_name in self.nto_renamings:
                    new_name = f"{tmp_name}_{count}"
                    count += 1
            assert (
                new_name not in self.nto_renamings
                and new_name not in self.otn_renamings.values()
            )

        else:
            new_name = tmp_name
        self.otn_renamings[item] = new_name
        self.nto_renamings[new_name] = item
        return new_name

    def get_item_named(self, name: str) -> WithName:
        """
        Since `MA-PDDL` has a stricter set of possible naming compared to the `unified_planning`, when writing
        a :class:`~unified_planning.model.Problem` it is possible that some things must be renamed. This is why the `MAPDDLWriter`
        offers this method, that takes a `MA-PDDL` name and returns the original `unified_planning` data structure that corresponds
        to the `MA-PDDL` entity with the given name.

        This method takes a name used in the `MA-PDDL` domain or `MA-PDDL` problem generated by this `MAPDDLWriter` and returns the original
        item in the `unified_planning` `Problem`.

        :param name: The name used in the generated `MA-PDDL`.
        :return: The `unified_planning` model entity corresponding to the given name.
        """
        try:
            return self.nto_renamings[name]
        except KeyError:
            raise UPException(f"The name {name} does not correspond to any item.")

    def get_ma_pddl_name(
        self,
        item: Union[
            "up.model.Type",
            "up.model.Action",
            "up.model.Fluent",
            "up.model.Object",
            "up.model.Parameter",
            "up.model.Variable",
        ],
    ) -> str:
        """
        This method takes an item in the :class:`~unified_planning.model.MultiAgentProblem` and returns the chosen name for the same item in the `MA-PDDL` problem
        or `MA-PDDL` domain generated by this `MAPDDLWriter`.

        :param item: The `unified_planning` entity renamed by this `MAPDDLWriter`.
        :return: The `MA-PDDL` name of the given item.
        """
        try:
            return self.otn_renamings[item]
        except KeyError:
            raise UPException(
                f"The item {item} does not correspond to any item renamed."
            )

    def _all_public_fluents(
        self,
        list_to_update: Set[Fluent],
        agents: List[up.model.multi_agent.Agent],
    ) -> None:
        """This function creates a list with all public fluents of all agents."""
        for agent in agents:
            for fluent in agent.public_fluents:
                list_to_update.add(fluent)

    def _populate_domain_objects(
        self, obe: ObjectsExtractor, agent: "up.model.multi_agent.Agent"
    ):
        self.domain_objects = {}
        self.domain_objects_agents = {}
        # Iterate the actions to retrieve domain objects
        import unified_planning.model.walkers as walkers

        get_dots = walkers.AnyGetter(lambda x: x.is_dot())
        for a in agent.actions:
            if isinstance(a, up.model.InstantaneousAction):
                for p in a.preconditions:
                    for d in get_dots.get(p):
                        _update_domain_objects_ag(
                            self.domain_objects_agents, self.problem.agent(d.agent())
                        )
                    _update_domain_objects(self.domain_objects, obe.get(p))
                for e in a.effects:
                    if e.is_conditional():
                        _update_domain_objects(
                            self.domain_objects, obe.get(e.condition)
                        )
                    _update_domain_objects(self.domain_objects, obe.get(e.fluent))
                    _update_domain_objects(self.domain_objects, obe.get(e.value))
            elif isinstance(a, DurativeAction):
                _update_domain_objects(self.domain_objects, obe.get(a.duration.lower))
                _update_domain_objects(self.domain_objects, obe.get(a.duration.upper))
                for cl in a.conditions.values():
                    for c in cl:
                        _update_domain_objects(self.domain_objects, obe.get(c))
                for el in a.effects.values():
                    for e in el:
                        if e.is_conditional():
                            _update_domain_objects(
                                self.domain_objects, obe.get(e.condition)
                            )
                        _update_domain_objects(self.domain_objects, obe.get(e.fluent))
                        _update_domain_objects(self.domain_objects, obe.get(e.value))


def _update_domain_objects(
    dict_to_update: Dict[_UserType, Set[Object]], values: Dict[_UserType, Set[Object]]
) -> None:
    """Small utility method that updated a UserType -> Set[Object] dict with another dict of the same type."""
    for ut, os in values.items():
        os_to_update = dict_to_update.setdefault(ut, set())
        os_to_update |= os


def _update_domain_objects_ag(
    dict_to_update: Dict["up.model.multi_agent.Agent", str],
    agent: up.model.multi_agent.Agent,
) -> None:
    """Small utility method that updated the dict domain_objects_agents."""
    dict_to_update.setdefault(agent, agent.name + "_type")
