"""Store WRDS credentials in the operating system credential manager."""

WRDS_CREDENTIAL_SERVICE = "ath-breakout-systematic.wrds"


def load_wrds_password(username: str) -> str | None:
    """Return a WRDS password from the system credential manager, if present."""
    import keyring

    return keyring.get_password(WRDS_CREDENTIAL_SERVICE, username)


def store_wrds_password(username: str, password: str) -> None:
    """Save a WRDS password in the system credential manager."""
    if not username:
        raise ValueError("A WRDS username is required")
    if not password:
        raise ValueError("A WRDS password is required")

    import keyring

    keyring.set_password(WRDS_CREDENTIAL_SERVICE, username, password)


def delete_wrds_password(username: str) -> bool:
    """Delete a stored WRDS password and report whether one existed."""
    import keyring

    if keyring.get_password(WRDS_CREDENTIAL_SERVICE, username) is None:
        return False
    keyring.delete_password(WRDS_CREDENTIAL_SERVICE, username)
    return True
