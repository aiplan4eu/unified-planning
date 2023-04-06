I/O & Interoperability
=================================

In order to make the library immediately usable for people having existing code on projects such as `tarski <https://github.com/aig-upf/tarski>`_ and/or other tools based on formal languages such as ``PDDL`` or ``ANML``, we developed a series of interoperability features to make use of existing models written in (different flavors of) PDDL or ANML and to convert from and to `tarski`.

PDDL/MAPDDL/HDDL reader and writer
--------
The library offers a comprehensive and well-tested parser for PDDL 2.1 level 3 (i.e. up to temporal planning without continuous change). The parser can be invoked as shown in the example below and can be used either to parse a whole planning instance (i.e. a domain and a problem), or just to porsche the domain file, resulting in an incomplete ``Problem`` object that can be completed using the UP API as shown below. This latter use-case allows to model the action schemata using PDDL and then formulate the problem(s) using the UP (possibly using data available at runtime for doing so).

.. literalinclude:: ./code_snippets/interop.py
    :caption: PDDLReader example
    :lines: 10-14

        reader = PDDLReader()
        # Reader used with both domain and problem file
        problem = reader.parse_problem(domain_filename, problem_filename)

.. literalinclude:: ./code_snippets/interop.py
    :caption: PDDLReader with domain file and problem populated using UP
    :lines: 16-30

        # Reader used with only domain file to create different instance
        # of the same domain but different problem
        problems = []
        problem = reader.parse_problem(domain_filename)
        Location = problem.user_type("Location")
        for i in range(2, 7):
            new_problem = problem.clone()
            new_problem.add_objects([Object(f"loc_{j}", Location) for j in range(i)])
            problems.append(new_problem)
        objects_numbers = [len(p.all_objects) for p in problems]
        print(objects_numbers)
        # [2, 3, 4, 5, 6]

Vice-versa, it is possible to generate the PDDL representation of a planning problem represented in the UP. This printing facility is limited to the modeling features available in PDDL 2.1 level 3 (e.g., no intermediate or external conditions or effects are supported).

.. code-block::
    :caption: PDDLWriter example

        # Get the problem to use in the Operation Modes
        problem = reader.parse_problem(problem_filename)
        problem = ...
        writer = PDDLWriter(problem)
        domain_filename = ... # Path to file where the PDDL domain will be printed.
        writer.write_domain(domain_filename)
        problem_filename = ... # Path to file where the PDDL problem will be printed.
        writer.write_problem(problem_filename)

For hierarchical planning problems, we also have a reader and writer for the `HDDL language <https://arxiv.org/abs/1911.05499>`_ working analogously to the basic PDDL ones and demonstrated below.

.. code-block::
    :caption: HDDL Read & Write example

        reader = PDDLReader()
        hddl_domain_filename = ...
        hddl_problem_filename = ...


        # Reader used to parse HDDL files and return a up.model.htn.HierarchicalProblem
        hierarchical_problem = reader.parse_problem(
            hddl_domain_filename,
            hddl_problem_filename
        )
        hierarchical_problem = ... # Modify the problem
        writer = PDDLWriter(hierarchical_problem)
        domain_filename = ... # Path to file where the HDDL domain will be printed.
        writer.write_domain(domain_filename)
        problem_filename = ... # Path to file where the HDDL problem will be printed.
        writer.write_problem(problem_filename)

Analogously, for multi-agent planning problems the UP provides a writer to the MAPDDL formalism

.. code-block::
    :caption: MAPDDL Example

        multiagent_problem = ...
        writer = MAPDDLWriter(multiagent_problem)
        domain_directory = ... # Path to directory where MA-PDDL domains will be printed.
        writer.write_ma_domain(domain_directory)
        problem_directory = ... # Path to file where the MA-PDDL problems will be printed.
        writer.write_ma_problem(problem_directory)

ANML Reader & Writer
--------

Also for the expressive ANML planning language, the UP provides a reader and a writer. At the time of writing the ANML support is limited to temporal planning, but we plan to add support for hierarchical features as well.

.. code-block::
    :caption: ANMLReader example

        reader = ANMLReader()
        problem_filename = ... # Path to the ANML problem file

.. code-block::
    :caption: ANMLWriter example

        problem = ...
        writer = ANMLWriter(problem)
        file_name = ... # Path to file where the ANML problem will be printed.
        writer.write_problem(file_name)

Tarski Interoperability
--------

Tarski is a python library providing planning support for a fragment of numeric planning. Differently from the UP, tarski does not involve multiple planning engines, but allows the creation, printing, parsing and solving of a planning specification called FSTRIPS. In order to make the UP and the tarski problem representation interoperable (up to the planning fragment supported by tarski), we created two conversion procedures, namely ``convert_problem_to_tarski(p : Problem)``, which takes a UP problem representation and produces an FSTRIPS problem representation as a tarski object, and ``convert_problem_from_tarski(env: Environment, tp: tarski.fstrips.Problem)`` which performs the inverse conversion. These functions allow the use of the tarski toolset starting from UP problems and vice-versa.

.. code-block::
    :caption: tarski interoperability example

        problem = ...
        tarski_problem: tarski.fstrips.Problem = convert_problem_to_tarski(problem)
        # You get a Tarski problem, which you can use to interact with the Tarski library

        # From a Tarski problem, you can generate the equivalent UP problem.
        problem = convert_problem_from_tarski(get_environment(), tarski_problem)
