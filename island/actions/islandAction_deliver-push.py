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
	return "Push a delover (develop & master & tag) on the remotre server"

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
	
	file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
	if os.path.exists(file_source_manifest) == False:
		debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")
	mani = manifest.Manifest(file_source_manifest)
	
	all_project = mani.get_all_configs()
	debug.info("fetch : " + str(len(all_project)) + " projects")
	id_element = 0
	for elem in all_project:
		id_element += 1
		
		# configure remote name:
		if argument_remote_name == "":
			argument_remote_name = elem.select_remote["name"]
		base_display = tools.get_list_base_display(id_element, len(all_project), elem)
		debug.info("deliver-push: " + base_display)
		tools.wait_for_server_if_needed()
		# Check the repo exist
		git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
		if os.path.exists(git_repo_path) == False:
			debug.warning("deliver-push: " + base_display + " ==> MUST be download")
			continue
		# check if we are on "master"
		select_branch = commands.get_current_branch(git_repo_path)
		if select_branch != "master":
			debug.warning("deliver-push: " + base_display + " ==> MUST be on master")
			continue
		# check if we have a local branch
		list_branch_local = commands.get_list_branch_local(git_repo_path)
		if "develop" not in list_branch_local:
			debug.warning("deliver-push: " + base_display + " ==> No 'develop' (not managed)")
			continue
		if "master" not in list_branch_local:
			debug.warning("deliver-push: " + base_display + " ==> No 'master' (not managed)")
			continue
		list_of_element_to_push = []
		# check sha1 of master
		sha_1_master = commands.get_sha1_for_branch(git_repo_path, "master")
		tracking_remote_branch = commands.get_tracking_branch(git_repo_path, argument_remote_name, "master")
		if tracking_remote_branch == None:
			debug.warning("deliver-push: " + base_display + " ==> 'master' have no tracking branch")
			deliver_availlable = False
		sha_1_master_tracking = commands.get_sha1_for_branch(git_repo_path, tracking_remote_branch)
		if sha_1_master == sha_1_master_tracking:
			debug.info("deliver-push: " + base_display + " ==> 'master' && '" + tracking_remote_branch + "' have the same sha1")
		else:
			list_of_element_to_push.append("master")
		# check sha1 of develop
		sha_1_develop = commands.get_sha1_for_branch(git_repo_path, "develop")
		tracking_remote_branch = commands.get_tracking_branch(git_repo_path, argument_remote_name, "develop")
		if tracking_remote_branch == None:
			debug.info("deliver-push: " + base_display + " ==> 'develop' have no tracking branch")
			deliver_availlable = False
		sha_1_develop_tracking = commands.get_sha1_for_branch(git_repo_path, tracking_remote_branch)
		if sha_1_develop == sha_1_develop_tracking:
			debug.info("deliver-push: " + base_display + " ==> 'develop' && '" + tracking_remote_branch + "' have the same sha1")
		else:
			list_of_element_to_push.append("develop")
		ret_current_tags = commands.get_tags_current(git_repo_path)
		if len(ret_current_tags) == 0:
			debug.info("deliver-push: " + base_display + " ==> No tag on the current 'master'")
			continue
		if len(ret_current_tags) > 1:
			debug.info("deliver-push: " + base_display + " ==> Too mush tags on the current 'master' : " + str(ret_current_tags) + " ==> only support 1")
			continue
		list_remote_tags = commands.get_tags_remote(git_repo_path, argument_remote_name)
		debug.verbose("remote tags: " + str(list_remote_tags))
		if ret_current_tags[0] not in list_remote_tags:
			debug.info("deliver-push: " + base_display + " ==> tag already exist.")
			list_of_element_to_push.append(ret_current_tags[0])
		if len(list_of_element_to_push) == 0:
			debug.info("deliver-push: " + base_display + " ==> Everything up-to-date")
			continue
		debug.info("deliver-push: " + base_display + " ==> element to push:" + str(list_of_element_to_push))
		#push all on the server:
		commands.push(git_repo_path, argument_remote_name, list_of_element_to_push)


