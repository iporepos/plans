.. _variables:

Variables
#######################################################################

The variables catalog defines every quantity a ``plans`` database can store.
Each dataset in a database (a *spec*) points to one variable by its name,
which fixes the units of the actual values and the domain used to flag
suspect values on insert. The catalog ships with the package and seeds the
``variables`` table when a database is created. This page is built from the
same file, so it always matches the installed version.

Variables are grouped by discipline and, within it, by theme. The domain
uses the interval notation of :mod:`plans.databases`: ``[`` and ``]``
include the bound, ``(`` and ``)`` exclude it, an empty bound is unbounded,
and ``U`` separates the bounds and joins intervals, so ``[0U)`` reads as
zero or more. Categorical results, such as positive and negative tests,
are stored as integer codes whose meaning is explained by the spec.

.. include:: ./generated/catalogs/variables.rst
