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


class Engine:
    """Represents the engine interface."""

    @property
    def name(self) -> str:
        raise NotImplementedError

    @staticmethod
    def is_oneshot_planner() -> bool:
        return False

    @staticmethod
    def is_plan_validator() -> bool:
        return False

    @staticmethod
    def is_compiler() -> bool:
        return False

    @staticmethod
    def supported_kind() -> ProblemKind:
        raise NotImplementedError

    @staticmethod
    def supports(problem_kind: 'ProblemKind') -> bool:
        raise NotImplementedError

    @staticmethod
    def get_credits(**kwargs) -> Optional[Credits]:
        '''
        This method returns the credits for this engine, that will be printed when the engine is used.
        If this function returns None, it means no credits to print.

        The **kwargs parameters are the same used in this engine to communicate
         the specific options for this Engine instance.
        '''
        return None

    def destroy(self):
        pass

    def __enter__(self):
        """Manages entering a Context (i.e., with statement)"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Manages exiting from Context (i.e., with statement)"""
        self.destroy()
