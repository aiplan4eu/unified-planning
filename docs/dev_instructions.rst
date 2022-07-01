.. _dev-instructions:

=======================
Developers Instructions
=======================

.. contents::
   :local:

In this guide we present the developers instructions for the Unified-Planning library.

Code formatting
===============

We decided to use `black <https://black.readthedocs.io>` to automatically check and format
the code according to a predefined code style.

For maintaining code formatting and styling, instead of humans correcting the linting mistakes,
we use `pre-commit <https://pre-commit.com/>`.
When you commit staged Python files, before committing pre-commit hooks are executed and
black checks the code formatting. If every check passes, the commit is made else, code
is automatically formatted and sent back for review.
