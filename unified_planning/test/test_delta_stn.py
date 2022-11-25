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


import os
import sys
from io import StringIO
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import TestCase, skipIfEngineNotAvailable
from unified_planning.model.temporal_state import DeltaSimpleTemporalNetwork

import pyparsing
from pyparsing import (
    ParseResults,
    ParserElement,
    one_of,
    Suppress,
    ZeroOrMore,
    Word,
    alphanums,
)

ParserElement.enable_packrat()

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
PDDL_DOMAINS_PATH = os.path.join(FILE_PATH, "delta_stn_examples")


class TestSTN(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        head = one_of(["Add", "CopyTN", "Check", "DestroyTN", "NewTN"])
        name = Word(alphanums + '"' + "-" + ".")
        self._row: ParserElement = (
            head
            + Suppress("(")
            + name
            + ZeroOrMore(Suppress(",") + name)
            + Suppress(");")
        )

    def test_delta_stn(self):
        files = [
            "matchcellar_5.tn",
            "painter_5_10.tn",
        ]
        for file_str in files:
            filename = os.path.join(PDDL_DOMAINS_PATH, file_str)
            stn_map: Dict[str, DeltaSimpleTemporalNetwork] = {}

            with open(filename, "r", encoding="utf-8") as file:
                while True:
                    line = file.readline()
                    if not line:
                        break
                    pr = self._row.parse_string(line, parse_all=True)
                    method = pr[0]
                    if method == "NewTN":
                        assert len(pr) == 2
                        name = pr[1]
                        stn_map[name] = DeltaSimpleTemporalNetwork()
                    elif method == "CopyTN":
                        assert len(pr) == 3
                        stn_map[pr[2]] = stn_map[pr[1]].copy_stn()
                    elif method == "Add":
                        assert len(pr) == 5
                        stn_map[pr[1]].add(int(pr[2]), int(pr[3]), Fraction(pr[4]))
                    elif method == "Check":
                        assert len(pr) == 2
                        self.assertTrue(stn_map[pr[1]].check_stn())
                    elif method == "DestroyTN":
                        assert len(pr) == 2
                        del stn_map[pr[1]]
                    else:
                        self.assertTrue(False)
