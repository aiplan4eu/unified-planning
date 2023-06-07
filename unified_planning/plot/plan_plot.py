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
from numbers import Real
import unified_planning as up
from unified_planning.engines.sequential_simulator import UPSequentialSimulator
from unified_planning.model import FNode, Problem, State
from unified_planning.model.walkers import StateEvaluator
from unified_planning.plans.plan import ActionInstance
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
import plotly.express as px
import matplotlib.pyplot as plt
import networkx as nx
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union, Callable

# Defaults
ARROWSIZE = 20
NODE_SIZE = 2000
NODE_COLOR = "#1f78b4"
EDGE_COLOR = "k"
FONT_SIZE = 8
FONT_COLOR = "k"
EDGE_FONT_SIZE = 6
EDGE_FONT_COLOR = "k"


def plot_sequential_plan(
    plan: "SequentialPlan",
    problem: Optional[Problem] = None,
    expression_or_expressions: Optional[Union[FNode, List[FNode]]] = None,
    *,
    filename: Optional[str] = None,
    top_bottom: bool = False,
    generate_node_label: Optional[Callable[["ActionInstance"], str]] = None,
    arrowsize: int = ARROWSIZE,
    node_size: Union[int, Sequence[int]] = NODE_SIZE,
    node_color: Union[str, Sequence[str]] = NODE_COLOR,
    edge_color: Union[str, Sequence[str]] = EDGE_COLOR,
    font_size: int = FONT_SIZE,
    font_color: str = FONT_COLOR,
    draw_networkx_kwargs: Optional[Dict[str, Any]] = None,
):
    """
    This method has 2 different usage:

    #. when ``expression_or_expressions`` is specified; the problem is required
        and all the arguments different from ``filename`` are ignored. This plots
        all given expressions in a graph, showing the changes during the execution
        of the plan.
    #. when ``expression_or_expressions`` is NOT specified; this plots the
        sequential plan simply as a straight graph.
        Minor note: the colors parameter must be a string accepted by

    :param plan: The plan to plot or the plan used to get the values of the
        expressions to plot.
    :param problem: The Problem for which the plan is generated; used only if
        ``expression_or_expressions`` is specified.
    :param expression_or_expressions: The Expressions to plot; this parameter
        defines the mode of this method.
    :param filename: The path of the file where the plot is saved; if not specified
        the plot will be shown in a pop-up.
    :param top_bottom: If ``True`` the graph will be vertical, if ``False`` it will be
        horizontal.
    :param generate_node_label: The function used to generate the node labels
        of the graph from an ``ActionInstance``; defaults to the str method.
    :param arrowsize: The size of the arrows of the graph.
    :param node_size: The size of the nodes of the graph. If a Sequence is
        specified, it must have the same length of the plan and the n'th node
        will have the n'th size.
    :param node_color: The color of the nodes of the graph in it's hexadecimal
        value. If a Sequence is specified, it must have the same length of the
        plan and the n'th node will have the n'th color.
    :param edge_color: The color of the edges of the graph in it's hexadecimal
        value. If a Sequence is specified, it must have the length of the
        plan -1 and the n'th edge will have the n'th color.
    :param font_size: The font size of the node labels.
    :param font_color: The font color of the node labels.
    :param draw_networkx_kwargs: This mapping is directly passed to the
        `draw_networkx <https://networkx.org/documentation/stable/reference/generated/networkx.drawing.nx_pylab.draw_networkx.html#networkx.drawing.nx_pylab.draw_networkx>`_
        method; use carefully. NOTE: This parameters is not guaranteed to be
        maintained in any way and it might be removed or modified at any moment.
    """
    if expression_or_expressions is None:
        # plot sequential_plan as graph
        graph = nx.DiGraph()
        if plan.actions:
            current_ai = plan.actions[0]
            for next_ai in plan.actions[1:]:
                graph.add_edge(current_ai, next_ai)
                current_ai = next_ai
        fig, _, _ = _draw_base_graph(
            graph,
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
        if filename is None:
            plt.show()
        else:
            fig.savefig(filename)
    else:
        assert (
            problem is not None
        ), "As documented, if some expressions must be plotted, the problem is required."
        if isinstance(expression_or_expressions, FNode):
            expressions: List[FNode] = [expression_or_expressions]
        else:
            expressions = list(expression_or_expressions)
        for expression in expressions:
            assert isinstance(expression, FNode), "Typing not respected"
            et = expression.type
            assert (
                et.is_bool_type() or et.is_int_type() or et.is_real_type()
            ), f"Expression {expression} has type {et}; but only bool, int or real are plottable"
        sequential_simulator = UPSequentialSimulator(
            problem
        )  # TODO handle unsupported kind
        _plot_expressions(
            plan, problem, expressions, sequential_simulator, filename=filename
        )


def plot_time_triggered_plan(
    problem: Problem,
    plan: "TimeTriggeredPlan",
    *,
    filename: Optional[str] = None,
):
    """
    Plots the TimeTriggered plan as a timeline.

    :param problem: The problem for which the plan is generated.
    :param plan: The plan to plot as a timeline
    :param filename: The path of the file where the plot is saved; if not specified
        the plot will be shown in a pop-up.
    """
    plan_epsilon = plan.extract_epsilon(problem)
    # The data frame created
    data_frame = []
    tick_vals: Set[Union[int, float]] = set()
    x_ticks: Dict[datetime.datetime, str] = {}
    for i, (start, ai, duration) in enumerate(
        sorted(plan.timed_actions, reverse=True, key=lambda x: (x[0], str(x[1])))
    ):
        end = start  # TODO understand if end = start prints a decent action -> NO IT DOES NOT
        if duration is not None:
            end = start + duration
        else:
            end = (
                start + plan_epsilon / 10
            )  # TODO find a better way to represent instantaneous actions in TimeTriggeredPlan
        start, end = float(start), float(end)
        start_date = datetime.datetime.fromtimestamp(start)
        end_date = datetime.datetime.fromtimestamp(end)
        tick_vals.add(start_date)
        tick_vals.add(end_date)
        x_ticks.setdefault(start_date, str(start))
        x_ticks.setdefault(end_date, str(end))
        data_frame.append(
            {
                "Action name": f"{ai}_{i}",
                "start": start_date,
                "end": end_date,
                "color": str(ai),
            }
        )
    plan_plot = px.timeline(
        data_frame, x_start="start", x_end="end", y="Action name", color="color"
    )
    tick_vals_list = list(tick_vals)
    plan_plot.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=tick_vals_list,
            ticktext=list(map(x_ticks.get, tick_vals_list)),
        )
    )
    if filename is not None:
        assert isinstance(filename, str), "typing not respected"
        plan_plot.write_image(file=filename, format="png")
    else:
        plan_plot.show()


def plot_stn_plan(
    plan: "STNPlan",
    *,
    filename: Optional[str] = None,
    top_bottom: bool = False,
    generate_node_label: Optional[Callable[["STNPlanNode"], str]] = None,
    arrowsize: int = ARROWSIZE,
    node_size: Union[int, Sequence[int]] = NODE_SIZE,
    node_color: Union[str, Sequence[str]] = NODE_COLOR,
    edge_color: Union[str, Sequence[str]] = EDGE_COLOR,
    font_size: int = FONT_SIZE,
    font_color: str = FONT_COLOR,
    generate_edge_label: Optional[
        Callable[[Optional[Fraction], Optional[Fraction]], str]
    ] = None,
    edge_font_size: int = EDGE_FONT_SIZE,
    edge_font_color: str = EDGE_FONT_COLOR,
    draw_networkx_kwargs: Optional[Dict[str, Any]] = None,
    draw_networkx_edge_labels_kwargs: Optional[Dict[str, Any]] = None,
):
    """
    This method plots the STN plan as a directed graph where the edges are
    labeled with the temporal constraints contained in the given ``plan``.

    :param plan: The plan to plot.
    :param filename: The path of the file where the plot is saved; if not specified
        the plot will be shown in a pop-up.
    :param top_bottom: If ``True`` the graph will be vertical, if ``False`` it will be
        horizontal.
    :param generate_node_label: The function used to generate the node labels
        of the graph from an ``STNPlanNode``; defaults to the str method.
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
            [Optional[Fraction], Optional[Fraction]], str
        ] = _generate_stn_edge_label
    else:
        edge_label_function = generate_edge_label
    if generate_node_label is None:
        generate_node_label = str
    edge_labels: Dict[Tuple[STNPlanNode, STNPlanNode], str] = {}
    graph = nx.DiGraph()
    for left_node, constraint_list in plan.get_constraints().items():
        for lower_bound, upper_bound, right_node in constraint_list:
            graph.add_edge(left_node, right_node)
            edge_labels[(left_node, right_node)] = edge_label_function(
                lower_bound, upper_bound
            )

    fig, ax, pos = _draw_base_graph(
        plan._graph,
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


def plot_contingent_plan(
    plan: "ContingentPlan",
    *,
    filename: Optional[str] = None,
    top_bottom: bool = False,
    generate_node_label: Optional[Callable[["ContingentPlanNode"], str]] = None,
    arrowsize: int = ARROWSIZE,
    node_size: Union[int, Sequence[int]] = NODE_SIZE,
    node_color: Union[str, Sequence[str]] = NODE_COLOR,
    edge_color: Union[str, Sequence[str]] = EDGE_COLOR,
    font_size: int = FONT_SIZE,
    font_color: str = FONT_COLOR,
    generate_edge_label: Optional[Callable[[Dict[FNode, FNode]], str]] = None,
    edge_font_size: int = EDGE_FONT_SIZE,
    edge_font_color: str = EDGE_FONT_COLOR,
    draw_networkx_kwargs: Optional[Dict[str, Any]] = None,
    draw_networkx_edge_labels_kwargs: Optional[Dict[str, Any]] = None,
):
    """
    This method plots the Contingent plan as a directed graph where the edges are
    labeled with the temporal constraints contained in the given ``plan``.

    :param plan: The plan to plot.
    :param filename: The path of the file where the plot is saved; if not specified
        the plot will be shown in a pop-up.
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
            [Dict[FNode, FNode]], str
        ] = _generate_contingent_edge_label
    else:
        edge_label_function = generate_edge_label
    if generate_node_label is None:
        generate_node_label = lambda x: str(x.action_instance)
    edge_labels: Dict[Tuple[ContingentPlanNode, ContingentPlanNode], str] = {}
    graph = nx.DiGraph()
    for node in visit_tree(plan.root_node):
        for fluents, child in node.children:
            graph.add_edge(node, child)
            edge_labels[(node, child)] = edge_label_function(fluents)

    fig, ax, pos = _draw_base_graph(
        plan._graph,
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


def plot_partial_order_plan(
    plan: "PartialOrderPlan",
    *,
    filename: Optional[str] = None,
    top_bottom: bool = False,
    generate_node_label: Optional[Callable[["ActionInstance"], str]] = None,
    arrowsize: int = ARROWSIZE,
    node_size: Union[int, Sequence[int]] = NODE_SIZE,
    node_color: Union[str, Sequence[str]] = NODE_COLOR,
    edge_color: Union[str, Sequence[str]] = EDGE_COLOR,
    font_size: int = FONT_SIZE,
    font_color: str = FONT_COLOR,
    draw_networkx_kwargs: Optional[Dict[str, Any]] = None,
):
    """
    This method plots the Contingent plan as a directed graph where the edges are
    labeled with the temporal constraints contained in the given ``plan``.

    :param plan: The plan to plot.
    :param filename: The path of the file where the plot is saved; if not specified
        the plot will be shown in a pop-up.
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
    fig, _, _ = _draw_base_graph(
        plan._graph,
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
    if filename is None:
        plt.show()
    else:
        fig.savefig(filename)


def _draw_base_graph(
    graph: nx.DiGraph,
    *,
    top_bottom: bool = False,
    generate_node_label: Optional[
        Union[Callable[["ContingentPlanNode"], str], Callable[["ActionInstance"], str]]
    ] = None,
    arrowsize: int = 20,
    node_size: Union[int, Sequence[int]] = 2000,
    node_color: Union[str, Sequence[str]] = "#1f78b4",
    edge_color: Union[str, Sequence[str]] = "k",
    font_size: int = 8,
    font_color: str = "k",
    draw_networkx_kwargs: Optional[Dict[str, Any]] = None,
):
    # input "sanitization"
    if not top_bottom:
        graph.graph.setdefault("graph", {})["rankdir"] = "LR"
    if generate_node_label is None:
        node_label = str
    else:
        node_label = generate_node_label
    if draw_networkx_kwargs is None:
        draw_networkx_kwargs = {}

    # drawing part
    fig = plt.figure()
    ax = fig.add_subplot()
    pos = nx.nx_agraph.graphviz_layout(graph, prog="dot")
    nx.draw_networkx(
        graph,
        pos,
        labels=dict(map(lambda x: (x, node_label(x)), graph.nodes)),
        arrowstyle="-|>",
        arrowsize=arrowsize,
        node_size=node_size,
        node_color=node_color,
        edge_color=edge_color,
        font_size=font_size,
        font_color=font_color,
        ax=ax,
        **draw_networkx_kwargs,
    )
    return fig, ax, pos


def _generate_contingent_edge_label(fluents: Dict[FNode, FNode]) -> str:
    if not fluents:
        return ""
    fluents_str: str = "\n".join(
        map(lambda x: str(_assignment_as_condition(x)), fluents.items())
    )
    return f"if {fluents_str}"


def _generate_stn_edge_label(
    lower_bound: Optional[Fraction], upper_bound: Optional[Fraction]
) -> str:
    if lower_bound is None:
        lb = "-inf"
    elif lower_bound.denominator == 1:
        lb = str(lower_bound.numerator)
    else:
        lb = str(float(lower_bound))

    if upper_bound is None:
        ub = "+inf"
    elif upper_bound.denominator == 1:
        ub = str(upper_bound.numerator)
    else:
        ub = str(float(upper_bound))
    return f"[{lb}, {ub}]"


def _assignment_as_condition(key_value: Tuple[FNode, FNode]) -> FNode:
    fluent, value = key_value
    em = fluent.environment.expression_manager
    ft = fluent.type
    if ft.is_bool_type() and value.is_true():
        return fluent
    elif ft.is_bool_type() and value.is_false():
        return em.Not(fluent)
    else:
        return em.Equals(fluent, value)


def _plot_expressions(
    plan: "SequentialPlan",
    problem: Problem,
    expressions: List[FNode],
    sequential_simulator: UPSequentialSimulator,
    *,
    filename: Optional[str] = None,
):

    se = StateEvaluator(problem)

    def get_numeric_value_from_state(
        expression: FNode, state: State
    ) -> Union[int, float]:
        exp_value = se.evaluate(expression, state).constant_value()
        if isinstance(exp_value, Fraction):
            exp_value = float(exp_value)
        assert isinstance(exp_value, (int, float))
        return exp_value

    bool_expressions = []
    numeric_expressions = []
    for e in expressions:
        if e.type.is_bool_type():
            bool_expressions.append(e)
        else:
            assert (
                e.type.is_int_type() or e.type.is_real_type()
            ), "Only boolean or numeric fluents can be plot"
            numeric_expressions.append(e)

    # Populate the data_frame with the numeric expressions
    # Populate initial state
    initial_state = sequential_simulator.get_initial_state()
    state_sequence: List[State] = [initial_state]
    current_state = initial_state
    label_str = "<initial value>"
    x_labels: List[str] = [label_str]
    data_frame_element = {"Action name": label_str}
    expressions_str = list(map(str, numeric_expressions))
    for exp, exp_str in zip(numeric_expressions, expressions_str):
        data_frame_element[exp_str] = get_numeric_value_from_state(exp, current_state)
    data_frame = [data_frame_element]

    for action_instance in plan.actions:
        # Compute the new state
        current_state = sequential_simulator.apply(current_state, action_instance)
        if current_state is None:
            # TODO consider raising an exception
            print(f"Error in applying: {action_instance}")
            break
        state_sequence.append(current_state)

        # Populate the data_frame
        label_str = str(action_instance)
        x_labels.append(label_str)
        data_frame_element = {"Action name": label_str}
        for exp, exp_str in zip(numeric_expressions, expressions_str):
            data_frame_element[exp_str] = get_numeric_value_from_state(
                exp, current_state
            )
        data_frame.append(data_frame_element)

    plan_plot = px.line(data_frame, x="Action name", y=expressions_str, markers=True)

    if bool_expressions:

        def get_bool_value_from_state(expression: FNode, state: State) -> int:
            exp_value = se.evaluate(expression, state).bool_constant_value()
            if exp_value:
                return 1
            return 0

        for exp in bool_expressions:
            plan_plot.add_scatter(
                x=x_labels,
                y=list(map(partial(get_bool_value_from_state, exp), state_sequence)),
                line_shape="hv",
                name=str(exp),
                hovertemplate="variable=%s<br>Action name=%%{x}<br>value=%%{y}<extra></extra>"
                % exp,
            )

    if filename is not None:
        assert isinstance(filename, str), "typing not respected"
        plan_plot.write_image(file=filename, format="png")
    else:
        plan_plot.show()
