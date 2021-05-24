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
"""Provides the most used functions in a nicely wrapped API.
This module defines a global environment, so that most methods can be
called without the need to specify an environment or a ExpressionManager.
"""

from upf.environment import get_env


def And(*args, **kwargs):
    return get_env().expression_manager.And(*args, **kwargs)

def Or(*args, **kwargs):
    return get_env().expression_manager.Or(*args, **kwargs)

def Implies(*args, **kwargs):
    return get_env().expression_manager.Implies(*args, **kwargs)

def Iff(*args, **kwargs):
    return get_env().expression_manager.Iff(*args, **kwargs)

def Equals(*args, **kwargs):
    return get_env().expression_manager.Equals(*args, **kwargs)

def Not(*args, **kwargs):
    return get_env().expression_manager.Not(*args, **kwargs)

def TRUE(*args, **kwargs):
    return get_env().expression_manager.TRUE(*args, **kwargs)

def FALSE(*args, **kwargs):
    return get_env().expression_manager.FALSE(*args, **kwargs)

def Bool(*args, **kwargs):
    return get_env().expression_manager.Bool(*args, **kwargs)

def FluentExp(*args, **kwargs):
    return get_env().expression_manager.FluentExp(*args, **kwargs)

def ParameterExp(*args, **kwargs):
    return get_env().expression_manager.ParameterExp(*args, **kwargs)

def ObjectExp(*args, **kwargs):
    return get_env().expression_manager.ObjectExp(*args, **kwargs)

def BOOL():
    return get_env().type_manager.BOOL()

def UserType(name):
    return get_env().type_manager.UserType(name)
