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
#
"""This module defines the engine interface."""

from unified_planning.model import ProblemKind
from unified_planning.engines.credits import Credits
from typing import Optional


class EngineMeta(type):
    def __new__(cls, name, bases, dct):
        obj = type.__new__(cls, name, bases, dct)
        for om in ["oneshot_planner", "plan_validator", "compiler", "simulator"]:
            if (
                not hasattr(obj, "is_" + om)
                and name != "Engine"
                and name != "MetaEngine"
            ):
                setattr(obj, "is_" + om, lambda: False)
        return obj


class Engine(metaclass=EngineMeta):
    """Represents the engine interface."""

    def __init__(self, **kwargs):
        self._skip_checks = False
        self._error_on_failed_checks = True

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def skip_checks(self) -> bool:
        """
        Flag defining if this engine skips the checks on the problem's problem_kind before
        executing methods like solve, compile or validate.

        By default this is set to False.
        """
        return self._skip_checks

    @skip_checks.setter
    def skip_checks(self, new_value: bool):
        """
        Sets the flag defining if this engine skips the checks on the problem's problem_kind before
        executing methods like solve, compile or validate.

        By default this is set to False.

        Note that this flag deactivates some safety measures, so when deactivated the given errors might
        not be totally clear.
        """
        self._skip_checks = new_value

    @property
    def error_on_failed_checks(self) -> bool:
        """
        When a check on the problem's problem_kind fails, this flag determines if this fail returns
        just a warning (when False), without failing the execution, or if the fail must return an
        error and stop the execution (when True).

        The default value is True.

        Note that if the property Engine.skip_checks is set to True, the value of this flag becomes
        irrelevant.

        Note also that this flag deactivates some safety measures, so when deactivated the given errors might
        not be totally clear.
        """
        return self._error_on_failed_checks

    @error_on_failed_checks.setter
    def error_on_failed_checks(self, new_value: bool):
        """
        Sets the flag deciding if a fail on the problem's kind checks should return in an error or
        just in a warning.
        """
        self._error_on_failed_checks = new_value

    @staticmethod
    def supported_kind() -> ProblemKind:
        raise NotImplementedError

    @staticmethod
    def supports(problem_kind: "ProblemKind") -> bool:
        raise NotImplementedError

    @staticmethod
    def get_credits(**kwargs) -> Optional[Credits]:
        """
        This method returns the credits for this engine, that will be printed when the engine is used.
        If this function returns None, it means no credits to print.

        The **kwargs parameters are the same used in this engine to communicate
         the specific options for this Engine instance.
        """
        return None

    def destroy(self):
        pass

    def __enter__(self):
        """Manages entering a Context (i.e., with statement)"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Manages exiting from Context (i.e., with statement)"""
        self.destroy()
