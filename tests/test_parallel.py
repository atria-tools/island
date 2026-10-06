"""Tests of the run of an action on several projects at a time."""

import io
import threading
import time

from realog import debug

from island import parallel
from island.parallel import ProjectResult, Status
from island.repo_config import RepoConfig


def make_projects(count: int) -> list[RepoConfig]:
    projects = []
    for index in range(count):
        project = RepoConfig()
        project.name = f"repo{index}.git"
        project.path = f"repo{index}"
        projects.append(project)
    return projects


def test_the_results_follow_the_order_of_the_projects() -> None:
    def job(project: RepoConfig) -> ProjectResult:
        # the first projects end last
        time.sleep(0.05 * (5 - int(project.path[4:])))
        return ProjectResult(Status.OK, "up to date", project.path)

    results = parallel.run_on_projects("test", make_projects(5), job, jobs=5, out=io.StringIO())
    assert [result.message for result in results] == [f"repo{index}" for index in range(5)]


def test_the_projects_run_at_the_same_time_up_to_the_jobs() -> None:
    lock = threading.Lock()
    running = 0
    most = 0

    def job(_project: RepoConfig) -> ProjectResult:
        nonlocal running, most
        with lock:
            running += 1
            most = max(most, running)
        time.sleep(0.05)
        with lock:
            running -= 1
        return ProjectResult(Status.OK, "up to date")

    parallel.run_on_projects("test", make_projects(12), job, jobs=5, out=io.StringIO())
    assert most == 5


def test_one_line_per_project_with_its_warnings_and_a_summary() -> None:
    def job(project: RepoConfig) -> ProjectResult:
        debug.info("a detail nobody needs")
        if project.path == "repo1":
            debug.warning("something to know")
            return ProjectResult(Status.WARNING, "modified", "fetched only")
        return ProjectResult(Status.CHANGED, "updated", "dev: 2 new commits")

    out = io.StringIO()
    parallel.run_on_projects("sync", make_projects(3), job, jobs=2, out=out)
    lines = out.getvalue().split("\n")
    assert len([line for line in lines if "updated    dev: 2 new commits" in line]) == 2
    warning = next(index for index, line in enumerate(lines) if "modified   fetched only" in line)
    assert "something to know" in lines[warning + 1]
    assert "a detail nobody needs" not in out.getvalue()
    assert lines[-2].startswith("sync: 3 projects in ")
    assert lines[-2].endswith("s: 2 updated, 1 modified")


def test_an_error_ends_its_project_alone() -> None:
    def job(project: RepoConfig) -> ProjectResult:
        if project.path == "repo0":
            debug.error("the server does not answer")
        if project.path == "repo1":
            raise ValueError("broken")
        return ProjectResult(Status.OK, "up to date")

    out = io.StringIO()
    results = parallel.run_on_projects("fetch", make_projects(3), job, jobs=3, out=out)
    assert (results[0].status, results[0].message) == (Status.ERROR, "the server does not answer")
    assert (results[1].status, results[1].message) == (Status.ERROR, "ValueError: broken")
    assert results[2].status is Status.OK
    assert parallel.has_error(results)
