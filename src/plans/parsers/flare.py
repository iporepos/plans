# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Routines for handling file name formatting

Overview
--------

# todo [major docstring improvement] -- overview
Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Pellentesque habitant morbi tristique senectus
et netus et malesuada fames ac turpis egestas.

Example
-------

# todo [major docstring improvement] -- examples
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam,
in porttitor lacus lobortis vitae. In a lacinia nisl.

"""

import re


def encode_number(number, decimals=0, len_min=1, is_latitude=True):
    """
    Encodes a given number (latitude or longitude) into a specific string format.

    :param number: The number to encode (latitude or longitude).
    :type number: float or int
    :param decimals: The number of decimal places to include. Default value = 0
    :type decimals: int
    :param len_min: The minimum length of the integer part, padded with leading zeros if necessary. Default value = 1
    :type len_min: int
    :param is_latitude: If True, the number is treated as a latitude; otherwise, as a longitude. Default value = True
    :type is_latitude: bool
    :return: The encoded number string.
    :rtype: str
    """

    def fill_integer_part(part, len_min):
        n_len_part = len(part)
        if n_len_part < len_min:
            return part.zfill(len_min)
        else:
            return part

    # Determine the sign flag based on number and coordinate type
    if is_latitude:  # Latitude: 's' for south (negative), 'n' for north (positive)
        if number < 0:
            sign_flag = "s"
        else:
            sign_flag = "n"
    else:  # Longitude: 'w' for west (negative), 'e' for east (positive)
        if number < 0:
            sign_flag = "w"
        else:
            sign_flag = "e"

    # Work with the absolute value for number representation
    abs_number = abs(number)

    encoded_number_part = ""

    # Handle decimals based on tolerance
    if decimals == 0:
        # If tolerance is zero, encode as an integer (no 'p')
        # Round the number to the nearest integer before converting to string
        integer_part_str = str(int(round(abs_number)))
        # Apply zfill to the integer part if zfill_amount is greater than its length
        integer_part_str = fill_integer_part(part=integer_part_str, len_min=len_min)
        encoded_number_part = integer_part_str
    else:
        # Format the number to the specified decimal places
        formatted_num_str = "{:.{}f}".format(abs_number, decimals)

        # Split into integer and fractional parts
        parts = formatted_num_str.split(".")
        integer_part_str = parts[0]
        fractional_part_str = parts[1]

        # Apply zfill to the integer part if zfill_amount is greater than its length
        integer_part_str = fill_integer_part(part=integer_part_str, len_min=len_min)

        # Reconstruct the number part with 'p'
        encoded_number_part = integer_part_str + "p" + fractional_part_str

    # Combine sign flag and the encoded number part, ensure lowercase output
    return (sign_flag + encoded_number_part).lower()


def decode_number(encoded_number):
    """
    Decodes an encoded number string (latitude or longitude) back into a float.

    :param encoded_number: The encoded number string.
    :type encoded_number: str
    :return: The decoded number.
    :rtype: float
    """
    # Convert the input to lowercase
    encoded_number_lower = encoded_number.lower()
    # Assume positive by default
    sign = 1

    # Check for negative signal flags
    if encoded_number_lower.startswith(("w", "s")):
        sign = -1
        # Remove the sign flag
        encoded_number_lower = encoded_number_lower[1:]
    # Check for positive signal flags
    elif encoded_number_lower.startswith(("e", "n")):
        # Remove the sign flag for number processing (sign remains positive)
        encoded_number_lower = encoded_number_lower[1:]

    # Check 'p' (decimal separator)
    if "p" in encoded_number_lower:
        # Replace 'p' with '.' for standard float conversion
        _ls = encoded_number_lower.split("p")
        integer_part = str(int(decode_number(encoded_number=_ls[0])))
        rational_part = _ls[1]
        encoded_number_lower = integer_part + "." + rational_part

    # return as float
    return sign * float(encoded_number_lower)


def encode_extent(extent_dc, decimals=2, len_min=2, human=False):
    """
    Encodes an extent dictionary into a string format.

    :param extent_dc: A dictionary containing the xmin, xmax, ymin, and ymax values of the extent.
    :type extent_dc: dict
    :param decimals: The number of decimal places to include for the encoded numbers. Default value = 2
    :type decimals: int
    :param len_min: The minimum length of the integer part for the encoded numbers, padded with leading zeros if necessary. Default value = 2
    :type len_min: int
    :param human: If True, the output string will be in a more human-readable format. Default value = False
    :type human: bool
    :return: The encoded extent string.
    :rtype: str
    """
    # retrieve values
    xmin = extent_dc["xmin"]
    xmax = extent_dc["xmax"]
    ymin = extent_dc["ymin"]
    ymax = extent_dc["ymax"]

    # Encode xmin (longitude, so is_latitude=False)
    encoded_xmin = encode_number(
        number=xmin, decimals=decimals, len_min=len_min, is_latitude=False
    )
    # Encode xmax (longitude, so is_latitude=False)
    encoded_xmax = encode_number(
        number=xmax, decimals=decimals, len_min=len_min, is_latitude=False
    )
    # Encode ymin (latitude, so is_latitude=True)
    encoded_ymin = encode_number(
        number=ymin, decimals=decimals, len_min=len_min, is_latitude=True
    )
    # Encode ymax (latitude, so is_latitude=True)
    encoded_ymax = encode_number(
        number=ymax, decimals=decimals, len_min=len_min, is_latitude=True
    )

    # Concatenate all encoded parts to form the extent ID string
    encoded_extent_str = encoded_xmin + encoded_xmax + encoded_ymin + encoded_ymax
    # handle human style
    if human:
        ss = "wesn"
        for s in ss:
            encoded_extent_str = encoded_extent_str.replace(s, f"-{s}")
        if encoded_extent_str[0] == "-":
            encoded_extent_str = encoded_extent_str[1:]
    return encoded_extent_str


def decode_extent(encoded_extent):
    """
    Decodes an encoded extent string back into an extent dictionary.

    :param encoded_extent: The encoded extent string.
    :type encoded_extent: str
    :return: A dictionary containing the xmin, xmax, ymin, and ymax values of the decoded extent.
    :rtype: dict
    """
    # handle human style
    encoded_extent = encoded_extent.replace("-", "")
    # Regex to capture the four parts: [signal][number_part]
    # (x[N]) where x is a signal and N is the number
    pattern = r"([wesn])(\d+p?\d*)"
    matches = re.findall(pattern, encoded_extent.lower())

    coordinates = {}
    # The convention is [left][right][bottom][top]

    # Left (xmin)
    xmin_flag = matches[0][0]
    xmin_value_str = matches[0][1]
    xmin = decode_number(xmin_flag + xmin_value_str)  # Re-add flag

    # Right (xmax)
    xmax_flag = matches[1][0]
    xmax_value_str = matches[1][1]
    xmax = decode_number(xmax_flag + xmax_value_str)

    # Bottom (ymin)
    ymin_flag = matches[2][0]
    ymin_value_str = matches[2][1]
    ymin = decode_number(ymin_flag + ymin_value_str)

    # Top (ymax)
    ymax_flag = matches[3][0]
    ymax_value_str = matches[3][1]
    ymax = decode_number(ymax_flag + ymax_value_str)

    coordinates["xmin"] = xmin
    coordinates["xmax"] = xmax
    coordinates["ymin"] = ymin
    coordinates["ymax"] = ymax

    return coordinates


def decode_epoch(epoch):
    """
    Decodes an epoch string into a dictionary representing the time information.

    This function supports various epoch formats including:
        - Time range (e.g., 'rs2023f2024')
        - Daily human-readable timestamp (YYYY-MM-DD)
        - Daily timestamp (YYYYMMDD)
        - Monthly human-readable timestamp (YYYY-MM)
        - Monthly timestamp (YYYYMM)
        - Yearly timestamp (YYYY)
        - Un-zoned human-readable timestamp (YYYY-MM-DD-thhmmss)
        - Un-zoned timestamp (YYYYMMDDthhmmss)
        - Full human-readable timestamp (YYYY-MM-DD-thhmmss-zshhmm)
        - Full timestamp (YYYYMMDDthhmmsszshhmm)

    :param epoch: The epoch string to decode.
    :type epoch: str
    :return: A dictionary containing the decoded time information, including its type and alias.
    :rtype: dict
    """
    # Check for time range pattern first
    if "f" in epoch.lower():
        parts = epoch.split("f")
        start_label = parts[0]
        end_label = parts[1]

        # Recursively decode start and end timestamps
        decoded_start = decode_epoch(start_label)
        decoded_end = decode_epoch(end_label)

        return {
            "type": "time range",
            "alias": "TR",
            "start": decoded_start,
            "end": decoded_end,
        }

    # Check for human-readable daily timestamp (YYYY-MM-DD)
    if len(epoch) == 10 and epoch[4] == "-" and epoch[7] == "-":
        return {
            "type": "daily human-readable timestamp",
            "alias": "TSDH",
            "year": int(epoch[0:4]),
            "month": int(epoch[5:7]),
            "day": int(epoch[8:10]),
        }

    # Check for daily timestamp (YYYYMMDD)
    if len(epoch) == 8 and epoch.isdigit():
        return {
            "type": "daily timestamp",
            "alias": "TSD",
            "year": int(epoch[0:4]),
            "month": int(epoch[4:6]),
            "day": int(epoch[6:8]),
        }

    # Check for human-readable monthly timestamp (YYYY-MM)
    if len(epoch) == 7 and epoch[4] == "-":
        return {
            "type": "monthly human-readable timestamp",
            "alias": "TSMH",
            "year": int(epoch[0:4]),
            "month": int(epoch[5:7]),
        }

    # Check for monthly timestamp (YYYYMM)
    if len(epoch) == 6 and epoch.isdigit():
        return {
            "type": "monthly timestamp",
            "alias": "TSM",
            "year": int(epoch[0:4]),
            "month": int(epoch[4:6]),
        }

    # Check for yearly timestamp (YYYY)
    if len(epoch) == 4 and epoch.isdigit():
        return {"type": "yearly timestamp", "alias": "TSY", "year": int(epoch[0:4])}

    # Check for un-zoned human-readable timestamp (YYYY-MM-DD-thhmmss)
    if "-t" in epoch and len(epoch) >= 18:
        parts = epoch.split("-t")
        date_part = parts[0]
        time_part = parts[1]
        dc = {
            "type": "Un-zoned human-readable timestamp",
            "alias": "TSUH",
        }
        dc.update(decode_date_part(date_part))
        dc.update(decode_time_part(time_part))
        return dc

    # Check for un-zoned timestamp (YYYYMMDDthhmmss)
    if "t" in epoch and "z" not in epoch and len(epoch) >= 15:
        parts = epoch.split("t")
        date_part = parts[0]
        time_part = parts[1]
        dc = {
            "type": "Un-zoned timestamp",
            "alias": "TSU",
        }
        dc.update(decode_date_part(date_part))
        dc.update(decode_time_part(time_part))
        return dc

    # Check for full human-readable timestamp (YYYY-MM-DD-thhmmss-zshhmm)
    if "-t" in epoch and "-z" in epoch and len(epoch) >= 25:
        date_time_part, tz_part = epoch.split("-z")
        date_part, time_part = date_time_part.split("-t")
        dc = {
            "type": "full human-readable timestamp",
            "alias": "TSH",
        }
        dc.update(decode_date_part(date_part))
        dc.update(decode_time_part(time_part))
        dc.update(decode_tz_part(tz_part))
        return dc

    # Check for full timestamp (YYYYMMDDthhmmsszshhmm)
    if "t" in epoch and "z" in epoch and len(epoch) >= 21:
        date_time_part, tz_part = epoch.split("z")
        date_part, time_part = date_time_part.split("t")
        dc = {
            "type": "full timestamp",
            "alias": "TS",
        }
        dc.update(decode_date_part(date_part))
        dc.update(decode_time_part(time_part))
        dc.update(decode_tz_part(tz_part))
        return dc

    return {"type": "Unknown", "label": epoch}


def decode_date_part(date_part):
    return {
        "year": int(date_part[0:4]),
        "month": int(date_part[4:6]),
        "day": int(date_part[6:8]),
    }


def decode_time_part(time_part):
    return {
        "hour": int(time_part[0:2]),
        "minute": int(time_part[2:4]),
        "second": float(decode_number(time_part[4:])),
    }


def decode_tz_part(tz_part):
    tz_sign = 1 if tz_part[0] == "e" else -1  # 'e' for positive, 'w' for negative
    return {
        "tz_sign": tz_sign,
        "tz_offset_hours": int(tz_part[1:3]),
        "tz_offset_minutes": int(tz_part[3:5]),
    }


def encode_epoch(epoch_dc):
    """
    Encodes an epoch dictionary into a string format.

    :param epoch_dc: A dictionary containing the epoch information.
    :type epoch_dc: dict
    :return: The encoded epoch string.
    :rtype: str
    """
    if epoch_dc["alias"] == "TR":
        start_label = encode_epoch(epoch_dc=epoch_dc["start"])  # Remove 'rs'
        end_label = encode_epoch(epoch_dc=epoch_dc["end"])
        flare_str = f"{start_label}f{end_label}"
    else:
        year = epoch_dc.get("year", 2000)
        month = epoch_dc.get("month", 1)
        day = epoch_dc.get("day", 1)

        hour = epoch_dc.get("hour", 0)
        minute = epoch_dc.get("minute", 0)
        second = epoch_dc.get(
            "second", 0.0
        )  # Default to 0.0 for potential milliseconds

        tz_sign = epoch_dc.get("tz_sign", 1)  # Default to +
        tz_offset_hours = epoch_dc.get("tz_offset_hours", 0)
        tz_offset_minutes = epoch_dc.get("tz_offset_minutes", 0)
        sep = ""
        if epoch_dc["alias"][-1].upper() == "H":
            sep = "-"
        # Format date and time parts with zero-filling
        date_part = f"{year:04d}{sep}{month:02d}{sep}{day:02d}"

        # Handle seconds with decimal part
        if isinstance(second, float):
            # Split integer and fractional parts of seconds
            seconds_int = int(second)
            seconds_frac = int(round((second - seconds_int) * 1000))  # Get milliseconds
            time_part = f"{hour:02d}{minute:02d}{seconds_int:02d}p{seconds_frac:03d}"
        else:
            time_part = f"{hour:02d}{minute:02d}{second:02d}"

        # Format timezone offset
        tz_sign_char = "w" if tz_sign == -1 else "e"
        tz_offset_part = f"{tz_sign_char}{tz_offset_hours:02d}{tz_offset_minutes:02d}"

        # Combine all parts to form ISO 8601 string
        flare_str = f"{date_part}t{time_part}z{tz_offset_part}"

    return flare_str


def encode_iso8601(datetime_dc):
    """
    Encodes a dictionary containing datetime components into an ISO 8601 formatted string.

    :param datetime_dc: A dictionary with datetime components. Expected keys include 'year', 'month', 'day', 'hour', 'minute', 'second' (can be float for milliseconds), 'tz_sign' (-1 for west, 1 for east), 'tz_offset_hours', and 'tz_offset_minutes'. Missing keys will be filled with default values (e.g., 2000-01-01T00:00:00.000+00:00).
    :type datetime_dc: dict
    :return: An ISO 8601 formatted string.
    :rtype: str
    """
    # Extract components from the dictionary
    # Default values for all components to ensure a full timestamp
    year = datetime_dc.get("year", 2000)
    month = datetime_dc.get("month", 1)
    day = datetime_dc.get("day", 1)

    hour = datetime_dc.get("hour", 0)
    minute = datetime_dc.get("minute", 0)
    second = datetime_dc.get("second", 0.0)  # Default to 0.0 for potential milliseconds

    tz_sign = datetime_dc.get("tz_sign", 1)  # Default to +
    tz_offset_hours = datetime_dc.get("tz_offset_hours", 0)
    tz_offset_minutes = datetime_dc.get("tz_offset_minutes", 0)

    # Format date and time parts with zero-filling
    date_part = f"{year:04d}-{month:02d}-{day:02d}"

    # Handle seconds with decimal part
    if isinstance(second, float):
        # Split integer and fractional parts of seconds
        seconds_int = int(second)
        seconds_frac = int(round((second - seconds_int) * 1000))  # Get milliseconds
        time_part = f"{hour:02d}:{minute:02d}:{seconds_int:02d}.{seconds_frac:03d}"
    else:
        time_part = f"{hour:02d}:{minute:02d}:{second:02d}"

    # Format timezone offset
    tz_sign_char = "-" if tz_sign == -1 else "+"
    tz_offset_part = f"{tz_sign_char}{tz_offset_hours:02d}:{tz_offset_minutes:02d}"

    # Combine all parts to form ISO 8601 string
    iso_string = f"{date_part}T{time_part}{tz_offset_part}"

    return iso_string
