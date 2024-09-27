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

from functools import lru_cache, partialmethod, total_ordering
from itertools import chain
from typing import Dict, Iterable, List, Optional, Set
from warnings import warn
import unified_planning as up

from unified_planning.model.problem_kind_versioning import (
    FEATURES_VERSIONS,
    equalize_versions,
    LATEST_PROBLEM_KIND_VERSION,
)


# TODO: This features map needs to be extended with all the problem characterizations.
FEATURES = {
    "PROBLEM_CLASS": [
        "ACTION_BASED",
        "HIERARCHICAL",
        "CONTINGENT",
        "ACTION_BASED_MULTI_AGENT",
        "SCHEDULING",
        "TAMP",
    ],
    "PROBLEM_TYPE": ["SIMPLE_NUMERIC_PLANNING", "GENERAL_NUMERIC_PLANNING"],
    "TIME": [
        "CONTINUOUS_TIME",
        "DISCRETE_TIME",
        "INTERMEDIATE_CONDITIONS_AND_EFFECTS",
        "EXTERNAL_CONDITIONS_AND_EFFECTS",
        "TIMED_EFFECTS",
        "TIMED_GOALS",
        "DURATION_INEQUALITIES",
        "SELF_OVERLAPPING",
        "PROCESSES",
        "EVENTS",
    ],
    "EXPRESSION_DURATION": [
        "STATIC_FLUENTS_IN_DURATIONS",
        "FLUENTS_IN_DURATIONS",
        "INTERPRETED_FUNCTIONS_IN_DURATIONS",
        "INT_TYPE_DURATIONS",
        "REAL_TYPE_DURATIONS",
    ],
    "NUMBERS": [
        "BOUNDED_TYPES",
        "CONTINUOUS_NUMBERS",  # deprecated
        "DISCRETE_NUMBERS",  # deprecated
    ],
    "CONDITIONS_KIND": [
        "NEGATIVE_CONDITIONS",
        "DISJUNCTIVE_CONDITIONS",
        "EQUALITIES",
        "EXISTENTIAL_CONDITIONS",
        "UNIVERSAL_CONDITIONS",
        "INTERPRETED_FUNCTIONS_IN_CONDITIONS",
    ],
    "EFFECTS_KIND": [
        "CONDITIONAL_EFFECTS",
        "INCREASE_EFFECTS",
        "DECREASE_EFFECTS",
        "INCREASE_CONTINUOUS_EFFECTS",
        "DECREASE_CONTINUOUS_EFFECTS",
        "NON_LINEAR_CONTINUOUS_EFFECTS",
        "STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS",
        "STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS",
        "STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS",
        "FLUENTS_IN_BOOLEAN_ASSIGNMENTS",
        "FLUENTS_IN_NUMERIC_ASSIGNMENTS",
        "FLUENTS_IN_OBJECT_ASSIGNMENTS",
        "INTERPRETED_FUNCTIONS_IN_BOOLEAN_ASSIGNMENTS",
        "INTERPRETED_FUNCTIONS_IN_NUMERIC_ASSIGNMENTS",
        "INTERPRETED_FUNCTIONS_IN_OBJECT_ASSIGNMENTS",
        "FORALL_EFFECTS",
    ],
    "TYPING": ["FLAT_TYPING", "HIERARCHICAL_TYPING"],
    "PARAMETERS": [
        "BOOL_FLUENT_PARAMETERS",
        "BOUNDED_INT_FLUENT_PARAMETERS",
        "BOOL_ACTION_PARAMETERS",
        "BOUNDED_INT_ACTION_PARAMETERS",
        "UNBOUNDED_INT_ACTION_PARAMETERS",
        "REAL_ACTION_PARAMETERS",
    ],
    "FLUENTS_TYPE": [
        "INT_FLUENTS",
        "REAL_FLUENTS",
        "OBJECT_FLUENTS",
        "NUMERIC_FLUENTS",  # deprecated
    ],
    "QUALITY_METRICS": [
        "ACTIONS_COST",
        "FINAL_VALUE",
        "MAKESPAN",
        "PLAN_LENGTH",
        "OVERSUBSCRIPTION",
        "TEMPORAL_OVERSUBSCRIPTION",
    ],
    "ACTIONS_COST_KIND": [
        "STATIC_FLUENTS_IN_ACTIONS_COST",
        "FLUENTS_IN_ACTIONS_COST",
        "INT_NUMBERS_IN_ACTIONS_COST",
        "REAL_NUMBERS_IN_ACTIONS_COST",
    ],
    "OVERSUBSCRIPTION_KIND": [
        "INT_NUMBERS_IN_OVERSUBSCRIPTION",
        "REAL_NUMBERS_IN_OVERSUBSCRIPTION",
    ],
    "SIMULATED_ENTITIES": ["SIMULATED_EFFECTS"],
    "CONSTRAINTS_KIND": ["TRAJECTORY_CONSTRAINTS", "STATE_INVARIANTS"],
    "HIERARCHICAL": [
        "METHOD_PRECONDITIONS",
        "TASK_NETWORK_CONSTRAINTS",
        "INITIAL_TASK_NETWORK_VARIABLES",
        "TASK_ORDER_TOTAL",
        "TASK_ORDER_PARTIAL",
        "TASK_ORDER_TEMPORAL",
    ],
    "MULTI_AGENT": [
        "AGENT_SPECIFIC_PRIVATE_GOAL",
        "AGENT_SPECIFIC_PUBLIC_GOAL",
    ],
    "INITIAL_STATE": [
        "UNDEFINED_INITIAL_NUMERIC",
        "UNDEFINED_INITIAL_SYMBOLIC",
    ],
}


all_features = set(chain(*FEATURES.values()))


@lru_cache(maxsize=None)
def get_valid_features(version: int) -> Set[str]:
    """
    Returns the set of features that are present and not deprecated in the
    given ProblemKind's version.

    :param version: The ProblemKind's version to extract the valid features from.
    :return: the set of features that are present and not deprecated in the
        given ProblemKind's version.
    """
    valid_features: Set[str] = set()
    for f in all_features:
        added_version, deprecated_version = FEATURES_VERSIONS.get(f, (1, None))
        if added_version > version:
            continue
        if deprecated_version is not None and deprecated_version <= version:
            continue
        valid_features.add(f)
    return valid_features


class ProblemKindMeta(type):
    """Meta class used to interpret the nodehandler decorator."""

    def __new__(cls, name, bases, dct):
        def _set(self, feature, possible_features):
            assert feature in possible_features, str(feature)
            added_feature_version, _ = FEATURES_VERSIONS.get(feature, (1, None))
            assert (
                self._version is None or added_feature_version <= self._version
            ), f"ProblemKind's declared version: {self._version} but {feature} is added in version {added_feature_version}"
            self._features.add(feature)

        def _unset(self, feature, possible_features):
            assert feature in possible_features
            self._features.discard(feature)

        def _has(self, features):
            return len(self._features.intersection(features)) > 0

        obj = type.__new__(cls, name, bases, dct)
        for m, l in FEATURES.items():
            setattr(obj, "set_" + m.lower(), partialmethod(_set, possible_features=l))
            setattr(
                obj, "unset_" + m.lower(), partialmethod(_unset, possible_features=l)
            )
            setattr(obj, "has_" + m.lower(), partialmethod(_has, features=l))
            for f in l:
                setattr(obj, "has_" + f.lower(), partialmethod(_has, features=[f]))
        return obj


@total_ordering
class ProblemKind(up.AnyBaseClass, metaclass=ProblemKindMeta):
    """
    This class represents the main interesting feature that a :class:`planning Problem <unified_planning.model.AbstractProblem>` can have in order to understand
    if an :class:`~unified_planning.engines.Engine` is capable of solving the `Problem` or not; some features might also help the `Engine`, allowing
    some assumptions to be made.

    The `ProblemKind` of a `Problem` is calculated by it's :func:`kind <unified_planning.model.Problem.kind>` property.
    """

    def __init__(
        self, features: Optional[Iterable[str]] = None, version: Optional[int] = None
    ):
        self._features: Set[str] = set() if features is None else set(features)
        for f in self._features:
            assert f in all_features, f"Feature {f} not in defined features"
        self._version = version
        if self._version is not None:
            assert self._version > 0 and isinstance(
                self._version, int
            ), "Error, the ProblemKind version must be a positive integer"
            for feature in self._features:
                added_feature_version, _ = FEATURES_VERSIONS.get(feature, (1, None))
                assert (
                    added_feature_version <= self._version
                ), f"ProblemKind's declared version: {self._version} but {feature} is added in version {added_feature_version}"

    def __repr__(self) -> str:
        features_gen = (f"'{feature}'" for feature in self._features)
        return f'ProblemKind([{", ".join(features_gen)}], version={self._version})'

    def __str__(self) -> str:
        features_mapped: Dict[str, List[str]] = {}
        for k, fl in FEATURES.items():
            for feature in self._features:
                if feature in fl:
                    feature_list = features_mapped.get(k, None)
                    if feature_list is None:
                        features_mapped[k] = [feature]
                    else:
                        feature_list.append(feature)
        result_str: List[str] = [f"{k}: {fl}" for k, fl in features_mapped.items()]
        return "\n".join(result_str)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, ProblemKind):
            if (
                self._version is None
                or oth._version is None
                or self._version == oth._version
            ):
                if self.version != oth.version:
                    return False
                valid_features = get_valid_features(self.version)
                self_feat = self._features.intersection(valid_features)
                oth_feat = oth._features.intersection(valid_features)
                return self_feat == oth_feat
        return False

    def __hash__(self) -> int:
        return sum(map(hash, self._features))

    def __le__(self, oth: object):
        if not isinstance(oth, ProblemKind):
            raise ValueError(f"Unable to compare a ProblemKind with a {type(oth)}")
        self_feat, oth_feat, version = equalize_versions(
            self._features, oth._features, self.version, oth.version
        )
        valid_version_features = get_valid_features(version)
        self_feat.intersection_update(valid_version_features)
        oth_feat.intersection_update(valid_version_features)
        return self_feat.issubset(oth_feat)

    def clone(self) -> "ProblemKind":
        return ProblemKind(self._features, self._version)

    @property
    def features(self) -> Set[str]:
        """Returns the features contained by this `ProblemKind`."""
        return self._features

    @property
    def version(self) -> int:
        """
        Returns the version of this `ProblemKind`. If it was not specified, returns the
        highest version represented by the features.
        """
        if self._version is not None:
            return self._version
        max_version = 1
        for f in self._features:
            added_feature_version, _ = FEATURES_VERSIONS.get(f, (1, None))
            max_version = max(max_version, added_feature_version)
        assert (
            max_version <= LATEST_PROBLEM_KIND_VERSION
        ), "Calculated version is > that the LATEST declared version"
        return max_version

    def get_version(self) -> Optional[int]:
        warn(
            "This method is deprecated; Use property version instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.version

    def union(self, oth: "ProblemKind") -> "ProblemKind":
        """
        Returns a new `ProblemKind` that is the union of this `ProblemKind` and
        the `ProblemKind` given as parameter.

        :param oth: the `ProblemKind` that must be united to this `ProblemKind`.
        :return: a new `ProblemKind` that is the union of this `ProblemKind` and `oth`
        """
        self_feat, oth_feat, version = equalize_versions(
            self._features, oth._features, self.version, oth.version
        )
        return ProblemKind(self_feat.union(oth_feat), version=version)

    def intersection(self, oth: "ProblemKind") -> "ProblemKind":
        """
        Returns a new `ProblemKind` that is the intersection of this `ProblemKind` and
        the `ProblemKind` given as parameter.

        :param oth: the `ProblemKind` that must be intersected with this `ProblemKind`.
        :return: a new `ProblemKind` that is the intersection between this `ProblemKind` and `oth`
        """
        self_feat, oth_feat, version = equalize_versions(
            self._features, oth._features, self.version, oth.version
        )
        return ProblemKind(self_feat.intersection(oth_feat), version=version)


basic_classical_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
basic_classical_kind.set_problem_class("ACTION_BASED")
basic_classical_kind.set_typing("FLAT_TYPING")

hierarchical_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
hierarchical_kind.set_typing("HIERARCHICAL_TYPING")

classical_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
classical_kind.set_problem_class("ACTION_BASED")
classical_kind.set_typing("FLAT_TYPING")
classical_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
classical_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
classical_kind.set_conditions_kind("EQUALITIES")

full_classical_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
full_classical_kind.set_problem_class("ACTION_BASED")
full_classical_kind.set_typing("FLAT_TYPING")
full_classical_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
full_classical_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
full_classical_kind.set_conditions_kind("EQUALITIES")
full_classical_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
full_classical_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
full_classical_kind.set_effects_kind("CONDITIONAL_EFFECTS")

object_fluent_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
object_fluent_kind.set_fluents_type("OBJECT_FLUENTS")

simple_numeric_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
simple_numeric_kind.set_problem_class("ACTION_BASED")
simple_numeric_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
simple_numeric_kind.set_typing("FLAT_TYPING")
simple_numeric_kind.set_fluents_type("INT_FLUENTS")
simple_numeric_kind.set_fluents_type("REAL_FLUENTS")
simple_numeric_kind.set_effects_kind("INCREASE_EFFECTS")
simple_numeric_kind.set_effects_kind("DECREASE_EFFECTS")

general_numeric_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
general_numeric_kind.set_problem_class("ACTION_BASED")
general_numeric_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
general_numeric_kind.set_typing("FLAT_TYPING")
general_numeric_kind.set_fluents_type("INT_FLUENTS")
general_numeric_kind.set_fluents_type("REAL_FLUENTS")

bounded_types_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
bounded_types_kind.set_numbers("BOUNDED_TYPES")

basic_temporal_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
basic_temporal_kind.set_problem_class("ACTION_BASED")
basic_temporal_kind.set_typing("FLAT_TYPING")
basic_temporal_kind.set_time("CONTINUOUS_TIME")

process_temporal_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
process_temporal_kind.set_problem_class("ACTION_BASED")
process_temporal_kind.set_time("PROCESSES")
process_temporal_kind.set_time("CONTINUOUS_TIME")


temporal_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
temporal_kind.set_problem_class("ACTION_BASED")
temporal_kind.set_typing("FLAT_TYPING")
temporal_kind.set_time("CONTINUOUS_TIME")
temporal_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
temporal_kind.set_time("TIMED_EFFECTS")
temporal_kind.set_time("TIMED_GOALS")
temporal_kind.set_time("DURATION_INEQUALITIES")
temporal_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")

int_duration_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
int_duration_kind.set_expression_duration("INT_TYPE_DURATIONS")

quality_metrics_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
quality_metrics_kind.set_quality_metrics("PLAN_LENGTH")
quality_metrics_kind.set_quality_metrics("ACTIONS_COST")
quality_metrics_kind.set_quality_metrics("FINAL_VALUE")

oversubscription_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
oversubscription_kind.set_quality_metrics("OVERSUBSCRIPTION")

actions_cost_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
actions_cost_kind.set_quality_metrics("ACTIONS_COST")

multi_agent_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
multi_agent_kind.set_problem_class("ACTION_BASED_MULTI_AGENT")
multi_agent_kind.set_typing("FLAT_TYPING")
multi_agent_kind.set_typing("HIERARCHICAL_TYPING")
multi_agent_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
multi_agent_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
multi_agent_kind.set_conditions_kind("EQUALITIES")
multi_agent_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
multi_agent_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
multi_agent_kind.set_effects_kind("CONDITIONAL_EFFECTS")
multi_agent_kind.set_fluents_type("INT_FLUENTS")
multi_agent_kind.set_fluents_type("REAL_FLUENTS")
multi_agent_kind.set_fluents_type("OBJECT_FLUENTS")
multi_agent_kind.set_multi_agent("AGENT_SPECIFIC_PRIVATE_GOAL")
multi_agent_kind.set_multi_agent("AGENT_SPECIFIC_PUBLIC_GOAL")
