"""
    Tools to find and open files associated with the runs
"""

import os
import xarray as xr

################################################################################

def get_pop_daily_ds(casenames, start_date='0001-01', end_date=None, verbose=False):
    """
        Return an xarray dataset containing pop daily history files
    """
    files = _get_pop_history_files(casenames, 'pop.h.nday1', start_date, end_date, 'YYYY-MM-01', verbose)
    if verbose:
      print('Opening xarray datasets...')
    ds = xr.open_mfdataset(files, combine='nested', concat_dim='time', decode_times=False)
    print(f'Datasets contain a total of {ds.sizes["time"]} days')
    print(f'Last daily average written at midnight on {xr.decode_cf(ds)["time"].data[-1].strftime(format="%b %d")}')
    return ds

################################################################################

def _get_rundir(casename):
    return os.path.join(os.sep, 'glade', 'scratch', 'mlevy', casename, 'run')

################################################################################

def _get_archive_pophist_dir(casename):
    return os.path.join(os.sep, 'glade', 'scratch', 'mlevy', 'archive', casename, 'ocn', 'hist')

################################################################################

def _get_archive_log_dir(casename):
    return os.path.join(os.sep, 'glade', 'scratch', 'mlevy', 'archive', casename, 'logs', 'hist')

################################################################################

def _get_pop_history_files(casenames, stream, start_date, end_date, date_template, verbose=False):
    if type(casenames) == str:
        casenames = [casenames]
    if type(casenames) != list:
        raise ValueError(f'{casenames} is not a string or list')

    files = []
    found = []
    keep_going = True

    dates = start_date.split('-')
    year = int(dates[0])
    month = int(dates[1])

    while keep_going:
        found.append(False)
        date=f'{year:04}-{month:02}'
        if stream == 'pop.h.nday1':
            stream_and_date = f'{stream}.{date}-01'
        else:
            stream_and_date  = f'{stream}.{date}'
        for rootdir in [_get_archive_pophist_dir, _get_rundir]:
            for casename in casenames:
                file = os.path.join(rootdir(casename), f'{casename}.{stream_and_date}.nc')
                found[-1] = os.path.exists(file)
                if found[-1]:
                    if verbose:
                        print(file)
                    files.append(file)
                    break
            if found[-1]:
                break
        if date == end_date:
            break
        month += 1
        if month>12:
            year += 1
            month -= 12
        keep_going = found[-1]

    if verbose:
        print(f'No match for {date}')

    return files
