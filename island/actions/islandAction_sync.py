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
	return "Syncronize all the repository referenced"


def add_specific_arguments(my_args, section):
	my_args.add("d", "download", haveParam=False, desc="Just download the 'not download' repository")

def execute(arguments):
	just_download = False
	for elem in arguments:
		if elem.get_option_name() == "download":
			just_download = True
			debug.info("find remote name: '" + elem.get_arg() + "'")
		else:
			debug.error("SYNC Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")
	
	# check if .XXX exist (create it if needed)
	if    os.path.exists(env.get_island_path()) == False \
	   or os.path.exists(env.get_island_path_config()) == False \
	   or os.path.exists(env.get_island_path_manifest()) == False:
		debug.error("System already init have an error: missing data: '" + str(env.get_island_path()) + "'")
	
	configuration = config.Config()
	
	# TODO: Load Old manifect to check diff ...
	
	debug.info("update manifest : '" + str(env.get_island_path_manifest()) + "'")
	is_modify_manifest = commands.check_repository_is_modify(env.get_island_path_manifest())
	if is_modify_manifest == True:
		commands.fetch(env.get_island_path_manifest(), "origin")
	else:
		commands.pull(env.get_island_path_manifest(), "origin")
	
	file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
	if os.path.exists(file_source_manifest) == False:
		debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")
	
	mani = manifest.Manifest(file_source_manifest)
	
	all_project = mani.get_all_configs()
	debug.info("synchronize : " + str(len(all_project)) + " projects")
	id_element = 0
	for elem in all_project:
		id_element += 1
		base_display = tools.get_list_base_display(id_element, len(all_project), elem)
		debug.info("sync : " + base_display)
		tools.wait_for_server_if_needed()
		#debug.debug("elem : " + str(elem))
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		if os.path.exists(git_repo_path) == False:
			# this is a new clone ==> this is easy ...
			#clone the manifest repository
			address_manifest = ""
			### example git@git.plouf.com:basic_folder
			cmd = "git clone " + elem.select_remote["fetch"]
			if     elem.select_remote["fetch"][0:4] == "git@" \
			   and len(elem.select_remote["fetch"][4:].split(":")) <= 1:
				cmd += ":"
			else:
				cmd += "/"
			cmd += elem.name + " --branch " + elem.branch + " --origin " + elem.select_remote["name"] + " " + git_repo_path
			debug.info("clone the repo")
			ret = multiprocess.run_command_direct(cmd)
			if     ret != "" \
			   and ret != False:
				# all is good, ready to get the system work corectly
				debug.info("'" + str(ret) + "'")
				debug.error("Clone repository does not work ... ")
				continue
			# add global mirror list
			for mirror in elem.select_remote["mirror"]:
				debug.verbose("Add global mirror: " + str(mirror))
				cmd = "git remote add " + mirror["name"] + " " + mirror["fetch"]
				if mirror["fetch"][0:4] == "git@":
					cmd += ":"
				else:
					cmd += "/"
				cmd += elem.name
				ret = multiprocess.run_command_direct(cmd, cwd=git_repo_path)
				if     ret != "" \
				   and ret != False:
					# all is good, ready to get the system work corectly
					debug.info("'" + str(ret) + "'")
					debug.warning("Can not add global mirror ... ")
					continue
				debug.verbose("Add global mirror: " + str(mirror) + " (done)")
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
		
		if just_download == True:
			debug.info("SYNC: Already downloaded")
			continue
		
		if os.path.exists(os.path.join(git_repo_path,".git")) == False:
			# path already exist but it is not used to as a git repo ==> this is an error
			debug.error("path '" + git_repo_path + "' is already existing but not used for a git repository. Clean it and restart")
		
		# simply update the repository ...
		debug.verbose("Fetching project: ")
		
		# get tracking branch
		ret_track = commands.get_current_tracking_branch(git_repo_path)
		is_modify = commands.check_repository_is_modify(git_repo_path)
		select_branch = commands.get_current_branch(git_repo_path)
		
		if is_modify == True:
			# fetch the repository
			commands.fetch(git_repo_path, elem.select_remote["name"])
			debug.warning("[" + elem.name + "] Not update ==> the repository is modified (just fetch)")
			continue
		commands.pull(git_repo_path, elem.select_remote["name"])
		
		debug.verbose("select branch = '" + select_branch + "' track: '" + str(ret_track) + "'")
		# check submodule if requested:
		if     elem.select_remote["sync"] == True \
		   and os.path.exists(os.path.join(git_repo_path, ".gitmodules")) == True:
			debug.info("    ==> sync submodule")
			commands.submodule_sync(git_repo_path)
			