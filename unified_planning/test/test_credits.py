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


import sys
from io import StringIO
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import unittest_TestCase, skipIfEngineNotAvailable


class TestCredits(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)

    @skipIfEngineNotAvailable("tamer")
    def test_robot_locations_visited(self):
        credits = StringIO()
        test_credits = [
            " *** Credits ***",
            "  * In operation mode `OneshotPlanner` at line ",
            "  * Engine name: ",
            "  * Developers:  ",
            "  * Description: ",
            "  *              ",
        ]
        set_credits_stream(credits)
        with OneshotPlanner(name="tamer"):
            for test in test_credits:
                printed_credits = credits.getvalue()
                self.assertIn(test, printed_credits)
        set_credits_stream(sys.stdout)

    def test_long_env_credits(self):
        credits = StringIO()
        credits_keywords = [
            "  * Engine name: ",
            "  * Developers:  ",
            "  * Description: ",
            "  * Contacts:    ",
            "  * Website:     ",
            "  * License:     ",
        ]
        get_environment().factory.print_engines_info(credits, show_credits=True)
        credits_printed = credits.getvalue()
        # test that every keyword occur the same number of time in the printed result
        number_of_credits_printed = credits_printed.count(credits_keywords[0])
        if number_of_credits_printed > 0:  # If at least one credit was printed
            for keyword in credits_keywords:
                self.assertIn(keyword, credits_printed)
                self.assertEqual(
                    credits_printed.count(keyword), number_of_credits_printed
                )
