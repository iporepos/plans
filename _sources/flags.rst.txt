.. _flags:

Flags
#######################################################################

Every record in a ``plans`` database carries one flag that qualifies its
value. The catalog ships with the package and seeds the ``flags`` table when
a database is created. This page is built from the same file.

The sign of the flag carries meaning. Positive flags always come with a
measured value: ``regular`` is the default, ``raw`` marks values as they came
from the instrument, ``consisted`` marks values validated by quality control,
and ``suspect`` is set automatically on insert when a ``regular`` value falls
outside the variable domain. Flags of zero or below mean there is no measured
value, and only they allow an empty value: a gap reported by the source
(``void``), an analysis that was not done or does not apply, or a result
below the detection limit. A ``nondetect`` record may hold the detection limit
instead of an empty value.

Because censored records hold a limit rather than a measurement, analyses
should select records by flag before computing statistics, instead of
averaging every record of a spec.

.. include:: ./generated/catalogs/flags.rst
