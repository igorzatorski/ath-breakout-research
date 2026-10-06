"""Delete a WRDS password from the operating system credential manager."""

import argparse

from ath_breakout.data.wrds_credentials import delete_wrds_password


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete a stored WRDS password from Windows Credential Manager."
    )
    parser.add_argument("--username", required=True, help="WRDS username.")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    deleted = delete_wrds_password(arguments.username)
    if deleted:
        print("Success: the stored WRDS credential was deleted.")
    else:
        print("No stored WRDS credential was found.")


if __name__ == "__main__":
    main()
