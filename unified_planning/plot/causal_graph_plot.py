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

from unified_planning.exceptions import (
    UPUsageError,
    UPNoSuitableEngineAvailableException,
    UPUnsupportedProblemTypeError,
)
from unified_planning.model import (
    Problem,
    FNode,
    Action,
    generate_causal_graph,
)
from unified_planning.plot.utils import (
    ARROWSIZE,
    NODE_COLOR,
    EDGE_COLOR,
    FONT_SIZE,
    FONT_COLOR,
    EDGE_FONT_SIZE,
    EDGE_FONT_COLOR,
    draw_base_graph,
)
from unified_planning.engines import CompilationKind


from itertools import chain, product
import networkx as nx
from typing import (
    Any,
    Dict,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    Callable,
)


def plot_causal_graph(
    problem: Problem,
    *,
    filename: Optional[str] = None,
    figsize: Optional[Tuple[float, float]] = None,
    top_bottom: bool = False,
    generate_node_label: Optional[Callable[[FNode], str]] = None,
    arrowsize: int = ARROWSIZE,
    node_size: Optional[Union[int, Sequence[int]]] = None,
    node_color: Union[str, Sequence[str]] = NODE_COLOR,
    edge_color: Union[str, Sequence[str]] = EDGE_COLOR,
    font_size: int = FONT_SIZE,
    font_color: str = FONT_COLOR,
    generate_edge_label: Optional[Callable[[Action, Sequence[FNode]], str]] = None,
    edge_font_size: int = EDGE_FONT_SIZE,
    edge_font_color: str = EDGE_FONT_COLOR,
    draw_networkx_kwargs: Optional[Dict[str, Any]] = None,
    draw_networkx_edge_labels_kwargs: Optional[Dict[str, Any]] = None,
):
    """
    This method plots the causal graph as a directed graph where the nodes are the
    fluents in the (grounded) problem and the edges are labeled with the actions
    that puts a relation on those fluents.

    Generally speaking, there is an arc from F1 to F2 if there is an action in the
    problem that reads F1 and writes F2. If an action writes both F1 and F2 the arc
    from F1 to F2 will be bidirectional.

    :param problem: The problem of which the causal graph is plotted.
    :param filename: The path of the file where the plot is saved; if not specified
        the plot will be shown in a pop-up.
    :param figsize: Width and height in inches.
    :param top_bottom: If ``True`` the graph will be vertical, if ``False`` it will be
        horizontal.
    :param generate_node_label: The function used to generate the node labels
        of the graph from a ``FNode``; defaults to the str method.
    :param arrowsize: The size of the arrows of the graph.
    :param node_size: The size of the nodes of the graph. If a Sequence is
        specified, it must have the same length of the nodes in the plan and
        the n'th node will have the n'th size.
    :param node_color: The color of the nodes of the graph in it's hexadecimal
        value. If a Sequence is specified, it must have the same length of the
        nodes in the plan and the n'th node will have the n'th color.
    :param edge_color: The color of the edges of the graph in it's hexadecimal
        value. If a Sequence is specified, it must have the length of the
        constraints and the n'th edge will have the n'th color.
    :param font_size: The font size of the node labels.
    :param font_color: The font color of the node labels.
    :param generate_edge_label: The function used to generate the edge labels
        of the graph.
    :param edge_font_size: The font size of the edge labels.
    :param edge_font_color: The font color of the edge labels.
    :param draw_networkx_kwargs: This mapping is directly passed to the
        `draw_networkx <https://networkx.org/documentation/stable/reference/generated/networkx.drawing.nx_pylab.draw_networkx.html#networkx.drawing.nx_pylab.draw_networkx>`_
        method; use carefully. NOTE: This parameters is not guaranteed to be
        maintained in any way and it might be removed or modified at any moment.
    :param draw_networkx_edge_labels_kwargs: This mapping is directly passed to the
        `draw_networkx_edge_labels <https://networkx.org/documentation/stable/reference/generated/networkx.drawing.nx_pylab.draw_networkx_edge_labels.html#networkx.drawing.nx_pylab.draw_networkx_edge_labels>`_
        method; use carefully. NOTE: This parameters is not guaranteed to be
        maintained in any way and it might be removed or modified at any moment.
    """
    # param "sanitization"
    import matplotlib.pyplot as plt  # type: ignore[import]

    if generate_edge_label is None:
        edge_label_function: Callable[
            [Action, Sequence[FNode]], str
        ] = _generate_causal_graph_edge_label
    else:
        edge_label_function = generate_edge_label
    if draw_networkx_edge_labels_kwargs is None:
        draw_networkx_edge_labels_kwargs = {}
    if generate_node_label is None:
        generate_node_label = str

    graph, edge_actions = generate_causal_graph(problem)
    edge_labels_set: Dict[Tuple[FNode, FNode], Set[str]] = {
        k: set(edge_label_function(e.action, e.actual_parameters) for e in v)
        for k, v in edge_actions.items()
    }

    edge_labels: Dict[Tuple[FNode, FNode], str] = {
        edge: ", ".join(labels) for edge, labels in edge_labels_set.items() if labels
    }

    fig, ax, pos = draw_base_graph(
        graph,
        figsize=figsize,
        top_bottom=top_bottom,
        generate_node_label=generate_node_label,
        arrowsize=arrowsize,
        node_size=node_size,
        node_color=node_color,
        edge_color=edge_color,
        font_size=font_size,
        font_color=font_color,
        draw_networkx_kwargs=draw_networkx_kwargs,
        prog="dot",
    )
    nx.draw_networkx_edge_labels(
        graph,
        pos,
        edge_labels=edge_labels,
        font_size=edge_font_size,
        font_color=edge_font_color,
        ax=ax,
        **draw_networkx_edge_labels_kwargs,
    )
    if filename is None:
        plt.show()
    else:
        fig.savefig(filename)


def _generate_causal_graph_edge_label(action: Action, params: Sequence[FNode]) -> str:
    if len(params) > 0:
        ps = ", ".join(map(str, params))
        params_str = f"({ps})"
    else:
        params_str = ""
    return f"{action.name}{params_str}"
