#! /usr/bin/env python3

import os
import sys
import pytest
import cftime
import numpy as np
import xarray as xr

sys.path.append(os.path.abspath(os.path.join("notebooks", "utils")))
sys.path.append(os.path.abspath("tests"))
from utils import time_year_plus_frac, time_set_mid, repl_coord, round_sig
from xr_ds_ex import gen_time_bounds_values, xr_ds_ex

nyrs = 300
var_const = False


@pytest.mark.parametrize("decode_times1", [True, False])
@pytest.mark.parametrize("decode_times2", [True, False])
@pytest.mark.parametrize("apply_chunk1", [True, False])
def test_repl_coord(decode_times1, decode_times2, apply_chunk1):
    ds1 = time_set_mid(xr_ds_ex(decode_times1, nyrs=nyrs, var_const=var_const), "time")
    if apply_chunk1:
        ds1 = ds1.chunk({"time": 12})

    # change time:bounds attribute variable rename corresponding variable
    tb_name_old = ds1["time"].attrs["bounds"]
    tb_name_new = tb_name_old + "_new"
    ds1["time"].attrs["bounds"] = tb_name_new
    ds1 = ds1.rename({tb_name_old: tb_name_new})

    # verify that repl_coord on xr_ds_ex gives same results as
    # 1) executing time_set_mid
    # 2) manually changing bounds
    ds2 = repl_coord(
        "time", ds1, xr_ds_ex(decode_times2, nyrs=nyrs, var_const=var_const)
    )
    assert ds2.identical(ds1)

    assert ds2["time"].encoding == ds1["time"].encoding
    assert ds2["time"].chunks == ds1["time"].chunks


@pytest.mark.parametrize("decode_times", [True, False])
@pytest.mark.parametrize("deep", [True, False])
@pytest.mark.parametrize("apply_chunk", [True, False])
def test_time_set_mid(decode_times, deep, apply_chunk):
    ds = xr_ds_ex(decode_times, nyrs=nyrs, var_const=var_const, time_mid=False)
    if apply_chunk:
        ds = ds.chunk({"time": 12})

    mid_month_values = gen_time_bounds_values(nyrs).mean(axis=1)
    if decode_times:
        time_encoding = ds["time"].encoding
        expected_values = cftime.num2date(
            mid_month_values, time_encoding["units"], time_encoding["calendar"]
        )
    else:
        expected_values = mid_month_values

    ds_out = time_set_mid(ds, "time", deep)

    assert ds_out.attrs == ds.attrs
    assert ds_out.encoding == ds.encoding
    assert ds_out.chunks == ds.chunks

    for varname in ds.variables:
        assert ds_out[varname].attrs == ds[varname].attrs
        assert ds_out[varname].encoding == ds[varname].encoding
        assert ds_out[varname].chunks == ds[varname].chunks
        if varname == "time":
            assert np.all(ds_out[varname].values == expected_values)
        else:
            assert np.all(ds_out[varname].values == ds[varname].values)
            assert (ds_out[varname].data is ds[varname].data) == (not deep)

    # verify that values are independent of ds being chunked in time
    ds_chunk = xr_ds_ex(
        decode_times, nyrs=nyrs, var_const=var_const, time_mid=False
    ).chunk({"time": 6})
    ds_chunk_out = time_set_mid(ds_chunk, "time")
    assert ds_chunk_out.identical(ds_out)


@pytest.mark.parametrize("decode_times", [True, False])
def test_time_year_plus_frac(decode_times):
    ds = xr_ds_ex(decode_times, nyrs=nyrs, var_const=var_const)

    # call time_year_plus_frac to ensure that it doesn't raise an exception
    ty = time_year_plus_frac(ds, "time")


@pytest.mark.parametrize(
    "x, ndigits, expected",
    [
        (0.0, 1, 0.0),
        (0.0, 2, 0.0),
        (1.25, 1, 1.0),
        (1.25, 3, 1.25),
        (12.5, 1, 10.0),
        (12.5, 2, 12.0),  # round to even
        (12.5, 3, 12.5),
        (12.5, 4, 12.5),
        (13.5, 1, 10.0),
        (13.5, 2, 14.0),  # round to even
        (13.5, 3, 13.5),
        (13.52, 3, 13.5),
        (13.48, 3, 13.5),
        (13.5, 4, 13.5),
    ],
)
def test_round_sig(x, ndigits, expected):
    assert round_sig(x, ndigits) == expected
