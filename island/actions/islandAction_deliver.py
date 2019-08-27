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
import status
import os


##
## @brief Get the global description of the current action
## @return (string) the description string (fist line if reserved for the overview, all is for the specific display)
##
def help():
	return "Deliver the current repository (develop & master MUST be up to date and you MUST be on master)"

##
## @brief Add argument to the specific action
## @param[in,out] my_args (death.Arguments) Argument manager
## @param[in] section Name of the currect action
##
def add_specific_arguments(_my_args, _section):
	pass

##
## @brief Execute the action required.
##
## @return error value [0 .. 50] the <0 value is reserved system ==> else, what you want.
##         None : No error (return program out 0)
##         -10 : ACTION is not existing
##         -11 : ACTION execution system error
##         -12 : ACTION Wrong parameters
##
def execute(_arguments):
	argument_remote_name = ""
	for elem in _arguments:
		debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")
	
	# check system is OK
	manifest.check_lutin_is_init()
	
	configuration = config.get_unique_config()
	
	file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
	if os.path.exists(file_source_manifest) == False:
		debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")
	
	mani = manifest.Manifest(file_source_manifest)
	
	destination_branch = mani.deliver_master
	source_branch = mani.deliver_develop
	
	
	all_project = mani.get_all_configs()
	debug.info("Check if all project are on master: " + str(len(all_project)) + " projects")
	id_element = 0
	deliver_availlable = True
	for elem in all_project:
		id_element += 1
		base_display = tools.get_list_base_display(id_element, len(all_project), elem)
		debug.verbose("deliver-ckeck: " + base_display)
		if status.deliver_check(elem, argument_remote_name, id_element, base_display, source_branch, destination_branch) == False:
			deliver_availlable = False
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
		# Check the validity of the version,
		version_description, add_in_version_management = status.get_current_version_repo(git_repo_path)
		if version_description == None:
			continue
		debug.info("deliver:     ==> version: " + str(version_description))
		
		# go to the dev branch
		select_branch = commands.get_current_branch(git_repo_path)
		
		# Checkout destination branch:
		commands.checkout(git_repo_path, destination_branch)
		
		# create new repo tag
		new_version_description = status.create_new_version_repo(git_repo_path, version_description, add_in_version_management, source_branch, destination_branch)
		debug.info("new version: " + str(new_version_description))
		if new_version_description == None:
			continue
		# merge branch
		if mani.deliver_mode == "merge":
			merge_force = True
		else:
			merge_force = False
		commands.merge_branch_on_master(git_repo_path, source_branch, merge_force, branch_destination=destination_branch)
		
		version_path_file = os.path.join(git_repo_path, "version.txt")
		# update version file:
		tools.file_write_data(version_path_file, tools.version_to_string(new_version_description))
		commands.add_file(git_repo_path, version_path_file)
		commands.commit_all(git_repo_path, "[RELEASE] Release v" + tools.version_to_string(new_version_description))
		commands.tag(git_repo_path, "v" + tools.version_to_string(new_version_description))
		commands.checkout(git_repo_path, source_branch)
		commands.reset_hard(git_repo_path, destination_branch)
		new_version_description.append("dev")
		tools.file_write_data(version_path_file, tools.version_to_string(new_version_description))
		commands.add_file(git_repo_path, version_path_file)
		commands.commit_all(git_repo_path, status.default_update_message)
		commands.checkout(git_repo_path, destination_branch)
		