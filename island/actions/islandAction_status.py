#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license MPL v2.0 (see license file)
##

from island import debug
from island import tools
from island import env
from island import multiprocess
from island import manifest
import os


def help():
	return "plop"





def execute(arguments):
	debug.info("execute:")
	for elem in arguments:
		debug.info("    '" + str(elem.get_arg()) + "'")
	if len(arguments) != 0:
		debug.error("status have not parameter")
	
	# check if .XXX exist (create it if needed)
	if    os.path.exists(env.get_island_path()) == False \
	   or os.path.exists(env.get_island_path_config()) == False \
	   or os.path.exists(env.get_island_path_manifest()) == False:
		debug.error("System already init have an error: missing data: '" + str(env.get_island_path()) + "'")
	
	configuration = manifest.load_config()
	
	file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration["file"])
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
		cmd = "git branch"
		debug.verbose("execute : " + cmd)
		ret_branch = multiprocess.run_command(cmd, cwd=git_repo_path)
		
		# get  tracking branch
		cmd = "git rev-parse --abbrev-ref --symbolic-full-name @{u}"
		debug.verbose("execute : " + cmd)
		ret_track = multiprocess.run_command(cmd, cwd=git_repo_path)
		
		is_modify = True
		if ret_diff[0] == 0:
			is_modify = False
		
		list_branch = ret_branch[1].split('\n')
		list_branch2 = []
		select_branch = ""
		for elem_branch in list_branch:
			if elem_branch[:2] == "* ":
				list_branch2.append([elem_branch[2:], True])
				select_branch = elem_branch[2:]
			else:
				list_branch2.append([elem_branch[2:], False])
		
		modify_status = "     "
		if is_modify == True:
			modify_status = " *** "
		
		debug.verbose("select branch = '" + select_branch + "' is modify : " + str(is_modify) + "     track: '" + str(ret_track[1]) + "'")
		
		#debug.info("" + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + "\r\t\t\t\t\t\t\t" + modify_status + "(" + select_branch + " -> " + ret_track[1] + " -> " + elem.select_remote["name"] + "/" + elem.branch + ")")
		debug.info("" + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + "\r\t\t\t\t\t\t\t" + modify_status + "(" + select_branch + " -> " + ret_track[1] + ")")
		if is_modify == True:
			cmd = "git status --short"
			debug.verbose("execute : " + cmd)
			ret_diff = multiprocess.run_command(cmd, cwd=git_repo_path)
			tmp_color_red    = "\033[31m"
			tmp_color_default= "\033[00m"
			debug.info(tmp_color_red + ret_diff[1] + tmp_color_default)
