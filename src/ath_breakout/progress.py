"""Consistent elapsed time and remaining-time estimates for bounded work stages."""
import time


def format_duration(seconds):
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes:02d}m {seconds:02d}s" if hours else f"{minutes}m {seconds:02d}s"


def timing_values(completed, total, started_at):
    elapsed = max(0, time.monotonic() - started_at) if started_at is not None else 0
    if total <= 0 or completed >= total:
        eta = 0
    elif completed > 0 and started_at is not None:
        eta = elapsed / completed * (total - completed)
    else:
        eta = None
    return {"elapsed": format_duration(elapsed),
            "eta": format_duration(eta) if eta is not None else "calculating",
            "total": format_duration(elapsed + eta) if eta is not None else "calculating"}


def timing_suffix(completed, total, started_at):
    values = timing_values(completed, total, started_at)
    return f"elapsed: {values['elapsed']:>12} | ETA: {values['eta']:>12} | total est.: {values['total']:>12}"
