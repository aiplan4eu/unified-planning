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

import subprocess
import re

from unified_planning.environment import Environment


VERSION = (0, 2, 0)

# Try to provide human-readable version of latest commit for dev versions
# E.g. v0.5.1-4-g49a49f2-wip
#      * 4 commits after tag v0.5.1
#      * Latest commit "49a49f2"
#      * -wip: Working tree is dirty (non committed stuff)
# See: https://git-scm.com/docs/git-describe
try:
    git_version = subprocess.check_output(["git", "describe",
                                            "--dirty=-wip"],
                                            stderr=subprocess.STDOUT)
    output = git_version.strip().decode('ascii')
    data = output.split("-")
    tag = data[0]
    match = re.match(r'^v(\d+)\.(\d)+\.(\d)$', tag)
    if match is not None:
        VERSION = tuple(int(x) for x in match.groups())
    if data[1] == 'wip':
        VERSION = (VERSION[0], VERSION[1], VERSION[2], 'post', 1)
    else:
        commits = int(data[1])
        VERSION = (VERSION[0], VERSION[1], VERSION[2]+commits, 'dev', 1)        
except Exception as ex:
    pass

# PEP440 Format
__version__ = "%d.%d.%d.%s%d" % VERSION if len(VERSION) == 5 else \
              "%d.%d.%d" % VERSION[:3]
