# Copyright 2021-2023 AIPlan4EU project
# Copyright 2024-2026 Unified Planning library and its maintainers
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
from collections import OrderedDict
from typing import Dict, Iterable, List, Optional, FrozenSet, Set, Tuple, Union, cast
import unified_planning as up
import unified_planning.environment
from unified_planning.exceptions import UPUnreachableCodeError
import unified_planning.model.walkers as walkers
from unified_planning.model.fnode import FNode
from unified_planning.model.types import _UserType
import unified_planning.model.operators as op


# One argument-position pattern of a recorded effect target, as classified by
# `_EffectTargetIndex._arg_spec`: `("const", fnode)` matches only that one constant argument,
# `("type", type)` matches any argument whose type is compatible with `type` (an action parameter
# or a forall-bound variable's type), and `("wild", None)` matches anything (a nested expression
# or object-fluent call the index can't otherwise classify).
_ArgSpec = Tuple[str, object]


class _EffectTargetIndex:
    """Over-approximates, for one :class:`~unified_planning.model.Problem`, which ground atoms of
    which fluents its actions/events/processes/timed-effects can ever write.

    :func:`~unified_planning.model.Problem.get_static_fluents` only answers at *schema*
    granularity: a fluent is static only if `no` grounding of it is ever written. That misses the
    common case of a fluent whose schema is written for some argument tuples but never others --
    e.g. a `pos(?o: Object)` fluent that is only ever assigned through an action parameter typed
    `Boat`, so `pos(some_fixed_waypoint)` never changes even though `pos` itself is not static.
    `may_write` answers that per-atom question instead, by recording one *pattern* per effect
    target (one spec per argument position, see `_ArgSpec`) and checking a candidate ground atom
    against every recorded pattern of the same fluent.

    Argument positions are checked independently of each other, so a correlation between two
    parameters of the same effect (e.g. an effect that only ever fires when two of an action's
    parameters happen to be equal) is invisible to this index -- which only ever makes `may_write`
    return `True` more often than strictly necessary, the safe direction: every atom that really
    is written is matched by its own pattern, so it is never mistakenly folded to a constant.

    Every recorded pattern is tagged with an `owner` -- the `Action`/`Event`/`Process` (or, for a
    timed effect, the `Effect` itself) it was scanned from -- so `forget`/`learn` can incrementally
    un-record/re-record exactly one owner's contribution in `O(that owner's own effect count)`,
    instead of rebuilding the whole index from a fresh scan of the `Problem` in `O(problem size)`.
    A `Grounder` refining an already-grounded problem to a fixed point (see
    `unified_planning.engines.compilers.grounder._refine_actions_to_fixed_point`) uses this to
    keep one index up to date across many action replacements/drops, at the cost of exactly the
    actions that actually change -- events/processes/timed-effects are never touched by that loop,
    so their entries never need `forget`/`learn` (any hashable owner key works for them; they're
    only ever consulted, never removed).

    Important NOTE: same contract as `Simplifier` itself -- the `Problem` given at construction
    time must not be modified directly (bypassing `forget`/`learn`) afterwards, or this index's
    answers (and its cache) become stale.
    """

    def __init__(self, problem: "up.model.problem.Problem"):
        self._patterns: Dict[
            "up.model.fluent.Fluent", Dict[object, List[Tuple[_ArgSpec, ...]]]
        ] = {}
        self._owners_fluents: Dict[object, Set["up.model.fluent.Fluent"]] = {}
        self._may_write_cache: Dict[FNode, bool] = {}
        for a in problem.actions:
            self._scan_action(a)
        for ev in problem.events:
            self._scan_effects(ev, ev.effects)
            self._scan_simulated_effects(ev, ev.simulated_effect)
        for pro in problem.processes:
            self._scan_effects(pro, pro.effects)
        for effs in problem.timed_effects.values():
            for e in effs:
                # No natural per-timed-effect "owner" object exists (unlike an Action/Event/
                # Process) -- the Effect itself is a fine, unique, hashable key: the grounder
                # never calls forget/learn on it (timed effects aren't touched by action
                # refinement), so nothing depends on it being anything more than stable.
                self._record_target(e, e.fluent)

    def _scan_action(self, a: "up.model.action.Action"):
        if isinstance(a, up.model.action.InstantaneousAction):
            self._scan_effects(a, a.effects)
            self._scan_simulated_effects(a, a.simulated_effect)
        elif isinstance(a, up.model.action.DurativeAction):
            for effs in a.effects.values():
                self._scan_effects(a, effs)
            for effs in a.continuous_effects.values():
                self._scan_effects(a, effs)
            for se in a.simulated_effects.values():
                self._scan_simulated_effects(a, se)
        else:
            raise NotImplementedError(
                f"_EffectTargetIndex does not know how to scan the effects of {type(a)}"
            )

    def _scan_effects(self, owner: object, effects: Iterable["up.model.effect.Effect"]):
        for e in effects:
            self._record_target(owner, e.fluent)

    def _scan_simulated_effects(
        self, owner: object, se: Optional["up.model.effect.SimulatedEffect"]
    ):
        if se is None:
            return
        # SimulatedEffect.fluents entries are, by construction, plain fluent expressions whose
        # arguments are constants or action-parameter expressions only (never a nested
        # expression, a Dot, or a forall-bound variable -- a simulated effect can't be
        # forall-quantified), so they fit the same per-position classification as a regular
        # effect target and need no separate handling.
        for f in se.fluents:
            self._record_target(owner, f)

    def _record_target(self, owner: object, target: FNode) -> "up.model.fluent.Fluent":
        if target.is_dot():
            # Multi-agent effect target: unwrap the `Dot` to the underlying fluent expression --
            # see UntimedEffectMixin.add_effect, which accepts `fluent_exp.is_dot()`.
            target = target.arg(0)
        fluent = target.fluent()
        pattern = tuple(self._arg_spec(arg) for arg in target.args)
        self._patterns.setdefault(fluent, {}).setdefault(owner, []).append(pattern)
        self._owners_fluents.setdefault(owner, set()).add(fluent)
        return fluent

    @staticmethod
    def _arg_spec(arg: FNode) -> _ArgSpec:
        if arg.is_constant():
            return ("const", arg)
        if arg.is_parameter_exp():
            return ("type", arg.parameter().type)
        if arg.is_variable_exp():
            return ("type", arg.variable().type)
        return ("wild", None)

    def may_write(self, fluent_exp: FNode) -> bool:
        """`True` if some recorded effect target might, for some grounding, write exactly
        `fluent_exp` -- `fluent_exp` must have only constant arguments."""
        cached = self._may_write_cache.get(fluent_exp)
        if cached is not None:
            return cached
        owners_patterns = self._patterns.get(fluent_exp.fluent())
        result = False
        if owners_patterns:
            args = fluent_exp.args
            for patterns in owners_patterns.values():
                if result:
                    break
                for pattern in patterns:
                    if all(
                        self._arg_matches(spec, arg) for spec, arg in zip(pattern, args)
                    ):
                        result = True
                        break
        self._may_write_cache[fluent_exp] = result
        return result

    @staticmethod
    def _arg_matches(spec: _ArgSpec, arg: FNode) -> bool:
        kind, payload = spec
        if kind == "wild":
            return True
        if kind == "const":
            return arg == payload
        assert kind == "type"
        return cast("up.model.types.Type", payload).is_compatible(arg.type)

    def write_count(self, fluent: "up.model.fluent.Fluent") -> int:
        """The number of distinct owners currently recorded as (possibly) writing `fluent` -- `0`
        means `fluent` is schema-static given everything this index has recorded so far."""
        return len(self._patterns.get(fluent, {}))

    def forget(self, owner: object) -> Set["up.model.fluent.Fluent"]:
        """Un-records every pattern `owner` contributed (e.g. because the action it came from was
        dropped, or is about to be replaced by a refolded version with different effects).

        :return: The fluents `owner` touched -- whether or not their pattern set became empty as a
            result. A *narrower* surviving pattern set (another owner still writes the fluent, so
            `write_count` didn't reach zero) can still newly unlock folding of one specific ground
            atom of that fluent (`may_write`), so callers must not assume only a `write_count` drop
            to zero matters.
        """
        fluents = self._owners_fluents.pop(owner, None)
        if not fluents:
            return set()
        for f in fluents:
            owners = self._patterns.get(f)
            if owners is not None:
                owners.pop(owner, None)
                if not owners:
                    del self._patterns[f]
        self._may_write_cache.clear()
        return fluents

    def learn(
        self, owner: object, targets: Iterable[FNode]
    ) -> Set["up.model.fluent.Fluent"]:
        """Records `owner`'s current effect targets. Intended to be called right after `forget`,
        with whichever (possibly narrower, possibly empty) set of effects `owner` currently has --
        calling it without a preceding `forget` would duplicate `owner`'s previously-recorded
        patterns rather than replace them.

        :return: The fluents touched by `targets`.
        """
        touched = {self._record_target(owner, target) for target in targets}
        if touched:
            self._may_write_cache.clear()
        return touched


class Simplifier(walkers.dag.DagWalker):
    """Performs basic simplifications of the input expression.

    Important NOTE:
    After the initialization, the :class:`~unified_planning.model.Problem` given as input can not be modified
    or the `Simplifier` behavior is undefined."""

    def __init__(
        self,
        environment: "unified_planning.environment.Environment",
        problem: Optional["unified_planning.model.problem.Problem"] = None,
        fold_static_fluent_exps: bool = False,
        effect_target_index: Optional[_EffectTargetIndex] = None,
    ):
        """
        :param environment: The `Environment` this `Simplifier` operates in.
        :param problem: If given, static fluents (`problem.get_static_fluents()`, or
            `effect_target_index`'s own view of staticness when that is given -- see below) are
            folded to their initial value.
        :param fold_static_fluent_exps: If `True`, also fold a ground fluent atom that is not
            static at the *schema* level (`problem.get_static_fluents()` doesn't include its
            fluent, because some other grounding of it IS written somewhere) but that this exact
            atom is nonetheless never the target of any effect in `problem` -- see
            `_EffectTargetIndex`. Requires `problem` to be a plain
            :class:`~unified_planning.model.Problem` (or a subclass that adds no extra effect
            source, e.g. `HierarchicalProblem`/`ContingentProblem`); ignored (folding stays off)
            for a `problem` of any other type, such as `SchedulingProblem`/`MultiAgentProblem`,
            which don't expose the effect surface `_EffectTargetIndex` scans. Defaults to `False`
            so existing callers (and `problem.kind`, which is computed through its own
            `Simplifier`) are unaffected.
        :param effect_target_index: An already-built `_EffectTargetIndex` to use instead of
            scanning `problem` again -- for a caller that already maintains one incrementally
            (see `unified_planning.engines.compilers.grounder._refine_actions_to_fixed_point`,
            which builds many cheap, short-lived `Simplifier`s around one long-lived index rather
            than re-scanning the whole problem on every one of them). When given, `static_fluents`
            is *derived from the index* (`write_count(f) == 0`) instead of a separate
            `problem.get_static_fluents()` call -- regardless of `fold_static_fluent_exps`, which
            only controls whether the index is *also* consulted for per-atom folding
            (`self._effect_target_index`, below). Requires `problem` to be given too (for
            `problem.fluents` and `problem.initial_value`).
        """
        walkers.dag.DagWalker.__init__(self)
        self.environment = environment
        self.manager = environment.expression_manager
        self.problem: Optional["unified_planning.model.problem.Problem"] = problem
        if effect_target_index is not None:
            assert problem is not None, (
                "effect_target_index requires problem to be given too"
            )
            self.static_fluents = {
                f for f in problem.fluents if effect_target_index.write_count(f) == 0
            }
            self._effect_target_index: Optional[_EffectTargetIndex] = (
                effect_target_index if fold_static_fluent_exps else None
            )
            return
        if problem is not None:
            self.static_fluents = problem.get_static_fluents()
        else:
            self.static_fluents = set()
        self._effect_target_index = None
        if fold_static_fluent_exps and isinstance(problem, up.model.problem.Problem):
            self._effect_target_index = _EffectTargetIndex(problem)

    def _number_to_fnode(self, value: Union[int, float, Fraction]) -> FNode:
        if isinstance(value, int):
            fnode = self.manager.Int(value)
        else:
            fnode = self.manager.Real(Fraction(value))
        return fnode

    def simplify(self, expression: FNode) -> FNode:
        """Performs basic simplification of the given expression.

        If a :class:`~unified_planning.model.Problem` is given at the constructor, it also uses the static `fluents` of the `Problem` for
        a better simplification.

        :param expression: The target expression that must be simplified with constant propagation.
        :return: The simplified expression.
        """
        return self.walk(expression)

    def walk_and(self, expression: FNode, args: List[FNode]) -> FNode:
        if len(args) == 2 and args[0] == args[1]:
            return args[0]

        new_args: OrderedDict[FNode, bool] = OrderedDict()
        for a in args:
            if a.is_true():
                continue
            if a.is_false():
                return self.manager.FALSE()
            if a.is_and():
                for s in a.args:
                    if self.walk_not(self.manager.Not(s), [s]) in new_args:
                        return self.manager.FALSE()
                    new_args[s] = True
            else:
                if self.walk_not(self.manager.Not(a), [a]) in new_args:
                    return self.manager.FALSE()
                new_args[a] = True

        if len(new_args) == 0:
            return self.manager.TRUE()
        elif len(new_args) == 1:
            return next(iter(new_args))
        else:
            return self.manager.And(new_args.keys())

    def walk_or(self, expression: FNode, args: List[FNode]) -> FNode:
        if len(args) == 2 and args[0] == args[1]:
            return args[0]

        new_args: OrderedDict[FNode, bool] = OrderedDict()
        for a in args:
            if a.is_false():
                continue
            if a.is_true():
                return self.manager.TRUE()
            if a.is_or():
                for s in a.args:
                    if self.walk_not(self.manager.Not(s), [s]) in new_args:
                        return self.manager.TRUE()
                    new_args[s] = True
            else:
                if self.walk_not(self.manager.Not(a), [a]) in new_args:
                    return self.manager.TRUE()
                new_args[a] = True

        if len(new_args) == 0:
            return self.manager.FALSE()
        elif len(new_args) == 1:
            return next(iter(new_args))
        else:
            return self.manager.Or(new_args.keys())

    def walk_not(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        child = args[0]
        if child.is_bool_constant():
            l = child.bool_constant_value()
            return self.manager.Bool(not l)
        elif child.is_not():
            return child.arg(0)

        return self.manager.Not(child)

    def walk_iff(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2

        sl = args[0]
        sr = args[1]

        if sl.is_bool_constant() and sr.is_bool_constant():
            l = sl.bool_constant_value()
            r = sr.bool_constant_value()
            return self.manager.Bool(l == r)
        elif sl.is_bool_constant():
            if sl.bool_constant_value():
                return sr
            else:
                return self.manager.Not(sr)
        elif sr.is_bool_constant():
            if sr.bool_constant_value():
                return sl
            else:
                return self.manager.Not(sl)
        elif sl == sr:
            return self.manager.TRUE()
        else:
            return self.manager.Iff(sl, sr)

    def walk_implies(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2

        sl = args[0]
        sr = args[1]

        if sl.is_bool_constant():
            l = sl.bool_constant_value()
            if l:
                return sr
            else:
                return self.manager.TRUE()
        elif sr.is_bool_constant():
            r = sr.bool_constant_value()
            if r:
                return self.manager.TRUE()
            else:
                return self.manager.Not(sl)
        elif sl == sr:
            return self.manager.TRUE()
        else:
            return self.manager.Implies(sl, sr)

    def walk_exists(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        free_vars: FrozenSet["up.model.variable.Variable"] = (
            self.environment.free_vars_oracle.get_free_variables(args[0])
        )
        vars = set(var for var in expression.variables() if var in free_vars)
        # Here we check if the arg is in the form:
        # phi(l_i) and l_i == x with phi and x general formulae and l_i a variable
        # bounded to this Exists.
        # if it is, it can be simplified with phi(x) and l_i is removed from the free variables.
        # this process is repeated until there are no more equalities with variables bounded to this
        # Exists
        new_arg, check_equality_simplification = args[0], True
        while check_equality_simplification:
            check_equality_simplification = False
            if new_arg.is_and():
                for i, and_arg in enumerate(new_arg.args):
                    if and_arg.is_equals():
                        variable, value = and_arg.args
                        if (
                            not variable.is_variable_exp()
                            or variable.variable() not in vars
                        ):
                            variable, value = value, variable
                        value_free_vars = (
                            self.environment.free_vars_oracle.get_free_variables(
                                args[0]
                            )
                        )
                        if (
                            variable.is_variable_exp()
                            and variable.variable() in vars
                            and variable not in value_free_vars
                        ):
                            check_equality_simplification = True
                            new_arg = self.manager.And(
                                *(a for j, a in enumerate(new_arg.args) if i != j)
                            )
                            new_arg = new_arg.substitute({variable: value})
                            vars.remove(variable.variable())
                            break
        if vars:
            return self.manager.Exists(new_arg, *vars)
        else:
            return new_arg

    def walk_forall(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        free_vars: FrozenSet["up.model.variable.Variable"] = (
            self.environment.free_vars_oracle.get_free_variables(args[0])
        )
        vars = tuple(var for var in expression.variables() if var in free_vars)
        if len(vars) == 0:
            return args[0]
        return self.manager.Forall(args[0], *vars)

    def walk_always(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        if args[0].is_true():
            return self.manager.TRUE()
        if args[0].is_false():
            return self.manager.FALSE()
        return self.manager.Always(args[0])

    def walk_at_most_once(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        if args[0].is_true() or args[0].is_false():
            return self.manager.TRUE()
        return self.manager.AtMostOnce(args[0])

    def walk_sometime(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        if args[0].is_true():
            return self.manager.TRUE()
        if args[0].is_false():
            return self.manager.FALSE()
        return self.manager.Sometime(args[0])

    def walk_sometime_before(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2
        if args[0].is_false():
            return self.manager.TRUE()
        if args[0].is_true():
            return self.manager.FALSE()
        return self.manager.SometimeBefore(args[0], args[1])

    def walk_sometime_after(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2
        if args[0].is_false():
            return self.manager.TRUE()
        if args[0].is_true():
            if args[1].is_true():
                return self.manager.TRUE()
            if args[1].is_false():
                return self.manager.FALSE()
        return self.manager.SometimeAfter(args[0], args[1])

    def walk_equals(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2

        sl = args[0]
        sr = args[1]

        if sl.is_constant() and sr.is_constant():
            l = sl.constant_value()
            r = sr.constant_value()
            return self.manager.Bool(l == r)
        elif sl == sr:
            return self.manager.TRUE()
        elif sl.type.is_user_type() and sr.type.is_user_type():
            slt, srt = cast(_UserType, sl.type), cast(_UserType, sr.type)
            if not slt.is_compatible(srt) and not srt.is_compatible(slt):
                return self.manager.FALSE()
        return self.manager.Equals(sl, sr)

    def walk_le(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2

        sl = args[0]
        sr = args[1]

        if sl.is_constant() and sr.is_constant():
            l = sl.constant_value()
            r = sr.constant_value()
            return self.manager.Bool(l <= r)
        return self.manager.LE(sl, sr)

    def walk_lt(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2

        sl = args[0]
        sr = args[1]

        if sl.is_constant() and sr.is_constant():
            l = sl.constant_value()
            r = sr.constant_value()
            return self.manager.Bool(l < r)
        return self.manager.LT(sl, sr)

    def walk_fluent_exp(self, expression: FNode, args: List[FNode]) -> FNode:
        new_exp = self.manager.FluentExp(expression.fluent(), tuple(args))
        fluent_is_static = expression.fluent() in self.static_fluents
        if not fluent_is_static and self._effect_target_index is None:
            # No schema-level staticness and per-atom folding isn't enabled
            return new_exp
        for a in args:
            if not a.is_constant():
                return new_exp
        if not fluent_is_static:
            # Not static at the schema level (some grounding of this fluent IS written
            # somewhere), but this specific ground atom is never among the effect targets the
            # index recorded -- fold it exactly like a schema-static one, below.
            assert self._effect_target_index is not None
            if self._effect_target_index.may_write(new_exp):
                return new_exp
        assert self.problem is not None
        static_value = self.problem.initial_value(new_exp)
        if static_value is not None:
            return static_value
        else:  # value is static but is not defined in the initial state
            return new_exp

    def walk_interpreted_function_exp(
        self, expression: FNode, args: List[FNode]
    ) -> FNode:
        new_exp = self.manager.InterpretedFunctionExp(
            expression.interpreted_function(), tuple(args)
        )
        newlist = []
        for a in args:
            if not a.is_constant():
                return new_exp
            else:
                v = a.constant_value()
                newlist.append(v)
        constantval = expression.interpreted_function().function(*newlist)
        if expression.interpreted_function().return_type.is_bool_type():
            constantval = self.manager.Bool(constantval)
        elif expression.interpreted_function().return_type.is_int_type():
            constantval = self.manager.Int(constantval)
        elif expression.interpreted_function().return_type.is_real_type():
            constantval = self.manager.Real(Fraction(constantval))
        elif expression.interpreted_function().return_type.is_user_type():
            constantval = self.manager.ObjectExp(constantval)
        else:
            raise UPUnreachableCodeError
        return constantval

    def walk_dot(self, expression: FNode, args: List[FNode]) -> FNode:
        return self.manager.Dot(expression.agent(), args[0])

    def walk_plus(self, expression: FNode, args: List[FNode]) -> FNode:
        new_args_plus: List[FNode] = list()
        accumulator: Union[int, Fraction] = 0
        # divide constant FNode and accumulate their value into accumulator
        for a in args:
            if a.is_int_constant() or a.is_real_constant():
                accumulator += a.constant_value()
            elif a.is_plus():
                for s in a.args:
                    if s.is_int_constant() or s.is_real_constant():
                        accumulator += s.constant_value()
                    else:
                        new_args_plus.append(s)
            else:
                new_args_plus.append(a)
        # if accumulator != 0 create it as a constant FNode and then add all the non-constant FNodes found
        # else return 0 or all the non-constant FNodes found
        if accumulator != 0:
            fnode_acc = self.manager.Plus(
                *new_args_plus, self._number_to_fnode(accumulator)
            )
            return fnode_acc
        else:
            if len(new_args_plus) == 0:
                return self.manager.Int(0)
            else:
                return self.manager.Plus(new_args_plus)

    def walk_minus(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2
        left, right = args
        value: Union[Fraction, int] = 0
        if (left.is_int_constant() or left.is_real_constant()) and (
            right.is_int_constant() or right.is_real_constant()
        ):
            value = left.constant_value() - right.constant_value()
            fnode_constant_values = self._number_to_fnode(value)
            return fnode_constant_values
        elif right.is_int_constant() or right.is_real_constant():
            if right.constant_value() < 0:
                value = -right.constant_value()
                fnode_constant_values = self._number_to_fnode(value)
                return self.manager.Plus(left, fnode_constant_values)
            else:
                return self.manager.Minus(left, right)
        else:
            return self.manager.Minus(left, right)

    def walk_times(self, expression: FNode, args: List[FNode]) -> FNode:
        new_args_times: List[FNode] = list()
        accumulator: Union[int, Fraction] = 1
        # divide constant FNode and accumulate their value into accumulator
        for a in args:
            if a.is_int_constant() or a.is_real_constant():
                if a.constant_value() == 0:
                    return self.manager.Int(0)
                else:
                    accumulator *= a.constant_value()
            elif a.is_times():
                for s in a.args:
                    if s.is_int_constant() or s.is_real_constant():
                        if s.constant_value() == 0:
                            return self.manager.Int(0)
                        else:
                            accumulator *= s.constant_value()
                    else:
                        new_args_times.append(s)
            else:
                new_args_times.append(a)
        # if accumulator != 1 create it as a constant FNode and then add all the non-constant FNodes found
        # else return  or all the non-constant FNodes found
        if accumulator != 1:
            fnode_acc = self._number_to_fnode(accumulator)
            return self.manager.Times(*new_args_times, fnode_acc)
        else:
            if len(new_args_times) == 0:
                return self.manager.Int(1)
            else:
                return self.manager.Times(new_args_times)

    def walk_div(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2
        left, right = args
        value: Union[Fraction, int, float] = 0
        if left.is_int_constant() and right.is_int_constant():
            if (left.constant_value() % right.constant_value()) == 0:
                value = int(left.constant_value() / right.constant_value())
            else:
                value = Fraction(left.constant_value(), right.constant_value())
        elif (left.is_int_constant() or left.is_real_constant()) and (
            right.is_int_constant() or right.is_real_constant()
        ):
            assert right.constant_value() != 0
            value = Fraction(left.constant_value(), right.constant_value())
        else:
            return self.manager.Div(left, right)
        return self._number_to_fnode(value)

    @walkers.handles(op.CONSTANTS)
    @walkers.handles(
        op.OperatorKind.PARAM_EXP,
        op.OperatorKind.VARIABLE_EXP,
        op.OperatorKind.OBJECT_EXP,
        op.OperatorKind.TIMING_EXP,
        op.OperatorKind.PRESENT_EXP,
    )
    def walk_identity(self, expression: FNode, args: List[FNode]) -> FNode:
        return expression
