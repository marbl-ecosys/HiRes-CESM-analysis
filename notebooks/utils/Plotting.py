"""
    Tools to find and open files associated with the runs
"""

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import cftime

import utils

################################################################################


def compare_fields_at_lat_lon(
    list_of_cases, varname, stream, nlat, nlon, individual_plots=False
):
    _check_for_var_in_case(list_of_cases, varname, stream)

    list_of_das = []
    for case in list_of_cases:
        list_of_das.append(
            _extract_field_from_file(case.history_contents[stream], varname, nlat, nlon)
        )

    # This shouldn't be hard-coded... but how else to get?
    xticks = 365 + np.array([0, 31, 59, 90, 120, 151])
    xlabels = ["Jan 1", "Feb 1", "Mar 1", "Apr 1", "May 1", "June 1"]
    yticks = np.linspace(0, 17e4, 18)

    # Get longitude and latitude (hard-coded to assume we want W and S)
    long_west = 360 - list_of_das[0]["TLONG"].data
    lat_south = -list_of_das[0]["TLAT"].data

    if individual_plots:
        nrows = int(np.ceil(len(list_of_cases) / 2))
        fig, axes = plt.subplots(
            nrows=nrows, ncols=2, figsize=(9 * nrows, 10.5), sharex=True
        )

        # Hard-coded title is also a bad idea
        fig.suptitle(f"Mix Layer Depth at ({long_west:.2f} W, {lat_south:.2f} S)")

        for n, da in enumerate(list_of_das):
            plt.subplot(nrows, 2, n + 1)
            da.plot()
            plt.title(f"Run {(n+1):03}")
            #             plt.xlim((np.min(xticks), np.max(xticks)))
            #             plt.xticks(xticks, xlabels)

            # Only label yticks on left-most column
            if n % 2 == 0:
                plt.yticks(yticks)
            else:
                plt.yticks(yticks, "")
                plt.ylabel("")

            # Only add xlabel on last row
            if (n + 1) / 2 == nrows:
                plt.xlabel("Date (year 0001)")
            else:
                plt.xlabel("")
    else:
        fig = plt.figure(figsize=(9.0, 5.25), clear=True)
        fig.suptitle(f"Mix Layer Depth at ({long_west:.2f} W, {lat_south:.2f} S)")

        for da in list_of_das:
            da.plot()
        plt.title("All 4 runs overlay")
        #         plt.xlim((np.min(xticks), np.max(xticks)))
        #         plt.xticks(xticks, xlabels)
        plt.yticks(yticks)
        plt.xlabel("Date (year 0001)")

    return fig


################################################################################


def plot_dict_with_date_keys(dict_in, title, legend=None):
    """
        Assume that keys of dict_in are 'YYYYMMDD' and values are numeric
    """
    time_units = "days since 0001-01-01 0:00:00"
    time = []
    array_val = []
    for date in dict_in.keys():
        if "log" not in date:
            (year, month, day) = date.split("-")
            time.append(cftime.DatetimeNoLeap(int(year), int(month), int(day)))
            array_val.append(dict_in[date])

    if type(array_val[0]) == list:
        dim2 = len(array_val[0])
        da = xr.DataArray(array_val, dims=["time", "dim2"])
    else:
        dim2 = None
        da = xr.DataArray(array_val, dims="time")
    da["time"] = time

    fig = plt.figure(figsize=(9.0, 5.25), clear=True)
    if dim2:
        for dim2ind in range(dim2):
            da.isel(dim2=dim2ind).plot()
    else:
        da.plot()
    if legend:
        plt.legend(legend)
    plt.title(title)
    plt.show()


#     return fig

################################################################################


def _check_for_var_in_case(list_of_cases, varname, stream):
    for case in list_of_cases:
        if varname not in case.history_contents[stream]:
            raise ValueError(f"Not all datasets contain {varname}")


################################################################################


def _extract_field_from_file(ds, varname, nlat, nlon):
    return ds[varname].isel(nlat=nlat, nlon=nlon).compute()


################################################################################


def summary_plot_global_ts(ds, da, var_metadata):
    reduce_dims = ["nlat", "nlon"]
    weights = ds["TAREA"].fillna(0)
    da_weighted = da.weighted(weights)
    spatial_op = var_metadata.get("spatial_op", "average")
    if spatial_op == "average":
        to_plot = da_weighted.mean(dim=reduce_dims)
        to_plot.attrs = da.attrs
        if "display_units" in var_metadata:
            to_plot = utils.conv_units(to_plot, var_metadata["display_units"])
    if spatial_op == "integrate":
        to_plot = da_weighted.sum(dim=reduce_dims)
        to_plot.attrs = da.attrs
        to_plot.attrs["units"] += f" {weights.attrs['units']}"
        if "integral_display_units" in var_metadata:
            to_plot = utils.conv_units(
                to_plot,
                var_metadata["integral_display_units"],
                units_scalef=var_metadata.get("integral_unit_conv"),
            )
    to_plot.plot.line("-o")
    plt.show()


################################################################################


def _apply_log10_vals(var_metadata):
    if var_metadata.get("apply_log10", False):
        return [False, True]
    else:
        return [False]


################################################################################


def summary_plot_histogram(da, var_metadata):
    # histogram, all time levels in one plot
    hist_bins = 20
    hist_log = True

    for apply_log10 in _apply_log10_vals(var_metadata):
        for t_ind in range(len(da["time"])):
            to_plot = da.isel(time=t_ind)
            if "display_units" in var_metadata:
                to_plot = utils.conv_units(to_plot, var_metadata["display_units"])
            if apply_log10:
                to_plot = np.log10(xr.where(to_plot > 0, to_plot, np.nan))
                to_plot.name = f"log10({to_plot.name})"
            to_plot.plot.hist(bins=hist_bins, log=hist_log, histtype="step")
        plt.show()


################################################################################


def summary_plot_maps(da, var_metadata):
    # maps, 1 plots for time level
    cmap = "plasma"

    for apply_log10 in _apply_log10_vals(var_metadata):
        vmin = var_metadata.get("map_vmin")
        vmax = var_metadata.get("map_vmax")
        if apply_log10:
            if vmin is not None:
                vmin = np.log10(vmin) if vmin > 0.0 else None
            if vmax is not None:
                vmax = np.log10(vmax) if vmax > 0.0 else None
        for t_ind in range(len(da["time"])):
            to_plot = da.isel(time=t_ind)
            if "display_units" in var_metadata:
                to_plot = utils.conv_units(to_plot, var_metadata["display_units"])
            if apply_log10:
                to_plot = np.log10(xr.where(to_plot > 0.0, to_plot, np.nan))
                to_plot.name = f"log10({to_plot.name})"

            to_plot.plot(cmap=cmap, vmin=vmin, vmax=vmax)
            plt.show()


################################################################################
