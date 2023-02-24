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
import unified_planning as up
from functools import wraps
from importlib.util import find_spec
from unified_planning.engines import OperationMode
from unified_planning.environment import get_environment
from unified_planning.model import ProblemKind
from unified_planning.test.pddl import enhsp
from typing import Optional
import unified_planning.test.scheduling


skipIf = unittest.skipIf
SkipTest = unittest.SkipTest


class skipIfEngineNotAvailable(object):
    """Skip a test if the given engine is not available."""

    def __init__(self, engine):
        self.engine = engine

    def __call__(self, test_fun):
        msg = "%s not available" % self.engine
        cond = self.engine not in get_environment().factory.engines

        @unittest.skipIf(cond, msg)
        @wraps(test_fun)
        def wrapper(*args, **kwargs):
            return test_fun(*args, **kwargs)

        return wrapper


class skipIfNoOneshotPlannerForProblemKind(object):
    """Skip a test if there are no oneshot planner for the given problem kind."""

    def __init__(
        self,
        kind: ProblemKind,
        optimality_guarantee: Optional[up.engines.OptimalityGuarantee] = None,
    ):
        self.kind = kind
        self.optimality_guarantee = optimality_guarantee

    def __call__(self, test_fun):
        msg = "no oneshot planner available for the given problem kind"
        cond = False
        try:
            get_environment().factory._get_engine_class(
                OperationMode.ONESHOT_PLANNER,
                problem_kind=self.kind,
                optimality_guarantee=self.optimality_guarantee,
            )
        except:
            cond = True

        @unittest.skipIf(cond, msg)
        @wraps(test_fun)
        def wrapper(*args, **kwargs):
            return test_fun(*args, **kwargs)

        return wrapper


class skipIfNoAnytimePlannerForProblemKind(object):
    """Skip a test if there are no anytime planner for the given problem kind."""

    def __init__(
        self,
        kind: ProblemKind,
        anytime_guarantee: Optional[up.engines.AnytimeGuarantee] = None,
    ):
        self.kind = kind
        self.anytime_guarantee = anytime_guarantee

    def __call__(self, test_fun):
        msg = "no anytime planner available for the given problem kind"
        cond = False
        try:
            get_environment().factory._get_engine_class(
                OperationMode.ANYTIME_PLANNER,
                problem_kind=self.kind,
                anytime_guarantee=self.anytime_guarantee,
            )
        except:
            cond = True

        @unittest.skipIf(cond, msg)
        @wraps(test_fun)
        def wrapper(*args, **kwargs):
            return test_fun(*args, **kwargs)

        return wrapper


class skipIfNoPlanValidatorForProblemKind(object):
    """Skip a test if there are no plan validator for the given problem kind."""

    def __init__(self, kind: ProblemKind):
        self.kind = kind

    def __call__(self, test_fun):
        msg = "no plan validator available for the given problem kind"
        cond = False
        try:
            get_environment().factory._get_engine_class(
                OperationMode.PLAN_VALIDATOR, problem_kind=self.kind
            )
        except:
            cond = True

        @unittest.skipIf(cond, msg)
        @wraps(test_fun)
        def wrapper(*args, **kwargs):
            return test_fun(*args, **kwargs)

        return wrapper


class skipIfModuleNotInstalled(object):
    """Skip a test if the given module is not installed."""

    def __init__(self, module_name: str):
        self.module_name = module_name

    def __call__(self, test_fun):
        msg = f"no module named {self.module_name} installed"
        try:
            test = find_spec(self.module_name)
            cond = test is None
        except ModuleNotFoundError:
            cond = True

        @unittest.skipIf(cond, msg)
        @wraps(test_fun)
        def wrapper(*args, **kwargs):
            return test_fun(*args, **kwargs)

        return wrapper


TestCase = unittest.TestCase
main = unittest.main
