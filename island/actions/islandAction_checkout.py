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
	if len(arguments) != 1:
		debug.error("checkout: missing argument to select the new branch ...")
	branch_to_checkout = ""
	for elem in arguments:
		if elem.get_option_name() == "":
			if branch_to_checkout != "":
				debug.error("checkout branch already set : '" + branch_to_checkout + "' !!! '" + elem.get_arg() + "'")
			branch_to_checkout = elem.get_arg()
		else:
			debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")
	
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
	debug.info("checkout of: " + str(len(all_project)) + " projects")
	id_element = 0
	for elem in all_project:
		id_element += 1
		debug.verbose("checkout : " + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name))
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		if os.path.exists(git_repo_path) == False:
			debug.warning("checkout " + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + " ==> repository does not exist ...")
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
		
		if is_modify == True:
			debug.warning("checkout " + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + " ==> modify data can not checkout new branch")
			continue
		
		list_branch = ret_branch[1].split('\n')
		list_branch2 = []
		select_branch = ""
		for elem_branch in list_branch:
			if elem_branch[:2] == "* ":
				list_branch2.append([elem_branch[2:], True])
				select_branch = elem_branch[2:]
			else:
				list_branch2.append([elem_branch[2:], False])
		
		
		# check if we are on the good branch:
		if branch_to_checkout == select_branch:
			debug.info("checkout " + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + " ==> No change already on good branch")
			continue
		
		# check if we have already checkout the branch before
		if branch_to_checkout in list_branch2:
			cmd = "git checkout " + branch_to_checkout
			debug.verbose("execute : " + cmd)
			ret = multiprocess.run_command(cmd, cwd=git_repo_path)
			if     ret[1] != "" \
			   and ret != False:
				debug.info("'" + ret + "'")
				debug.error("checkout " + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + " ==> Can not checkout to the corest branch")
				continue
			debug.info("checkout " + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + " ==> switch branch")
			# TODO : Check the number of commit to the origin/XXX branch ....
			
			continue
			
		
		# TODO: Check if the remote branch exist ...
		
		
		# checkout the new branch:
		cmd = "git checkout --quiet " + elem.select_remote["name"] + "/" + branch_to_checkout + " -b " + branch_to_checkout
		# + " --track " + elem.select_remote["name"] + "/" + branch_to_checkout
		debug.verbose("execute : " + cmd)
		ret = multiprocess.run_command(cmd, cwd=git_repo_path)
		if     ret[1] != "" \
		   and ret != False:
			debug.info("'" + str(ret) + "'")
			debug.error("checkout " + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + " ==> Can not checkout to the correct branch")
			continue
		debug.info("checkout " + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + " ==> create new branch")
		continue


