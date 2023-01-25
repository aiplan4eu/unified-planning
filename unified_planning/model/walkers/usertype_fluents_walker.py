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

from fractions import Fraction
from collections import OrderedDict
from functools import reduce
from typing import Dict, List, Optional, Set, Tuple, Union
import unified_planning as up
import unified_planning.environment
import unified_planning.model.walkers as walkers
from unified_planning.model.walkers.identitydag import IdentityDagWalker
from unified_planning.model.fnode import FNode
from unified_planning.model.fluent import Fluent
from unified_planning.model.variable import Variable
from unified_planning.model.types import Type
import unified_planning.model.operators as op


class UsertypeFluentsWalker(IdentityDagWalker):
    """
    TODO
    """

    def __init__(
        self,
        new_fluents: Dict[Fluent, Fluent],
        env: "unified_planning.environment.Environment",
    ):
        walkers.dag.DagWalker.__init__(self)
        self._new_fluents = new_fluents
        self.env = env
        self.manager = env.expression_manager

    def remove_usertype_fluents(
        self, expression: FNode
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        """
        TODO
        Performs basic simplification of the given expression.

        If a :class:`~unified_planning.model.Problem` is given at the constructor, it also uses the static `fluents` of the `Problem` for
        a better simplification.

        :param expression: The target expression that must be simplified with constant propagation.
        :return: The simplified expression.
        """
        return self.walk(expression)

    # TODO handle conflicting variable names

    def _process_exp_args(
        self,
        args: List[Tuple[FNode, Set[Variable], Set[FNode]]],
        types: Optional[List[Type]] = None,
    ) -> Tuple[List[FNode], Set[Variable], Set[FNode]]:
        """
        This method takes the args given as parameters to a walker method (walk_and
        for example) and a List of expected types (the default is everything boolean)
        and returns the resulting expressions, the set of free Variables and the set
        of FluentExp that are instantiated over the free Variables.

        If the type expected is boolean and there are free variables, those are bounded
        to the boolean expression using an And with their instantiated FluentExp and
        returning the And created under an Exists.

        :param args: The args given as parameters to a walker method.
        :param types: The List of expected Types, defaults to all BoolType.
        :return: The computed expressions, the Variables that are still free in the
            computed expressions and the FluentExp that use the free Variables
        """
        if types is None:
            types_list = [self.env.type_manager.BoolType() for _ in args]
        else:
            types_list = types
        exp_args = []
        variables = set()
        fluents = set()
        assert len(args) == len(types_list)
        # TODO understand if the types parameter can be removed, for now it is ignored
        # for (arg, free_vars, ut_fluents), arg_type in zip(args, types_list):
        for arg, free_vars, ut_fluents in args:
            arg_type = arg.type
            if free_vars and arg_type.is_bool_type():
                assert ut_fluents
                exp_args.append(
                    self.manager.Exists(self.manager.And(arg, *ut_fluents), *free_vars)
                )
            else:
                variables.union(free_vars)
                fluents.union(ut_fluents)
                exp_args.append(arg)
        # check that if types is None there are no variables and fluents
        assert (not variables and not fluents) or types is not None
        return (exp_args, variables, fluents)

    def walk_and(
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.And(*exp_args), set(), set())

    def walk_or(
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.Or(*exp_args), set(), set())

    def walk_not(
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        assert len(args) == 1
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.Not(*exp_args), set(), set())

    def walk_iff(
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        assert len(args) == 2
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.Iff(*exp_args), set(), set())

    def walk_implies(
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        assert len(args) == 2
        exp_args, _, _ = self._process_exp_args(args)
        return (self.manager.Implies(*exp_args), set(), set())

    def walk_exists(
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        assert len(args) == 1
        exp_args, _, _ = self._process_exp_args(args)
        added_vars = args[0][1]
        assert not any(
            v in added_vars for v in expression.variables()
        ), "Conflicting Variables naming"
        return (self.manager.Exists(*exp_args, *expression.variables()), set(), set())

    def walk_forall(
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        assert len(args) == 1
        exp_args, _, _ = self._process_exp_args(args)
        added_vars = args[0][1]
        assert not any(
            v in added_vars for v in expression.variables()
        ), "Conflicting Variables naming"
        return (self.manager.Forall(*exp_args, *expression.variables()), set(), set())

    def walk_equals(
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
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
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
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
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
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
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        exp_args, variables, fluents = self._process_exp_args(
            args, types=[p.type for p in expression.fluent().signature]
        )
        new_fluent = self._new_fluents.get(expression.fluent(), None)
        if new_fluent is not None and not variables:
            name = "new_name"  # TODO find a way to name without conflicts
            new_var = Variable(name, expression.fluent().type, self.env)
            return (
                self.manager.VariableExp(new_var),
                {new_var},
                {self.manager.FluentExp(new_fluent, *exp_args)},
            )
        elif (
            new_fluent is not None
        ):  # and variables, meaning there are nested usertype_fluents
            var_type = expression.fluent().type
            basename, counter = (
                "new_name",
                0,
            )  # TODO find a way to name without conflicts
            new_var = Variable(basename, var_type, self.env)
            while new_var in variables:
                name = f"{basename}_{counter}"
                counter += 1
                new_var = Variable(name, var_type, self.env)
            variables.add(new_var)
            fluents.add({self.manager.FluentExp(new_fluent, *exp_args, new_var)})
            return (self.manager.VariableExp(new_var), variables, fluents)
        else:
            return (
                self.manager.FluentExp(expression.fluent(), exp_args),
                variables,
                fluents,
            )

    def walk_plus(
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        exp_args, variables, fluents = self._process_exp_args(args)
        return (self.manager.Plus(*exp_args), variables, fluents)

    def walk_minus(
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        assert len(args) == 2
        exp_args, variables, fluents = self._process_exp_args(args)
        return (self.manager.Minus(*exp_args), variables, fluents)

    def walk_times(
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        exp_args, variables, fluents = self._process_exp_args(args)
        return (self.manager.Times(*exp_args), variables, fluents)

    def walk_div(
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        assert len(args) == 2
        exp_args, variables, fluents = self._process_exp_args(args)
        return (self.manager.Div(*exp_args), variables, fluents)

    def walk_dot(
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
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
        self, expression: FNode, args: List[Tuple[FNode, Set[Variable], Set[FNode]]]
    ) -> Tuple[FNode, Set[Variable], Set[FNode]]:
        return (expression, set(), set())
