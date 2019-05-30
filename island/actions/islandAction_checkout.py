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
from island import config
from island import multiprocess
from island import manifest
from island import commands
import os


def help():
	return "Ckeckout a specific branch in all repository"

def add_specific_arguments(my_args, section):
	my_args.add("r", "remote", haveParam=True, desc="Name of the remote server")
	my_args.add_arg("branch", optionnal=False, desc="Branch to checkout")

def execute(arguments):
	argument_remote_name = ""
	branch_to_checkout = ""
	for elem in arguments:
		if elem.get_option_name() == "remote":
			debug.info("find remote name: '" + elem.get_arg() + "'")
			argument_remote_name = elem.get_arg()
		elif elem.get_option_name() == "branch":
			branch_to_checkout = elem.get_arg()
		else:
			debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")
	
	# check if .XXX exist (create it if needed)
	if    os.path.exists(env.get_island_path()) == False \
	   or os.path.exists(env.get_island_path_config()) == False \
	   or os.path.exists(env.get_island_path_manifest()) == False:
		debug.error("System already init have an error: missing data: '" + str(env.get_island_path()) + "'")
	
	configuration = config.Config()
	
	# update the local configuration file:
	configuration.set_branch(branch_to_checkout)
	configuration.store()
	
	file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
	if os.path.exists(file_source_manifest) == False:
		debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")
	
	mani = manifest.Manifest(file_source_manifest)
	
	all_project = mani.get_all_configs()
	debug.info("checkout of: " + str(len(all_project)) + " projects")
	id_element = 0
	for elem in all_project:
		id_element += 1
		base_display = tools.get_list_base_display(id_element, len(all_project), elem)
		debug.verbose("checkout : " + base_display)
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		if os.path.exists(git_repo_path) == False:
			debug.warning("checkout " + base_display + " ==> repository does not exist ...")
			continue
		
		# check if the repository is modify
		is_modify = commands.check_repository_is_modify(git_repo_path)
		if is_modify == True:
			debug.warning("checkout " + base_display + " ==> modify data can not checkout new branch")
			continue
		
		list_branch_local = commands.get_list_branch_local(git_repo_path)
		select_branch = commands.get_current_branch(git_repo_path)
		
		# check if we are on the good branch:
		if branch_to_checkout == select_branch:
			debug.info("checkout " + base_display + " ==> No change already on good branch")
			continue
		
		# check if we have already checkout the branch before
		debug.verbose("      check : " + branch_to_checkout + "    in " + str(list_branch_local))
		if branch_to_checkout in list_branch_local:
			cmd = "git checkout " + branch_to_checkout
			debug.verbose("execute : " + cmd)
			ret = multiprocess.run_command(cmd, cwd=git_repo_path)
			if     ret[0] != 0 \
			   and ret[1] != "" \
			   and ret != False:
				debug.info("'" + str(ret) + "'")
				debug.error("checkout " + base_display + " ==> Can not checkout to the correct branch")
				continue
			debug.info("checkout " + base_display + " ==> switch branch")
			# TODO : Check the number of commit to the origin/XXX branch ....
			continue
		
		# Check if the remote branch exist ...
		list_branch_remote = commands.get_list_branch_remote(git_repo_path)
		if elem.select_remote["name"] + "/" + branch_to_checkout in list_branch_remote:
			debug.info("    ==> find ...")
		else:
			debug.info("checkout " + base_display + " ==> NO remote branch")
			continue
		
		# checkout the new branch:
		cmd = "git checkout --quiet " + elem.select_remote["name"] + "/" + branch_to_checkout + " -b " + branch_to_checkout
		# + " --track " + elem.select_remote["name"] + "/" + branch_to_checkout
		debug.verbose("execute : " + cmd)
		ret = multiprocess.run_command(cmd, cwd=git_repo_path)
		if     ret[1] != "" \
		   and ret != False:
			debug.info("'" + str(ret) + "'")
			debug.error("checkout " + base_display + " ==> Can not checkout to the correct branch")
			continue
		debug.info("checkout " + base_display + " ==> create new branch")
		continue



