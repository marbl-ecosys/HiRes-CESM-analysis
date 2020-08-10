"""
    Tools to find and open files associated with the runs
"""

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import cftime

################################################################################

def compare_fields_at_lat_lon(list_of_cases, varname, stream, nlat, nlon, individual_plots=False):
    _check_for_var_in_case(list_of_cases, varname, stream)

    list_of_das = []
    for case in list_of_cases:
        list_of_das.append(_extract_field_from_file(case.history_contents[stream], varname, nlat, nlon))

    # This shouldn't be hard-coded... but how else to get?
    xticks = 365 + np.array([0, 31, 59, 90, 120, 151])
    xlabels = ['Jan 1', 'Feb 1', 'Mar 1', 'Apr 1', 'May 1', 'June 1']
    yticks=np.linspace(0, 17e4, 18)

    # Get longitude and latitude (hard-coded to assume we want W and S)
    long_west = 360 - list_of_das[0]['TLONG'].data
    lat_south = -list_of_das[0]['TLAT'].data

    if individual_plots:
        nrows = int(np.ceil(len(list_of_cases)/2))
        fig, axes = plt.subplots(nrows=nrows, ncols=2, figsize=(9*nrows, 10.5))

        # Hard-coded title is also a bad idea
        fig.suptitle(f'Mix Layer Depth at ({long_west:.2f} W, {lat_south:.2f} S)')

        for n, da in enumerate(list_of_das):
            plt.subplot(nrows, 2, n+1)
            da.plot()
            plt.title(f'Run {(n+1):03}')
            plt.xlim((np.min(xticks), np.max(xticks)))
            plt.xticks(xticks, xlabels)

            # Only label yticks on left-most column
            if n%2 == 0:
                plt.yticks(yticks)
            else:
                plt.yticks(yticks, '')
                plt.ylabel('')

            # Only add xlabel on last row
            if (n+1)/2 == nrows:
                plt.xlabel('Date (year 0001)')
            else:
                plt.xlabel('')
    else:
        fig = plt.figure(figsize=(9.0, 5.25))
        fig.suptitle(f'Mix Layer Depth at ({long_west:.2f} W, {lat_south:.2f} S)')

        for da in list_of_das:
            da.plot()
        plt.title('All 4 runs overlay')
        plt.xlim((np.min(xticks), np.max(xticks)))
        plt.xticks(xticks, xlabels)
        plt.yticks(yticks)
        plt.xlabel('Date (year 0001)')

    return fig

################################################################################

def plot_dict_with_date_keys(dict_in, title):
    """
        Assume that keys of dict_in are 'YYYYMMDD' and values are numeric
    """
    time_units = 'days since 0001-01-01 0:00:00'
    time = []
    array_val = []
    for date in dict_in.keys():
         if 'log' not in date:
            (year, month, day) = date.split('-')
            time.append(cftime.DatetimeNoLeap(int(year), int(month), int(day)))
            array_val.append(dict_in[date])

    da = xr.DataArray(array_val, dims='time')
    da['time'] = time
    da.plot()
    plt.title(title)

################################################################################

def _check_for_var_in_case(list_of_cases, varname, stream):
    for case in list_of_cases:
        if varname not in case.history_contents[stream]:
            raise ValueError(f"Not all datasets contain {varname}")

################################################################################

def _extract_field_from_file(ds, varname, nlat, nlon):
    return ds[varname].isel(nlat=nlat, nlon=nlon).compute()