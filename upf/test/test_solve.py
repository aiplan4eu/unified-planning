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

import upf
from upf.test import TestCase, main
from upf.test import generate_simple_problem


class TestSolve(TestCase):
    def setUp(self):
        self.size = 14
        self.problem = generate_simple_problem(self.size)

    def test_cppplanner(self):
        with upf.Planner('upf_cppplanner') as p:
            plan = p.solve(self.problem)
            self.assertEqual(len(plan), self.size*3-1)

    def test_pyplanner(self):
        with upf.Planner('upf_pyplanner') as p:
            plan = p.solve(self.problem)
            self.assertEqual(len(plan), self.size*3-1)


if __name__ == "__main__":
    main()
