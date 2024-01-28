#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Command interface.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import errno
import fnmatch
import os
import shutil
import stat

# Local import
from realog import debug

from . import (
    env,
    multiprocess,
)


def check_repository_is_modify(path_repository):
    # check if the repository is modify
    cmd = "git diff --quiet"
    debug.verbose(f"execute : {cmd}")
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(
        return_value,
        "check_repository_is_modify",
        error_only=True,
        available_return=[0, 1],
        display_if_nothing=False,
    )
    ret_diff = return_value
    if ret_diff[0] == 0:
        return False
    return True


def get_list_branch_meta(path_repository):
    # get local branch
    cmd = "git branch -a"
    debug.verbose("execute : " + cmd)
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "get_list_branch_meta", error_only=True)
    ret_branch = return_value
    list_branch = ret_branch[1].split("\n")
    out = []
    for elem_branch in list_branch:
        is_remote = False
        branch_name = ""
        is_selected = False
        if len(elem_branch.split(" -> ")) != 1:
            continue
        # separate the remote element
        if elem_branch[2:10] == "remotes/":
            elem_branch = elem_branch[:2] + elem_branch[10:]
            is_remote = True
        # separate select branch
        if elem_branch[:2] == "* ":
            is_selected = True
            branch_name = elem_branch[2:]
        else:
            branch_name = elem_branch[2:]
        out.append({"remote": is_remote, "name": branch_name, "select": is_selected})
    debug.extreme_verbose("List all branch Meta: " + str(out))
    return out


def get_list_branch_all(path_repository):
    tmp = get_list_branch_meta(path_repository)
    out = []
    for elem in tmp:
        out.append(elem["name"])
    debug.verbose("List all branch: " + str(out))
    return out


def get_list_branch_local(path_repository):
    tmp = get_list_branch_meta(path_repository)
    out = []
    for elem in tmp:
        if elem["remote"] is False:
            out.append(elem["name"])
    debug.verbose("List local branch: " + str(out))
    return out


def get_list_branch_remote(path_repository):
    tmp = get_list_branch_meta(path_repository)
    out = []
    for elem in tmp:
        if elem["remote"] is True:
            out.append(elem["name"])
    debug.verbose("List remote branch: " + str(out))
    return out


def get_current_branch(path_repository):
    tmp = get_list_branch_meta(path_repository)
    for elem in tmp:
        if elem["select"] is True:
            debug.verbose("List local branch: " + str(elem["name"]))
            return elem["name"]
    debug.verbose("List local branch: None")
    return None


def get_current_tracking_branch(path_repository):
    # get  tracking branch
    cmd = "git rev-parse --abbrev-ref --symbolic-full-name @{u}"
    debug.verbose("execute : " + cmd)
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    if return_value[1] == "@{u}":
        debug.warning("in '" + path_repository + "' no tracking branch is specify")
        return None
    multiprocess.generic_display_error(return_value, "get_current_tracking_branch", error_only=True)
    return return_value[1]


def get_revision_list_to_branch(path_repository, branch):
    cmd = "git rev-list " + branch
    debug.verbose("execute : " + cmd)
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "get_revision_list_to_branch", error_only=True)
    return return_value[1].split("\n")


def get_specific_commit_message(path_repository, sha_1):
    if sha_1 is None or sha_1 == "":
        return ""
    cmd = "git log --format=%B -n 1 " + sha_1
    debug.verbose("execute : " + cmd)
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "get_specific_commit_message", error_only=True)
    return return_value[1].split("\n")[0]


def get_sha1_for_branch(path_repository, branch_name):
    if branch_name == None or branch_name == "":
        return None
    cmd = "git rev-parse " + branch_name
    debug.verbose("execute : " + cmd)
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "get_sha1_for_branch", error_only=True)
    return return_value[1].split("\n")[0]


def get_tags_current(path_repository):
    cmd = "git tag --points-at"
    debug.verbose("execute : " + cmd)
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "get_tags_current", error_only=True)
    list_tags = []
    for elem in return_value[1].split("\n"):
        if elem != "":
            list_tags.append(elem)
    return list_tags


def get_tags(path_repository):
    cmd = "git tag"
    debug.verbose("execute : " + cmd)
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "get_tags", error_only=True)
    return return_value[1].split("\n")


def get_tags_remote(path_repository, remote_name):
    if remote_name == "" or remote_name == None:
        return get_current_tracking_branch(path_repository)
    cmd = "git ls-remote --tags " + remote_name
    debug.verbose("execute : " + cmd)
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "get_tags_remote", error_only=True)
    list_element = return_value[1].split("\n")
    debug.verbose(" receive: " + str(list_element))
    # 6bc01117e85d00686ae2d423193a161e82df9a44	refs/tags/0.1.0
    # 7ef9caa51cf3744de0f46352e5aa07bd4980fe89	refs/tags/v0.2.0
    # 870e8e039b0a98370a9d23844f0af66824c57a5f	refs/tags/v0.2.0^{}
    # 16707e17e58f16b3409f8c64df7f595ba7dcf499	refs/tags/v0.3.0
    # dfb97c3dfea776e5c4862dc9f60f8c5ad83b55eb	refs/tags/v0.3.0^{}
    out = []
    for elem in list_element:
        cut = elem.split("\t")
        if len(cut) != 2:
            continue
        if cut[1][-3:] == "^{}":
            # specific usage for the annotated commit
            continue
        if cut[1][:10] == "refs/tags/":
            out.append(cut[1][10:])
        else:
            out.append(cut[1])
    return out


def get_tracking_branch(path_repository, remote_name, select_branch):
    # get tracking branch
    if remote_name == "" or remote_name == None:
        return get_current_tracking_branch(path_repository)
    list_branch_remote = get_list_branch_remote(path_repository)
    debug.extreme_verbose("check if exist " + remote_name + "/" + select_branch + " in " + str(list_branch_remote))
    if remote_name + "/" + select_branch not in list_branch_remote:
        debug.debug("    ==> can not get remote branch")
        return None
    return remote_name + "/" + select_branch


def merge_branch_on_master(path_repository, branch_name, merge_force=True, branch_destination="master"):
    if branch_name == None or branch_name == "":
        raise "Missing branch name"
    cmd = "git merge "
    if merge_force is True:
        cmd += "--no-ff "
    cmd += branch_name + " --message \"Merge branch '" + branch_name + "' into '" + branch_destination + "'\""
    debug.verbose("execute : " + cmd)
    # TODO: check if the command work correctly
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "merge_branch_on_master", error_only=True)
    return return_value


def add_file(path_repository, file_path):
    if file_path == None or file_path == "":
        raise "Missing file_path name"
    cmd = "git add " + file_path
    debug.verbose("execute : " + cmd)
    # TODO: check if the command work correctly
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "add_file", error_only=True)
    return return_value


def commit_all(path_repository, comment):
    if comment == None or comment == "":
        raise "Missing comment description"
    cmd = 'git commit -a --message "' + comment + '"'
    debug.verbose("execute : " + cmd)
    # TODO: check if the command work correctly
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "commit_all", error_only=True)
    return return_value


def tag(path_repository, tag_name):
    if tag_name == None or tag_name == "":
        raise "Missing tag name"
    tag_name = tag_name.replace(" ", "_")
    cmd = "git tag " + tag_name + ' --message "[TAG] create tag ' + tag_name + '"'
    debug.verbose("execute : " + cmd)
    # TODO: check if the command work correctly
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "tag", error_only=True)
    return return_value


def checkout(path_repository, branch_name):
    if branch_name == None or branch_name == "":
        raise "Missing branch name"
    cmd = "git checkout " + branch_name
    debug.verbose("execute : " + cmd)
    # TODO: check if the command work correctly
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "checkout", error_only=True)
    return return_value


def reset_hard(path_repository, destination):
    if destination == None or destination == "":
        raise "Missing destination 'sha1' or 'branch name'"
    cmd = "git reset --hard " + destination
    debug.verbose("execute : " + cmd)
    # TODO: check if the command work correctly
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "reset_hard", error_only=True)
    return return_value


def rebase(path_repository, destination):
    if destination == None or destination == "":
        raise "Missing destination 'sha1' or 'branch name'"
    cmd = "git rebase " + destination
    debug.verbose("execute : " + cmd)
    # TODO: check if the command work correctly
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "rebase", error_only=True)
    return return_value


def clone(path_repository, address, branch_name=None, origin=None):
    if address == None or address == "":
        raise "Missing address"
    cmd = "git clone " + address
    if branch_name != None and branch_name == "":
        cmd += " --branch " + branch_name
    if origin != None and origin == "":
        cmd += " --origin " + origin
    if path_repository != None and path_repository != "":
        cmd += " " + path_repository
    debug.verbose("execute : " + cmd)
    if os.path.exists(path_repository) is True:
        debug.warning("Can not clone repository path already exist")
        return False
    return_value = multiprocess.run_command(cmd)
    multiprocess.generic_display_error(return_value, "clone", error_only=True)
    return return_value


def fetch(path_repository, remote_name, prune=True):
    cmd = "git fetch " + remote_name
    if prune is True:
        cmd += " --prune"
    debug.verbose("execute : " + cmd)
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "fetch")
    return return_value


def pull(path_repository, remote_name, prune=True):
    if remote_name == None or remote_name == "":
        raise "Missing remote_name"
    cmd = "git pull " + remote_name
    if prune is True:
        cmd += " --prune"
    debug.verbose("execute : " + cmd)
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "pull")
    return return_value


def push(path_repository, remote_name, elements):
    if remote_name == None or remote_name == "":
        raise "Missing remote_name"
    if len(elements) == 0:
        raise "No elements to push on server"
    cmd = "git push " + remote_name
    for elem in elements:
        cmd += " " + elem
    debug.verbose("execute : " + cmd)
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "push")
    return return_value


def submodule_sync(path_repository, remote_name):
    cmd = "git submodule sync"
    debug.verbose("execute : " + cmd)
    return_value = multiprocess.run_command(cmd, cwd=path_repository)
    multiprocess.generic_display_error(return_value, "submodule_sync")
    """
	if ret[:31] == "Synchronizing submodule url for":
		#all is good ...
		debug.info("    " + ret)
	elif     ret != "" \
	     and ret != False:
		# all is good, ready to get the system work corectly
		debug.info("'" + ret + "'")
		debug.error("Can not sync submodules ... ")
	"""


def get_forward(path_repository, branch_name):
    if branch_name == None or branch_name == "":
        raise "get_fast_forward: Missing branch_name"
    select_branch = get_current_branch(path_repository)
    # get tracking branch
    ret_current_branch_sha1 = get_revision_list_to_branch(path_repository, select_branch)
    ret_track_branch_sha1 = get_revision_list_to_branch(path_repository, branch_name)
    # count the number of commit fast forward
    forward_count = 0
    for elem_sha1 in ret_current_branch_sha1:
        if elem_sha1 not in ret_track_branch_sha1:
            forward_count += 1
    return forward_count


def is_forward(path_repository, branch_name):
    return get_forward(path_repository, branch_name) != 0


def get_behind(path_repository, branch_name):
    if branch_name == None or branch_name == "":
        raise "get_fast_forward: Missing branch_name"
    select_branch = get_current_branch(path_repository)
    # get tracking branch
    ret_current_branch_sha1 = get_revision_list_to_branch(path_repository, select_branch)
    ret_track_branch_sha1 = get_revision_list_to_branch(path_repository, branch_name)
    # count the number of commit behind
    behind_count = 0
    for elem_sha1 in ret_track_branch_sha1:
        if elem_sha1 not in ret_current_branch_sha1:
            behind_count += 1
    return behind_count


def is_behind(path_repository, branch_name):
    return get_behind(path_repository, branch_name) != 0
