.. _statistics:

Statistics
#######################################################################

The statistics catalog tells how the values of a spec were obtained from
the source data. A monthly precipitation total uses ``sum``, a daily mean
temperature uses ``mean``, and values that were never aggregated, such as a
lab analysis or a single station reading, use ``instant``. The catalog ships
with the package and seeds the ``statistics`` table when a database is
created. This page is built from the same file.

Percentiles are named ``pNNN`` after their level: ``p000``, ``p001``,
``p005``, then every 5 up to ``p095``, then ``p099`` and ``p100``. The
formula only defines the quantile, so a spec should state its interpolation
method when it matters. Standard deviation and variance are sample estimates,
dividing by :math:`n-1`.

.. include:: ./generated/catalogs/statistics.rst
