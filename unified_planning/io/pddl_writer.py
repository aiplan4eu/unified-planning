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


from fractions import Fraction
import sys
import re

from decimal import Decimal, localcontext
from warnings import warn

import unified_planning as up
import unified_planning.model.walkers as walkers
from unified_planning.model import (
    InstantaneousAction,
    DurativeAction,
    Fluent,
    Parameter,
    Problem,
    Object,
    Effect,
    Timing,
)
from unified_planning.exceptions import (
    UPTypeError,
    UPProblemDefinitionError,
    UPException,
)
from unified_planning.model.htn import HierarchicalProblem
from unified_planning.model.types import _UserType
from unified_planning.plans import (
    SequentialPlan,
    TimeTriggeredPlan,
    Plan,
    ActionInstance,
)
from typing import Callable, Dict, IO, List, Optional, Set, Union, cast
from io import StringIO
from functools import reduce

GENERAL_PDDL_KEYWORDS = {
    "define",
    "domain",
    "requirements",
    "types",
    "constants",
    "predicates",
    "problem",
    "either",
    "number",
    "action",
    "parameters",
    "precondition",
    "effect",
    "and",
    "forall",
    "or",
    "not",
    "imply",
    "exists",
    "scale-up",
    "scale-down",
    "increase",
    "decrease",
    "derived",
    "objects",
    "init",
    "goal",
    "when",
    "metric",
    "minimize",
    "maximize",
    "total-time",
    "strips",
    "negative-preconditions",
    "typing",
    "disjunctive-preconditions",
    "equality",
    "existential-preconditions",
    "universal-preconditions",
    "quantified-preconditions",
    "conditional-effects",
    "fluents",
    "adl",
    "durative-actions",
    "derived-predicates",
    "timed-initial-literals",
    "timed-initial-effects",
    "contingent",
    "time",
    "continuous-effects",
}

TEMPORAL_PDDL_KEYWORDS = GENERAL_PDDL_KEYWORDS.union(
    {
        "durative-action",
        "duration",
        "condition",
        "at",
        "over",
        "start",
        "end",
        "all",
    }
)

PDDL3_KEYWORDS = TEMPORAL_PDDL_KEYWORDS.union(
    {
        "constraints",
        "preferences",
        "is-violated",
        "preference",
        "always",
        "sometime",
        "within",
        "at-most-once",
        "sometime-after",
        "sometime-before",
        "always-within",
        "hold-during",
        "hold-after",
    }
)

PDDL_PLUS_KEYWORDS = GENERAL_PDDL_KEYWORDS.union({"process", "event"})

# The following map is used to mangle the invalid names by their class.
INITIAL_LETTER: Dict[type, str] = {
    InstantaneousAction: "a",
    DurativeAction: "a",
    Fluent: "f",
    Parameter: "p",
    Problem: "p",
    Object: "o",
}

WithName = Union[
    "up.model.Type",
    "up.model.Action",
    "up.model.NaturalTransition",
    "up.model.Fluent",
    "up.model.Object",
    "up.model.Parameter",
    "up.model.Variable",
    "up.model.multi_agent.Agent",
    "up.model.htn.Method",
    "up.model.htn.Task",
]
MangleFunction = Callable[[WithName], str]


class ObjectsExtractor(walkers.DagWalker):
    """Returns the object instances appearing in the expression."""

    def __init__(self):
        walkers.dag.DagWalker.__init__(self)

    def get(self, expression: "up.model.FNode") -> Dict[_UserType, Set[Object]]:
        """Returns all the free vars of the given expression."""
        return self.walk(expression)

    def walk_object_exp(
        self, expression: "up.model.FNode", args: List[Dict[_UserType, Set[Object]]]
    ) -> Dict[_UserType, Set[Object]]:
        res: Dict[_UserType, Set[Object]] = {}
        for a in args:
            _update_domain_objects(res, a)
        obj = expression.object()
        assert obj.type.is_user_type()
        res.setdefault(cast(_UserType, obj.type), set()).add(obj)
        return res

    @walkers.handles(
        set(up.model.OperatorKind).difference((up.model.OperatorKind.OBJECT_EXP,))
    )
    def walk_all_types(
        self, expression: "up.model.FNode", args: List[Dict[_UserType, Set[Object]]]
    ) -> Dict[_UserType, Set[Object]]:
        res: Dict[_UserType, Set[Object]] = {}
        for a in args:
            _update_domain_objects(res, a)
        return res


class ConverterToPDDLString(walkers.DagWalker):
    """Expression converter to a PDDL string."""

    DECIMAL_PRECISION = 10  # Number of decimal places to print real constants

    def __init__(
        self,
        environment: "up.environment.Environment",
        get_mangled_name: MangleFunction,
    ):
        walkers.DagWalker.__init__(self)
        self.get_mangled_name = get_mangled_name
        self.simplifier = environment.simplifier

    def convert(self, expression):
        """Converts the given expression to a PDDL string."""
        return self.walk(self.simplifier.simplify(expression))

    def convert_fraction(self, frac):
        with localcontext() as ctx:
            ctx.prec = self.DECIMAL_PRECISION
            dec = frac.numerator / Decimal(frac.denominator, ctx)

            if Fraction(dec) != frac:
                warn(
                    "The PDDL printer cannot exactly represent the real constant '%s'"
                    % frac
                )
            return float(dec)

    def walk_exists(self, expression, args):
        assert len(args) == 1
        vars_string_list = [
            f"{self.get_mangled_name(v)} - {self.get_mangled_name(v.type)}"
            for v in expression.variables()
        ]
        return f'(exists ({" ".join(vars_string_list)})\n {args[0]})'

    def walk_forall(self, expression, args):
        assert len(args) == 1
        vars_string_list = [
            f"{self.get_mangled_name(v)} - {self.get_mangled_name(v.type)}"
            for v in expression.variables()
        ]
        return f'(forall ({" ".join(vars_string_list)})\n {args[0]})'

    def walk_always(self, expression, args):
        assert len(args) == 1
        return f"(always {args[0]})"

    def walk_at_most_once(self, expression, args):
        assert len(args) == 1
        return f"(at-most-once {args[0]})"

    def walk_sometime(self, expression, args):
        assert len(args) == 1
        return f"(sometime {args[0]})"

    def walk_sometime_before(self, expression, args):
        assert len(args) == 2
        return f"(sometime-before {args[0]} {args[1]})"

    def walk_sometime_after(self, expression, args):
        assert len(args) == 2
        return f"(sometime-after {args[0]} {args[1]})"

    def walk_variable_exp(self, expression, args):
        assert len(args) == 0
        return f"{self.get_mangled_name(expression.variable())}"

    def walk_and(self, expression, args):
        assert len(args) > 1
        return f'(and {" ".join(args)})'

    def walk_or(self, expression, args):
        assert len(args) > 1
        return f'(or {" ".join(args)})'

    def walk_not(self, expression, args):
        assert len(args) == 1
        return f"(not {args[0]})"

    def walk_implies(self, expression, args):
        assert len(args) == 2
        return f"(imply {args[0]} {args[1]})"

    def walk_iff(self, expression, args):
        assert len(args) == 2
        return f"(and (imply {args[0]} {args[1]}) (imply {args[1]} {args[0]}) )"

    def walk_fluent_exp(self, expression, args):
        fluent = expression.fluent()
        return f'({self.get_mangled_name(fluent)}{" " if len(args) > 0 else ""}{" ".join(args)})'

    def walk_param_exp(self, expression, args):
        assert len(args) == 0
        p = expression.parameter()
        return f"{self.get_mangled_name(p)}"

    def walk_object_exp(self, expression, args):
        assert len(args) == 0
        o = expression.object()
        return f"{self.get_mangled_name(o)}"

    def walk_bool_constant(self, expression, args):
        raise up.exceptions.UPUnreachableCodeError(
            f"Found expression {expression} in PDDL"
        )

    def walk_real_constant(self, expression, args):
        assert len(args) == 0
        frac = expression.constant_value()
        return str(self.convert_fraction(frac))

    def walk_int_constant(self, expression, args):
        assert len(args) == 0
        return str(expression.constant_value())

    def walk_plus(self, expression, args):
        assert len(args) > 1
        return reduce(lambda x, y: f"(+ {y} {x})", args)

    def walk_minus(self, expression, args):
        assert len(args) == 2
        return f"(- {args[0]} {args[1]})"

    def walk_times(self, expression, args):
        assert len(args) > 1
        return reduce(lambda x, y: f"(* {y} {x})", args)

    def walk_div(self, expression, args):
        assert len(args) == 2
        return f"(/ {args[0]} {args[1]})"

    def walk_le(self, expression, args):
        assert len(args) == 2
        return f"(<= {args[0]} {args[1]})"

    def walk_lt(self, expression, args):
        assert len(args) == 2
        return f"(< {args[0]} {args[1]})"

    def walk_equals(self, expression, args):
        assert len(args) == 2
        return f"(= {args[0]} {args[1]})"


class PDDLWriter:
    """
    This class can be used to write a :class:`~unified_planning.model.Problem` in `PDDL`.
    The constructor of this class takes the problem to write and 3 flags:
    needs_requirements determines if the printed problem must have the :requirements,
    rewrite_bool_assignments determines if this writer will write
    non constant boolean assignment as conditional effects.
    empty_preconditions determines if this writer will write ':precondition ()' in case of an instantenuous
    action without preconditions instead of writing nothing or similar with conditions in durative actions.
    """

    def __init__(
        self,
        problem: "up.model.Problem",
        needs_requirements: bool = True,
        rewrite_bool_assignments: bool = False,
        empty_preconditions: bool = False,
    ):
        self.problem = problem
        self.problem_kind = self.problem.kind
        self.needs_requirements = needs_requirements
        self.rewrite_bool_assignments = rewrite_bool_assignments
        self.empty_preconditions = empty_preconditions
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

        if len(self.problem.processes) > 0 or len(self.problem.events) > 0:
            self.pddl_keywords = PDDL_PLUS_KEYWORDS
        elif len(self.problem.trajectory_constraints) > 0:
            self.pddl_keywords = PDDL3_KEYWORDS
        elif any(
            map(
                lambda action: isinstance(action, up.model.action.DurativeAction),
                self.problem.actions,
            )
        ):
            self.pddl_keywords = TEMPORAL_PDDL_KEYWORDS
        else:
            self.pddl_keywords = GENERAL_PDDL_KEYWORDS

    def _write_parameters(self, out, a):
        for ap in a.parameters:
            if ap.type.is_user_type():
                out.write(
                    f" {self._get_mangled_name(ap)} - {self._get_mangled_name(ap.type)}"
                )
            else:
                raise UPTypeError("PDDL supports only user type parameters")

    def _write_domain(self, out: IO[str]):
        if self.problem_kind.has_intermediate_conditions_and_effects():
            raise UPProblemDefinitionError(
                "PDDL does not support ICE.\nICE are Intermediate Conditions and Effects therefore when an Effect (or Condition) are not at StartTIming(0) or EndTIming(0)."
            )
        if self.problem_kind.has_timed_goals():
            raise UPProblemDefinitionError("PDDL does not support timed goals.")
        obe = ObjectsExtractor()
        out.write("(define ")
        if self.problem.name is None:
            name = "pddl"
        else:
            name = _get_pddl_name(self.problem, self.pddl_keywords)
        out.write(f"(domain {name}-domain)\n")

        if self.needs_requirements:
            out.write(" (:requirements :strips")
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
                or self.problem_kind.has_fluents_in_actions_cost()
            ):
                out.write(" :numeric-fluents")
            if self.problem_kind.has_conditional_effects():
                out.write(" :conditional-effects")
            if self.problem_kind.has_existential_conditions():
                out.write(" :existential-preconditions")
            if (
                self.problem_kind.has_trajectory_constraints()
                or self.problem_kind.has_state_invariants()
            ):
                out.write(" :constraints")
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
                self.problem_kind.has_increase_continuous_effects()
                or self.problem_kind.has_decrease_continuous_effects()
            ):
                out.write(" :continuous-effects")
            if (
                self.problem_kind.has_actions_cost()
                or self.problem_kind.has_plan_length()
            ):
                out.write(" :action-costs")
            if self.problem_kind.has_timed_effects():
                only_bool = True
                for le in self.problem.timed_effects.values():
                    for e in le:
                        if not e.fluent.type.is_bool_type():
                            only_bool = False
                if not only_bool:
                    out.write(" :timed-initial-effects")
                else:
                    out.write(" :timed-initial-literals")
            if self.problem_kind.has_hierarchical():
                out.write(" :hierarchy")  # HTN / HDDL
            if self.problem_kind.has_method_preconditions():
                out.write(" :method-preconditions")
            if self.problem_kind.has_processes() or self.problem_kind.has_events():
                out.write(" :time")
            out.write(")\n")

        if self.problem_kind.has_hierarchical_typing():
            user_types_hierarchy = self.problem.user_types_hierarchy
            out.write(f" (:types\n")
            stack: List["up.model.Type"] = (
                user_types_hierarchy[None] if None in user_types_hierarchy else []
            )
            out.write(
                f'    {" ".join(self._get_mangled_name(t) for t in stack)} - object\n'
            )
            while stack:
                current_type = stack.pop()
                direct_sons: List["up.model.Type"] = user_types_hierarchy[current_type]
                if direct_sons:
                    stack.extend(direct_sons)
                    out.write(
                        f'    {" ".join([self._get_mangled_name(t) for t in direct_sons])} - {self._get_mangled_name(current_type)}\n'
                    )
            out.write(" )\n")
        else:
            pddl_types = [
                self._get_mangled_name(t)
                for t in self.problem.user_types
                if cast(_UserType, t).name != "object"
            ]
            out.write(
                f' (:types {" ".join(pddl_types)})\n' if len(pddl_types) > 0 else ""
            )

        if self.domain_objects is None:
            # This method populates the self._domain_objects map
            self._populate_domain_objects(obe)
        assert self.domain_objects is not None

        if len(self.domain_objects) > 0:
            out.write(" (:constants")
            for ut, os in self.domain_objects.items():
                if len(os) > 0:
                    out.write(
                        f'\n   {" ".join([self._get_mangled_name(o) for o in os])} - {self._get_mangled_name(ut)}'
                    )
            out.write("\n )\n")

        predicates = []
        functions = []
        for f in self.problem.fluents:
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
                        raise UPTypeError("PDDL supports only user type parameters")
                predicates.append(f'({self._get_mangled_name(f)}{"".join(params)})')
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
                        raise UPTypeError("PDDL supports only user type parameters")
                functions.append(f'({self._get_mangled_name(f)}{"".join(params)})')
            else:
                raise UPTypeError("PDDL supports only boolean and numerical fluents")
        if self.problem.kind.has_actions_cost() or self.problem.kind.has_plan_length():
            functions.append("(total-cost)")
        predicates_string = "\n             ".join(predicates)
        out.write(
            f" (:predicates \n             {predicates_string}\n )\n"
            if len(predicates) > 0
            else ""
        )
        functions_string = "\n             ".join(functions)
        out.write(
            f" (:functions \n             {functions_string}\n )\n"
            if len(functions) > 0
            else ""
        )

        converter = ConverterToPDDLString(
            self.problem.environment, self._get_mangled_name
        )
        costs: Dict[
            Union[up.model.NaturalTransition, up.model.Action], Optional[up.model.FNode]
        ] = {}
        metrics = self.problem.quality_metrics
        if len(metrics) == 1:
            metric = metrics[0]
            if isinstance(metric, up.model.metrics.MinimizeActionCosts):
                for a in self.problem.actions:
                    cost_exp = metric.get_action_cost(a)
                    costs[a] = cost_exp
                    if cost_exp is not None:
                        _update_domain_objects(self.domain_objects, obe.get(cost_exp))
            elif metric.is_minimize_sequential_plan_length():
                for a in self.problem.actions:
                    costs[a] = self.problem.environment.expression_manager.Int(1)
        elif len(metrics) > 1:
            raise up.exceptions.UPUnsupportedProblemTypeError(
                "Only one metric is supported!"
            )
        em = self.problem.environment.expression_manager
        if isinstance(self.problem, HierarchicalProblem):
            for task in self.problem.tasks:
                out.write(f" (:task {self._get_mangled_name(task)}")
                out.write(f"\n  :parameters (")
                for ap in task.parameters:
                    if ap.type.is_user_type():
                        out.write(
                            f" {self._get_mangled_name(ap)} - {self._get_mangled_name(ap.type)}"
                        )
                    else:
                        raise UPTypeError("PDDL supports only user type parameters")
                out.write("))\n")

            for m in self.problem.methods:
                out.write(f" (:method {self._get_mangled_name(m)}")
                out.write(f"\n  :parameters (")
                for ap in m.parameters:
                    if ap.type.is_user_type():
                        out.write(
                            f" {self._get_mangled_name(ap)} - {self._get_mangled_name(ap.type)}"
                        )
                    else:
                        raise UPTypeError("PDDL supports only user type parameters")
                out.write(")")

                params_str = " ".join(
                    converter.convert(em.ParameterExp(p))
                    for p in m.achieved_task.parameters
                )
                out.write(
                    f"\n  :task ({self._get_mangled_name(m.achieved_task.task)} {params_str})"
                )
                if len(m.preconditions) > 0:
                    precond_str: List[str] = []
                    for p in (c.simplify() for c in m.preconditions):
                        if not p.is_true():
                            if p.is_and():
                                precond_str.extend(map(converter.convert, p.args))
                            else:
                                precond_str.append(converter.convert(p))
                    out.write(f'\n  :precondition (and {" ".join(precond_str)})')
                elif len(m.preconditions) == 0 and self.empty_preconditions:
                    out.write(f"\n  :precondition ()")
                self._write_task_network(m, out, converter)
                out.write(")\n")

        for a in self.problem.actions:
            if isinstance(a, up.model.InstantaneousAction):
                if any(p.simplify().is_false() for p in a.preconditions):
                    continue
                out.write(f" (:action {self._get_mangled_name(a)}")
                out.write(f"\n  :parameters (")
                self._write_parameters(out, a)
                out.write(")")
                self._write_untimed_preconditions(a, converter, out)
                self._write_untimed_effects(a, converter, out, costs)
                out.write(")\n")
            elif isinstance(a, DurativeAction):
                if any(
                    c.simplify().is_false() for cl in a.conditions.values() for c in cl
                ):
                    continue
                out.write(f" (:durative-action {self._get_mangled_name(a)}")
                out.write(f"\n  :parameters (")
                for ap in a.parameters:
                    if ap.type.is_user_type():
                        out.write(
                            f" {self._get_mangled_name(ap)} - {self._get_mangled_name(ap.type)}"
                        )
                    else:
                        raise UPTypeError("PDDL supports only user type parameters")
                out.write(")")
                l, r = a.duration.lower, a.duration.upper
                if l == r:
                    out.write(f"\n  :duration (= ?duration {converter.convert(l)})")
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
                        for c in (cond.simplify() for cond in cl):
                            out.write(f"\n                 ")
                            if c.is_true():
                                continue
                            if interval.lower == interval.upper:
                                if interval.lower.is_from_start():
                                    out.write(f"(at start {converter.convert(c)})")
                                else:
                                    out.write(f"(at end {converter.convert(c)})")
                            else:
                                if not interval.is_left_open():
                                    out.write(f"(at start {converter.convert(c)})")
                                out.write(f"(over all {converter.convert(c)})")
                                if not interval.is_right_open():
                                    out.write(f"(at end {converter.convert(c)})")
                    out.write(f"\n             )")
                elif len(a.conditions) == 0 and self.empty_preconditions:
                    out.write(f"\n  :condition (and )")
                if (len(a.effects) + len(a.continuous_effects)) > 0 or a in costs:
                    out.write(f"\n  :effect (and")
                    if len(a.effects) > 0:
                        for t, el in a.effects.items():
                            for e in el:
                                out.write(f"\n             ")
                                _write_effect(
                                    e,
                                    t,
                                    out,
                                    converter,
                                    self.rewrite_bool_assignments,
                                    self._get_mangled_name,
                                )
                    if a in costs:
                        out.write(f"\n             ")
                        out.write(
                            f" (at end (increase (total-cost) {converter.convert(costs[a])}))"
                        )
                    for interval, el in a.continuous_effects.items():
                        for ce in el:
                            out.write(f"\n")
                            if (
                                interval.lower.is_from_start()
                                and interval.upper.is_from_end()
                            ):
                                _write_effect(
                                    ce,
                                    None,
                                    out,
                                    converter,
                                    self.rewrite_bool_assignments,
                                    self._get_mangled_name,
                                )
                            else:
                                raise UPException(
                                    "PDDL only supports intervals from start to end for continuous effects"
                                )
                    out.write(f"\n          )")
                out.write("\n )\n")

            else:
                raise NotImplementedError
        for proc in self.problem.processes:

            if any(p.simplify().is_false() for p in proc.preconditions):
                continue
            out.write(f" (:process {self._get_mangled_name(proc)}")
            out.write(f"\n  :parameters (")
            self._write_parameters(out, proc)
            out.write(")")
            self._write_untimed_preconditions(proc, converter, out)
            if len(proc.effects) > 0:
                out.write("\n  :effect (and")
                for e in proc.effects:
                    _write_continuous_effects(
                        e,
                        out,
                        converter,
                    )
                out.write(")")
            out.write(")\n")
        for eve in self.problem.events:

            if any(p.simplify().is_false() for p in eve.preconditions):
                continue
            out.write(f" (:event {self._get_mangled_name(eve)}")
            out.write(f"\n  :parameters (")
            self._write_parameters(out, eve)
            out.write(")")
            self._write_untimed_preconditions(eve, converter, out)
            self._write_untimed_effects(eve, converter, out, costs)
            out.write(")\n")
        out.write(")\n")

    def _write_problem(self, out: IO[str]):
        if self.problem.name is None:
            name = "pddl"
        else:
            name = _get_pddl_name(self.problem, self.pddl_keywords)
        out.write(f"(define (problem {name}-problem)\n")
        out.write(f" (:domain {name}-domain)\n")
        if self.domain_objects is None:
            # This method populates the self._domain_objects map
            self._populate_domain_objects(ObjectsExtractor())
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
            out.write("\n )\n")
        converter = ConverterToPDDLString(
            self.problem.environment, self._get_mangled_name
        )
        if isinstance(self.problem, up.model.htn.HierarchicalProblem):
            out.write(" (:htn")
            self._write_task_network(self.problem.task_network, out, converter)
            out.write(")\n")
        out.write(" (:init")
        for f, v in self.problem.initial_values.items():
            if v.is_true():
                out.write(f"\n             ")
                out.write(f" {converter.convert(f)}")
            elif v.is_false():
                pass
            else:
                out.write(f"\n             ")
                out.write(f" (= {converter.convert(f)} {converter.convert(v)})")
        if self.problem.kind.has_actions_cost() or self.problem.kind.has_plan_length():
            out.write(f"\n             ")
            out.write(" (= (total-cost) 0)")
        for tm, le in self.problem.timed_effects.items():
            for e in le:
                out.write(f"\n             ")
                out.write(f" (at {str(converter.convert_fraction(tm.delay))}")
                _write_effect(
                    e,
                    None,
                    out,
                    converter,
                    self.rewrite_bool_assignments,
                    self._get_mangled_name,
                )
                out.write(f")")
        out.write(f"\n )\n")
        goals_str: List[str] = []
        for g in (c.simplify() for c in self.problem.goals):
            if g.is_and():
                goals_str.extend(map(converter.convert, g.args))
            else:
                goals_str.append(converter.convert(g))
        goals_string = "\n           ".join(goals_str)
        out.write(f" (:goal (and \n           {goals_string}\n        )\n )\n")
        if len(self.problem.trajectory_constraints) > 0:
            trajectory_constraints_str = "\n             ".join(
                [converter.convert(c) for c in self.problem.trajectory_constraints]
            )
            out.write(f" (:constraints {trajectory_constraints_str})\n")
        metrics = self.problem.quality_metrics
        if len(metrics) == 1:
            metric = metrics[0]
            out.write(" (:metric ")
            if metric.is_minimize_expression_on_final_state():
                assert isinstance(
                    metric, up.model.metrics.MinimizeExpressionOnFinalState
                )
                out.write(f"minimize {converter.convert(metric.expression)}")
            elif metric.is_maximize_expression_on_final_state():
                assert isinstance(
                    metric, up.model.metrics.MaximizeExpressionOnFinalState
                )
                out.write(f"maximize {converter.convert(metric.expression)}")
            elif (
                metric.is_minimize_action_costs()
                or metric.is_minimize_sequential_plan_length()
            ):
                out.write(f"minimize (total-cost)")
            elif metric.is_minimize_makespan():
                out.write(f"minimize (total-time)")
            else:
                raise NotImplementedError
            out.write(")\n")
        elif len(metrics) > 1:
            raise up.exceptions.UPUnsupportedProblemTypeError(
                "Only one metric is supported!"
            )
        out.write(")\n")

    def _write_plan(self, plan: Plan, out: IO[str]):
        def _format_action_instance(action_instance: ActionInstance) -> str:
            param_str = ""
            if action_instance.actual_parameters:
                param_str = f" {' '.join((self._get_mangled_name(p.object()) for p in action_instance.actual_parameters))}"
            return f"({self._get_mangled_name(action_instance.action)}{param_str})"

        if isinstance(plan, SequentialPlan):
            for ai in plan.actions:
                out.write(f"{_format_action_instance(ai)}\n")
        elif isinstance(plan, TimeTriggeredPlan):
            for s, ai, dur in plan.timed_actions:
                start = s.numerator if s.denominator == 1 else float(s)
                out.write(f"{start}: {_format_action_instance(ai)}")
                if dur is not None:
                    duration = dur.numerator if dur.denominator == 1 else float(dur)
                    out.write(f"[{duration}]")
                out.write("\n")
        else:
            raise NotImplementedError

    def print_domain(self):
        """Prints to std output the `PDDL` domain."""
        self._write_domain(sys.stdout)

    def print_problem(self):
        """Prints to std output the `PDDL` problem."""
        self._write_problem(sys.stdout)

    def print_plan(self, plan: Plan):
        """Prints to std output the `PDDL` plan."""
        self._write_plan(plan, sys.stdout)

    def get_domain(self) -> str:
        """Returns the `PDDL` domain."""
        out = StringIO()
        self._write_domain(out)
        return out.getvalue()

    def get_problem(self) -> str:
        """Returns the `PDDL` problem."""
        out = StringIO()
        self._write_problem(out)
        return out.getvalue()

    def get_plan(self, plan: Plan) -> str:
        """Returns the `PDDL` plan."""
        out = StringIO()
        self._write_plan(plan, out)
        return out.getvalue()

    def write_domain(self, filename: str):
        """Dumps to file the `PDDL` domain."""
        with open(filename, "w") as f:
            self._write_domain(f)

    def write_problem(self, filename: str):
        """Dumps to file the `PDDL` problem."""
        with open(filename, "w") as f:
            self._write_problem(f)

    def write_plan(self, plan: Plan, filename: str):
        """Dumps to file the `PDDL` plan."""
        with open(filename, "w") as f:
            self._write_plan(plan, f)

    def _get_mangled_name(
        self,
        item: WithName,
    ) -> str:
        """This function returns a valid and unique PDDL name."""

        # If we already encountered this item, return it
        if item in self.otn_renamings:
            return self.otn_renamings[item]

        if isinstance(item, up.model.Type):
            assert item.is_user_type()
            original_name = cast(_UserType, item).name
            tmp_name = _get_pddl_name(item, self.pddl_keywords)
            # If the problem is hierarchical and the name is object, we want to change it
            if self.problem_kind.has_hierarchical_typing() and tmp_name == "object":
                tmp_name = f"{tmp_name}_"
        else:
            original_name = item.name
            tmp_name = _get_pddl_name(item, self.pddl_keywords)
        # if the pddl valid name is the same of the original one and it does not create conflicts,
        # it can be returned
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
        self.otn_renamings[item] = new_name
        self.nto_renamings[new_name] = item
        return new_name

    def get_item_named(self, name: str) -> WithName:
        """
        Since `PDDL` has a stricter set of possible naming compared to the `unified_planning`, when writing
        a :class:`~unified_planning.model.Problem` it is possible that some things must be renamed. This is why the `PDDLWriter`
        offers this method, that takes a `PDDL` name and returns the original `unified_planning` data structure that corresponds
        to the `PDDL` entity with the given name.

        This method takes a name used in the `PDDL` domain or `PDDL` problem generated by this `PDDLWriter` and returns the original
        item in the `unified_planning` `Problem`.

        :param name: The name used in the generated `PDDL`.
        :return: The `unified_planning` model entity corresponding to the given name.
        """
        try:
            return self.nto_renamings[name]
        except KeyError:
            raise UPException(f"The name {name} does not correspond to any item.")

    def get_pddl_name(
        self,
        item: WithName,
    ) -> str:
        """
        This method takes an item in the :class:`~unified_planning.model.Problem` and returns the chosen name for the same item in the `PDDL` problem
        or `PDDL` domain generated by this `PDDLWriter`.

        :param item: The `unified_planning` entity renamed by this `PDDLWriter`.
        :return: The `PDDL` name of the given item.
        """
        try:
            return self.otn_renamings[item]
        except KeyError:
            raise UPException(
                f"The item {item} does not correspond to any item renamed."
            )

    def _populate_domain_objects(self, obe: ObjectsExtractor):
        self.domain_objects = {}
        # Iterate the actions to retrieve domain objects
        for a in self.problem.actions:
            if isinstance(a, up.model.InstantaneousAction):
                for p in a.preconditions:
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
                for interval, cl in a.conditions.items():
                    for c in cl:
                        _update_domain_objects(self.domain_objects, obe.get(c))
                for t, el in a.effects.items():
                    for e in el:
                        if e.is_conditional():
                            _update_domain_objects(
                                self.domain_objects, obe.get(e.condition)
                            )
                        _update_domain_objects(self.domain_objects, obe.get(e.fluent))
                        _update_domain_objects(self.domain_objects, obe.get(e.value))
        if isinstance(self.problem, HierarchicalProblem):
            for m in self.problem.methods:
                for p in m.preconditions:
                    _update_domain_objects(self.domain_objects, obe.get(p))
                for subtask in m.subtasks:
                    for targ in subtask.parameters:
                        _update_domain_objects(self.domain_objects, obe.get(targ))
                for c in m.non_temporal_constraints():
                    _update_domain_objects(self.domain_objects, obe.get(c))

    def _write_task_network(
        self,
        tn: up.model.htn.task_network.AbstractTaskNetwork,
        out,
        converter: ConverterToPDDLString,
    ):
        def format_subtask(t: up.model.htn.Subtask):
            return f"({t.identifier} ({self._get_mangled_name(t.task)} {' '.join(map(converter.convert, t.parameters))}))"

        if isinstance(tn, up.model.htn.TaskNetwork) and len(tn.variables) > 0:
            out.write(f"\n  :parameters (")
            for ap in tn.variables:
                if ap.type.is_user_type():
                    out.write(
                        f" {self._get_mangled_name(ap)} - {self._get_mangled_name(ap.type)}"
                    )
                else:
                    raise UPTypeError("PDDL supports only user type parameters")
            out.write(")")

        to = tn.total_order()
        po = tn.partial_order()
        if len(tn.subtasks) == 0:
            pass  # nothing to do
        elif to is not None:  # subtasks form a total order
            ordered_tasks = "\n    ".join(
                format_subtask(tn.get_subtask(id)) for id in to
            )
            out.write(f"\n  :ordered-subtasks (and\n    {ordered_tasks})")
        elif po is not None:  # subtasks for a partial order
            tasks = "\n    ".join(format_subtask(t) for t in tn.subtasks)
            out.write(f"\n  :subtasks (and\n    {tasks})")
            orders = "\n    ".join(f"(< {id1} {id2})" for id1, id2 in po)
            out.write(f"\n  :ordering (and\n    {orders})")
        else:
            raise UPProblemDefinitionError(
                "HDDL does not support general temporal constraints. From:\n" + str(tn)
            )

        if len(tn.non_temporal_constraints()) > 0:
            constraint_str: List[str] = []
            for p in (c.simplify() for c in tn.non_temporal_constraints()):
                if not p.is_true():
                    if p.is_and():
                        constraint_str.extend(map(converter.convert, p.args))
                    else:
                        constraint_str.append(converter.convert(p))
            out.write(f'\n  :constraints (and {" ".join(constraint_str)})')
            raise UPProblemDefinitionError(
                "Task network constraints not supported by HDDL Writer yet"
            )

    def _write_untimed_preconditions(self, item, converter, out):
        if len(item.preconditions) > 0:
            precond_str: list[str] = []
            for p in (c.simplify() for c in item.preconditions):
                if not p.is_true():
                    if p.is_and():
                        precond_str.extend(map(converter.convert, p.args))
                    else:
                        precond_str.append(converter.convert(p))
            out.write(f'\n  :precondition (and {" ".join(precond_str)})')
        elif len(item.preconditions) == 0 and self.empty_preconditions:
            out.write(f"\n  :precondition ()")

    def _write_untimed_effects(self, item, converter, out, costs):
        if len(item.effects) > 0:
            out.write("\n  :effect (and")
            for e in item.effects:
                _write_effect(
                    e,
                    None,
                    out,
                    converter,
                    self.rewrite_bool_assignments,
                    self._get_mangled_name,
                )

            if item in costs:
                out.write(f" (increase (total-cost) {converter.convert(costs[item])})")
            out.write(")")


def _get_pddl_name(
    item: Union[WithName, "up.model.AbstractProblem"], pddl_keywords: Set[str]
) -> str:
    """This function returns a pddl name for the chosen item"""
    name = item.name  # type: ignore
    assert name is not None
    name = name.lower()
    regex = re.compile(r"^[a-zA-Z]+.*")
    if (
        re.match(regex, name) is None
    ):  # If the name does not start with an alphabetic char, we make it start with one.
        name = f'{INITIAL_LETTER.get(type(item), "x")}_{name}'

    name = re.sub("[^0-9a-zA-Z_-]", "_", name)  # Substitute non-valid elements with "_"
    while (
        name in pddl_keywords
    ):  # If the name is in the keywords, apply an underscore at the end until it is not a keyword anymore.
        name = f"{name}_"
    if isinstance(item, up.model.Parameter) or isinstance(item, up.model.Variable):
        name = f"?{name}"
    return name


def _update_domain_objects(
    dict_to_update: Dict[_UserType, Set[Object]], values: Dict[_UserType, Set[Object]]
) -> None:
    """Small utility method that updated a UserType -> Set[Object] dict with another dict of the same type."""
    for ut, os in values.items():
        os_to_update = dict_to_update.setdefault(ut, set())
        os_to_update |= os


def _write_effect(
    effect: Effect,
    timing: Optional[Timing],
    out: IO[str],
    converter: ConverterToPDDLString,
    rewrite_bool_assignments: bool,
    get_mangled_name: MangleFunction,
):
    simplified_cond = effect.condition.simplify()
    # check for non-constant-bool-assignment
    non_const_bool_ass = (
        effect.value.type.is_bool_type()
        and not effect.value.is_true()
        and not effect.value.is_false()
    )
    if non_const_bool_ass and not rewrite_bool_assignments:
        raise UPProblemDefinitionError(
            "The problem has non-constant boolean assignments.This can't be directly written ",
            "in PDDL, but it can be translated into a conditional effect maintaining the ",
            "semantic. To enable this feature, set the flag rewrite_bool_assignments",
            " to True in the PDDLWriter constructor.",
        )
    forall_str = ""
    if effect.is_forall():
        mid_str = " ".join(
            (
                f"{get_mangled_name(v)} - {get_mangled_name(v.type)}"
                for v in effect.forall
            )
        )
        forall_str = f"(forall ({mid_str})"
    simplified_cond = effect.condition.simplify()
    if non_const_bool_ass:
        assert effect.is_assignment()
        positive_cond = (simplified_cond & effect.value).simplify()
        if not positive_cond.is_false():
            out.write(forall_str)
            if not positive_cond.is_true():
                out.write(" (when ")
                if timing is not None:
                    if timing.is_from_start():
                        out.write(f" (at start")
                    else:
                        out.write(f" (at end")
                elif effect.is_continuous_increase() or effect.is_continuous_decrease():
                    out.write(f" (at start")
                out.write(f"{converter.convert(positive_cond)}")
                if timing is not None:
                    out.write(")")
                out.write(f" {converter.convert(effect.fluent)})")
            if timing is not None:
                if timing.is_from_start():
                    out.write(f" (at start")
                else:
                    out.write(f" (at end")
            if positive_cond.is_true():
                out.write(f" {converter.convert(effect.fluent)}")
            if timing is not None:
                out.write(")")
            if effect.is_forall():
                out.write(")")
        negative_cond = (simplified_cond & effect.value.Not()).simplify()
        if not negative_cond.is_false():
            out.write(forall_str)
            if not negative_cond.is_true():
                out.write(" (when")
                if timing is not None:
                    if timing.is_from_start():
                        out.write(f" (at start")
                    else:
                        out.write(f" (at end")
                elif effect.is_continuous_increase() or effect.is_continuous_decrease():
                    out.write(f" (at start")
                out.write(f" {converter.convert(negative_cond)}")
                if timing is not None:
                    out.write(")")
                out.write(f" (not {converter.convert(effect.fluent)}))")
            if timing is not None:
                if timing.is_from_start():
                    out.write(f" (at start")
                else:
                    out.write(f" (at end")
            if negative_cond.is_true():
                out.write(f" {converter.convert(effect.fluent)}")
            if timing is not None:
                out.write(")")
            if effect.is_forall():
                out.write(")")
        return

    if simplified_cond.is_false():
        return
    out.write(forall_str)
    if not simplified_cond.is_true():
        out.write(f" (when")
        if timing is not None:
            if timing.is_from_start():
                out.write(f" (at start")
            else:
                out.write(f" (at end")
        elif effect.is_continuous_increase() or effect.is_continuous_decrease():
            out.write(f" (at start")
        out.write(f" {converter.convert(effect.condition)}")
        if timing is not None:
            out.write(")")
    if timing is not None:
        if timing.is_from_start():
            out.write(f" (at start")
        else:
            out.write(f" (at end")
    simplified_value = effect.value.simplify()
    fluent = converter.convert(effect.fluent)
    if simplified_value.is_true():
        out.write(f" {fluent}")
    elif simplified_value.is_false():
        out.write(f" (not {fluent})")
    elif effect.is_increase():
        out.write(f" (increase {fluent} {converter.convert(simplified_value)})")
    elif effect.is_decrease():
        out.write(f" (decrease {fluent} {converter.convert(simplified_value)})")
    elif effect.is_continuous_increase():
        out.write(f" (increase {fluent} (* #t {converter.convert(simplified_value)}))")
    elif effect.is_continuous_decrease():
        out.write(f" (decrease {fluent} (* #t {converter.convert(simplified_value)}))")
    else:
        out.write(f" (assign {fluent} {converter.convert(simplified_value)})")
    if not simplified_cond.is_true():
        out.write(")")
    if timing is not None:
        out.write(")")
    if effect.is_forall():
        out.write(")")


def _write_continuous_effects(
    effect: Effect,
    out: IO[str],
    converter: ConverterToPDDLString,
):
    # check for non-constant-bool-assignment
    simplified_value = effect.value.simplify()
    fluent = converter.convert(effect.fluent)
    if effect.is_continuous_increase():
        out.write(f" (increase {fluent} (* #t {converter.convert(simplified_value)} ))")
    elif effect.is_continuous_decrease():
        out.write(f" (decrease {fluent} (* #t {converter.convert(simplified_value)} ))")
    else:
        raise UPProblemDefinitionError(
            "Processes can only contains continuous effects in PDDL",
        )
