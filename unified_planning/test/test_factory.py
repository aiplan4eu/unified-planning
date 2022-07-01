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
import tempfile
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


class TestFactory(TestCase):
    def test_config_file(self):
        self.assertTrue("pyperplan" in get_env().factory.preference_list)
        with tempfile.TemporaryDirectory() as tempdir:
            config_filename = os.path.join(tempdir, "up.ini")
            with open(config_filename, "w") as config:
                config.write("[global]\n")
                config.write("engine_preference_list: tamer\n")
            env = unified_planning.environment.Environment()
            env.factory.configure_from_file(config_filename)
            self.assertTrue("pyperplan" not in env.factory.preference_list)
            self.assertEqual(env.factory.preference_list, ["tamer"])
