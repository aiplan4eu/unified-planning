Contributor's Guide
===================

This page is dedicated to the technical information that you may find useful when contributing code or documentation to the UP repository.
For information on the contribution process, please have a look to the `corresponding page <https://github.com/aiplan4eu/unified-planning/blob/master/CONTRIBUTING.md>`_.

Common commands (Justfile)
--------------------------

A list of common commands and recipes are available in a `justfile <https://github.com/aiplan4eu/unified-planning/blob/master/justfile>`_.
You can use it to find out common commands (e.g. running tests, reformatting the code) or use it directly with the `just <https://github.com/casey/just>`_ command line tool.

Whenever you see a command ``just RECIPE_NAME`` in this page, it means the command is available as a just recipe.
You can run it directly with ``just`` or check the ``justfile`` for the actual commands to run.

Checklist
---------

Before sending a pull-request, you should check the following conditions:

 - your code is properly formatted with ``black`` (``just format``)
 - your code passes the linter check (``just check-mypy``)
 - your code passes all existing unit tests
 - you have added tests to ensure that your change is and remains valid
 - you have updated the documentation to reflect your changes

Whenever possible these are automatically check in CI.

Documentation
-------------

The documentation is maintained in the `docs/` folder of the `main repository <https://github.com/aiplan4eu/unified-planning/tree/master/docs>`_ 
It consists of a collection of reStructuredText documents and python notebooks that rendered to HTML and published on `readthedocs <https://unified-planning.readthedocs.io/en/latest/>`_ on each release.


Building the documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^

The documentation can be built locally like so (``just build-doc``)::

    cd docs/  # enter the documentation folder
    pip install -r requirements.txt  # install documentation toolchain
    make html

After this, the documentation will be available as a set of HTML pages in the `_build/html` folder and can be visualized with a regular web browser.


Updating the Reference API
^^^^^^^^^^^^^^^^^^^^^^^^^^

The reference API part of the documentation is built automatically by the `docs/generate_api_doc.py <https://github.com/aiplan4eu/unified-planning/blob/master/docs/generate_api_doc.py>`_ script. 
The script contains the list of classes that will appear in the documentation.
If you contribute a new *user-facing* class, the list of classes should be updated to make it appear in the API reference.

Ensuring documentation consistency
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As much as possible, we strive to make example code testable to ensure that it remains valid when updating the library.
This notably include all code in ``docs/code_snippets`` as well as all notebooks in ``docs/notebooks``.

If your notebook has some code that should *not* be run in CI, the corresponding cell should be tagged with the ``remove_from_CI`` flag.

Protobuf bindings
-----------------

The UP provides protobuf bindings that can be used export the problems modeled with the UP in a protobuf format.
The schema for this format are available in the `unified_planning/grpc/unified_planning.proto <https://github.com/aiplan4eu/unified-planning/blob/master/unified_planning/grpc/unified_planning.proto>`_ file.

When updating them you should ensure that:

 - the schema remains backward compatible (no removal, no change in the fields indices)
 - you have regenerated the python bindings available in the repository (``just gen-protobuf``)
