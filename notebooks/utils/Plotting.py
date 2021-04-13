"""
    Tools to find and open files associated with the runs
"""

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import cftime
import datetime

# local modules, not available through __init__
from .utils import time_year_plus_frac, round_sig
from .utils_units import conv_units
from .PlotTypeClass import (
    SummaryMapClass,
    SummaryTSClass,
    SummaryHistClass,
    TrendMapClass,
    TrendHistClass,
)

################################################################################


def compare_fields_at_lat_lon(
    list_of_das_in, nlat, nlon, individual_plots=False, filename=None
):

    # This shouldn't be hard-coded... but how else to get?
    xticks = 365 + np.array([0, 31, 59, 90, 120, 151])
    xlabels = ["Jan 1", "Feb 1", "Mar 1", "Apr 1", "May 1", "June 1"]
    yticks = np.linspace(0, 17e4, 18)

    list_of_das = []
    for da in list_of_das_in:
        list_of_das.append(da.isel(nlat=nlat, nlon=nlon).compute())

    # Get longitude and latitude (hard-coded to assume we want W and S)
    long_west = 360 - list_of_das[0]["TLONG"].data
    lat_south = -list_of_das[0]["TLAT"].data

    if individual_plots:
        nrows = int(np.ceil(len(list_of_das) / 2))
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

    if filename:
        fig.savefig(filename)

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


def _extract_field_from_file(ds, varname, nlat, nlon):
    return ds[varname].isel(nlat=nlat, nlon=nlon).compute()


################################################################################


def summary_plot_global_ts(
    ds, da, diag_metadata, time_coarsen_len=None, **plot_options
):
    save_pngs = plot_options.get("save_pngs", False)
    if save_pngs:
        casename = plot_options["casename"]  # Required!
        root_dir = plot_options.get("root_dir", "images")
        kwargs = plot_options.get("savefig_kwargs", {})
        isel_dict = diag_metadata.get("isel_dict", {})

    reduce_dims = da.dims[-2:]
    weights = ds["TAREA"].fillna(0)
    da_weighted = da.weighted(weights)
    spatial_op = diag_metadata.get("spatial_op", "average")
    if spatial_op == "average":
        to_plot = da_weighted.mean(dim=reduce_dims)
        to_plot.attrs = da.attrs
        if "display_units" in diag_metadata:
            to_plot = conv_units(to_plot, diag_metadata["display_units"])
    if spatial_op == "integrate":
        to_plot = da_weighted.sum(dim=reduce_dims)
        to_plot.attrs = da.attrs
        to_plot.attrs["units"] += f" {weights.attrs['units']}"
        if "integral_display_units" in diag_metadata:
            to_plot = conv_units(
                to_plot,
                diag_metadata["integral_display_units"],
                units_scalef=diag_metadata.get("integral_unit_conv"),
            )
    # do not use to_plot.plot.line("-o") because of incorrect time axis values
    # https://github.com/pydata/xarray/issues/4401
    fig, ax = plt.subplots()
    ax.plot(time_year_plus_frac(to_plot, "time"), to_plot.values, "-o")
    ax.set_xlabel(xr.plot.utils.label_from_attrs(to_plot["time"]))
    ax.set_ylabel(xr.plot.utils.label_from_attrs(to_plot))
    ax.set_title(to_plot._title_for_slice())
    if time_coarsen_len is not None:
        tlen = len(to_plot.time)
        tlen_trunc = (tlen // time_coarsen_len) * time_coarsen_len
        to_plot_trunc = to_plot.isel(time=slice(0, tlen_trunc))
        to_plot_coarse = to_plot_trunc.coarsen({"time": time_coarsen_len}).mean()
        ax.plot(
            time_year_plus_frac(to_plot_coarse, "time"), to_plot_coarse.values, "-o"
        )
        title = ax.get_title()
        if title != "":
            title += ", "
        title += f"last mean value={round_sig(to_plot_coarse.values[-1],4)}"
        ax.set_title(title)
    if save_pngs:
        str_datestamp = f'{ds["time_bound"].load().data[0,0]}'
        first_datestamp = str_datestamp.split(" ")[0]
        str_datestamp = f'{ds["time_bound"].data[-1,-1]-datetime.timedelta(days=1)}'
        last_datestamp = str_datestamp.split(" ")[0]
        summary_ts = SummaryTSClass(
            da, casename, first_datestamp, last_datestamp, isel_dict
        )
        summary_ts.savefig(fig, root_dir=root_dir, **kwargs)
    else:
        plt.show()
    plt.close(fig)


################################################################################


def summary_plot_histogram(ds, da, diag_metadata, lines_per_plot=12, **plot_options):
    save_pngs = plot_options.get("save_pngs", False)
    if save_pngs:
        casename = plot_options["casename"]  # Required!
        root_dir = plot_options.get("root_dir", "images")
        kwargs = plot_options.get("savefig_kwargs", {})
        isel_dict = diag_metadata.get("isel_dict", {})

    # histogram, all time levels in one plot
    hist_bins = 20
    hist_log = True

    # Loop length
    t_cnt = len(da["time"])
    for apply_log10 in _apply_log10_vals(diag_metadata):
        t_ind_beg = 0
        fig, ax = plt.subplots()
        # fig.tight_layout()
        for t_ind in range(t_cnt):
            to_plot = da.isel(time=t_ind)
            if "display_units" in diag_metadata:
                to_plot = conv_units(to_plot, diag_metadata["display_units"])
            if apply_log10:
                to_plot = np.log10(xr.where(to_plot > 0, to_plot, np.nan))
                to_plot.name = f"log10({to_plot.name})"
            # to_plot.plot.hist(bins=hist_bins, log=hist_log, histtype="step")
            to_plot.plot.hist(ax=ax, bins=hist_bins, log=hist_log, histtype="step")
            if t_ind % lines_per_plot == lines_per_plot - 1:
                t_beg = ds.time_bound.values[t_ind_beg, 0]
                t_str_beg = f"{t_beg.year:04}-{t_beg.month:02}-{t_beg.day:02}"
                t_ind_end = t_ind
                t_end = ds.time_bound.values[t_ind_end, -1] - datetime.timedelta(days=1)
                t_str_end = f"{t_end.year:04}-{t_end.month:02}-{t_end.day:02}"
                plt.title(f"Histogram: {t_str_beg} : {t_str_end}")
                t_ind_beg = t_ind_end + 1
                if save_pngs:
                    summary_hist = SummaryHistClass(
                        da, casename, apply_log10, t_str_beg, t_str_end, isel_dict
                    )
                    summary_hist.savefig(fig, root_dir=root_dir, **kwargs)
                else:
                    plt.show()
                plt.close(fig)
                if t_ind != t_cnt - 1:
                    fig, ax = plt.subplots()

        if t_ind % lines_per_plot != lines_per_plot - 1:
            t_beg = ds.time_bound.values[t_ind_beg, 0]
            t_str_beg = f"{t_beg.year:04}-{t_beg.month:02}-{t_beg.day:02}"
            t_ind_end = t_ind
            t_end = ds.time_bound.values[t_ind_end, -1] - datetime.timedelta(days=1)
            t_str_end = f"{t_end.year:04}-{t_end.month:02}-{t_end.day:02}"
            plt.title(f"Histogram: {t_str_beg} : {t_str_end}")
            if save_pngs:
                summary_hist = SummaryHistClass(
                    da, casename, t_str_beg, t_str_end, isel_dict
                )
                summary_hist.savefig(fig, root_dir=root_dir, **kwargs)
            else:
                plt.show()
            plt.close(fig)


################################################################################


def summary_plot_maps(da, diag_metadata, **plot_options):

    save_pngs = plot_options.get("save_pngs", False)
    if save_pngs:
        casename = plot_options["casename"]  # Required!
        root_dir = plot_options.get("root_dir", "images")
        isel_dict = diag_metadata.get("isel_dict", {})

    # maps, 1 plots for time level
    cmap = "plasma"

    for apply_log10 in _apply_log10_vals(diag_metadata):
        vmin = diag_metadata.get("map_vmin")
        vmax = diag_metadata.get("map_vmax")
        if apply_log10:
            if vmin is not None:
                vmin = np.log10(vmin) if vmin > 0.0 else None
            if vmax is not None:
                vmax = np.log10(vmax) if vmax > 0.0 else None
        for t_ind in range(len(da["time"])):
            to_plot = da.isel(time=t_ind)
            if "display_units" in diag_metadata:
                to_plot = conv_units(to_plot, diag_metadata["display_units"])
            if apply_log10:
                to_plot = np.log10(xr.where(to_plot > 0.0, to_plot, np.nan))
                to_plot.name = f"log10({to_plot.name})"

            ax = to_plot.plot(cmap=cmap, vmin=vmin, vmax=vmax)
            fig = ax.get_figure()
            if save_pngs:
                datestamp = f"{da.time[t_ind].data.item()}".split(" ")[0]
                summary_map = SummaryMapClass(
                    da, casename, datestamp, apply_log10, isel_dict
                )
                summary_map.savefig(fig, root_dir=root_dir)
            else:
                plt.show()
            plt.close(fig)


################################################################################


def trend_plot(ds, da, vmin=None, vmax=None, invert_yaxis=False, **plot_options):

    save_pngs = plot_options.get("save_pngs", False)
    if save_pngs:
        casename = plot_options["casename"]  # Required!
        root_dir = plot_options.get("root_dir", "images")
        isel_dict = plot_options.get("isel_dict", {})
        t_beg = ds.time_bound.values[0, 0]
        t_str_beg = f"{t_beg.year:04}-{t_beg.month:02}-{t_beg.day:02}"
        t_end = ds.time_bound.values[-1, -1] - datetime.timedelta(days=1)
        t_str_end = f"{t_end.year:04}-{t_end.month:02}-{t_end.day:02}"

    trend = da.polyfit("time", 1).polyfit_coefficients.sel(degree=1)
    trend.name = da.name + " Trend"
    trend.attrs["long_name"] = da.attrs["long_name"] + " Trend"
    nsec_per_yr = 1.0e9 * 86400 * 365
    trend = nsec_per_yr * trend
    trend.attrs["units"] = da.attrs["units"] + "/yr"
    trend.load()

    fig, ax = plt.subplots()
    trend.plot.hist(bins=20, log=True, ax=ax)
    plt.title(da._title_for_slice())
    if save_pngs:
        trend_hist = TrendHistClass(da, casename, t_str_beg, t_str_end, isel_dict)
        trend_hist.savefig(fig, root_dir=root_dir)
    else:
        plt.show()
    plt.close(fig)

    fig, ax = plt.subplots()
    trend.plot.pcolormesh(cmap="plasma", vmin=vmin, vmax=vmax, ax=ax)
    plt.title(da._title_for_slice())
    if invert_yaxis:
        ax.invert_yaxis()
    if save_pngs:
        trend_map = TrendMapClass(da, casename, t_str_beg, t_str_end, isel_dict)
        trend_map.savefig(fig, root_dir=root_dir)
    else:
        plt.show()
    plt.close(fig)


################################################################################


def _apply_log10_vals(diag_metadata):
    if diag_metadata.get("apply_log10", False):
        return [False, True]
    else:
        return [False]


################################################################################
