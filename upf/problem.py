from upf.action import Action
from dataclasses import dataclass
from typing import FrozenSet, List

@dataclass
class Problem:
    actions: List[Action]
    init: FrozenSet[str]
    goal: FrozenSet[str]
