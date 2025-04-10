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
"""This module defines all the operators used by the Unified Planning library."""
from enum import Enum, auto


class OperatorKind(Enum):
    """
    Enum representing the type of an :class:`~unified_planning.model.FNode`. The :func:`Operator <unified_planning.model.FNode.node_type>` of an `FNode` defines the semantic for all the
    other fields of the `FNode`.
    """

    AND = auto()
    OR = auto()
    NOT = auto()
    IMPLIES = auto()
    IFF = auto()
    EXISTS = auto()
    FORALL = auto()
    FLUENT_EXP = auto()
    PARAM_EXP = auto()
    VARIABLE_EXP = auto()
    OBJECT_EXP = auto()
    TIMING_EXP = auto()
    IS_PRESENT_EXP = auto()
    BOOL_CONSTANT = auto()
    INT_CONSTANT = auto()
    REAL_CONSTANT = auto()
    PLUS = auto()
    MINUS = auto()
    TIMES = auto()
    DIV = auto()
    LE = auto()
    LT = auto()
    EQUALS = auto()
    ALWAYS = auto()
    SOMETIME = auto()
    SOMETIME_BEFORE = auto()
    SOMETIME_AFTER = auto()
    AT_MOST_ONCE = auto()
    DOT = auto()


BOOL_OPERATORS = frozenset(
    [
        OperatorKind.AND,
        OperatorKind.OR,
        OperatorKind.NOT,
        OperatorKind.IMPLIES,
        OperatorKind.IFF,
        OperatorKind.EXISTS,
        OperatorKind.FORALL,
    ]
)

CONSTANTS = frozenset(
    [OperatorKind.BOOL_CONSTANT, OperatorKind.REAL_CONSTANT, OperatorKind.INT_CONSTANT]
)

IRA_RELATIONS = frozenset([OperatorKind.LE, OperatorKind.LT])

RELATIONS = frozenset((OperatorKind.EQUALS,)) | IRA_RELATIONS

IRA_OPERATORS = frozenset(
    [OperatorKind.PLUS, OperatorKind.MINUS, OperatorKind.TIMES, OperatorKind.DIV]
)

TRAJECTORY_CONSTRAINTS = frozenset(
    [
        OperatorKind.ALWAYS,
        OperatorKind.SOMETIME,
        OperatorKind.SOMETIME_BEFORE,
        OperatorKind.SOMETIME_AFTER,
        OperatorKind.AT_MOST_ONCE,
    ]
)
