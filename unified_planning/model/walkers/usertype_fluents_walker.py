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


from typing import Dict, Iterable, List, Set, Tuple, cast
import unified_planning as up
import unified_planning.environment
import unified_planning.model.walkers as walkers
from unified_planning.model.fnode import FNode
from unified_planning.model.fluent import Fluent
from unified_planning.model.types import _UserType
import unified_planning.model.operators as op


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
        self, expression: FNode
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        """
        Removes UserType Fluents from the given expression and returns the generated
        expression, the set of Variables that are still free in the returned expression
        and the set of FluentExp that must be True in order for the given expression to
        be equivalent to the returned one.

        :param expression: The target expression in which usertype fluents must be removed.
        :return: The expression without userType fluents, the free variables in the
            expression and all the FluentExp that must be True for the 2 expressions to be
            equivalent.
        """
        exp, free_vars, added_fluents = self.walk(expression)
        return (exp, free_vars.copy(), added_fluents.copy())

    def _get_fresh_name(self, basename: str) -> str:
        name, counter = basename, 0
        while name in self._defined_names:
            name = f"{basename}_{counter}"
            counter += 1
        self._defined_names.add(name)
        return name

    def _process_exp_args(
        self,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[List[FNode], Set["up.model.variable.Variable"], Set[FNode]]:
        """
        This method takes the args given as parameters to a walker method (walk_and
        for example) and returns the resulting expressions, the set of free Variables
        and the set of FluentExp that are instantiated over the free Variables.

        If the arg type is boolean and there are free variables, those are bounded
        to the boolean expression using an And with their instantiated FluentExp and
        returning the And created under an Exists.

        :param args: The args given as parameters to a walker method.
        :return: The computed expressions, the Variables that are still free in the
            computed expressions and the FluentExp that use the free Variables
        """
        exp_args = []
        variables: Set["up.model.variable.Variable"] = set()
        fluents: Set[FNode] = set()
        for arg, free_vars, ut_fluents in args:
            arg_type = arg.type
            if free_vars and arg_type.is_bool_type():
                assert ut_fluents
                exp_args.append(
                    self.manager.Exists(self.manager.And(arg, *ut_fluents), *free_vars)
                )
            else:
                variables.update(free_vars)
                fluents.update(ut_fluents)
                exp_args.append(arg)
        return (exp_args, variables, fluents)

    def walk_and(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.And(*exp_args), set(), set())

    def walk_or(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.Or(*exp_args), set(), set())

    def walk_not(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        assert len(args) == 1
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.Not(*exp_args), set(), set())

    def walk_iff(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        assert len(args) == 2
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.Iff(*exp_args), set(), set())

    def walk_implies(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        assert len(args) == 2
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.Implies(*exp_args), set(), set())

    def walk_exists(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        assert len(args) == 1
        exp_args, _, _ = self._process_exp_args(args)
        added_vars = args[0][1]
        assert not any(
            v in added_vars for v in expression.variables()
        ), "Conflicting Variables naming"
        return (self.manager.Exists(exp_args[0], *expression.variables()), set(), set())

    def walk_forall(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        assert len(args) == 1
        exp_args, _, _ = self._process_exp_args(args)
        added_vars = args[0][1]
        assert not any(
            v in added_vars for v in expression.variables()
        ), "Conflicting Variables naming"
        return (self.manager.Forall(exp_args[0], *expression.variables()), set(), set())

    def walk_equals(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        assert len(args) == 2

        l_exp, l_vars, l_fluents = args[0]
        r_exp, r_vars, r_fluents = args[1]

        if not l_vars and not r_vars:
            assert not l_fluents and not r_fluents
            return (self.manager.Equals(l_exp, r_exp), set(), set())
        else:
            return (
                self.manager.Exists(
                    self.manager.And(
                        self.manager.Equals(l_exp, r_exp), *l_fluents, *r_fluents
                    ),
                    *l_vars,
                    *r_vars,
                ),
                set(),
                set(),
            )

    def walk_le(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        assert len(args) == 2

        l_exp, l_vars, l_fluents = args[0]
        r_exp, r_vars, r_fluents = args[1]

        if not l_vars and not r_vars:
            assert not l_fluents and not r_fluents
            return (self.manager.LE(l_exp, r_exp), set(), set())
        else:
            return (
                self.manager.Exists(
                    self.manager.And(
                        self.manager.LE(l_exp, r_exp), *l_fluents, *r_fluents
                    ),
                    *l_vars,
                    *r_vars,
                ),
                set(),
                set(),
            )

    def walk_lt(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        assert len(args) == 2

        l_exp, l_vars, l_fluents = args[0]
        r_exp, r_vars, r_fluents = args[1]

        if not l_vars and not r_vars:
            return (self.manager.LT(l_exp, r_exp), set(), set())
        else:
            return (
                self.manager.Exists(
                    self.manager.And(
                        self.manager.LT(l_exp, r_exp), *l_fluents, *r_fluents
                    ),
                    *l_vars,
                    *r_vars,
                ),
                set(),
                set(),
            )

    def walk_fluent_exp(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
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
            variables.add(new_var)
            fluents.add(self.manager.FluentExp(new_fluent, exp_args))

            return (self.manager.VariableExp(new_var), variables, fluents)
        else:
            return (
                self.manager.FluentExp(expression.fluent(), exp_args),
                variables,
                fluents,
            )

    def walk_plus(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        exp_args, variables, fluents = self._process_exp_args(args)
        return (self.manager.Plus(*exp_args), variables, fluents)

    def walk_minus(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        assert len(args) == 2
        exp_args, variables, fluents = self._process_exp_args(args)
        return (self.manager.Minus(*exp_args), variables, fluents)

    def walk_times(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        exp_args, variables, fluents = self._process_exp_args(args)
        return (self.manager.Times(*exp_args), variables, fluents)

    def walk_div(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        assert len(args) == 2
        exp_args, variables, fluents = self._process_exp_args(args)
        return (self.manager.Div(*exp_args), variables, fluents)

    def walk_dot(
        self,
        expression: FNode,
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
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
        args: List[Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]],
    ) -> Tuple[FNode, Set["up.model.variable.Variable"], Set[FNode]]:
        return (expression, set(), set())
