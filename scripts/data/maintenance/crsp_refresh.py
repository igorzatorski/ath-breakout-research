"""Shared automatic CRSP coverage check for public commands."""
import argparse

from scripts.data.maintenance.update_data_layer import refresh


def refresh_before_run(arguments=None):
    arguments = list(arguments or [])
    if "--help" in arguments or "-h" in arguments:
        return arguments
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--wrds-username")
    parser.add_argument("--skip-crsp-check", action="store_true")
    options, remaining = parser.parse_known_args(arguments)
    if options.skip_crsp_check:
        print("CRSP online check explicitly skipped; using local data.")
    else:
        refresh(options.wrds_username)
    return remaining
