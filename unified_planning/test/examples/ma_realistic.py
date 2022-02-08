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
from unified_planning.model.environment import Environment

Example = namedtuple('Example', ['problem', 'plan'])
problems = {}
examples = get_example_problems()

def ma_example():
    problem = examples['robot'].problem

    # examples['...'].problem supported:
    # Yes: robot
    # No: robot_fluent_of_user_type
    # Yes: robot_no_negative_preconditions
    # Yes: robot_decrease
    # Yes: robot_loader
    # Yes: robot_loader_mod
    # Yes: robot_loader_adv
    # Yes: robot_locations_connected
    # Yes: No robot_locations_visited
    # Yes: charge_discharge
    # No: matchcellar
    # No: timed_connected_locations

    fluents_problem = problem.fluents()
    actions_problem = problem.actions()
    init_values_problem = problem.initial_values()
    goals_problem = problem.goals()
    objects_problem = problem.all_objects()
    plan = examples['robot'].plan
    robot1 = Agent()
    robot2 = Agent()
    environment = Environment()

    robot1.add_individual_fluents(fluents_problem)
    robot2.add_individual_fluents(fluents_problem)
    robot1.add_actions(actions_problem)
    robot2.add_actions(actions_problem)
    robot1.set_initial_values(init_values_problem)
    robot2.set_initial_values(init_values_problem)
    robot1.add_goals(goals_problem)
    robot2.add_goals(goals_problem)
    robot1.add_objects(objects_problem)
    robot2.add_objects(objects_problem)

    ma_problem = MultiAgentProblem('robots')
    ma_problem.add_agent(robot1)
    ma_problem.add_agent(robot2)
    ma_problem.add_environment(environment)
    problem = ma_problem.compile()
    print(problem)
    print("Single agent plan:\n ", plan)
    plan = ma_problem.extract_plans(plan)
    print("Multi agent plan:\n ", plan)
    robots = Example(problem=problem, plan=plan)
    problems['robots'] = robots


def ma_example_env():
    problem = examples['robot'].problem

    fluents_problem = problem.fluents()
    actions_problem = problem.actions()
    init_values_problem = problem.initial_values()
    goals_problem = problem.goals()
    objects_problem = problem.all_objects()
    plan = examples['robot'].plan
    robot1 = Agent()
    robot2 = Agent()
    environment = Environment()

    robot1.add_individual_fluents(fluents_problem)
    robot2.add_individual_fluents(fluents_problem)
    robot1.add_actions(actions_problem)
    robot2.add_actions(actions_problem)
    robot1.set_initial_values(init_values_problem)
    robot2.set_initial_values(init_values_problem)
    robot1.add_goals(goals_problem)
    robot2.add_goals(goals_problem)
    robot1.add_objects(objects_problem)
    robot2.add_objects(objects_problem)

    l1 = robot1.object("l1")
    l2 = robot2.object("l2")
    Location = UserType('Location')
    cargo_at = Fluent('cargo_at', BoolType(), [Location])
    environment.add_fluent(cargo_at)
    environment.add_fluent(cargo_at)
    environment.add_goal(cargo_at(l1))
    environment.set_initial_value(cargo_at(l1), False)
    environment.set_initial_value(cargo_at(l2), True)

    ma_problem = MultiAgentProblem('robots_env')
    ma_problem.add_agent(robot1)
    ma_problem.add_agent(robot2)
    ma_problem.add_environment(environment)
    problem = ma_problem.compile()
    print("Single agent plan:\n ", plan)
    plan = ma_problem.extract_plans(plan)
    print("Multi agent plan:\n ", plan)
    robots = Example(problem=problem, plan=plan)
    problems['robots_env'] = robots

ma_example()