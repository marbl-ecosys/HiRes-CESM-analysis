# HiRes-CESM-analysis

This repository is building a set of tools for analyzing BGC output in a high-resolution POP run.

## For Developers

Please take advantage of the pre-commit package to ensure that `black` is run before commiting:

```
pre-commit install --install-hooks
```

The pre-commit package is already installed via the `hires-marbl` conda environment.
There is a github action to run `black` on all pull requests,
but running it locally via-pre-commit will reduce the number of failed actions.
