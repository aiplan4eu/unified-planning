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

import unified_planning as up
from unified_planning.model.types import _UserType
from unified_planning.exceptions import UPProblemDefinitionError, UPValueError
from typing import Iterator, List, Union, Optional, cast


class ObjectsSetMixin:
    """
    This class is a mixin that contains a set of objects with some related methods.

    NOTE: when this mixin is used in combination with other mixins that share some
    of the attributes (e.g. env, add_user_type_method, has_name_method), it is required
    to pass the very same arguments to the mixins constructors.
    """

    def __init__(self, env, add_user_type_method, has_name_method):
        self._env = env
        self._add_user_type_method = add_user_type_method
        self._has_name_method = has_name_method
        self._objects: List["up.model.object.Object"] = []

    @property
    def env(self) -> "up.environment.Environment":
        """Returns the problem environment."""
        return self._env

    def add_object(
        self,
        obj_or_name: Union["up.model.object.Object", str],
        typename: Optional["up.model.types.Type"] = None,
    ) -> "up.model.object.Object":
        """Add the given object to the problem, constructing it from the parameters if needed.

        :param obj_or_name: Either an Object instance or a string containing the name of the object.
        :param typename: If the first argument contains only the name of the object, this parameter should contain
                         its type, to allow creating the object.
        :return: The Object that was passed or constructed.

        Examples
        --------
        >>> from unified_planning.shortcuts import *
        >>> problem = Problem()
        >>> cup = UserType("Cup")
        >>> o1 = Object("o1", cup)  # creates a new object o1
        >>> problem.add_object(o1)  # adds it to the problem
        o1
        >>> o2 = problem.add_object("o2", cup)  # alternative syntax to create a new object and add it to the problem.
        """
        if isinstance(obj_or_name, up.model.object.Object):
            assert typename is None
            obj = obj_or_name
            assert (
                obj.environment == self._env
            ), "Object does not have the same environemt fo the problem"
        else:
            assert typename is not None, "Missing type of the object"
            obj = up.model.object.Object(obj_or_name, typename, self._env)
        if self._has_name_method(obj.name):
            raise UPProblemDefinitionError("Name " + obj.name + " already defined!")
        self._objects.append(obj)
        if obj.type.is_user_type():
            self._add_user_type_method(obj.type)
        return obj

    def add_objects(self, objects: List["up.model.object.Object"]):
        """
        Adds the given objects to the problem.

        :param objects: The list of objects that must be added to the problem.
        """
        for obj in objects:
            self.add_object(obj)

    def object(self, name: str) -> "up.model.object.Object":
        """
        Returns the object with the given name.

        :param name: The name of the target object in the problem.
        """
        for o in self._objects:
            if o.name == name:
                return o
        raise UPValueError(f"Object of name: {name} is not defined!")

    def has_object(self, name: str) -> bool:
        """
        Returns true if the object with the given name is in the problem,
        False otherwise.

        :param name: The name of the target object in the problem.
        :return: True if an object with the given name is in the problem,
                False otherwise.
        """
        for o in self._objects:
            if o.name == name:
                return True
        return False

    def objects(
        self, typename: "up.model.types.Type"
    ) -> Iterator["up.model.object.Object"]:
        """
        Returns the objects compatible with the given type: this includes the given
        type and its heirs.

        :param typename: The target type of the objects that are retrieved.
        :return: A generator of all the objects in the problem that are compatible with the
        given type.
        """
        for obj in self._objects:
            if cast(_UserType, obj.type).is_subtype(typename):
                yield obj

    @property
    def all_objects(self) -> List["up.model.object.Object"]:
        """Returns the list containing all the objects in the problem."""
        return self._objects
