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

from importlib.metadata import PackageNotFoundError, version as _pkg_version
from typing import Any, TYPE_CHECKING

from unified_planning.environment import Environment


if TYPE_CHECKING:
    # can't actually subclass Any at runtime
    AnyBaseClass = Any
else:
    AnyBaseClass = object


try:
    __version__ = _pkg_version("unified-planning")
except PackageNotFoundError:
    __version__ = "unknown"
