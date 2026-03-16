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


import warnings
from unittest.mock import Mock, patch
from typing import Dict, List
import unified_planning as up
import unified_planning.shortcuts as shortcuts
from unified_planning.environment import Environment
from unified_planning.engines import OperationMode, UPSequentialSimulator
from unified_planning.engines.engine import Engine
from unified_planning.engines.mixins.action_selector import ActionSelectorMixin
from unified_planning.exceptions import UPUsageError
from unified_planning.model import Fluent, InstantaneousAction, Problem, ProblemKind
from unified_planning.test import unittest_TestCase, main


class DummyActionSelector(Engine, ActionSelectorMixin):
    def __init__(self, problem: Problem, error_on_failed_checks=True, **kwargs):
        Engine.__init__(self)
        self.error_on_failed_checks = error_on_failed_checks
        self.get_action_calls = 0
        self.update_calls: List[Dict[up.model.FNode, up.model.FNode]] = []
        self._switch_policy = False
        self._actions_by_name = {action.name: action for action in problem.actions}
        ActionSelectorMixin.__init__(self, problem)

    @property
    def name(self):
        return "dummy-action-selector"

    @staticmethod
    def supported_kind() -> ProblemKind:
        return ProblemKind()

    @staticmethod
    def supports(problem_kind: ProblemKind) -> bool:
        return True

    def _get_action(self):
        self.get_action_calls += 1
        selected_name = "set_false" if self._switch_policy else "set_true"
        return self._actions_by_name[selected_name]()

    def _update(self, observation):
        self.update_calls.append(observation)
        self._switch_policy = bool(observation)


class UnsupportedActionSelector(Engine, ActionSelectorMixin):
    def __init__(self, problem, error_on_failed_checks=True, skip_checks=False):
        Engine.__init__(self)
        self.error_on_failed_checks = error_on_failed_checks
        self.skip_checks = skip_checks
        ActionSelectorMixin.__init__(self, problem)

    @property
    def name(self):
        return "unsupported-action-selector"

    @staticmethod
    def supported_kind() -> ProblemKind:
        return ProblemKind()

    @staticmethod
    def supports(problem_kind: ProblemKind) -> bool:
        return False


class MinimalActionSelector(Engine, ActionSelectorMixin):
    def __init__(self, problem, error_on_failed_checks=True, skip_checks=True):
        Engine.__init__(self)
        self.error_on_failed_checks = error_on_failed_checks
        self.skip_checks = skip_checks
        ActionSelectorMixin.__init__(self, problem)

    @property
    def name(self):
        return "minimal-action-selector"

    @staticmethod
    def supported_kind() -> ProblemKind:
        return ProblemKind()

    @staticmethod
    def supports(problem_kind: ProblemKind) -> bool:
        return True


class TestActionSelector(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.env = Environment()
        self.problem = Problem("action_selector_problem", self.env)
        self.flag = Fluent("flag", environment=self.env)
        self.problem.add_fluent(self.flag, default_initial_value=False)
        set_true = InstantaneousAction("set_true", _env=self.env)
        set_true.add_effect(self.flag, True)
        set_false = InstantaneousAction("set_false", _env=self.env)
        set_false.add_effect(self.flag, False)
        self.problem.add_actions([set_true, set_false])

    def test_operation_mode_contains_action_selector(self):
        self.assertEqual(OperationMode.ACTION_SELECTOR.value, "action_selector")

    def test_factory_action_selector_calls_get_engine_with_expected_arguments(self):
        expected = object()
        with patch.object(self.env.factory, "_get_engine", return_value=expected) as p:
            res = self.env.factory.ActionSelector(
                self.problem, name="dummy", params={"k": "v"}
            )
        self.assertIs(res, expected)
        p.assert_called_once_with(
            OperationMode.ACTION_SELECTOR,
            "dummy",
            None,
            {"k": "v"},
            self.problem.kind,
            problem=self.problem,
        )

    def test_shortcut_action_selector_delegates_to_factory(self):
        env_mock = Mock()
        expected = object()
        env_mock.factory.ActionSelector.return_value = expected
        with patch.object(shortcuts, "get_environment", return_value=env_mock):
            res = shortcuts.ActionSelector(
                problem=self.problem, name="dummy", params={"a": "b"}
            )
        self.assertIs(res, expected)
        env_mock.factory.ActionSelector.assert_called_once_with(
            problem=self.problem, name="dummy", params={"a": "b"}
        )

    def test_factory_returns_dummy_action_selector_named_and_unnamed(self):
        self.env.factory.add_engine(
            "dummy-action-selector", __name__, "DummyActionSelector"
        )
        self.env.factory.preference_list = ["dummy-action-selector"]

        named = self.env.factory.ActionSelector(
            self.problem, name="dummy-action-selector"
        )
        self.assertIsInstance(named, DummyActionSelector)
        self.assertFalse(named.error_on_failed_checks)

        unnamed = self.env.factory.ActionSelector(self.problem)
        self.assertIsInstance(unnamed, DummyActionSelector)
        self.assertTrue(unnamed.error_on_failed_checks)

    def test_action_selector_typical_flow_observation_changes_selected_action(self):
        selector = DummyActionSelector(self.problem, skip_checks=True)
        simulator = UPSequentialSimulator(self.problem)

        state = simulator.get_initial_state()
        first_action = selector.get_action()
        first_state = simulator.apply(state, first_action)
        self.assertIsNotNone(first_state)
        if first_state is None:
            self.fail("Expected the first action to be applicable.")
        state = first_state
        self.assertTrue(state.get_value(self.flag()).bool_constant_value())

        selector.update(
            {self.flag(): self.problem.environment.expression_manager.TRUE()}
        )
        second_action = selector.get_action()
        second_state = simulator.apply(state, second_action)
        self.assertIsNotNone(second_state)
        if second_state is None:
            self.fail("Expected the second action to be applicable.")
        state = second_state
        self.assertFalse(state.get_value(self.flag()).bool_constant_value())

    def test_action_selector_edge_case_empty_observation_does_not_switch_policy(self):
        selector = DummyActionSelector(self.problem, skip_checks=True)
        first_action = selector.get_action()
        selector.update({})
        second_action = selector.get_action()
        self.assertEqual(first_action.action.name, "set_true")
        self.assertEqual(second_action.action.name, "set_true")

    def test_action_selector_update_records_expected_inputs(self):
        selector = DummyActionSelector(self.problem, skip_checks=True)
        obs = {self.flag(): self.problem.environment.expression_manager.FALSE()}
        selector.update(obs)
        self.assertEqual(selector.update_calls, [obs])

    def test_action_selector_init_unsupported_problem_raises_usage_error(self):
        with self.assertRaises(UPUsageError):
            UnsupportedActionSelector(self.problem)

    def test_action_selector_init_unsupported_problem_warns_when_errors_disabled(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            UnsupportedActionSelector(self.problem, error_on_failed_checks=False)
        self.assertEqual(len(caught), 1)
        self.assertIn("able to handle this problem", str(caught[0].message))

    def test_action_selector_init_skips_support_check_when_skip_checks_true(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            selector = UnsupportedActionSelector(
                self.problem, error_on_failed_checks=True, skip_checks=True
            )
        self.assertIsInstance(selector, UnsupportedActionSelector)
        self.assertEqual(len(caught), 0)

    def test_action_selector_default_methods_raise_not_implemented(self):
        selector = MinimalActionSelector(self.problem)
        with self.assertRaises(NotImplementedError):
            selector.get_action()
        with self.assertRaises(NotImplementedError):
            selector.update({})

    def test_is_action_selector_static_flag_is_true(self):
        self.assertTrue(DummyActionSelector.is_action_selector())


if __name__ == "__main__":
    main()
