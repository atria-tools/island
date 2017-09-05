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
from island import config
from island import multiprocess
from island import manifest
import os


def help():
	return "plop"





def execute(arguments):
	debug.info("execute:")
	origin_name = ""
	for elem in arguments:
		debug.info("    '" + str(elem.get_arg()) + "'")
	if len(arguments) == 0:
		pass
	elif len(arguments) == 1:
		origin_name = arguments[0].get_arg()
		debug.info("try fetch remote if exist: '" + str(origin_name) + "'")
	else:
		debug.error("Sync have not parameter")
	
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
		debug.info("fetch : " + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name))
		#debug.debug("elem : " + str(elem))
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		if os.path.exists(git_repo_path) == False:
			debug.error("can not fetch project that not exist")
			continue
		
		if os.path.exists(os.path.join(git_repo_path,".git")) == False:
			# path already exist but it is not used to as a git repo ==> this is an error
			debug.error("path '" + git_repo_path + "' is already existing but not used for a git repository. Clean it and restart")
		
		# simply update the repository ...
		debug.verbose("Fetching project: ")
		# fetch the repository
		if origin_name == "":
			cmd = "git fetch " + elem.select_remote["name"]
		else:
			cmd = "git fetch " + origin_name
		debug.verbose("execute : " + cmd)
		multiprocess.run_command_direct(cmd, cwd=git_repo_path)
		
