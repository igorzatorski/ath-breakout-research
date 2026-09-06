"""Compatibility entry point; implementation lives in scripts/internal."""
from scripts.internal.build_crsp_strategy_history import *  # noqa: F401,F403

if __name__ == "__main__":
    from scripts.internal.build_crsp_strategy_history import main
    main()
