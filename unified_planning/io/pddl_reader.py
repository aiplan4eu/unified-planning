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
#


import re
from typing import Callable, List
import typing
from warnings import warn
import unified_planning as up
from unified_planning.environment import Environment, get_environment
from unified_planning.exceptions import (
    UPUnsupportedProblemTypeError,
)
from unified_planning.interop.from_pddl import (
    check_ai_pddl_requirements,
    convert_problem_from_ai_pddl,
)
from unified_planning.io.up_pddl_reader import UPPDDLReader

from pddl.parser.domain import DomainParser  # type: ignore
from pddl.parser.problem import ProblemParser  # type: ignore


class PDDLReader:
    """
    Uses the `unified_planning.interop.from_pddl.from_ai_pddl` if the requirements are respected, otherwise uses the `UPPDDLReader`
    to parse the `PDDL` domain and the `PDDL` problem; generates the equivalent :class:`~unified_planning.model.Problem`.

    Note: in the error report messages, a tabulation counts as one column; and due to PDDL case-insensitivity, everything in the
    PDDL files will be turned to lower case, so the names of fluents, actions etc. and the error report
    will all be in lower-case.
    """

    def __init__(
        self,
        environment: typing.Optional[Environment] = None,
        force_up_pddl_reader: bool = False,
        force_ai_planning_reader: bool = False,
        deactivate_fallback: bool = False,
        disable_warnings: bool = False,
    ):
        """
        Creates the `PDDLReader` with the specified parameters.

        :param environment: the environment used to create the problems/plans, defaults to None
        :param force_up_pddl_reader: when `True` forces the `parse_problem` methods to use the `UPPDDLReader`, defaults to False
        :param force_ai_planning_reader: when `True` forces `parse_problem` methods to use the `from_ai_pddl` method, defaults to False
        :param deactivate_fallback: when `True` disables the fallback on the `UPPDDLReader` if `from_ai_pddl` fails, defaults to False
        :param disable_warnings: when `True` the warnings when `from_ai_pddl` fails but the requirements are respected are not raised, defaults to False
        """
        self._env = get_environment(environment)
        self._up_pddl_reader = UPPDDLReader(self._env)
        self._force_up_pddl_reader = force_up_pddl_reader
        self._force_ai_planning_reader = force_ai_planning_reader
        self._deactivate_fallback = deactivate_fallback
        self._disable_warnings = disable_warnings

    def parse_problem(
        self, domain_filename: str, problem_filename: typing.Optional[str] = None
    ) -> "up.model.Problem":
        """
        Takes in input a filename containing the `PDDL` domain and optionally a filename
        containing the `PDDL` problem and returns the parsed `Problem`; the Problem
        is parsed using `from_ai_pddl` if all the requirements specified in the domain
        are supported, if this fails or the requirements specified are not supported,
        falls back to the `UPPDDLReader`.

        Note: that if the `problem_filename` is `None`, an incomplete `Problem` will be returned.

        Note: due to PDDL case-insensitivity, everything in the PDDL files will be turned to
        lower case, so the names of fluents, actions etc. and the error report will all be
        in lower-case.

        :param domain_filename: The path to the file containing the `PDDL` domain.
        :param problem_filename: Optionally the path to the file containing the `PDDL` problem.
        :return: The `Problem` parsed from the given pddl domain + problem.
        """
        with open(domain_filename, encoding="utf-8-sig") as domain_file:
            domain_str = domain_file.read()

        problem_str = None
        if problem_filename is not None:
            with open(problem_filename, encoding="utf-8-sig") as problem_file:
                problem_str = problem_file.read()

        return self.parse_problem_string(domain_str, problem_str)

    def parse_problem_string(
        self, domain_str: str, problem_str: typing.Optional[str] = None
    ) -> "up.model.Problem":
        """
        Takes in input a str representing the `PDDL` domain and optionally a str
        representing the `PDDL` problem and returns the parsed `Problem`; the Problem
        is parsed using `from_ai_pddl` if all the requirements specified in the domain
        are supported, if this fails or the requirements specified are not supported,
        falls back to the `UPPDDLReader`.

        Note that if the `problem_str` is `None`, an incomplete `Problem` will be returned.

        Note: due to PDDL case-insensitivity, everything in the PDDL files will be turned to
        lower case, so the names of fluents, actions etc. and the error report will all be
        in lower-case.

        :param domain_filename: The string representing the `PDDL` domain.
        :param problem_filename: Optionally the string representing the `PDDL` problem.
        :return: The `Problem` parsed from the given pddl domain + problem.
        """
        if self._force_up_pddl_reader:
            return self._up_pddl_reader.parse_problem_string(domain_str, problem_str)
        if self._force_ai_planning_reader:
            ai_domain = DomainParser()(domain_str)
            ai_problem = (
                ProblemParser()(problem_str) if problem_str is not None else None
            )
            return convert_problem_from_ai_pddl(ai_domain, ai_problem, self._env)
        requirements = extract_pddl_requirements(domain_str)
        if check_ai_pddl_requirements(requirements):
            ai_pddl_parsing_failed = False
            try:
                ai_domain = DomainParser()(domain_str)
                ai_problem = ProblemParser()(problem_str)
            except Exception as e:
                ai_pddl_parsing_failed = True
                if self._deactivate_fallback:
                    raise e
                if not self._disable_warnings:
                    warn(
                        f"The problem could not be converted using the AI Planning reader due to an issue in the AI PDDL parser: {e}"
                    )
            if not ai_pddl_parsing_failed:
                try:
                    return convert_problem_from_ai_pddl(
                        ai_domain, ai_problem, self._env
                    )
                except UPUnsupportedProblemTypeError as e:
                    if self._deactivate_fallback:
                        raise e
                    if not self._disable_warnings:
                        warn(
                            f"The problem could not be converted using the AI Planning reader due to an issue in the UP converter: {e}"
                        )
        return self._up_pddl_reader.parse_problem_string(domain_str, problem_str)

    def parse_plan(
        self,
        problem: "up.model.Problem",
        plan_filename: str,
        get_item_named: typing.Optional[
            Callable[
                [str],
                "up.io.pddl_writer.WithName",
            ]
        ] = None,
    ) -> "up.plans.Plan":
        """
        Takes a problem, a filename and optionally a map of renaming and returns the plan parsed from the file.

        The format of the file must be:
        ``(action-name param1 param2 ... paramN)`` in each line for SequentialPlans
        ``start-time: (action-name param1 param2 ... paramN) [duration]`` in each line for TimeTriggeredPlans,
        where ``[duration]`` is optional and not specified for InstantaneousActions.

        :param problem: The up.model.problem.Problem instance for which the plan is generated.
        :param plan_filename: The path of the file in which the plan is written.
        :param get_item_named: A function that takes a name and returns the original up.model element instance
            linked to that renaming; if None the problem is used to retrieve the actions and objects in the
            plan from their name.
        :return: The up.plans.Plan corresponding to the parsed plan from the file
        """
        with open(plan_filename, encoding="utf-8-sig") as plan:
            return self.parse_plan_string(problem, plan.read(), get_item_named)

    def parse_plan_string(
        self,
        problem: "up.model.Problem",
        plan_str: str,
        get_item_named: typing.Optional[
            Callable[
                [str],
                "up.io.pddl_writer.WithName",
            ]
        ] = None,
    ) -> "up.plans.Plan":
        """
        Takes a problem, a string and optionally a map of renaming and returns the plan parsed from the string.

        The format of the file must be:
        ``(action-name param1 param2 ... paramN)`` in each line for SequentialPlans
        ``start-time: (action-name param1 param2 ... paramN) [duration]`` in each line for TimeTriggeredPlans,
        where ``[duration]`` is optional and not specified for InstantaneousActions.

        :param problem: The up.model.problem.Problem instance for which the plan is generated.
        :param plan_str: The plan in string.
        :param get_item_named: A function that takes a name and returns the original up.model element instance
            linked to that renaming; if None the problem is used to retrieve the actions and objects in the
            plan from their name.:return: The up.plans.Plan corresponding to the parsed plan from the string
        """
        return self._up_pddl_reader.parse_plan_string(problem, plan_str, get_item_named)


def extract_pddl_requirements(domain_str: str) -> List[str]:
    """
    Extract the requirements from the given domain in a List of requirements strings.
    For example if the requirements are `(:requirements :strips :typing)` returns:
    `[":strips", ":typing"]`

    :param domain_str: the domain str from which the requirements have to be extracted.
    :return: The `List[str]` of requirements extracted from the domain.
    """
    requirements_lines = []
    found_requirements = False

    for line in domain_str.splitlines():
        if ":requirements" in line:
            assert not found_requirements
            found_requirements = True
        if found_requirements:
            requirements_lines.append(line)
            if ")" in line:
                break

    requirements_str = " ".join(requirements_lines)
    match = re.search(r"\(:requirements\s+([^)]+)\)", requirements_str)
    if match:
        requirements = match.group(1).split()
        return requirements
    else:
        return []
