from unified_planning.shortcuts import *

from unified_planning.model.multi_agent import MultiAgentProblem, Agent

problem = MultiAgentProblem("robot_migration")
Location = UserType("Location")
is_connected = Fluent("is_connected", BoolType(), l1=Location, l2=Location)
problem.ma_environment.add_fluent(is_connected, default_initial_value=False)

locations_number = 4
locations = [Object(f"l{i}", Location) for i in range(1, locations_number + 1)]
problem.add_objects(locations)

robot_position = Fluent("pos", Location)

move = InstantaneousAction("move", l_from=Location, l_to=Location)
l_from = move.parameter("l_from")
l_to = move.parameter("l_to")
move.add_precondition(Equals(robot_position, l_from))
move.add_precondition(is_connected(l_from, l_to))
move.add_effect(robot_position, l_to)

robots_number = 3
robots = []
for i in range(1, robots_number + 1):
    robot = Agent(f"robot{i}", problem)
    robots.append(robot)
    robot.add_fluent(robot_position)
    robot.add_action(move)
    problem.add_agent(robot)

last_location = locations[0]
for robot in robots:
    problem.set_initial_value(Dot(robot, robot_position), last_location)

for location in locations[1:]:
    problem.set_initial_value(is_connected(last_location, location), True)
    last_location = location

for robot in robots:
    problem.add_goal(Equals(Dot(robot, robot_position), locations[-1]))


from unified_planning.model import ContingentProblem, SensingAction

problem = ContingentProblem("lost_packages")
Package = UserType("Package")
Location = UserType("Location")
loader_plate = problem.add_object("loader_plate", Location)
loader_at = problem.add_fluent("loader_at", Location)
is_package_at = problem.add_fluent("is_package_at", location=Location, package=Package)
loader_free = problem.add_fluent("loader_free", default_initial_value=True)

# senses if the package is at the location
sense_package = SensingAction("sense_package", location=Location, package=Package)
sense_package.add_observed_fluent(
    is_package_at(sense_package.location, sense_package.package)
)
sense_package.add_precondition(loader_at.Equals(sense_package.location))

move_loader = InstantaneousAction("move_loader", l_from=Location, l_to=Location)
move_loader.add_precondition(loader_at.Equals(move_loader.l_from))
move_loader.add_effect(loader_at, move_loader.l_to)

load = InstantaneousAction("load", package=Package, location=Location)
load.add_precondition(is_package_at(load.location, load.package))
load.add_precondition(loader_at.Equals(load.location))
load.add_precondition(loader_free)
load.add_effect(is_package_at(load.location, load.package), False)
load.add_effect(is_package_at(loader_plate, load.package), True)
load.add_effect(loader_free, False)

unload = InstantaneousAction("unload", package=Package)
unload.add_precondition(is_package_at(loader_plate, unload.package))
unload.add_effect(loader_free, True)
unload.add_effect(is_package_at(loader_plate, unload.package), False)
unload.add_effect(is_package_at(loader_at, unload.package), False)

problem.add_actions([sense_package, move_loader, load, unload])

locations_number = 5
locations = [Object(f"l{i}", Location) for i in range(1, locations_number + 1)]
problem.add_objects(locations)
problem.set_initial_value(loader_at, locations[1])
packages_number = 10
packages = [Object(f"p{i}", Package) for i in range(1, packages_number + 1)]
problem.add_objects(packages)

for p in packages:
    # The package is in only one of the locations
    problem.add_oneof_initial_constraint([is_package_at(l, p) for l in locations])
    problem.set_initial_value(is_package_at(loader_plate, p), False)
    problem.add_goal(is_package_at(locations[-1], p))
