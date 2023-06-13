from unified_planning.shortcuts import *
from unified_planning.plans import SequentialPlan

compiled_plan = SequentialPlan([])

original_problem = Problem()
Brick = UserType("Brick")
Location = UserType("Location")

b1 = original_problem.add_object("b1", Brick)
b2 = original_problem.add_object("b2", Brick)
b3 = original_problem.add_object("b3", Brick)
working_site = original_problem.add_object("working_site", Location)
store = original_problem.add_object("store", Location)

is_at = original_problem.add_fluent(
    "is_at", pos=Location, element=Brick, default_initial_value=False
)
original_problem.set_initial_value(is_at(working_site, b1), True)
original_problem.set_initial_value(is_at(working_site, b2), True)
original_problem.set_initial_value(is_at(working_site, b3), True)
b = Variable("b", Brick)
original_problem.add_goal(Forall(is_at(working_site, b), b))

print(f"Brick objects: {original_problem.objects(Brick)}")
print(f"Original goals: {original_problem.goals}")
with Compiler(
    problem_kind=original_problem.kind,
    compilation_kind=CompilationKind.QUANTIFIERS_REMOVING,
) as compiler:
    compilation_result = compiler.compile(original_problem)
    print(f"Compiled goals: {compilation_result.problem.goals}")
    # Get a valid plan for the compiled problem with the OneshotPlanner Operation Mode
    # compiled_plan = ...
    original_plan = compiled_plan.replace_action_instances(
        compilation_result.map_back_action_instance
    )
    # original_plan is a valid plan for the original problem.

    # Brick objects: [b1, b2, b3]
    # Original goals: [Forall (Brick b) is_at(working_site, b)]
    # Compiled goals: [is_at(working_site, b1) and is_at(working_site, b2) and
    #     is_at(working_site, b3)]
