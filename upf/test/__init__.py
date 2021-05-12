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

try:
    import unittest2 as unittest
except ImportError:
    import unittest


def generate_simple_problem(size: int) -> upf.Problem:
    actions = [upf.Action('mk_y', set(['x']), set(['y']), set(['x'])),
               upf.Action('reset_x', set([]), set(['x']), set([]))]
    goal = []
    for i in range(size):
        name = f"v{i}"
        goal.append(name)
        actions.append(upf.Action(f'mk_{name}', set(['y']), set([name]), set(['y'])),)
    init = set(['x'])
    return upf.Problem(actions, init, set(goal))


TestCase = unittest.TestCase
main = unittest.main
