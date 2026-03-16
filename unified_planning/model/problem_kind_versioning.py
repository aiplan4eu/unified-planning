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
    "UNDEFINED_INITIAL_NUMERIC": (2, None),
    "UNDEFINED_INITIAL_SYMBOLIC": (2, None),
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


def upgrade_1_2(version_1_features: Set[str]) -> Set[str]:
    """Upgrade features from version 1 to version 2."""
    version_2_features = version_1_features.copy()

    if "CONTINUOUS_NUMBERS" in version_1_features:
        if "NUMERIC_FLUENTS" in version_1_features:
            version_2_features.update({"REAL_FLUENTS"})

    if "DISCRETE_NUMBERS" in version_1_features:
        if "NUMERIC_FLUENTS" in version_1_features:
            version_2_features.update({"INT_FLUENTS"})

    if "ACTIONS_COST" in version_1_features:
        version_2_features.update(
            {"INT_NUMBERS_IN_ACTIONS_COST", "REAL_NUMBERS_IN_ACTIONS_COST"}
        )

    if "OVERSUBSCRIPTION" in version_1_features:
        version_2_features.update(
            {"INT_NUMBERS_IN_OVERSUBSCRIPTION", "REAL_NUMBERS_IN_OVERSUBSCRIPTION"}
        )

    if "CONTINUOUS_TIME" in version_1_features:
        version_2_features.update({"REAL_TYPE_DURATIONS", "INT_TYPE_DURATIONS"})

    if "DISCRETE_TIME" in version_1_features:
        version_2_features.update({"INT_TYPE_DURATIONS"})

    # Remove deprecated features
    version_2_features.difference_update(
        {
            "CONTINUOUS_NUMBERS",
            "DISCRETE_NUMBERS",
            "NUMERIC_FLUENTS",
        }
    )

    return version_2_features


def upgrade_2_3(version_2_features: Set[str]) -> Set[str]:
    """Upgrade features from version 2 to version 3."""
    return version_2_features.copy()


# Mapping of upgrade functions
upgrade_functions_map = {
    (1, 2): upgrade_1_2,
    (2, 3): upgrade_2_3,
}


def equalize_versions(
    features_1: Set[str], features_2: Set[str], version_1: int, version_2: int
) -> Tuple[Set[str], Set[str], int]:
    """Equalizes two ProblemKind versions by upgrading the older one."""
    while version_1 < version_2:
        upgrade_function = upgrade_functions_map[(version_1, version_1 + 1)]
        features_1 = upgrade_function(features_1)
        version_1 += 1

    while version_2 < version_1:
        upgrade_function = upgrade_functions_map[(version_2, version_2 + 1)]
        features_2 = upgrade_function(features_2)
        version_2 += 1

    assert version_1 == version_2
    return features_1, features_2, version_1
