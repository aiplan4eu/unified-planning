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
        f = self.functions[type(element)]
        return f(element, *args)
