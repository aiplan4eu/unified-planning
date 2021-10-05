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
#

import upf
import upf.types
from upf.action import ActionInterface, ActionParameter
from upf.environment import Environment
from upf.fnode import FNode
from upf.exceptions import UPFTypeError
from upf.expression import BoolExpression, Expression
from upf.effect import Effect, INCREASE, DECREASE
from fractions import Fraction
from typing import List, Union, Dict
from collections import OrderedDict


class Timing:
    def __init__(self, bound: Union[int, Fraction]):
        self._bound = bound

    def bound(self):
        return self._bound

    def is_from_start(self):
        raise NotImplementedError

    def is_from_end(self):
        raise NotImplementedError


class StartTiming(Timing):
    def __init__(self, bound: Union[int, Fraction] = 0):
        Timing.__init__(self, bound)

    def is_from_start(self):
        return True

    def is_from_end(self):
        return False


class EndTiming(Timing):
    def __init__(self, bound: Union[int, Fraction] = 0):
        Timing.__init__(self, bound)

    def is_from_start(self):
        return False

    def is_from_end(self):
        return True


class ConstantTiming(Timing):
    def __init__(self, bound: Union[int, Fraction]):
        Timing.__init__(self, bound)

    def is_from_start(self):
        return False

    def is_from_end(self):
        return False


class Interval:
    def __init__(self, lower: Timing, upper: Timing):
        self._lower = lower
        self._upper = upper

    def lower(self):
        return self._lower

    def upper(self):
        return self._upper

    def is_left_open(self):
        raise NotImplementedError

    def is_right_open(self):
        raise NotImplementedError


class CloseInterval(Interval):
    def __init__(self, lower: Timing, upper: Timing):
        Interval.__init__(self, lower, upper)

    def is_left_open(self):
        return False

    def is_right_open(self):
        return False


class PointInterval(CloseInterval):
    def __init__(self, size: Timing):
        CloseInterval.__init__(self, size, size)


class OpenInterval(Interval):
    def __init__(self, lower: Timing, upper: Timing):
        Interval.__init__(self, lower, upper)

    def is_left_open(self):
        return True

    def is_right_open(self):
        return True


class LeftOpenInterval(Interval):
    def __init__(self, lower: Timing, upper: Timing):
        Interval.__init__(self, lower, upper)

    def is_left_open(self):
        return True

    def is_right_open(self):
        return False


class RightOpenInterval(Interval):
    def __init__(self, lower: Timing, upper: Timing):
        Interval.__init__(self, lower, upper)

    def is_left_open(self):
        return False

    def is_right_open(self):
        return True


class DurativeAction(ActionInterface):
    """Represents a durative action."""
    def __init__(self, _name: str, _parameters: 'OrderedDict[str, upf.types.Type]' = None,
                 _env: Environment = None, **kwargs: upf.types.Type):
        ActionInterface.__init__(self, _name, _parameters, _env, **kwargs)
        self._duration: Interval = PointInterval(ConstantTiming(0))
        self._conditions: Dict[Timing, List[FNode]] = {}
        self._durative_conditions: Dict[Interval, List[FNode]] = {}
        self._effects: Dict[Timing, List[Effect]] = {}

    def duration(self):
        """Returns the action duration interval."""
        return self._duration

    def conditions(self):
        """Returns the action conditions."""
        return self._conditions

    def durative_conditions(self):
        """Returns the action durative conditions."""
        return self._durative_conditions

    def effects(self):
        """Returns the action effects."""
        return self._effects

    def conditional_effects(self):
        """Return the action conditional effects."""
        retval: Dict[Timing, List[Effect]] = {}
        for timing, effect_list in self._effects.items():
            cond_effect_list = [e for e in effect_list if e.is_conditional()]
            if len(cond_effect_list) > 0:
                retval[timing] = cond_effect_list
        return retval

    def unconditional_effects(self):
        """Return the action unconditional effects."""
        retval: Dict[Timing, List[Effect]] = {}
        for timing, effect_list in self._effects.items():
            uncond_effect_list = [e for e in effect_list if not e.is_conditional()]
            if len(uncond_effect_list) > 0:
                retval[timing] = uncond_effect_list
        return retval

    def is_conditional(self) -> bool:
        """Returns True if the action has conditional effects."""
        return any(e.is_conditional() for t, l in self._effects.items() for e in l)

    def set_duration_constraint(self, interval: Interval):
        """Sets the duration interval."""
        self._duration = interval

    def add_condition(self, timing: Timing,
                      condition: Union[FNode, 'upf.Fluent', ActionParameter, bool]):
        """Adds the given condition."""
        condition_exp, = self._env.expression_manager.auto_promote(condition)
        assert self._env.type_checker.get_type(condition_exp).is_bool_type()
        if timing in self._conditions:
            self._conditions[timing].append(condition_exp)
        else:
            self._conditions[timing] = [condition_exp]

    def add_durative_condition(self, interval: Interval,
                               condition: Union[FNode, 'upf.Fluent', ActionParameter, bool]):
        """Adds the given durative condition."""
        condition_exp, = self._env.expression_manager.auto_promote(condition)
        assert self._env.type_checker.get_type(condition_exp).is_bool_type()
        if interval in self._durative_conditions:
            self._durative_conditions[interval].append(condition_exp)
        else:
            self._durative_conditions[interval] = [condition_exp]

    def add_effect(self, timing: Timing, fluent: Union[FNode, 'upf.Fluent'],
                   value: Expression, condition: BoolExpression = True):
        """Adds the given action effect."""
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Action effect has not compatible types!')
        self._add_effect_instance(timing, Effect(fluent_exp, value_exp, condition_exp))

    def add_increase_effect(self, timing: Timing, fluent: Union[FNode, 'upf.Fluent'],
                            value: Expression, condition: BoolExpression = True):
        """Adds the given action increase effect."""
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Action effect has not compatible types!')
        self._add_effect_instance(timing,
                                  Effect(fluent_exp, value_exp,
                                         condition_exp, kind = INCREASE))

    def add_decrease_effect(self, timing: Timing, fluent: Union[FNode, 'upf.Fluent'],
                            value: Expression, condition: BoolExpression = True):
        """Adds the given action decrease effect."""
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Action effect has not compatible types!')
        self._add_effect_instance(timing,
                                  Effect(fluent_exp, value_exp,
                                         condition_exp, kind = DECREASE))

    def _add_effect_instance(self, timing: Timing, effect: Effect):
        if timing in self._effects:
            self._effects[timing].append(effect)
        else:
            self._effects[timing] = [effect]
