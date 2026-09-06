"""Compatibility entry point; implementation lives in scripts/internal."""
from scripts.internal.build_wrds_crsp_universe_history import *  # noqa: F401,F403

if __name__ == "__main__":
    from scripts.internal.build_wrds_crsp_universe_history import main
    main()
