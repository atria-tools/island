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
	_my_args.add("r", "remote", haveParam=True, desc="Name of the remote server")
	
	_my_args.add("t", "tags", haveParam=False, desc="Display if the commit is on a tag (and display it)")


def execute(arguments):
	argument_remote_name = ""
	argument_display_tag = False
	for elem in arguments:
		if elem.get_option_name() == "remote":
			debug.info("find remote name: '" + elem.get_arg() + "'")
			argument_remote_name = elem.get_arg()
		elif elem.get_option_name() == "tags":
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
	is_modify_manifest = commands.check_repository_is_modify(env.get_island_path_manifest())
	if is_modify_manifest == True:
		debug.info("!!!!!!!!!!!! MANIFEST is modify !!!!!!!!")
	
	all_project = mani.get_all_configs()
	debug.info("status of: " + str(len(all_project)) + " projects")
	id_element = 0
	for elem in all_project:
		id_element += 1
		base_display = tools.get_list_base_display(id_element, len(all_project), elem)
		debug.verbose("status : " + base_display)
		#debug.debug("elem : " + str(elem))
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		if os.path.exists(git_repo_path) == False:
			debug.info(base_display + "\r\t\t\t\t\t\t\t\t\t" + "     (not download)")
			continue
		
		is_modify = commands.check_repository_is_modify(git_repo_path)
		list_branch = commands.get_list_branch_all(git_repo_path)
		select_branch = commands.get_current_branch(git_repo_path)
		debug.verbose("List all branch: " + str(list_branch))
		# get tracking branch
		tracking_remote_branch = commands.get_tracking_branch(git_repo_path, argument_remote_name, select_branch)
		if tracking_remote_branch == None:
			debug.info(base_display + "\r\t\t\t\t\t\t\t     (NO BRANCH)")
			continue
		
		modify_status = "     "
		if is_modify == True:
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
		if argument_display_tag == True:
			ret_current_tags = commands.get_tags_current(git_repo_path)
			debug.verbose("tags found: " + str(ret_current_tags))
			for elem_tag in ret_current_tags:
				if len(tags_comment) != 0:
					tags_comment += ","
				tags_comment += elem_tag
		if len(tags_comment) != 0:
			tags_comment = "\r\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t[" + tags_comment + "]"
		
		debug.info(base_display + "\r\t\t\t\t\t\t\t" + modify_status + "(" + select_branch + " -> " + tracking_remote_branch + ")" + behind_forward_comment + tags_comment)
		if is_modify == True:
			cmd = "git status --short"
			debug.verbose("execute : " + cmd)
			ret_diff = multiprocess.run_command(cmd, cwd=git_repo_path)
			tmp_color_red    = "\033[31m"
			tmp_color_default= "\033[00m"
			debug.info(tmp_color_red + ret_diff[1] + tmp_color_default)
