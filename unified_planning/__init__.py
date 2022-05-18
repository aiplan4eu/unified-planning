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


VERSION = (0, 3, 0)
__version__ = ".".join(str(x) for x in VERSION)

# Try to provide human-readable version of latest commit for dev versions
# E.g. v0.5.1-4-g49a49f2-wip
#      * 4 commits after tag v0.5.1
#      * Latest commit "49a49f2"
#      * -wip: Working tree is dirty (non committed stuff)
# See: https://git-scm.com/docs/git-describe
try:
    git_version = subprocess.check_output(["git", "describe", "--tags",
                                            "--dirty=-wip"],
                                            stderr=subprocess.STDOUT)
    output = git_version.strip().decode('ascii')
    data = output.split("-")
    tag = data[0]
    match = re.match(r'^v(\d+)\.(\d)+\.(\d)$', tag)
    if match is not None:
        MAJOR, MINOR, REL = tuple(int(x) for x in match.groups())

    try:
        COMMITS = int(data[1])
    except ValueError:
        COMMITS = 0

    if data[-1] == 'wip':
        if COMMITS == 0:
            VERSION = (MAJOR, MINOR, REL, 'post', 1) #type: ignore
            __version__ = f'{MAJOR}.{MINOR}.{REL}.post1'
        else:
            VERSION = (MAJOR, MINOR, REL, COMMITS, 'post', 1) #type: ignore
            __version__ = f'{MAJOR}.{MINOR}.{REL}.{COMMITS}.post1'
    else:
        VERSION = (MAJOR, MINOR, REL, COMMITS, 'dev', 1) #type: ignore
        __version__ = f'{MAJOR}.{MINOR}.{REL}.{COMMITS}.dev1'
except Exception as ex:
    pass
