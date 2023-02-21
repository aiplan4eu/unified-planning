from unified_planning.test.scheduling import examples, jobshop


def problems():
    instances = [
        examples.basic(),
        examples.resource_set(),
        examples.Example(jobshop.parse(jobshop.FT06, "ft06"), None),
    ]
    return dict((instance.problem.name, instance) for instance in instances)
