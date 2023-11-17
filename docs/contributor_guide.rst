Contributor's Guide
===================



Documentation
-------------

The documentation is maintained in the `docs/` folder of the `main repository <https://github.com/aiplan4eu/unified-planning/tree/master/docs>`_ 
It consists of a collection of reStructuredText documents and python notebooks that rendered to HTML and published on `readthedocs <https://unified-planning.readthedocs.io/en/latest/>`_ on each release.


Building the documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^


The documentation can be built locally like so::

    cd docs/  # enter the documentation folder
    pip install -r requirements.txt  # install documentation toolchain
    make html

After this, the documentation will be available as a set of HTML pages in the `_build/html` folder and can be visualized with a regular web browser.


Updating the Reference API
^^^^^^^^^^^^^^^^^^^^^^^^^^

The reference API part of the documentation is built automatically by the `docs/generate_api_doc.py <https://github.com/aiplan4eu/unified-planning/blob/master/docs/generate_api_doc.py>`_ script. 
The script contains the list of classes that will appear in the documentation.
If you contribute a new *user-facing* class, the list of classes should be updated to make it appear in the API reference.





Issue Tracking
--------------

Issue tracking is done in GitHub issues: https://github.com/aiplan4eu/unified-planning/issues
