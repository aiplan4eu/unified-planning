import upf

try:
    import unittest2 as unittest
except ImportError:
    import unittest


def generate_simple_problem(size: int) -> upf.Problem:
    actions = [upf.Action('mk_y', set(['x']), set(['y']), set(['x'])),
               upf.Action('reset_x', set([]), set(['x']), set([]))]
    goal = []
    for i in range(size):
        name = f"v{i}"
        goal.append(name)
        actions.append(upf.Action(f'mk_{name}', set(['y']), set([name]), set(['y'])),)
    init = set(['x'])
    return upf.Problem(actions, init, set(goal))


TestCase = unittest.TestCase
main = unittest.main
