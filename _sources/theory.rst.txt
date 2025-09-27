.. include:: ./includes/external_links.rst

.. include:: ./includes/warning_development.rst

.. _theory:

Theoretical Reference
#######################################################################

.. _theory introduction:

Introduction
=======================================================================

.. include:: ./includes/ipsum.rst

.. _theory fundamentals:

Fundamentals
=======================================================================

System Dynamics
----------------------------------------------------------------------

`System Dynamics`_ is a modeling paradigm used to represent complex systems through a set of interconnected components. Under this paradigm, a model is built as a network of **storages**, or stocks, and flows that move between them.

Other model paradigms include **data-driven models**, where empirical and statistical approaches are used, and **distributed models** (aka physically-based), where flows are described by the calculation of the water velocity field.

System dynamics in hydrology
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

System Dynamics models has a long history in Hydrology. The earliest hydrological models (the Stanford Model) were based on this paradigm because it is intuitive, simple to understand and easy to develop: the catchment is represented as water buckets connected by flows.

The **parameters** of the model define the size of the storages, regulate the flows, determine the feedback mechanisms that govern system behavior, and specify the initial and boundary conditions needed to start the simulation.

Lumped and semi-distributed approaches
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

System Dynamics models can be fully **lumped**, where the entire catchment or hillslope is represented by a single system of storages, or **semi-distributed**, where the catchment is divided into several cells or units.

In the case of semi-distributed, each cell or unit is modeled independently, but this approach still does not simulate velocity fields explicitly. This is a key difference from distributed models, which use gridded representations of flow fields to calculate velocities at each point in space.

.. _water-balance:

Water balance
----------------------------------------------------------------------

In system dynamics models of hydrology, the key process of simulation is the water balance. Each storage is evaluated in terms of its net balance: all inflows are added to the current water level and all outflows are subtracted. This evaluation is performed at every time step of the simulation, so that the state of each storage is updated step by step.

This process can be expressed as a numerical equation where the storage level at the next time step is equal to the previous storage level plus the sum of all inflows minus the sum of all outflows.

.. math::
   :label: eq:water-balance

   S_{t+1} = S_t + \sum \text{inflows} - \sum \text{outflows}

Here, :math:`S` is the storage level, :math:`t` is the current time step, :math:`t+1` is the next time step, and the summations represent the total inflows and outflows during the interval.

In hydrology, a typical soil water (:math:`S`) balance at the catchment scale would include precipitation (:math:`P`) as the main inflow, and evapotranspiration (:math:`E`) and streamflow (:math:`Q`) as the main outflows:

.. math::
   :label: eq:catchment-balance

   S_{t+1} = S_t + P - (E + Q)

This example represents the long-term water balance for an entire catchment, while each individual storage or sub-component has its own water balance computed within a model.

Linear storage
----------------------------------------------------------------------

Linear storage is a fundamental concept in system dynamics and in hydrology. Early works, such as Horton (1933), proposed that groundwater behaves like a linear reservoir: it drains in proportion to the current storage level.

A simple way to visualize this is to imagine a water bucket with a small hole at the bottom. The bucket drains continuously, and the discharge rate is proportional to the water level inside. As the storage empties, the discharge gradually decreases, eventually approaching zero as time tends to infinity.

This behavior can be described by a simple differential equation, where the outflow is proportional to the storage. The parameter :math:`k` is known as the *residence time* and controls how quickly or slowly the storage drains.

.. math::
   :label: eq-linear-storage

   Q(t) = \frac{1}{k} \cdot S(t)

In this equation, :math:`Q(t)` is the outflow at time :math:`t`, :math:`S(t)` is the current storage, and :math:`k` is the residence time. A small value of :math:`k` results in faster drainage, while a larger :math:`k` leads to slower drainage. Although this equation can be solved analytically for a single storage, in practice it is often embedded within a numerical scheme, like the Euler Method, that accounts for multiple inflows, outflows, and other interacting storages.

Recession curves
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When solved analytically for an isolated storage with no additional inflows, the solution yields an exponential decay, or **recession curve**:

.. math::
   :label: eq-recession-curve

   Q(t) = Q_0 \cdot e^{-t/k}

Here, :math:`Q_0` is the initial discharge at the beginning of the recession. This equation describes how discharge decreases exponentially over time, converging asymptotically toward zero.

Horton (1933) noted that this behavior closely matches the observed recession curves of rivers during periods of no rainfall and negligible evapotranspiration. These curves provide valuable information about the catchment’s storage properties, allowing estimates of parameters such as :math:`Q_0` and the effective storage capacity of the catchment.

In practice, these are effective values representing the average conditions of the soils and aquifers that contribute to baseflow at the gauging section.


Macropores and fast subsurface flows
----------------------------------------------------------------------

Although linear storage provides a good first approximation for groundwater drainage, early studies showed that it does not represent all forms of flow
from soils to streams. In many forested catchments, a significant portion of stream response can be attributed to fast subsurface flow through macropores
and highly conductive soil layers.

These macropores, often formed by root channels, decayed organic material, or soil cracks, create preferential flow paths that transmit water rapidly downslope.
As a result, streams may rise quickly after rainfall events even when there is no direct overland flow and no significant recharge to deep groundwater.
This process is particularly important in forest hydrology and in hillslopes
with well-developed organic layers, where macropore flow can dominate the
hydrological response.


Overland flow generation
----------------------------------------------------------------------

Overland flow, or runoff generation, occurs when rainfall produces water that
cannot be immediately stored in the soil and instead moves across the surface
towards the channel network. There are two main mechanisms for overland flow: infiltration-
excess and saturation-excess.

**Infiltration-excess** overland flow happens when rainfall intensity exceeds the
soil's capacity to absorb water, causing direct runoff.

**Saturation-excess** overland flow occurs when water reaches areas that are already saturated, so
any additional rainfall quickly contributes to surface flow.

The **variable source area** concept explains the spatial and temporal dynamics of
saturation-excess flow. Saturated areas in the catchment, sometimes referred
to as temporary wetlands, expand and contract depending on the soil water
content. During wet periods, saturated areas extend from valleys toward
uphill regions, while during dry periods they shrink. This dynamic behavior
creates a non-linear relationship between precipitation and runoff, where the
same rainfall can generate very different amounts of overland flow depending
on the antecedent wetness of the catchment.


Connectivity
----------------------------------------------------------------------

.. include:: ./includes/ipsum.rst

.. math::
   :label: eq-connectivity

   Q_a =
   \begin{cases}
   0 & \text{if } \quad S \leq s_a \\
   \Lambda \cdot (S - s_a) & \text{if } \quad S > s_a
   \end{cases}


Scale issues
----------------------------------------------------------------------

.. include:: ./includes/ipsum.rst

Upscaling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: ./includes/ipsum.rst


Downscaling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: ./includes/ipsum.rst


Soil moisture
----------------------------------------------------------------------

.. include:: ./includes/ipsum.rst


Parameters of soil and land use
----------------------------------------------------------------------

.. include:: ./includes/ipsum.rst


.. _theory model structure:

Model Structure
=======================================================================

The model is based on a `System Dynamics`_ structure, representing the hillslope system as a column of interconnected storages — like a series of “water buckets” — that fill, spill, drain and dry over time.

In the standard configuration, the model column begins with a canopy storage, followed by a surface storage (which can include an organic soil layer where present). Beneath it lies the mineral soil storage, divided into an unsaturated zone (where water moves vertically through pores) and a saturated phreatic zone (fully saturated, driving drainage and lateral exchanges with neighboring cells).

Each column represents a cell on a 2D grid, which can be simulated in distributed or semi-lumped configurations, allowing flexibility in spatial resolution and computational power.

.. include:: ./figs/model_structure.rst

.. admonition:: System components index
   :class: seealso

   Check out the full reference for variables and parameters at the :ref:`system-index` page.

Storage phases
----------------------------------------------------------------------

Each storage exchanges water through three main mechanisms: **draining** (water leaks downward), **spilling** (water overflows to the next component), and **drying** (water is lost through evaporation). Together, these processes form a network of storages connected by flows, with parameters regulating their behavior (e.g., residence time).

.. include:: ./figs/model_phases.rst



.. _theory model equations:

Model Equations
=======================================================================

.. include:: ./includes/ipsum.rst

.. admonition:: System components reference
   :class: seealso

   Check out the full reference for variables and parameters at the :ref:`system-index` page.


.. include:: ./includes/ipsum.rst

.. math::
   :label: eq-pythagoras

   a^2 + b^2 = c^2


References
=======================================================================

.. include:: ./includes/ipsum.rst


.. toctree::
   :maxdepth: 1
   :hidden:

   system
