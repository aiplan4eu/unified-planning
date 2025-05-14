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


# global variable to avoid repetition of warnings
_PREVIOUS_WARNINGS = set()


class handles:
    def __init__(self, *what):
        self.what = what

    def __call__(self, func):
        func._what = self.what
        return func


class Converter:
    def __init__(self):
        self.functions = {}
        for k in dir(self):
            v = getattr(self, k)
            if hasattr(v, "_what"):
                for x in v._what:
                    self.functions[x] = v

    def convert(self, element, *args):
        """Finds and applies the converter for the given object, based on its type.
        If there are no converter for the base class, we look for converter for a parent type but emit a warning if one of these is used
        as some information could be lost in the process.
        """
        global _PREVIOUS_WARNINGS
        leaf_type = type(element)
        for tpe in type.mro(leaf_type):
            if tpe in self.functions:
                if tpe != leaf_type and (leaf_type, tpe) not in _PREVIOUS_WARNINGS:
                    _PREVIOUS_WARNINGS.add((leaf_type, tpe))
                    print(
                        f"Warning: no converter for type {leaf_type},\n       treating it as if it was a {tpe} instead."
                    )
                f = self.functions[tpe]
                return f(element, *args)
        raise ValueError(f"No converter for type: {leaf_type} nor its parent types.")
