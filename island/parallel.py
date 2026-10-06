"""Run an action on the projects of the workspace, several at a time, with one line per project.

Each project runs in a thread (git does the work, island waits for it). What the project logs through
realog is kept apart while it runs, then shown under its line: its warnings and errors always, all of
it from the debug level. An error of a project (an exception, or a debug.error that would stop
island) ends that project alone.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import enum
import os
import re
import sys
import threading
import time
from typing import TextIO

from realog import debug

from . import env
from .repo_config import RepoConfig


class Status(enum.Enum):
    """How a project ended, from the best to the worst."""

    OK = "ok"
    CHANGED = "changed"
    SKIPPED = "skipped"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ProjectResult:
    """What an action did on a project: a status, a short label (up to date, cloned...) and a message."""

    status: Status
    label: str
    message: str = ""
    logs: list[str] = field(default_factory=list)
    duration: float = 0.0


_ANSI = re.compile(r"\033\[[0-9;]*m")
_COLORS = {
    Status.OK: "\033[32m",
    Status.CHANGED: "\033[36m",
    Status.SKIPPED: "\033[02m",
    Status.WARNING: "\033[33m",
    Status.ERROR: "\033[31m",
}
_RESET = "\033[00m"


# the logs of realog go to the list of the thread while one of its projects runs
_capture = threading.local()
_original_local_print = debug.local_print


def _print_or_capture(value: str) -> None:
    lines: list[str] | None = getattr(_capture, "lines", None)
    if lines is None:
        _original_local_print(value)
    else:
        lines.extend(value.split("\n"))


def _install_capture() -> None:
    if debug.local_print is not _print_or_capture:
        debug.local_print = _print_or_capture


def get_jobs() -> int:
    """Get the number of projects run at a time: 1 when island waits between the server accesses."""
    if env.get_wait_between_sever_command() != 0:
        return 1
    return max(1, env.get_jobs())


def project_name(project: RepoConfig) -> str:
    """Get the name a project is shown with: its folder, or its repository (option --folder)."""
    return project.path if env.get_display_folder_instead_of_git_name() is True else project.name


def _run_one(job: Callable[[RepoConfig], ProjectResult], project: RepoConfig) -> ProjectResult:
    _capture.lines = []
    start = time.monotonic()
    try:
        result = job(project)
    except SystemExit:
        # debug.error stopped the project: its message is the last error logged
        errors = [_ANSI.sub("", line).removeprefix("[ERROR] ") for line in _capture.lines if "[ERROR]" in line]
        result = ProjectResult(Status.ERROR, "error", errors[-1] if errors else "failed")
    except Exception as ex:
        result = ProjectResult(Status.ERROR, "error", f"{type(ex).__name__}: {ex}")
    finally:
        logs: list[str] = _capture.lines
        _capture.lines = None
    result.logs = logs + result.logs
    result.duration = time.monotonic() - start
    return result


class _Display:
    """One line per project as it ends, and on a terminal the projects still running at the bottom."""

    def __init__(self, action: str, projects: Sequence[RepoConfig], jobs: int, out: TextIO) -> None:
        self.action = action
        self.out = out
        self.count = len(projects)
        self.done = 0
        self.running: list[str] = []
        self.width = max((len(project_name(project)) for project in projects), default=0)
        self.terminal = out.isatty()
        self.color = (self.terminal and "NO_COLOR" not in os.environ) or bool(debug.debug_color and debug.color_default)
        self.lock = threading.Lock()

    def _paint(self, status: Status, text: str) -> str:
        return _COLORS[status] + text + _RESET if self.color else text

    def _write(self, text: str) -> None:
        if self.terminal:
            # erase the line of the running projects first
            self.out.write("\r\033[K")
        self.out.write(text)
        if self.terminal and self.running:
            self.out.write(
                f"  {self.action}: {self.done}/{self.count} done, running {', '.join(self.running)}"[
                    : os.get_terminal_size(self.out.fileno()).columns - 1
                ]
            )
        self.out.flush()

    def start(self, name: str) -> None:
        with self.lock:
            self.running.append(name)
            self._write("")

    def end(self, name: str, result: ProjectResult) -> None:
        with self.lock:
            self.running.remove(name)
            self.done += 1
            index = f"[{self.done:>{len(str(self.count))}}/{self.count}]"
            text = f"{index} {name:<{self.width}}  {self._paint(result.status, f'{result.label:<10}')} {result.message}".rstrip() + "\n"
            for line in result.logs:
                if line.strip() == "":
                    continue
                if debug.get_level() >= 4 or "[W]" in line or "[ERROR]" in line:
                    text += "        " + line + "\n"
            self._write(text)

    def summary(self, results: Sequence[ProjectResult], duration: float) -> None:
        by_label: dict[tuple[Status, str], int] = {}
        for result in sorted(results, key=lambda elem: list(Status).index(elem.status)):
            by_label[(result.status, result.label)] = by_label.get((result.status, result.label), 0) + 1
        parts = [self._paint(status, f"{number} {label}") for (status, label), number in by_label.items()]
        self._write(f"{self.action}: {self.count} projects in {duration:.1f} s: {', '.join(parts)}\n")


def run_on_projects(
    action: str,
    projects: Sequence[RepoConfig],
    job: Callable[[RepoConfig], ProjectResult],
    jobs: int | None = None,
    out: TextIO | None = None,
    summary: bool = True,
) -> list[ProjectResult]:
    """Run a job on each project, several at a time, and show how each one ends.

    :param action: Name of the action, shown in the progress and the summary
    :param projects: Projects to run the job on
    :param job: What to do on a project; it may log through realog
    :param jobs: Number of projects run at a time (None: the option --jobs)
    :param out: Where the lines go (None: the standard output)
    :param summary: Show the summary line at the end
    :return: the result of each project, in the order of the projects
    """
    _install_capture()
    display = _Display(action, projects, jobs or get_jobs(), out or sys.stdout)
    start = time.monotonic()

    def run(project: RepoConfig) -> ProjectResult:
        name = project_name(project)
        display.start(name)
        result = _run_one(job, project)
        display.end(name, result)
        return result

    with ThreadPoolExecutor(max_workers=jobs or get_jobs()) as executor:
        results = list(executor.map(run, projects))
    if summary is True:
        display.summary(results, time.monotonic() - start)
    return results


def has_error(results: Sequence[ProjectResult]) -> bool:
    return any(result.status is Status.ERROR for result in results)
