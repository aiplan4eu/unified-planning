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


from fractions import Fraction
from functools import partial
import unified_planning as up
from unified_planning.engines.sequential_simulator import (
    UPSequentialSimulator,
    evaluate_quality_metric_in_initial_state,
    evaluate_quality_metric,
)
from unified_planning.model import (
    FNode,
    Problem,
    State,
    PlanQualityMetric,
    Expression,
    Action,
)
from unified_planning.model.walkers import StateEvaluator
from unified_planning.plans.plan import ActionInstance, Plan
from unified_planning.plans.sequential_plan import SequentialPlan
from unified_planning.plans.stn_plan import STNPlan, STNPlanNode
from unified_planning.plans.time_triggered_plan import TimeTriggeredPlan
from unified_planning.plans.contingent_plan import (
    ContingentPlan,
    ContingentPlanNode,
    visit_tree,
)
from unified_planning.plans.partial_order_plan import PartialOrderPlan
import datetime
import plotly.express as px  # type: ignore[import]
import matplotlib.pyplot as plt  # type: ignore[import]
import networkx as nx
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    Callable,
)

# Defaults
FIGSIZE = (13, 8)
ARROWSIZE = 20
MIN_NODE_SIZE = 4000
NODE_COLOR = "#1f78b4"
EDGE_COLOR = "k"
FONT_SIZE = 10
FONT_COLOR = "k"
EDGE_FONT_SIZE = 8
EDGE_FONT_COLOR = "k"
FIGSIZE_SCALE_FACTOR = 65  # A scale factor from the figure size of plotly vs matplotlib


def draw_base_graph(
    graph: nx.DiGraph,
    *,
    figsize: Optional[Sequence[float]] = None,
    top_bottom: bool = False,
    generate_node_label: Optional[
        Union[
            Callable[["ContingentPlanNode"], str],
            Callable[["ActionInstance"], str],
            Optional[Callable[["STNPlanNode"], str]],
            Optional[Callable[[FNode], str]],
        ]
    ] = None,
    arrowsize: int = ARROWSIZE,
    node_size: Optional[Union[float, Sequence[float]]] = None,
    node_color: Union[str, Sequence[str]] = NODE_COLOR,
    edge_color: Union[str, Sequence[str]] = EDGE_COLOR,
    font_size: int = FONT_SIZE,
    font_color: str = FONT_COLOR,
    draw_networkx_kwargs: Optional[Dict[str, Any]] = None,
):
    # input "sanitization"
    if top_bottom:
        graph.graph.setdefault("graph", {})["rankdir"] = "TB"
    else:
        graph.graph.setdefault("graph", {})["rankdir"] = "LR"
    if generate_node_label is None:
        node_label: Callable[[Any], str] = str
    else:
        node_label = generate_node_label
    if draw_networkx_kwargs is None:
        draw_networkx_kwargs = {}

    # drawing part
    labels: Dict[Any, str] = dict(map(lambda x: (x, node_label(x)), graph.nodes))
    if node_size is None:
        font_factor = font_size * font_size * 10.7

        def length_factor(label_length: int) -> float:
            return label_length * label_length / 28

        node_size = [
            max(length_factor(max(len(labels[node]), 3)) * font_factor, MIN_NODE_SIZE)
            for node in graph.nodes
        ]
    if figsize is None:
        figsize = FIGSIZE
    assert figsize is not None
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot()
    pos = nx.nx_agraph.graphviz_layout(graph, prog="dot")
    nx.draw_networkx(
        graph,
        pos,
        labels=labels,
        arrowstyle="-|>",
        arrowsize=arrowsize,
        node_size=node_size,
        node_color=node_color,
        edge_color=edge_color,
        font_size=font_size,
        font_color=font_color,
        font_family="monospace",
        ax=ax,
        **draw_networkx_kwargs,
    )
    return fig, ax, pos
