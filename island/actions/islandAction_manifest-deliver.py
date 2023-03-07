# -*- coding: utf-8 -*-
"""Action script for manifest-deliver.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

from realog import debug
import status

from island import (
    commands,
    config,
    env,
    manifest,
    multiprocess,
    tools,
)


#
# @brief Get the global description of the current action
# @return (string) the description string (fist line if reserved for the overview, all is for the specific display)
#
def help():
    return "Deliver the manifest (merge develop vertion and create a branch with the specific current tags)"


#
# @brief Add argument to the specific action
# @param[in,out] my_args (death.Arguments) Argument manager
# @param[in] section Name of the currect action
#
def add_specific_arguments(my_args, section):
    pass


# must be on the branch we choice to merge ...


#
# @brief Execute the action required.
#
# @return error value [0 .. 50] the <0 value is reserved system ==> else, what you want.
#         None : No error (return program out 0)
#         -10 : ACTION is not existing
#         -11 : ACTION execution system error
#         -12 : ACTION Wrong parameters
#
def execute(_arguments):
    argument_remote_name = ""
    for elem in _arguments:
        debug.error("pull Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_lutin_is_init()

    configuration = config.get_unique_config()

    file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
    if os.path.exists(file_source_manifest) is False:
        debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")

    elem = configuration.get_manifest_config()

    mani = manifest.Manifest(file_source_manifest)

    destination_branch = mani.deliver_master
    source_branch = mani.deliver_develop

    # Check the manifest is up to date ...
    base_display = tools.get_list_base_display(0, 0, elem)
    debug.verbose("deliver-ckeck: " + base_display)
    if (
        status.deliver_check(
            elem,
            argument_remote_name,
            0,
            base_display,
            source_branch,
            destination_branch,
        )
        is False
    ):
        debug.error("Can not deliver a MANIFEST that is not ready to merge", crash=False)
        return env.ret_action_fail

    all_tags = check_all_tags(mani)
    if all_tags == None:
        debug.error("Need the Tags are set in sub-repository", crash=False)
        return env.ret_action_fail

    # deliver the manifest (if Needed ...)
    base_display = tools.get_list_base_display(0, 0, elem)

    debug.info("manifest-deliver: ========================================================================")
    debug.info("manifest-deliver: == " + base_display)
    debug.info("manifest-deliver: ========================================================================")

    git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
    # Check the validity of the version,
    version_description, add_in_version_management = status.get_current_version_repo(git_repo_path)
    if version_description == None:
        return env.ret_action_fail
    debug.info("manifest-deliver:     ==> version: " + str(version_description))

    # go to the dev branch
    select_branch = commands.get_current_branch(git_repo_path)

    # create new repo tag
    new_version_description = status.create_new_version_repo(
        git_repo_path,
        version_description,
        add_in_version_management,
        source_branch,
        destination_branch,
    )
    debug.info("new version: " + str(new_version_description))
    if new_version_description == None:
        return
    # merge branch
    commands.checkout(git_repo_path, destination_branch)
    if mani.deliver_mode == "merge":
        merge_force = True
    else:
        merge_force = False
    commands.merge_branch_on_master(git_repo_path, source_branch, merge_force, branch_destination=destination_branch)

    manifest.tag_manifest(file_source_manifest, all_tags)

    version_path_file = os.path.join(git_repo_path, "version.txt")
    # update version file:
    tools.file_write_data(version_path_file, tools.version_to_string(new_version_description))
    commands.add_file(git_repo_path, version_path_file)
    commands.commit_all(
        git_repo_path,
        "[RELEASE] Release v" + tools.version_to_string(new_version_description),
    )
    commands.tag(git_repo_path, "v" + tools.version_to_string(new_version_description))
    commands.checkout(git_repo_path, source_branch)
    commands.reset_hard(git_repo_path, destination_branch)
    new_version_description.append("dev")
    manifest.tag_clear(file_source_manifest)
    tools.file_write_data(version_path_file, tools.version_to_string(new_version_description))
    commands.add_file(git_repo_path, version_path_file)
    commands.commit_all(git_repo_path, status.default_update_message)
    commands.checkout(git_repo_path, destination_branch)

    debug.info("manifest-deliver: ==> DONE")


def check_all_tags(mani):
    all_project = mani.get_all_configs()
    debug.info("Check all: " + str(len(all_project)) + " projects have a current tag ...")
    id_element = 0
    check_have_error = False
    list_tags = []
    for elem in all_project:
        id_element += 1
        base_display = tools.get_list_base_display(id_element, len(all_project), elem)
        if elem.volatile is True:
            debug.info(base_display + "\r\t\t\t\t\t\t\t\t\t" + "     (Not Managed)")
            continue
        tags_comment = ""
        git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
        if os.path.exists(git_repo_path) is False:
            debug.error(
                base_display + volatile + "\r\t\t\t\t\t\t\t\t\t" + "     (not download)",
                crash=False,
            )
            check_have_error = True
            continue
        ret_current_tags = commands.get_tags_current(git_repo_path)
        debug.verbose("tags found: " + str(ret_current_tags))
        if len(ret_current_tags) == 0:
            list_tags.append({"name": elem.name, "tag": ""})
        else:
            list_tags.append({"name": elem.name, "tag": ret_current_tags[0]})
        for elem_tag in ret_current_tags:
            if len(tags_comment) != 0:
                tags_comment += ","
            tags_comment += elem_tag
        if len(ret_current_tags) == 0:
            debug.error(
                base_display + "\r\t\t\t\t\t\t\t\t\t" + "     (NO TAG DETECTED)",
                crash=False,
            )
            check_have_error = True
            continue
        else:
            debug.info(base_display + "\r\t\t\t\t\t\t\t\t\t" + "     " + tags_comment)
    if check_have_error is True:
        return None
    return list_tags
