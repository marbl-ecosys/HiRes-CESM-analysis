
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/marbl-ecosys/HiRes-CESM-analysis/Continuous%20Integration?label=CI&logo=github&style=for-the-badge)](https://github.com/marbl-ecosys/HiRes-CESM-analysis/actions?query=workflow%3A%22Continuous+Integration%22)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/marbl-ecosys/HiRes-CESM-analysis/Run%20all%20pre-commit%20checks%20one%20more%20time?label=code-style&style=for-the-badge)](https://github.com/marbl-ecosys/HiRes-CESM-analysis/actions?query=workflow%3A%22Run+all+pre-commit+checks+one+more+time%22)

# HiRes-CESM Analysis

- [HiRes-CESM Analysis](#hires-cesm-analysis)
  - [For Developers](#for-developers)
    - [Keep your conda environment up to date](#keep-your-conda-environment-up-to-date)
    - [Use `pre-commit` to test code before commiting](#use-pre-commit-to-test-code-before-commiting)
    - [Run `pytest` after modifying python in `utils/`](#run-pytest-after-modifying-python-in-utils)

This repository is building a set of tools for analyzing BGC output in a high-resolution POP run.

## For Developers

A few recommended practices to incorporate in your development sandbox:

### Keep your conda environment up to date

The first time you check out this repository, run

```
$ conda env install -f environments/environment.yaml
```

If you notice the YAML file has changed after you fetch changes from github,
update the environment with

```
$ conda env update -f environments/environment.yaml
```

If the `env update` command fails, you can remove the environment and re-create it:

```
$ conda env remove --name hires-marbl
$ conda env create -f environments/environment.yaml
```

### Use `pre-commit` to test code before commiting

Please take advantage of the pre-commit package to ensure that `black` is run before commiting:

```
$ pre-commit install --install-hooks # set up pre-commit
$ pre-commit run -a                  # check all the files currently in the repo
```

The pre-commit package is already installed via the `hires-marbl` conda environment.
There is a github action to run these checks on all pull requests,
but running them locally via-pre-commit will reduce the number of failed actions.
NOTE: for some reason, to properly install `pre-commit` on the CISL systems,
the above command must be run from `casper` rather than `cheyenne`.

Note that pre-commit creates a virtual environment using specific tags of each package.
As newer versions of `black` become available on `conda-forge`, we will update the pre-commit environment.

### Run `pytest` after modifying python in `utils/`

To test some of the python code in `notebooks/utils/`, run `pytest`.
These tests can be run from the top level of this repository by running

```
$ pytest tests/
```

If you add new code to this directory,
consider writing small tests to ensure it is running as expected.
