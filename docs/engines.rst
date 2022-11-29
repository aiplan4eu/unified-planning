Planning Engines
================


The ``Engine`` class is the class interface that has to be implemented in order to define an engine that exposes one or more operative modes. It has some methods that implements that operation modes and other methods that can be called to know if the engine is suitable for a given problem kind.

The ``MetaEngine`` class is a child class of ``Engine`` that is defined over a generic engine implementation. The implementation of a meta engine can be used with all the compatible engines available on the system.


.. toctree::
    :hidden:
    :glob:
    :titlesonly:

    engines/aries