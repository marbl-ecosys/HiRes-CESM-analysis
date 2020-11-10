"""
methods specific to CIME, but independent of models/components that are run with CIME
"""

import os
import subprocess


def cime_xmlquery(caseroot, varname):
    """run CIME's xmlquery for varname in the directory caseroot, return the value"""
    if os.path.isdir(caseroot):
        return subprocess.check_output(
            ["./xmlquery", "--value", varname], cwd=caseroot
        ).decode()
    else:
        return None
