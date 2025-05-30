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
from unified_planning.test.examples.scheduling import (
    examples,
    jobshop,
    flexible_jobshop,
)


def get_example_problems():
    instances = [
        examples.basic(),
        examples.resource_set(),
        examples.non_numeric(),
        examples.optional(),
        examples.optional_activities_constraints(),
        examples.optional_activities_effects(),
        examples.optional_activities_conditions(),
        examples.TestCase(jobshop.parse(jobshop.FT06, "ft06"), solvable=True),
        examples.TestCase(
            flexible_jobshop.create_scheduling_problem(flexible_jobshop.MT06),
            solvable=True,
        ),
    ]
    return dict((instance.problem.name, instance) for instance in instances)
