"""
    Class to use to output (log and netCDF) from the runs
"""

import glob
import os
import gzip as gz
import numpy as np
import xarray as xr

# local modules, not available through __init__
from .config import (
    add_first_date_and_reformat,
    get_archive_log_dir,
    get_campaign_popseries_dir,
    get_archive_pophist_dir,
    get_rundir,
)
from .utils import time_set_mid

################################################################################


class CaseClass(object):

    # Constructor [goal: get an intake-esm catalog into memory; read from disk or generate it]
    def __init__(self, casenames, verbose=False):
        if type(casenames) == str:
            casenames = [casenames]
        if type(casenames) != list:
            raise ValueError(f"{casenames} is not a string or list")
        self._casenames = casenames
        self._verbose = verbose
        self._log_filenames = self._find_log_files()
        self._timeseries_filenames = self._find_timeseries_files()
        self._history_filenames = self._find_hist_files()

        self.log_contents = dict()

    ############################################################################

    def get_co2calc_warning_cnt(self, max_it=4):
        self._read_log("cesm")

        warning_count = dict()
        # For each date, pull value from most recent log file
        for date in self.log_contents["cesm"]:
            logs = list(self.log_contents["cesm"][date].keys())
            logs.sort()
            warning_count[date] = []
            for it in range(1, max_it + 1):
                warning_count[date].append(
                    sum(
                        [
                            f"MARBL WARNING (marbl_co2calc_mod:drtsafe): (marbl_co2calc_mod:drtsafe) it = {it}"
                            in entry
                            for entry in self.log_contents["cesm"][date][logs[-1]]
                        ]
                    )
                )

        return warning_count

    ############################################################################

    def _find_log_files(self):
        """
        Look in rundir and archive for cesm.log, ocn.log, and cpl.log files
        """
        files = dict()
        for component in ["cesm", "ocn", "cpl"]:
            files[component] = []
            for rootdir in [get_archive_log_dir, get_rundir]:
                for casename in self._casenames:
                    files[component] += glob.glob(
                        os.path.join(rootdir(casename), f"{component}.log.*")
                    )
        return files

    ############################################################################

    def _find_timeseries_files(self):
        """
        Look in campaign_dir for pop history files
        """
        files = dict()
        subdirs = dict()
        subdirs["pop.h"] = "month_1"
        subdirs["pop.h.nday1"] = "day_1"
        subdirs["pop.h.nyear1"] = "year_1"
        for stream in ["pop.h", "pop.h.nday1"]:
            files[stream] = []
            for casename in self._casenames:
                files[stream] += glob.glob(
                    os.path.join(
                        get_campaign_popseries_dir(casename),
                        subdirs[stream],
                        f"{casename}.{stream}.*.nc",
                    )
                )
            files[stream].sort()
        return files

    ############################################################################

    def _find_hist_files(self):
        """
        Look in rundir and archive for pop history files
        """
        files = dict()
        for stream in ["pop.h", "pop.h.nday1"]:
            files[stream] = []
            for rootdir in [get_archive_pophist_dir, get_rundir]:
                for casename in self._casenames:
                    files[stream] += glob.glob(
                        os.path.join(rootdir(casename), f"{casename}.{stream}.0*.nc")
                    )
            files[stream].sort()
        return files

    ############################################################################

    def _read_log(self, component):
        """
        Read all log files from specified component. Returns a dict where keys
        are dates and values are contents of log from that date; if multiple
        logs contain the same date, uses the most recent.
        """
        if component in self.log_contents:
            return
        if component not in self._log_filenames:
            raise ValueError(f"No known {component}.log files")

        datestamps = {"cesm": "model date =", "cpl": "tStamp"}
        try:
            datestamp = datestamps[component]
        except:
            raise ValueError(f"Do not know how to find dates in {component}.log")

        all_dates = []
        contents = dict()
        for log in self._log_filenames[component]:
            # Open file
            is_gz = log.endswith("gz")
            if is_gz:
                local_open = gz.open
                mode = "rt"
            else:
                local_open = open
                mode = "r"
            with local_open(log, mode) as f:
                single_log_contents = f.readlines()

            # Look for datestamps in log; if none found, save contents as 'date_unknown'
            date_inds = np.where([datestamp in entry for entry in single_log_contents])[
                0
            ]
            if len(date_inds) == 0:
                date = log.split("/")[-1]
                if date not in contents:
                    contents[date] = dict()
                contents[date][log] = single_log_contents
                continue

            # Set up list of dates and np array of indices
            dates_in_log = [
                entry.split(datestamp)[1].strip()[:8]
                for entry in np.array(single_log_contents)[date_inds].tolist()
            ]
            # add first day of run to dates_in_log, and prepend 0 to date_inds
            date_inds = np.insert(date_inds, 0, 0)
            dates_in_log = add_first_date_and_reformat(dates_in_log)

            # for each date, add contents to dictionary
            for n, date in enumerate(dates_in_log[:-1]):
                if date not in contents:
                    contents[date] = dict()
                contents[date][log] = single_log_contents[
                    date_inds[n] : date_inds[n + 1]
                ]

            #  Need to account for partial days from runs that die
            # e.g. model crashes midway through 00010104 => need an 00010105 stamp (since we're using datestamp from end of the day, e.g. midnight the next day)
            if not is_gz:
                date = dates_in_log[-1]
                if date not in contents:
                    contents[date] = dict()
                contents[date][log] = single_log_contents[date_inds[-1] :]

        self.log_contents[component] = dict()
        for key in sorted(contents):
            self.log_contents[component][key] = contents[key]

    ############################################################################

    def get_catalog(self):
        """
        Return intake esm catalog that was created / read in constructor
        """
        return self.catalog

    ############################################################################

    def gen_dataset(
        self, varnames, stream, start_year=1, end_year=61, verbose=False, **kwargs
    ):
        """
        Open all history files from a specified stream. Returns a dict where keys
        are stream names and values are xarray Datasets

        Pared-down API for working with intake-esm catalog.
        Users familiar with intake-esm may prefer self.get_catalog() and then querying directly.
        """
        if type(varnames) == str:
            varnames = [varnames]
        if type(varnames) != list:
            raise ValueError(f"{casenames} is not a string or list")

        # Set some defaults to pass to open_mfdataset, then apply kwargs argument
        default_kwargs = dict()
        # data_vars="minimal", to avoid introducing time dimension to time-invariant fields
        default_kwargs["data_vars"] = "minimal"
        # compat="override", to skip var consistency checks (for speed)
        default_kwargs["compat"] = "override"
        # coords="minimal", because coords cannot be default="different" if compat="override"
        default_kwargs["coords"] = "minimal"

        # Make sure these variables are kept in all datasets
        _vars_to_keep = ["time_bound", "TAREA"]

        default_kwargs.update(kwargs)

        # Pare down time series file list (only contains years and variables we are interested in)
        ds_timeseries = None
        timeseries_filenames = []
        for var in varnames:
            for year in range(start_year, end_year + 1):
                timeseries_filenames += [
                    filename
                    for filename in self._timeseries_filenames[stream]
                    if f".{var}." in filename and f".{year:04}" in filename
                ]

        if timeseries_filenames:
            ds_timeseries = time_set_mid(
                xr.open_mfdataset(timeseries_filenames, **default_kwargs,)[
                    varnames + _vars_to_keep
                ],
                "time",
            )
            tb = ds_timeseries["time_bound"]
            if tb.dtype == np.dtype("O"):
                start_year = int(tb.values[-1, 1].strftime("%Y"))

        # Pare down history file list
        ds_history = None
        history_filenames = []
        for year in range(start_year, end_year + 1):
            history_filenames += [
                filename
                for filename in self._history_filenames[stream]
                if f".{year:04}" in filename
            ]

        if history_filenames:
            ds_history = time_set_mid(
                xr.open_mfdataset(history_filenames, **default_kwargs,)[
                    varnames + _vars_to_keep
                ],
                "time",
            )

        if not (ds_history or ds_timeseries):
            raise ValueError(
                f"Can not find requested variables between {start_year:04} and {end_year:04}"
            )
        elif ds_history and ds_timeseries:
            print(
                f'Time series ends at {ds_timeseries["time_bound"].values[-1,1]}, history files begin at {ds_history["time_bound"].values[0,0]}'
            )
            ds = xr.concat([ds_timeseries, ds_history], dim="time")
        else:
            ds = ds_history or ds_timeseries

        print(f'Datasets contain a total of {ds.sizes["time"]} time samples')
        tb_name = ds["time"].attrs["bounds"]
        print(f"Last average written at {ds[tb_name].values[-1, 1]}")
        return ds
