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

import unittest
from functools import wraps
from upf.environment import get_env
from upf.factory import DEFAULT_SOLVERS

skipIf = unittest.skipIf
SkipTest = unittest.SkipTest

class skipIfSolverNotAvailable(object):
    """Skip a test if the given solver is not available."""

    def __init__(self, solver):
        self.solver = solver

    def __call__(self, test_fun):
        msg = "%s not available" % self.solver
        cond = self.solver not in get_env().factory.solvers
        @unittest.skipIf(cond, msg)
        @wraps(test_fun)
        def wrapper(*args, **kwargs):
            return test_fun(*args, **kwargs)
        return wrapper


TestCase = unittest.TestCase
main = unittest.main
