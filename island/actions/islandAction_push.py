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
import os


def help():
	return "Push all repository to the upper server"




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
	
	if env.get_fetch_manifest() == True:
		debug.info("update manifest : '" + str(env.get_island_path_manifest()) + "'")
		# update manifest
		cmd = "git fetch --all"
		multiprocess.run_command_direct(cmd, cwd=env.get_island_path_manifest())
	
	file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
	if os.path.exists(file_source_manifest) == False:
		debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")
	mani = manifest.Manifest(file_source_manifest)
	
	all_project = mani.get_all_configs()
	debug.info("fetch : " + str(len(all_project)) + " projects")
	id_element = 0
	for elem in all_project:
		id_element += 1
		debug.info("push: " + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name))
		#debug.debug("elem : " + str(elem))
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		if os.path.exists(git_repo_path) == False:
			debug.error("can not push project that not exist")
			continue
		
		if os.path.exists(os.path.join(git_repo_path,".git")) == False:
			# path already exist but it is not used to as a git repo ==> this is an error
			debug.error("path '" + git_repo_path + "' exist but not used for a git repository. Clean it and restart")
		
		# get the current branch:
		# get local branch
		cmd = "git branch -a"
		debug.verbose("execute : " + cmd)
		ret_branch = multiprocess.run_command(cmd, cwd=git_repo_path)
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
		
		# simply update the repository ...
		debug.verbose("Push project: ")
		# fetch the repository
		cmd = "git push"
		if argument_remote_name != "":
			cmd += " " + argument_remote_name
		else:
			cmd += " " + elem.select_remote["name"]
		cmd += " " + select_branch + ":" + select_branch
		debug.info("execute : " + cmd)
		multiprocess.run_command_direct(cmd, cwd=git_repo_path)
		
