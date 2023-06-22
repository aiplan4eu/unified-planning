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

from dataclasses import dataclass
from typing import IO


@dataclass
class Credits:
    name: str
    author: str
    contact: str
    website: str
    license: str
    short_description: str
    long_description: str

    def write_credits(self, stream: IO[str], full_credits: bool = False):
        """
        Writes those credits on the given `IO[str]`; based on the flag `full_credits`
        discriminates if the user wants a long version or a short version.

        :param stream: The `IO[str]` stream on which the credits are written.
        :param full_credits: Flag deciding if the user wants long or short credits.
        """
        stream.write(f"  * Engine name: {self.name}\n  * Developers:  {self.author}\n")
        if not full_credits:
            stream.write("  * Description: ")
            stream.write(self.short_description.replace("\n", "\n  *              "))
            stream.write("\n")
        else:
            stream.write(f"  * Contacts:    {self.contact}\n")
            stream.write(f"  * Website:     {self.website}\n")
            stream.write(f"  * License:     {self.license}\n  * Description: ")
            stream.write(self.long_description.replace("\n", "\n  *              "))
            stream.write("\n")
