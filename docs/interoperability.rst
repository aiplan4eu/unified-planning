I/O & Interoperability
=================================

Finally, the Unified-Planning library offers primitives and functions for the interoperability with external formal languages and libraries. In particular, we offer a strong integration with the Planning Domain Definition Language (PDDL) language: we implemented a parser that can read in a problem specified in PDDL and convert it into a Unified-Planning problem data structure, and we have a comprehensive emitter that yelds PDDL specifications from a Unified-Planning problem instance.
We also have automatic interfacing with other planning libraries. In particular, we have a conversion from a ``tarski`` representation into a Unified-Planning problem allowing a user to import from this external data structure and simplify the interoperability between the two libraries.
The input-output classes and functions can be found in the unified_planning.io package, while the interoperability with ``tarski`` (and in the future with other libraries) are in the ups.interop package.

Example
-------
The following example shows how to read a PDDL problem from files and how to dump to files in PDDL format a Unified-Planning problem.

.. literalinclude:: ./code_snippets/robot_battery.py
    :lines: 90-104
