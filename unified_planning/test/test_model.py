# Copyright 2021 AIPlan4EU project
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


import unified_planning
from unified_planning.shortcuts import *
from unified_planning.exceptions import (
    UPUsageError,
    UPTypeError,
    UPConflictingEffectsException,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.test import TestCase, main


class TestModel(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_expression(self):
        test_type = UserType("test_type")
        identity = Fluent("identity", test_type, obj=test_type)
        id = Fluent("id", test_type, obj_id=IntType())
        self.assertEqual(id(1).type, test_type)
        env_2 = up.environment.Environment()
        test_type_2 = env_2.type_manager.UserType("test_type")
        it_2 = env_2.type_manager.IntType()
        id_2 = Fluent("id", test_type_2, obj_id=it_2, environment=env_2)
        obj_2 = Object("obj", test_type_2, env_2)
        self.assertEqual(id_2(1).type, test_type_2)
        self.assertNotEqual(id_2(1).type, test_type)
        with self.assertRaises(AssertionError) as e:
            Equals(id_2(1), obj_2)
        self.assertEqual(
            str(e.exception),
            "Expression has a different environment of the expression manager",
        )
        with self.assertRaises(AssertionError) as e:
            identity(obj_2)
        self.assertEqual(
            str(e.exception),
            "Object has a different environment of the expression manager",
        )
        with self.assertRaises(AssertionError) as e:
            Object("obj", test_type_2)
        self.assertEqual(
            str(e.exception),
            "type of the object does not belong to the same environment of the object",
        )

    def test_clone_problem_and_action(self):
        for _, (problem, _) in self.problems.items():
            problem_clone_1 = problem.clone()
            problem_clone_2 = problem.clone()
            for action_1, action_2 in zip(
                problem_clone_1.actions, problem_clone_2.actions
            ):
                if isinstance(action_2, InstantaneousAction):
                    action_2._effects = []
                    action_1_clone = action_1.clone()
                    action_1_clone._effects = []
                elif isinstance(action_2, DurativeAction):
                    action_2._effects = {}
                    action_1_clone = action_1.clone()
                    action_1_clone._effects = {}
                else:
                    raise NotImplementedError
                self.assertEqual(action_2, action_1_clone)
                self.assertEqual(action_1_clone, action_2)
                self.assertNotEqual(action_1, action_1_clone)
                self.assertNotEqual(action_1_clone, action_1)
                self.assertNotEqual(action_1, action_1_clone.name)
                self.assertNotEqual(action_1_clone.name, action_1)
            self.assertEqual(problem_clone_1, problem)
            self.assertEqual(problem, problem_clone_1)
            self.assertNotEqual(problem_clone_2, problem)
            self.assertNotEqual(problem, problem_clone_2)

    def test_clone_action(self):
        Location = UserType("Location")
        a = Action("move", l_from=Location, l_to=Location)
        with self.assertRaises(NotImplementedError):
            a.clone()
        with self.assertRaises(NotImplementedError):
            hash(a)
        with self.assertRaises(NotImplementedError):
            a == a.name
        with self.assertRaises(NotImplementedError):
            a.is_conditional()

    def test_clone_effect(self):
        x = FluentExp(Fluent("x"))
        y = FluentExp(Fluent("y"))
        z = FluentExp(Fluent("z"))
        e = Effect(x, z, y, unified_planning.model.EffectKind.ASSIGN)
        e_clone_1 = e.clone()
        e_clone_2 = e.clone()
        e_clone_2._condition = TRUE()
        self.assertEqual(e_clone_1, e)
        self.assertEqual(e, e_clone_1)
        self.assertNotEqual(e_clone_2, e)
        self.assertNotEqual(e, e_clone_2)
        self.assertNotEqual(e, e.value)
        self.assertNotEqual(e.value, e)

    def test_istantaneous_action(self):
        Location = UserType("Location")
        move = InstantaneousAction("move", l_from=Location, l_to=Location)
        km = Fluent("km", IntType())
        move.add_increase_effect(km, 10)
        e = Effect(
            FluentExp(km), Int(10), TRUE(), unified_planning.model.EffectKind.INCREASE
        )
        self.assertEqual(move.effects[0], e)

        # variables used to test exceptions
        Utl1 = UserType("UserTypeL1")
        Utl2 = UserType("UserTypeL2")
        is_at = Fluent("is_at", BoolType(), obj=Utl1)
        int_fluent = Fluent("int", IntType())
        test_exceptions = InstantaneousAction("test_exceptions")
        l1 = ObjectExp(Object("l1", Utl1))
        l2 = ObjectExp(Object("l2", Utl2))

        # test add_effect exceptions
        with self.assertRaises(UPUsageError) as usage_error:
            test_exceptions.add_effect(l1, l2)
        self.assertEqual(
            str(usage_error.exception),
            "fluent field of add_effect must be a Fluent or a FluentExp",
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_effect(is_at(l1), l2, l1)
        self.assertEqual(
            str(type_error.exception), "Effect condition is not a Boolean condition!"
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_effect(is_at(l1), l2)
        self.assertEqual(
            str(type_error.exception),
            f"InstantaneousAction effect has an incompatible value type. Fluent type: {is_at(l1).type} // Value type: {l2.type}",
        )
        test_exceptions.add_effect(int_fluent, 5)
        test_exceptions.add_effect(int_fluent, 5)
        with self.assertRaises(UPConflictingEffectsException) as conf_error:
            test_exceptions.add_effect(int_fluent, 6)
        effect = Effect(int_fluent(), Int(6), TRUE())
        self.assertEqual(
            str(conf_error.exception),
            f"The effect {effect} is in conflict with the effects already in the action.",
        )

        # test add_increase_effect exceptions
        with self.assertRaises(UPUsageError) as usage_error:
            test_exceptions.add_increase_effect(l1, l2)
        self.assertEqual(
            str(usage_error.exception),
            "fluent field of add_increase_effect must be a Fluent or a FluentExp",
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_increase_effect(is_at(l1), l2, l1)
        self.assertEqual(
            str(type_error.exception), "Effect condition is not a Boolean condition!"
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_increase_effect(is_at(l1), l2)
        self.assertEqual(
            str(type_error.exception),
            f"InstantaneousAction effect has an incompatible value type. Fluent type: {is_at(l1).type} // Value type: {l2.type}",
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_increase_effect(is_at(l1), True)
        self.assertEqual(
            str(type_error.exception),
            "Increase effects can be created only on numeric types!",
        )
        with self.assertRaises(UPConflictingEffectsException) as conf_error:
            test_exceptions.add_increase_effect(int_fluent, 6)
        effect = Effect(int_fluent(), Int(6), TRUE(), EffectKind.INCREASE)
        self.assertEqual(
            str(conf_error.exception),
            f"The effect {effect} is in conflict with the effects already in the action.",
        )
        test_exceptions.clear_effects()
        test_exceptions.add_increase_effect(int_fluent, 6)
        sim_eff = SimulatedEffect([int_fluent()], lambda x, y, z: [Int(6)])
        with self.assertRaises(UPConflictingEffectsException) as conf_error:
            test_exceptions.set_simulated_effect(sim_eff)
        self.assertEqual(
            str(conf_error.exception),
            f"The simulated effect {sim_eff} is in conflict with the effects already in the action.",
        )

        # test add_decrease_effect exceptions
        with self.assertRaises(UPUsageError) as usage_error:
            test_exceptions.add_decrease_effect(l1, l2)
        self.assertEqual(
            str(usage_error.exception),
            "fluent field of add_decrease_effect must be a Fluent or a FluentExp",
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_decrease_effect(is_at(l1), l2, l1)
        self.assertEqual(
            str(type_error.exception), "Effect condition is not a Boolean condition!"
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_decrease_effect(is_at(l1), l2)
        self.assertEqual(
            str(type_error.exception),
            f"InstantaneousAction effect has an incompatible value type. Fluent type: {is_at(l1).type} // Value type: {l2.type}",
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_decrease_effect(is_at(l1), True)
        self.assertEqual(
            str(type_error.exception),
            "Decrease effects can be created only on numeric types!",
        )

    def test_durative_action(self):
        Location = UserType("Location")
        x = Fluent("x")
        move = DurativeAction("move", l_from=Location, l_to=Location)
        km = Fluent("km", IntType())
        move.add_decrease_effect(StartTiming(), km, 5)
        move.add_increase_effect(EndTiming(), km, 20)
        e_end = Effect(
            FluentExp(km), Int(20), TRUE(), unified_planning.model.EffectKind.INCREASE
        )
        e_start = Effect(
            FluentExp(km), Int(5), TRUE(), unified_planning.model.EffectKind.DECREASE
        )
        effects_test = {StartTiming(): [e_start], EndTiming(): [e_end]}
        self.assertEqual(effects_test, move.effects)
        move.set_closed_duration_interval(1, 2)
        self.assertEqual(move.duration, ClosedDurationInterval(Int(1), Int(2)))
        move.set_open_duration_interval(2, Fraction(7, 2))
        self.assertEqual(
            move.duration, OpenDurationInterval(Int(2), Real(Fraction(7, 2)))
        )
        move.set_left_open_duration_interval(1, 2)
        self.assertEqual(move.duration, LeftOpenDurationInterval(Int(1), Int(2)))
        move.set_right_open_duration_interval(1, 2)
        self.assertEqual(move.duration, RightOpenDurationInterval(Int(1), Int(2)))
        move.add_condition(StartTiming(), x)
        move.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), x)
        self.assertIn("duration = [1, 2)", str(move))

        # variables used to test exceptions
        Utl1 = UserType("UserTypeL1")
        Utl2 = UserType("UserTypeL2")
        is_at = Fluent("is_at", BoolType(), obj=Utl1)
        int_fluent = Fluent("int", IntType())
        test_exceptions = DurativeAction("test_exceptions")
        l1 = ObjectExp(Object("l1", Utl1))
        l2 = ObjectExp(Object("l2", Utl2))
        t = StartTiming()

        # test add_effect exceptions
        with self.assertRaises(UPUsageError) as usage_error:
            test_exceptions.add_effect(t, l1, l2)
        self.assertEqual(
            str(usage_error.exception),
            "fluent field of add_effect must be a Fluent or a FluentExp",
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_effect(t, is_at(l1), l2, l1)
        self.assertEqual(
            str(type_error.exception), "Effect condition is not a Boolean condition!"
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_effect(t, is_at(l1), l2)
        self.assertEqual(
            str(type_error.exception),
            f"DurativeAction effect has an incompatible value type. Fluent type: {is_at(l1).type} // Value type: {l2.type}",
        )
        test_exceptions.add_effect(t, int_fluent, 5)
        test_exceptions.add_effect(t, int_fluent, 5)
        with self.assertRaises(UPConflictingEffectsException) as conf_error:
            test_exceptions.add_effect(t, int_fluent, 6)
        effect = Effect(int_fluent(), Int(6), TRUE())
        self.assertEqual(
            str(conf_error.exception),
            f"The effect {effect} at timing {t} is in conflict with the effects already in the action or problem: test_exceptions.",
        )

        # test add_increase_effect exceptions
        with self.assertRaises(UPUsageError) as usage_error:
            test_exceptions.add_increase_effect(t, l1, l2)
        self.assertEqual(
            str(usage_error.exception),
            "fluent field of add_increase_effect must be a Fluent or a FluentExp",
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_increase_effect(t, is_at(l1), l2, l1)
        self.assertEqual(
            str(type_error.exception), "Effect condition is not a Boolean condition!"
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_increase_effect(t, is_at(l1), l2)
        self.assertEqual(
            str(type_error.exception),
            f"DurativeAction effect has an incompatible value type. Fluent type: {is_at(l1).type} // Value type: {l2.type}",
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_increase_effect(t, is_at(l1), True)
        self.assertEqual(
            str(type_error.exception),
            "Increase effects can be created only on numeric types!",
        )
        with self.assertRaises(UPConflictingEffectsException) as conf_error:
            test_exceptions.add_increase_effect(t, int_fluent, 6)
        effect = Effect(int_fluent(), Int(6), TRUE(), EffectKind.INCREASE)
        self.assertEqual(
            str(conf_error.exception),
            f"The effect {effect} at timing {t} is in conflict with the effects already in the action or problem: test_exceptions.",
        )
        test_exceptions.clear_effects()
        test_exceptions.add_increase_effect(t, int_fluent, 6)
        sim_eff = SimulatedEffect([int_fluent()], lambda x, y, z: [Int(6)])
        with self.assertRaises(UPConflictingEffectsException) as conf_error:
            test_exceptions.set_simulated_effect(t, sim_eff)
        self.assertEqual(
            str(conf_error.exception),
            f"The simulated effect {sim_eff} at timing {t} is in conflict with the effects already in the action or problem: test_exceptions.",
        )

        # test add_decrease_effect exceptions
        with self.assertRaises(UPUsageError) as usage_error:
            test_exceptions.add_decrease_effect(t, l1, l2)
        self.assertEqual(
            str(usage_error.exception),
            "fluent field of add_decrease_effect must be a Fluent or a FluentExp",
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_decrease_effect(t, is_at(l1), l2, l1)
        self.assertEqual(
            str(type_error.exception), "Effect condition is not a Boolean condition!"
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_decrease_effect(t, is_at(l1), l2)
        self.assertEqual(
            str(type_error.exception),
            f"DurativeAction effect has an incompatible value type. Fluent type: {is_at(l1).type} // Value type: {l2.type}",
        )
        with self.assertRaises(UPTypeError) as type_error:
            test_exceptions.add_decrease_effect(t, is_at(l1), True)
        self.assertEqual(
            str(type_error.exception),
            "Decrease effects can be created only on numeric types!",
        )

    def test_problem(self):
        x = Fluent("x")
        y = Fluent("y")
        km = Fluent("km", IntType())
        problem = Problem("problem_test")
        problem.add_fluent(x, default_initial_value=True)
        problem.add_fluent(y, default_initial_value=False)
        problem.add_fluent(km, default_initial_value=Int(0))
        problem.add_timed_effect(GlobalStartTiming(5), x, y)
        problem.add_timed_goal(GlobalStartTiming(11), x)
        problem.add_timed_goal(
            TimeInterval(GlobalStartTiming(5), GlobalStartTiming(9)), x
        )
        problem.add_action(DurativeAction("move"))
        problem.add_action(InstantaneousAction("stop_moving"))
        stop_moving_list = [a for a in problem.instantaneous_actions]
        self.assertEqual(len(stop_moving_list), 1)
        stop_moving = stop_moving_list[0]
        self.assertEqual(stop_moving.name, "stop_moving")
        move_list = [a for a in problem.durative_actions]
        self.assertEqual(len(move_list), 1)
        move = move_list[0]
        self.assertEqual(move.name, "move")
        problem.add_increase_effect(GlobalStartTiming(5), km, 10)
        problem.add_decrease_effect(GlobalStartTiming(10), km, 5)
        self.assertIn(
            str(
                Effect(
                    FluentExp(km),
                    Int(10),
                    TRUE(),
                    unified_planning.model.EffectKind.INCREASE,
                )
            ),
            str(problem),
        )
