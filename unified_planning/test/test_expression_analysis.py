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
from typing import Callable

import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


class TestExprAnalysis(TestCase):
    def test_any(self):
        a = FluentExp(Fluent("a"))
        b = FluentExp(Fluent("b"))
        c = FluentExp(Fluent("c"))
        e1 = Not(Implies(a, And(b, c)))  # !(a => (b && c))

        def check_any(e: FNode, pred: Callable[[FNode], bool]):
            checker = unified_planning.model.walkers.AnyChecker(pred)
            return checker.any(e)

        print(e1)
        assert check_any(e1, lambda e: e.is_fluent_exp())
        assert check_any(e1, lambda e: e.is_and())
        assert check_any(e1, lambda e: e.is_not())

        assert not check_any(e1, lambda e: e.is_or())
        assert not check_any(e1, lambda e: e.is_times())
