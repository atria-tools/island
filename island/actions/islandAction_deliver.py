#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license MPL v2.0 (see license file)
##

from realog import debug
from island import tools
from island import env
from island import multiprocess
from island import config
from island import manifest
from island import commands
import os


def help():
	return "Get the status of all the repositories"


def add_specific_arguments(_my_args, _section):
	_my_args.add("t", "tags", haveParam=False, desc="Display if the commit is on a tag (and display it)")

default_behind_message = "[DEV] update dev tag version"
default_update_message = "[VERSION] update dev tag version"

def execute(arguments):
	argument_remote_name = ""
	argument_display_tag = False
	for elem in arguments:
		if elem.get_option_name() == "tags":
			argument_display_tag = True
		else:
			debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")
	
	# check if .XXX exist (create it if needed)
	if    os.path.exists(env.get_island_path()) == False \
	   or os.path.exists(env.get_island_path_config()) == False \
	   or os.path.exists(env.get_island_path_manifest()) == False:
		debug.error("System already init have an error: missing data: '" + str(env.get_island_path()) + "'")
	
	configuration = config.Config()
	
	file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
	if os.path.exists(file_source_manifest) == False:
		debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")
	
	mani = manifest.Manifest(file_source_manifest)
	
	all_project = mani.get_all_configs()
	debug.info("Check if all project are on master: " + str(len(all_project)) + " projects")
	id_element = 0
	deliver_availlable = True
	for elem in all_project:
		id_element += 1
		base_display = tools.get_list_base_display(id_element, len(all_project), elem)
		debug.verbose("deliver-ckeck: " + base_display)
		# Check the repo exist
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		if os.path.exists(git_repo_path) == False:
			debug.warning("deliver-ckeck: " + base_display + " ==> MUST be download")
			deliver_availlable = False
			continue
		# check if we are on "master"
		select_branch = commands.get_current_branch(git_repo_path)
		if select_branch != "master":
			debug.warning("deliver-ckeck: " + base_display + " ==> MUST be on master")
			deliver_availlable = False
		# check if we have a remote traking branch
		tracking_remote_branch = commands.get_tracking_branch(git_repo_path, argument_remote_name, select_branch)
		if tracking_remote_branch == None:
			debug.warning("deliver-ckeck: " + base_display + " ==> MUST have a remote tracking branch")
			deliver_availlable = False
		# check if we have a local branch
		list_branch_local = commands.get_list_branch_local(git_repo_path)
		if "develop" not in list_branch_local:
			debug.warning("deliver-ckeck: " + base_display + " ==> MUST have local branch named develop")
			deliver_availlable = False
		# TODO: check develop is up to date
		
		# check if the curent repo is modify
		is_modify = commands.check_repository_is_modify(git_repo_path)
		if is_modify == True:
			debug.warning("deliver-ckeck: " + base_display + " ==> MUST not be modify")
			deliver_availlable = False
		# check the remote branch and the local branch are the same
		#sha_tracking = get_sha1_for_branch(git_repo_path, tracking_remote_branch)
		#sha_current = get_sha1_for_branch(git_repo_path, select_branch)
	if deliver_availlable == False:
		debug.error("deliver-ckeck: Correct the warning to validate the Merge")
		return
	debug.info("deliver-ckeck: ==> All is OK")
	id_element = 0
	for elem in all_project:
		id_element += 1
		base_display = tools.get_list_base_display(id_element, len(all_project), elem)
		debug.info("deliver: ========================================================================")
		debug.info("deliver: == " + base_display)
		debug.info("deliver: ========================================================================")
		
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		version_path_file = os.path.join(git_repo_path, "version.txt")
		if os.path.exists(git_repo_path) == False:
			debug.info("deliver:     ==> No 'version.txt' file ==> not manage release version.")
			continue
		version_description = tools.version_string_to_list(tools.file_read_data(version_path_file))
		debug.info("deliver:     ==> version: " + str(version_description))
		
		select_branch = commands.get_current_branch(git_repo_path)
		
		# get tracking branch
		ret_current_branch_sha1 = commands.get_revision_list_to_branch(git_repo_path, select_branch)
		ret_track_branch_sha1 = commands.get_revision_list_to_branch(git_repo_path, "develop")
		# remove all identical sha1 ==> not needed for this
		have_forward = False
		for elem_sha1 in ret_current_branch_sha1:
			if elem_sha1 not in ret_track_branch_sha1:
				message = commands.get_specific_commit_message(git_repo_path, elem_sha1)
				debug.warning("deliver:      Forward commit: '" + message + "'")
				have_forward = True
		if have_forward == True:
			debug.error("Master must not be forward develop branch")
			continue
		behind_message = ""
		behind_count = 0
		for elem_sha1 in ret_track_branch_sha1:
			if elem_sha1 not in ret_current_branch_sha1:
				message = commands.get_specific_commit_message(git_repo_path, elem_sha1)
				behind_count += 1
				behind_message = message
		if behind_count == 0:
			debug.info("deliver:     ==> Nothing to do (1).")
			continue
		if     behind_count == 1 \
		   and (    behind_message == default_behind_message
		         or behind_message == default_update_message):
			debug.info("deliver:     ==> Nothing to do (2).")
			continue
		for elem_sha1 in ret_track_branch_sha1:
			if elem_sha1 not in ret_current_branch_sha1:
				message = commands.get_specific_commit_message(git_repo_path, elem_sha1)
				debug.info("deliver:      Behind  commit: '" + message + "'")
		# Choice of the new version:
		valid = False
		while valid == False:
			debug.info("update version: curent: " + str(version_description))
			debug.info("    (1) Major version  (change API)")
			debug.info("    (2) Medium version (add feature)")
			debug.info("    (3) Minor version  (Bug fix & doc)")
			input1 = input()
			if input1 in ["1", "2", "3"]:
				valid = True
			else:
				debug.info("!!! Must select in range " + str(["1", "2", "3"]))
		if input1 == "1":
			version_description[0] += 1
			version_description[1] = 0
			version_description[2] = 0
		elif input1 == "2":
			version_description[1] += 1
			version_description[2] = 0
		elif input1 == "3":
			version_description[2] += 1
		debug.info("new version: " + str(version_description))
		
		commands.merge_branch_on_master(git_repo_path, "develop")
		
		# update version file:
		tools.file_write_data(version_path_file, tools.version_to_string(version_description))
		commands.add_file(git_repo_path, version_path_file)
		commands.commit_all(git_repo_path, "[RELEASE] Release v" + tools.version_to_string(version_description))
		commands.tag(git_repo_path, "v" + tools.version_to_string(version_description))
		commands.checkout(git_repo_path, "develop")
		commands.reset_hard(git_repo_path, "master")
		version_description.append("dev")
		tools.file_write_data(version_path_file, tools.version_to_string(version_description))
		commands.add_file(git_repo_path, version_path_file)
		commands.commit_all(git_repo_path, default_update_message)
		commands.checkout(git_repo_path, "master")
		continue
		
		
		is_modify = commands.check_repository_is_modify(git_repo_path)
		list_branch = commands.get_list_branch_all(git_repo_path)
		select_branch = commands.get_current_branch(git_repo_path)
		debug.verbose("List all branch: " + str(list_branch))
		# get tracking branch
		tracking_remote_branch = get_tracking_branch(git_repo_path, argument_remote_name, select_branch)
		if tracking_remote_branch == None:
			debug.info("" + base_display + "\r\t\t\t\t\t\t\t     (NO BRANCH)")
			continue
		
		modify_status = "     "
		if is_modify == True:
			modify_status = " *** "
		
		debug.verbose("select branch = '" + select_branch + "' is modify : " + str(is_modify) + "     track: '" + str(ret_track[1]) + "'")
		
		cmd = "git rev-list " + select_branch
		debug.verbose("execute : " + cmd)
		ret_current_branch_sha1 = multiprocess.run_command(cmd, cwd=git_repo_path)[1].split('\n')
		cmd = "git rev-list " + ret_track[1]
		debug.verbose("execute : " + cmd)
		ret_track_branch_sha1 = multiprocess.run_command(cmd, cwd=git_repo_path)[1].split('\n')
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
		if argument_display_tag == True:
			cmd = "git tag --points-at"
			debug.verbose("execute : " + cmd)
			ret_current_tags = multiprocess.run_command(cmd, cwd=git_repo_path)[1].split('\n')
			debug.verbose("tags found: " + str(ret_current_tags))
			for elem_tag in ret_current_tags:
				if len(tags_comment) != 0:
					tags_comment += ","
				tags_comment += elem_tag
		if len(tags_comment) != 0:
			tags_comment = "\r\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t[" + tags_comment + "]"
		
		#debug.info("" + base_display + "\r\t\t\t\t\t\t\t" + modify_status + "(" + select_branch + " -> " + ret_track[1] + " -> " + elem.select_remote["name"] + "/" + elem.branch + ")")
		debug.info("" + base_display + "\r\t\t\t\t\t\t\t" + modify_status + "(" + select_branch + " -> " + ret_track[1] + ")" + behind_forward_comment + tags_comment)
		if is_modify == True:
			cmd = "git status --short"
			debug.verbose("execute : " + cmd)
			ret_diff = multiprocess.run_command(cmd, cwd=git_repo_path)
			tmp_color_red    = "\033[31m"
			tmp_color_default= "\033[00m"
			debug.info(tmp_color_red + ret_diff[1] + tmp_color_default)
