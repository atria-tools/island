"""Action script for sync.

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
    multiprocess,
    parallel,
    tools,
)
from island.actions import update_links
from island.parallel import ProjectResult, Status
from island.repo_config import RepoConfig


def help() -> str:
    return "Syncronize all the repository referenced"


def help_example() -> str:
    return "island init https://git.heeroyui.org/atria-tools/island.git"


def add_specific_arguments(my_args: Arguments, section: str) -> None:
    my_args.add(
        "d",
        "download",
        haveParam=False,
        desc="Just download the 'not download' repository",
    )


def execute(_arguments: list[ArgElement]) -> int | None:
    just_download = False
    for elem in _arguments:
        if elem.get_option_name() == "download":
            just_download = True
            debug.info("find remote name: '" + elem.get_arg() + "'")
        else:
            debug.error("SYNC Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_island_is_init()

    configuration = config.get_unique_config()

    # TODO: Load Old manifect to check diff ...

    commands.configure_repository(env.get_island_path_manifest(), configuration)
    if env.get_fetch_manifest() is False:
        debug.info("manifest not updated (--no-fetch-manifest)")
    else:
        # the manifest first: it tells what the projects are
        manifest_result = parallel.run_on_projects(
            "manifest", [configuration.get_manifest_config()], lambda elem: sync_project(elem, configuration, False), jobs=1, summary=False
        )
        if parallel.has_error(manifest_result):
            return env.ret_action_fail

    file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
    if os.path.exists(file_source_manifest) is False:
        debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")

    mani = manifest.Manifest(file_source_manifest)

    all_project = mani.get_all_configs()

    def job(elem: RepoConfig) -> ProjectResult:
        tools.wait_for_server_if_needed()
        return sync_project(elem, configuration, just_download)

    results = parallel.run_on_projects("sync", all_project, job)

    # Update the links:
    have_error = update_links.update(configuration, mani, "sync")
    if have_error is True or parallel.has_error(results):
        return env.ret_action_fail
    return None


def sync_project(elem: RepoConfig, configuration: config.Config, just_download: bool) -> ProjectResult:
    """Clone a project, or bring it up to date with its tracking branch."""
    git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
    if elem.tag is not None:
        debug.warning("Need to select a specific tag version ... " + elem.tag)
    if os.path.exists(git_repo_path) is False:
        return clone_project(elem, configuration, git_repo_path)
    if just_download is True:
        return ProjectResult(Status.SKIPPED, "present", "already downloaded")
    if os.path.exists(os.path.join(git_repo_path, ".git")) is False:
        return ProjectResult(Status.ERROR, "error", "the folder exists but is not a git repository: clean it and sync again")

    commands.configure_repository(git_repo_path, configuration)
    select_branch = commands.get_current_branch(git_repo_path)
    tracking_branch = commands.get_current_tracking_branch(git_repo_path)
    if select_branch is None or tracking_branch is None or commands.check_repository_is_modify(git_repo_path) is True:
        # nothing to pull into: only fetch
        ret = commands.fetch(git_repo_path, elem.select_remote["name"])
        if ret.returncode != 0:
            return ProjectResult(Status.ERROR, "error", ret.stderr.split("\n")[-1])
        if select_branch is None:
            return ProjectResult(Status.SKIPPED, "empty", "no commit")
        if tracking_branch is None:
            return ProjectResult(Status.WARNING, "no upstream", select_branch + " has no tracking branch: fetched only")
        behind = commands.count_commits(git_repo_path, "HEAD", tracking_branch)
        return ProjectResult(Status.WARNING, "modified", f"{select_branch} has local changes: fetched only, {behind} new on {tracking_branch}")

    before = commands.get_sha1_for_branch(git_repo_path, "HEAD")
    ret = commands.pull(git_repo_path, elem.select_remote["name"])
    if ret.returncode != 0:
        return ProjectResult(Status.ERROR, "error", ret.stderr.split("\n")[-1])
    # check submodule if requested:
    if elem.select_remote["sync"] is True and os.path.exists(os.path.join(git_repo_path, ".gitmodules")) is True:
        commands.submodule_sync(git_repo_path, elem.select_remote["name"])
    after = commands.get_sha1_for_branch(git_repo_path, "HEAD")
    if before == after or before is None or after is None:
        return ProjectResult(Status.OK, "up to date", select_branch)
    count = commands.count_commits(git_repo_path, before, after)
    return ProjectResult(Status.CHANGED, "updated", f"{select_branch}: {count} new commit{'s' if count > 1 else ''}")


def clone_project(elem: RepoConfig, configuration: config.Config, git_repo_path: str) -> ProjectResult:
    """Clone a project with its mirrors and its submodules."""
    # example git@git.plouf.com:basic_folder
    address_manifest = elem.select_remote["fetch"]
    if elem.select_remote["fetch"][0:4] == "git@" and len(elem.select_remote["fetch"][4:].split(":")) <= 1:
        address_manifest += ":"
    else:
        address_manifest += "/"
    address_manifest += elem.name
    ret = commands.clone(
        git_repo_path,
        address_manifest,
        branch_name=elem.branch,
        origin=elem.select_remote["name"],
    )
    if ret is False or ret.returncode != 0:
        return ProjectResult(Status.ERROR, "error", "can not clone " + address_manifest + ("" if ret is False else ": " + ret.stderr.split("\n")[-1]))
    # add global mirror list
    for mirror in elem.select_remote["mirror"]:
        debug.verbose("Add global mirror: " + str(mirror))
        cmd = "git remote add " + mirror["name"] + " " + mirror["fetch"]
        if mirror["fetch"][0:4] == "git@":
            cmd += ":"
        else:
            cmd += "/"
        cmd += elem.name
        ret_mirror = multiprocess.run_command(cmd, cwd=git_repo_path)
        if ret_mirror.returncode != 0:
            debug.info("'" + str(ret_mirror) + "'")
            debug.warning("Can not add global mirror ... ")
            continue
        debug.verbose("Add global mirror: " + str(mirror) + " (done)")
    # check submodule if requested:
    if elem.select_remote["sync"] is True and os.path.exists(os.path.join(git_repo_path, ".gitmodules")) is True:
        debug.info("    ==> update submodule")
        for cmd in ("git submodule init", "git submodule update"):
            ret_submodule = multiprocess.run_command(cmd, cwd=git_repo_path)
            if ret_submodule.returncode != 0:
                debug.info("'" + str(ret_submodule) + "'")
                debug.error("Can not init submodules ... ")
            if ret_submodule.stdout != "":
                debug.info("    " + ret_submodule.stdout)
    commands.configure_repository(git_repo_path, configuration)
    return ProjectResult(Status.CHANGED, "cloned", str(commands.get_current_branch(git_repo_path)))
