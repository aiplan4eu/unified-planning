from dataclasses import dataclass
from typing import FrozenSet

@dataclass
class Action:
    name: str
    precondition: FrozenSet[str]
    positive_effect: FrozenSet[str]
    negative_effect: FrozenSet[str]
