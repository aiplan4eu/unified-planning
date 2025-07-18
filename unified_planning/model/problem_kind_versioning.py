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
from typing import Set, Tuple


# This module handles the changing of versions of the ProblemKind class, defined in the
# up.model.problem_kind.py file


# Mapping from a feature to the  version it was introduced (defaults to 1) and the
# version it was deprecated (defaults to None, None if it not yet deprecated)
FEATURES_VERSIONS = {
    "CONTINUOUS_NUMBERS": (1, 2),
    "DISCRETE_NUMBERS": (1, 2),
    "NUMERIC_FLUENTS": (1, 2),
    "INT_TYPE_DURATIONS": (2, None),
    "REAL_TYPE_DURATIONS": (2, None),
    "INT_FLUENTS": (2, None),
    "REAL_FLUENTS": (2, None),
    "INT_NUMBERS_IN_ACTIONS_COST": (2, None),
    "REAL_NUMBERS_IN_ACTIONS_COST": (2, None),
    "INT_NUMBERS_IN_OVERSUBSCRIPTION": (2, None),
    "REAL_NUMBERS_IN_OVERSUBSCRIPTION": (2, None),
    "UNDEFINED_INITIAL_NUMERIC": (3, None),
    "UNDEFINED_INITIAL_SYMBOLIC": (3, None),
    "PROCESSES": (3, None),
    "EVENTS": (3, None),
    "INCREASE_CONTINUOUS_EFFECTS": (3, None),
    "DECREASE_CONTINUOUS_EFFECTS": (3, None),
    "NON_LINEAR_CONTINUOUS_EFFECTS": (3, None),
}

LATEST_PROBLEM_KIND_VERSION = 3

# Version changes:
# Version 2: Added granularity to the numeric side in different part of the problem
#            and deprecated the version 1 way of describing it.
# Added:
# REAL_FLUENTS
# INT_FLUENTS
# REAL_TYPE_DURATIONS
# INT_TYPE_DURATIONS
# REAL_NUMBERS_IN_ACTIONS_COST
# INT_NUMBERS_IN_ACTIONS_COST
# REAL_NUMBERS_IN_OVERSUBSCRIPTION
# INT_NUMBERS_IN_OVERSUBSCRIPTION
# Note: INT_* is a special case of REAL_*, so if REAL_* is supported, also
#       INT_* should be specified as supported.
# Deprecated:
# CONTINUOUS_NUMBERS
# DISCRETE_NUMBERS
# NUMERIC_FLUENTS


def downgrade_2_1(version_2_features: Set[str]) -> Set[str]:
    """
    Method to downgrade the features of a ProblemKind of version 2 to the features
    of a ProblemKind of version 1.
    """
    version_1_features = version_2_features.copy()
    continuous_numbers_features = ("REAL_FLUENTS", "REAL_ACTION_PARAMETERS")
    discrete_numbers_features = (
        "BOUNDED_INT_FLUENT_PARAMETERS",
        "BOUNDED_INT_ACTION_PARAMETERS",
        "UNBOUNDED_INT_ACTION_PARAMETERS",
        "INT_FLUENTS",
    )
    numeric_fluents_features = ("INT_FLUENTS", "REAL_FLUENTS")

    if any(f in version_2_features for f in continuous_numbers_features):
        version_1_features.add("CONTINUOUS_NUMBERS")
    if any(f in version_2_features for f in discrete_numbers_features):
        version_1_features.add("DISCRETE_NUMBERS")
    if any(f in version_2_features for f in numeric_fluents_features):
        version_1_features.add("NUMERIC_FLUENTS")

    features_to_remove = (
        "REAL_FLUENTS",
        "INT_FLUENTS",
        "REAL_TYPE_DURATIONS",
        "INT_TYPE_DURATIONS",
        "REAL_NUMBERS_IN_ACTIONS_COST",
        "INT_NUMBERS_IN_ACTIONS_COST",
        "REAL_NUMBERS_IN_OVERSUBSCRIPTION",
        "INT_NUMBERS_IN_OVERSUBSCRIPTION",
    )
    for f in features_to_remove:
        version_1_features.discard(f)

    return version_1_features


def downgrade_3_2(version_3_features: Set[str]) -> Set[str]:
    """
    Method to downgrade the features of a ProblemKind of version 3 to the features
    of a ProblemKind of version 2.
    """
    version_2_features = version_3_features.copy()

    features_to_remove = (
        "UNDEFINED_INITIAL_NUMERIC",
        "UNDEFINED_INITIAL_SYMBOLIC",
        "PROCESSES",
        "EVENTS",
        "INCREASE_CONTINUOUS_EFFECTS",
        "DECREASE_CONTINUOUS_EFFECTS",
        "NON_LINEAR_CONTINUOUS_EFFECTS",
    )

    for f in features_to_remove:
        version_2_features.discard(f)

    return version_2_features


# A mapping from a tuple from a version to another and the function that does that conversion
downgrade_functions_map = {(2, 1): downgrade_2_1, (3, 2): downgrade_3_2}


def equalize_versions(
    features_1: Set[str], features_2: Set[str], version_1: int, version_2: int
) -> Tuple[Set[str], Set[str], int]:
    """Method that equalizes 2 ProblemKind's versions."""
    while version_1 > version_2:
        downgrade_function = downgrade_functions_map[(version_1, version_1 - 1)]
        features_1 = downgrade_function(features_1)
        version_1 -= 1

    while version_2 > version_1:
        downgrade_function = downgrade_functions_map[(version_2, version_2 - 1)]
        features_2 = downgrade_function(features_2)
        version_2 -= 1

    assert version_1 == version_2
    return features_1, features_2, version_1
