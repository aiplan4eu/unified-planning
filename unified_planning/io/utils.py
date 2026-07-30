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


from typing import Union, Sequence, List


def parse_string(obj, problem_str, parse_all):
    return obj.parse_string(problem_str, parse_all=parse_all)


def parse_file(obj, problem_filename: Union[str, Sequence[str]], parse_all):
    if isinstance(problem_filename, str):
        return obj.parse_file(problem_filename, parse_all=parse_all)
    else:
        problem_parts: List[str] = []
        for filename in problem_filename:
            assert isinstance(filename, str), "Typing not respected"
            with open(filename, encoding="utf-8-sig") as file:
                problem_parts.append(file.read())
        return parse_string(obj, "\n".join(problem_parts), parse_all)


def set_results_name(obj, name):
    return obj.set_results_name(name)


def set_parse_action(obj, fun):
    return obj.set_parse_action(fun)
