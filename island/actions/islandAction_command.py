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
	return "write the command you want to be executed in every repository"

def execute(arguments):
	cmd = ""
	for elem in arguments:
		debug.info("Get data element: " + str(elem.get_arg()))
		cmd += elem.get_arg() + " "
	
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
		debug.info("------------------------------------------")
		id_element += 1
		debug.info("execute command : " + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name))
		#debug.debug("elem : " + str(elem))
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		if os.path.exists(git_repo_path) == False:
			debug.info("" + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name) + "\r\t\t\t\t\t\t\t\t\t" + "     (not download)")
			continue
		
		debug.verbose("execute : " + cmd)
		ret = multiprocess.run_command(cmd, cwd=git_repo_path)
		if ret[0] == 0:
			debug.info("ret=" + ret[1])
			debug.info("err=" + ret[2])
		else:
			debug.info("Execution ERROR")
		