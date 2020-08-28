#! /usr/bin/env python3

import os
import sys
import pytest
import xarray as xr
import numpy as np

sys.path.append(os.path.abspath(os.path.join("notebooks", "utils")))
sys.path.append(os.path.abspath("tests"))
from utils_units import _clean_units, conv_units
from xr_ds_ex import xr_ds_ex

nyrs = 3
var_const = False


@pytest.mark.parametrize(
    "units_in, units_out",
    [
        # basic example, straight from dictionary
        ("years", "common_years"),
        # ensure 'gC' in 'degC' doesn't get converted
        ("degC", "degC"),
        # matches within expressions
        ("gN leaf/m^2", "g leaf/m^2"),  # LNC
        ("gC/m^2/s", "g/m^2/s"),  # AR
        ("meq/m^3", "mmol/m^3"),  # ALK
        (
            "(centimeter^2)(meq/m^3 cm/s)",
            "(centimeter^2)(mmol/m^3 cm/s)",
        ),  # ALK_RIV_FLUX integral
        ("neq/cm3", "nmol/cm3"),  # ABIO_ALK_SURF
        ("degC*cm/s", "degC*cm/s"),  # T_FLUX_EXCH_INTRF
        ("days since 0001-01-01 00:00:00", "days since 0001-01-01 00:00:00"),  # time
        # multiple matches
        ("gC/gN", "g/g"),  # LEAFCN
    ],
)
def test_clean_units(units_in, units_out):
    assert _clean_units(units_in) == units_out


@pytest.mark.parametrize("apply_chunk", [True, False])
@pytest.mark.parametrize("add_encoding", [True, False])
def test_conv_units(apply_chunk, add_encoding):
    da = xr_ds_ex()["var_ex"]
    da.attrs["units"] = "kg"
    da.attrs["long_name"] = "var_ex"
    if apply_chunk:
        da = da.chunk({"time": 12})
    if add_encoding:
        da.encoding["_FillValue"] = None

    da_out = conv_units(da, "g")

    assert da_out.attrs["units"] == "g"
    assert da_out.encoding == da.encoding
    assert da_out.chunks == da.chunks
    assert np.all(da_out.values == 1000.0 * da.values)
