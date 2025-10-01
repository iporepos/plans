.. include:: ./includes/external_links.rst

.. include:: ./includes/warning_development.rst

.. _system-index:

System Index
#######################################################################

This page provides a complete index reference for the components of the
``plans`` model system, including variables, parameters, initial conditions,
and boundary conditions. Each component is presented in tabular form with
its symbol, name, description, units, and other relevant details. Together,
these tables serve as a comprehensive guide to understanding the building
blocks of the model and how they interact.

.. _system overview:

System overview
************************************************************************

The ``plans`` model is based on a `System Dynamics`_ approach, representing the
hillslope system as a column of interconnected storages — like a series
of “water buckets” — that fill, spill, drain and dry over time.

.. include:: ./figs/model_structure.rst

.. seealso::

   See more details in :ref:`theory model structure`.


.. _system variables:

Variables
************************************************************************

Variables represent the dynamic components of the hydrological system.
They hold numerical values for storage levels, as well as the instantaneous
flows at each time step of the model simulation. Together, they describe
how the system evolves over time.

.. csv-table::
   :file: ./data/system_variables.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


.. _system parameters:

Parameters
************************************************************************

Parameters control the behavior of the system. They can influence storage
levels and flows, but unlike variables, they remain constant throughout the
simulation. Parameters define the conditions under which the model operates
and can be adjusted to reproduce observed behavior or to fine-tune
the system for a desired outcome.

.. csv-table::
   :file: ./data/system_parameters.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


.. _system initial conditions:

Initial Conditions
************************************************************************

Initial Conditions define the starting values of storage variables at
the first time step of the simulation. They serve as the starting point
from which the system evolves, allowing the model to compute changes
and update states over the entire simulation period.

.. csv-table::
   :file: ./data/system_init.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


.. _system boundary conditions:

Boundary Conditions
************************************************************************

Boundary Conditions define the structural and contextual setup of the system.
They determine how the model interacts with its surroundings, such as the
configuration of a drainage network for routing procedures. Different boundary
arrangements lead to different simulation outcomes, making them a critical
input for running the model.

.. csv-table::
   :file: ./data/system_bounds.csv
   :header-rows: 1
   :widths: auto
   :delim: ;