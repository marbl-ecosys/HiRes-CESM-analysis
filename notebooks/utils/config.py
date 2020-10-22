"""
    Helper functions to find files in the various directories
"""

import os

user = "mlevy"


def get_rundir(casename):
    return os.path.join(os.sep, "glade", "scratch", user, casename, "run")


################################################################################


def get_campaign_popseries_dir(casename):
    freq_name = dict()
    return os.path.join(
        os.sep,
        "glade",
        "campaign",
        "cesm",
        "development",
        "bgcwg",
        "projects",
        "hi-res_JRA",
        "cases",
        casename,
        "output",
        "ocn",
        "proc",
        "tseries",
    )


################################################################################


def get_campaign_ciceseries_dir(casename):
    freq_name = dict()
    return os.path.join(
        os.sep,
        "glade",
        "campaign",
        "cesm",
        "development",
        "bgcwg",
        "projects",
        "hi-res_JRA",
        "cases",
        casename,
        "output",
        "ice",
        "proc",
        "tseries",
    )


################################################################################


def get_archive_pophist_dir(casename):
    return os.path.join(
        os.sep, "glade", "scratch", user, "archive", casename, "ocn", "hist"
    )


################################################################################


def get_archive_cicehist_dir(casename):
    return os.path.join(
        os.sep, "glade", "scratch", user, "archive", casename, "ice", "hist"
    )


################################################################################


def get_archive_log_dir(casename):
    return os.path.join(os.sep, "glade", "scratch", user, "archive", casename, "logs")


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
