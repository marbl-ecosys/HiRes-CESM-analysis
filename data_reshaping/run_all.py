#!/usr/bin/env python
import os


def _parse_args():
    """ Parse command line arguments """

    import argparse

    parser = argparse.ArgumentParser(
        description="Submit scripts to reshape highres BGC output",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Required: specify year
    parser.add_argument(
        "-y",
        "--years",
        action="store",
        dest="years",
        type=int,
        required=True,
        nargs="+",
        help="Year of run to convert to time series",
    )

    # Optional: which case to convert
    parser.add_argument(
        "-c",
        "--case",
        action="store",
        dest="case",
        type=str,
        default="004",
        help="Suffix of case to convert to time series",
    )

    # Optional: specify which scripts to run
    parser.add_argument(
        "-s",
        "--scripts",
        action="store",
        dest="scripts",
        type=str,
        nargs="+",
        default=[
            "pop.h_t13.sh",
            "pop.h.nday1_t13.sh",
            "cice.h_t13.sh",
            "pop.h.nyear1_t13.sh",
            "cice.h1_t13.sh",
        ],
        help="Scripts to submit to slurm",
    )

    # Optional: is this a dry-run? If so, don't submit anything
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        dest="dryrun",
        help="If true, do not actually submit job",
    )

    # Optional: By default, slurm will email users when jobs start and finish
    parser.add_argument(
        "--no-mail",
        action="store_false",
        dest="send_mail",
        help="If true, send SLURM emails to {user}@ucar.edu",
    )

    return parser.parse_args()


###################

if __name__ == "__main__":
    args = _parse_args()
    case = args.case
    mail_opt = (
        f"--mail-type=ALL --mail-user={os.environ['USER']}@ucar.edu"
        if args.send_mail
        else "--mail-type=NONE"
    )

    for yr in args.years:
        year = f"{yr:04}"
        for script in args.scripts:
            print(f"Submitting {script} for year {year} of {case}...")
            cmd = f"sbatch {mail_opt} --dependency=singleton {script} {case} {year}"
            if not args.dryrun:
                # note: the --dependency=singleton option means only one job per job name
                #       Some jobs had been crashing, and I think it was due to temporary
                #       files clobbering each other? But only having one pop.h_t13.sh job
                #       at a time seems to have prevented these issues.
                os.system(cmd)
            else:
                print(f"Command to run: {cmd}")
