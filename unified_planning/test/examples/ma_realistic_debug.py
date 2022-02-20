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
# limitations under the License.


import unified_planning
from unified_planning.shortcuts import *
from collections import namedtuple
from unified_planning.model.agent import Agent
from unified_planning.model.ma_problem import MultiAgentProblem
from realistic import get_example_problems
from unified_planning.model.environment_ma import Environment_

from unified_planning.io.pddl_writer import PDDLWriter
from unified_planning.io.pddl_reader import PDDLReader
from unified_planning.transformers import NegativeConditionsRemover

Example = namedtuple('Example', ['problem', 'plan'])
problems = {}
examples = get_example_problems()

def ma_example():
    problem = examples['robot_no_negative_preconditions'].problem

    # examples['...'].problem supported:
    # Yes: robot                                 PDDL:Yes
    # No: robot_fluent_of_user_type
    # Yes: robot_no_negative_preconditions       PDDL:Yes    OneShotPlanner:Yes
    # Yes: robot_decrease                        PDDL:Yes
    # Yes: robot_loader                          PDDL:Yes
    # Yes: robot_loader_mod                      PDDL:Yes
    # Yes: robot_loader_adv                      PDDL:Yes
    # Yes: robot_locations_connected             PDDL:Yes
    # No:  robot_locations_visited
    # Yes: charge_discharge                      PDDL:Yes
    # No: matchcellar
    # No: timed_connected_locations

    fluents_problem = problem.fluents()
    actions_problem = problem.actions()
    init_values_problem = problem.initial_values()
    goals_problem = problem.goals()
    objects_problem = problem.all_objects()
    plan = examples['robot_no_negative_preconditions'].plan
    robot1 = Agent()
    robot2 = Agent()
    environment = Environment_()

    robot1.add_fluents(fluents_problem)
    robot2.add_fluents(fluents_problem)
    robot1.add_actions(actions_problem)
    robot2.add_actions(actions_problem)
    robot1.set_initial_values(init_values_problem)
    robot2.set_initial_values(init_values_problem)
    robot1.add_goals(goals_problem)
    robot2.add_goals(goals_problem)

    ma_problem = MultiAgentProblem('robots')
    ma_problem.add_agent(robot1)
    ma_problem.add_agent(robot2)
    ma_problem.add_environment_(environment)
    ma_problem.add_objects(objects_problem)
    problem = ma_problem.compile()
    print(problem)

    print("Single agent plan:\n ", plan)
    plan = ma_problem.extract_plans(plan)
    print("Multi agent plan:\n ", plan)
    robots = Example(problem=problem, plan=plan)
    problems['robots'] = robots

    w = PDDLWriter(problem)
    print(w.get_domain())
    print(w.get_problem())

    #KeyError di Location ("Usertype")
    with OneshotPlanner(name='tamer') as planner:
        solve_plan = planner.solve(problem)
        print("Pyperplan returned: %s" % solve_plan)

    #unified_planning.exceptions.UPExpressionDefinitionError: Expression: (not (l_from == l_to)) is not in NNF.
    npr = NegativeConditionsRemover(problem)
    positive_problem = npr.get_rewritten_problem()
    print("positive_problem", positive_problem)



ma_example()