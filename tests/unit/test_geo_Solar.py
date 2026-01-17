# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short module description (1-3 sentences)}
todo docstring

"""

# ***********************************************************************
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
# import {module}
import unittest

# ... {develop}

# External imports
# =======================================================================
import pandas as pd
import matplotlib.pyplot as plt

# ... {develop}

# Project-level imports
# =======================================================================
from plans import geo
from tests.conftest import testmsg

# ... {develop}


# ***********************************************************************
# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# ***********************************************************************
# FUNCTIONS
# ***********************************************************************


# ***********************************************************************
# CLASSES
# ***********************************************************************


# CLASSES -- Project-level
# =======================================================================
class TestSolar(unittest.TestCase):

    # Julian day tests
    # ------------------------------------------------------------------

    def test_julian_day_jan_1(self):
        """
        January 1st must always be day 1.
        """
        dt = "2024-01-01"
        j = geo.julian_day(dt)
        print("\n")
        print(testmsg(f"Date: {dt}"))
        print(testmsg(f"Day: {j}"))
        self.assertEqual(j, 1)

    def test_julian_day_dec_31_non_leap(self):
        """
        December 31st in a non-leap year must be day 365.
        """
        dt = "2023-12-31"
        j = geo.julian_day(dt)
        print("\n")
        print(testmsg(f"Date: {dt}"))
        print(testmsg(f"Day: {j}"))
        self.assertEqual(j, 365)

    def test_julian_day_dec_31_leap(self):
        """
        December 31st in a leap year must be day 366.
        """
        dt = "2024-12-31"
        j = geo.julian_day(dt)
        print("\n")
        print(testmsg(f"Date: {dt}"))
        print(testmsg(f"Day: {j}"))
        self.assertEqual(j, 366)

    # Solar altitude tests
    # ------------------------------------------------------------------

    def test_equator_equinox_noon(self):
        """
        Equator + equinox + noon → Sun at zenith.
        """
        date = "2024-03-20"
        v = geo.solar_altitude(0.0, 12.0, date)
        print("\n")
        print(testmsg("Equator Setting: 0, 12, 2024-03-20"))
        print(testmsg(f"Vertical Angle: {v}"))
        self.assertTrue(88 <= v <= 92)

    def test_tropic_capricorn_dec_solstice(self):
        """
        Tropic of Capricorn + December solstice → zenith Sun.
        """
        date = "2024-12-21"
        v = geo.solar_altitude(-23.45, 12.0, date)
        print("\n")
        print(testmsg("Capricorn Setting: -23, 12, 2024-12-21"))
        print(testmsg(f"Vertical Angle: {v}"))
        self.assertTrue(88 <= v <= 92)

    def test_tropic_cancer_june_solstice(self):
        """
        Tropic of Cancer + June solstice → zenith Sun.
        """
        date = "2024-06-21"
        v = geo.solar_altitude(23.45, 12.0, date)
        print("\n")
        print(testmsg("Cancer Setting: 23, 12, 2024-06-21"))
        print(testmsg(f"Vertical Angle: {v}"))
        self.assertTrue(88 <= v <= 92)

    # ------------------------------------------------------------------
    # Solar azimuth tests
    # ------------------------------------------------------------------

    def test_equator_equinox_morning_east(self):
        """
        Equator + equinox + morning → Sun must be in the eastern sky.
        """
        date = "2024-03-20"
        az = geo.solar_azimuth(0.0, 9.0, date)
        print("\n", testmsg(f"Azimuth (equator, morning): {az:.2f}"), sep="\n")
        self.assertTrue(45 <= az <= 135)

    def test_equator_equinox_afternoon_west(self):
        """
        Equator + equinox + afternoon → Sun must be in the western sky.
        """
        date = "2024-03-20"
        az = geo.solar_azimuth(0.0, 15.0, date)
        print("\n", testmsg(f"Azimuth (equator, afternoon): {az:.2f}"), sep="\n")
        self.assertTrue(225 <= az <= 315)

    def test_northern_hemisphere_noon_south(self):
        """
        Northern Hemisphere midday Sun must come from the south.
        """
        date = "2024-06-21"
        az = geo.solar_azimuth(45.0, 12.0, date)
        print("\n", testmsg(f"Azimuth (NH noon): {az:.2f}"), sep="\n")
        self.assertTrue(135 <= az <= 225)

    def test_southern_hemisphere_noon_north(self):
        """
        Southern Hemisphere midday Sun must come from the north.
        """
        date = "2024-12-21"
        az = geo.solar_azimuth(-45.0, 12.0, date)
        print("\n", testmsg(f"Azimuth (SH noon): {az:.2f}"), sep="\n")
        self.assertTrue(az <= 45 or az >= 315)

    def test_azimuth_monotonicity_before_noon(self):
        """
        Azimuth must increase monotonically during the morning.
        """
        date = "2024-03-20"
        az1 = geo.solar_azimuth(0.0, 9.0, date)
        az2 = geo.solar_azimuth(0.0, 10.0, date)
        az3 = geo.solar_azimuth(0.0, 11.0, date)

        print(
            "\n",
            testmsg(
                f"Azimuths (Equinox, Equator, Morning): {az1:.2f}, {az2:.2f}, {az3:.2f}"
            ),
            sep="\n",
        )
        self.assertTrue(az1 < az2 < az3)

    def test_azimuth_monotonicity_after_noon(self):
        """
        Azimuth must increase monotonically after noon.
        """
        date = "2024-03-20"
        az1 = geo.solar_azimuth(0.0, 13.0, date)
        az2 = geo.solar_azimuth(0.0, 14.0, date)
        az3 = geo.solar_azimuth(0.0, 15.0, date)

        print(
            "\n",
            testmsg(
                f"Azimuths (Equinox, Equator, Afternoon): {az1:.2f}, {az2:.2f}, {az3:.2f}"
            ),
            sep="\n",
        )
        self.assertTrue(az1 < az2 < az3)

    def test_azimuth_symmetry_around_noon(self):
        """
        Morning and afternoon azimuths should be symmetric around solar noon.
        """
        date = "2024-03-20"
        az_morning = geo.solar_azimuth(0.0, 10.0, date)
        az_afternoon = geo.solar_azimuth(0.0, 14.0, date)

        print(
            "\n",
            testmsg(f"Azimuth (equator morning): {az_morning:.2f}"),
            testmsg(f"Azimuth (equator morning): {az_afternoon:.2f}"),
            sep="\n",
        )

        self.assertAlmostEqual(
            az_morning + az_afternoon,
            360,
            delta=5,
        )

    # Solar illumination (hourly simulation) tests
    # ------------------------------------------------------------------

    def test_simulation_head_tail_visual_inspection(self):
        """
        Diagnostic test: print head and tail of the annual simulation
        for manual inspection in CI logs.
        """
        df = geo.solar_illumination(2024, 65.0, frequency="1h")

        print("\n--- solar_illumination HEAD ---")
        print(df.head(10))

        print("\n--- solar_illumination TAIL ---")
        print(df.tail(10))

        # Minimal sanity check to keep this as a valid unit test
        self.assertGreater(len(df), 0)

    def test_simulation_length_non_leap_year_1h(self):
        """
        Non-leap year must have 365 * 24 hourly records.
        """
        df = geo.solar_illumination(2023, 0.0, frequency="1h")
        self.assertEqual(len(df), 365 * 24)

    def test_simulation_length_non_leap_year_2h(self):
        """
        Non-leap year must have 365 * 24 hourly records.
        """
        df = geo.solar_illumination(2023, 0.0, frequency="2h")
        self.assertEqual(len(df), 365 * 12)

    def test_simulation_length_leap_year(self):
        """
        Leap year must have 366 * 24 hourly records.
        """
        df = geo.solar_illumination(2024, 0.0)
        self.assertEqual(len(df), 366 * 24)

    def test_simulation_columns(self):
        """
        Output DataFrame must contain the expected columns.
        """
        df = geo.solar_illumination(2024, 0.0)
        expected = {"datetime", "julian_day", "altitude", "azimuth"}
        self.assertTrue(expected.issubset(df.columns))

    def test_datetime_monotonicity(self):
        """
        Datetime column must be strictly increasing hourly.
        """
        df = geo.solar_illumination(2024, 0.0)
        self.assertTrue(df["datetime"].is_monotonic_increasing)

    def test_julian_day_bounds(self):
        """
        Julian day must stay within valid bounds.
        """
        df = geo.solar_illumination(2024, 0.0)
        self.assertEqual(df["julian_day"].min(), 1)
        self.assertEqual(df["julian_day"].max(), 366)

    def test_nighttime_values_are_nan(self):
        """
        When altitude is NaN (night), azimuth must also be NaN.
        """
        df = geo.solar_illumination(2024, 0.0)
        night = df["altitude"].isna()
        self.assertTrue(df.loc[night, "azimuth"].isna().all())

    def test_midday_altitude_positive(self):
        """
        At least one midday value per year must have positive altitude.
        """
        df = geo.solar_illumination(2024, 0.0)
        midday = df[df["datetime"].dt.hour == 12]
        self.assertTrue((midday["altitude"] > 0).any())

    def test_azimuth_bounds(self):
        """
        Azimuth values must lie in [0, 360).
        """
        df = geo.solar_illumination(2024, 0.0)
        az = df["azimuth"].dropna()
        self.assertTrue(((az >= 0) & (az < 360)).all())

    def test_altitude_physical_bounds(self):
        """
        Solar altitude must lie in (0, 90].
        """
        df = geo.solar_illumination(2024, 0.0)
        alt = df["altitude"].dropna()
        self.assertTrue(((alt > 0) & (alt <= 90)).all())

    def test_consistency_with_scalar_functions(self):
        """
        Aggregated values must match scalar solar_altitude and solar_azimuth.
        """
        df = geo.solar_illumination(2024, 0.0)

        row = df.iloc[1000]
        dt = row["datetime"]
        hour = dt.hour + dt.minute / 60

        alt = geo.solar_altitude(0.0, hour, date=dt.strftime("%Y-%m-%d"))
        az = geo.solar_azimuth(0.0, hour, date=dt.strftime("%Y-%m-%d"))

        if pd.isna(alt):
            self.assertTrue(pd.isna(row["altitude"]))
            self.assertTrue(pd.isna(row["azimuth"]))
        else:
            self.assertAlmostEqual(row["altitude"], alt, places=6)
            self.assertAlmostEqual(row["azimuth"], az, places=6)


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    # Script section
    # ===================================================================
    unittest.main()
    # ... {develop}
