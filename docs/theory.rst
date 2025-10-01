.. include:: ./includes/external_links.rst

.. include:: ./includes/warning_development.rst

.. _theory:

Theoretical Reference
#######################################################################

.. _theory introduction:

Introduction
=======================================================================

This page provides a basic theoretical background and some technical details
for understanding how the ``plans`` model work.

.. admonition:: System components index
   :class: seealso

   Check out the full reference for variables and parameters at the
   :ref:`system-index` page.

.. _theory systems:

System Models
=======================================================================

The ``plans`` model is based on a `System Dynamics`_ approach, representing the
hillslope system as a column of interconnected storages — like a series
of “water buckets” — that fill, spill, drain and dry over time.

The `System Dynamics`_ approach is a modeling paradigm used to represent complex systems
through a set of interconnected components. Under this paradigm, a model is
built as a network of **storages** and **flows** that move between them.

Other model paradigms include **data-driven models**, where empirical and
statistical approaches are used, and **distributed models** (also known as
physically-based models), where flows are described by the calculation of
the water velocity vector field.

.. _theory system hydrology:

System Dynamics in Hydrology
----------------------------------------------------------------------

System Dynamics models has a long history in Hydrology. The earliest
hydrological models (the Stanford Model) were based on this paradigm because
it is intuitive, simple to understand and easy to develop. In short, the
catchment is represented as web of storages (like water buckets) connected by flows.

The **parameters** of the model define the size of the storages, regulate the
flows, determine the feedback mechanisms that govern system behavior.

Initial and boundary conditions also must be defined to start the simulation.
**Initial conditions** usually are the storage levels at the first time step.
**Boundary conditions** are a set of information that shapes the system, like
the structure of terrain topography and channel network.

.. _theory system models:

Lumped and semi-distributed models
----------------------------------------------------------------------

System Dynamics models in Hydrology can be fully **lumped**, where the
entire catchment or hillslope is represented by a single system of storages,
or **semi-distributed**, where the catchment is divided into an array of
cells. This cells can be spatially arranged in a regular or irregular grid or mesh.

In the case of semi-distributed models, each cell or unit is simulated
just like a tiny lumped model, also known as Hydrological Response Units ``HRU``.
This is a key difference from truly distributed models, which use gridded
spatial representations of the velocity vector field to calculate flows.

The ``plans`` model falls into the category of semi-distributed models.

.. _theory simulation approaches:

Simulation approaches
----------------------------------------------------------------------

In semi-distributed models, Hydrological response units ``HRU`` can be
simulated in two main ways: **grid-to-grid simulation** and **histogram simulation**.
Each approach has distinct advantages and limitations, depending on the
scale of the study area and the computational resources available.

.. _theory g2g:

Grid-To-Grid simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In grid-to-grid simulation ``G2G``, each map cell (or pixel) is treated as an
unique ``HRU``. This approach is most suitable when parameters are expressed
as continuous spatial variables (e.g., canopy cover, soil storage capacity, etc).

*Advantages*:
- Directly represents spatial heterogeneity at pixel resolution.
- Results are already mapped at the same scale as the input data, requiring no additional downscaling.

*Disadvantages*:
- Memory- and computation-intensive, especially for large basins.
- Simulation may become impractical if the study area contains millions of cells.

.. _theory hst:

Histogram Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In histogram simulation ``HST``, the ``HRU`` units are larger patches that
share common parameter values. For example, canopy parameters may be
averaged for all cells within a given land-use class.

The area fraction of each ``HRU`` type is then represented in a histogram,
which is used to upscale simulated values.

*Advantages*:
 - Highly efficient in terms of memory and computational cost.
 - Suitable for large study areas where grid-to-grid simulation is infeasible.
 - Suitable for calibration or monte carlo analysis where many simulations are needed.

*Disadvantages*:
 - Simulation occurs at an intermediate scale, requiring an additional step to downscale or reproject results back onto maps.
 - Some spatial detail is lost due to parameter aggregation.
 - Mapping outputs back to raster resolution requires extra processing.

.. _theory water balance:

Water balance
----------------------------------------------------------------------

In System Dynamics models of Hydrology, the key process of simulation is
the water balance. Each storage is evaluated in terms of its net balance:
all inflows are added to the current water level and all outflows are
subtracted. This evaluation is performed at every time step of the simulation,
so that the state of each storage is updated step by step.

This process can be expressed as a numerical equation where the storage
level at the next time step is equal to the previous storage level plus
the sum of all inflows minus the sum of all outflows.

.. math::
   :label: eq:water-balance

   S_{t+1} = S_t + \sum \text{inflows} - \sum \text{outflows}

Here, :math:`S` is the storage level, :math:`t` is the current time step,
:math:`t+1` is the next time step, and the summations represent the
total inflows and outflows during the interval.

In Hydrology, a typical soil water (:math:`S`) balance at the catchment
scale would include precipitation (:math:`P`) as the main inflow,
and evapotranspiration (:math:`E`) and streamflow (:math:`Q`)
as the main outflows:

.. math::
   :label: eq:catchment-balance

   S_{t+1} = S_t + P - (E + Q)

This example represents the long-term water balance for an entire catchment,
while each individual storage or sub-component has its own water balance
computed within a model.

.. _theory hydrology:

Hydrology
=======================================================================

.. _theory linear storage:

Linear Storage
----------------------------------------------------------------------

The Linear Storage is a fundamental concept in System Dynamics and in Hydrology.
Early works, such as Horton (1933), proposed that soil and aquifers behaves like
a linear reservoir: it drains in proportion to the current storage level.

A simple way to visualize this is to imagine a water bucket with a small and porous
hole at the bottom. The bucket drains continuously, and the discharge rate
is proportional to the water level inside. As the storage empties, the
discharge gradually decreases, eventually approaching zero as time tends
to infinity.

This behavior can be described by a simple differential equation, where
the outflow is proportional to the storage. The parameter :math:`k` is
known as the *residence time* and controls how quickly or slowly the
storage drains.

.. math::
   :label: eq-linear-storage

   Q(t) = \frac{1}{k} \cdot S(t)

In this equation, :math:`Q(t)` is the outflow at time :math:`t`,
:math:`S(t)` is the current storage, and :math:`k` is the residence time.
A small value of :math:`k` results in faster drainage, while a larger
:math:`k` leads to slower drainage. Although this equation can be solved
analytically for a single storage, in practice it is often embedded within
a numerical scheme, like the Euler Method, that accounts for multiple
inflows, outflows, and other interacting storages.

.. _theory recession curves:

Recession curves
----------------------------------------------------------------------

When solved analytically for an isolated storage with no additional inflows,
the solution yields an exponential decay, or **recession curve**:

.. math::
   :label: eq-recession-curve

   Q(t) = Q_0 \cdot e^{-t/k}

Here, :math:`Q_0` is the initial discharge at the beginning of the recession.
This equation describes how discharge decreases exponentially over time,
converging asymptotically toward zero.

Horton (1933) noted that this behavior closely matches the observed recession
curves of rivers during periods of no rainfall and negligible evapotranspiration.
These curves provide valuable information about the catchment’s storage
properties, allowing estimates of parameters such as :math:`Q_0` and the
effective storage capacity of the catchment.

In practice, these are effective values representing the average conditions
of the soils and aquifers that contribute to baseflow at the gauging section.

.. _theory subsurface flows:

Subsurface flows
----------------------------------------------------------------------

Although linear storage provides a good first approximation for groundwater
drainage, early studies showed that it does not represent all forms of flow
from soils to streams. In many forested catchments, a significant portion
of stream response can be attributed to fast **subsurface flow** through macropores
and highly conductive soil layers.

These macropores, often formed by root channels, decayed organic material,
or soil cracks, create preferential flow paths that transmit water rapidly downslope.
As a result, headwater streams may rise quickly after rainfall events even when there
is no direct overland flow and no significant recharge to deep groundwater.

This process is particularly important in forest hydrology and in hillslopes
with well-developed organic layers, where macropore flow can dominate the
hydrological response.

.. _theory overland flow:

Overland flow
----------------------------------------------------------------------

**Overland flow**, also known as **runoff**, occurs when rain flow fills
the **surface storage**, causing a **spill flow** pulse by the activation
small channels that convey water downhill to the main stream network.

There are two main **mechanisms** for overland flow generation:

.. _theory infiltration-excess:

Infiltration-excess
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This happens when rain flow is so intense that infiltration flow is exceeded.
Common during heavy storms and where the soil surface presents a high residence
time (like compacted soils).

.. _theory saturation-excess:

Saturation-excess
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This occurs when rain reaches areas where soil is fully saturated and there
is zero potential for infiltration. Common in all events where rain reaches
a saturated soil surface.

.. _theory variable source area:

Variable source area
----------------------------------------------------------------------

The **variable source area** concept explains the spatial and temporal dynamics of
saturation-excess overland flow.

Saturated areas in the catchment, also known as **riparian wetlands**,
expand and contract depending on the soil water level. During wet periods,
saturated areas extend from valleys toward uphill regions, while during dry
periods they shrink.

This dynamic behavior creates a non-linear relationship between precipitation
and overland flow, where the same rainfall can generate very different amounts of
runoff depending on the antecedent wetness of the catchment.

.. _theory connectivity:

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

.. _theory scaling:

Scaling
=======================================================================

Scale issues are a common challenge in environmental modelling, spatial
analysis, and temporal analysis. The core difficulty lies in
*transferring information from one scale to another*, known as **scaling**.
This can occur in two main directions:

- **Upscaling**: aggregating information from a finer scale to a coarser
  scale (e.g., daily precipitation aggregated into monthly totals, or
  county-level population data aggregated to the state level).
- **Downscaling**: distributing information from a coarser scale to a
  finer scale (e.g., disaggregating monthly precipitation into daily
  values, or allocating national population totals to local districts).

In many cases, intermediate scales are also introduced, and each scale
is composed of discrete *units* that hold information.

.. _theory scaling nomenclature:

Formal Notation
----------------------------------------------------------------------

**Scale units in time or space**

Let the spatial or temporal region :math:`R` be partitioned into
:math:`N` units (e.g., patches in space or time intervals) with similar
attributes.

**Variable** :math:`V`

Let :math:`V_u` denote a scalar attribute associated with the unit of
index :math:`u`.

**Upper level**

At a coarser scale, upper-level unit is the region :math:`R`
with extent :math:`A` and attribute value :math:`V`.

**Lower level** :math:`i`

At a finer scale, the upper-level unit is subdivided into
:math:`N` lower-level units. Each lower-level unit, indexed by
:math:`i \in \{1, 2, \ldots, N\}`, has extent
:math:`A_{i}` and attribute value :math:`V_{i}`.

This formalism provides a consistent framework for discussing scale
transformations, whether upscaling or downscaling, across both spatial
and temporal domains.

.. _theory upscaling:

Upscaling
----------------------------------------------------------------------

Upscaling refers to transferring information from a finer scale
(lower-level units :math:`V_{i}`) to a coarser scale
(upper-level unit :math:`V`). Conceptually, information is *blended*
from the lower level to form a representative value at the higher level.

Two common cases of upscaling are:

- **Aggregation (sum)** — typically used for *storage* variables or
  cumulative quantities.
- **Averaging (weighted mean)** — typically used for *state* or
  *flow* variables, where values are normalized by extent (area or
  duration).

The choice between aggregation and averaging depends on the type of
process or variable under consideration.

.. _theory aggregation:

Aggregation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In aggregation, the upscaled value is the sum of the lower-level values:

.. math::
  :label: eq-upscaling-agg

   V = \sum_{i=1}^{N} V_{i}

.. _theory averaging:

Averaging
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In averaging, the upscaled value is the weighted mean of the lower-level
values, with weights given by their extent:

.. math::
  :label: eq-upscaling-avg

   V = \frac{ \sum_{i=1}^N V_{i} A_{i}}
               {\sum_{i=1}^N A_{i}}

where

- :math:`V_{i}` is the attribute value of sub-unit :math:`i` under the
  upper-level unit,
- :math:`A_{i}` is the extent (e.g., area, duration) of sub-unit
  :math:`i`,
- :math:`N` is the number of sub-units contained within the
  upper-level unit

.. _theory downscaling:

Downscaling
----------------------------------------------------------------------

Downscaling is the process of disaggregating and distributing a variable
from upper-level units (:math:`V`) to lower-level units
(:math:`V_{i}`). Unlike upscaling, which aggregates information,
downscaling is more subtle because it *creates detail* based
on assumed premisses.

Downscaling relies on a **distribution function** :math:`f`. This also
needs one or more **covariate** :math:`W_{i}` that is known at the target
lower level.

Formally, for one covariate:

.. math::
  :label: eq-downscaling-func

   V_{i} = f(V, W_{i})

Several approaches can be applied, depending on the nature of the
variable and the covariates.

.. _theory downscaling linear:

Linear Downscaling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Linear downscaling assumes a direct proportionality between the variable
of interest :math:`V` and the covariate :math:`W`:

.. math::
  :label: eq-downscaling-linear1

   \frac{V_{i}}{V} = \frac{W_{i}}{W}

Rearranging yields:

.. math::
  :label: eq-downscaling-linear

   V_{i} = V \cdot \frac{W_{i}}{W}

.. _theory downscaling variance:

Variance Downscaling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Variance downscaling assumes that deviations of the covariate
:math:`W_{i}` around its mean correspond proportionally to deviations
of the variable :math:`V_{i}` around its mean:

.. math::
  :label: eq-downscaling-variance1

   V_{i} - \bar{V} \propto W_{i} - \bar{W}

Introducing a **scaling factor** :math:`m`:

.. math::
  :label: eq-downscaling-variance2

   V_{i} - \bar{V} = m \cdot (W_{i} - \bar{W})

Rearranging yields:

.. math::
  :label: eq-downscaling-variance

   V_{i} = \bar{V} + m \cdot (W_{i} - \bar{W})

.. admonition:: Caution with overflow error
  :class: caution

  Depending on the choice of scaling factor :math:`m`, results for
  :math:`V_{i}` may produce unrealistic values, such as negative
  quantities or extreme magnitudes (overflow error).

.. _theory downscaling variance reverse:

Reverse Variance Downscaling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Reverse proportionality of variance occurs when the covariate is a reversed
variable. This yields a a similar approach for downscaling:

.. math::
  :label: eq-downscaling-variance-rotated1

   V_{i} - \bar{V} = m \cdot (\bar{W} - W_{i})

Rearranging yields:

.. math::
  :label: eq-downscaling-variance-rotated

   V_{i} = V - m \cdot (W_{i} - W)



.. _theory model structure:

Model Structure
=======================================================================

The ``plans`` model is based on a `System Dynamics`_ structure, representing the
hillslope system as **columns** of interconnected storages — like a collection
of water buckets — that fill, spill, drain and dry over time.

Each column is known as the **hydrological response unit** ``HRU``. A
landscape spatial unit with a specific parameter set.

The model column begins with a canopy storage,
followed by a surface storage (which can include an organic soil layer
where present). Beneath it lies the mineral soil storage, divided into
an unsaturated zone (where water moves vertically through pores) and a
saturated phreatic zone (fully saturated, driving drainage and lateral
exchanges with neighboring cells).


.. include:: ./figs/model_structure.rst

.. admonition:: System components index
   :class: seealso

   Check out the full reference for variables and parameters at the
   :ref:`system-index` page.

Storage phases
----------------------------------------------------------------------

Each storage exchanges water through three main mechanisms: **draining**
(water leaks downward), **spilling** (water overflows to the next
component), and **drying** (water is lost through evaporation).
Together, these processes form a network of storages connected by flows,
with parameters regulating their behavior (e.g., residence time).

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

.. _theory model scaling:

Model Scaling
=======================================================================

Scaling in ``plans`` makes use of the concept of Hydrologic Response Units (HRU).
Theses units are defined by a unique combination of land use class, soil class
and topographic saturation index. All variables and parameters simulated are
referred to the scale of the HRU.

The size of HRU can vary depending on the simulation approach. In the
:ref:`G2G approach<theory g2g>` the HRU is cell (or pixel) in the raster maps.
In the :ref:`HST approach<theory hst>` the HRU size is an intermediate set of
units aggregated by soil, land use and a discretization of the topographic saturation index.


.. _theory scaling parameters:

Scaling parameters
----------------------------------------------------------------------

A parameter is a static value attributed to the HRU. In the case of land use,
it can vary with time, but it is defined as an input prior to the simulation.

In ``plans``, parameters usually are given at the basin scale in the
:ref:`io-parameters_info` table. This means that downscaling is the most
required process. However, upscaling is also needed for some processing
steps.

.. _theory upscaling parameters:

Upscaling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Model parameters :math:`V` of land use and soils are upscaled by
:ref:`theory averaging`. Equation :eq:`eq-upscaling-avg` is
applied over the basin area in the map.

In the hydrological terms: let :math:`V_{u}` be the parameter value in
HRU units in a basin :math:`B` indexed by :math:`u \in \{1, 2, \ldots, N\}`.
This value is upscaled to the basin level :math:`B` by area averaging:

.. math::
  :label: eq-upscaling-parameters

   V_{B} = \frac{ \sum_{u=1}^N V_{u} A_{u}}
               {\sum_{u=1}^N A_{u}}

where

- :math:`V_{B}` is the upscaled value to basin :math:`B`,
- :math:`V_{u}` is the parameter value of HRU :math:`u`,
- :math:`A_{u}` is the area extent of HRU :math:`u`,
- :math:`N` is the number of HRU contained within the basin

For example, if a basin contains multiple land-use or soil classes,
the **effective parameter value** for the entire basin is obtained as
the weighted average of each classes's parameter value.
The weights in here correspond to the **area** of each class within the basin.

This formulation ensures that land use or soil classes with larger spatial
extent contribute more strongly to the effective, upscaled parameter value.

.. _theory downscaling parameters:

Downscaling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In contrast to upscaling, The effective basin-scale parameter value
:math:`V` is known a priori from the model parameter table [todo link].
Once the value is known, the downscaling method applies
:ref:`theory downscaling linear`.

In the hydrological terms: let :math:`V_{B}` be the upscaled parameter value in
a basin :math:`B` indexed by :math:`u \in \{1, 2, \ldots, N\}` HRU units.
Also, let :math:`W_{u}` be a **downscaling weight** known at the HRU scale,
and :math:`W_{B}` is the averaged downscaling weight value at the basin scale.
The downscaled value of :math:`V_{u}` ay the HRU level is given by linear proportion:

.. math::
  :label: eq-downscaling-parameters

   V_{u} = W_{u} \cdot \frac{V_{B}}{W_{B}}

This means that Equation :eq:`eq-downscaling-parameters` distributes the
basin-scale parameter value :math:`V_{B}` back to the HRU values :math:`V_{u}` by
applying the provided downscaling weights :math:`W_{u}` provided in the attribute table of
land use or soil classes [todo links].

.. admonition:: Using covariates as downscaling weights
   :class: note

   Downscaling weights :math:`W_{i}` can be defined with downscaling functions and
   the use of **covariates**. For example, one might use a theory relating vegetation
   indices (e.g., LAI or NDVI [todo link]) as proxies for the distribution of
   land use parameters. The same logic applies to soils information.


.. _theory scaling soil moisture:

Scaling soil moisture
----------------------------------------------------------------------

.. include:: ./includes/ipsum.rst

.. _theory upscaling soil moisture:

Upscaling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: ./includes/ipsum.rst

.. _theory downscaling soil moisture:

Upscaling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: ./includes/ipsum.rst


.. _theory scaling other:

Other variables
----------------------------------------------------------------------

.. include:: ./includes/ipsum.rst


References
=======================================================================

.. include:: ./includes/ipsum.rst


.. toctree::
   :maxdepth: 1
   :hidden:

   system
