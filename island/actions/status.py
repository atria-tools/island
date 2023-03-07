# -*- coding: utf-8 -*-
"""Status interface display.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

from realog import debug

from island import (
    commands,
    config,
    env,
    manifest,
    multiprocess,
    tools,
)


default_behind_message = "[DEV] update dev tag version"
default_update_message = "[VERSION] update dev tag version"


base_name_of_a_tagged_branch = "branch_on_tag_"


def display_status(elem, argument_remote_name, argument_display_tag, id_element, base_display):
    volatile = ""
    if elem.volatile is True:
        volatile = " (volatile)"
    debug.verbose("status : " + base_display)
    # debug.debug("elem : " + str(elem))
    git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
    if os.path.exists(git_repo_path) is False:
        debug.info(base_display + volatile + "\r\t\t\t\t\t\t\t\t\t" + "     (not download)")
        return

    is_modify = commands.check_repository_is_modify(git_repo_path)
    list_branch = commands.get_list_branch_all(git_repo_path)
    select_branch = commands.get_current_branch(git_repo_path)
    debug.verbose("List all branch: " + str(list_branch))
    if select_branch[: len(base_name_of_a_tagged_branch)] != base_name_of_a_tagged_branch:
        # get tracking branch
        tracking_remote_branch = commands.get_tracking_branch(git_repo_path, argument_remote_name, select_branch)
        if tracking_remote_branch == None:
            debug.info(base_display + volatile + "\r\t\t\t\t\t\t\t     (NO BRANCH)")
            return
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


def deliver_check(
    elem,
    argument_remote_name,
    id_element,
    base_display,
    source_branch,
    destination_branch,
):
    deliver_available = True
    debug.debug("deliver-ckeck: " + base_display)
    debug.debug("    ==> check repo exist")
    # Check the repo exist
    git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
    if os.path.exists(git_repo_path) is False:
        debug.warning("deliver-ckeck: " + base_display + " ==> MUST be download")
        return False
    debug.debug("    ==> check is modify")
    # check if the curent repo is modify
    is_modify = commands.check_repository_is_modify(git_repo_path)
    if is_modify is True:
        debug.warning("deliver-ckeck: " + base_display + " ==> MUST not be modify")
        return False

    debug.debug("    ==> check current branch is '" + source_branch + "'")
    # check if we are on source_branch
    select_branch = commands.get_current_branch(git_repo_path)
    if select_branch != source_branch:
        debug.warning("deliver-ckeck: " + base_display + " ==> MUST be on source branch: '" + source_branch + "' and is: '" + select_branch + "'")
        return False
    debug.debug("    ==> check have tracking branch")
    # check if we have a remote traking branch
    tracking_remote_branch = commands.get_tracking_branch(git_repo_path, argument_remote_name, select_branch)
    if tracking_remote_branch == None:
        debug.warning("deliver-ckeck: " + base_display + " ==> MUST have a remote tracking branch")
        deliver_available = False

    # go on destination branch
    commands.checkout(git_repo_path, destination_branch)
    # TODO: check return value

    debug.debug("    ==> check current branch is '" + source_branch + "'")
    # check if we are on "master"
    select_branch = commands.get_current_branch(git_repo_path)
    if select_branch != destination_branch:
        debug.warning("deliver-ckeck: " + base_display + " ==> Can not checkout branch: '" + destination_branch + "' and is: '" + select_branch + "'")
        deliver_available = False
    debug.debug("    ==> check have tracking branch")
    # check if we have a remote traking branch
    tracking_remote_branch = commands.get_tracking_branch(git_repo_path, argument_remote_name, select_branch)
    if tracking_remote_branch == None:
        debug.warning("deliver-ckeck: " + base_display + " ==> MUST have a remote tracking branch")
        deliver_available = False

    """
	# check if we have a local branch
	list_branch_local = commands.get_list_branch_local(git_repo_path)
	if destination_branch not in list_branch_local:
		debug.warning("deliver-ckeck: " + base_display + " ==> MUST have local branch named '" + destination_branch + "'")
		deliver_available = False
	# TODO: check source_branch is up to date

	# TODO: check the remote branch and the local branch are the same
	#sha_tracking = get_sha1_for_branch(git_repo_path, tracking_remote_branch)
	#sha_current = get_sha1_for_branch(git_repo_path, select_branch)
	"""

    # check out back the source branch
    commands.checkout(git_repo_path, source_branch)
    return deliver_available


def checkout_elem(elem, argument_remote_name, branch_to_checkout, base_display):
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
        if elem.tag == None:
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
        if ret[0] != 0 and ret[1] != "" and ret != False:
            debug.info("'" + str(ret) + "'")
            debug.error("checkout " + base_display + " ==> Can not checkout to the correct branch")
            return False
        debug.info("checkout " + base_display + " ==> switch branch")
        # TODO : Check the number of commit to the origin/XXX branch ....
        return True

    list_tags = commands.get_tags(git_repo_path)
    if branch_to_checkout in list_tags:
        is_tag = True
        if elem.tag == None:
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
        if ret[1] != "" and ret != False:
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
    if ret[1] != "" and ret != False:
        debug.info("'" + str(ret) + "'")
        debug.error("checkout " + base_display + " ==> Can not checkout to the correct tags")
        return False
    debug.info("checkout " + base_display + " ==> create new branch: " + branch_to_checkout)
    return True


def get_current_version_repo(git_repo_path):
    version_path_file = os.path.join(git_repo_path, "version.txt")
    add_in_version_management = False
    version_description = None
    if os.path.exists(version_path_file) is False:
        debug.info("deliver:     ==> No 'version.txt' file ==> not manage release version....")
        # Action to do:
        valid = False
        while valid is False:
            debug.info("Create a new version: (0.0.0)")
            debug.info("    (1) Add in managing version")
            debug.info("    (2) Do NOTHING & continue")
            input1 = input()
            if input1 in ["1", "2"]:
                valid = True
            else:
                debug.info("!!! Must select in range " + str(["1", "2"]))
        if input1 == "1":
            version_description = [0, 0, 0]
            add_in_version_management = True
        elif input1 == "2":
            debug.info("Continue Not managing for this repository")
            return (None, None)
        else:
            debug.warning("An error occured for this repository")
            return (None, None)
    else:
        version_description = tools.version_string_to_list(tools.file_read_data(version_path_file))
    return (version_description, add_in_version_management)


def create_new_version_repo(
    git_repo_path,
    version_description,
    add_in_version_management,
    source_branch,
    destination_branch,
):
    # get tracking branch
    ret_destination_branch_sha1 = commands.get_revision_list_to_branch(git_repo_path, destination_branch)
    ret_source_branch_sha1 = commands.get_revision_list_to_branch(git_repo_path, source_branch)
    # remove all identical sha1 ==> not needed for this
    have_forward = False
    for elem_sha1 in ret_destination_branch_sha1:
        if elem_sha1 not in ret_source_branch_sha1:
            message = commands.get_specific_commit_message(git_repo_path, elem_sha1)
            debug.warning("deliver:      Forward commit: '" + message + "'")
            have_forward = True
    if have_forward is True:
        debug.error("'" + destination_branch + "' branch must not be forward '" + source_branch + "' branch")
        return None
    behind_message = ""
    behind_count = 0
    for elem_sha1 in ret_source_branch_sha1:
        if elem_sha1 not in ret_destination_branch_sha1:
            message = commands.get_specific_commit_message(git_repo_path, elem_sha1)
            behind_count += 1
            behind_message = message
    if behind_count == 0 and add_in_version_management is False:
        debug.info("deliver:     ==> Nothing to do (1).")
        return None
    if behind_count == 1 and (behind_message == default_behind_message or behind_message == default_update_message):
        debug.info("deliver:     ==> Nothing to do (2).")
        return None
    for elem_sha1 in ret_source_branch_sha1:
        if elem_sha1 not in ret_destination_branch_sha1:
            message = commands.get_specific_commit_message(git_repo_path, elem_sha1)
            debug.info("deliver:      Behind  commit: '" + message + "'")
    # Choice of the new version:
    valid = False
    while valid is False:
        debug.info("update version: curent: " + str(version_description))
        debug.info("    (1) Major version  (change API)")
        debug.info("    (2) Medium version (add feature)")
        debug.info("    (3) Minor version  (Bug fix & doc)")
        debug.info("    (4) Do not release & continue")
        input1 = input()
        if input1 in ["1", "2", "3", "4"]:
            valid = True
        else:
            debug.info("!!! Must select in range " + str(["1", "2", "3", "4"]))
    # limit and force at 3 the nuber of variables
    version_description_tmp = version_description
    version_description = []
    if len(version_description_tmp) >= 1:
        version_description.append(version_description_tmp[0])
    else:
        version_description.append(0)
    if len(version_description_tmp) >= 2:
        version_description.append(version_description_tmp[1])
    else:
        version_description.append(0)
    if len(version_description_tmp) >= 3:
        version_description.append(version_description_tmp[2])
    else:
        version_description.append(0)
    debug.info("update version: curent: " + str(version_description))
    # increment the version
    if input1 == "1":
        version_description[0] += 1
        version_description[1] = 0
        version_description[2] = 0
    elif input1 == "2":
        version_description[1] += 1
        version_description[2] = 0
    elif input1 == "3":
        version_description[2] += 1
    elif input1 == "4":
        debug.info("No release for this repository")
        return None
    else:
        debug.warning("An error occured for this repository")
        return None
    debug.info("update version: curent: " + str(version_description))
    return version_description


def deliver_push(elem, argument_remote_name, destination_branch, source_branch, base_display):
    # Check the repo exist
    git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
    if os.path.exists(git_repo_path) is False:
        debug.warning("deliver-push: " + base_display + " ==> MUST be download")
        return
    # check if we are on destination_branch
    select_branch = commands.get_current_branch(git_repo_path)
    if select_branch != destination_branch:
        debug.warning("deliver-push: " + base_display + " ==> MUST be on '" + destination_branch + "'")
        return
    # check if we have a local branch
    list_branch_local = commands.get_list_branch_local(git_repo_path)
    if source_branch not in list_branch_local:
        debug.warning("deliver-push: " + base_display + " ==> No '" + source_branch + "' (not managed)")
        return
    if destination_branch not in list_branch_local:
        debug.warning("deliver-push: " + base_display + " ==> No '" + destination_branch + "' (not managed)")
        return
    list_of_element_to_push = []
    # check sha1 of destination_branch
    sha_1_destination = commands.get_sha1_for_branch(git_repo_path, destination_branch)
    tracking_remote_branch = commands.get_tracking_branch(git_repo_path, argument_remote_name, destination_branch)
    if tracking_remote_branch == None:
        debug.warning("deliver-push: " + base_display + " ==> '" + destination_branch + "' have no tracking branch")
        deliver_available = False
    sha_1_destination_tracking = commands.get_sha1_for_branch(git_repo_path, tracking_remote_branch)
    if sha_1_destination == sha_1_destination_tracking:
        debug.info("deliver-push: " + base_display + " ==> '" + destination_branch + "' && '" + tracking_remote_branch + "' have the same sha1")
    else:
        list_of_element_to_push.append(destination_branch)
    # check sha1 of source_branch
    sha_1_source = commands.get_sha1_for_branch(git_repo_path, source_branch)
    tracking_remote_branch = commands.get_tracking_branch(git_repo_path, argument_remote_name, source_branch)
    if tracking_remote_branch == None:
        debug.info("deliver-push: " + base_display + " ==> '" + source_branch + "' have no tracking branch")
        deliver_available = False
    sha_1_source_tracking = commands.get_sha1_for_branch(git_repo_path, tracking_remote_branch)
    if sha_1_source == sha_1_source_tracking:
        debug.info("deliver-push: " + base_display + " ==> '" + source_branch + "' && '" + tracking_remote_branch + "' have the same sha1")
    else:
        list_of_element_to_push.append(source_branch)
    ret_current_tags = commands.get_tags_current(git_repo_path)
    if len(ret_current_tags) == 0:
        debug.info("deliver-push: " + base_display + " ==> No tag on the current '" + destination_branch + "'")
        return
    if len(ret_current_tags) > 1:
        debug.info(
            "deliver-push: "
            + base_display
            + " ==> Too mush tags on the current '"
            + destination_branch
            + "' : "
            + str(ret_current_tags)
            + " ==> only support 1"
        )
        return
    list_remote_tags = commands.get_tags_remote(git_repo_path, argument_remote_name)
    debug.verbose("remote tags: " + str(list_remote_tags))
    if ret_current_tags[0] not in list_remote_tags:
        debug.info("deliver-push: " + base_display + " ==> tag already exist.")
        list_of_element_to_push.append(ret_current_tags[0])
    if len(list_of_element_to_push) == 0:
        debug.info("deliver-push: " + base_display + " ==> Everything up-to-date")
        return
    debug.info("deliver-push: " + base_display + " ==> element to push:" + str(list_of_element_to_push))
    # push all on the server:
    commands.push(git_repo_path, argument_remote_name, list_of_element_to_push)
