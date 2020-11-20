"""
    Helper functions to find files in the various directories
"""

import os


################################################################################


def add_first_date_and_reformat(date_list):
    new_list = []
    for date in date_list:
        year = int(date[:4])
        month = int(date[4:6])
        day = int(date[6:])
        if len(new_list) == 0:
            if day > 1:
                first_date = f"{year:04}-{month:02}-{(day-1):02}"
            else:
                first_date = "first"
            new_list.append(first_date)
        new_list.append(f"{year:04}-{month:02}-{day:02}")
    return new_list
