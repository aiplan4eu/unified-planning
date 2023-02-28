from fractions import Fraction
from typing import Union, Dict, Any

import unified_planning as up
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPTypeError,
    UPExpressionDefinitionError,
)
from unified_planning.model.fluent import get_all_fluent_exp
from unified_planning.model.mixins import ObjectsSetMixin, FluentsSetMixin


class InitialStateMixin:
    """A Problem mixin that allows setting and infering the value of fluents in the initial state."""

    def __init__(
        self,
        object_set: ObjectsSetMixin,
        fluent_set: FluentsSetMixin,
        environment: "up.environment.Environment",
    ):
        self._object_set = object_set
        self._fluent_set = fluent_set
        self._env = environment
        self._initial_value: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"] = {}

    def set_initial_value(
        self,
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: Union[
            "up.model.fnode.FNode",
            "up.model.fluent.Fluent",
            "up.model.object.Object",
            bool,
            int,
            float,
            Fraction,
        ],
    ):
        """
        Sets the initial value for the given `Fluent`. The given `Fluent` must be grounded, therefore if
        it's :func:`arity <unified_planning.model.Fluent.arity>` is `> 0`, the `fluent` parameter must be
        an `FNode` and the method :func:`~unified_planning.model.FNode.is_fluent_exp` must return `True`.

        :param fluent: The grounded `Fluent` of which the initial value must be set.
        :param value: The `value` assigned in the initial state to the given `fluent`.
        """
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        if not fluent_exp.type.is_compatible(value_exp.type):
            raise UPTypeError("Initial value assignment has not compatible types!")
        self._initial_value[fluent_exp] = value_exp

    def initial_value(
        self, fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"]
    ) -> "up.model.fnode.FNode":
        """
        Retrieves the initial value assigned to the given `fluent`.

        :param fluent: The target `fluent` of which the `value` in the initial state must be retrieved.
        :return: The `value` expression assigned to the given `fluent` in the initial state.
        """
        (fluent_exp,) = self._env.expression_manager.auto_promote(fluent)
        for a in fluent_exp.args:
            if not a.is_constant():
                raise UPExpressionDefinitionError(
                    f"Impossible to return the initial value of a fluent expression with no constant arguments: {fluent_exp}."
                )
        if fluent_exp in self._initial_value:
            return self._initial_value[fluent_exp]
        elif fluent_exp.fluent() in self._fluent_set.fluents_defaults:
            return self._fluent_set.fluents_defaults[fluent_exp.fluent()]
        else:
            raise UPProblemDefinitionError(
                f"Initial value not set for fluent: {fluent}"
            )

    @property
    def initial_values(self) -> Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]:
        """
        Gets the initial value of all the grounded fluents present in the `Problem`.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible.
        """
        res = self._initial_value
        for f in self._fluent_set.fluents:
            for f_exp in get_all_fluent_exp(self._object_set, f):
                res[f_exp] = self.initial_value(f_exp)
        return res

    @property
    def explicit_initial_values(
        self,
    ) -> Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]:
        """
        Returns the problem's defined initial values; those are only the initial values set with the
        :func:`~unified_planning.model.Problem.set_initial_value` method.

        IMPORTANT NOTE: For all the initial values of the problem use :func:`initial_values <unified_planning.model.Problem.initial_values>`.
        """
        return self._initial_value

    def __eq__(self, oth: Any) -> bool:
        """Returns true iff the two initial states are equivalent."""
        if not isinstance(oth, InitialStateMixin):
            return False
        oth_initial_values = oth.initial_values
        initial_values = self.initial_values
        if len(initial_values) != len(oth_initial_values):
            return False
        for fluent, value in initial_values.items():
            oth_value = oth_initial_values.get(fluent, None)
            if oth_value is None:
                return False
            elif value != oth_value:
                return False
        return True

    def __hash__(self):
        return sum(map(hash, self.initial_values.items()))

    def _clone_to(self, other: "InitialStateMixin"):
        other._initial_value = self._initial_value.copy()
