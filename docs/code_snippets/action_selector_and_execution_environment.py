from typing import Dict, Optional

from unified_planning.environment import Environment
from unified_planning.engines.engine import Engine
from unified_planning.engines.mixins.action_selector import ActionSelectorMixin
from unified_planning.model import Fluent, InstantaneousAction, Problem, ProblemKind
from unified_planning.model.contingent import (
    ContingentProblem,
    SensingAction,
    SimulatedExecutionEnvironment,
)


# [action-selector-class-start]
class DemoActionSelector(Engine, ActionSelectorMixin):
    def __init__(
        self,
        problem,
        error_on_failed_checks: bool = True,
        default_action: Optional[str] = None,
        true_action: Optional[str] = None,
        false_action: Optional[str] = None,
        **kwargs,
    ):
        Engine.__init__(self)
        self.error_on_failed_checks = error_on_failed_checks
        self._default_action = default_action
        self._true_action = true_action
        self._false_action = false_action
        self._next_action_name: Optional[str] = None
        ActionSelectorMixin.__init__(self, problem)
        if self._default_action is None:
            self._default_action = next(iter(problem.actions)).name
        self._next_action_name = self._default_action

    @property
    def name(self):
        return "demo-action-selector"

    @staticmethod
    def supported_kind() -> ProblemKind:
        return ProblemKind()

    @staticmethod
    def supports(problem_kind: ProblemKind) -> bool:
        return True

    def _get_action(self):
        assert self._next_action_name is not None
        return self._problem.action(self._next_action_name)()

    def _update(self, observation: Dict):
        if not observation or self._true_action is None or self._false_action is None:
            return
        observed_value = next(iter(observation.values()))
        if observed_value.is_bool_constant():
            self._next_action_name = (
                self._true_action
                if observed_value.bool_constant_value()
                else self._false_action
            )


# [action-selector-class-end]

# [action-selector-minimal-start]
env = Environment()
problem = Problem("minimal_action_selector_problem", env)
flag = Fluent("flag", environment=env)
problem.add_fluent(flag, default_initial_value=False)

set_true = InstantaneousAction("set_true", _env=env)
set_true.add_effect(flag, True)
set_false = InstantaneousAction("set_false", _env=env)
set_false.add_effect(flag, False)
problem.add_actions([set_true, set_false])

env.factory.add_engine("demo-action-selector", __name__, "DemoActionSelector")
with env.factory.ActionSelector(
    problem,
    name="demo-action-selector",
    params={
        "default_action": "set_true",
        "true_action": "set_false",
        "false_action": "set_true",
    },
) as selector:
    first_action = selector.get_action()
    selector.update({flag(): env.expression_manager.TRUE()})
    second_action = selector.get_action()

assert first_action.action.name == "set_true"
assert second_action.action.name == "set_false"
print(first_action, second_action)

# [action-selector-minimal-end]

# [execution-environment-flow-start]
env2 = Environment()
problem2 = ContingentProblem("parcel_delivery", environment=env2)

is_box = Fluent("is_box", environment=env2)
delivered = Fluent("delivered", environment=env2)
problem2.add_fluent(is_box, default_initial_value=False)
problem2.add_fluent(delivered, default_initial_value=False)
problem2.add_unknown_initial_constraint(is_box)

sense_box = SensingAction("sense_box", _env=env2)
sense_box.add_observed_fluent(is_box())

pick_box = InstantaneousAction("pick_box", _env=env2)
pick_box.add_precondition(is_box())
pick_box.add_effect(delivered, True)

pick_bag = InstantaneousAction("pick_bag", _env=env2)
pick_bag.add_precondition(env2.expression_manager.Not(is_box()))
pick_bag.add_effect(delivered, True)

problem2.add_actions([sense_box, pick_box, pick_bag])
problem2.add_goal(delivered())

env2.factory.add_engine("demo-action-selector", __name__, "DemoActionSelector")
execution_env = SimulatedExecutionEnvironment(problem2, max_constraints=1)

selected_actions = []
with env2.factory.ActionSelector(
    problem2,
    name="demo-action-selector",
    params={
        "default_action": "sense_box",
        "true_action": "pick_box",
        "false_action": "pick_bag",
    },
) as selector:
    for _ in range(2):
        action_instance = selector.get_action()
        selected_actions.append(action_instance.action.name)
        print("Selected action:", action_instance)
        observation = execution_env.apply(action_instance)
        print("Observation:", observation)
        selector.update(observation)
        if execution_env.is_goal_reached():
            break

assert selected_actions[0] == "sense_box"
assert len(selected_actions) == 2
assert selected_actions[1] in ("pick_box", "pick_bag")
assert execution_env.is_goal_reached()
print("Goal reached:", execution_env.is_goal_reached())

# [execution-environment-flow-end]
