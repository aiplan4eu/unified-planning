#!/usr/bin/env python3
"""Times the PDDL and ANML readers on generated large problems and on small repo files."""

import os
import sys
import time
import warnings

from unified_planning.io import ANMLReader, PDDLReader
from unified_planning.io.up_pddl_reader import UPPDDLReader

TEST_DIR = os.path.join(os.path.dirname(__file__), "..", "unified_planning", "test")
DEPOT_DOMAIN = os.path.join(TEST_DIR, "pddl", "depot", "domain.pddl")
DEPOT_PROBLEM = os.path.join(TEST_DIR, "pddl", "depot", "problem.pddl")
HYDRONE = os.path.join(TEST_DIR, "anml", "hydrone.anml")


def depot_problem(n: int) -> str:
    objs = " ".join(f"o{i}" for i in range(n))
    init = " ".join(
        f"(at o{i} o{(i * 7) % n}) (clear o{i}) (crate o{i})" for i in range(n)
    )
    goal = " ".join(f"(on o{i} o{(i + 1) % n})" for i in range(n // 2))
    return f"(define (problem p) (:domain depot) (:objects {objs}) (:init {init}) (:goal (and {goal})))"


def anml_problem(n: int) -> str:
    src = (
        "type Loc;\nfluent boolean at(Loc l);\nfluent integer cnt(Loc l);\n"
        "action go(Loc a, Loc b) { [start] at(a) == true; [start] at(a) := false;"
        " [end] at(b) := true; [end] cnt(b) := cnt(b) + 1; };\n"
    )
    src += "".join(f"instance Loc l{i};\n" for i in range(n))
    src += "".join(
        f"[start] at(l{i}) := {'true' if i % 2 else 'false'};\n[start] cnt(l{i}) := {i};\n"
        for i in range(n)
    )
    src += "".join(f"[end] at(l{i}) == true;\n" for i in range(0, n, 3))
    return src


def timed(label: str, fn, repeat: int = 1) -> None:
    fn()  # warm-up, so lazily built parsers are not counted
    start = time.perf_counter()
    for _ in range(repeat):
        fn()
    print(f"{label:<45} {(time.perf_counter() - start) / repeat * 1000:8.1f} ms")


def main(n: int) -> None:
    warnings.simplefilter("ignore")
    with open(DEPOT_DOMAIN) as f:
        domain = f.read()
    problem = depot_problem(n)
    anml = anml_problem(n // 2)
    timed(
        f"UPPDDLReader depot, {n} objects",
        lambda: UPPDDLReader().parse_problem_string(domain, problem),
    )
    timed(
        f"ANMLReader, {n // 2} instances",
        lambda: ANMLReader().parse_problem_string(anml),
    )
    timed(
        "PDDLReader small depot",
        lambda: PDDLReader().parse_problem(DEPOT_DOMAIN, DEPOT_PROBLEM),
        repeat=10,
    )
    timed("ANMLReader hydrone.anml", lambda: ANMLReader().parse_problem(HYDRONE), 10)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2000)
