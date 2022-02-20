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
from unified_planning.transformers import DisjunctiveConditionsRemover
from unified_planning.transformers import ConditionalEffectsRemover
from unified_planning.transformers  import QuantifiersRemover

Example = namedtuple('Example', ['problem', 'plan'])
problems = {}
examples = get_example_problems()

def ma_example():
    problem = examples['robot_no_negative_preconditions'].problem

    # examples['...'].problem supported:
    # Yes: robot
    # No:  robot_fluent_of_user_type
    # Yes: robot_no_negative_preconditions
    # Yes: robot_decrease
    # Yes: robot_loader
    # Yes: robot_loader_mod
    # Yes: robot_loader_adv
    # Yes: robot_locations_connected
    # Yes: robot_locations_visited
    # Yes: charge_discharge
    # No:  matchcellar
    # No:  timed_connected_locations

    fluents_problem = problem.fluents()
    user_types = problem.user_types()
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
    #ma_problem.add_user_types(user_types)
    print("user_types: ", ma_problem.user_types())
    problem = ma_problem.compile()
    print(problem)
    print("Single agent plan:\n ", plan)
    plan = ma_problem.extract_plans(plan)
    print("Multi agent plan:\n ", plan)
    robots = Example(problem=problem, plan=plan)
    problems['robots'] = robots

    '''w = PDDLWriter(problem)
    print(w.get_domain())
    print(w.get_problem())'''

    #npr = NegativeConditionsRemover(problem)
    #positive_problem = npr.get_rewritten_problem()
    # print("positive_problem", positive_problem)

    with OneshotPlanner(name='pyperplan') as planner:
        solve_plan = planner.solve(problem)
        print("Tamer returned: %s" % solve_plan)

    #with OneshotPlanner(name='pyperplan') as planner:
    #    solve_plan = planner.solve(problem)
    #    print("Pyperplan returned: %s" % solve_plan)

    #dnfr = DisjunctiveConditionsRemover(problem)
    #dnf_problem = dnfr.get_rewritten_problem()
    #print(dnf_problem)

    #cer = ConditionalEffectsRemover(problem)
    #unconditional_problem = cer.get_rewritten_problem()
    #print(unconditional_problem)
    #qr = QuantifiersRemover(problem)
    #uq_problem = qr.get_rewritten_problem()



def ma_example_env():
    problem = examples['robot'].problem

    fluents_problem = problem.fluents()
    actions_problem = problem.actions()
    print("fluents_problem", fluents_problem)


    init_values_problem = problem.initial_values()
    goals_problem = problem.goals()
    objects_problem = problem.all_objects()
    plan = examples['robot'].plan
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


    Location = UserType('Location')
    l3 = Object('l1', Location)
    l4 = Object('l2', Location)
    cargo_at = Fluent('cargo_at', BoolType(), [Location])
    environment.add_fluent(cargo_at)
    environment.set_initial_value(cargo_at(l3), False)
    environment.set_initial_value(cargo_at(l4), True)

    ma_problem = MultiAgentProblem('robots_env')
    ma_problem.add_agent(robot1)
    ma_problem.add_agent(robot2)
    ma_problem.add_objects(objects_problem)
    ma_problem.add_environment_(environment)
    problem = ma_problem.compile()
    print("Single agent plan:\n ", plan)
    plan = ma_problem.extract_plans(plan)
    print("\n Multi agent plan:\n ", plan)
    robots = Example(problem=problem, plan=plan)
    problems['robots_env'] = robots
    print(problems['robots_env'])

ma_example()