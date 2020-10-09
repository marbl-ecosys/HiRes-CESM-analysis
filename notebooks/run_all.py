#!/usr/bin/env python
"""
    This script is intended for developers to rerun all dask-free notebooks without
    launching JupyterHub or a jupyter lab session.
    It relies on the run_notebooks function.
"""

import os

notebooks = []
# Sanity Check
notebooks.append("Sanity\ Check.ipynb")

# Notebooks that act on range of years
for case in range(3, 5):
    # For now, plot_suite and trend_maps don't run with nbconvert
    # It may be NCAR_jobqueue related...
    notebooks.append(f"compare_ts_and_hist_{case:03}.ipynb")

# per-year notebooks
for case in range(3, 5):
    for year in range(1, 62):
        notebook = f"plot_suite_maps_{year:04}_{case:03}.ipynb"
        if not os.path.isfile(notebook):
            continue
        notebooks.append(notebook)

cmd = "./run_notebooks.sh " + " ".join(notebooks)
os.system(cmd)
