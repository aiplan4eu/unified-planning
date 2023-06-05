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


from functools import partial
from numbers import Real
import unified_planning as up
from unified_planning.engines.sequential_simulator import UPSequentialSimulator
from unified_planning.model import FNode, Problem, State
from unified_planning.model.walkers import StateEvaluator
from unified_planning.plans.plan import ActionInstance
from unified_planning.plans.sequential_plan import SequentialPlan
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
from typing import Dict, Iterator, List, Optional, Sequence, Set, Tuple, Union, Callable


def plot_sequential_plan(
    plan: "SequentialPlan",
    problem: Optional[Problem] = None,
    fluent_or_fluents: Optional[
        Union[FNode, Sequence[FNode]]
    ] = None,  # TODO accept arbitrary NUMERIC (or boolean) expression?
    *,
    filename: Optional[str] = None,
    sequential_simulator: Optional[UPSequentialSimulator] = None,
):
    if fluent_or_fluents is None:
        # plot sequential_plan as graph
        graph = nx.DiGraph()
        if plan.actions:
            current_ai = plan.actions[0]
            for next_ai in plan.actions[1:]:
                graph.add_edge(current_ai, next_ai)
                current_ai = next_ai
        fig, _, _ = _draw_base_graph(graph)
        if filename is None:
            fig.show()
        else:
            fig.savefig(filename)
        return

    assert (
        problem is not None
    ), "As docuemented, if some fluents must be plotted, the problem is required."
    if isinstance(fluent_or_fluents, FNode):
        fluents: List[FNode] = [fluent_or_fluents]
    else:
        assert isinstance(fluent_or_fluents, Sequence[FNode]), "Typing not respected"
        fluents = list(fluent_or_fluents)
    fluents_type = fluents[0].type
    for fluent in fluents:
        assert fluent.type == fluents_type
    if sequential_simulator is not None:
        assert (
            sequential_simulator._problem == problem
        ), "Different problem from method parameter to simulator problem"
    else:
        # TODO handle unsupported kind
        sequential_simulator = UPSequentialSimulator(problem)
    assert sequential_simulator is not None

    se = StateEvaluator(problem)

    def get_value_from_state(expression: FNode, state: State) -> Union[int, float]:
        value = se.evaluate(expression, state).constant_value()
        if isinstance(value, bool):
            if value:
                return 1
            return 0
        assert isinstance(value, (int, float))
        return value

    initial_state = sequential_simulator.get_initial_state()
    labels = ["<initial value>"]
    state_sequence: List[State] = [initial_state]
    # fluents_values: Dict[FNode, List[FNode]] = {}
    # for fluent in fluent_or_fluents:
    #     fluents_values[fluent] = [initial_state.get_value(fluent).constant_value()]
    current_state = initial_state
    data_frame = [
        {
            "Action name": f"<initial value>",
            "Fluent value": list(
                map(partial(get_value_from_state, state=current_state), fluents)
            ),
        }
    ]
    for action_instance in plan.actions:
        current_state = sequential_simulator.apply(current_state, action_instance)
        if current_state is None:
            # TODO consider raising an exception
            print(f"Error in applying: {action_instance}")
            break
        labels.append(str(action_instance))
        state_sequence.append(current_state)
        # for fluent in fluent_or_fluents:
        #     fluent_value = current_state.get_value(fluent).constant_value()
        #     fluents_values[fluent].append(fluent_value)
        data_frame.append(
            {
                "Action name": str(action_instance),
                "Fluent value": list(
                    map(partial(get_value_from_state, state=current_state), fluents)
                ),
            }
        )
    plan_plot = px.line(data_frame, x="Action name", y="Fluent value", markers=True)
    if filename is not None:
        assert isinstance(filename, str), "typing not respected"
        with open(filename, "w") as image_file:
            plan_plot.write_image(file=image_file, format="png")
    else:
        plan_plot.show()


def plot_time_triggered_plan(
    problem: Problem,
    plan: "TimeTriggeredPlan",  # notes different
    *,
    filename: Optional[str] = None,
):
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
        with open(filename, "w") as image_file:
            plan_plot.write_image(file=image_file, format="png")
    else:
        plan_plot.show()


def plot_contingent_plan(
    plan: "ContingentPlan",
    *,
    filename: Optional[str] = None,
    top_bottom: bool = False,
    generate_node_label: Optional[Callable[["ContingentPlanNode"], str]] = None,
    generate_edge_label: Optional[Callable[[Dict[FNode, FNode]], str]] = None,
):
    # param "sanitization"
    if generate_edge_label is None:
        edge_label_function: Callable[[Dict[FNode, FNode]], str] = _generate_edge_label
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
    )
    nx.draw_networkx_edge_labels(
        graph,
        pos,
        edge_labels=edge_labels,
        font_size=6,
        ax=ax,
    )
    if filename is None:
        fig.show()
    else:
        fig.savefig(filename)


def plot_partial_order_plan(
    plan: "PartialOrderPlan",
    *,
    filename: Optional[str] = None,
    top_bottom: bool = False,
    generate_node_label: Optional[Callable[["ActionInstance"], str]] = None,
):
    fig, _, _ = _draw_base_graph(
        plan._graph,
        top_bottom=top_bottom,
        generate_node_label=generate_node_label,
    )
    if filename is None:
        fig.show()
    else:
        fig.savefig(filename)


def _draw_base_graph(  # TODO add kwargs
    graph: nx.DiGraph,
    *,
    top_bottom: bool = False,
    generate_node_label: Optional[
        Union[Callable[["ContingentPlanNode"], str], Callable[["ActionInstance"], str]]
    ] = None,
):
    # input "sanitization"
    if not top_bottom:
        graph.graph.setdefault("graph", {})["rankdir"] = "LR"
    if generate_node_label is None:
        node_label = str
    else:
        node_label = generate_node_label

    # drawing part
    fig = plt.figure()
    ax = fig.add_subplot()
    pos = nx.nx_agraph.graphviz_layout(graph, prog="dot")
    nx.draw_networkx(
        graph,
        pos,
        labels=dict(map(lambda x: (x, node_label(x)), graph.nodes)),
        arrowstyle="-|>",
        arrowsize=20,
        node_size=2000,
        font_size=8,
        ax=ax,
    )
    return fig, ax, pos


def _generate_edge_label(fluents: Dict[FNode, FNode]) -> str:
    if not fluents:
        return ""
    fluents_str: str = "\n".join(
        map(lambda x: str(_assignment_as_condition(x)), fluents.items())
    )
    return f"if {fluents_str}"


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
