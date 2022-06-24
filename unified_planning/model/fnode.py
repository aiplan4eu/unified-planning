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
"""FNode are the building blocks of expressions."""

import unified_planning
import unified_planning.model.fluent
import collections
from unified_planning.model.operators import OperatorKind
from typing import List, Union
from fractions import Fraction

FNodeContent = collections.namedtuple("FNodeContent",
                                      ["node_type", "args", "payload"])

class FNode(object):
    __slots__ = ["_content", "_node_id", "_monitoring_atom_predicate"]

    def __init__(self, content: FNodeContent, node_id: int):
        self._content = content
        self._node_id = node_id
        return

    # __eq__ is left as default while __hash__ uses the node id. This
    # is because we always have shared FNodes, hence in a single
    # environment two nodes have always different ids, but in
    # different environments they can have the same id. This is not an
    # issue since, by default, equality coincides with identity.
    def __hash__(self) -> int:
        return self._node_id

    def get_nary_expression_string(self, op: str, args: List['FNode']) -> str:
        p = []
        if len(args) > 0:
            p.append('(')
            p.append(str(args[0]))
            for x in args[1:]:
                p.append(op)
                p.append(str(x))
            p.append(')')
        return ''.join(p)

    def __repr__(self) -> str:
        if self.is_bool_constant():
            return 'true' if self.is_true() else 'false'
        elif self.is_int_constant():
            return str(self.constant_value())
        elif self.is_real_constant():
            return str(self.constant_value())
        elif self.is_fluent_exp():
            return self.fluent().name + self.get_nary_expression_string(', ', self.args)
        elif self.is_parameter_exp():
            return self.parameter().name
        elif self.is_variable_exp():
            return self.variable().name
        elif self.is_object_exp():
            return self.object().name
        elif self.is_timing_exp():
            return str(self.timing())
        elif self.is_and():
            return self.get_nary_expression_string(' and ', self.args)
        elif self.is_or():
            return self.get_nary_expression_string(' or ', self.args)
        elif self.is_not():
            return f'(not {str(self.arg(0))})'
        elif self.is_implies():
            return self.get_nary_expression_string(' implies ', self.args)
        elif self.is_iff():
            return self.get_nary_expression_string(' iff ', self.args)
        elif self.is_exists():
            s = ', '.join(str(v) for v in self.variables())
            return f"Exists ({s}) {str(self.arg(0))}"
        elif self.is_always():
            return f"Always({str(self.arg(0))})"
        elif self.is_sometime():
            return f"Sometime({str(self.arg(0))})"
        elif self.is_sometime_before():
            s = ', '.join(str(v) for v in self.args)
            return f"Sometime-Before({str(s)})"
        elif self.is_sometime_after():
            s = ', '.join(str(v) for v in self.args)
            return f"Sometime-After({str(s)})"
        elif self.is_at_most_once:
            return f"At-Most-Once({str(self.arg(0))})"
        elif self.is_forall():
            s = ', '.join(str(v) for v in self.variables())
            return f"Forall ({s}) {str(self.arg(0))}"
        elif self.is_plus():
            return self.get_nary_expression_string(' + ', self.args)
        elif self.is_minus():
            return self.get_nary_expression_string(' - ', self.args)
        elif self.is_times():
            return self.get_nary_expression_string(' * ', self.args)
        elif self.is_div():
            return self.get_nary_expression_string(' / ', self.args)
        elif self.is_le():
            return self.get_nary_expression_string(' <= ', self.args)
        elif self.is_lt():
            return self.get_nary_expression_string(' < ', self.args)
        elif self.is_equals():
            return self.get_nary_expression_string(' == ', self.args)
        else:
            raise

    @property
    def node_id(self) -> int:
        return self._node_id

    @property
    def node_type(self) -> OperatorKind:
        return self._content.node_type

    @property
    def args(self) -> List['FNode']:
        """Returns the subexpressions."""
        return self._content.args

    def arg(self, idx: int) -> 'FNode':
        """Return the given subexpression at the given position."""
        return self._content.args[idx]

    def is_constant(self) -> bool:
        """Test whether the expression is a constant."""
        return self.node_type == OperatorKind.BOOL_CONSTANT or \
            self.node_type == OperatorKind.INT_CONSTANT or \
            self.node_type == OperatorKind.REAL_CONSTANT or \
            self.node_type == OperatorKind.OBJECT_EXP

    def constant_value(self) -> Union[bool, int, Fraction]:
        """Return the value of the Constant."""
        assert self.is_constant()
        return self._content.payload

    def bool_constant_value(self) -> bool:
        """Return the bool value of the Constant."""
        assert self.is_bool_constant()
        return self._content.payload

    def int_constant_value(self) -> int:
        """Return the int value of the Constant."""
        assert self.is_int_constant()
        return self._content.payload

    def real_constant_value(self) -> Fraction:
        """Return the real value of the Constant."""
        assert self.is_real_constant()
        return self._content.payload

    def fluent(self) -> 'unified_planning.model.fluent.Fluent':
        """Return the fluent of the FluentExp."""
        assert self.is_fluent_exp()
        return self._content.payload

    def parameter(self) -> 'unified_planning.model.parameter.Parameter':
        """Return the parameter of the ParameterExp."""
        assert self.is_parameter_exp()
        return self._content.payload

    def set_monitoring_atom_predicate(self, atom):
        assert (self.is_always() or self.is_at_most_once or self.is_sometime
            or self.is_sometime_after or self.is_sometime_before)
        self._monitoring_atom_predicate = atom

    def variable(self) -> 'unified_planning.model.variable.Variable':
        """Return the variable of the VariableExp."""
        assert self.is_variable_exp()
        return self._content.payload

    def variables(self) -> List['unified_planning.model.variable.Variable']:
        """Return the variable of the Exists or Forall."""
        assert self.is_exists() or self.is_forall()
        return list(self._content.payload)

    def object(self) -> 'unified_planning.model.object.Object':
        """Return the object of the ObjectExp."""
        assert self.is_object_exp()
        return self._content.payload

    def timing(self) -> 'unified_planning.model.timing.Timing':
        """Return the object of the TimingExp."""
        assert self.is_timing_exp()
        return self._content.payload

    def is_bool_constant(self) -> bool:
        """Test whether the expression is a boolean constant."""
        return self.node_type == OperatorKind.BOOL_CONSTANT

    def is_int_constant(self) -> bool:
        """Test whether the expression is an integer constant."""
        return self.node_type == OperatorKind.INT_CONSTANT

    def is_real_constant(self) -> bool:
        """Test whether the expression is a real constant."""
        return self.node_type == OperatorKind.REAL_CONSTANT

    def is_true(self) -> bool:
        """Test whether the expression is the True Boolean constant."""
        return self.is_bool_constant() and self.constant_value() == True

    def is_false(self) -> bool:
        """Test whether the expression is the False Boolean constant."""
        return self.is_bool_constant() and self.constant_value() == False

    def is_and(self) -> bool:
        """Test whether the node is the And operator."""
        return self.node_type == OperatorKind.AND

    def is_or(self) -> bool:
        """Test whether the node is the Or operator."""
        return self.node_type == OperatorKind.OR

    def is_not(self) -> bool:
        """Test whether the node is the Not operator."""
        return self.node_type == OperatorKind.NOT

    def is_implies(self) -> bool:
        """Test whether the node is the Implies operator."""
        return self.node_type == OperatorKind.IMPLIES

    def is_iff(self) -> bool:
        """Test whether the node is the Iff operator."""
        return self.node_type == OperatorKind.IFF

    def is_exists(self) -> bool:
        """Test whether the node is the Exists operator."""
        return self.node_type == OperatorKind.EXISTS

    def is_always(self) -> bool:
        """Test whether the node is the Always constraint."""
        return self.node_type == OperatorKind.ALWAYS

    def is_sometime(self) -> bool:
        """Test whether the node is the Sometime constraint."""
        return self.node_type == OperatorKind.SOMETIME

    def is_at_most_once(self) -> bool:
        """Test whether the node is the At-Most-Once constraint."""
        return self.node_type == OperatorKind.AT_MOST_ONCE

    def is_sometime_before(self) -> bool:
        """Test whether the node is the Sometime-Before constraint."""
        return self.node_type == OperatorKind.SOMETIME_BEFORE

    def is_sometime_after(self) -> bool:
        """Test whether the node is the Sometime-After constraint."""
        return self.node_type == OperatorKind.SOMETIME_AFTER

    def is_forall(self) -> bool:
        """Test whether the node is the Forall operator."""
        return self.node_type == OperatorKind.FORALL

    def is_fluent_exp(self) -> bool:
        """Test whether the node is a fluent."""
        return self.node_type == OperatorKind.FLUENT_EXP

    def is_parameter_exp(self) -> bool:
        """Test whether the node is an action parameter."""
        return self.node_type == OperatorKind.PARAM_EXP

    def is_variable_exp(self) -> bool:
        """Test whether the node is a variable."""
        return self.node_type == OperatorKind.VARIABLE_EXP

    def is_object_exp(self) -> bool:
        """Test whether the node is an action object."""
        return self.node_type == OperatorKind.OBJECT_EXP

    def is_timing_exp(self) -> bool:
        """Test whether the node is an action object."""
        return self.node_type == OperatorKind.TIMING_EXP

    def is_plus(self) -> bool:
        """Test whether the node is the Plus operator."""
        return self.node_type == OperatorKind.PLUS

    def is_minus(self) -> bool:
        """Test whether the node is the Minus operator."""
        return self.node_type == OperatorKind.MINUS

    def is_times(self) -> bool:
        """Test whether the node is the Times operator."""
        return self.node_type == OperatorKind.TIMES

    def is_div(self) -> bool:
        """Test whether the node is the Div operator."""
        return self.node_type == OperatorKind.DIV

    def is_equals(self) -> bool:
        """Test whether the node is the Equals operator."""
        return self.node_type == OperatorKind.EQUALS

    def is_le(self) -> bool:
        """Test whether the node is the LE operator."""
        return self.node_type == OperatorKind.LE

    def is_lt(self) -> bool:
        """Test whether the node is the LT operator."""
        return self.node_type == OperatorKind.LT
