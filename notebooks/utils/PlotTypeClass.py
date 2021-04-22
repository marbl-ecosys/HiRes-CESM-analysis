import json
import os
import pathlib


class _PlotTypeBaseClass(object):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("This must be implemented in child class")

    def get_filepaths(self, *args, **kwargs):
        raise NotImplementedError("This must be implemented in child class")

    def get_isel_str(self, da, isel_dict):
        """
            If diag metadata passes isel_dict option, we need that reflected in file name.

            This subroutine produces an additional string of the form var1_val1.var2_val2...,
            where isel_dict is equivalent to da.sel(var1=val1,var2=val2). Note the switch
            from .isel to .sel -- val1 should be da.var1[isel_dict[var1]] (the true value,
            rather than the index)
        """
        # Return empty string if isel_dict is empty dictionary
        isel_list = []
        for varname in isel_dict:
            value = da[varname].data
            try:
                # Use two digits after decimal for floats
                isel_list.append(f"{varname}--{value:.2f}")
            except:
                # Otherwise just include the variable value (e.g. strings)
                isel_list.append(f"{varname}--{value}")
        isel_str = "__".join(isel_list)
        if len(isel_str) > 0:
            isel_str = "." + isel_str
        return isel_str

    def savefig(self, fig, root_dir="images", **kwargs):
        """
            Saves fig as a PNG, with the file name determined by the other parameters.

            Also writes metadata about image file to a JSON file
        """

        # Always use tight_layout
        fig.tight_layout()

        # Remove trailing slash from root_dir
        if root_dir[-1] == "/":
            root_dir = root_dir[:-1]

        # Set up dictionary for metadata
        metadata = self.metadata
        filepath, jsonpath = self.get_filepaths()
        metadata["filepath"] = os.path.join(
            self.metadata["plot_type"], f"{filepath}.png"
        )
        filepath = os.path.join(
            root_dir, self.metadata["casename"], metadata["filepath"]
        )
        jsonpath = os.path.join(
            root_dir,
            self.metadata["casename"],
            self.metadata["plot_type"],
            f"{jsonpath}.json",
        )

        for path in [filepath, jsonpath]:
            parent_dir = pathlib.Path(path).parent
            parent_dir.mkdir(parents=True, exist_ok=True)

        fig.savefig(filepath, **kwargs)
        with open(jsonpath, "w") as fp:
            json.dump(metadata, fp)


################################################################################


class SummaryMapClass(_PlotTypeBaseClass):
    def __init__(self, da, casename, datestamp, apply_log10, isel_dict):
        self.metadata = dict()
        self.metadata["plot_type"] = "summary_map"
        self.metadata["varname"] = da.name
        self.metadata["casename"] = casename
        self.metadata["date"] = datestamp
        self.metadata["apply_log10"] = apply_log10
        self.metadata["sel_dict"] = dict()
        for varname in isel_dict:
            value = da[varname].data
            try:
                # Use two digits after decimal for floats
                str_val = f"{value:.2f}"
            except:
                # Otherwise just include the variable value (e.g. strings)
                str_val = f"{value}"
            self.metadata["sel_dict"][varname] = str_val
        self.isel_str = self.get_isel_str(da, isel_dict)

    def get_filepaths(self):
        log_str = "" if not self.metadata["apply_log10"] else ".log10"
        file_prefix = f"{self.metadata['varname']}.{self.metadata['date']}{self.isel_str}{log_str}"
        filepath = file_prefix
        jsonpath = os.path.join("metadata", file_prefix)

        return filepath, jsonpath


################################################################################


class SummaryTSClass(_PlotTypeBaseClass):
    def __init__(self, da, casename, start_date, end_date, isel_dict):
        self.metadata = dict()
        self.metadata["plot_type"] = "time_series"
        self.metadata["varname"] = da.name
        self.metadata["casename"] = casename
        self.metadata["time_period"] = f"{start_date}_{end_date}"
        self.metadata["sel_dict"] = dict()
        for varname in isel_dict:
            value = da[varname].data
            try:
                # Use two digits after decimal for floats
                str_val = f"{value:.2f}"
            except:
                # Otherwise just include the variable value (e.g. strings)
                str_val = f"{value}"
            self.metadata["sel_dict"][varname] = str_val
        self.isel_str = self.get_isel_str(da, isel_dict)

    def get_filepaths(self):
        file_prefix = (
            f"{self.metadata['varname']}.{self.metadata['time_period']}{self.isel_str}"
        )
        filepath = file_prefix
        jsonpath = os.path.join("metadata", file_prefix)

        return filepath, jsonpath


################################################################################


class SummaryHistClass(_PlotTypeBaseClass):
    def __init__(self, da, casename, apply_log10, start_date, end_date, isel_dict):
        self.metadata = dict()
        self.metadata["plot_type"] = "histogram"
        self.metadata["varname"] = da.name
        self.metadata["casename"] = casename
        self.metadata["apply_log10"] = apply_log10
        self.metadata["time_period"] = f"{start_date}_{end_date}"
        self.metadata["sel_dict"] = dict()
        for varname in isel_dict:
            value = da[varname].data
            try:
                # Use two digits after decimal for floats
                str_val = f"{value:.2f}"
            except:
                # Otherwise just include the variable value (e.g. strings)
                str_val = f"{value}"
            self.metadata["sel_dict"][varname] = str_val
        self.isel_str = self.get_isel_str(da, isel_dict)

    def get_filepaths(self):
        log_str = "" if not self.metadata["apply_log10"] else ".log10"
        file_prefix = f"{self.metadata['varname']}.{self.metadata['time_period']}{self.isel_str}{log_str}"
        filepath = file_prefix
        jsonpath = os.path.join("metadata", file_prefix)

        return filepath, jsonpath


################################################################################


class TrendMapClass(_PlotTypeBaseClass):
    def __init__(self, da, casename, start_date, end_date, isel_dict):
        self.metadata = dict()
        self.metadata["plot_type"] = "trend_map"
        self.metadata["varname"] = da.name
        self.metadata["casename"] = casename
        self.metadata["time_period"] = f"{start_date}_{end_date}"
        self.metadata["sel_dict"] = dict()
        for varname in isel_dict:
            value = da[varname].data
            try:
                # Use two digits after decimal for floats
                str_val = f"{value:.2f}"
            except:
                # Otherwise just include the variable value (e.g. strings)
                str_val = f"{value}"
            self.metadata["sel_dict"][varname] = str_val
        self.isel_str = self.get_isel_str(da, isel_dict)

    def get_filepaths(self):
        file_prefix = (
            f"{self.metadata['varname']}.{self.metadata['time_period']}{self.isel_str}"
        )
        filepath = os.path.join(file_prefix)
        jsonpath = os.path.join("metadata", file_prefix)

        return filepath, jsonpath


################################################################################


class TrendHistClass(_PlotTypeBaseClass):
    def __init__(self, da, casename, start_date, end_date, isel_dict):
        self.metadata = dict()
        self.metadata["plot_type"] = "trend_hist"
        self.metadata["varname"] = da.name
        self.metadata["casename"] = casename
        self.metadata["time_period"] = f"{start_date}_{end_date}"
        self.metadata["sel_dict"] = dict()
        for varname in isel_dict:
            value = da[varname].data
            try:
                # Use two digits after decimal for floats
                str_val = f"{value:.2f}"
            except:
                # Otherwise just include the variable value (e.g. strings)
                str_val = f"{value}"
            self.metadata["sel_dict"][varname] = str_val
        self.isel_str = self.get_isel_str(da, isel_dict)

    def get_filepaths(self):
        file_prefix = (
            f"{self.metadata['varname']}.{self.metadata['time_period']}{self.isel_str}"
        )
        filepath = os.path.join(file_prefix)
        jsonpath = os.path.join("metadata", file_prefix)

        return filepath, jsonpath
