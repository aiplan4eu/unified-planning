from fractions import Fraction
from typing import *

import unified_planning as up
from unified_planning import Environment
from unified_planning.environment import get_environment
from unified_planning.exceptions import UPProblemDefinitionError


class Chronicle:
    """Core structure to represent a set of timed conditions and effects."""

    def __init__(
        self,
        _name: str,
        _parameters: Optional["OrderedDict[str, up.model.types.Type]"] = None,
        _env: Optional[Environment] = None,
        **kwargs: "up.model.types.Type",
    ):

        self._duration = None
        self._env = get_environment(_env)
        self._name = _name
        self._parameters: "OrderedDict[str, up.model.parameter.Parameter]" = (
            OrderedDict()
        )
        if _parameters is not None:
            assert len(kwargs) == 0
            for n, t in _parameters.items():
                assert self._env.type_manager.has_type(
                    t
                ), "type of parameter does not belong to the same environment of the action"
                self._parameters[n] = up.model.parameter.Parameter(n, t, self._env)
        else:
            for n, t in kwargs.items():
                assert self._env.type_manager.has_type(
                    t
                ), "type of parameter does not belong to the same environment of the action"
                self._parameters[n] = up.model.parameter.Parameter(n, t, self._env)

        self._constraints: List["up.model.fnode.FNode"] = []
        self._conditions: Dict[
            "up.model.timing.TimeInterval", List["up.model.fnode.FNode"]
        ] = {}
        self._effects: Dict[
            "up.model.timing.Timing", List["up.model.effect.Effect"]
        ] = {}
        self._simulated_effects: Dict[
            "up.model.timing.Timing", "up.model.effect.SimulatedEffect"
        ] = {}
        self._fluents_assigned: Dict[
            "up.model.timing.Timing", Set["up.model.FNode"]
        ] = {}
        self._fluents_inc_dec: Dict[
            "up.model.timing.Timing", Set["up.model.FNode"]
        ] = {}

    def __repr__(self) -> str:
        s = []
        s.append(f"{self.name}")
        first = True
        for p in self.parameters:
            if first:
                s.append("(")
                first = False
            else:
                s.append(", ")
            s.append(str(p))
        if not first:
            s.append(")")
        s.append(" {\n")
        s.append(f"    duration = {str(self._duration)}\n")
        if len(self._constraints) > 0:
            s.append("    constraints = [\n")
            for c in self._constraints:
                s.append(f"      {str(c)}\n")
            s.append("    ]\n")

        if len(self.conditions) > 0:
            s.append("    conditions = [\n")
            for i, cl in self.conditions.items():
                s.append(f"      {str(i)}:\n")
                for c in cl:
                    s.append(f"        {str(c)}\n")
            s.append("    ]\n")
        if len(self.effects) > 0:
            s.append("    effects = [\n")
            for t, el in self.effects.items():
                s.append(f"      {str(t)}:\n")
                for e in el:
                    s.append(f"        {str(e)}:\n")
            s.append("    ]\n")
        if len(self._simulated_effects) > 0:
            s.append("    simulated effects = [\n")
            for t, se in self.simulated_effects.items():
                s.append(f"      {str(t)}: {se}\n")
            s.append("    ]\n")
        s.append("  }")
        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Chronicle):
            if (
                self._env != oth._env
                or self._name != oth._name
                or self._parameters != oth._parameters
                or self._duration != oth._duration
            ):
                return False
            if len(self._conditions) != len(oth._conditions):
                return False
            for i, cl in self._conditions.items():
                oth_cl = oth._conditions.get(i, None)
                if oth_cl is None:
                    return False
                elif set(cl) != set(oth_cl):
                    return False
            if len(self._effects) != len(oth._effects):
                return False
            for t, el in self._effects.items():
                oth_el = oth._effects.get(t, None)
                if oth_el is None:
                    return False
                elif set(el) != set(oth_el):
                    return False
            for t, se in self._simulated_effects.items():
                oth_se = oth._simulated_effects.get(t, None)
                if oth_se is None:
                    return False
                elif se != oth_se:
                    return False
            return True
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._name) + hash(self._duration)
        for ap in self._parameters.items():
            res += hash(ap)
        for i, cl in self._conditions.items():
            res += hash(i)
            for c in cl:
                res += hash(c)
        for t, el in self._effects.items():
            res += hash(t)
            for e in el:
                res += hash(e)
        for t, se in self._simulated_effects.items():
            res += hash(t) + hash(se)
        return res

    def clone(self):
        raise NotImplementedError()
        # new_params = {
        #     param_name: param.type for param_name, param in self._parameters.items()
        # }
        # new_durative_action = DurativeAction(self._name, new_params, self._env)
        # new_durative_action._duration = self._duration
        # new_durative_action._conditions = {
        #     t: cl[:] for t, cl in self._conditions.items()
        # }
        # new_durative_action._effects = {
        #     t: [e.clone() for e in el] for t, el in self._effects.items()
        # }
        # new_durative_action._simulated_effects = {
        #     t: se for t, se in self._simulated_effects.items()
        # }
        # new_durative_action._fluents_assigned = {
        #     t: fs.copy() for t, fs in self._fluents_assigned.items()
        # }
        # new_durative_action._fluents_inc_dec = {
        #     t: fs.copy() for t, fs in self._fluents_inc_dec.items()
        # }
        # return new_durative_action

    @property
    def name(self) -> str:
        """Returns the `Chronicle` `name`."""
        return self._name

    @property
    def parameters(self) -> List["up.model.parameter.Parameter"]:
        """Returns the `list` of the `Action parameters`."""
        return list(self._parameters.values())

    @property
    def duration(self) -> "up.model.timing.DurationInterval":
        """Returns the `action` `duration interval`."""
        return self._duration

    @property
    def conditions(
        self,
    ) -> Dict["up.model.timing.TimeInterval", List["up.model.fnode.FNode"]]:
        """
        Returns the `action conditions`; a map from `TimeInterval` to a `list` of `Expressions`
        indicating that for this `action` to be applicable, during the whole `TimeInterval`
        set as `key`, all the `expression` in the `mapped list` must evaluate to `True`.
        """
        return self._conditions

    def clear_conditions(self):
        """Removes all `conditions`."""
        self._conditions = {}

    @property
    def effects(self) -> Dict["up.model.timing.Timing", List["up.model.effect.Effect"]]:
        """
        Returns the all the `action's effects`; a map from `Timing` to `list` of `Effects`
        indicating that, when the action is applied, all the `Effects` must be applied at the
        `Timing` set as `key` in the map.
        """
        return self._effects

    def clear_effects(self):
        """Removes all `effects` from the `Action`."""
        self._effects = {}
        self._fluents_assigned = {}
        self._fluents_inc_dec = {}

    @property
    def conditional_effects(
        self,
    ) -> Dict["up.model.timing.Timing", List["up.model.effect.Effect"]]:
        """
        Return the `action` `conditional effects`.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible.
        """
        retval: Dict[up.model.timing.Timing, List[up.model.effect.Effect]] = {}
        for timing, effect_list in self._effects.items():
            cond_effect_list = [e for e in effect_list if e.is_conditional()]
            if len(cond_effect_list) > 0:
                retval[timing] = cond_effect_list
        return retval

    @property
    def unconditional_effects(
        self,
    ) -> Dict["up.model.timing.Timing", List["up.model.effect.Effect"]]:
        """
        Return the `action` `unconditional effects`.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible.
        """
        retval: Dict[up.model.timing.Timing, List[up.model.effect.Effect]] = {}
        for timing, effect_list in self._effects.items():
            uncond_effect_list = [e for e in effect_list if not e.is_conditional()]
            if len(uncond_effect_list) > 0:
                retval[timing] = uncond_effect_list
        return retval

    def is_conditional(self) -> bool:
        """Returns `True` if the `action` has `conditional effects`, `False` otherwise."""
        return any(e.is_conditional() for l in self._effects.values() for e in l)

    def set_duration_constraint(self, duration: "up.model.timing.DurationInterval"):
        """
        Sets the `duration interval` for this `action`.

        :param duration: The new `duration interval` of this `action`.
        """
        lower, upper = duration.lower, duration.upper
        tlower = self._env.type_checker.get_type(lower)
        tupper = self._env.type_checker.get_type(upper)
        assert tlower.is_int_type() or tlower.is_real_type()
        assert tupper.is_int_type() or tupper.is_real_type()
        if (
            lower.is_constant()
            and upper.is_constant()
            and (
                upper.constant_value() < lower.constant_value()
                or (
                    upper.constant_value() == lower.constant_value()
                    and (duration.is_left_open() or duration.is_right_open())
                )
            )
        ):
            raise UPProblemDefinitionError(
                f"{duration} is an empty interval duration of action: {self.name}."
            )
        self._duration = duration

    def set_fixed_duration(self, value: Union["up.model.fnode.FNode", int, Fraction]):
        """
        Sets the `duration interval` for this `action` as the interval `[value, value]`.

        :param value: The `value` set as both edges of this `action's duration`.
        """
        (value_exp,) = self._env.expression_manager.auto_promote(value)
        self.set_duration_constraint(up.model.timing.FixedDuration(value_exp))

    def set_closed_duration_interval(
        self,
        lower: Union["up.model.fnode.FNode", int, Fraction],
        upper: Union["up.model.fnode.FNode", int, Fraction],
    ):
        """
        Sets the `duration interval` for this `action` as the interval `[lower, upper]`.

        :param lower: The value set as the lower edge of this `action's duration`.
        :param upper: The value set as the upper edge of this `action's duration`.
        """
        lower_exp, upper_exp = self._env.expression_manager.auto_promote(lower, upper)
        self.set_duration_constraint(
            up.model.timing.ClosedDurationInterval(lower_exp, upper_exp)
        )

    def set_open_duration_interval(
        self,
        lower: Union["up.model.fnode.FNode", int, Fraction],
        upper: Union["up.model.fnode.FNode", int, Fraction],
    ):
        """
        Sets the `duration interval` for this action as the interval `]lower, upper[`.

        :param lower: The value set as the lower edge of this `action's duration`.
        :param upper: The value set as the upper edge of this `action's duration`.

        Note that `lower` and `upper` are not part of the interval.
        """
        lower_exp, upper_exp = self._env.expression_manager.auto_promote(lower, upper)
        self.set_duration_constraint(
            up.model.timing.OpenDurationInterval(lower_exp, upper_exp)
        )

    def set_left_open_duration_interval(
        self,
        lower: Union["up.model.fnode.FNode", int, Fraction],
        upper: Union["up.model.fnode.FNode", int, Fraction],
    ):
        """
        Sets the `duration interval` for this `action` as the interval `]lower, upper]`.

        :param lower: The value set as the lower edge of this `action's duration`.
        :param upper: The value set as the upper edge of this `action's duration`.

        Note that `lower` is not part of the interval.
        """
        lower_exp, upper_exp = self._env.expression_manager.auto_promote(lower, upper)
        self.set_duration_constraint(
            up.model.timing.LeftOpenDurationInterval(lower_exp, upper_exp)
        )

    def set_right_open_duration_interval(
        self,
        lower: Union["up.model.fnode.FNode", int, Fraction],
        upper: Union["up.model.fnode.FNode", int, Fraction],
    ):
        """
        Sets the `duration interval` for this `action` as the interval `[lower, upper[`.

        :param lower: The value set as the lower edge of this `action's duration`.
        :param upper: The value set as the upper edge of this `action's duration`.

        Note that `upper` is not part of the interval.
        """
        lower_exp, upper_exp = self._env.expression_manager.auto_promote(lower, upper)
        self.set_duration_constraint(
            up.model.timing.RightOpenDurationInterval(lower_exp, upper_exp)
        )

    def add_constraint(
        self,
        constraint: Union[
            "up.model.fnode.FNode",
            "up.model.fluent.Fluent",
            "up.model.parameter.Parameter",
            bool,
        ],
    ):
        """
        Adds the given expression to the `chronicle's constraints`.
        """
        (constraint_exp,) = self._env.expression_manager.auto_promote(constraint)
        assert self._env.type_checker.get_type(constraint_exp).is_bool_type()
        if constraint_exp not in self._constraints:
            self._constraints.append(constraint_exp)

    def add_condition(
        self,
        interval: Union["up.model.timing.Timing", "up.model.timing.TimeInterval"],
        condition: Union[
            "up.model.fnode.FNode",
            "up.model.fluent.Fluent",
            "up.model.parameter.Parameter",
            bool,
        ],
    ):
        """
        Adds the given expression to the `action's conditions`. For this `action` to be applicable
        the given expression must evaluate to `True` during the whole given `interval`.

        :param interval: The `interval` in which the given expression must evaluate to `True` for this
            `action` to be applicable.
        :param condition: The expression that must be `True` in the given `interval` for this
            `action` to be applicable.
        """
        if isinstance(interval, up.model.Timing):
            interval = up.model.TimePointInterval(interval)
        (condition_exp,) = self._env.expression_manager.auto_promote(condition)
        assert self._env.type_checker.get_type(condition_exp).is_bool_type()
        if interval in self._conditions:
            if condition_exp not in self._conditions[interval]:
                self._conditions[interval].append(condition_exp)
        else:
            self._conditions[interval] = [condition_exp]

    def _set_conditions(
        self,
        interval: "up.model.timing.TimeInterval",
        conditions: List["up.model.fnode.FNode"],
    ):
        self._conditions[interval] = conditions

    def add_effect(
        self,
        timing: "up.model.timing.Timing",
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
    ):
        """
        At the given time, adds the given assignment to the `action's effects`.

        :param timing: The exact time in which the assignment is applied.
        :param fluent: The `fluent` which value is modified by the assignment.
        :param value: The `value` to assign to the given `fluent`.
        :param condition: The `condition` in which this `effect` is applied; the default
            value is `True`.
        """
        (
            fluent_exp,
            value_exp,
            condition_exp,
        ) = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPTypeError("Effect condition is not a Boolean condition!")
        if not fluent_exp.type.is_compatible(value_exp.type):
            raise UPTypeError("InstantaneousAction effect has not compatible types!")
        self._add_effect_instance(
            timing, up.model.effect.Effect(fluent_exp, value_exp, condition_exp)
        )

    def add_increase_effect(
        self,
        timing: "up.model.timing.Timing",
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
    ):
        """
        At the given time, adds the given `increment` to the `action's effects`.

        :param timing: The exact time in which the increment is applied.
        :param fluent: The `fluent` which value is incremented by the added `effect`.
        :param value: The given `fluent` is incremented by the given `value`.
        :param condition: The `condition` in which this effect is applied; the default
            value is `True`.
        """
        (
            fluent_exp,
            value_exp,
            condition_exp,
        ) = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not condition_exp.type.is_bool_type():
            raise UPTypeError("Effect condition is not a Boolean condition!")
        if not fluent_exp.type.is_compatible(value_exp.type):
            raise UPTypeError("InstantaneousAction effect has not compatible types!")
        if not fluent_exp.type.is_int_type() and not fluent_exp.type.is_real_type():
            raise UPTypeError("Increase effects can be created only on numeric types!")
        self._add_effect_instance(
            timing,
            up.model.effect.Effect(
                fluent_exp,
                value_exp,
                condition_exp,
                kind=up.model.effect.EffectKind.INCREASE,
            ),
        )

    def add_decrease_effect(
        self,
        timing: "up.model.timing.Timing",
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: "up.model.expression.Expression",
        condition: "up.model.expression.BoolExpression" = True,
    ):
        """
        At the given time, adds the given `decrement` to the `action's effects`.

        :param timing: The exact time in which the `decrement` is applied.
        :param fluent: The `fluent` which value is decremented by the added effect.
        :param value: The given `fluent` is decremented by the given `value`.
        :param condition: The `condition` in which this effect is applied; the default
            value is `True`.
        """
        (
            fluent_exp,
            value_exp,
            condition_exp,
        ) = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not condition_exp.type.is_bool_type():
            raise UPTypeError("Effect condition is not a Boolean condition!")
        if not fluent_exp.type.is_compatible(value_exp.type):
            raise UPTypeError("InstantaneousAction effect has not compatible types!")
        if not fluent_exp.type.is_int_type() and not fluent_exp.type.is_real_type():
            raise UPTypeError("Decrease effects can be created only on numeric types!")
        self._add_effect_instance(
            timing,
            up.model.effect.Effect(
                fluent_exp,
                value_exp,
                condition_exp,
                kind=up.model.effect.EffectKind.DECREASE,
            ),
        )

    def _add_effect_instance(
        self, timing: "up.model.timing.Timing", effect: "up.model.effect.Effect"
    ):
        assert (
            self._env == effect.environment
        ), "effect does not have the same environment of the action"
        fluents_assigned = self._fluents_assigned.setdefault(timing, set())
        fluents_inc_dec = self._fluents_inc_dec.setdefault(timing, set())
        simulated_effect = self._simulated_effects.get(timing, None)
        if not effect.is_conditional():
            if effect.is_assignment():
                if (
                    effect.fluent in fluents_assigned
                    or effect.fluent in fluents_inc_dec
                ):
                    raise UPConflictingEffectsException(
                        f"The effect {effect} at timing {timing} is in conflict with the effects already in the action."
                    )
                fluents_assigned.add(effect.fluent)
            elif effect.is_increase() or effect.is_decrease():
                if effect.fluent in fluents_assigned:
                    raise UPConflictingEffectsException(
                        f"The effect {effect} at timing {timing} is in conflict with the effects already in the action."
                    )
                fluents_inc_dec.add(effect.fluent)
            else:
                raise NotImplementedError
        if simulated_effect is not None and effect.fluent in simulated_effect.fluents:
            raise UPConflictingEffectsException(
                f"The effect {effect} is in conflict with the simulated effects already in the action."
            )
        self._effects.setdefault(timing, []).append(effect)

    @property
    def simulated_effects(
        self,
    ) -> Dict["up.model.timing.Timing", "up.model.effect.SimulatedEffect"]:
        """Returns the `action` `simulated effects`."""
        return self._simulated_effects

    def set_simulated_effect(
        self,
        timing: "up.model.timing.Timing",
        simulated_effect: "up.model.effect.SimulatedEffect",
    ):
        """
        Sets the given `simulated effect` at the specified `timing`.

        :param timing: The time in which the `simulated effect` must be applied.
        :param simulated effects: The `simulated effect` that must be applied at the given `timing`.
        """
        for f in simulated_effect.fluents:
            if f in self._fluents_assigned.get(
                timing, set()
            ) or f in self._fluents_inc_dec.get(timing, set()):
                raise UPConflictingEffectsException(
                    f"The simulated effect {simulated_effect} is in conflict with the effects already in the action."
                )
        self._simulated_effects[timing] = simulated_effect
