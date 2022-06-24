# Copyright 2022 AIPlan4EU project
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

import os
import inspect
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


class TestFactory(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        home = os.path.expanduser('~')
        self.fname = os.path.join(home, '.up.ini')
        if os.path.isfile(self.fname):
            os.rename(self.fname, f'{self.fname}.temp')

    def tearDown(self):
        TestCase.tearDown(self)
        if os.path.isfile(self.fname):
            os.remove(self.fname)
        if os.path.isfile(f'{self.fname}.temp'):
            os.rename(f'{self.fname}.temp', self.fname)

    def test_config_file(self):
        self.assertTrue('pyperplan' in get_env().factory.preference_list)
        with open(self.fname, 'w') as conf:
            conf.write('[global]\n')
            conf.write('engine_preference_list: tamer\n')
        env = unified_planning.environment.Environment()
        self.assertTrue('pyperplan' not in env.factory.preference_list)
        self.assertEqual(env.factory.preference_list, ['tamer'])
