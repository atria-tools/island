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
import os


def help():
	return "plop"


def add_specific_arguments(my_args, section):
	my_args.add("r", "remote", haveParam=True, desc="Name of the remote server")


def execute(arguments):
	argument_remote_name = ""
	for elem in arguments:
		if elem.get_option_name() == "remote":
			debug.info("find remote name: '" + elem.get_arg() + "'")
			argument_remote_name = elem.get_arg()
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
	debug.info("status of: " + str(len(all_project)) + " projects")
	id_element = 0
	for elem in all_project:
		id_element += 1
		debug.verbose("status : " + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name))
		#debug.debug("elem : " + str(elem))
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		if os.path.exists(git_repo_path) == False:
			debug.info("" + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + "\r\t\t\t\t\t\t\t\t\t" + "     (not download)")
			continue
		
		# check if the repository is modify
		cmd = "git diff --quiet"
		debug.verbose("execute : " + cmd)
		ret_diff = multiprocess.run_command(cmd, cwd=git_repo_path)
		# get local branch
		cmd = "git branch -a"
		debug.verbose("execute : " + cmd)
		ret_branch = multiprocess.run_command(cmd, cwd=git_repo_path)
		
		is_modify = True
		if ret_diff[0] == 0:
			is_modify = False
		
		list_branch = ret_branch[1].split('\n')
		list_branch2 = []
		list_branch3 = []
		select_branch = ""
		for elem_branch in list_branch:
			if len(elem_branch.split(" -> ")) != 1:
				continue
			if elem_branch[2:10] == "remotes/":
				elem_branch = elem_branch[:2] + elem_branch[10:]
			if elem_branch[:2] == "* ":
				list_branch2.append([elem_branch[2:], True])
				select_branch = elem_branch[2:]
			else:
				list_branch2.append([elem_branch[2:], False])
			list_branch3.append(elem_branch[2:])
		debug.verbose("List all branch: " + str(list_branch3))
		# get tracking branch
		if argument_remote_name == "":
			cmd = "git rev-parse --abbrev-ref --symbolic-full-name @{u}"
			debug.verbose("execute : " + cmd)
			ret_track = multiprocess.run_command(cmd, cwd=git_repo_path)
		else:
			debug.extreme_verbose("check if exist " + argument_remote_name + "/" + select_branch + " in " + str(list_branch3))
			if argument_remote_name + "/" + select_branch not in list_branch3:
				debug.info("" + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + "\r\t\t\t\t\t\t\t     (NO BRANCH)")
				continue;
			else:
				ret_track = [True, argument_remote_name + "/" + select_branch]
		
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
		#debug.info("" + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + "\r\t\t\t\t\t\t\t" + modify_status + "(" + select_branch + " -> " + ret_track[1] + " -> " + elem.select_remote["name"] + "/" + elem.branch + ")")
		debug.info("" + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + "\r\t\t\t\t\t\t\t" + modify_status + "(" + select_branch + " -> " + ret_track[1] + ")" + behind_forward_comment)
		if is_modify == True:
			cmd = "git status --short"
			debug.verbose("execute : " + cmd)
			ret_diff = multiprocess.run_command(cmd, cwd=git_repo_path)
			tmp_color_red    = "\033[31m"
			tmp_color_default= "\033[00m"
			debug.info(tmp_color_red + ret_diff[1] + tmp_color_default)
