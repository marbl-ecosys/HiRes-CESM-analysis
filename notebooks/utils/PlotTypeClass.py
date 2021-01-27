import json
import os
import pathlib


class PlotTypeClass(object):
    def __init__(self):
        raise NotImplementedError("This must be implemented in child class")

    def get_filepath(self):
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
        filepath = self.get_filepath()
        metadata = self.metadata
        metadata["filepath"] = f"{filepath}.png"
        fullpath = os.path.join(
            root_dir, self.metadata["plot_type"], metadata["filepath"]
        )
        jsonpath = os.path.join(
            root_dir, self.metadata["plot_type"], "metadata", f"{filepath}.json"
        )

        for path in [fullpath, jsonpath]:
            parent_dir = pathlib.Path(path).parent
            parent_dir.mkdir(parents=True, exist_ok=True)

        fig.savefig(fullpath)
        with open(jsonpath, "w") as fp:
            json.dump(metadata, fp)


################################################################################


class SummaryMapClass(PlotTypeClass):
    def __init__(self, varname, datestamp, apply_log10):
        self.metadata = dict()
        self.metadata["plot_type"] = "summary_map"
        self.metadata["varname"] = varname
        self.metadata["date"] = datestamp
        self.metadata["apply_log10"] = apply_log10

    def get_filepath(self):
        log_str = "" if not self.metadata["apply_log10"] else ".log10"
        return f"{self.metadata['varname']}.{self.metadata['date']}{log_str}"
