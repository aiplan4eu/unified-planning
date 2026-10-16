# Copyright 2026 AIPlan4EU project
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

"""Checks the s-expression UPPDDLReader against the legacy pyparsing one.

Temporary: deleted together with `_legacy_up_pddl_reader.py`.
"""

import glob
import os
import re
from typing import Iterator, Optional, Tuple

from unified_planning.environment import Environment
from unified_planning.io import PDDLWriter
from unified_planning.io._legacy_up_pddl_reader import UPPDDLReader as LegacyReader
from unified_planning.io.up_pddl_reader import UPPDDLReader
from unified_planning.test import get_test_cases, unittest_TestCase

REPO = os.path.join(os.path.dirname(__file__), "..", "..")
# Valid files the legacy grammar rejected only because of the section order.
SECTION_ORDER_ONLY = ("processes/car_linear/",)


def _repo_files() -> Iterator[Tuple[str, str, Optional[str]]]:
    for d in sorted(glob.glob(f"{REPO}/**/", recursive=True)):
        files = sorted(glob.glob(os.path.join(d, "*.pddl")))
        domains = [f for f in files if "domain" in os.path.basename(f)]
        if len(domains) != 1:
            continue
        with open(domains[0]) as f:
            domain = f.read()
        yield domains[0], domain, None
        for p in files:
            if p != domains[0]:
                with open(p) as f:
                    yield p, domain, f.read()


def _written_problems() -> Iterator[Tuple[str, str, Optional[str]]]:
    cases = dict(get_test_cases())
    try:
        from up_test_cases.report import get_test_cases_from_packages

        cases.update(get_test_cases_from_packages(["up_test_cases.builtin"]))
    except ImportError:
        pass
    for name, tc in cases.items():
        try:
            w = PDDLWriter(tc.problem)
            yield name, w.get_domain(), w.get_problem()
        except Exception:
            continue  # the writer does not support this problem kind


def _mutations(domain: str) -> Iterator[str]:
    """Deterministic broken variants of a valid file."""
    closing = [m.start() for m in re.finditer(r"\)", domain)]
    for pos in closing[:: max(1, len(closing) // 4)]:
        yield domain[:pos] + domain[pos + 1 :]
    yield domain.replace("(:action", "(:action (", 1)
    yield domain.replace(":parameters", ":parameterz", 1)


def _error_line(e: Exception) -> Optional[int]:
    if hasattr(e, "lineno") and isinstance(e.lineno, int):
        return e.lineno
    m = re.search(r"line:? (\d+)", str(e))
    return int(m.group(1)) if m else None


def _parse(reader_cls, env: Environment, domain: str, problem: Optional[str]):
    try:
        return reader_cls(env).parse_problem_string(domain, problem), None
    except Exception as e:
        return None, e


class TestPDDLReaderDifferential(unittest_TestCase):
    def _compare(self, name: str, domain: str, problem: Optional[str]):
        env = Environment()  # shared, so that Problem.__eq__ can compare the results
        old, old_err = _parse(LegacyReader, env, domain, problem)
        new, new_err = _parse(UPPDDLReader, env, domain, problem)
        with self.subTest(name=name):
            if any(k in name for k in SECTION_ORDER_ONLY):
                self.assertIsNone(new_err, f"{name}: new reader raised {new_err!r}")
            elif old_err is None:
                self.assertIsNone(new_err, f"{name}: new reader raised {new_err!r}")
                self.assertEqual(old, new)
            else:
                self.assertIsNotNone(new_err, f"{name}: legacy raised {old_err!r}")
                self.assertEqual(
                    _error_line(old_err),
                    _error_line(new_err),
                    f"{name}: legacy {old_err!r} vs new {new_err!r}",
                )

    def test_repo_files(self):
        for name, domain, problem in _repo_files():
            self._compare(name, domain, problem)

    def test_written_problems(self):
        for name, domain, problem in _written_problems():
            self._compare(name, domain, problem)

    def test_malformed_files(self):
        for name, domain, problem in _repo_files():
            if problem is not None or any(k in name for k in SECTION_ORDER_ONLY):
                continue
            for i, broken in enumerate(_mutations(domain)):
                self._compare(f"{name}#{i}", broken, None)
