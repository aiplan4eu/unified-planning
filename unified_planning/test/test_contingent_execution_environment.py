# Copyright 2021-2023 AIPlan4EU project
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


from unittest.mock import Mock, patch
import unified_planning as up
from unified_planning.exceptions import UPUsageError
from unified_planning.model import (
    Fluent,
    InstantaneousAction,
    Problem,
    State,
    generate_causal_graph,
)
from unified_planning.model.contingent import (
    ContingentProblem,
    ExecutionEnvironment,
    SensingAction,
    SimulatedExecutionEnvironment,
)
from unified_planning.model.contingent.ExecutionEnvironment import all_smt
from unified_planning.test import (
    main,
    skipIfModuleNotInstalled,
    unittest_TestCase,
)


class _FakeBool:
    def __init__(self, value: bool):
        self._value = value

    def is_bool_constant(self) -> bool:
        return True

    def is_true(self) -> bool:
        return self._value


class _FakeSequentialSimulator:
    def __init__(self, problem, error_on_failed_checks=True):
        self.problem = problem
        self.error_on_failed_checks = error_on_failed_checks
        self._state = object()

    def get_initial_state(self):
        return self._state


class TestContingentExecutionEnvironment(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problem = ContingentProblem("contingent_problem")
        self.flag = Fluent("flag", environment=self.problem.environment)
        self.problem.add_fluent(self.flag, default_initial_value=False)

    def _fresh_state(self) -> State:
        return up.engines.UPSequentialSimulator(self.problem, False).get_initial_state()

    def test_execution_environment_base_methods_raise_not_implemented(self):
        env = ExecutionEnvironment(self.problem)
        with self.assertRaises(NotImplementedError):
            env.apply(None)  # type: ignore[arg-type]
        with self.assertRaises(NotImplementedError):
            env.is_goal_reached()

    def test_problem_sensing_actions_iterator_recognizes_new_sensing_action_class(self):
        simple_problem = Problem("simple_problem")
        f = Fluent("f")
        simple_problem.add_fluent(f, default_initial_value=False)
        sensing = SensingAction("sense")
        sensing.add_observed_fluent(f())
        normal = InstantaneousAction("flip")
        normal.add_effect(f, True)
        simple_problem.add_actions([sensing, normal])

        sensing_actions = list(simple_problem.sensing_actions)
        self.assertEqual(len(sensing_actions), 1)
        self.assertIs(sensing_actions[0], sensing)
        self.assertIsInstance(sensing_actions[0], SensingAction)

    def test_problem_kind_marks_contingent_when_new_sensing_action_is_added(self):
        simple_problem = Problem("simple_problem")
        f = Fluent("f")
        simple_problem.add_fluent(f, default_initial_value=False)
        sensing = SensingAction("sense")
        sensing.add_observed_fluent(f())
        simple_problem.add_action(sensing)
        self.assertTrue(simple_problem.kind.has_contingent())

    def test_generate_causal_graph_rejects_contingent_problem(self):
        with self.assertRaises(NotImplementedError):
            generate_causal_graph(self.problem)

    def test_contingent_problem_initial_values_include_known_and_exclude_hidden(self):
        visible = Fluent("visible", environment=self.problem.environment)
        hidden = Fluent("hidden", environment=self.problem.environment)
        self.problem.add_fluent(visible, default_initial_value=False)
        self.problem.add_fluent(hidden, default_initial_value=True)
        self.problem.set_initial_value(visible, True)
        self.problem.add_unknown_initial_constraint(hidden)

        values = self.problem.initial_values
        self.assertIn(visible(), values)
        self.assertTrue(values[visible()].bool_constant_value())
        self.assertNotIn(hidden(), values)

    def test_simulated_execution_environment_init_wires_clone_random_init_and_simulator(
        self,
    ):
        with patch.object(
            SimulatedExecutionEnvironment,
            "_randomly_set_full_initial_state",
        ) as random_init, patch(
            "unified_planning.model.contingent.ExecutionEnvironment.up.engines.UPSequentialSimulator",
            new=_FakeSequentialSimulator,
        ):
            env = SimulatedExecutionEnvironment(self.problem)
        self.assertIsNot(env._deterministic_problem, self.problem)
        self.assertEqual(env._max_constraints, float("inf"))
        self.assertIs(env._state, env._simulator.get_initial_state())
        self.assertFalse(env._simulator.error_on_failed_checks)
        self.assertEqual(random_init.call_count, 1)

    def test_simulated_execution_environment_init_respects_max_constraints_argument(
        self,
    ):
        with patch.object(
            SimulatedExecutionEnvironment,
            "_randomly_set_full_initial_state",
        ), patch(
            "unified_planning.model.contingent.ExecutionEnvironment.up.engines.UPSequentialSimulator",
            new=_FakeSequentialSimulator,
        ):
            env = SimulatedExecutionEnvironment(self.problem, max_constraints=3)
        self.assertEqual(env._max_constraints, 3)

    def test_simulated_apply_raises_when_action_not_applicable(self):
        action = InstantaneousAction("noop", _env=self.problem.environment)
        ai = up.plans.ActionInstance(action)
        env = SimulatedExecutionEnvironment(self.problem)
        env._simulator = Mock()
        env._simulator.apply.return_value = None
        env._state = self._fresh_state()

        with self.assertRaises(UPUsageError):
            env.apply(ai)

    def test_simulated_apply_returns_empty_observation_for_non_sensing_action(self):
        action = InstantaneousAction("noop", _env=self.problem.environment)
        ai = up.plans.ActionInstance(action)
        old_state = self._fresh_state()
        new_state = self._fresh_state()
        env = SimulatedExecutionEnvironment(self.problem)
        env._simulator = Mock()
        env._simulator.apply.return_value = new_state
        observation = env.apply(ai)
        self.assertEqual(observation, {})
        self.assertIs(env._state, new_state)
        env._simulator.apply.assert_called_once_with(old_state, action, tuple())

    def test_simulated_apply_returns_observation_for_sensing_action_and_substitutes_parameters(
        self,
    ):
        bounded = self.problem.environment.type_manager.IntType(0, 1)
        seen = Fluent("seen", environment=self.problem.environment, i=bounded)
        self.problem.add_fluent(seen, default_initial_value=False)
        action = SensingAction("sense", _env=self.problem.environment, i=bounded)
        action.add_observed_fluent(seen(action.parameter("i")))
        ai = up.plans.ActionInstance(
            action, (self.problem.environment.expression_manager.Int(1),)
        )
        expected_key = seen(self.problem.environment.expression_manager.Int(1))

        new_state = Mock()
        new_state.get_value.return_value = (
            self.problem.environment.expression_manager.TRUE()
        )
        env = SimulatedExecutionEnvironment(self.problem)
        env._deterministic_problem.add_action(action)
        env._simulator = Mock()
        env._simulator.apply.return_value = new_state
        env._state = self._fresh_state()

        observation = env.apply(ai)
        self.assertEqual(observation, {expected_key: new_state.get_value.return_value})
        new_state.get_value.assert_called_once_with(expected_key)

    def test_simulated_apply_updates_internal_state_after_success(self):
        action = InstantaneousAction("noop", _env=self.problem.environment)
        ai = up.plans.ActionInstance(action)
        new_state = self._fresh_state()
        env = SimulatedExecutionEnvironment(self.problem)
        env._simulator = Mock()
        env._simulator.apply.return_value = new_state
        env._state = self._fresh_state()

        env.apply(ai)
        self.assertIs(env._state, new_state)

    def test_simulated_is_goal_reached_delegates_to_simulator(self):
        state = self._fresh_state()
        env = SimulatedExecutionEnvironment(self.problem)
        env._state = state
        env._simulator = Mock()
        env._simulator.is_goal.return_value = True

        self.assertTrue(env.is_goal_reached())
        env._simulator.is_goal.assert_called_once_with(state)

    def test_randomly_set_full_initial_state_applies_model_assignments(self):
        hidden = Fluent("hidden", environment=self.problem.environment)
        self.problem.add_fluent(hidden, default_initial_value=False)
        self.problem.add_unknown_initial_constraint(hidden)
        env = SimulatedExecutionEnvironment(self.problem)
        env._max_constraints = float("inf")

        def fake_all_smt(formula, keys):
            yield {k: _FakeBool(True) for k in keys}

        with patch(
            "unified_planning.model.contingent.ExecutionEnvironment.all_smt",
            side_effect=fake_all_smt,
        ) as p_all_smt, patch(
            "unified_planning.model.contingent.ExecutionEnvironment.random.choice",
            side_effect=lambda models: models[0],
        ):
            env._randomly_set_full_initial_state(self.problem)
        hidden_initial_value = env._deterministic_problem.initial_value(hidden())
        self.assertIsNotNone(hidden_initial_value)
        if hidden_initial_value is None:
            self.fail("Expected a concrete initial value for hidden fluent.")
        self.assertTrue(hidden_initial_value.bool_constant_value())
        self.assertEqual(p_all_smt.call_count, 1)

    @skipIfModuleNotInstalled("pysmt")
    def test_all_smt_enumerates_models_for_sat_formula(self):
        from pysmt.shortcuts import Or, Symbol

        x = Symbol("x")
        y = Symbol("y")
        models = list(all_smt(Or(x, y), [x, y]))
        model_values = {(m[x].is_true(), m[y].is_true()) for m in models}
        self.assertEqual(len(models), 3)
        self.assertEqual(model_values, {(True, False), (False, True), (True, True)})

    @skipIfModuleNotInstalled("pysmt")
    def test_all_smt_returns_empty_for_unsat_formula(self):
        from pysmt.shortcuts import And, Not, Symbol

        x = Symbol("x")
        self.assertEqual(len(list(all_smt(And(x, Not(x)), [x]))), 0)

    def test_model_contingent_namespace_exports_expected_classes(self):
        self.assertTrue(hasattr(up.model, "contingent"))
        self.assertTrue(hasattr(up.model.contingent, "ContingentProblem"))
        self.assertTrue(hasattr(up.model.contingent, "SensingAction"))
        cp = up.model.contingent.ContingentProblem("cp")
        sa = up.model.contingent.SensingAction("sense", _env=cp.environment)
        self.assertIsInstance(cp, ContingentProblem)
        self.assertIsInstance(sa, SensingAction)


if __name__ == "__main__":
    main()
