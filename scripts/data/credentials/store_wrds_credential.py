"""Store a WRDS password in the operating system credential manager."""

import argparse
from getpass import getpass

from ath_breakout.data.wrds_credentials import store_wrds_password


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Store a WRDS password in Windows Credential Manager."
    )
    parser.add_argument("--username", required=True, help="WRDS username.")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    password = getpass("WRDS password: ")
    confirmation = getpass("Repeat WRDS password: ")
    if password != confirmation:
        raise SystemExit("Passwords did not match; nothing was stored.")

    store_wrds_password(arguments.username, password)
    print("Success: the WRDS credential was stored by Windows Credential Manager.")


if __name__ == "__main__":
    main()
