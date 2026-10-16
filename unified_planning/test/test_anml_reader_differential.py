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

"""Checks the lark ANML reader against the legacy pyparsing one.

Temporary: deleted together with `_legacy_anml_grammar.py` and `_legacy_anml_reader.py`.
"""

import glob
import os
import re
from typing import Iterator, Optional, Tuple

from unified_planning.environment import Environment
from unified_planning.io import ANMLReader, ANMLWriter
from unified_planning.io._legacy_anml_reader import ANMLReader as LegacyReader
from unified_planning.test import get_test_cases, unittest_TestCase

REPO = os.path.join(os.path.dirname(__file__), "..", "..")
# Reviewed: legacy blames the first line of the block missing its "}", lark the token where it fails.
DIFFERENT_ERROR_LINE = ("anml/match.anml#9",)


def _repo_files() -> Iterator[Tuple[str, str]]:
    for path in sorted(glob.glob(f"{REPO}/**/*.anml", recursive=True)):
        if ".venv" not in path:
            with open(path) as f:
                yield path, f.read()


def _written_problems() -> Iterator[Tuple[str, str]]:
    cases = dict(get_test_cases())
    try:
        from up_test_cases.report import get_test_cases_from_packages

        cases.update(get_test_cases_from_packages(["up_test_cases.builtin"]))
    except ImportError:
        pass
    for name, tc in cases.items():
        try:
            yield name, ANMLWriter(tc.problem).get_problem()
        except Exception:
            continue  # the writer does not support this problem kind


def _mutations(text: str) -> Iterator[str]:
    """Deterministic broken variants of a valid file."""
    for token in (";", ")", "}", "]"):
        positions = [m.start() for m in re.finditer(re.escape(token), text)]
        for pos in positions[:: max(1, len(positions) // 3)]:
            yield text[:pos] + text[pos + 1 :]
    yield text.replace("action ", "action (", 1)
    yield text.replace(":=", "=:", 1)


def _error_line(e: Exception) -> Optional[int]:
    if hasattr(e, "lineno") and isinstance(e.lineno, int):
        return e.lineno
    m = re.search(r"line:? (\d+)", str(e))
    return int(m.group(1)) if m else None


def _parse(reader_cls, env: Environment, text: str):
    try:
        return reader_cls(env).parse_problem_string(text), None
    except Exception as e:
        return None, e


class TestANMLReaderDifferential(unittest_TestCase):
    def _compare(self, name: str, text: str):
        env = Environment()  # shared, so that Problem.__eq__ can compare the results
        old, old_err = _parse(LegacyReader, env, text)
        new, new_err = _parse(ANMLReader, env, text)
        with self.subTest(name=name):
            if old_err is None:
                self.assertIsNone(new_err, f"{name}: new reader raised {new_err!r}")
                self.assertEqual(old, new)
            else:
                self.assertIsNotNone(new_err, f"{name}: legacy raised {old_err!r}")
                if name.endswith(DIFFERENT_ERROR_LINE):
                    return
                self.assertEqual(
                    _error_line(old_err),
                    _error_line(new_err),
                    f"{name}: legacy {old_err!r} vs new {new_err!r}",
                )

    def test_repo_files(self):
        for name, text in _repo_files():
            self._compare(name, text)

    def test_written_problems(self):
        for name, text in _written_problems():
            self._compare(name, text)

    def test_malformed_files(self):
        for name, text in _repo_files():
            for i, broken in enumerate(_mutations(text)):
                self._compare(f"{name}#{i}", broken)
