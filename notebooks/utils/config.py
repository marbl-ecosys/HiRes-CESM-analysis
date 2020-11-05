"""
    Helper functions to find files in the various directories
"""

import os


def get_rundir(casename, run_root):
    return os.path.join(run_root, casename, "run")


################################################################################


def get_campaign_popseries_dir(casename, campaign_root):
    freq_name = dict()
    return os.path.join(campaign_root, casename, "output", "ocn", "proc", "tseries",)


################################################################################


def get_campaign_ciceseries_dir(casename, campaign_root):
    freq_name = dict()
    return os.path.join(campaign_root, casename, "output", "ice", "proc", "tseries",)


################################################################################


def get_archive_pophist_dir(casename, archive_hist_root):
    return os.path.join(archive_hist_root, casename, "ocn", "hist")


################################################################################


def get_archive_cicehist_dir(casename, archive_hist_root):
    return os.path.join(archive_hist_root, casename, "ice", "hist")


################################################################################


def get_archive_log_dir(casename, archive_hist_root):
    return os.path.join(archive_hist_root, casename, "logs")


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
