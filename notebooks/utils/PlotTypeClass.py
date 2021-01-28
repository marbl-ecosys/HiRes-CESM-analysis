import json
import os
import pathlib


class _PlotTypeBaseClass(object):
    def __init__(self):
        raise NotImplementedError("This must be implemented in child class")

    def get_filepaths(self):
        raise NotImplementedError("This must be implemented in child class")

    def savefig(self, fig, root_dir="images"):
        """
            Saves fig as a PNG, with the file name determined by the other parameters.

            Also writes metadata about image file to a JSON file
        """

        # Remove trailing slash from root_dir
        if root_dir[-1] == "/":
            root_dir = root_dir[:-1]

        # Set up dictionary for metadata
        metadata = self.metadata
        filepath, jsonpath = self.get_filepaths()
        metadata["filepath"] = os.path.join(
            root_dir, self.metadata["plot_type"], f"{filepath}.png"
        )
        jsonpath = os.path.join(
            root_dir, self.metadata["plot_type"], f"{jsonpath}.json"
        )

        for path in [metadata["filepath"], jsonpath]:
            parent_dir = pathlib.Path(path).parent
            parent_dir.mkdir(parents=True, exist_ok=True)

        fig.savefig(metadata["filepath"])
        with open(jsonpath, "w") as fp:
            json.dump(metadata, fp)


################################################################################


class SummaryMapClass(_PlotTypeBaseClass):
    def __init__(self, varname, casename, datestamp, apply_log10):
        self.metadata = dict()
        self.metadata["plot_type"] = "summary_map"
        self.metadata["varname"] = varname
        self.metadata["casename"] = casename
        self.metadata["date"] = datestamp
        self.metadata["apply_log10"] = apply_log10

    def get_filepaths(self):
        log_str = "" if not self.metadata["apply_log10"] else ".log10"
        file_prefix = f"{self.metadata['varname']}.{self.metadata['date']}{log_str}"
        filepath = os.path.join(self.metadata["casename"], file_prefix)
        jsonpath = os.path.join(self.metadata["casename"], "metadata", file_prefix)

        return filepath, jsonpath


################################################################################


class SummaryTSClass(_PlotTypeBaseClass):
    def __init__(self, varname, casename, start_date, end_date):
        self.metadata = dict()
        self.metadata["plot_type"] = "time_series"
        self.metadata["varname"] = varname
        self.metadata["casename"] = casename
        self.metadata["time_period"] = f"{start_date}_{end_date}"

    def get_filepaths(self):
        file_prefix = f"{self.metadata['varname']}.{self.metadata['time_period']}"
        filepath = os.path.join(self.metadata["casename"], file_prefix)
        jsonpath = os.path.join(self.metadata["casename"], "metadata", file_prefix)

        return filepath, jsonpath
