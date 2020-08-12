"""
utility functions related to units
"""

import re

from pint import UnitRegistry
import xarray as xr


def clean_units(units):
    """replace some troublesome unit terms with acceptable replacements"""
    replacements = {
        "unitless": "1",
        "years": "common_years",
        "yr": "common_year",
        "meq": "mmol",
        "neq": "nmol",
    }
    units_split = re.split(r"( |\(|\)|\^|\*|/|-[0-9]+|[0-9]+)", units)
    units_split_repl = [
        replacements[token] if token in replacements else token for token in units_split
    ]
    return "".join(units_split_repl)


def conv_units_np(values, units_in, units_out, units_scalef=None):
    """
    return a copy of numpy array values, with units converted from units_in to units_out
    """
    ureg = UnitRegistry()
    values_in_pint = ureg.Quantity(values, ureg(clean_units(units_in)))
    if units_scalef is not None:
        values_in_pint *= ureg(clean_units(units_scalef))
    values_out_pint = values_in_pint.to(clean_units(units_out))
    return values_out_pint.magnitude


def conv_units(da, units_out, units_scalef=None):
    """
    return a copy of da, with units converted to units_out
    """
    # use apply_ufunc to preserve dask-ness of da
    func = lambda values: conv_units_np(
        values, da.attrs["units"], units_out, units_scalef
    )
    da_out = xr.apply_ufunc(
        func, da, keep_attrs=True, dask="parallelized", output_dtypes=[da.dtype]
    )
    da_out.attrs["units"] = units_out
    da_out.encoding = da.encoding
    return da_out
