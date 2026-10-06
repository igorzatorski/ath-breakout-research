"""Consistent elapsed time and remaining-time estimates for bounded work stages."""

import time
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


class DownloadProgress:
    """Animate downloads in a terminal; leave redirected logs to static progress."""

    def __init__(self, total, console=None):
        self.console = console or Console()
        self.animated = self.console.is_terminal and not self.console.is_dumb_terminal
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("{task.completed:.0f}/{task.total:.0f}"),
            TextColumn("elapsed"),
            TimeElapsedColumn(),
            TextColumn("ETA"),
            TimeRemainingColumn(),
            TextColumn("ok: {task.fields[successful]} failed: {task.fields[failed]}"),
            console=self.console,
            disable=not self.animated,
            refresh_per_second=8,
        )
        self.task = self.progress.add_task(
            "Yahoo download", total=total, successful=0, failed=0
        )

    def __enter__(self):
        if self.animated:
            self.progress.start()
        return self

    def update(self, completed, successful, failed, description="Yahoo download"):
        self.progress.update(
            self.task,
            completed=completed,
            successful=successful,
            failed=failed,
            description=description,
        )

    def __exit__(self, *exception):
        if self.animated:
            self.progress.stop()


def format_duration(seconds):
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return (
        f"{hours}h {minutes:02d}m {seconds:02d}s"
        if hours
        else f"{minutes}m {seconds:02d}s"
    )


def timing_values(completed, total, started_at):
    elapsed = max(0, time.monotonic() - started_at) if started_at is not None else 0
    if total <= 0 or completed >= total:
        eta = 0
    elif completed > 0 and started_at is not None:
        eta = elapsed / completed * (total - completed)
    else:
        eta = None
    return {
        "elapsed": format_duration(elapsed),
        "eta": format_duration(eta) if eta is not None else "calculating",
        "total": format_duration(elapsed + eta) if eta is not None else "calculating",
    }


def timing_suffix(completed, total, started_at):
    values = timing_values(completed, total, started_at)
    return f"elapsed: {values['elapsed']:>12} | ETA: {values['eta']:>12} | total est.: {values['total']:>12}"
