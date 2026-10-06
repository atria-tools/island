"""Status interface display.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

from realog import debug

from island import (
    commands,
    env,
    multiprocess,
)
from island.repo_config import RepoConfig


base_name_of_a_tagged_branch = "branch_on_tag_"


def display_status(elem: RepoConfig, argument_remote_name: str, argument_display_tag: bool, id_element: int, base_display: str) -> int | None:
    volatile = ""
    if elem.volatile is True:
        volatile = " (volatile)"
    debug.verbose("status : " + base_display)
    # debug.debug("elem : " + str(elem))
    git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
    if os.path.exists(git_repo_path) is False:
        debug.info(base_display + volatile + "\r\t\t\t\t\t\t\t\t\t" + "     (not download)")
        return None

    is_modify = commands.check_repository_is_modify(git_repo_path)
    list_branch = commands.get_list_branch_all(git_repo_path)
    select_branch = commands.get_current_branch(git_repo_path)
    debug.verbose("List all branch: " + str(list_branch))
    if select_branch is None:
        # a repository without any commit (empty on the server) has no branch at all
        debug.info(base_display + volatile + "\r\t\t\t\t\t\t\t     (NO COMMIT)")
        return None
    if select_branch[: len(base_name_of_a_tagged_branch)] != base_name_of_a_tagged_branch:
        # get tracking branch
        tracking_remote_branch = commands.get_tracking_branch(git_repo_path, argument_remote_name, select_branch)
        if tracking_remote_branch is None:
            debug.info(base_display + volatile + "\r\t\t\t\t\t\t\t     (NO BRANCH)")
            return None
    else:
        tracking_remote_branch = select_branch[len(base_name_of_a_tagged_branch) :]
    modify_status = "     "
    if is_modify is True:
        modify_status = " *** "

    debug.verbose("select branch = '" + select_branch + "' is modify : " + str(is_modify) + "     track: '" + str(tracking_remote_branch) + "'")

    ret_current_branch_sha1 = commands.get_revision_list_to_branch(git_repo_path, select_branch)
    ret_track_branch_sha1 = commands.get_revision_list_to_branch(git_repo_path, tracking_remote_branch)
    # remove all identical sha1 ==> not needed for this
    in_forward = 0
    for elem_sha1 in ret_current_branch_sha1:
        if elem_sha1 not in ret_track_branch_sha1:
            in_forward += 1
    in_behind = 0
    for elem_sha1 in ret_track_branch_sha1:
        if elem_sha1 not in ret_current_branch_sha1:
            in_behind += 1

    behind_forward_comment = ""
    if in_forward != 0:
        behind_forward_comment += "forward=" + str(in_forward)
    if in_behind != 0:
        if in_forward != 0:
            behind_forward_comment += " "
        behind_forward_comment += "behind=" + str(in_behind)
    if behind_forward_comment != "":
        behind_forward_comment = "\r\t\t\t\t\t\t\t\t\t\t\t\t[" + behind_forward_comment + "]"

    tags_comment = ""
    # check the current tags of the repository
    if argument_display_tag is True:
        ret_current_tags = commands.get_tags_current(git_repo_path)
        debug.verbose("tags found: " + str(ret_current_tags))
        for elem_tag in ret_current_tags:
            if len(tags_comment) != 0:
                tags_comment += ","
            tags_comment += elem_tag
        if len(tags_comment) != 0:
            tags_comment = "\r\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t[" + tags_comment + "]"
        else:
            tags_comment = "\r\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t- - - - -"
    debug.info(
        base_display
        + volatile
        + "\r\t\t\t\t\t\t\t"
        + modify_status
        + "("
        + select_branch
        + " -> "
        + tracking_remote_branch
        + ")"
        + behind_forward_comment
        + tags_comment
    )
    if is_modify is True:
        cmd = "git status --short"
        debug.verbose("execute : " + cmd)
        ret_diff = multiprocess.run_command(cmd, cwd=git_repo_path)
        tmp_color_red = "\033[31m"
        tmp_color_default = "\033[00m"
        debug.info(tmp_color_red + ret_diff[1] + tmp_color_default)
    return in_behind


def checkout_elem(elem: RepoConfig, argument_remote_name: str, branch_to_checkout: str, base_display: str) -> bool:
    debug.verbose("checkout : " + base_display)
    git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
    if os.path.exists(git_repo_path) is False:
        debug.warning("checkout " + base_display + " ==> repository does not exist ...")
        return False

    # check if the repository is modify
    is_modify = commands.check_repository_is_modify(git_repo_path)
    if is_modify is True:
        debug.warning("checkout " + base_display + " ==> modify data can not checkout new branch")
        return False

    list_branch_local = commands.get_list_branch_local(git_repo_path)
    select_branch = commands.get_current_branch(git_repo_path)

    is_tag = False
    if branch_to_checkout == "__TAG__":
        branch_to_checkout = base_name_of_a_tagged_branch + str(elem.tag)
        is_tag = True
        if elem.volatile is True:
            debug.info("checkout " + base_display + " ==> Can not checkout for 'volatile' repository")
            return True
        if elem.tag is None:
            debug.info("checkout " + base_display + " ==> Can not checkout for '''None''' Tag")
            return True
    # check if we are on the good branch:
    if branch_to_checkout == select_branch:
        debug.info("checkout " + base_display + " ==> No change already on good branch")
        return True

    # check if we have already checkout the branch before
    debug.verbose("      check : " + branch_to_checkout + "    in " + str(list_branch_local))
    if branch_to_checkout in list_branch_local:
        cmd = "git checkout " + branch_to_checkout
        debug.verbose("execute : " + cmd)
        ret = multiprocess.run_command(cmd, cwd=git_repo_path)
        if ret.returncode != 0:
            debug.info("'" + str(ret) + "'")
            debug.error("checkout " + base_display + " ==> Can not checkout to the correct branch")
            return False
        debug.info("checkout " + base_display + " ==> switch branch")
        # TODO : Check the number of commit to the origin/XXX branch ....
        return True

    list_tags = commands.get_tags(git_repo_path)
    if branch_to_checkout in list_tags:
        is_tag = True
        if elem.tag is None:
            elem.tag = branch_to_checkout
            branch_to_checkout = base_name_of_a_tagged_branch + str(elem.tag)

    # Check if the remote branch exist ...
    if is_tag is False:
        list_branch_remote = commands.get_list_branch_remote(git_repo_path)
        if elem.select_remote["name"] + "/" + branch_to_checkout in list_branch_remote:
            debug.info("    ==> find ...")
        else:
            debug.info("checkout " + base_display + " ==> NO remote branch")
            return True
        # checkout the new branch:
        cmd = "git checkout --quiet " + elem.select_remote["name"] + "/" + branch_to_checkout + " -b " + branch_to_checkout
        # + " --track " + elem.select_remote["name"] + "/" + branch_to_checkout
        debug.verbose("execute : " + cmd)
        ret = multiprocess.run_command(cmd, cwd=git_repo_path)
        if ret.returncode != 0:
            debug.info("'" + str(ret) + "'")
            debug.error("checkout " + base_display + " ==> Can not checkout to the correct branch")
            return False
        debug.info("checkout " + base_display + " ==> create new branch")
        return True
    # Checkout a specific tags:
    if elem.tag in list_tags:
        debug.info("    ==> find ...")
    else:
        debug.info("checkout " + base_display + " ==> NO remote tags")
        return True
    # checkout the new branch:
    cmd = "git checkout --quiet " + elem.tag + " -b " + branch_to_checkout
    # + " --track " + elem.select_remote["name"] + "/" + branch_to_checkout
    debug.verbose("execute : " + cmd)
    ret = multiprocess.run_command(cmd, cwd=git_repo_path)
    if ret.returncode != 0:
        debug.info("'" + str(ret) + "'")
        debug.error("checkout " + base_display + " ==> Can not checkout to the correct tags")
        return False
    debug.info("checkout " + base_display + " ==> create new branch: " + branch_to_checkout)
    return True
