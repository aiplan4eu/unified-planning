Welcome to Unified-Planning documentation!
==========================================

=============
 Introduction
=============

The Unified-Planning library makes it easy to formulate planning problems and to invoke automated planners.

* Define problems in a *simple*, *intuitive*, and *planner independent* way
* Solve your planning problems using one of the native solvers, or by using any PDDL planner
* Dump your problems in PDDL (or  ANML) format
* Parse PDDL problem formulations
* Simplification, grounding, removal of conditional effects and many other transformations are available
* and more...

The purpose of the library is to provide an abstraction layer for planning technology allowing a user to specify planning problems in a planner independent way and then use one of the available planning engines installed on the system. The library is implemented as a Python package offering high level API to specify planning problems and to invoke planning engineers. Moreover, the library offers functionalities for transforming and simplifying planning problems and to parse  problems from existing formal languages.
The library is being developed publicly under a permissive open-source license (Apache 2.0) and the progress and the code can be followed at https://github.com/aiplan4eu/unified-planning.


Check out our :ref:`Getting Started Guide <getting-started>` and the full :ref:`API Reference <api-ref>`.

Github page of the project available :ref:`here<https://unified-planning.readthedocs.io/en/latest/>`.


Table of Contents
=================

.. toctree::
   :maxdepth: 2

   api_ref
   getting_started
   dev_instructions


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
