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

import upf
import tarski.io # type: ignore
from upf.environment import Environment, get_env
from upf.interop.tarski import convert_tarski_problem


class PDDLReader:
    """
    Parse a PDDL problem and generate a upf problem.

    The current implementation relies on tarski and has a bug parsing real
    constants. See issue https://github.com/aig-upf/tarski/issues/114.
    """
    def __init__(self, env: Environment = None):
        self.reader = tarski.io.PDDLReader(raise_on_error=True,
                                           strict_with_requirements=False)
        self.env = get_env(env)

    def parse_problem(self, domain: str, problem: str) -> upf.Problem:
        self.reader.parse_domain(domain)
        problem = self.reader.parse_instance(problem)
        return convert_tarski_problem(self.env, problem)
