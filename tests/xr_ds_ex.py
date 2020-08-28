"""function for example xarray.Dataset object"""

import cftime
import numpy as np
import xarray as xr

days_1yr = np.array(
    [31.0, 28.0, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]
)


def gen_time_bounds_values(nyrs=3):
    """return numpy array of values of month boundaries"""
    time_edges = np.insert(np.cumsum(np.tile(days_1yr, nyrs)), 0, 0)
    return np.stack((time_edges[:-1], time_edges[1:]), axis=1)


def xr_ds_ex(decode_times=True, nyrs=3, var_const=True, time_mid=True):
    """return an example xarray.Dataset object, useful for testing functions"""

    # set up values for Dataset, nyrs yrs of analytic monthly values
    time_bounds_values = gen_time_bounds_values(nyrs)
    if time_mid:
        time_values = 0.5 * time_bounds_values[:, 0] + 0.5 * time_bounds_values[:, 1]
    else:
        time_values = 0.25 * time_bounds_values[:, 0] + 0.75 * time_bounds_values[:, 1]
    time_values_yr = time_values / 365.0
    if var_const:
        var_values = np.ones_like(time_values_yr)
    else:
        var_values = np.sin(np.pi * time_values_yr) * np.exp(-0.1 * time_values_yr)

    time_units = "days since 0001-01-01"
    calendar = "noleap"

    if decode_times:
        time_values = cftime.num2date(time_values, time_units, calendar)
        time_bounds_values = cftime.num2date(time_bounds_values, time_units, calendar)

    # create Dataset, including time_bounds
    time_var = xr.DataArray(
        time_values,
        name="time",
        dims="time",
        coords={"time": time_values},
        attrs={"bounds": "time_bounds"},
    )
    if not decode_times:
        time_var.attrs["units"] = time_units
        time_var.attrs["calendar"] = calendar
    time_bounds = xr.DataArray(
        time_bounds_values,
        name="time_bounds",
        dims=("time", "d2"),
        coords={"time": time_var},
    )
    var = xr.DataArray(
        var_values, name="var_ex", dims="time", coords={"time": time_var}
    )
    ds = var.to_dataset()
    days_in_month = xr.DataArray(
        np.tile(days_1yr, nyrs).squeeze(),
        name="days_in_month",
        dims="time",
        coords={"time": time_var},
    )
    ds = xr.merge([ds, time_bounds, days_in_month])

    if decode_times:
        ds.time.encoding["units"] = time_units
        ds.time.encoding["calendar"] = calendar

    return ds
