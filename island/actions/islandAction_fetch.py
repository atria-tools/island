"""Action script for fetch.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

from death.ArgElement import ArgElement
from death.Arguments import Arguments
from realog import debug

from island import (
    commands,
    config,
    env,
    manifest,
    parallel,
)
from island.parallel import ProjectResult, Status
from island.repo_config import RepoConfig


def help() -> str:
    return "Fecth all the repository (get all modification on the server)"


def add_specific_arguments(my_args: Arguments, section: str) -> None:
    my_args.add("r", "remote", haveParam=True, desc="Name of the remote server")


def fetch_project(elem: RepoConfig, remote_name: str) -> ProjectResult:
    """Fetch a project, then tell how its branch stands against its tracking branch."""
    git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
    if os.path.exists(git_repo_path) is False:
        return ProjectResult(Status.SKIPPED, "missing", "not downloaded (island sync)")
    if os.path.exists(os.path.join(git_repo_path, ".git")) is False:
        return ProjectResult(Status.ERROR, "error", "the folder exists but is not a git repository")
    ret = commands.fetch(git_repo_path, remote_name)
    if ret.returncode != 0:
        return ProjectResult(Status.ERROR, "error", ret.stderr.split("\n")[-1])
    return compare_with_tracking_branch(git_repo_path)


def compare_with_tracking_branch(git_repo_path: str) -> ProjectResult:
    """Tell how the current branch of a repository stands against its tracking branch."""
    select_branch = commands.get_current_branch(git_repo_path)
    if select_branch is None:
        return ProjectResult(Status.SKIPPED, "empty", "no commit")
    tracking_branch = commands.get_current_tracking_branch(git_repo_path)
    if tracking_branch is None:
        return ProjectResult(Status.WARNING, "no upstream", select_branch + " has no tracking branch")
    behind = commands.count_commits(git_repo_path, "HEAD", tracking_branch)
    ahead = commands.count_commits(git_repo_path, tracking_branch, "HEAD")
    to_push = f", {ahead} to push" if ahead != 0 else ""
    if behind != 0:
        return ProjectResult(Status.CHANGED, "to pull", f"{select_branch}: {behind} new on {tracking_branch}{to_push}")
    return ProjectResult(Status.OK, "up to date", select_branch + to_push)


def execute(_arguments: list[ArgElement]) -> int | None:
    argument_remote_name = ""
    for elem in _arguments:
        if elem.get_option_name() == "remote":
            debug.info("find remote name: '" + elem.get_arg() + "'")
            argument_remote_name = elem.get_arg()
        else:
            debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_island_is_init()

    configuration = config.get_unique_config()
    file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
    if os.path.exists(file_source_manifest) is False:
        debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")
    mani = manifest.Manifest(file_source_manifest)

    manifest_config = configuration.get_manifest_config()
    all_project = [manifest_config, *mani.get_all_configs()]

    def job(elem: RepoConfig) -> ProjectResult:
        # the manifest is always fetched from its origin
        remote_name = argument_remote_name if argument_remote_name != "" and elem is not manifest_config else elem.select_remote["name"]
        return fetch_project(elem, remote_name)

    results = parallel.run_on_projects("fetch", all_project, job)
    if parallel.has_error(results):
        return env.ret_action_fail
    return None
