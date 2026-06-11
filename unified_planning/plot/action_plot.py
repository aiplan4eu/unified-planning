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
"""
This module provides a schematic (non-metric) visualization of the actions of a
:class:`~unified_planning.model.Problem`.

Differently from the rest of the :mod:`unified_planning.plot` package (which draws
graphs and timelines), the functions here lay out each action "by hand" with
matplotlib patches:

 - Instantaneous actions are a vertical bar; preconditions are drawn above it and
   effects (``fluent := / += / -= expression``) below it.
 - Durative actions are a rectangle representing the ``[start, end]`` interval. Start
   conditions/effects are anchored to the left edge, end ones to the right edge and
   intermediate ones to interior vertical bars. The duration constraint is written
   inside the rectangle and "overall"/sub-interval conditions are double-headed arrows
   above it, spanning the relevant (sub-)interval.
 - Events are drawn like instantaneous actions but with a squiggly bar.
 - Processes are a rectangle (of a different color) with their preconditions shown as
   an overall condition above and their (continuous) effects below.

All conditions are suffixed with ``?`` and all effects with ``!``.
"""

from fractions import Fraction
from typing import List, Optional, Tuple

import unified_planning as up
from unified_planning.model.action import InstantaneousAction, DurativeAction
from unified_planning.model.effect import Effect
from unified_planning.model.natural_transition import Event, Process
from unified_planning.plot.utils import FIGSIZE, NODE_COLOR, FONT_SIZE

# Default colors (see the module docstring for the encoding)
INSTANTANEOUS_COLOR = "k"
EVENT_COLOR = "#ff7f0e"
DURATIVE_COLOR = NODE_COLOR  # "#1f78b4"
PROCESS_COLOR = "#2ca02c"

# Layout constants, expressed in "em" units (1 unit == font_size points once rendered).
_CHAR_W = 0.6  # approximate width of one character
_LINE_H = 1.6  # vertical space reserved for one line of text
_BAR_H = 3.0  # vertical extent of a bar / rectangle
_NAME_PAD = 1.0  # gap between the action name and its drawing
_COL_PAD = 2.0  # horizontal padding added to the widest column text
_COL_MIN = 4.0  # minimum column / box width
_GAP = 0.6  # gap between the bar and the surrounding text
_LANE_GAP = 2.0  # vertical gap between two stacked actions
_MARGIN = 2.0  # outer margin around the whole drawing


def _text_w(s: str) -> float:
    """Approximate rendered width of ``s`` in em units."""
    return len(s) * _CHAR_W


def _format_condition(condition: "up.model.fnode.FNode") -> str:
    """Renders a (boolean) condition expression, suffixed with ``?``."""
    return f"{condition}?"


def _format_effect(effect: Effect) -> str:
    """
    Renders an effect, suffixed with ``!``. Handles assignment/increase/decrease and
    continuous effects, conditional (guarded) effects and universally quantified
    (``forall``) effects.
    """
    fluent, value = str(effect.fluent), str(effect.value)
    if effect.is_continuous_increase():
        core = f"d({fluent})/dt += {value}"
    elif effect.is_continuous_decrease():
        core = f"d({fluent})/dt -= {value}"
    elif effect.is_increase():
        core = f"{fluent} += {value}"
    elif effect.is_decrease():
        core = f"{fluent} -= {value}"
    else:
        core = f"{fluent} := {value}"
    if effect.is_conditional():
        core = f"{effect.condition}? => {core}"
    if effect.is_forall():
        variables = ", ".join(str(v) for v in effect.forall)
        core = f"forall {variables}: {core}"
    return f"{core} !"


def _format_duration(duration: "up.model.timing.DurationInterval") -> str:
    """Renders the duration constraint of a durative action."""
    lower, upper = str(duration.lower), str(duration.upper)
    if duration.lower == duration.upper:
        return f"dur = {lower}"
    left = "(" if duration.is_left_open() else "["
    right = ")" if duration.is_right_open() else "]"
    return f"dur in {left}{lower}, {upper}{right}"


def _draw_squiggle(ax, x: float, y0: float, y1: float, color: str) -> None:
    """Draws a vertical squiggly (sine wave) bar between ``y0`` and ``y1``."""
    import numpy as np  # type: ignore[import]
    from matplotlib.lines import Line2D  # type: ignore[import]

    ys = np.linspace(y0, y1, 50)
    periods = max(1.0, (y1 - y0))
    xs = x + 0.25 * np.sin((ys - y0) / (y1 - y0) * periods * 2 * np.pi)
    ax.add_line(Line2D(xs, ys, color=color, lw=2))


def _draw_span_arrow(
    ax, x1: float, x2: float, y: float, label: str, color: str, font_size: int
) -> None:
    """Draws a double-headed arrow between ``x1`` and ``x2`` with a centered label."""
    from matplotlib.patches import FancyArrowPatch  # type: ignore[import]

    ax.add_patch(
        FancyArrowPatch(
            (x1, y),
            (x2, y),
            arrowstyle="<->",
            mutation_scale=10,
            color=color,
            lw=1,
        )
    )
    if label:
        ax.text(
            (x1 + x2) / 2,
            y + 0.4,
            label,
            ha="center",
            va="bottom",
            fontsize=font_size * 0.85,
        )


def _action_label(action) -> str:
    """
    Returns the action's signature, e.g. ``move`` or ``move(l_from: Location, l_to:
    Location)`` when it has parameters.
    """
    parameters = action.parameters
    if not parameters:
        return action.name
    signature = ", ".join(f"{p.name}: {p.type}" for p in parameters)
    return f"{action.name}({signature})"


def _draw_name(ax, action, x: float, y: float, font_size: int) -> None:
    """Draws the action signature, left aligned and vertically centered on ``y``."""
    ax.text(
        x,
        y,
        _action_label(action),
        ha="left",
        va="center",
        fontsize=font_size,
        fontweight="bold",
    )


def _draw_bar(
    ax, action, x0: float, y0: float, color: str, font_size: int, squiggle: bool
) -> Tuple[float, float]:
    """Draws an instantaneous action (``squiggle=False``) or an event (``True``)."""
    from matplotlib.lines import Line2D  # type: ignore[import]

    conditions = [_format_condition(p) for p in action.preconditions]
    effects = [_format_effect(e) for e in action.effects]
    text_w = max([1.0] + [_text_w(s) for s in conditions + effects])
    name_w = _text_w(_action_label(action))

    bar_x = x0 + name_w + _NAME_PAD + text_w / 2
    bar_y0 = y0 + len(effects) * _LINE_H + _GAP
    bar_y1 = bar_y0 + _BAR_H

    if squiggle:
        _draw_squiggle(ax, bar_x, bar_y0, bar_y1, color)
    else:
        ax.add_line(Line2D([bar_x, bar_x], [bar_y0, bar_y1], color=color, lw=3))

    for j, s in enumerate(conditions):
        ax.text(bar_x, bar_y1 + (j + 0.5) * _LINE_H, s, ha="center", va="center", fontsize=font_size * 0.85)
    for j, s in enumerate(effects):
        ax.text(bar_x, bar_y0 - (j + 0.5) * _LINE_H, s, ha="center", va="center", fontsize=font_size * 0.85)
    _draw_name(ax, action, x0, (bar_y0 + bar_y1) / 2, font_size)

    height = len(effects) * _LINE_H + _GAP + _BAR_H + len(conditions) * _LINE_H + _GAP
    width = name_w + _NAME_PAD + text_w
    return width, height


def _timing_key(timing: "up.model.timing.Timing") -> Tuple[int, float]:
    """
    Schematic ordering key for a timing: start-anchored timings come before
    end-anchored ones, ordered by their (symbolic) delay.
    """
    return (0 if timing.is_from_start() else 1, float(timing.delay))


def _draw_durative(
    ax, action: DurativeAction, x0: float, y0: float, color: str, font_size: int
) -> Tuple[float, float]:
    """Draws a durative action as an annotated rectangle."""
    from matplotlib.lines import Line2D  # type: ignore[import]
    from matplotlib.patches import Rectangle  # type: ignore[import]

    start_key, end_key = (0, 0.0), (1, 0.0)
    column_keys = {start_key, end_key}
    for timing in action.effects:
        column_keys.add(_timing_key(timing))
    for interval in action.conditions:
        column_keys.add(_timing_key(interval.lower))
        column_keys.add(_timing_key(interval.upper))
    for interval in action.continuous_effects:
        column_keys.add(_timing_key(interval.lower))

    order = sorted(column_keys)
    index = {key: i for i, key in enumerate(order)}
    n = len(order)
    above: List[List[str]] = [[] for _ in range(n)]
    below: List[List[str]] = [[] for _ in range(n)]
    spans: List[Tuple[int, int, str]] = []

    for timing, effects in action.effects.items():
        below[index[_timing_key(timing)]].extend(_format_effect(e) for e in effects)
    for interval, effects in action.continuous_effects.items():
        below[index[_timing_key(interval.lower)]].extend(_format_effect(e) for e in effects)
    for interval, conditions in action.conditions.items():
        lower_key, upper_key = _timing_key(interval.lower), _timing_key(interval.upper)
        if lower_key == upper_key:
            above[index[lower_key]].extend(_format_condition(c) for c in conditions)
        else:
            label = "; ".join(_format_condition(c) for c in conditions)
            spans.append((index[lower_key], index[upper_key], label))

    column_text_w = [
        max([0.0] + [_text_w(s) for s in above[i] + below[i]]) for i in range(n)
    ]
    duration_text = _format_duration(action.duration)
    column_w = max(_COL_MIN, max(column_text_w) + _COL_PAD)
    # widen the columns if needed so the duration text fits inside the rectangle
    column_w = max(column_w, (_text_w(duration_text) + _COL_PAD) / max(1, n - 1))

    name_w = _text_w(_action_label(action))
    left_pad = column_text_w[0] / 2
    right_pad = column_text_w[-1] / 2
    box_left = x0 + name_w + _NAME_PAD + left_pad
    column_x = [box_left + i * column_w for i in range(n)]
    box_right = column_x[-1]

    n_above = max([0] + [len(c) for c in above])
    n_below = max([0] + [len(c) for c in below])
    box_y0 = y0 + n_below * _LINE_H + _GAP
    box_y1 = box_y0 + _BAR_H

    ax.add_patch(
        Rectangle(
            (box_left, box_y0),
            box_right - box_left,
            _BAR_H,
            facecolor=color,
            edgecolor="k",
            alpha=0.5,
            lw=1.5,
        )
    )
    ax.text((box_left + box_right) / 2, (box_y0 + box_y1) / 2, duration_text, ha="center", va="center", fontsize=font_size * 0.9)
    for i in range(1, n - 1):  # interior intermediate bars
        ax.add_line(Line2D([column_x[i], column_x[i]], [box_y0, box_y1], color="k", lw=1))
    for i in range(n):
        for j, s in enumerate(above[i]):
            ax.text(column_x[i], box_y1 + (j + 0.5) * _LINE_H, s, ha="center", va="center", fontsize=font_size * 0.85)
        for j, s in enumerate(below[i]):
            ax.text(column_x[i], box_y0 - (j + 0.5) * _LINE_H, s, ha="center", va="center", fontsize=font_size * 0.85)

    span_base = box_y1 + n_above * _LINE_H + _GAP
    for s_i, (i, j, label) in enumerate(spans):
        _draw_span_arrow(ax, column_x[i], column_x[j], span_base + s_i * _LINE_H + 0.3, label, "k", font_size)
    _draw_name(ax, action, x0, (box_y0 + box_y1) / 2, font_size)

    height = n_below * _LINE_H + _GAP + _BAR_H + n_above * _LINE_H + len(spans) * _LINE_H + _GAP
    width = name_w + _NAME_PAD + left_pad + (box_right - box_left) + right_pad
    return width, height


def _draw_process(
    ax, action: Process, x0: float, y0: float, color: str, font_size: int
) -> Tuple[float, float]:
    """Draws a process as a rectangle with overall preconditions and effects below."""
    from matplotlib.patches import Rectangle  # type: ignore[import]

    conditions = [_format_condition(p) for p in action.preconditions]
    effects = [_format_effect(e) for e in action.effects]
    label = "; ".join(conditions)
    text_w = max([_COL_MIN] + [_text_w(s) for s in effects] + [_text_w(label)])
    name_w = _text_w(_action_label(action))

    box_w = text_w + _COL_PAD
    box_left = x0 + name_w + _NAME_PAD
    box_right = box_left + box_w
    box_y0 = y0 + len(effects) * _LINE_H + _GAP
    box_y1 = box_y0 + _BAR_H

    ax.add_patch(
        Rectangle((box_left, box_y0), box_w, _BAR_H, facecolor=color, edgecolor="k", alpha=0.5, lw=1.5)
    )
    ax.text((box_left + box_right) / 2, (box_y0 + box_y1) / 2, "process", ha="center", va="center", fontsize=font_size * 0.9, style="italic")
    for j, s in enumerate(effects):
        ax.text((box_left + box_right) / 2, box_y0 - (j + 0.5) * _LINE_H, s, ha="center", va="center", fontsize=font_size * 0.85)
    n_span = 0
    if conditions:
        _draw_span_arrow(ax, box_left, box_right, box_y1 + _GAP + 0.3, label, "k", font_size)
        n_span = 1
    _draw_name(ax, action, x0, (box_y0 + box_y1) / 2, font_size)

    height = len(effects) * _LINE_H + _GAP + _BAR_H + n_span * _LINE_H + _GAP
    width = name_w + _NAME_PAD + box_w
    return width, height


def _draw_action(
    ax,
    action,
    x0: float,
    y0: float,
    instantaneous_color: str,
    event_color: str,
    durative_color: str,
    process_color: str,
    font_size: int,
) -> Tuple[float, float]:
    """Dispatches to the right drawing routine; returns the consumed ``(width, height)``."""
    if isinstance(action, DurativeAction):
        return _draw_durative(ax, action, x0, y0, durative_color, font_size)
    elif isinstance(action, InstantaneousAction):
        return _draw_bar(ax, action, x0, y0, instantaneous_color, font_size, squiggle=False)
    elif isinstance(action, Event):
        return _draw_bar(ax, action, x0, y0, event_color, font_size, squiggle=True)
    elif isinstance(action, Process):
        return _draw_process(ax, action, x0, y0, process_color, font_size)
    else:
        raise NotImplementedError(f"Plotting of {type(action).__name__} is not supported")


def _finalize(ax, content_w, content_h, figsize, filename, font_size):
    """Sets axis limits/aspect, sizes the figure to the content, then shows or saves."""
    import matplotlib.pyplot as plt  # type: ignore[import]

    ax.set_xlim(-_MARGIN, content_w + _MARGIN)
    ax.set_ylim(-_MARGIN, content_h + _MARGIN)
    ax.set_aspect("equal")
    ax.axis("off")
    fig = ax.get_figure()
    if figsize is None:
        scale = font_size / 72.0  # em units -> inches
        figsize = (
            max(4.0, min((content_w + 2 * _MARGIN) * scale, 25.0)),
            max(3.0, min((content_h + 2 * _MARGIN) * scale, 40.0)),
        )
    fig.set_size_inches(*figsize)
    if filename is None:
        plt.show()
    else:
        fig.savefig(filename, bbox_inches="tight")


def plot_action(
    action,
    *,
    ax=None,
    x_offset: float = 0.0,
    y_offset: float = 0.0,
    filename: Optional[str] = None,
    figsize: Optional[Tuple[float, float]] = None,
    instantaneous_color: str = INSTANTANEOUS_COLOR,
    event_color: str = EVENT_COLOR,
    durative_color: str = DURATIVE_COLOR,
    process_color: str = PROCESS_COLOR,
    font_size: int = FONT_SIZE,
) -> Tuple[float, float]:
    """
    Draws a single ``action`` (an ``InstantaneousAction``, ``DurativeAction``,
    ``Event`` or ``Process``) as a schematic.

    If ``ax`` is given the action is drawn into it at ``(x_offset, y_offset)`` and the
    consumed ``(width, height)`` is returned without showing/saving (this is how
    :func:`plot_actions` lays out its lanes). If ``ax`` is ``None`` a new figure is
    created, finalized and either shown (``filename`` is ``None``) or saved.
    """
    standalone = ax is None
    if standalone:
        import matplotlib.pyplot as plt  # type: ignore[import]

        _, ax = plt.subplots()
    width, height = _draw_action(
        ax,
        action,
        x_offset,
        y_offset,
        instantaneous_color,
        event_color,
        durative_color,
        process_color,
        font_size,
    )
    if standalone:
        _finalize(ax, x_offset + width, y_offset + height, figsize, filename, font_size)
    return width, height


def plot_actions(
    problem: "up.model.Problem",
    *,
    filename: Optional[str] = None,
    figsize: Optional[Tuple[float, float]] = None,
    instantaneous_color: str = INSTANTANEOUS_COLOR,
    event_color: str = EVENT_COLOR,
    durative_color: str = DURATIVE_COLOR,
    process_color: str = PROCESS_COLOR,
    font_size: int = FONT_SIZE,
) -> None:
    """
    Draws all the actions, events and processes of ``problem`` as schematics, stacked
    top-to-bottom in a single figure with the names on the left.

    The figure is shown if ``filename`` is ``None``, otherwise it is saved to it.
    """
    import matplotlib.pyplot as plt  # type: ignore[import]

    items = list(problem.actions) + list(problem.events) + list(problem.processes)
    _, ax = plt.subplots()

    y, max_w = 0.0, 0.0
    # draw in reverse so that the first item ends up on top of the stack
    for item in reversed(items):
        width, height = _draw_action(
            ax,
            item,
            0.0,
            y,
            instantaneous_color,
            event_color,
            durative_color,
            process_color,
            font_size,
        )
        max_w = max(max_w, width)
        y += height + _LANE_GAP

    content_h = max(0.0, y - _LANE_GAP)
    _finalize(ax, max_w, content_h, figsize, filename, font_size)
