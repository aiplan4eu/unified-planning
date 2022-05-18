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


import sys
from io import StringIO
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import TestCase, skipIfSolverNotAvailable


class TestCredits(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    @skipIfSolverNotAvailable('tamer')
    def test_robot_locations_visited(self):
        credits = StringIO()
        test_credits = '''You are using Tamer
Developers: FBK Tamer Development Team
Tamer offers the capability to generate a plan for classical, numerical and temporal problems.
For those kind of problems tamer also offers the possibility of validating a submitted plan.

'''
        set_credits_stream(credits)
        with OneshotPlanner(name='tamer'):
            self.assertEqual(credits.getvalue(), test_credits)
        set_credits_stream(sys.stdout)

    @skipIfSolverNotAvailable('tamer')
    @skipIfSolverNotAvailable('pyperplan')
    @skipIfSolverNotAvailable('sequential_plan_validator')
    @skipIfSolverNotAvailable('up_grounder')
    @skipIfSolverNotAvailable('tarski_grounder')
    @skipIfSolverNotAvailable('opt-pddl-solver')
    def test_long_env_credits(self):
        credits = StringIO()
        test_credits = ['These are the solvers currently available:\n',
'''---------------------------------------
Tamer
Developers: FBK Tamer Development Team
Contacts: tamer@fbk.eu
Website: https://tamer.fbk.eu
License: Free for Educational Use
Tamer offers the capability to generate a plan for classical, numerical and temporal problems.
For those kind of problems tamer also offers the possibility of validating a submitted plan.
You can find all the related publications here: https://tamer.fbk.eu/publications/''',
'''---------------------------------------
pyperplan
Developers: Artificial Intelligence Group - University of Basel
Contacts: Yusra Alkhazraji and Matthias Frorath and Markus Grützner and Malte Helmert and Thomas Liebetraut and Robert Mattmüller and Manuela Ortlieb and Jendrik Seipp and Tobias Springenberg and Philip Stahl and Jan Wülfing
Website: https://github.com/aibasel/pyperplan
License: GNU GENERAL PUBLIC LICENSE, Version 3
Pyperplan is a lightweight STRIPS planner written in Python.
Please note that Pyperplan deliberately prefers clean code over fast code. It is designed to be used as a teaching or prototyping tool. If you use it for paper experiments, please state clearly that Pyperplan does not offer state-of-the-art performance.
It was developed during the planning practical course at Albert-Ludwigs-Universität Freiburg during the winter term 2010/2011 and is published under the terms of the GNU General Public License 3 (GPLv3).
Pyperplan supports the following PDDL fragment: STRIPS without action costs.

This engine supports the following features:''',
'''---------------------------------------
UP sequential plan validator
Developers: AIPlan4EU-team
Contacts: aiplan4eu@fbk.eu
Website: https://github.com/aiplan4eu/unified-planning/solvers/plan_validator
License: Apache 2.0
UP sequential validator, does sequential plan validation by creating a state from the problem initial state.
After that the validator tries to apply the action instances of the given plan.
If the every action instance is applicable in the reached state and after the sequential applications of all the actions, the goals is reached, the plan is considered valid. Otherwise the plan is invalid and the unsatisfied condition is reported to the user as an ERROR level LogMessage.

This engine supports the following features:''',
'''---------------------------------------
UP naive grounder
Developers: AIPlan4EU-team
Contacts: aiplan4eu@fbk.eu
Website: https://github.com/aiplan4eu/unified-planning/solvers/grounder
License: Apache 2.0
This grounder, does basic simplification and removes impossible actions and actions with different assignment to the same variable. It implements the naive grounding algorithm for classical, numeric and temporal planning

This engine supports the following features:''',
'''---------------------------------------
Tarski grounder
Developers: Artificial Intelligence and Machine Learning Group - Universitat Pompeu Fabra
Contacts: info-ai@upf.edu
Website: https://github.com/aig-upf/tarski
License: Apache 2.0
Tarski grounder, more information available on the given website.

This engine supports the following features:''',
'''---------------------------------------
ENHSP
Developers: Enrico Scala
Contacts: enricos83@gmail.com
Website: https://sites.google.com/view/enhsp/home
License: GNU General Public license, version 3 or later
ENHSP is a forward heuristic search planner, but it is expressive in that it can handle:
 - Classical Planning
 - Numeric Planning with linear and non-linear (!!) expressions
 - Planning with discretised autonomous processes and events
 - Global constraints, which are the analogous of always constraints of PDDL.

This engine supports the following features:'''
]
        get_env().factory.print_solvers_info(credits, True)
        credits_printed = credits.getvalue()
        for test in test_credits:
            self.assertIn(test, credits_printed)
