Testing an Engine Integration
=============================

The ``report.py`` script in ``unified-planning/up_test_cases`` is used to test an ``Engine`` on a collection of ``Problems``.


Report.py usage
---------------

To get a parameters description of the ``report.py`` script run ``python3 up_test_cases/report.py -h``; this gives an idea of the parameters and their usage.

To test an engine that is not a default engine, follow this procedure: `Engine selection and preference list <https://unified-planning.readthedocs.io/en/latest/engines.html#engine-selection-and-preference-list>`__

Some examples:


* ``python3 up_test_cases/report.py aries fast-downward -m oneshot``: runs the ``OneshotPlanner`` mode of ``aries`` and ``fast-downward`` on all the problems.
* ``python3 up_test_cases/report.py tamer -m validation -f numeric temporal``: runs the ``Validator`` mode of ``tamer`` on all the problems that contain the word ""numeric" or "temporal".
* ``python3 up_test_cases/report.py lpg -e performance -t 30``: runs ``lpg`` on all the default problems and the problems in the package "performance", with a timeout of 30 seconds.
* ``python3 up_test_cases/report.py enhsp -p builtin.numeric performance``: runs ``enhsp`` on problems defined in the packages ""numeric" and "performance".


Add custom problems
-------------------

To add custom problems you need to create a python package that exposes a method called ``get_test_cases``. This method returns a ``Dict[str, TestCase]`` (where ``TestCase`` is defined in the ``unified_planning.test.__init__.py`` file).

After you have a package like this that is available in the python path (``import example_package`` must not fail), you can specify ``example_package`` in the options ``-p (--packages)`` or ``-e (--extra-packages)`` of the ``report.py`` script.

This should allow the user to specify it's own set of problems to submit to the engine testing.
