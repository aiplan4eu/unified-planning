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
from unified_planning.model.environment_ma import Environment_ma

from unified_planning.io.pddl_writer import PDDLWriter
from unified_planning.io.pddl_writer_ma import PDDLWriter_MA, Write_MA_Problem
from unified_planning.io.pddl_reader import PDDLReader


Example = namedtuple('Example', ['problem'])
problems = {}
examples_realistic = get_example_problems()

def depot_and_truck_problem():
    problems = {}
    problem = examples_realistic['depot'].problem
    # examples['...'].problem supported:
    # Yes: robot                                 PDDL:Yes
    # Yes: robot_fluent_of_user_type             PDDL:No (PDDL supports only boolean and numerical fluents)
    # Yes: robot_no_negative_preconditions       PDDL:Yes    OneShotPlanner:Yes
    # Yes: robot_decrease                        PDDL:Yes
    # Yes: robot_loader                          PDDL:Yes
    # Yes: robot_loader_mod                      PDDL:Yes
    # Yes: robot_loader_adv                      PDDL:Ye
    # Yes: robot_locations_connected             PDDL:Yes
    # Yes: robot_locations_visited               PDDL:Yes
    # Yes: charge_discharge                      PDDL:Yes
    # No: matchcellar
    # No: timed_connected_locations
    fluents_problem = problem.fluents
    actions_problem = problem.actions
    init_values_problem = problem.initial_values
    goals_problem = problem.goals
    objects_problem = problem.all_objects

    robot1 = Agent('depot0')
    robot2 = Agent('distributor0')
    robot3 = Agent('distributor1')
    robot4 = Agent('truck0')
    robot5 = Agent('truck1')
    environment = Environment_ma()

    robot1.add_fluents(fluents_problem)
    robot2.add_fluents(fluents_problem)
    robot3.add_fluents(fluents_problem)
    robot1.add_actions(actions_problem)
    robot2.add_actions(actions_problem)
    robot3.add_actions(actions_problem)
    robot4.add_actions(actions_problem)
    robot5.add_actions(actions_problem)
    robot1.set_initial_values(init_values_problem)
    robot2.set_initial_values(init_values_problem)
    robot3.set_initial_values(init_values_problem)
    robot4.set_initial_values(init_values_problem)
    robot5.set_initial_values(init_values_problem)
    robot1.add_goals(goals_problem)
    robot2.add_goals(goals_problem)
    robot3.add_goals(goals_problem)
    robot4.add_goals(goals_problem)
    robot5.add_goals(goals_problem)

    ma_problem = MultiAgentProblem('depots')
    ma_problem.add_agent(robot1)
    ma_problem.add_agent(robot2)
    ma_problem.add_agent(robot3)
    ma_problem.add_agent(robot4)
    ma_problem.add_agent(robot5)
    ma_problem.add_environment(environment)
    ma_problem.add_objects(objects_problem)

    problem = ma_problem.compile_ma()

    ma_problem.add_shared_data(ma_problem.fluent('clear_h'))
    ma_problem.add_shared_data(ma_problem.fluent('clear_s'))
    ma_problem.add_shared_data(ma_problem.fluent('at'))

    ma_problem.add_shared_data(ma_problem.fluent('pos_p'))
    ma_problem.add_shared_data(ma_problem.fluent('pos_u'))
    ma_problem.add_shared_data(ma_problem.fluent('on_h'))
    ma_problem.add_shared_data(ma_problem.fluent('on_u'))
    ma_problem.add_shared_data(ma_problem.fluent('on_s'))

    # Add fucntions
    ma_problem.add_flu_function(ma_problem.fluent('located'))
    ma_problem.add_flu_function(ma_problem.fluent('at'))
    ma_problem.add_flu_function(ma_problem.fluent('placed'))
    ma_problem.add_flu_function(ma_problem.fluent('pos_p'))
    ma_problem.add_flu_function(ma_problem.fluent('pos_u'))
    ma_problem.add_flu_function(ma_problem.fluent('on_h'))
    ma_problem.add_flu_function(ma_problem.fluent('on_u'))
    ma_problem.add_flu_function(ma_problem.fluent('on_s'))

    print(problem)

    robots = Example(problem=problem)
    problems['depots'] = robots


    ##################################depot_truck##################################
    problem = examples_realistic['depot_truck'].problem
    fluents_problem = problem.fluents
    actions_problem = problem.actions
    init_values_problem = problem.initial_values
    goals_problem = problem.goals
    objects_problem = problem.all_objects
    #plan = examples['robot'].plan
    robot1 = Agent('depot0')
    robot2 = Agent('distributor0')
    robot3 = Agent('distributor1')
    robot4 = Agent('truck0')
    robot5 = Agent('truck1')

    environment = Environment_ma()

    robot1.add_fluents(fluents_problem)
    robot2.add_fluents(fluents_problem)
    robot3.add_fluents(fluents_problem)
    robot4.add_fluents(fluents_problem)
    robot5.add_fluents(fluents_problem)
    robot1.add_actions(actions_problem)
    robot2.add_actions(actions_problem)
    robot3.add_actions(actions_problem)
    robot4.add_actions(actions_problem)
    robot5.add_actions(actions_problem)
    robot1.set_initial_values(init_values_problem)
    robot2.set_initial_values(init_values_problem)
    robot3.set_initial_values(init_values_problem)
    robot4.set_initial_values(init_values_problem)
    robot5.set_initial_values(init_values_problem)
    robot1.add_goals(goals_problem)
    robot2.add_goals(goals_problem)
    robot3.add_goals(goals_problem)
    robot4.add_goals(goals_problem)
    robot5.add_goals(goals_problem)

    ma_problem = MultiAgentProblem('depot_trucks')
    ma_problem.add_agent(robot1)
    ma_problem.add_agent(robot2)
    ma_problem.add_agent(robot3)
    ma_problem.add_agent(robot4)
    ma_problem.add_agent(robot5)
    ma_problem.add_environment(environment)
    ma_problem.add_objects(objects_problem)


    problem = ma_problem.compile_ma()
    ma_problem.add_shared_data(ma_problem.fluent('clear_h'))
    ma_problem.add_shared_data(ma_problem.fluent('clear_s'))
    ma_problem.add_shared_data(ma_problem.fluent('at'))
    ma_problem.add_shared_data(ma_problem.fluent('pos_p'))
    ma_problem.add_shared_data(ma_problem.fluent('pos_u'))
    ma_problem.add_shared_data(ma_problem.fluent('on_h'))
    ma_problem.add_shared_data(ma_problem.fluent('on_u'))
    ma_problem.add_shared_data(ma_problem.fluent('on_s'))

    #Add fucntions
    ma_problem.add_flu_function(ma_problem.fluent('located'))
    ma_problem.add_flu_function(ma_problem.fluent('at'))
    ma_problem.add_flu_function(ma_problem.fluent('placed'))
    ma_problem.add_flu_function(ma_problem.fluent('pos_p'))
    ma_problem.add_flu_function(ma_problem.fluent('pos_u'))
    ma_problem.add_flu_function(ma_problem.fluent('on_h'))
    ma_problem.add_flu_function(ma_problem.fluent('on_u'))
    ma_problem.add_flu_function(ma_problem.fluent('on_s'))

    print(problem)


    robots = Example(problem=problem)
    problems['depot_trucks'] = robots






    ##################################depot_truck##################################
    problem = examples_realistic['depot_mix'].problem
    fluents_problem = problem.fluents
    actions_problem = problem.actions
    init_values_problem = problem.initial_values
    goals_problem = problem.goals
    objects_problem = problem.all_objects

    robot1 = Agent('depot0')
    robot2 = Agent('distributor0')
    robot3 = Agent('distributor1')
    robot4 = Agent('truck0')
    robot5 = Agent('truck1')

    environment = Environment_ma()

    robot1.add_fluents(fluents_problem)
    robot2.add_fluents(fluents_problem)
    robot3.add_fluents(fluents_problem)
    robot4.add_fluents(fluents_problem)
    robot5.add_fluents(fluents_problem)
    robot1.add_actions(actions_problem)
    robot2.add_actions(actions_problem)
    robot3.add_actions(actions_problem)
    robot4.add_actions(actions_problem)
    robot5.add_actions(actions_problem)
    robot1.set_initial_values(init_values_problem)
    robot2.set_initial_values(init_values_problem)
    robot3.set_initial_values(init_values_problem)
    robot4.set_initial_values(init_values_problem)
    robot5.set_initial_values(init_values_problem)
    robot1.add_goals(goals_problem)
    robot2.add_goals(goals_problem)
    robot3.add_goals(goals_problem)
    robot4.add_goals(goals_problem)
    robot5.add_goals(goals_problem)

    ma_problem = MultiAgentProblem('depot_trucks')
    ma_problem.add_agent(robot1)
    ma_problem.add_agent(robot2)
    ma_problem.add_agent(robot3)
    ma_problem.add_agent(robot4)
    ma_problem.add_agent(robot5)
    ma_problem.add_environment(environment)
    ma_problem.add_objects(objects_problem)


    problem = ma_problem.compile_ma()
    ma_problem.add_shared_data(ma_problem.fluent('clear_h'))
    ma_problem.add_shared_data(ma_problem.fluent('clear_s'))
    ma_problem.add_shared_data(ma_problem.fluent('at'))
    ma_problem.add_shared_data(ma_problem.fluent('pos_p'))
    ma_problem.add_shared_data(ma_problem.fluent('pos_u'))
    ma_problem.add_shared_data(ma_problem.fluent('on_h'))
    ma_problem.add_shared_data(ma_problem.fluent('on_u'))
    ma_problem.add_shared_data(ma_problem.fluent('on_s'))

    #Add fucntions
    ma_problem.add_flu_function(ma_problem.fluent('located'))
    ma_problem.add_flu_function(ma_problem.fluent('at'))
    ma_problem.add_flu_function(ma_problem.fluent('placed'))
    ma_problem.add_flu_function(ma_problem.fluent('pos_p'))
    ma_problem.add_flu_function(ma_problem.fluent('pos_u'))
    ma_problem.add_flu_function(ma_problem.fluent('on_h'))
    ma_problem.add_flu_function(ma_problem.fluent('on_u'))
    ma_problem.add_flu_function(ma_problem.fluent('on_s'))

    print(problem)


    robots = Example(problem=problem)
    problems['depots_mix'] = robots


    problem_depots = problems['depots'].problem
    problem_trucks = problems['depot_trucks'].problem
    problems_ma = [problem_depots, problem_trucks]

    w = Write_MA_Problem()
    w.map_agent_problem(problem_depots, 'depot0')
    w.map_agent_problem(problem_depots, 'distributor0')
    w.map_agent_problem(problem_depots, 'distributor1')
    w.map_agent_problem(problem_trucks, 'truck0')
    w.map_agent_problem(problem_trucks, 'truck1')
    w.write_ma_problem(problems_ma)
    plan = w.FMAP_planner()

    print(plan)






depot_and_truck_problem()