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


import pyparsing
from typing import Union, Sequence, List


def parse_string(obj, problem_str, parse_all):
    if pyparsing.__version__ < "3.0.0":
        return obj.parseString(problem_str, parseAll=parse_all)
    else:
        return obj.parse_string(problem_str, parse_all=parse_all)


def parse_file(obj, problem_filename: Union[str, Sequence[str]], parse_all):
    if isinstance(problem_filename, str):
        if pyparsing.__version__ < "3.0.0":
            return obj.parseFile(problem_filename, parseAll=parse_all)
        else:
            return obj.parse_file(problem_filename, parse_all=parse_all)
    else:
        problem_parts: List[str] = []
        for filename in problem_filename:
            assert isinstance(filename, str), "Typing not respected"
            with open(filename, encoding="utf-8-sig") as file:
                problem_parts.append(file.read())
        return parse_string(obj, "\n".join(problem_parts), parse_all)


def set_results_name(obj, name):
    if pyparsing.__version__ < "3.0.0":
        return obj.setResultsName(name)
    else:
        return obj.set_results_name(name)


def set_parse_action(obj, fun):
    if pyparsing.__version__ < "3.0.0":
        return obj.setParseAction(fun)
    else:
        return obj.set_parse_action(fun)


if pyparsing.__version__ < "3.0.0":
    from pyparsing import ParseResults, ParseElementEnhance

    class Located(ParseElementEnhance):
        def parseImpl(self, instring, loc, doActions=True):
            start = loc
            loc, tokens = self.expr._parse(instring, start, doActions, callPreParse=False)  # type: ignore
            ret_tokens = ParseResults([start, tokens, loc])
            ret_tokens["locn_start"] = start
            ret_tokens["value"] = tokens
            ret_tokens["locn_end"] = loc
            if self.resultsName:
                return loc, [ret_tokens]
            else:
                return loc, ret_tokens

else:
    from pyparsing import Located  # type: ignore
