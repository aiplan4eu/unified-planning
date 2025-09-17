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
#
"""This module contains all custom exceptions."""


class UPException(Exception):
    """Base class for all custom exceptions of the unified_planning (UP) library."""

    pass


class UPProblemDefinitionError(UPException):
    pass


class UPPlanDefinitionError(UPException):
    pass


class UPTypeError(UPException, TypeError):
    pass


class UPUnsupportedProblemTypeError(UPException):
    pass


class UPUnboundedVariablesError(UPException):
    pass


class UPExpressionDefinitionError(UPException):
    pass


class UPUnreachableCodeError(UPException):
    pass


class UPValueError(UPException):
    pass


class UPUsageError(UPException):
    pass


class UPNoSuitableEngineAvailableException(UPException):
    pass


class UPNoRequestedEngineAvailableException(UPException):
    pass


class UPConflictingEffectsException(UPException):
    pass


class ANMLSyntaxError(UPException, SyntaxError):
    pass


class UPInvalidActionError(UPException):
    pass


class UPAIPDDLPlanningError(UPException):
    pass
