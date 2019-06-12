#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license MPL v2.0 (see license file)
##

import os
import shutil
import errno
import fnmatch
import stat
# Local import
from realog import debug
from . import env
from . import multiprocess
from . import debug



def generic_display_error(return_value, type_name, error_only=False):
	debug.verbose(str(return_value))
	if return_value[0] == 0:
		if error_only == True:
			return
		display = False
		if return_value[1] != "":
			debug.info(return_value[1])
			display = True
		if return_value[2] != "":
			debug.warning(return_value[2])
			display = True
		if display == False:
			debug.verbose("GIT(" + type_name + "): All done OK")
	else:
		display = False
		if return_value[1] != "":
			debug.warning("ERROR GIT(" + type_name + ") 1:" + return_value[1])
			display = True
		if return_value[2] != "":
			debug.warning("ERROR GIT(" + type_name + ") 2:" + return_value[2])
			display = True
		if display == False:
			debug.warning("ERROR GIT(" + type_name + "): Unknow error return_value=" + str(return_value[0]))



"""
	
"""
def check_repository_is_modify(path_repository):
	# check if the repository is modify
	cmd = "git diff --quiet"
	debug.verbose("execute : " + cmd)
	return_value = multiprocess.run_command(cmd, cwd=path_repository)
	generic_display_error(return_value, "check_repository_is_modify", error_only=True)
	ret_diff = return_value
	if ret_diff[0] == 0:
		return False
	return True

def get_list_branch_meta(path_repository):
	# get local branch
	cmd = "git branch -a"
	debug.verbose("execute : " + cmd)
	return_value = multiprocess.run_command(cmd, cwd=path_repository)
	generic_display_error(return_value, "get_list_branch_meta", error_only=True)
	ret_branch = return_value
	list_branch = ret_branch[1].split('\n')
	out = []
	for elem_branch in list_branch:
		is_remote = False
		branch_name = ""
		is_selected = False
		if len(elem_branch.split(" -> ")) != 1:
			continue
		# separate the remote element
		if elem_branch[2:10] == "remotes/":
			elem_branch = elem_branch[:2] + elem_branch[10:]
			is_remote = True
		# separate select branch
		if elem_branch[:2] == "* ":
			is_selected = True
			branch_name = elem_branch[2:]
		else:
			branch_name = elem_branch[2:]
		out.append({
			"remote": is_remote,
			"name": branch_name,
			"select": is_selected
			})
	debug.extreme_verbose("List all branch Meta: " + str(out))
	return out


def get_list_branch_all(path_repository):
	tmp = get_list_branch_meta(path_repository)
	out = []
	for elem in tmp:
		out.append(elem["name"])
	debug.verbose("List all branch: " + str(out))
	return out

def get_list_branch_local(path_repository):
	tmp = get_list_branch_meta(path_repository)
	out = []
	for elem in tmp:
		if elem["remote"] == False:
			out.append(elem["name"])
	debug.verbose("List local branch: " + str(out))
	return out

def get_list_branch_remote(path_repository):
	tmp = get_list_branch_meta(path_repository)
	out = []
	for elem in tmp:
		if elem["remote"] == True:
			out.append(elem["name"])
	debug.verbose("List remote branch: " + str(out))
	return out

def get_current_branch(path_repository):
	tmp = get_list_branch_meta(path_repository)
	for elem in tmp:
		if elem["select"] == True:
			debug.verbose("List local branch: " + str(elem["name"]))
			return elem["name"]
	debug.verbose("List local branch: None" )
	return None

def get_current_tracking_branch(path_repository):
	# get  tracking branch
	cmd = "git rev-parse --abbrev-ref --symbolic-full-name @{u}"
	debug.verbose("execute : " + cmd)
	return_value = multiprocess.run_command(cmd, cwd=path_repository)
	generic_display_error(return_value, "get_current_tracking_branch", error_only=True)
	return return_value[1]

def get_revision_list_to_branch(path_repository, branch):
	cmd = "git rev-list " + branch
	debug.verbose("execute : " + cmd)
	return_value = multiprocess.run_command(cmd, cwd=path_repository)
	generic_display_error(return_value, "get_revision_list_to_branch", error_only=True)
	return return_value[1].split('\n')

def get_specific_commit_message(path_repository, sha_1):
	if sha_1 == None or sha_1 == "":
		return ""
	cmd = "git log --format=%B -n 1 " + sha_1
	debug.verbose("execute : " + cmd)
	return_value = multiprocess.run_command(cmd, cwd=path_repository)
	generic_display_error(return_value, "get_specific_commit_message", error_only=True)
	return return_value[1].split('\n')[0]

def get_sha1_for_branch(path_repository, branch_name):
	if branch_name == None or branch_name == "":
		return None
	cmd = "git rev-parse" + sha_1
	debug.verbose("execute : " + cmd)
	return_value = multiprocess.run_command(cmd, cwd=path_repository)
	generic_display_error(return_value, "get_sha1_for_branch", error_only=True)
	return return_value[1].split('\n')[0]



def get_tracking_branch(path_repository, remote_name, select_branch):
	# get tracking branch
	if remote_name == "" or remote_name == None:
		return get_current_tracking_branch(path_repository)
	list_branch_remote = get_list_branch_remote(path_repository)
	debug.extreme_verbose("check if exist " + remote_name + "/" + select_branch + " in " + str(list_branch_remote))
	if remote_name + "/" + select_branch not in list_branch_remote:
		debug.debug("    ==> can not get remote branch")
		return None
	return remote_name + "/" + select_branch


def merge_branch_on_master(path_repository, branch_name):
	if branch_name == None or branch_name == "":
		raise "Missing branch name"
	cmd = "git merge --no-ff " + branch_name + " --message \"Merge branch '" + branch_name + "' into 'master'\""
	debug.verbose("execute : " + cmd)
	# TODO: check if the command work correctly
	return_value = multiprocess.run_command(cmd, cwd=path_repository)
	generic_display_error(return_value, "merge_branch_on_master", error_only=True)
	return return_value


def add_file(path_repository, file_path):
	if file_path == None or file_path == "":
		raise "Missing file_path name"
	cmd = "git add " + file_path
	debug.verbose("execute : " + cmd)
	# TODO: check if the command work correctly
	return_value = multiprocess.run_command(cmd, cwd=path_repository)
	generic_display_error(return_value, "add_file", error_only=True)
	return return_value


def commit_all(path_repository, comment):
	if comment == None or comment == "":
		raise "Missing comment description"
	cmd = 'git commit -a --message "' + comment +'"'
	debug.verbose("execute : " + cmd)
	# TODO: check if the command work correctly
	return_value = multiprocess.run_command(cmd, cwd=path_repository)
	generic_display_error(return_value, "commit_all", error_only=True)
	return return_value

def tag(path_repository, tag_name):
	if tag_name == None or tag_name == "":
		raise "Missing tag name"
	tag_name = tag_name.replace(" ", "_")
	cmd = 'git tag ' + tag_name + ' --message "[TAG] create tag ' + tag_name +'"'
	debug.verbose("execute : " + cmd)
	# TODO: check if the command work correctly
	return_value = multiprocess.run_command(cmd, cwd=path_repository)
	generic_display_error(return_value, "tag", error_only=True)
	return return_value

def checkout(path_repository, branch_name):
	if branch_name == None or branch_name == "":
		raise "Missing branch name"
	cmd = 'git checkout ' + branch_name
	debug.verbose("execute : " + cmd)
	# TODO: check if the command work correctly
	return_value = multiprocess.run_command(cmd, cwd=path_repository)
	generic_display_error(return_value, "checkout", error_only=True)
	return return_value

def reset_hard(path_repository, destination):
	if destination == None or destination == "":
		raise "Missing destination 'sha1' or 'branch name'"
	cmd = 'git reset --hard ' + destination
	debug.verbose("execute : " + cmd)
	# TODO: check if the command work correctly
	return_value = multiprocess.run_command(cmd, cwd=path_repository)
	generic_display_error(return_value, "reset_hard", error_only=True)
	return return_value
