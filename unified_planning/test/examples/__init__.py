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


import unified_planning.test.examples.minimals as minimals
import unified_planning.test.examples.realistic as realistic
import unified_planning.test.examples.testing_variants as testing_variants
import unified_planning.test.examples.hierarchical as hierarchical
import unified_planning.test.examples.scheduling as scheduling
import unified_planning.test.examples.processes as processes


def get_example_problems():
    sub_modules = [
        minimals,
        realistic,
        testing_variants,
        hierarchical,
        scheduling,
        processes,
    ]
    return dict(x for m in sub_modules for x in m.get_example_problems().items())
