.. _engines:

================
Planning Engines
================

.. contents::
   :local:

The `unified_planning` library provides the functionality needed to model and to transform planning problems and organizes the possible queries to the planning engines in a series of Operation Modes. An operation mode defines how the user can interact with a certain planning engine in an abstract way: each planning engine must define which is the subset of operation modes that it is able to support. In this way, the library is capable of automatically selecting a planning engine for a certain operational mode taking into account the specific characteristics of the problem formulated by the user.
The planning engines themselves are not included in the UP Library, but it is possible to add planning engines externally by means of a plugin system offered by the `unified_planning`.engines package. Moreover, the installation system of the UP library allows the automated installation of several commonly used engines.
The UP library defines the set of Operation Modes as a set of interfaces to be instantiated by each engine.

