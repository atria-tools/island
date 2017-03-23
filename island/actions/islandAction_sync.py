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
		debug.error("Sync have not parameter")
	
	# check if .XXX exist (create it if needed)
	if    os.path.exists(env.get_island_path()) == False \
	   or os.path.exists(env.get_island_path_config()) == False \
	   or os.path.exists(env.get_island_path_manifest()) == False:
		debug.error("System already init have an error: missing data: '" + str(env.get_island_path()) + "'")
	
	
	configuration = manifest.load_config()
	
	debug.info("update manifest : '" + str(env.get_island_path_manifest()) + "'")
	# update manifest
	cmd = "git fetch --all"
	multiprocess.run_command_direct(cmd, cwd=env.get_island_path_manifest())
	
	file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration["file"])
	if os.path.exists(file_source_manifest) == False:
		debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")
	
	mani = manifest.Manifest(file_source_manifest)
	
	all_project = mani.get_all_configs()
	debug.info("synchronize : " + str(len(all_project)) + " projects")
	id_element = 0
	for elem in all_project:
		id_element += 1
		debug.info("sync : " + str(id_element) + "/" + str(len(all_project)) + " : " + str(elem.name))
		#debug.debug("elem : " + str(elem))
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		if os.path.exists(git_repo_path) == False:
			# this is a new clone ==> this is easy ...
			#clone the manifest repository
			address_manifest = ""
			
			cmd = "git clone " + elem.select_remote["fetch"] + "/" + elem.name + " --branch " + elem.branch + " --origin " + elem.select_remote["name"] + " " + git_repo_path
			debug.info("clone the repo")
			ret = multiprocess.run_command_direct(cmd)
			if     ret != "" \
			   and ret != False:
				# all is good, ready to get the system work corectly
				debug.info("'" + str(ret) + "'")
				debug.error("Clone repository does not work ... ")
				continue
			#debug.info("plop " + str(elem.select_remote.keys()))
			# check submodule if requested:
			if     elem.select_remote["sync"] == True \
			   and os.path.exists(os.path.join(git_repo_path, ".gitmodules")) == True:
				debug.info("    ==> update submodule")
				cmd = "git submodule init"
				ret = multiprocess.run_command_direct(cmd, cwd=git_repo_path)
				if     ret != "" \
				   and ret != False:
					# all is good, ready to get the system work corectly
					debug.info("'" + str(ret) + "'")
					debug.error("Can not init submodules ... ")
					continue
				cmd = "git submodule update"
				ret = multiprocess.run_command_direct(cmd, cwd=git_repo_path)
				if ret[:16] == "Submodule path '":
					#all is good ...
					debug.info("    " + ret)
				elif     ret != "" \
				     and ret != False:
					# all is good, ready to get the system work corectly
					debug.info("'" + str(ret) + "'")
					debug.error("Can not init submodules ... ")
					continue
				
			continue
		
		if os.path.exists(os.path.join(git_repo_path,".git")) == False:
			# path already exist but it is not used to as a git repo ==> this is an error
			debug.error("path '" + git_repo_path + "' is already existing but not used for a git repository. Clean it and restart")
		
		# simply update the repository ...
		debug.verbose("Fetching project: ")
		# fetch the repository
		cmd = "git fetch " + elem.select_remote["name"]
		debug.verbose("execute : " + cmd)
		multiprocess.run_command_direct(cmd, cwd=git_repo_path)
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
		
		
		if is_modify == True:
			debug.warning("[" + elem.name + "] Not update ==> the repository is modified")
			continue
		
		if ret_track[1] != elem.select_remote["name"] + "/" + elem.branch:
			debug.warning("[" + elem.name + "] Not update ==> the current branch does not track the correct branch : track '" + ret_track[1] + "' instead of '" + elem.select_remote["name"] + "/" + elem.branch + "'")
			continue
		
		debug.info("select branch = '" + select_branch + "' is modify : " + str(is_modify) + "     track: '" + str(ret_track[1]) + "'")
		# check submodule if requested:
		if     elem.select_remote["sync"] == True \
		   and os.path.exists(os.path.join(git_repo_path, ".gitmodules")) == True:
			debug.info("    ==> sync submodule")
			cmd = "git submodule sync"
			ret = multiprocess.run_command_direct(cmd, cwd=git_repo_path)
			if     ret != "" \
			   and ret != False:
				# all is good, ready to get the system work corectly
				debug.info("'" + ret + "'")
				debug.error("Can not sync submodules ... ")
				continue
			"""
			cmd = "git submodule init"
			ret = multiprocess.run_command_direct(cmd, cwd=git_repo_path)
			if     ret != "" \
			   and ret != False:
				# all is good, ready to get the system work corectly
				debug.info("'" + ret + "'")
				debug.error("Can not init submodules ... ")
				continue
			cmd = "git submodule update"
			ret = multiprocess.run_command_direct(cmd, cwd=git_repo_path)
			if ret[:16] == "Submodule path '":
				#all is good ...
				debug.info("    " + ret)
			elif     ret != "" \
			     and ret != False:
				# all is good, ready to get the system work corectly
				debug.info("'" + ret + "'")
				debug.error("Can not init submodules ... ")
				continue
			"""
