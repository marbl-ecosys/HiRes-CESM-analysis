"""utility functions"""

import math

import cftime
import numpy as np
import xarray as xr


def repl_coord(coordname, ds1, ds2):
    """
    Return copy of d2 with coordinate coordname replaced, using coordname from ds1.
    Drop ds2.coordname.attrs['bounds'] in result, if ds2.coordname has bounds attribute.
    Add ds1.coordname.attrs['bounds'] to result, if ds1.coordname has bounds attribute.
    Except for coordname, the returned Dataset is a non-deep copy of ds2.
    """
    if "bounds" in ds2[coordname].attrs:
        tb_name = ds2[coordname].attrs["bounds"]
        ds_out = ds2.drop(tb_name).assign_coords({coordname: ds1[coordname]})
    else:
        ds_out = ds2.assign_coords({coordname: ds1[coordname]})
    if "bounds" in ds1[coordname].attrs:
        tb_name = ds1[coordname].attrs["bounds"]
        ds_out = xr.merge([ds_out, ds1[tb_name]])
    return ds_out


def time_set_mid(ds, time_name, deep=False):
    """
    Return copy of ds with values of ds[time_name] replaced with midpoints of
    ds[time_name].attrs['bounds'], if bounds attribute exists.
    Except for time_name, the returned Dataset is a copy of ds2.
    The copy is deep or not depending on the argument deep.
    """

    ds_out = ds.copy(deep=deep)

    if "bounds" not in ds[time_name].attrs:
        return ds_out

    tb_name = ds[time_name].attrs["bounds"]
    tb = ds[tb_name]
    bounds_dim = next(dim for dim in tb.dims if dim != time_name)

    # Use da = da.copy(data=...), in order to preserve attributes and encoding.

    # If tb is an array of datetime objects then encode time before averaging.
    # Do this because computing the mean on datetime objects with xarray fails
    # if the time span is 293 or more years.
    #     https://github.com/klindsay28/CESM2_coup_carb_cycle_JAMES/issues/7
    if tb.dtype == np.dtype("O"):
        units = "days since 0001-01-01"
        calendar = "noleap"
        tb_vals = cftime.date2num(ds[tb_name].values, units=units, calendar=calendar)
        tb_mid_decode = cftime.num2date(
            tb_vals.mean(axis=1), units=units, calendar=calendar
        )
        ds_out[time_name] = ds[time_name].copy(data=tb_mid_decode)
    else:
        ds_out[time_name] = ds[time_name].copy(data=tb.mean(bounds_dim))

    return ds_out


def time_year_plus_frac(ds, time_name):
    """return time variable, as numpy array of year plus fraction of year values"""

    # this is straightforward if time has units='days since 0000-01-01' and calendar='noleap'
    # so convert specification of time to that representation

    # get time values as an np.ndarray of cftime objects
    if np.dtype(ds[time_name]) == np.dtype("O"):
        tvals_cftime = ds[time_name].values
    else:
        tvals_cftime = cftime.num2date(
            ds[time_name].values,
            ds[time_name].attrs["units"],
            ds[time_name].attrs["calendar"],
        )

    # convert cftime objects to representation mentioned above
    tvals_days = cftime.date2num(
        tvals_cftime, "days since 0000-01-01", calendar="noleap"
    )

    return tvals_days / 365.0


def round_sig(x, ndigits):
    """round x to ndigits precision"""
    if x == 0:
        return x
    ndigits_offset = math.floor(math.log10(abs(x)))
    return round(x, ndigits - 1 - ndigits_offset)
