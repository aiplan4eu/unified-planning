Planning Engines
================

The ``Engine`` class is the class interface that has to be implemented in order to define an engine that exposes one or more operative modes. It has some methods that implements that operation modes and other methods that can be called to know if the engine is suitable for a given problem kind.

Engine selection and preference list
--------

The UP library instantiates planning engines via the ``unified_planning.engines.Factory`` class. A single instance of ``Factory`` is needed for each environment and can be retrieved by the factory property of an ``Environment`` object. This class maintains a set of known engines each with a unique name, and offers methods to add new engines by specifying the name and the python class, to instantiate and retrieve planning engines by name and to read configuration files in custom locations.

If operation modes are invoked without specifying the name of an engine to use, the UP library will filter the list of engines known to the ``Factory`` by checking which engine supports the given ``problem kind`` with the given operation mode. If more than one engine passes the check, the ``Factory`` uses a `customizable` preference list to select the engine to retrieve. The default preference list is a simple heuristic we developed, but a user can override it by setting the ``preference_list`` property of the ``Factory``.

A user can set a custom preference list and add external engines to the library by creating a configuration file called either ``up.ini`` or ``.up.ini`` and located in any of the parent directories from which the program code was called. Alternatively also ``~/up.ini``, ``~/.up.ini``, ``~/.uprc`` are valid files that the library checks by default. The syntax of the configuration files is straightforward and depicted below.

.. code-block::
    :caption: Preference List structure

        [global]
        engine_preference_list: <engine-name> <engine-name> <engine-name>


        [engine <engine-name>]
        module_name: <module-name>
        class_name: <class-name>

Plug-in system
--------

As mentioned at the beginning, one of key characteristics of the UP library is the engine plug-in system. The idea is that the set of planning engines is not fixed a-priori and can be easily extended. In this section we detail this mechanism together with the concept of “meta-engine”, which is an engine using another engine as a service to achieve a certain operation mode. An overview of the engines integrated throughout the project by the consortium partners is available in this section.

Meta-Engines
--------
In addition to plain planning engines, the UP library embeds the concept of “meta-engine”. A meta-engine is a planning engine that needs access to another engine (or meta-engine) services to provide its own services. For example, the ``NaiveReplanner`` meta-engine (partially reported in the snippet below) implements the ``Replanner`` OperationMode by repeatedly calling any ``OneshotPlanner`` engine internally.

.. code-block::
    :caption: NaiveReplanner partial implementation and usage

        class NaiveReplanner(MetaEngine, mixins.ReplannerMixin):
            ...

            def _resolve(self, timeout, output_stream):
                return self.engine.solve(self._problem, timeout, output_stream)

            def _update_initial_value(self, fluent, value):
                self._problem.set_initial_value(fluent, value)

            def _add_goal(self, goal):
                self._problem.add_goal(goal)

            def _add_action(self, action):
                self._problem.add_action(action)

            ...


        factory.add_meta_engine("naive-replanner", __name__, "NaiveReplanner")


        problem = …
        with Replanner(name="naive-replanner[tamer]", problem=problem) as replanner:
            result = replanner.resolve()
            ...

The general idea of a meta-engine is to implement algorithms relying on planning engines to implement certain operation modes. The library uses a special naming convention for meta engines; if the meta engine is called ``meta``, its instantiation with the engine ``e`` is called ``meta[e]``. One can add meta-engine to the library via the ``Factory`` class, similarly to engines, the ``add_meta_engine(name: str, module_name: str, class_name: str)`` method allows the user to add new meta engines, which are automatically instantiated with all the compatible engines. Compatibility between an engine and a meta-engine is determined by the UP thanks to the MetaEngine class that is the base of every meta-engine: each meta-engine must implement the  ``is_compatible_engine(engine: Type[Engine])`` method, which checks if a given engine is compatible with the meta-engine at hand. This schema allows the creation of very general algorithms whose capability varies depending on the engine they are instantiated with.

.. toctree::
    :hidden:
    :glob:
    :titlesonly:

    engines/*
