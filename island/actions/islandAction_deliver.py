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
from island import commands
import os


def help():
	return "Deliver the current repository (develop & master MUST be up to date and you MUST be on master)"


def add_specific_arguments(_my_args, _section):
	pass

default_behind_message = "[DEV] update dev tag version"
default_update_message = "[VERSION] update dev tag version"

def execute(arguments):
	argument_remote_name = ""
	for elem in arguments:
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
	debug.info("Check if all project are on master: " + str(len(all_project)) + " projects")
	id_element = 0
	deliver_availlable = True
	for elem in all_project:
		id_element += 1
		base_display = tools.get_list_base_display(id_element, len(all_project), elem)
		debug.verbose("deliver-ckeck: " + base_display)
		# Check the repo exist
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		if os.path.exists(git_repo_path) == False:
			debug.warning("deliver-ckeck: " + base_display + " ==> MUST be download")
			deliver_availlable = False
			continue
		# check if we are on "master"
		select_branch = commands.get_current_branch(git_repo_path)
		if select_branch != "master":
			debug.warning("deliver-ckeck: " + base_display + " ==> MUST be on master")
			deliver_availlable = False
		# check if we have a remote traking branch
		tracking_remote_branch = commands.get_tracking_branch(git_repo_path, argument_remote_name, select_branch)
		if tracking_remote_branch == None:
			debug.warning("deliver-ckeck: " + base_display + " ==> MUST have a remote tracking branch")
			deliver_availlable = False
		# check if we have a local branch
		list_branch_local = commands.get_list_branch_local(git_repo_path)
		if "develop" not in list_branch_local:
			debug.warning("deliver-ckeck: " + base_display + " ==> MUST have local branch named develop")
			deliver_availlable = False
		# TODO: check develop is up to date
		
		# check if the curent repo is modify
		is_modify = commands.check_repository_is_modify(git_repo_path)
		if is_modify == True:
			debug.warning("deliver-ckeck: " + base_display + " ==> MUST not be modify")
			deliver_availlable = False
		# check the remote branch and the local branch are the same
		#sha_tracking = get_sha1_for_branch(git_repo_path, tracking_remote_branch)
		#sha_current = get_sha1_for_branch(git_repo_path, select_branch)
	if deliver_availlable == False:
		debug.error("deliver-ckeck: Correct the warning to validate the Merge")
		return
	debug.info("deliver-ckeck: ==> All is OK")
	id_element = 0
	for elem in all_project:
		id_element += 1
		base_display = tools.get_list_base_display(id_element, len(all_project), elem)
		debug.info("deliver: ========================================================================")
		debug.info("deliver: == " + base_display)
		debug.info("deliver: ========================================================================")
		
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		version_path_file = os.path.join(git_repo_path, "version.txt")
		add_in_version_management = False
		if os.path.exists(version_path_file) == False:
			debug.info("deliver:     ==> No 'version.txt' file ==> not manage release version....")
			# Action to do:
			valid = False
			while valid == False:
				debug.info("Create a new version: (0.0.0)")
				debug.info("    (1) Add in managing version")
				debug.info("    (2) Do NOTHING & continue")
				input1 = input()
				if input1 in ["1", "2"]:
					valid = True
				else:
					debug.info("!!! Must select in range " + str(["1", "2"]))
			if input1 == "1":
				version_description = [0, 0, 0]
				add_in_version_management = True
			elif input1 == "2":
				debug.info("Continue Not managing for this repository")
				continue
			else:
				debug.warning("An error occured for this repository")
				continue
		else:
			version_description = tools.version_string_to_list(tools.file_read_data(version_path_file))
		debug.info("deliver:     ==> version: " + str(version_description))
		
		select_branch = commands.get_current_branch(git_repo_path)
		
		# get tracking branch
		ret_current_branch_sha1 = commands.get_revision_list_to_branch(git_repo_path, select_branch)
		ret_track_branch_sha1 = commands.get_revision_list_to_branch(git_repo_path, "develop")
		# remove all identical sha1 ==> not needed for this
		have_forward = False
		for elem_sha1 in ret_current_branch_sha1:
			if elem_sha1 not in ret_track_branch_sha1:
				message = commands.get_specific_commit_message(git_repo_path, elem_sha1)
				debug.warning("deliver:      Forward commit: '" + message + "'")
				have_forward = True
		if have_forward == True:
			debug.error("Master must not be forward develop branch")
			continue
		behind_message = ""
		behind_count = 0
		for elem_sha1 in ret_track_branch_sha1:
			if elem_sha1 not in ret_current_branch_sha1:
				message = commands.get_specific_commit_message(git_repo_path, elem_sha1)
				behind_count += 1
				behind_message = message
		if behind_count == 0 and add_in_version_management == False:
			debug.info("deliver:     ==> Nothing to do (1).")
			continue
		if     behind_count == 1 \
		   and (    behind_message == default_behind_message
		         or behind_message == default_update_message):
			debug.info("deliver:     ==> Nothing to do (2).")
			continue
		for elem_sha1 in ret_track_branch_sha1:
			if elem_sha1 not in ret_current_branch_sha1:
				message = commands.get_specific_commit_message(git_repo_path, elem_sha1)
				debug.info("deliver:      Behind  commit: '" + message + "'")
		# Choice of the new version:
		valid = False
		while valid == False:
			debug.info("update version: curent: " + str(version_description))
			debug.info("    (1) Major version  (change API)")
			debug.info("    (2) Medium version (add feature)")
			debug.info("    (3) Minor version  (Bug fix & doc)")
			debug.info("    (4) Do not release & continue")
			input1 = input()
			if input1 in ["1", "2", "3", "4"]:
				valid = True
			else:
				debug.info("!!! Must select in range " + str(["1", "2", "3", "4"]))
		if input1 == "1":
			version_description[0] += 1
			version_description[1] = 0
			version_description[2] = 0
		elif input1 == "2":
			version_description[1] += 1
			version_description[2] = 0
		elif input1 == "3":
			version_description[2] += 1
		elif input1 == "4":
			debug.info("No release for this repository")
			continue
		else:
			debug.warning("An error occured for this repository")
			continue
		debug.info("new version: " + str(version_description))
		
		commands.merge_branch_on_master(git_repo_path, "develop")
		
		# update version file:
		tools.file_write_data(version_path_file, tools.version_to_string(version_description))
		commands.add_file(git_repo_path, version_path_file)
		commands.commit_all(git_repo_path, "[RELEASE] Release v" + tools.version_to_string(version_description))
		commands.tag(git_repo_path, "v" + tools.version_to_string(version_description))
		commands.checkout(git_repo_path, "develop")
		commands.reset_hard(git_repo_path, "master")
		version_description.append("dev")
		tools.file_write_data(version_path_file, tools.version_to_string(version_description))
		commands.add_file(git_repo_path, version_path_file)
		commands.commit_all(git_repo_path, default_update_message)
		commands.checkout(git_repo_path, "master")
		