"""
    Class to use to output (log and netCDF) from the runs
"""

import glob
import os
import gzip as gz
import numpy as np
import xarray as xr

################################################################################

class HiResRun(object):

    # Constructor
    def __init__(self, casenames, start_date='0001-01', end_date=None, verbose=False):
        if type(casenames) == str:
            casenames = [casenames]
        if type(casenames) != list:
            raise ValueError(f'{casenames} is not a string or list')
        self._casenames = casenames
        self._verbose = verbose

        self._log_filenames = self._find_log_files()
        self._history_filenames = self._find_hist_files(start_date, end_date)
        self.log_contents = dict()
        self.history_contents = dict()
        self._read_log('cesm')

    ############################################################################

    def get_co2calc_warning_cnt(self):
        self._read_log('cesm')

        warning_count = dict()
        for date in self.log_contents['cesm']:
            warning_count[date] = []
            for log in self.log_contents['cesm'][date]:
                warning_count[date].append(sum(['MARBL WARNING (marbl_co2calc_mod:drtsafe): (marbl_co2calc_mod:drtsafe) it' in entry for entry in self.log_contents['cesm'][date][log]])) 
        return warning_count

    ############################################################################

    def _find_log_files(self):
        """
            Look in rundir and archive for cesm.log, ocn.log, and cpl.log files
        """
        files = dict()
        for component in ['cesm', 'ocn', 'cpl']:
            files[component] = []
            for rootdir in [_get_archive_log_dir, _get_rundir]:
                for casename in self._casenames:
                    files[component] += glob.glob(os.path.join(rootdir(casename), f'{component}.log.*'))
        return files

    ############################################################################

    def _find_hist_files(self, start_date, end_date):
        """
            Look in rundir and archive for pop history files
        """
        files = dict()
        found = dict()
        for stream in ['pop.h', 'pop.h.nday1']:
            files[stream] = []
            found[stream] = []
            keep_going = True

            dates = start_date.split('-')
            year = int(dates[0])
            month = int(dates[1])

            while keep_going:
                found[stream].append(False)
                date=f'{year:04}-{month:02}'
                if stream == 'pop.h.nday1':
                    stream_and_date = f'{stream}.{date}-01'
                else:
                    stream_and_date  = f'{stream}.{date}'
                for rootdir in [_get_archive_pophist_dir, _get_rundir]:
                    for casename in self._casenames:
                        file = os.path.join(rootdir(casename), f'{casename}.{stream_and_date}.nc')
                        found[stream][-1] = os.path.exists(file)
                        if found[stream][-1]:
                            if self._verbose:
                                print(file)
                            files[stream].append(file)
                            break
                    if found[stream][-1]:
                        break
                if date == end_date:
                    break
                month += 1
                if month>12:
                    year += 1
                    month -= 12
                keep_going = found[stream][-1]

            if self._verbose:
                print(f'No match for {date}')

        return files

    ############################################################################

    def _read_log(self, component):
        """
            Read all log files from specified component. Returns a dict where keys
            are dates and values are contents of log from that date; if multiple
            logs contain the same date, uses the most recent.
        """
        if component in self.log_contents:
            return
        if component not in self._log_filenames:
            raise ValueError(f'No known {component}.log files')

        datestamps = {'cesm' : 'model date =', 'cpl' : 'tStamp'}
        try:
            datestamp = datestamps[component]
        except:
            raise ValueError(f'Do not know how to find dates in {component}.log')

        all_dates = []
        contents = dict()
        for log in self._log_filenames[component]:
            # Open file
            is_gz = log.endswith('gz')
            if is_gz:
                local_open = gz.open
                mode = 'rt'
            else:
                local_open = open
                mode = 'r'
            with local_open(log, mode) as f:
                single_log_contents = f.readlines()

            # Look for datestamps in log; if none found, save contents as 'date_unknown'
            date_inds = np.where([datestamp in entry for entry in single_log_contents])[0]
            if len(date_inds) == 0:
                date = 'date_unknown'
                if date not in contents:
                    contents[date] = dict()
                contents[date][log] = single_log_contents
                continue

            # Set up list of dates and np array of indices
            dates_in_log = [entry.split(datestamp)[1].strip()[:8] for entry in np.array(single_log_contents)[date_inds].tolist()]
            # add first day of run to dates_in_log, and prepend 0 to date_inds
            date_inds = np.insert(date_inds, 0, 0)
            dates_in_log = _add_first_date(dates_in_log)

            # for each date, add contents to dictionary 
            for n, date in enumerate(dates_in_log[:-1]):
                if date not in contents:
                    contents[date] = dict()
                contents[date][log] = single_log_contents[date_inds[n]:date_inds[n+1]]

            #  Need to account for partial days from runs that die
            # e.g. model crashes midway through 00010104 => need an 00010105 stamp (since we're using datestamp from end of the day, e.g. midnight the next day)
            if not is_gz:
                date = dates_in_log[-1]
                if date not in contents:
                    contents[date] = dict()
                contents[date][log] = single_log_contents[date_inds[-1]:]

        self.log_contents[component] = contents

    ############################################################################
    
    def _read_history_files(self, stream):
        """
            Read all history files from a specified stream. Returns a dict where keys
            are stream names and values are xarray Datasets
        """
        if stream in self.history_contents:
            return
        if stream not in self._history_filenames:
            raise ValueError(f'No known {stream} files')

        self.history_contents[stream] = xr.open_mfdataset(self._history_filenames[stream], combine='nested', concat_dim='time', decode_times=False)
        print(f'Datasets contain a total of {self.history_contents[stream].sizes["time"]} days')
        print(f'Last daily average written at midnight on {xr.decode_cf(self.history_contents[stream])["time"].data[-1].strftime(format="%b %d")}')



################################################################################

#####################################
## HELPER FUNCTIONS                ##
## No need to be part of the class ##
#####################################

def _get_rundir(casename):
    return os.path.join(os.sep, 'glade', 'scratch', 'mlevy', casename, 'run')

################################################################################

def _get_archive_pophist_dir(casename):
    return os.path.join(os.sep, 'glade', 'scratch', 'mlevy', 'archive', casename, 'ocn', 'hist')

################################################################################

def _get_archive_log_dir(casename):
    return os.path.join(os.sep, 'glade', 'scratch', 'mlevy', 'archive', casename, 'logs')

################################################################################

def _add_first_date(date_list):
    year = int(date_list[0][:4])
    month = int(date_list[0][4:6])
    day = int(date_list[0][6:])
    if day > 1:
        first_date = f'{year:04}{month:02}{(day-1):02}'
    else:
        first_date = 'first'
    return [first_date] + date_list
