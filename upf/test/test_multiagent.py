import upf
from upf.shortcuts import *
from collections import namedtuple
from agent import agent
from ma_problem import MultiAgentProblem



def init_robot1():
    Location = UserType('Location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    battery_charge = Fluent('battery_charge', RealType(0, 100))

    # Creo gli ogetti robot1 e robot2
    robot1 = agent(robot_at, [], [])
    robot1.add_fluents(battery_charge)

    # Azione move con le sue precondizioni ed effetti
    move = InstantaneousAction('move', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(GE(battery_charge, 30))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_effect(battery_charge, Minus(battery_charge, 40))

    # Aggiungo move con le precondizioni e gli effetti associati
    robot1.add_actions(move)

    # Uso i metodi preconditions ed effects della classe InstantaneousAction dentro Robot1
    actions_r1 = robot1.get_actions()
    print("Actions_r1: ", actions_r1)
    print("Preconditions: ", actions_r1[0].preconditions())
    print("Effects: ", actions_r1[0].effects())

    # Aggiungo un fluente a Robot1
    cargo_at = Fluent('cargo_at', BoolType(), [Location])
    robot1.add_fluents(cargo_at)

    # Ottengo i fluenti di Robot1
    fluents_r1 = robot1.get_fluents()

    # Uso i metodi name e type della classe Fluents dentro Robot1
    print("\n Fluents: ", fluents_r1)

    return robot1


def init_robot2():
    Location = UserType('Location2')
    robot_at = Fluent('robot_at2', BoolType(), [Location])
    battery_charge = Fluent('battery_charge2', RealType(0, 100))

    # Creo gli ogetti robot1 e robot2
    robot2 = agent(robot_at, [], [])
    robot2.add_fluents(battery_charge)

    # Azione move con le sue precondizioni ed effetti
    move = InstantaneousAction('move_2', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(GE(battery_charge, 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_effect(battery_charge, Minus(battery_charge, 10))
    # Aggiungo move con le precondizioni e gli effetti associati
    robot2.add_actions(move)

    # Uso i metodi preconditions ed effects della classe InstantaneousAction dentro Robot1
    actions_r2 = robot2.get_actions()
    print("Actions_r2: ", actions_r2)
    print("Preconditions_r2: ", actions_r2[0].preconditions())
    print("Effects_r2: ", actions_r2[0].effects())

    # Aggiungo un fluente a Robot1
    cargo_at = Fluent('cargo_at2', BoolType(), [Location])
    robot2.add_fluents(cargo_at)

    # Ottengo i fluenti di Robot1
    fluents_r1 = robot2.get_fluents()

    return robot2


print("------------------Robot1------------------")
robot1 = init_robot1()
print("------------------Robot2------------------")
robot2 = init_robot2()

Example = namedtuple('Example', ['problem', 'plan'])


def problems_agents(robot1, robot2):
    problems = {}


    Location = UserType('Location')
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    ok = []
    problem = MultiAgentProblem('robots')

    problem.add_agent(robot1)
    problem.add_agent(robot2)

    Location2 = UserType('Location2')
    l1_2 = Object('l1_1', Location2)
    l2_2 = Object('l2_2', Location2)


    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot1.ID(l1), True)
    problem.set_initial_value(robot1.ID(l2), False)
    battery_charge = Fluent('battery_charge', RealType(0, 100))
    problem.set_initial_value(battery_charge, 30)
    problem.add_goal(robot1.ID(l2))


    problem.add_object(l1_2)
    problem.add_object(l2_2)
    problem.set_initial_value(robot2.ID(l1_2), True)
    problem.set_initial_value(robot2.ID(l2_2), False)
    battery_charge = Fluent('battery_charge2', RealType(0, 100))
    problem.set_initial_value(battery_charge, 80)
    problem.add_goal(robot2.ID(l2_2))


    ObjectExps_1 = [(ObjectExp(l1), ObjectExp(l2))]  # robot1
    ObjectExps_2 = [(ObjectExp(l1_2), ObjectExp(l2_2))]  # robot2


    problem.compile(problem)

    plan = []
    for ag in problem.get_agent():
        #print(ag.get_actions(), "plan")
        for i in range(len(ag.get_actions())):

            plan.append(upf.plan.SequentialPlan([upf.plan.ActionInstance(ag.get_actions()[i], ObjectExps_1[i])]))

    robots = Example(problem=problem, plan=plan)
    problems['robots'] = robots


    return problems


#print("\n \n------------------Problems------------------: \n", problems)
print("\n \n------------------Problems------------------: \n")
problems_agents(robot1, robot2)


