from unified_planning.test.examples.scheduling import examples, jobshop


def get_example_problems():
    instances = [
        examples.basic(),
        examples.resource_set(),
        examples.non_numeric(),
        examples.Example(jobshop.parse(jobshop.FT06, "ft06"), None),
    ]
    return dict((instance.problem.name, instance) for instance in instances)
