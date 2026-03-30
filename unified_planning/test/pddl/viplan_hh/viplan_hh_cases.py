from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Dict, Mapping, Tuple

from unified_planning.io import UPPDDLReader
from unified_planning.model import UPState

AtomSpec = Tuple[str, ...]
StateSpec = Dict[AtomSpec, bool]
StateChoice = Tuple[Mapping[AtomSpec, bool], ...]

_VIPLAN_HH_DIR = Path(__file__).parent
VIPLAN_HH_DOMAIN_FILE = _VIPLAN_HH_DIR / "domain.pddl"


@dataclass(frozen=True)
class ViPlanHHCase:
    """Declarative description of a ViPlan-HH test case.

    Each case points to a problem file under the shared ViPlan-HH domain and
    declares:
    - representative_states: a small set of plausible initial states used by
      compile and end-to-end smoke tests.
    - base_state: facts shared by every generated uncertain world.
    - uncertainty_dimensions: mutually-exclusive choices whose Cartesian
      product defines the full uncertain state space for stress tests.
    - true_state: the ground-truth initial state that must always be included
      in the stress-test subsets.
    """

    name: str
    problem_file: str
    representative_states: Tuple[Mapping[AtomSpec, bool], ...]
    true_state: Mapping[AtomSpec, bool]
    base_state: Mapping[AtomSpec, bool] = field(default_factory=dict)
    uncertainty_dimensions: Tuple[StateChoice, ...] = field(default_factory=tuple)

    @property
    def problem_path(self) -> Path:
        return _VIPLAN_HH_DIR / self.problem_file

    def possible_state_specs(self) -> Tuple[StateSpec, ...]:
        """Return the full set of possible states generated from the case data."""
        if not self.uncertainty_dimensions:
            return tuple(dict(spec) for spec in self.representative_states)

        states = []
        for choices in product(*self.uncertainty_dimensions):
            merged = dict(self.base_state)
            for choice in choices:
                merged.update(choice)
            states.append(merged)
        return tuple(states)


def parse_problem(case: ViPlanHHCase):
    reader = UPPDDLReader()
    return reader.parse_problem(str(VIPLAN_HH_DOMAIN_FILE), str(case.problem_path))


def state_spec_to_upstate(problem, state_spec: Mapping[AtomSpec, bool]) -> UPState:
    """Build a UPState from an atom-based specification.

    Atom specs are tuples like ("inside", "bowl_1", "cabinet_1") so callers
    do not need string parsing or per-problem helper functions.
    """
    em = problem.environment.expression_manager
    values = {}
    for atom, value in state_spec.items():
        fluent_name = atom[0]
        object_names = atom[1:]
        fluent = problem.fluent(fluent_name)
        objects = [problem.object(name) for name in object_names]
        values[fluent(*objects)] = em.TRUE() if value else em.FALSE()
    return UPState(values, problem)


def state_specs_to_upstates(problem, state_specs) -> Tuple[UPState, ...]:
    return tuple(state_spec_to_upstate(problem, spec) for spec in state_specs)


_CLEANING_OUT_DRAWERS_BASE_STATE = {
    ("inside", "bowl_1", "cabinet_1"): False,
    ("ontop", "bowl_1", "sink_1"): False,
    ("reachable", "bowl_1"): False,
    ("reachable", "cabinet_1"): False,
    ("reachable", "sink_1"): True,
    ("holding", "bowl_1"): False,
    ("nextto", "bowl_1", "bowl_1"): True,
    ("nextto", "bowl_1", "sink_1"): False,
}

CLEANING_OUT_DRAWERS = ViPlanHHCase(
    name="cleaning_out_drawers",
    problem_file="cleaning_out_drawers.pddl",
    representative_states=(
        {("inside", "bowl_1", "cabinet_1"): True},
        {
            ("reachable", "bowl_1"): True,
            ("ontop", "bowl_1", "sink_1"): True,
        },
    ),
    true_state={
        **_CLEANING_OUT_DRAWERS_BASE_STATE,
        ("inside", "bowl_1", "cabinet_1"): True,
        ("open", "cabinet_1"): False,
        ("ontop", "bowl_1", "bowl_1"): False,
        ("ontop", "bowl_1", "cabinet_1"): False,
        ("nextto", "bowl_1", "cabinet_1"): False,
    },
    base_state=_CLEANING_OUT_DRAWERS_BASE_STATE,
    uncertainty_dimensions=(
        (
            {("open", "cabinet_1"): False},
            {("open", "cabinet_1"): True},
        ),
        (
            {("ontop", "bowl_1", "bowl_1"): False},
            {("ontop", "bowl_1", "bowl_1"): True},
        ),
        (
            {("ontop", "bowl_1", "cabinet_1"): False},
            {("ontop", "bowl_1", "cabinet_1"): True},
        ),
        (
            {("nextto", "bowl_1", "cabinet_1"): False},
            {("nextto", "bowl_1", "cabinet_1"): True},
        ),
    ),
)

_SORTING_BOOKS_BASE_STATE = {
    ("holding", "hardback_1"): False,
    ("ontop", "hardback_1", "shelf_1"): False,
}

SORTING_BOOKS_SIMPLE = ViPlanHHCase(
    name="sorting_books",
    problem_file="sorting_books.pddl",
    representative_states=(
        # True initial state: only ontop(hardback_1, table_1)=True (PDDL default);
        # all relevant atoms are False.
        {},
        # Alternative: agent starts near shelf
        {("reachable", "shelf_1"): True},
    ),
    true_state={
        **_SORTING_BOOKS_BASE_STATE,
        ("reachable", "hardback_1"): False,
        ("reachable", "table_1"): False,
        ("reachable", "shelf_1"): False,
    },
    base_state=_SORTING_BOOKS_BASE_STATE,
    uncertainty_dimensions=(
        (
            {("reachable", "hardback_1"): False},
            {("reachable", "hardback_1"): True},
        ),
        (
            {("reachable", "table_1"): False},
            {("reachable", "table_1"): True},
        ),
        (
            {("reachable", "shelf_1"): False},
            {("reachable", "shelf_1"): True},
        ),
    ),
)

_PUTTING_AWAY_TOYS_BASE_STATE = {
    ("holding", "plaything_1"): False,
    ("holding", "plaything_2"): False,
    ("holding", "plaything_3"): False,
    ("holding", "plaything_4"): False,
    ("inside", "plaything_1", "carton_1"): False,
    ("inside", "plaything_2", "carton_1"): False,
    ("inside", "plaything_3", "carton_1"): False,
    ("inside", "plaything_4", "carton_1"): False,
    ("reachable", "table_1"): False,
}

PUTTING_AWAY_TOYS = ViPlanHHCase(
    name="putting_away_toys",
    problem_file="putting_away_toys.pddl",
    representative_states=(
        # True initial state: open(carton_1)=True from PDDL, all other relevant atoms False.
        {},
        # Alternative: agent starts near plaything_4 (a goal object)
        {("reachable", "plaything_4"): True},
        # Alternative: agent starts near the carton
        {("reachable", "carton_1"): True},
    ),
    true_state={
        **_PUTTING_AWAY_TOYS_BASE_STATE,
        ("reachable", "plaything_1"): False,
        ("reachable", "plaything_2"): False,
        ("reachable", "plaything_3"): False,
        ("reachable", "plaything_4"): False,
        ("reachable", "carton_1"): False,
        ("open", "carton_1"): True,
    },
    base_state=_PUTTING_AWAY_TOYS_BASE_STATE,
    uncertainty_dimensions=(
        (
            {("reachable", "plaything_1"): False},
            {("reachable", "plaything_1"): True},
        ),
        (
            {("reachable", "plaything_2"): False},
            {("reachable", "plaything_2"): True},
        ),
        (
            {("reachable", "plaything_3"): False},
            {("reachable", "plaything_3"): True},
        ),
        (
            {("reachable", "plaything_4"): False},
            {("reachable", "plaything_4"): True},
        ),
        (
            {("reachable", "carton_1"): False},
            {("reachable", "carton_1"): True},
        ),
        (
            {("open", "carton_1"): False},
            {("open", "carton_1"): True},
        ),
    ),
)

_ORGANIZING_FILE_CABINET_BASE_STATE = {
    # Goal atoms: not achieved at start
    ("ontop", "marker_1", "table_1"): False,
    ("inside", "document_1", "cabinet_1"): False,
    ("inside", "document_3", "cabinet_1"): False,
    # Agent is always empty-handed
    ("holding", "marker_1"): False,
    ("holding", "document_1"): False,
    ("holding", "document_2"): False,
    ("holding", "document_3"): False,
    ("holding", "document_4"): False,
    ("holding", "folder_1"): False,
    ("holding", "folder_2"): False,
    # Other non-goal atoms: all False at start
    ("inside", "marker_1", "cabinet_1"): False,
    ("inside", "document_4", "cabinet_1"): False,
    ("reachable", "document_4"): False,
    ("reachable", "folder_1"): False,
    ("reachable", "folder_2"): False,
}

ORGANIZING_FILE_CABINET = ViPlanHHCase(
    name="organizing_file_cabinet",
    problem_file="organizing_file_cabinet.pddl",
    representative_states=(
        # True initial state: agent not near any object (empty init)
        {},
        # Alternative: agent starts near the cabinet (must open + place docs)
        {("reachable", "cabinet_1"): True},
        # Alternative: agent starts near the marker
        {("reachable", "marker_1"): True},
    ),
    true_state={
        **_ORGANIZING_FILE_CABINET_BASE_STATE,
        ("open", "cabinet_1"): False,
        ("reachable", "marker_1"): False,
        ("reachable", "table_1"): False,
        ("reachable", "cabinet_1"): False,
        ("reachable", "document_1"): False,
        ("reachable", "document_2"): False,
        ("reachable", "document_3"): False,
        # inside uncertainty: none of these are in cabinet at true start
        ("inside", "document_2", "cabinet_1"): False,
        ("inside", "folder_1", "cabinet_1"): False,
        ("inside", "folder_2", "cabinet_1"): False,
    },
    base_state=_ORGANIZING_FILE_CABINET_BASE_STATE,
    uncertainty_dimensions=(
        ({("open", "cabinet_1"): False}, {("open", "cabinet_1"): True}),
        ({("reachable", "marker_1"): False}, {("reachable", "marker_1"): True}),
        ({("reachable", "table_1"): False}, {("reachable", "table_1"): True}),
        ({("reachable", "cabinet_1"): False}, {("reachable", "cabinet_1"): True}),
        ({("reachable", "document_1"): False}, {("reachable", "document_1"): True}),
        ({("reachable", "document_2"): False}, {("reachable", "document_2"): True}),
        ({("reachable", "document_3"): False}, {("reachable", "document_3"): True}),
        (
            {("inside", "document_2", "cabinet_1"): False},
            {("inside", "document_2", "cabinet_1"): True},
        ),
        (
            {("inside", "folder_1", "cabinet_1"): False},
            {("inside", "folder_1", "cabinet_1"): True},
        ),
        (
            {("inside", "folder_2", "cabinet_1"): False},
            {("inside", "folder_2", "cabinet_1"): True},
        ),
    ),
)

VIPLAN_HH_CASES = {
    CLEANING_OUT_DRAWERS.name: CLEANING_OUT_DRAWERS,
    SORTING_BOOKS_SIMPLE.name: SORTING_BOOKS_SIMPLE,
    PUTTING_AWAY_TOYS.name: PUTTING_AWAY_TOYS,
    ORGANIZING_FILE_CABINET.name: ORGANIZING_FILE_CABINET,
}
