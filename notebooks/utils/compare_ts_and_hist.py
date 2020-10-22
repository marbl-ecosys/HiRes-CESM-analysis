#!/usr/bin/env python
"""
A script to verify that converting from history files to time series worked as expected
"""

import xarray as xr

from .CaseClass import CaseClass


def compare_ts_and_hist(
    casename, stream, year, exclude_vars=["time_bound", "time_bounds"]
):
    """
    Generate a CaseClass object from a given casename. For a given stream
    and year, open the history files from the case. Then loop through the
    variables (excluding time_bound in POP and time_bounds in CICE) and
    verify that those fields are available in time series.
    """
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

    found_all = True

    case = CaseClass(casename)
    # Return if no time series is available
    if len(case.get_timeseries_files(year, stream)) == 0:
        return "no time series"

    # Return if no history files are available
    history_filenames = case.get_history_files(year, stream)
    if len(history_filenames) == 0:
        return "no history"

    # Open history files to build dataset
    ds_hist = xr.open_mfdataset(history_filenames, **open_mfdataset_kwargs)
    vars_to_check = [
        var
        for var in ds_hist.data_vars
        if "time" in ds_hist[var].coords and not var in exclude_vars
    ]

    # Look for each variable in time series
    for var in vars_to_check:
        if len(case.get_timeseries_files(year, stream, var)) == 0:
            print(f"No time series files for {var} in year {year:04}")
            found_all = False

    # Return "same" if all variables were found, otherwise return "datasets differ"
    if not found_all:
        return "datasets differ"
    return "same"


########################

if __name__ == "__main__":
    print("Feature not implemented yet")
