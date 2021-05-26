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

ALL_TYPES = list(range(0, 10))

(
AND, OR, NOT, IMPLIES, IFF, EQUALS,
FLUENT_EXP, BOOL_CONSTANT, PARAM_EXP,
OBJECT_EXP
) = ALL_TYPES


def op_to_str(node_id: int) -> str:
    """Returns a string representation of the given node."""
    return __OP_STR__[node_id]


__OP_STR__ = {
    AND : "AND",
    OR : "OR",
    NOT : "NOT",
    IMPLIES : "IMPLIES",
    IFF : "IFF",
    EQUALS : "EQUALS",
    FLUENT_EXP : "FLUENT_EXP",
    BOOL_CONSTANT : "BOOL_CONSTANT",
    PARAM_EXP: "PARAM_EXP",
    OBJECT_EXP: "OBJECT_EXP"
}
