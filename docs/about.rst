.. include:: ./_links.rst

.. include:: ./includes/warning_development.rst

.. _about:

About
######################################################################

.. include:: ./includes/short_description.rst

.. include:: ./figs/about.rst

In a nutshell, it allows assessment and simulation of of **hydrological processes** such as `overland flow`_, `infiltration`_ and `soil moisture`_ in a very useful spatial resolution, the **hillslope scale**.

``plans`` is based on the `TOPMODEL`_ approach for modeling hillslope hydrology. This approach allows a spatially explicit representation of **riparian wetland dynamics** (also known as the concept of *variable source area*).

.. include:: ./figs/riparian_wetlands.rst

In this sense, ``plans`` is an alternative for tools like `SWAT`_ and `InVEST`_, since they do *not* represent this dynamics. Actually, most hydrological models represent hydrology only at the **catchment scale**, while TOPMODEL allows for a finer detail in mapping hydrological processes.

Process representation at the hillslope scale makes the use of ``plans`` fit for the purpose of planning **watershed conservation projects**. Managers may use ``plans`` outputs to map the **infiltration potential** across the landscape, optimizing the spatial allocation of Nature-based solutions.

.. include:: ./figs/infiltration_pot.rst

To run ``plans`` in a Area of Interest, users are required to provide a set of **input data**, like time series of rain and maps of topography and land use.

.. admonition:: User Guide
   :class: seealso

   Check out the :ref:`User Guide <userguide>` for more details on how to use ``plans``

.. admonition:: Gallery
   :class: seealso

   Check out the :ref:`Gallery <gallery>` page for more details on ``plans`` outputs

.. admonition:: Study Cases
   :class: seealso

   Check out the :ref:`Study Cases <cases>` page for ``plans`` published applications

.. admonition:: Theoretical Reference
   :class: seealso

   Check out the :ref:`Theoretical Reference <theory>` page for the scientific basis of ``plans``


.. toctree::
   :maxdepth: 1
   :hidden:

   About <self>
   gallery
   cases
   theory








