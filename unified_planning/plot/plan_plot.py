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
from unified_planning.plot.utils import (
    FIGSIZE,
    FIGSIZE_SCALE_FACTOR,
    ARROWSIZE,
    NODE_COLOR,
    EDGE_COLOR,
    FONT_SIZE,
    FONT_COLOR,
    EDGE_FONT_SIZE,
    EDGE_FONT_COLOR,
    draw_base_graph,
)

import datetime
from fractions import Fraction
from functools import partial
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
from unified_planning.model.multi_agent.agent import Agent
import graphviz
import tempfile
import os


def plot_plan(
    plan: "Plan",
    *,
    filename: Optional[str] = None,
    figsize: Optional[Tuple[float, float]] = None,
):
    """
    Method to plot a generic plan; for more control over the overall plot use
    the specific methods for each type of plan.

    :param plan: The plan to plot.
    :param filename: The path of the file where the plot is saved; if not specified
        the plot will be shown in a pop-up.
    :param figsize: Width and height in inches.
    """
    functions_map = {
        SequentialPlan: plot_sequential_plan,
        TimeTriggeredPlan: plot_time_triggered_plan,
        STNPlan: plot_stn_plan,
        ContingentPlan: plot_contingent_plan,
        PartialOrderPlan: plot_partial_order_plan,
    }
    plot_plan_function = functions_map.get(type(plan), None)
    if plot_plan_function is None:
        raise NotImplementedError(
            f"{type(plan).__name__} is not supported in the plot_plan function"
        )
    plot_plan_function(plan=plan, filename=filename, figsize=figsize)  # type: ignore[operator]


def plot_sequential_plan(
    plan: "SequentialPlan",
    problem: Optional[Problem] = None,
    expression_or_expressions: Optional[Union[Expression, Iterable[Expression]]] = None,
    metric_or_metrics: Optional[
        Union[PlanQualityMetric, Iterable[PlanQualityMetric]]
    ] = None,
    *,
    filename: Optional[str] = None,
    figsize: Optional[Tuple[float, float]] = None,
    top_bottom: bool = False,
    generate_node_label: Optional[Callable[["ActionInstance"], str]] = None,
    arrowsize: int = ARROWSIZE,
    node_size: Optional[Union[int, Sequence[int]]] = None,
    node_color: Union[str, Sequence[str]] = NODE_COLOR,
    edge_color: Union[str, Sequence[str]] = EDGE_COLOR,
    font_size: int = FONT_SIZE,
    font_color: str = FONT_COLOR,
    draw_networkx_kwargs: Optional[Dict[str, Any]] = None,
):
    """
    This method has 2 different usage:

    #. when ``expression_or_expressions`` or ``metric_or_metrics`` is specified;
        the problem is required and all the arguments different from ``filename``
        are ignored. This plots all given expressions and metrics in a graph,
        showing the changes during the execution of the plan.
    #. when ``expression_or_expressions`` and ``metric_or_metrics`` are NOT
        specified; this plots the sequential plan simply as a straight graph.
        Minor note: the colors parameter must be a string accepted by
        `draw_networkx <https://networkx.org/documentation/stable/reference/generated/networkx.drawing.nx_pylab.draw_networkx.html#networkx.drawing.nx_pylab.draw_networkx>`_.

    :param plan: The plan to plot or the plan used to get the values of the
        expressions to plot.
    :param problem: The Problem for which the plan is generated; used only if
        ``expression_or_expressions`` or ``metric_or_metrics`` are specified.
    :param expression_or_expressions: The Expressions to plot; this parameter
        defines the mode of this method.
    :param metric_or_metrics: The PlanQUalityMetrics to plot; this parameter
        defines the mode of this method.
    :param filename: The path of the file where the plot is saved; if not specified
        the plot will be shown in a pop-up.
    :param figsize: Width and height in inches or pixels/100 if
        ``expression_or_expressions`` or ``metric_or_metrics`` are specified; for
        example, 10 will be 1000 pixels.
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
    import matplotlib.pyplot as plt  # type: ignore[import]

    if expression_or_expressions is None and metric_or_metrics is None:
        # plot sequential_plan as graph
        graph = nx.DiGraph()
        if plan.actions:
            current_ai = plan.actions[0]
            graph.add_node(current_ai)
            for next_ai in plan.actions[1:]:
                graph.add_edge(current_ai, next_ai)
                current_ai = next_ai
        fig, _, _ = draw_base_graph(
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
        if filename is None:
            plt.show()
        else:
            fig.savefig(filename)
    else:
        assert (
            problem is not None
        ), "As documented, if some expressions must be plotted, the problem is required."
        auto_promote = problem.environment.expression_manager.auto_promote
        expressions = (
            []
            if expression_or_expressions is None
            else auto_promote(expression_or_expressions)
        )
        for expression in expressions:
            assert isinstance(expression, FNode)
            et = expression.type
            assert (
                et.is_bool_type() or et.is_int_type() or et.is_real_type()
            ), f"Expression {expression} has type {et}; but only bool, int or real are plottable"
        if isinstance(metric_or_metrics, PlanQualityMetric):
            metrics: List[PlanQualityMetric] = [metric_or_metrics]
        elif metric_or_metrics is not None:
            metrics = list(metric_or_metrics)
        else:
            metrics = []
        assert all(
            isinstance(metric, PlanQualityMetric) for metric in metrics
        ), "Typing not respected"
        sequential_simulator = UPSequentialSimulator(problem)
        _plot_expressions(
            plan,
            problem,
            expressions,
            metrics,
            sequential_simulator,
            filename=filename,
            figsize=figsize,
        )


def plot_time_triggered_plan(
    plan: "TimeTriggeredPlan",
    *,
    filename: Optional[str] = None,
    figsize: Optional[Tuple[float, float]] = None,
    instantaneous_actions_length: int = 1,
):
    """
    Plots the TimeTriggered plan as a timeline.

    :param plan: The plan to plot as a timeline
    :param filename: The path of the file where the plot is saved; if not specified
        the plot will be shown in a pop-up.
    :param figsize: Width and height in pixels/100; for example (10, 15) means 1000
        pixels wide and 1500 pixels high.
    """

    import plotly.express as px  # type: ignore[import]

    if figsize is None:
        figsize = FIGSIZE
    assert figsize is not None
    # The data frame created
    data_frame = []
    tick_vals: Set[datetime.datetime] = set()
    x_ticks: Dict[datetime.datetime, str] = {}
    y_remapping: Dict[str, str] = {}
    start: Union[float, Fraction] = 0.0
    for i, (start, ai, duration) in enumerate(
        sorted(plan.timed_actions, reverse=True, key=lambda x: (x[0], str(x[1])))
    ):
        if duration is not None:
            end: Union[float, Fraction] = start + duration
        else:
            end = start + instantaneous_actions_length
        start, end = float(start), float(end)
        start_date = datetime.datetime.fromtimestamp(start)
        end_date = datetime.datetime.fromtimestamp(end)
        tick_vals.add(start_date)
        tick_vals.add(end_date)
        x_ticks.setdefault(start_date, str(start))
        x_ticks.setdefault(end_date, str(end))
        y_key = f"{ai}_{i}"
        y_remapping[y_key] = str(ai)
        data_frame.append(
            {
                "Action name": f"{ai}_{i}",
                "start": start_date,
                "end": end_date,
                "color": str(ai.action.name),
            }
        )
    plan_plot = px.timeline(
        data_frame,
        x_start="start",
        x_end="end",
        y="Action name",
        color="color",
        width=figsize[0] * FIGSIZE_SCALE_FACTOR,
        height=figsize[1] * FIGSIZE_SCALE_FACTOR,
    )
    x_tick_vals_list = list(tick_vals)
    y_tick_vals_list = list(y_remapping.keys())
    plan_plot.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=x_tick_vals_list,
            ticktext=list(map(x_ticks.get, x_tick_vals_list)),
            title_text="Time",
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=y_tick_vals_list,
            ticktext=list(map(y_remapping.get, y_tick_vals_list)),
        ),
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
    figsize: Optional[Tuple[float, float]] = None,
    top_bottom: bool = False,
    generate_node_label: Optional[Callable[["STNPlanNode"], str]] = None,
    arrowsize: int = ARROWSIZE,
    node_size: Optional[Union[int, Sequence[int]]] = None,
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
    :param figsize: Width and height in inches.
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
    import matplotlib.pyplot as plt  # type: ignore[import]

    # param "sanitization"
    if generate_edge_label is None:
        edge_label_function: Callable[
            [Optional[Fraction], Optional[Fraction]], str
        ] = _generate_stn_edge_label
    else:
        edge_label_function = generate_edge_label
    if generate_node_label is None:
        generate_node_label = str
    if draw_networkx_edge_labels_kwargs is None:
        draw_networkx_edge_labels_kwargs = {}
    edge_labels: Dict[Tuple[STNPlanNode, STNPlanNode], str] = {}
    graph = nx.DiGraph()
    for left_node, constraint_list in plan.get_constraints().items():
        for lower_bound, upper_bound, right_node in constraint_list:
            graph.add_edge(left_node, right_node)
            edge_labels[(left_node, right_node)] = edge_label_function(
                lower_bound, upper_bound
            )

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
    figsize: Optional[Tuple[float, float]] = None,
    top_bottom: bool = False,
    generate_node_label: Optional[Callable[["ContingentPlanNode"], str]] = None,
    arrowsize: int = ARROWSIZE,
    node_size: Optional[Union[int, Sequence[int]]] = None,
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
    import matplotlib.pyplot as plt  # type: ignore[import]

    # param "sanitization"
    if generate_edge_label is None:
        edge_label_function: Callable[
            [Dict[FNode, FNode]], str
        ] = _generate_contingent_edge_label
    else:
        edge_label_function = generate_edge_label
    if generate_node_label is None:
        generate_node_label = lambda x: str(x.action_instance)
    if draw_networkx_edge_labels_kwargs is None:
        draw_networkx_edge_labels_kwargs = {}
    edge_labels: Dict[Tuple[ContingentPlanNode, ContingentPlanNode], str] = {}
    graph = nx.DiGraph()
    for node in visit_tree(plan.root_node):
        graph.add_node(node)
        for fluents, child in node.children:
            graph.add_edge(node, child)
            edge_labels[(node, child)] = edge_label_function(fluents)

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
    figsize: Optional[Tuple[float, float]] = None,
    top_bottom: bool = False,
    generate_node_label: Optional[Callable[["ActionInstance"], str]] = None,
    arrowsize: int = ARROWSIZE,
    node_size: Optional[Union[int, Sequence[int]]] = None,
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
    import matplotlib.pyplot as plt  # type: ignore[import]

    fig, _, _ = draw_base_graph(
        plan._graph,
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
    if filename is None:
        plt.show()
    else:
        fig.savefig(filename)


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
    metrics: List[PlanQualityMetric],
    sequential_simulator: UPSequentialSimulator,
    *,
    filename: Optional[str] = None,
    figsize: Optional[Tuple[float, float]] = None,
):

    import plotly.express as px  # type: ignore[import]

    if figsize is None:
        figsize = FIGSIZE
    assert figsize is not None
    se = StateEvaluator(problem)

    def fraction_to_float(number: Union[int, Fraction]) -> Union[int, float]:
        if isinstance(number, Fraction):
            if number.denominator == 1:
                return number.numerator
            return float(number)
        return number

    def get_numeric_value_from_state(
        expression: FNode, state: State
    ) -> Union[int, float]:
        exp_value: Union[int, Fraction] = se.evaluate(
            expression, state
        ).constant_value()
        return fraction_to_float(exp_value)

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
    metric_values: Dict[PlanQualityMetric, Union[int, Fraction]] = {
        metric: evaluate_quality_metric_in_initial_state(sequential_simulator, metric)
        for metric in metrics
    }
    state_sequence: List[State] = [initial_state]
    current_state: Optional[State] = initial_state
    label_str = "<initial value>"
    x_labels: List[str] = [label_str]
    data_frame_element: Dict[str, Any] = {"Action name": label_str}
    expressions_str = list(map(str, numeric_expressions))
    for exp, exp_str in zip(numeric_expressions, expressions_str):
        assert current_state is not None
        data_frame_element[exp_str] = get_numeric_value_from_state(exp, current_state)
    for metric, value in metric_values.items():
        data_frame_element[str(metric)] = fraction_to_float(value)
    data_frame = [data_frame_element]

    for action_instance in plan.actions:
        # Compute the new state
        assert current_state is not None
        previous_state = current_state
        current_state = sequential_simulator.apply(current_state, action_instance)
        if current_state is None:
            print(f"Error in applying: {action_instance}")
            break
        state_sequence.append(current_state)

        # Update the metric values
        eqm = partial(
            evaluate_quality_metric,
            simulator=sequential_simulator,
            state=previous_state,
            action=action_instance.action,
            parameters=action_instance.actual_parameters,
            next_state=current_state,
        )
        metric_values = dict(
            map(
                lambda x: (x[0], eqm(quality_metric=x[0], metric_value=x[1])),
                metric_values.items(),
            )
        )

        # Populate the data_frame
        label_str = str(action_instance)
        x_labels.append(label_str)
        data_frame_element = {"Action name": label_str}
        for exp, exp_str in zip(numeric_expressions, expressions_str):
            data_frame_element[exp_str] = get_numeric_value_from_state(
                exp, current_state
            )
        for metric, value in metric_values.items():
            data_frame_element[str(metric)] = fraction_to_float(value)
        data_frame.append(data_frame_element)

    expressions_str.extend(map(str, metrics))
    plan_plot = px.line(
        data_frame,
        x="Action name",
        y=expressions_str,
        markers=True,
        width=figsize[0] * FIGSIZE_SCALE_FACTOR,
        height=figsize[1] * FIGSIZE_SCALE_FACTOR,
    )

    # plot boolean expressions
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


class GraphvizGenerator:
    available_colors = [
        "firebrick2",
        "gold2",
        "cornflowerblue",
        "darkorange1",
        "darkgreen",
        "coral4",
        "darkviolet",
        "deeppink1",
        "deepskyblue4",
        "burlywood4",
        "gray32",
        "lightsteelblue4",
    ]
    random_color_counter = 0

    @classmethod
    def get_next_agent_color(cls) -> str:
        if cls.random_color_counter < len(cls.available_colors):
            color = cls.available_colors[cls.random_color_counter]
            cls.random_color_counter += 1
        else:
            # Se gli available_colors sono esauriti, genera un colore casuale
            color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        return color

    @classmethod
    def create_graphviz_output(
        cls,
        adjacency_list: Dict[
            "plans.plan.ActionInstance", List["plans.plan.ActionInstance"]
        ],
    ) -> str:
        """
        Creates Graphviz output with colors for agents if present, otherwise without colors.

        :param adjacency_list: The adjacency list representing the partial order plan.
        :return: The Graphviz representation as a string.
        """
        for action_instance, _ in adjacency_list.items():
            if action_instance.agent is not None:
                return cls._create_graphviz_output_with_agents(adjacency_list)
        return cls._create_graphviz_output_simple(adjacency_list)

    @classmethod
    def _create_graphviz_output_with_agents(
        cls,
        adjacency_list: Dict[
            "plans.plan.ActionInstance", List["plans.plan.ActionInstance"]
        ],
    ) -> str:
        agent_colors = {}
        graphviz_out = ""
        graphviz_out += "digraph {\n"

        # Scansione della adjacency_list per identificare gli agenti
        for start, end_list in adjacency_list.items():
            agent_name = start.agent
            if agent_name not in agent_colors:
                # Generazione di un colore per l'agente
                color = cls.get_next_agent_color()
                agent_colors[agent_name] = color

        # Creazione del grafo con colori degli agenti
        for start, end_list in adjacency_list.items():
            agent_name = start.agent
            agent_color = agent_colors.get(agent_name, "black")
            graphviz_out += f'\t"{start}" [color="{agent_color}"]\n'
            for end in end_list:
                graphviz_out += f'\t"{start}" -> "{end}"\n'

        # Creazione della legenda
        graphviz_out += "\t// Legenda\n"
        graphviz_out += "\t{\n"
        graphviz_out += "\t\trank = max;\n"
        graphviz_out += '\t\tlabel="Legenda";\n'
        graphviz_out += '\t\tlabelloc="b";\n'
        graphviz_out += '\t\trankdir="LR";\n'

        for agent_name, agent_color in agent_colors.items():
            if agent_name is not None and isinstance(agent_name, Agent):
                graphviz_out += f'\t\t"{agent_name.name}" [shape=none, margin=0, label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"><TR><TD WIDTH="30" HEIGHT="30" ALIGN="CENTER" BGCOLOR="{agent_color}"></TD><TD>{agent_name.name}</TD></TR></TABLE>>];\n'

        graphviz_out += "\t}\n"
        graphviz_out += "}"

        return graphviz_out

    @classmethod
    def _create_graphviz_output_simple(
        cls,
        adjacency_list: Dict[
            "plans.plan.ActionInstance", List["plans.plan.ActionInstance"]
        ],
    ) -> str:
        """
        Creates Graphviz output without agents.

        :param adjacency_list: The adjacency list representing the partial order plan.
        :return: The Graphviz representation as a string.
        """
        graphviz_out = ""
        graphviz_out += "digraph {\n"
        for start, end_list in adjacency_list.items():
            for end in end_list:
                graphviz_out += f'\t"{start}" -> "{end}"\n'
        graphviz_out += "}"
        return graphviz_out


def graphviz_partial_order_plan(
    plan: "PartialOrderPlan", filename: Optional[str] = None
):

    graphviz_out = GraphvizGenerator.create_graphviz_output(plan.get_adjacency_list)
    graph = graphviz.Source(graphviz_out)

    def get_graph_file(file_name: str) -> str:
        with open(f"{file_name}.dot", "w") as f:
            f.write(graphviz_out)
        return graphviz_out

    if filename is None:
        # If filename is None, show the image without saving it locally
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_name = temp_file.name
            graph.render(filename=temp_file_name, format="svg", view=True)
    else:
        # Otherwise, save the image and graph with a .dot extension
        get_graph_file(filename)
        graph.render(filename=filename, format="svg", view=True)
