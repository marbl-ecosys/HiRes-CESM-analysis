"""
    Tools to find and open files associated with the runs
"""

import os
import xarray as xr

################################################################################

def get_pop_daily_ds(casenames, start_month=1, nmonths=5, verbose=False):
    """
        Return an xarray dataset containing pop daily history files
    """
    files = _get_daily_pop_files(casenames)
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

def _get_daily_pop_files(casenames, start_month=1, nmonths=5, verbose=False):
    if type(casenames) == str:
        casenames = [casenames]
    if type(casenames) != list:
        raise ValueError(f'{casenames} is not a string or list')

    files = []
    found = []
    for month in range(start_month, start_month+nmonths):
        found.append(False)
        date=f'0001-0{month}-01'
        for rootdir in [_get_archive_pophist_dir, _get_rundir]:
            for casename in casenames:
                file = os.path.join(rootdir(casename), f'{casename}.pop.h.nday1.{date}.nc')
                found[-1] = os.path.exists(file)
                if found[-1]:
                    if verbose:
                        print(file)
                    files.append(file)
                    break
            if found[-1]:
                break
        if not found[-1] and verbose:
            print(f'No match for {date}')

    return files

