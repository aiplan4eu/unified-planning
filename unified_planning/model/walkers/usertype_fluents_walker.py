# Copyright 2021 AIPlan4EU project
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


from typing import Dict, Iterable, List, Optional, Set, Tuple, cast
import unified_planning as up
import unified_planning.environment
import unified_planning.model.walkers as walkers
import unified_planning.model.operators as op
from unified_planning.model.fnode import FNode
from unified_planning.model.fluent import Fluent
from unified_planning.model.types import _UserType


class UsertypeFluentsWalker(walkers.dag.DagWalker):
    """
    This walker takes the mapping from the usertype fluents to be removed from
    the expression to the substituting Fluent; the set of the names already
    defined in the Problem (to avoid naming conflicts) and the environment
    and offers the capability to take an FNode with userType fluents and return
    the equivalent expression without userType fluents.
    """

    def __init__(
        self,
        new_fluents: Dict[Fluent, Fluent],
        defined_names: Iterable[str],
        env: "unified_planning.environment.Environment",
    ):
        walkers.dag.DagWalker.__init__(self)
        self._new_fluents = new_fluents
        self.env = env
        self.manager = env.expression_manager
        self._defined_names: Set[str] = set(defined_names)

    def remove_usertype_fluents(
        self,
        expression: FNode,
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        """
        Removes UserType Fluents from the given expression and returns the generated
        expression, the top-level Variable (if any, None otherwise), the set of Variables
        that are still free in the returned expression, the top-level Variable (if any,
        None otherwise) and the set of FluentExp that must be True in order for the given
        expression to be equivalent to the returned one.

        :param expression: The target expression in which usertype fluents must be removed.
        :return: The expression without userType fluents, the top level added variable, the free variables in the
            expression, the top level fluent and all the FluentExp that must be True for the 2 expressions to be
            equivalent.
        """
        exp, last_var, free_vars, last_fluent, added_fluents = self.walk(expression)
        if last_var is not None:
            assert last_fluent is not None
            assert expression.is_fluent_exp()
            assert expression.type.is_user_type()
            assert expression.fluent() in self._new_fluents
        else:
            assert last_fluent is None
        return (exp, last_var, free_vars.copy(), last_fluent, added_fluents.copy())

    def remove_usertype_fluents_from_condition(self, expression: FNode) -> FNode:
        """
        Removes the UsertypeFluents from an Expression and returns the equivalent condition.
        The Fluents of type UserType are given at construction time in the new_fluents map.

        :param expression: The FNode that must be returned without UsertypeFluents.
        :return: The equivalent expression without Usertype Fluents.
        """
        new_exp, last_var, free_vars, last_fluent, added_fluents = self.walk(expression)
        assert (
            last_var is None and last_fluent is None
        ), "A boolean condition can't have last_var or last_fluent"
        if free_vars:
            assert added_fluents
            new_exp = self.manager.Exists(
                self.manager.And(new_exp, *added_fluents), *free_vars
            )
        else:
            assert not added_fluents
        return new_exp.simplify()

    def _get_fresh_name(self, basename: str) -> str:
        name, counter = basename, 0
        while name in self._defined_names:
            name = f"{basename}_{counter}"
            counter += 1
        self._defined_names.add(name)
        return name

    def _process_exp_args(
        self,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[List[FNode], Set["up.model.variable.Variable"], Set[FNode]]:
        """
        This method takes the args given as parameters to a walker method (walk_and
        for example) and returns the resulting expressions, the set of free Variables
        and the set of FluentExp that are instantiated over the free Variables.

        If the arg type is boolean and there are free variables, those are bounded
        to the boolean expression using an And with their instantiated FluentExp and
        returning the And created under an Existential.

        :param args: The args given as parameters to a walker method.
        :return: The computed expressions, the Variables that are still free in the
            computed expressions and the FluentExp that use the free Variables
        """
        exp_args = []
        variables: Set["up.model.variable.Variable"] = set()
        fluents: Set[FNode] = set()
        for arg, last_var, free_vars, last_fluent, ut_fluents in args:
            arg_type = arg.type
            if free_vars and arg_type.is_bool_type():
                assert ut_fluents and last_var is None and last_fluent is None
                exp_args.append(
                    self.manager.Exists(self.manager.And(arg, *ut_fluents), *free_vars)
                )
            else:
                if last_var is not None:
                    variables.add(last_var)
                variables.update(free_vars)
                if last_fluent is not None:
                    fluents.add(last_fluent)
                fluents.update(ut_fluents)
                exp_args.append(arg)
        return (exp_args, variables, fluents)

    def walk_and(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.And(*exp_args), None, set(), None, set())

    def walk_or(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.Or(*exp_args), None, set(), None, set())

    def walk_not(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 1
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.Not(*exp_args), None, set(), None, set())

    def walk_iff(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 2
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.Iff(*exp_args), None, set(), None, set())

    def walk_implies(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 2
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.Implies(*exp_args), None, set(), None, set())

    def walk_exists(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 1
        exp_args, _, _ = self._process_exp_args(args)
        added_vars = args[0][2]
        assert args[0][1] is None
        assert not any(
            v in added_vars for v in expression.variables()
        ), "Conflicting Variables naming"
        return (
            self.manager.Exists(exp_args[0], *expression.variables()),
            None,
            set(),
            None,
            set(),
        )

    def walk_forall(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 1
        exp_args, _, _ = self._process_exp_args(args)
        added_vars = args[0][2]
        assert args[0][1] is None
        assert not any(
            v in added_vars for v in expression.variables()
        ), "Conflicting Variables naming"
        return (
            self.manager.Forall(exp_args[0], *expression.variables()),
            None,
            set(),
            None,
            set(),
        )

    def walk_equals(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 2

        l_exp, l_var, l_vars, l_fluent, l_fluents = args[0]
        r_exp, r_var, r_vars, r_fluent, r_fluents = args[1]

        if l_var is not None:
            assert l_fluent is not None
            l_vars = {l_var}
            l_vars.update(l_vars)
            l_fluents = {l_fluent}
            l_fluents.update(l_fluents)
        if r_var is not None:
            assert r_fluent is not None
            r_vars = {r_var}
            r_vars.update(r_vars)
            r_fluents = {r_fluent}
            r_fluents.update(r_fluents)

        if not l_vars and not r_vars:
            assert not l_fluents and not r_fluents
            return (self.manager.Equals(l_exp, r_exp), None, set(), None, set())
        else:
            return (
                self.manager.Exists(
                    self.manager.And(
                        self.manager.Equals(l_exp, r_exp), *l_fluents, *r_fluents
                    ),
                    *l_vars,
                    *r_vars,
                ),
                None,
                set(),
                None,
                set(),
            )

    def walk_le(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 2

        l_exp, l_var, l_vars, l_fluent, l_fluents = args[0]
        r_exp, r_var, r_vars, r_fluent, r_fluents = args[1]

        assert l_var is None and l_fluent is None
        assert r_var is None and r_fluent is None

        if not l_vars and not r_vars:
            assert not l_fluents and not r_fluents
            return (self.manager.LE(l_exp, r_exp), None, set(), None, set())
        else:
            return (
                self.manager.Exists(
                    self.manager.And(
                        self.manager.LE(l_exp, r_exp), *l_fluents, *r_fluents
                    ),
                    *l_vars,
                    *r_vars,
                ),
                None,
                set(),
                None,
                set(),
            )

    def walk_lt(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 2

        l_exp, l_var, l_vars, l_fluent, l_fluents = args[0]
        r_exp, r_var, r_vars, r_fluent, r_fluents = args[1]

        assert l_var is None and l_fluent is None
        assert r_var is None and r_fluent is None

        if not l_vars and not r_vars:
            return (self.manager.LT(l_exp, r_exp), None, set(), None, set())
        else:
            return (
                self.manager.Exists(
                    self.manager.And(
                        self.manager.LT(l_exp, r_exp), *l_fluents, *r_fluents
                    ),
                    *l_vars,
                    *r_vars,
                ),
                None,
                set(),
                None,
                set(),
            )

    def walk_fluent_exp(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        exp_args, variables, fluents = self._process_exp_args(args)
        new_fluent = self._new_fluents.get(expression.fluent(), None)
        if new_fluent is not None:
            v_type = cast(_UserType, expression.fluent().type)
            assert v_type.is_user_type()
            fresh_name = self._get_fresh_name(
                f"{new_fluent.name}_{v_type.name}".lower()
            )
            new_var = up.model.variable.Variable(fresh_name, v_type, self.env)
            exp_args.append(self.manager.VariableExp(new_var))
            return (
                self.manager.VariableExp(new_var),
                new_var,
                variables,
                self.manager.FluentExp(new_fluent, exp_args),
                fluents,
            )
        else:
            return (
                self.manager.FluentExp(expression.fluent(), exp_args),
                None,
                variables,
                None,
                fluents,
            )

    def walk_plus(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        exp_args, variables, fluents = self._process_exp_args(args)
        return (self.manager.Plus(*exp_args), None, variables, None, fluents)

    def walk_minus(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 2
        exp_args, variables, fluents = self._process_exp_args(args)
        return (self.manager.Minus(*exp_args), None, variables, None, fluents)

    def walk_times(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        exp_args, variables, fluents = self._process_exp_args(args)
        return (self.manager.Times(*exp_args), None, variables, None, fluents)

    def walk_div(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 2
        exp_args, variables, fluents = self._process_exp_args(args)
        return (self.manager.Div(*exp_args), None, variables, None, fluents)

    def walk_always(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 1
        exp_args, _, _ = self._process_exp_args(args)
        assert len(exp_args) == 1
        return (self.manager.Always(exp_args[0]), None, set(), None, set())

    def walk_sometime(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 1
        exp_args, _, _ = self._process_exp_args(args)
        assert len(exp_args) == 1
        return (self.manager.Sometime(exp_args[0]), None, set(), None, set())

    def walk_sometime_before(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 2
        exp_args, _, _ = self._process_exp_args(args)
        assert len(exp_args) == 2
        return (
            self.manager.SometimeBefore(exp_args[0], exp_args[1]),
            None,
            set(),
            None,
            set(),
        )

    def walk_sometime_after(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 2
        exp_args, _, _ = self._process_exp_args(args)
        assert len(exp_args) == 2
        return (
            self.manager.SometimeAfter(exp_args[0], exp_args[1]),
            None,
            set(),
            None,
            set(),
        )

    def walk_at_most_once(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        assert len(args) == 1
        exp_args, _, _ = self._process_exp_args(args)
        assert len(exp_args) == 1
        return (self.manager.AtMostOnce(exp_args[0]), None, set(), None, set())

    def walk_dot(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        raise NotImplementedError(
            "The UserType Fluents remover currently does not support multiagent"
        )

    @walkers.handles(op.CONSTANTS)
    @walkers.handles(
        op.OperatorKind.PARAM_EXP,
        op.OperatorKind.VARIABLE_EXP,
        op.OperatorKind.OBJECT_EXP,
        op.OperatorKind.TIMING_EXP,
    )
    def walk_identity(
        self,
        expression: FNode,
        args: List[
            Tuple[
                FNode,
                Optional["up.model.variable.Variable"],
                Set["up.model.variable.Variable"],
                Optional[FNode],
                Set[FNode],
            ]
        ],
    ) -> Tuple[
        FNode,
        Optional["up.model.variable.Variable"],
        Set["up.model.variable.Variable"],
        Optional[FNode],
        Set[FNode],
    ]:
        return (expression, None, set(), None, set())
