#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license MPL v2.0 (see license file)
##
import platform
import sys
import os
import copy
import json
# Local import
from realog import debug
from . import tools
from . import env
from . import multiprocess
from . import repo_config

env.get_island_path_config()

unique_config = None

def get_unique_config():
	global unique_config
	if unique_config == None:
		unique_config = Config()
	return unique_config


class Config():
	def __init__(self):
		self._repo = ""
		self._branch = "master"
		self._manifest_name = "default.xml"
		self._volatiles = []
		self._curent_link = []
		self.load()
	
	# set it deprecated at 2020/07
	def load_old(self):
		config_property = tools.file_read_data(env.get_island_path_config_old())
		element_config = config_property.split("\n")
		for line in element_config:
			if    len(line) == 0 \
			   or line[0] == "#":
				# simple comment line ==> pass
				pass
			elif line[:5] == "repo=":
				self._repo = line[5:]
			elif line[:7] == "branch=":
				self._branch = line[7:]
			elif line[:5] == "file=":
				self._manifest_name = line[5:]
			else:
				debug.warning("island config error: can not parse: '" + str(line) + "'")
		return True
	
	def convert_config_file(self):
		debug.warning("INTERNAL: Convert your configuration file: " + str(env.get_island_path_config_old()) + " -> " + str(env.get_island_path_config()))
		self.load_old()
		self.store()
		tools.remove_file(env.get_island_path_config_old())
	
	def load(self):
		# transform the old format of configuration (use json now ==> simple
		if os.path.exists(env.get_island_path_config_old()) == True:
			self.convert_config_file()
		if os.path.exists(env.get_island_path_config()) == False:
			return True
		self._volatiles = []
		self._curent_link = []
		with open(env.get_island_path_config()) as json_file:
			data = json.load(json_file)
			if "repo" in data.keys():
				self._repo = data["repo"]
			if "branch" in data.keys():
				self._branch = data["branch"]
			if "manifest_name" in data.keys():
				self._manifest_name = data["manifest_name"]
			if "volatiles" in data.keys():
				for elem in data["volatiles"]:
					if "git_address" in elem.keys() and "path" in elem.keys():
						self.add_volatile(elem["git_address"], elem["path"])
			if "link" in data.keys():
				for elem in data["link"]:
					if "source" in elem.keys() and "destination" in elem.keys():
						self.add_link(elem["source"], elem["destination"])
			return True
		return False
	
	def store(self):
		data = {}
		data["repo"] = self._repo
		data["branch"] = self._branch
		data["manifest_name"] = self._manifest_name
		data["volatiles"] = self._volatiles
		data["link"] = self._curent_link
		with open(env.get_island_path_config(), 'w') as outfile:
			json.dump(data, outfile, indent=4)
			return True
		return False
	
	def set_manifest(self, value):
		self._repo = value
	
	def get_manifest(self):
		return self._repo
	
	def set_branch(self, value):
		self._branch = value
	
	def get_branch(self):
		return self._branch
	
	def set_manifest_name(self, value):
		self._manifest_name = value
	
	def get_manifest_name(self):
		return self._manifest_name
	
	def add_volatile(self, git_adress, local_path):
		for elem in self._volatiles:
			if elem["path"] == local_path:
				debug.error("can not have multiple local repositoty on the same PATH", crash=False)
				return False
		self._volatiles.append( {
			"git_address": git_adress,
			"path": local_path
			})
		return True
	
	def get_volatile(self):
		return copy.deepcopy(self._volatiles)
	
	
	def get_links(self):
		return self._curent_link
	
	def add_link(self, source, destination):
		for elem in self._curent_link:
			if elem["destination"] == destination:
				debug.error("can not have multiple destination folder in link " + destination, crash=False)
				return False
		self._curent_link.append( {
			"source": source,
			"destination": destination
			})
		return True
	
	def remove_link(self, destination):
		for elem in self._curent_link:
			if elem["destination"] == destination:
				del self._curent_link[elem]
				return
		debug.warning("Request remove link that does not exist")
	
	def clear_links(self):
		self._curent_link = []
	
	
	def get_manifest_config(self):
		conf = repo_config.RepoConfig()
		base_volatile, repo_volatile = repo_config.split_repo(self.get_manifest())
		conf.name = repo_volatile
		conf.path = os.path.join("." + env.get_system_base_name(), "manifest") #env.get_island_path_manifest()
		conf.branch = "master"
		conf.volatile = False
		conf.remotes = [
			{
				'name': 'origin',
				'fetch': base_volatile,
				'mirror': []
			}
			]
		conf.select_remote = {
				'name': 'origin',
				'fetch': base_volatile,
				'sync': False,
				'mirror': []
			}
		return conf

