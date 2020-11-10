#!/usr/bin/env python
"""
    This script is intended for developers to rerun all dask-free notebooks without
    launching JupyterHub or a jupyter lab session.
    It relies on the run_notebooks function.
"""

import os

# For now, plot_suite and trend_maps don't run with nbconvert
# It may be NCAR_jobqueue related...
notebooks = []
notebooks.append("Sanity\ Check.ipynb")
notebooks.append("Pull\ info\ from\ logs.ipynb")
notebooks.append(f"compare_ts_and_hist_*.ipynb")
notebooks.append(f"plot_suite_maps_*.ipynb")

cmd = "./run_notebooks.sh " + " ".join(notebooks)
os.system(cmd)
