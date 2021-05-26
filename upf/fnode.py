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

import collections
import upf.operators as op

FNodeContent = collections.namedtuple("FNodeContent",
                                      ["node_type", "args", "payload"])

class FNode(object):
    __slots__ = ["_content", "_node_id"]

    def __init__(self, content, node_id):
        self._content = content
        self._node_id = node_id
        return

    # __eq__ is left as default while __hash__ uses the node id. This
    # is because we always have shared FNodes, hence in a single
    # environment two nodes have always different ids, but in
    # different environments they can have the same id. This is not an
    # issue since, by default, equality coincides with identity.
    def __hash__(self):
        return self._node_id

    def node_id(self):
        return self._node_id

    def node_type(self):
        return self._content.node_type

    def args(self):
        """Returns the subformulae."""
        return self._content.args

    def arg(self, idx):
        """Return the given subformula at the given position."""
        return self._content.args[idx]

    def is_constant(self, _type=None, value=None):
        """Test whether the formula is a constant."""
        return self.node_type() == op.BOOL_CONSTANT

    def constant_value(self):
        """Return the value of the Constant."""
        assert self.is_constant()
        return self._content.payload

    def fluent(self):
        """Return the fluent of the FluentExp."""
        assert self.is_fluent_exp()
        return self._content.payload

    def parameter(self):
        """Return the parameter of the ParameterExp."""
        assert self.is_parameter_exp()
        return self._content.payload

    def object(self):
        """Return the object of the ObjectExp."""
        assert self.is_object_exp()
        return self._content.payload

    def is_true(self):
        """Test whether the formula is the True Boolean constant."""
        return self.constant_value() == True

    def is_false(self):
        """Test whether the formula is the False Boolean constant."""
        return self.constant_value() == False

    def is_and(self):
        """Test whether the node is the And operator."""
        return self.node_type() == op.AND

    def is_or(self):
        """Test whether the node is the Or operator."""
        return self.node_type() == op.OR

    def is_not(self):
        """Test whether the node is the Not operator."""
        return self.node_type() == op.NOT

    def is_implies(self):
        """Test whether the node is the Implies operator."""
        return self.node_type() == op.IMPLIES

    def is_iff(self):
        """Test whether the node is the Iff operator."""
        return self.node_type() == op.IFF

    def is_equals(self):
        """Test whether the node is the Equals operator."""
        return self.node_type() == op.EQUALS

    def is_fluent_exp(self):
        """Test whether the node is a fluent."""
        return self.node_type() == op.FLUENT_EXP

    def is_parameter_exp(self):
        """Test whether the node is an action parameter."""
        return self.node_type() == op.PARAM_EXP

    def is_object_exp(self):
        """Test whether the node is an action object."""
        return self.node_type() == op.OBJECT_EXP
