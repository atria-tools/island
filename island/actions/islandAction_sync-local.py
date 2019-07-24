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
	return "Update all the branche to the trackin branch in local (no remote access)"


def add_specific_arguments(my_args, section):
	#my_args.add("d", "download", haveParam=False, desc="Just download the 'not download' repository")
	pass

def execute(arguments):
	for elem in arguments:
		"""if elem.get_option_name() == "download":
			just_download = True
			debug.info("find remote name: '" + elem.get_arg() + "'")
		else:
			
		"""
		debug.error("SYNC Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")
	
	# check if .XXX exist (create it if needed)
	if    os.path.exists(env.get_island_path()) == False \
	   or os.path.exists(env.get_island_path_config()) == False \
	   or os.path.exists(env.get_island_path_manifest()) == False:
		debug.error("System already init have an error: missing data: '" + str(env.get_island_path()) + "'")
	
	configuration = config.Config()
	
	# TODO: Load Old manifect to check diff ...
	
	#debug.info("update manifest : '" + str(env.get_island_path_manifest()) + "'")
	#is_modify_manifest = commands.check_repository_is_modify(env.get_island_path_manifest())
	#if is_modify_manifest == True:
	#	commands.fetch(env.get_island_path_manifest(), "origin")
	#else:
	#	commands.pull(env.get_island_path_manifest(), "origin")
	
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
		debug.info("----------------------------------------------------------------")
		debug.info("sync-local: " + base_display)
		#debug.debug("elem : " + str(elem))
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		if os.path.exists(git_repo_path) == False:
			# The Repository does not exist ==> Nothing to do...
			debug.warning("sync-local:    ==> Not download")
			continue
		
		if os.path.exists(os.path.join(git_repo_path,".git")) == False:
			# path already exist but it is not used to as a git repo ==> this is an error
			debug.warning("sync-local: is already existing but not used for a git repository. Remove it and sync")
		# simply update the repository ...
		debug.verbose("Check modify:")
		is_modify = commands.check_repository_is_modify(git_repo_path)
		if is_modify == True:
			# fetch the repository
			debug.warning("sync-local: Not update ==> the repository is modified (pass through)")
			continue
		debug.verbose("Check tracking and local branch:")
		# get tracking branch
		ret_track = commands.get_current_tracking_branch(git_repo_path)
		select_branch = commands.get_current_branch(git_repo_path)
		debug.info("sync-local: check: " + select_branch + " ==> " + ret_track)
		debug.verbose("Check forward:")
		is_forward = commands.is_forward(git_repo_path, ret_track)
		if is_forward == True:
			# fetch the repository
			debug.warning("sync-local: Not update ==> the repository is forward the remote branch " + str(commands.get_forward(git_repo_path, ret_track)))
			continue
		debug.verbose("Check behind:")
		is_behind = commands.is_behind(git_repo_path, ret_track)
		if is_behind == False:
			# fetch the repository
			debug.info("sync-local: Nothing to do.")
			continue
		
		debug.info("sync-local: Reset to " + ret_track)
		commands.reset_hard(git_repo_path, ret_track)
		