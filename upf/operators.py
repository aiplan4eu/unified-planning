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
"""This module defines all the operators used by the UPF."""

ALL_TYPES = list(range(0, 21))

(
AND, OR, NOT, IMPLIES, IFF, EXISTS, FORALL,
FLUENT_EXP, PARAM_EXP, VARIABLE_EXP, OBJECT_EXP,
BOOL_CONSTANT, INT_CONSTANT, REAL_CONSTANT,
PLUS, MINUS, TIMES, DIV,
LE, LT, EQUALS
) = ALL_TYPES

BOOL_OPERATORS = frozenset([AND, OR, NOT, IMPLIES, IFF, EXISTS, FORALL])

CONSTANTS = frozenset([BOOL_CONSTANT, REAL_CONSTANT, INT_CONSTANT])

IRA_RELATIONS = frozenset([LE, LT])

RELATIONS = frozenset((EQUALS,)) | IRA_RELATIONS

IRA_OPERATORS = frozenset([PLUS, MINUS, TIMES, DIV])


def op_to_str(node_id: int) -> str:
    """Returns a string representation of the given node."""
    return __OP_STR__[node_id]


__OP_STR__ = {
    AND : "AND",
    OR : "OR",
    NOT : "NOT",
    IMPLIES : "IMPLIES",
    IFF : "IFF",
    EXISTS : "EXISTS",
    FORALL : "FORALL",
    FLUENT_EXP : "FLUENT_EXP",
    PARAM_EXP: "PARAM_EXP",
    VARIABLE_EXP: "VARIABLE_EXP",
    OBJECT_EXP: "OBJECT_EXP",
    BOOL_CONSTANT : "BOOL_CONSTANT",
    INT_CONSTANT : "INT_CONSTANT",
    REAL_CONSTANT : "REAL_CONSTANT",
    PLUS : "PLUS",
    MINUS : "MINUS",
    TIMES : "TIMES",
    DIV : "DIV",
    LE : "LE",
    LT : "LT",
    EQUALS : "EQUALS"
}
