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
#from unified_planning.transformers import NegativeConditionsRemover


Example = namedtuple('Example', ['problem'])
problems = {}
examples_realistic = get_example_problems()

def ma_example():
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

    fluents_problem = problem.fluents()
    actions_problem = problem.actions()
    init_values_problem = problem.initial_values()
    goals_problem = problem.goals()
    objects_problem = problem.all_objects()
    plan = examples_realistic['robot'].plan
    robot1 = Agent()
    robot2 = Agent()
    environment = Environment_ma()

    '''print(fluents_problem, init_values_problem, "weeeeeeeeeeeeeeee",init_values_problem.keys())
    cargo_flu = fluents_problem[1]
    #cargo_flu2 = fluents_problem[2]
    key = 'cargo_at(l1)'
    if key in init_values_problem.keys():
        init_flu = init_values_problem[key]
    else:
        init_flu = None

    for i in enumerate(init_values_problem.items()):
        if str(i[1][0]) == 'cargo_at(l1)':
            print(i[1])
            init_flu_key = i[1][0]
            init_flu_value = i[1][1]
    for i in enumerate(init_values_problem.items()):
        if str(i[1][0]) == 'cargo_at(l2)':
            print(i[1])
            init_flu_key2 = i[1][0]
            init_flu_value2 = i[1][1]
    print(init_flu_key, cargo_flu)
    environment.add_fluent(cargo_flu)
    #environment.add_fluent(cargo_flu2)
    environment.set_initial_value(init_flu_key, init_flu_value)
    environment.set_initial_value(init_flu_key2, init_flu_value2)
    print(environment.get_initial_values(), environment.get_fluents())'''


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
    ma_problem.add_environment(environment)
    ma_problem.add_objects(objects_problem)
    #problem = ma_problem.compile()
    problem = ma_problem.compile_ma()
    print(problem)

    print("Single agent plan:\n ", plan)
    plan = ma_problem.extract_plans(plan)
    print("Multi agent plan:\n ", plan, "\n")
    robots = Example(problem=problem, plan=plan)
    problems['robots'] = robots

    #w = PDDLWriter(problem)
    #print(w.get_domain())
    #print(w.get_problem())

    w = PDDLWriter_MA(problem)
    print(w.get_domain())
    print(w.get_problem())

    #ma_problem.pddl_writer()


    #KeyError di Location ("Usertype")
    #with OneshotPlanner(name='tamer') as planner:
    #    solve_plan = planner.solve(problem)
    #    print("Pyperplan returned: %s" % solve_plan)

    #unified_planning.exceptions.UPExpressionDefinitionError: Expression: (not (l_from == l_to)) is not in NNF.
    #npr = NegativeConditionsRemover(problem)
    #positive_problem = npr.get_rewritten_problem()
    #print("positive_problem", positive_problem)



#ma_example()


def ma_example_2():
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



    # Add shared data
    # problem = ma_problem.compile()
    problem = ma_problem.compile_ma()
    #Prima compilo poi estraggo il fluente dal problem per indicarlo come
    #fluente condiviso tra gli agenti

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

    #print("Single agent plan:\n ", plan)
    #plan = ma_problem.extract_plans(plan)
    #print("Multi agent plan:\n ", plan, "\n")
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
    surface = UserType('surface', None)
    ciao = Fluent('ciao', None, surface=surface)
    robot5.add_fluent(ciao)
    environment.add_fluent(ciao)

    ma_problem = MultiAgentProblem('depot_trucks')
    ma_problem.add_agent(robot1)
    ma_problem.add_agent(robot2)
    ma_problem.add_agent(robot3)
    ma_problem.add_agent(robot4)
    ma_problem.add_agent(robot5)
    ma_problem.add_environment(environment)
    ma_problem.add_objects(objects_problem)


    #Add shared data
    #problem = ma_problem.compile()

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

    #print("Single agent plan:\n ", plan)
    #plan = ma_problem.extract_plans(plan)
    #print("Multi agent plan:\n ", plan, "\n")
    robots = Example(problem=problem)
    problems['depot_trucks'] = robots


    #ag_list = ['depot0', 'distributor0', "distributor1"]
    #ag_list = problem.agent_list_problems = ['truck0', 'truck1'] #in caso di "depot_truck"

    #Devo associare in qualche modo a un problema il suo nome ex:"depot0"
    #Il nome è il nome dell'agente
    #Perchè io prima compilo e ottengo il ma problem di depot e poi
    #faccio lo stesso con depot_truck.
    #Questa mappatura mi serve per creare i

    '''problem_depots = problems['depots'].problem
    problem.map_agent_problem(problem_depots, 'depot0')
    problem.map_agent_problem(problem_depots, 'distributor0')
    problem.map_agent_problem(problem_depots, 'distributor1')

    problem_trucks = problems['depot_trucks'].problem
    problem.map_agent_problem(problem_trucks, 'truck0')
    problem.map_agent_problem(problem_trucks, 'truck1')

    problems_ma = [problem_depots, problem_trucks]
    
    problem.write_ma_problem(self, problems_ma)
    plan = problem.FMAP_planner()
    print(plan)'''

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






ma_example_2()