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
"""Helpers shared by the text-based writers in this package."""

from decimal import Decimal, localcontext
from fractions import Fraction
from warnings import warn


def decimal_literal(frac: Fraction, precision: int, printer: str) -> str:
    """Formats a Fraction as a `digits "." digits` decimal literal.

    Neither the PDDL nor the ANML numeric grammar accepts scientific notation or a
    `numerator/denominator` fraction, so the value is rendered with `format(dec, "f")`
    and always given a fractional part (which the ANML `real` production requires and
    PDDL accepts).

    :param frac: The value to render.
    :param precision: Significant digits used to round `frac`.
    :param printer: Printer name used in the warning raised when `frac` has no exact
        terminating decimal representation at `precision` digits.
    :return: `frac` formatted as a plain decimal literal.

    >>> decimal_literal(Fraction(1, 100000), 10, "PDDL")
    '0.00001'
    >>> decimal_literal(Fraction(10), 10, "ANML")
    '10.0'
    """
    with localcontext() as ctx:
        ctx.prec = precision
        dec = frac.numerator / Decimal(frac.denominator, ctx)
        if Fraction(dec) != frac:
            warn(
                f"The {printer} printer cannot exactly represent the real constant '{frac}'",
                stacklevel=2,
            )
        res = format(dec, "f")  # never scientific notation
    return res if "." in res else f"{res}.0"  # some grammars require a fractional part
