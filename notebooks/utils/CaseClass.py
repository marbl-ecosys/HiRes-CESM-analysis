"""
    Class to use to access output (log and netCDF) from CESM runs
"""

import glob
import os
import gzip as gz
import cftime
import numpy as np
import xarray as xr

# local modules, not available through __init__
from .config import add_first_date_and_reformat

from .utils import time_set_mid, dict_copy_vals, print_key_metadata

################################################################################


class CaseClass(object):

    # Constructor [goal: get an intake-esm catalog into memory; read from disk or generate it]
    def __init__(
        self, casenames, output_roots, verbose=False,
    ):
        """
        casenames: a string or list containing the name(s) of the case(s) to include in the object
        output_roots: a string or list containing the name(s) of the directories to search for log / netCDF files
                      * netCDF files may be in one of three locations:
                        1. history files may be in {output_root} itself
                           [e.g. output_root = RUNDIR]
                        2. history files may be in {output_root}/{component}/hist
                           [e.g. output_root = DOUT_S]
                        3. time series files may be in {output_root}/{component}/proc/tseries/{freq}
                           [e.g. output_root = root of pyReshaper output]
                      * log files may be in one of two locations
                        1. {output_root} itself [e.g. output_root = RUNDIR]
                        2. {output_root}/logs [e.g. output_root = DOUT_S]
        """
        if type(casenames) == str:
            casenames = [casenames]
        if type(casenames) != list:
            raise ValueError(f"{casenames} is not a string or list")

        if type(output_roots) == str:
            output_roots = [output_roots]
        if type(output_roots) != list:
            raise ValueError(f"{output_roots} is not a string or list")

        self._casenames = casenames
        self._output_roots = []
        for output_dir in output_roots:
            if os.path.isdir(output_dir):
                self._output_roots.append(output_dir)
        self._verbose = verbose
        # TODO: figure out how to let this configuration be user-specified (maybe YAML?)
        self._stream_metadata = dict()
        self._stream_metadata["pop.h"] = {"comp": "ocn", "freq": "month_1"}
        self._stream_metadata["pop.h.nday1"] = {"comp": "ocn", "freq": "day_1"}
        self._stream_metadata["pop.h.nyear1"] = {"comp": "ocn", "freq": "year_1"}
        self._stream_metadata["cice.h"] = {"comp": "ice", "freq": "month_1"}
        self._stream_metadata["cice.h1"] = {"comp": "ice", "freq": "day_1"}
        self._log_filenames = self._find_log_files()
        self._history_filenames, self._timeseries_filenames = self._find_nc_files()
        self._dataset_files = dict()
        self._dataset_src = dict()

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

    def _get_single_year_timeseries_files(self, year, stream, varname):
        timeseries_filenames = [
            filename
            for filename in self._timeseries_filenames[stream]
            if (f".{varname}." in filename and f".{year:04}" in filename)
        ]
        return timeseries_filenames

    ############################################################################

    def get_timeseries_files(self, year, stream, varnames=None):
        if type(varnames) == str:
            varnames = [varnames]
        if not (type(varnames) == list or varnames is None):
            raise ValueError(
                f"varnames = {varnames} which is not None, a string, or a list"
            )

        timeseries_filenames = []
        if varnames:
            for varname in varnames:
                timeseries_filenames.extend(
                    self._get_single_year_timeseries_files(year, stream, varname)
                )
        else:
            timeseries_filenames = self._get_single_year_timeseries_files(year, stream)

        return timeseries_filenames

    ############################################################################

    def check_for_year_in_timeseries_files(self, year, stream):
        """
        Return True if {stream} has any timeseries files from {year}
        """
        return any(
            [
                f".{year:04}" in filename
                for filename in self._timeseries_filenames[stream]
            ]
        )

    ############################################################################

    def get_history_files(self, year, stream):
        return [
            filename
            for filename in self._history_filenames[stream]
            if f"{stream}.{year:04}" in filename
        ]

    ############################################################################

    def _find_log_files(self):
        """
        Look in each _output_roots dir (and /logs) for cesm.log, ocn.log, and cpl.log files
        """
        files = dict()
        for component in ["cesm", "ocn", "cpl"]:
            files[component] = []
            for output_dir in self._output_roots:
                files[component].extend(
                    glob.glob(os.path.join(output_dir, f"{component}.log.*"))
                )
                if os.path.isdir(os.path.join(output_dir, "logs")):
                    files[component].extend(
                        glob.glob(
                            os.path.join(output_dir, "logs", f"{component}.log.*")
                        )
                    )
        return files

    ############################################################################

    def _find_nc_files(self):
        """
        Look for netcdf files in each output_root directory, as well as
        {component}/hist and {component}/proc/tseries/{freq} subdirectories
        """
        hist_files = dict()
        ts_files = dict()
        for stream in self._stream_metadata:
            hist_files[stream] = []
            ts_files[stream] = []
            comp = self._stream_metadata[stream]["comp"]
            freq = self._stream_metadata[stream]["freq"]
            for casename in self._casenames:
                for output_dir in self._output_roots:
                    if self._verbose:
                        print(f"Checking {output_dir} for {stream} files...")
                    # (1) Look for history files in output_dir
                    #     TODO: need better way to avoid wrong stream than .0*
                    #           (do not want to glob *.pop.h.nday1.* when looking for pop.h files)
                    pattern = f"{casename}.{stream}.0*.nc"
                    files_found = glob.glob(os.path.join(output_dir, pattern))
                    files_found.sort()
                    hist_files[stream].extend(files_found)

                    # (2) look for history files that might be in {output_dir}/{comp}/hist
                    #     TODO: need better way to avoid wrong stream than .0*
                    #           (do not want to glob *.pop.h.nday1.* when looking for pop.h files)
                    hist_dir = os.path.join(output_dir, comp, "hist")
                    if os.path.isdir(hist_dir):
                        pattern = f"{casename}.{stream}.0*.nc"
                        files_found = glob.glob(os.path.join(hist_dir, pattern))
                        files_found.sort()
                        hist_files[stream].extend(files_found)

                    # (3) look for time series files that might be in {output_dir}/{comp}/proc/time_series/{freq}
                    tseries_dir = os.path.join(
                        output_dir, comp, "proc", "tseries", freq
                    )
                    if os.path.isdir(tseries_dir):
                        pattern = f"{casename}.{stream}.*.nc"
                        files_found = glob.glob(os.path.join(tseries_dir, pattern))
                        files_found.sort()
                        ts_files[stream].extend(files_found)

        return hist_files, ts_files

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

    def get_dataset_source(self, stream, year, varname):

        # Does _dataset_src[stream] exist?
        if stream not in self._dataset_src:
            print(f"No datasets have been returned from {stream}")
            return None

        # Does _dataset_src[stream][year] exist?
        if year not in self._dataset_src[stream]:
            print(
                f"No datasets covering year {year:04} have been returned from {stream}"
            )
            return None

        # Does _dataset_src[stream][year][varname] exist?
        if varname not in self._dataset_src[stream][year]:
            print(
                f"No dataset containing {varname} from year {year:04} have been returned from {stream}"
            )
            return None

        return self._dataset_src[stream][year][varname]

    ############################################################################

    def gen_dataset(
        self,
        varnames,
        stream,
        vars_to_keep=None,
        start_year=1,
        end_year=61,
        quiet=False,
        debug=False,
        **kwargs,
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
            raise ValueError(f"{varnames} is not a string or list")

        if stream not in self._dataset_files:
            self._dataset_files[stream] = dict()
            self._dataset_src[stream] = dict()

        # Set some defaults to pass to open_mfdataset, then apply kwargs argument
        open_mfdataset_kwargs = dict()
        # data_vars="minimal", to avoid introducing time dimension to time-invariant fields
        open_mfdataset_kwargs["data_vars"] = "minimal"
        # compat="override", to skip var consistency checks (for speed)
        open_mfdataset_kwargs["compat"] = "override"
        # coords="minimal", because coords cannot be default="different" if compat="override"
        open_mfdataset_kwargs["coords"] = "minimal"
        #  parallel=True to open files in parallel
        open_mfdataset_kwargs["parallel"] = True
        open_mfdataset_kwargs.update(kwargs)

        # Pull specific keys from open_mfdataset_kwargs to pass to xr.concat
        concat_keys = ["data_vars", "compat", "coords"]
        concat_kwargs = {
            key: value
            for key, value in open_mfdataset_kwargs.items()
            if key in concat_keys
        }

        # Make sure these variables are kept in all datasets
        _vars_to_keep = ["time_bound", "TAREA"]
        if vars_to_keep is not None:
            if type(vars_to_keep) == str:
                vars_to_keep = [vars_to_keep]
            if type(vars_to_keep) != list:
                raise ValueError(f"{vars_to_keep} is not a string or list")
            _vars_to_keep.extend(vars_to_keep)

        # Pare down time series file list (only contains years and variables we are interested in)
        ds_timeseries_per_var = []
        for varname in varnames:
            timeseries_filenames = []
            for year in range(start_year, end_year + 1):
                if year not in self._dataset_files[stream]:
                    self._dataset_files[stream][year] = dict()
                    self._dataset_src[stream][year] = dict()
                self._dataset_files[stream][year][varname] = self.get_timeseries_files(
                    year, stream, varnames
                )
                if self._dataset_files[stream][year][varname]:
                    self._dataset_src[stream][year][varname] = "time series"
                    timeseries_filenames.extend(
                        self._dataset_files[stream][year][varname]
                    )
            if timeseries_filenames:
                dsmf = xr.open_mfdataset(timeseries_filenames, **open_mfdataset_kwargs)[
                    [varname] + _vars_to_keep
                ]
                with xr.open_dataset(timeseries_filenames[0])[
                    [varname] + _vars_to_keep
                ] as ds0:
                    if debug:
                        print(open_mfdataset_kwargs)
                        print_key_metadata(
                            dsmf, "timeseries_filenames open_mfdataset dsmf"
                        )
                        print_key_metadata(
                            ds0, "timeseries_filenames open_mfdataset ds0"
                        )
                    dict_copy_vals(ds0.encoding, dsmf.encoding, "unlimited_dims")
                    dict_copy_vals(
                        ds0["time"].encoding,
                        dsmf["time"].encoding,
                        ["dtype", "_FillValue", "units", "calendar"],
                    )
                ds_timeseries_per_var.append(dsmf)

        if ds_timeseries_per_var:
            ds_timeseries = xr.merge(ds_timeseries_per_var, combine_attrs="override")
            ds0 = ds_timeseries_per_var[0]
            if debug:
                print_key_metadata(
                    ds_timeseries, "ds_timeseries_per_var merge ds_timeseries"
                )
                print_key_metadata(ds0, "ds_timeseries_per_var merge ds0")
            dict_copy_vals(ds0.encoding, ds_timeseries.encoding, "unlimited_dims")
            tb_name_ts = ds_timeseries["time"].attrs["bounds"]
            tb = ds_timeseries[tb_name_ts]
            if tb.dtype == np.dtype("O"):
                start_year = int(tb.values[-1, 1].strftime("%Y"))
            else:
                # NOTE: this block will be used if decode_times=False in open_mfdataset()
                #       If decode_times=False because cftime can not decode the time dimension,
                #       then this will likely fail and we'll need a better way to determine
                #       the last year read from time series. Maybe pull from filenames?
                decoded_tb = cftime.num2date(
                    tb.values[-1, 1],
                    tb.attrs["units"],
                    calendar=ds_timeseries["time"].attrs["calendar"],
                )
                start_year = int(decoded_tb.strftime("%Y"))

        # Pare down history file list
        history_filenames = []
        for year in range(start_year, end_year + 1):
            if year not in self._dataset_files[stream]:
                self._dataset_files[stream][year] = dict()
                self._dataset_src[stream][year] = dict()
            self._dataset_files[stream][year][varname] = self.get_history_files(
                year, stream
            )
            if self._dataset_files[stream][year][varname]:
                self._dataset_src[stream][year][varname] = "hist"
                history_filenames.extend(self._dataset_files[stream][year][varname])

        if history_filenames:
            ds_history = xr.open_mfdataset(history_filenames, **open_mfdataset_kwargs)[
                varnames + _vars_to_keep
            ]
            with xr.open_dataset(history_filenames[0])[varnames + _vars_to_keep] as ds0:
                if debug:
                    print_key_metadata(
                        ds_history, "history_filenames open_mfdataset ds_history"
                    )
                    print_key_metadata(ds0, "history_filenames open_mfdataset ds0")
                dict_copy_vals(ds0.encoding, ds_history.encoding, "unlimited_dims")
                dict_copy_vals(
                    ds0["time"].encoding,
                    ds_history["time"].encoding,
                    ["dtype", "_FillValue", "units", "calendar"],
                )

        # Concatenate discovered datasets
        if ds_timeseries_per_var:
            if history_filenames:
                print(
                    f'Time series ends at {ds_timeseries["time_bound"].values[-1,1]}, history files begin at {ds_history["time_bound"].values[0,0]}'
                )
                ds = xr.concat([ds_timeseries, ds_history], dim="time", **concat_kwargs)
                if debug:
                    print_key_metadata(ds, "xr.concat ds")
                    print_key_metadata(ds_timeseries, "xr.concat ds_timeseries")
                    print_key_metadata(ds_history, "xr.concat ds_history")
                for ds_src in [ds_timeseries, ds_history]:
                    dict_copy_vals(
                        ds_src["time"].encoding,
                        ds["time"].encoding,
                        ["dtype", "_FillValue", "units", "calendar"],
                    )
            else:
                ds = ds_timeseries
        else:
            if history_filenames:
                ds = ds_history
            else:
                raise ValueError(
                    f"Can not find requested variables between {start_year:04} and {end_year:04}"
                )

        ds = time_set_mid(ds, "time")

        if not quiet:
            print(f'Datasets contain a total of {ds.sizes["time"]} time samples')
        tb_name = ds["time"].attrs["bounds"]
        if not quiet:
            print(f"Last average written at {ds[tb_name].values[-1, 1]}")
        return ds
