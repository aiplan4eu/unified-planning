Problem Representation
=====================

The main functionality offered by the library concerns the specification of a planning problem. The API provides classes and functions to populate a Problem object with the fluents, actions, initial states and goal specifications constituting the planning problem specification.
The functionalities for creating model objects and to manipulate them are collected in the unified_planning.model package of the library.

Example
-------
The following example shows a simple robotic planning problem modeling a robot moving between locations while consuming battery. The example shows the basic functionalities and objects needed to declare the problem specification. A more detailed presentation of the different objects is available on the `Google Colab <https://colab.research.google.com/github/aiplan4eu/unified-planning/blob/master/notebooks/Unified_Planning_Basics.ipynb>`_ Python notebook where we document and explain all the different classes and their semantics.

.. literalinclude:: ./code_snippets/robot_battery.py
    :lines: 3-38


In the current version, the Unified-Planning library allows the specification of classical, numerical and temporal planning problems. In order to support the latitude expressiveness levels we have operators for arithmetic such as plus minus times and division and specific temporal operators to attach conditions and effects to specific timings within the duration of an action. The library :ref:`documentation <api-ref>` provides examples and describes the use of these functionalities.

