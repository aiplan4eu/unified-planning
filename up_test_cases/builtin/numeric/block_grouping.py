from collections import namedtuple
from itertools import chain, combinations
from unified_planning.shortcuts import *
from unified_planning.test import TestCase
import random

# ProblemMetadata is a data structure that contains the information to create different instance of the "block_grouping" problem.
# since some initial values are created using a random generator, the seed is needed for replication fo the same test.
# groups determines how many block groups there are
ProblemMetadata = namedtuple(
    "ProblemMetadata", ["max_coordinate", "blocks_number", "groups", "seed"]
)

problems_meta_data = [
    ProblemMetadata(5, 5, 1, 1),
]


def get_test_cases():
    res = {}

    base_problem = Problem()
    Block = UserType("block")

    x = Fluent("x", RealType(), b=Block)
    y = Fluent("y", RealType(), b=Block)
    max_x = Fluent("max_x", RealType())
    min_x = Fluent("min_x", RealType())
    max_y = Fluent("max_y", RealType())
    min_y = Fluent("min_y", RealType())
    base_problem.add_fluent(x)
    base_problem.add_fluent(y)
    base_problem.add_fluent(max_x)
    base_problem.add_fluent(min_x, default_initial_value=1)
    base_problem.add_fluent(max_y)
    base_problem.add_fluent(min_y, default_initial_value=1)

    move_block_up = InstantaneousAction("move_block_up", b=Block)
    b = move_block_up.b
    move_block_up.add_precondition(LE(Plus(y(b), 1), max_y))
    move_block_up.add_increase_effect(y(b), 1)

    move_block_down = InstantaneousAction("move_block_down", b=Block)
    b = move_block_down.b
    move_block_down.add_precondition(LE(min_y, Minus(y(b), 1)))
    move_block_down.add_decrease_effect(y(b), 1)

    move_block_right = InstantaneousAction("move_block_right", b=Block)
    b = move_block_right.b
    move_block_right.add_precondition(LE(Plus(x(b), 1), max_x))
    move_block_right.add_increase_effect(x(b), 1)

    move_block_left = InstantaneousAction("move_block_left", b=Block)
    b = move_block_left.b
    move_block_left.add_precondition(LE(min_x, Minus(x(b), 1)))
    move_block_left.add_decrease_effect(x(b), 1)
    base_problem.add_actions(
        (move_block_up, move_block_down, move_block_right, move_block_left)
    )

    for md in problems_meta_data:
        random.seed(md.seed)
        problem = base_problem.clone()
        problem.name = f"block_grouping_{md.max_coordinate}_{md.blocks_number}_{md.groups}_{md.seed}"

        problem.set_initial_value(max_x, md.max_coordinate)
        problem.set_initial_value(max_y, md.max_coordinate)

        # mapping from an object to the objects in the same group
        groups: List[List[Object]] = []
        first_elements: List[Object] = []

        for i in range(md.blocks_number):
            block = Object(f"b{i+1}", Block)
            if i < md.groups:
                groups.append([block])
                first_elements.append(block)
            else:
                groups[i % md.groups].append(block)
            problem.add_object(block)

        for block in chain(*groups):
            problem.set_initial_value(x(block), random.randint(1, md.max_coordinate))
            problem.set_initial_value(y(block), random.randint(1, md.max_coordinate))

        # in the goal, every block in the same group must have same x and y,
        # and different groups must have either x or y (or both) different
        for block_a, block_b in combinations(first_elements, 2):
            problem.add_goal(
                Or(
                    Not(Equals(x(block_a), x(block_b))),
                    Not(Equals(y(block_a), y(block_b))),
                )
            )
        for block_group in groups:
            head = block_group[0]
            for other_element in block_group[1:]:
                problem.add_goal(
                    And(
                        Equals(x(head), x(other_element)),
                        Equals(y(head), y(other_element)),
                    )
                )

        res[problem.name] = TestCase(problem=problem, solvable=True)

    return res
