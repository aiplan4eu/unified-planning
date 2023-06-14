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

from itertools import chain, product
from unified_planning.model import (
    Problem,
    FNode,
    Action,
    InstantaneousAction,
    DurativeAction,
)
from unified_planning.plot.plan_plot import (
    FIGSIZE,
    ARROWSIZE,
    NODE_SIZE,
    NODE_COLOR,
    EDGE_COLOR,
    FONT_SIZE,
    FONT_COLOR,
    EDGE_FONT_SIZE,
    EDGE_FONT_COLOR,
    _draw_base_graph,
)
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


def plot_causal_graph(
    problem: Problem,
    *,
    filename: Optional[str] = None,
    figsize: Tuple[float, float] = FIGSIZE,
    top_bottom: bool = False,
    generate_node_label: Optional[Callable[[FNode], str]] = None,
    arrowsize: int = ARROWSIZE,
    node_size: Union[int, Sequence[int]] = NODE_SIZE,
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
    """# TODO update
    This method plots the Contingent plan as a directed graph where the edges are
    labeled with the temporal constraints contained in the given ``plan``.

    :param plan: The plan to plot.
    :param filename: The path of the file where the plot is saved; if not specified
        the plot will be shown in a pop-up.
    :param figsize: Width and height in inches.
    :param top_bottom: If ``True`` the graph will be vertical, if ``False`` it will be
        horizontal.
    :param generate_node_label: The function used to generate the node labels
        of the graph from a ``ContingentPlanNode``; defaults to the str of the
        node action instance.
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

    # TODO handle problem not grounded
    fluents_red: Dict[FNode, Set[Action]] = {}
    fluents_written: Dict[FNode, Set[Action]] = {}

    fve = problem.environment.free_vars_extractor
    for action in problem.actions:
        assert not action.parameters
        if isinstance(action, InstantaneousAction):
            for p in action.preconditions:
                # TODO cover when a fluent has fluents inside...
                for fluent in fve.get(p):
                    if any(map(fve.get, fluent.args)):
                        raise NotImplementedError(
                            "nested fluents still are not implemented"
                        )
                    fluents_red.setdefault(fluent, set()).add(action)
            for e in action.effects:
                fluent = e.fluent
                assert fluent.is_fluent_exp()
                if any(map(fve.get, fluent.args)):
                    raise NotImplementedError(
                        "nested fluents still are not implemented"
                    )
                fluents_written.setdefault(fluent, set()).add(action)
                for fluent in chain(fve.get(e.value), fve.get(e.condition)):
                    if any(map(fve.get, fluent.args)):
                        raise NotImplementedError(
                            "nested fluents still are not implemented"
                        )
                    fluents_red.setdefault(fluent, set()).add(action)
        elif isinstance(action, DurativeAction):
            for p in chain(*action.conditions.values()):
                # TODO cover when a fluent has fluents inside...
                for fluent in fve.get(p):
                    if any(map(fve.get, fluent.args)):
                        raise NotImplementedError(
                            "nested fluents still are not implemented"
                        )
                    fluents_red.setdefault(fluent, set()).add(action)
            for e in chain(*action.effects.values()):
                fluent = e.fluent
                assert fluent.is_fluent_exp()
                if any(map(fve.get, fluent.args)):
                    raise NotImplementedError(
                        "nested fluents still are not implemented"
                    )
                fluents_written.setdefault(fluent, set()).add(action)
                for fluent in chain(fve.get(e.value), fve.get(e.condition)):
                    if any(map(fve.get, fluent.args)):
                        raise NotImplementedError(
                            "nested fluents still are not implemented"
                        )
                    fluents_red.setdefault(fluent, set()).add(action)
        else:
            raise NotImplementedError
    edge_labels_set: Dict[Tuple[FNode, FNode], Set[str]] = {}
    graph = nx.DiGraph()
    all_fluents = set(chain(fluents_red.keys(), fluents_written.keys()))
    # Add an edge if a fluent that is red or written and it's in the same action of a written fluent
    empty_set = set()
    for left_node, right_node in product(all_fluents, fluents_written.keys()):
        rn_actions = fluents_written.get(right_node, empty_set)
        if left_node != right_node and rn_actions:
            label = edge_labels_set.setdefault((left_node, right_node), set())
            edge_created = False
            for ln_action in chain(
                fluents_red.get(left_node, empty_set),
                fluents_written.get(left_node, empty_set),
            ):
                if ln_action in rn_actions:
                    if not edge_created:
                        edge_created = True
                        graph.add_edge(left_node, right_node)
                    label.add(
                        edge_label_function(ln_action, tuple())
                    )  # TODO fix the tuple when non-grounded problems will be accepted
    edge_labels: Dict[Tuple[FNode, FNode], str] = {
        edge: ", ".join(labels) for edge, labels in edge_labels_set.items() if labels
    }

    fig, ax, pos = _draw_base_graph(
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
